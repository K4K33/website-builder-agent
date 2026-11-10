-- Kaurivo demo build jobs. Public-schema table is private (admin-only RLS).
-- An authenticated browser may request a job via the narrowly scoped RPC;
-- it cannot write completion status, links, QA flags or processing fields.
create table if not exists public.kaurivo_demo_build_jobs (
 id uuid primary key default gen_random_uuid(),
 prospect_id uuid not null references public.kaurivo_crm_prospects(id) on delete restrict,
 requested_by uuid not null references auth.users(id),
 business_id text not null,
 company_name text not null,
 original_url text not null default '',
 website_language text not null default 'undetermined',
 status text not null default 'queued' check (status in (
   'queued','researching','building','qa','publishing',
   'internal_preview','hold','failed'
 )),
 progress text not null default 'Odottaa rakennustyön aloitusta',
 preview_url text not null default '',
 qa_url text not null default '',
 github_run_url text not null default '',
 github_run_id bigint,
 release_sha text not null default '',
 error_code text not null default '',
 master_prompt_sha256 text not null default '',
 attempt integer not null default 0 check (attempt between 0 and 3),
 created_at timestamptz not null default now(),
 started_at timestamptz,
 finished_at timestamptz,
 updated_at timestamptz not null default now(),
 constraint kaurivo_demo_preview_url_check check (
   preview_url = '' or preview_url ~ '^https://'
 ),
 constraint kaurivo_demo_unique_evidence check (
   status <> 'internal_preview' or
   (preview_url <> '' and qa_url <> '' and release_sha ~ '^[0-9a-f]{40}$')
 )
);
create index if not exists kaurivo_demo_jobs_created_idx
 on public.kaurivo_demo_build_jobs(created_at desc);
create index if not exists kaurivo_demo_jobs_prospect_idx
 on public.kaurivo_demo_build_jobs(prospect_id,created_at desc);
create unique index if not exists kaurivo_demo_one_running_per_prospect
 on public.kaurivo_demo_build_jobs(prospect_id)
 where status in ('queued','researching','building','qa','publishing');

alter table public.kaurivo_demo_build_jobs enable row level security;
revoke all on public.kaurivo_demo_build_jobs from anon, authenticated;
grant select on public.kaurivo_demo_build_jobs to authenticated;
grant all on public.kaurivo_demo_build_jobs to service_role;

drop policy if exists kaurivo_admin_reads_demo_jobs on public.kaurivo_demo_build_jobs;
create policy kaurivo_admin_reads_demo_jobs
 on public.kaurivo_demo_build_jobs for select to authenticated
 using ((select kaurivo_internal.is_kaurivo_admin()));

-- User-facing request. Never trust company data or URLs sent from browser:
-- read the existing prospect directly by UUID and snapshot public business facts.
create or replace function public.kaurivo_request_demo_build(p_prospect_id uuid)
returns uuid
language plpgsql
security definer
set search_path = ''
as $$
declare
 p record;
 old_id uuid;
 made_id uuid;
 job_count integer;
 chosen_url text;
 chosen_language text;
begin
 if (select kaurivo_internal.is_kaurivo_admin()) is not true then
   raise exception 'not authorized' using errcode = '42501';
 end if;
 select id, business_id, company_name, marketing_opt_out,
        website_found_url, website_listed_url, website_candidate_url,
        website_languages, review_status
 into p
 from public.kaurivo_crm_prospects
 where id=p_prospect_id
 for share;
 if not found then
   raise exception 'company not found' using errcode = '22023';
 end if;
 if p.review_status='skipped' then
   raise exception 'company is skipped' using errcode = '22023';
 end if;
 if p.marketing_opt_out then
   raise exception 'company has opted out; manual handling required' using errcode = '22023';
 end if;
 select id into old_id from public.kaurivo_demo_build_jobs
 where prospect_id=p_prospect_id and status in
   ('queued','researching','building','qa','publishing')
 order by created_at desc limit 1;
 if old_id is not null then return old_id; end if;
 -- Free-cap safeguard: at most five newly requested builds per Helsinki day.
 select count(*) into job_count from public.kaurivo_demo_build_jobs
 where created_at >= ((now() at time zone 'Europe/Helsinki')::date
   ::timestamp at time zone 'Europe/Helsinki')
   and created_at < (((now() at time zone 'Europe/Helsinki')::date + 1)
   ::timestamp at time zone 'Europe/Helsinki');
 if job_count >= 5 then
   raise exception 'daily free-build request cap reached (5)'
     using errcode = '22023';
 end if;
 chosen_url := coalesce(nullif(trim(p.website_found_url), ''),
                        nullif(trim(p.website_listed_url), ''),
                        nullif(trim(p.website_candidate_url), ''), '');
 if chosen_url <> '' and
    (chosen_url !~ '^https?://[A-Za-z0-9]' or
      char_length(chosen_url)>1500) then
    raise exception 'website URL must be reviewed before building'
      using errcode = '22023';
 end if;
 chosen_language := coalesce(nullif(trim(p.website_languages), ''),
                              'undetermined');
 -- Missing websites remain legitimate research jobs, but the worker must
 -- prove an independent verified-no-site source before generating a website.
 insert into public.kaurivo_demo_build_jobs(
   prospect_id,requested_by,business_id,company_name,original_url,
   website_language,status,progress)
 values (
   p_prospect_id,(select auth.uid()),p.business_id,p.company_name,
   chosen_url,chosen_language,'queued',
   case when chosen_url='' then
     'Jonossa: ensin vahvistettava, ettei yrityksellä ole verkkosivua'
   else 'Jonossa: alkuperäinen verkkosivu tutkitaan ennen rakentamista' end
 )
 returning id into made_id;
 return made_id;
exception
 when unique_violation then
   select id into old_id from public.kaurivo_demo_build_jobs
   where prospect_id=p_prospect_id and status in
   ('queued','researching','building','qa','publishing')
   order by created_at desc limit 1;
   if old_id is not null then return old_id; end if;
   raise;
end;
$$;
revoke all on function public.kaurivo_request_demo_build(uuid) from public,anon;
grant execute on function public.kaurivo_request_demo_build(uuid) to authenticated;

-- GitHub Actions OIDC-verified worker may claim one request at a time.
create or replace function public.kaurivo_worker_claim_demo(
 p_run_id bigint,
 p_run_url text
) returns table(
 id uuid,company_name text,business_id text,original_url text,
 website_language text
)
language plpgsql
security definer
set search_path = ''
as $$
declare record_id uuid;
begin
 if p_run_id is null or p_run_id <= 0
 or p_run_url !~ '^https://github[.]com/K4K33/website-builder-agent/actions/runs/[0-9]+$' then
   raise exception 'invalid worker identity' using errcode='22023';
 end if;
 select j.id into record_id from public.kaurivo_demo_build_jobs j
 where j.status='queued' order by j.created_at
 for update skip locked limit 1;
 if record_id is null then return; end if;
 update public.kaurivo_demo_build_jobs j
 set status='researching',progress='Tutkitaan yritystä ja alkuperäistä verkkosivua',
     github_run_id=p_run_id,github_run_url=p_run_url,
     started_at=now(),updated_at=now(),attempt=attempt+1
 where j.id=record_id;
 return query select j.id,j.company_name,j.business_id,
                     j.original_url,j.website_language
 from public.kaurivo_demo_build_jobs j where j.id=record_id;
end;
$$;
revoke all on function public.kaurivo_worker_claim_demo(bigint,text) from public,anon,authenticated;
grant execute on function public.kaurivo_worker_claim_demo(bigint,text) to service_role;

-- Bind worker updates to the specific claimed GitHub Actions run.
create or replace function public.kaurivo_worker_update_demo(
 p_id uuid, p_run_id bigint, p_status text,
 p_progress text default '',
 p_preview_url text default '',
 p_qa_url text default '',
 p_release_sha text default '',
 p_error_code text default ''
) returns boolean
language plpgsql
security definer
set search_path = ''
as $$
declare previous_status text;
begin
 select j.status into previous_status
 from public.kaurivo_demo_build_jobs j
 where j.id=p_id and j.github_run_id=p_run_id
 for update;
 if not found then return false; end if;
 if previous_status not in ('researching','building','qa','publishing') then
   return false;
 end if;
 if p_status not in ('researching','building','qa','publishing',
                     'internal_preview','hold','failed') then
   return false;
 end if;
 if p_status='internal_preview' then
   if previous_status not in ('qa','publishing')
      or p_preview_url !~ '^https://(k4k33[.]github[.]io|[A-Za-z0-9-]+[.]onrender[.]com)/'
      or p_qa_url !~ '^https://github[.]com/K4K33/website-builder-agent/actions/runs/[0-9]+$'
      or p_release_sha !~ '^[0-9a-f]{40}$' then
      return false;
   end if;
 end if;
 update public.kaurivo_demo_build_jobs
 set status=p_status,
     progress=left(coalesce(p_progress,''),300),
     preview_url=case when p_status='internal_preview' then p_preview_url else preview_url end,
     qa_url=case when p_status='internal_preview' then p_qa_url else qa_url end,
     release_sha=case when p_status='internal_preview' then p_release_sha else release_sha end,
     error_code=case when p_status in ('hold','failed') then left(p_error_code,100) else '' end,
     finished_at=case when p_status in ('internal_preview','hold','failed') then now() else finished_at end,
     updated_at=now()
 where id=p_id;
 return true;
end;
$$;
revoke all on function public.kaurivo_worker_update_demo(
 uuid,bigint,text,text,text,text,text,text
) from public,anon,authenticated;
grant execute on function public.kaurivo_worker_update_demo(
 uuid,bigint,text,text,text,text,text,text
) to service_role;

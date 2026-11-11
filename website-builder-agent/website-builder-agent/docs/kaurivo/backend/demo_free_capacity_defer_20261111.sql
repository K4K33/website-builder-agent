-- Kaurivo: preserve an explicit owner's build intent across free-provider
-- daily capacity exhaustion. Never charge for paid models, invent site
-- content, or silently mark the private preview ready.
-- No retries in a loop: at most 3 claims per job, different UTC days.

alter table public.kaurivo_demo_build_jobs
 add column if not exists next_eligible_at timestamptz;

create or replace function public.kaurivo_worker_claim_demo(
 p_run_id bigint, p_run_url text
) returns table(id uuid,company_name text,business_id text,
                original_url text,website_language text)
language plpgsql security definer set search_path = ''
as $$
declare record_id uuid;
begin
 if p_run_id is null or p_run_id<=0
 or p_run_url <> ('https://github.com/K4K33/website-builder-agent/actions/runs/'||p_run_id::text)
 then raise exception 'invalid worker identity' using errcode='22023'; end if;

 update public.kaurivo_demo_build_jobs j
 set status='hold',error_code='runner_stale_timeout',
     progress='Rakennustyö keskeytyi tai ei saanut valmista tarkistusta. Vaatii uuden yrityskohtaisen tarkistuksen.',
     finished_at=now(),updated_at=now()
 where j.status in ('researching','building','qa','publishing')
   and j.updated_at<now()-interval '70 minutes';

 select j.id into record_id from public.kaurivo_demo_build_jobs j
 where j.status='queued'
   and j.attempt<3
   and (j.next_eligible_at is null or j.next_eligible_at<=now())
 order by j.created_at
 for update skip locked limit 1;
 if record_id is null then return; end if;
 update public.kaurivo_demo_build_jobs j
 set status='researching',
     progress='Tutkitaan yritystä ja alkuperäistä verkkosivua',
     error_code='',next_eligible_at=null,
     github_run_id=p_run_id,github_run_url=p_run_url,
     started_at=now(),updated_at=now(),attempt=attempt+1
 where j.id=record_id;
 return query select j.id,j.company_name,j.business_id,j.original_url,
                     j.website_language
 from public.kaurivo_demo_build_jobs j where j.id=record_id;
end;
$$;
revoke all on function public.kaurivo_worker_claim_demo(bigint,text)
 from public,anon,authenticated;
grant execute on function public.kaurivo_worker_claim_demo(bigint,text)
 to service_role;

create or replace function public.kaurivo_worker_update_demo(
 p_id uuid, p_run_id bigint, p_status text,
 p_progress text default '', p_preview_url text default '',
 p_qa_url text default '', p_release_sha text default '',
 p_error_code text default ''
) returns boolean
language plpgsql security definer set search_path = ''
as $$
declare previous_status text;
declare previous_attempt integer;
begin
 select j.status,j.attempt into previous_status,previous_attempt
 from public.kaurivo_demo_build_jobs j
 where j.id=p_id and j.github_run_id=p_run_id
 for update;
 if not found or previous_status not in
   ('researching','building','qa','publishing')
 then return false; end if;

 -- The only legal rollback to QUEUED is quota-related, from the matching
 -- authenticated GitHub worker, never an arbitrary status reset.
 if p_status='queued' then
   if p_error_code<>'free_ai_capacity_unavailable' then return false; end if;
   update public.kaurivo_demo_build_jobs j
   set status=case when previous_attempt>=3 then 'hold' else 'queued' end,
       progress=case when previous_attempt>=3
          then 'Ilmainen AI-kapasiteetti ei riittänyt kolmella yrityksellä. Uusi yritys vaatii ylläpitäjän pyynnön.'
          else left(coalesce(p_progress,''),300) end,
       error_code='free_ai_capacity_unavailable',
       next_eligible_at=case when previous_attempt>=3 then null
          else ((date_trunc('day',now() at time zone 'UTC')
                   + interval '1 day 10 minutes') at time zone 'UTC') end,
       finished_at=case when previous_attempt>=3 then now() else null end,
       updated_at=now()
   where j.id=p_id;
   return true;
 end if;

 if p_status not in ('researching','building','qa','publishing',
                     'internal_preview','hold','failed') then return false; end if;
 if p_status='internal_preview' then
   if previous_status not in ('qa','publishing')
      or p_preview_url !~ '^https://(k4k33[.]github[.]io|[A-Za-z0-9-]+[.]onrender[.]com)/'
      or p_qa_url !~ '^https://github[.]com/K4K33/website-builder-agent/actions/runs/[0-9]+$'
      or p_release_sha !~ '^[0-9a-f]{40}$' then
      return false;
   end if;
 end if;
 update public.kaurivo_demo_build_jobs
 set status=p_status,progress=left(coalesce(p_progress,''),300),
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

-- Security: existing admin-only prospect access, owner RPC and marketing
-- consent gates are unchanged. All preview publishing/QA checks remain hard.

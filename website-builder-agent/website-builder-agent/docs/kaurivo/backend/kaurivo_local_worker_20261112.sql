-- Single owner-enrolled private Windows worker; no Supabase service key on PC.
-- A 256-bit bearer token is generated server-side, shown once, and only its
-- SHA-256 digest is stored in this private schema. Revoking enrollment rotates
-- the credential and invalidates all old copies.
create table if not exists kaurivo_internal.local_worker_devices (
 owner_id uuid primary key,
 token_hash text not null unique check(token_hash ~ '^[0-9a-f]{64}$'),
 run_id bigint not null unique check(run_id between 2000000000000000 and 8999999999999999),
 last_seen_at timestamptz,
 ai_ready boolean not null default false,
 created_at timestamptz not null default now(),
 updated_at timestamptz not null default now(),
 expires_at timestamptz not null default (now()+interval '180 days')
);
alter table kaurivo_internal.local_worker_devices enable row level security;
revoke all on kaurivo_internal.local_worker_devices from public,anon,authenticated;
grant all on kaurivo_internal.local_worker_devices to service_role;
alter table public.kaurivo_demo_build_jobs
 add column if not exists runner_kind text not null default 'github';
alter table public.kaurivo_demo_build_jobs
 add constraint kaurivo_demo_runner_kind_valid check (runner_kind in ('github','local'));

create or replace function public.kaurivo_local_worker_enroll(
 p_digest text,p_run_id bigint
) returns boolean language plpgsql security definer set search_path=''
as $$
begin
 if (select kaurivo_internal.is_kaurivo_admin()) is not true
   or auth.uid() is null then
   raise exception 'not authorized' using errcode='42501';
 end if;
 if p_digest !~ '^[0-9a-f]{64}$'
    or p_run_id not between 2000000000000000 and 8999999999999999
 then raise exception 'invalid worker credential' using errcode='22023'; end if;
 insert into kaurivo_internal.local_worker_devices(
     owner_id,token_hash,run_id,last_seen_at,ai_ready,updated_at,expires_at
 ) values(auth.uid(),p_digest,p_run_id,null,false,now(),now()+interval '180 days')
 on conflict (owner_id) do update set
     token_hash=excluded.token_hash,run_id=excluded.run_id,
     last_seen_at=null,ai_ready=false,updated_at=now(),
     expires_at=excluded.expires_at;
 return true;
end;
$$;
revoke all on function public.kaurivo_local_worker_enroll(text,bigint)
 from public,anon;
grant execute on function public.kaurivo_local_worker_enroll(text,bigint)
 to authenticated;

create or replace function public.kaurivo_local_worker_validate(
 p_digest text,p_ready boolean default null
) returns bigint language plpgsql security definer set search_path=''
as $$
declare result_id bigint;
begin
 if p_digest !~ '^[0-9a-f]{64}$' then return null; end if;
 select run_id into result_id from kaurivo_internal.local_worker_devices
 where token_hash=p_digest and expires_at>now();
 if result_id is not null then
   -- A 1-second local queue poll must not produce 86,400 unnecessary
   -- database writes per day. Heartbeat at most once every 8 seconds
   -- unless the actual model availability changed.
   update kaurivo_internal.local_worker_devices
   set last_seen_at=now(),ai_ready=coalesce(p_ready,ai_ready),updated_at=now()
   where token_hash=p_digest and expires_at>now()
     and (last_seen_at is null
          or last_seen_at<now()-interval '8 seconds'
          or (p_ready is not null and ai_ready is distinct from p_ready));
   -- An active Ollama model may legitimately take longer than 70 minutes.
   -- A live worker with a still valid claim must not be marked dead.
   update public.kaurivo_demo_build_jobs
   set updated_at=now()
   where github_run_id=result_id and runner_kind='local'
     and status in ('researching','building','qa','publishing')
     and updated_at<now()-interval '20 seconds';
 end if;
 return result_id;
end;
$$;
revoke all on function public.kaurivo_local_worker_validate(text,boolean)
 from public,anon,authenticated;
grant execute on function public.kaurivo_local_worker_validate(text,boolean)
 to service_role;

create or replace function public.kaurivo_local_worker_online()
returns boolean language sql security definer set search_path=''
as $$
 select (select kaurivo_internal.is_kaurivo_admin()) is true
 and exists (
   select 1 from kaurivo_internal.local_worker_devices
   where owner_id=auth.uid() and ai_ready=true
     and last_seen_at>now()-interval '20 seconds' and expires_at>now()
 );
$$;
revoke all on function public.kaurivo_local_worker_online() from public,anon;
grant execute on function public.kaurivo_local_worker_online()
 to authenticated;

create or replace function public.kaurivo_local_worker_claim(
 p_run_id bigint
) returns table(id uuid,company_name text,business_id text,
                original_url text,website_language text)
language plpgsql security definer set search_path=''
as $$
declare record_id uuid;
declare utc_today date := (now() at time zone 'UTC')::date;
begin
 if not exists (select 1 from kaurivo_internal.local_worker_devices
                where run_id=p_run_id and expires_at>now() and ai_ready=true
                 and last_seen_at>now()-interval '30 seconds') then
   return;
 end if;
 select j.id into record_id
 from public.kaurivo_demo_build_jobs j
 where j.status='queued'
   -- A proven local Ollama model does not consume cloud daily allowance.
   and (j.next_eligible_at is null or j.next_eligible_at<=now()
        or j.error_code='free_ai_capacity_unavailable')
   and (j.retry_day is distinct from utc_today or j.retry_claims_today<3)
 order by j.created_at desc
 for update skip locked limit 1;
 if record_id is null then return; end if;
 update public.kaurivo_demo_build_jobs j
 set status='researching',
     progress='Windows-rakentaja tutkii alkuperäistä verkkosivua',
     error_code='',next_eligible_at=null,dispatch_error_code='',
     github_run_id=p_run_id,github_run_url='',runner_kind='local',
     started_at=now(),updated_at=now(),attempt=attempt+1,
     retry_claims_today=case when retry_day=utc_today then retry_claims_today+1 else 1 end,
     retry_day=utc_today
 where j.id=record_id;
 return query select j.id,j.company_name,j.business_id,j.original_url,
                     j.website_language
 from public.kaurivo_demo_build_jobs j where j.id=record_id;
end;
$$;
revoke all on function public.kaurivo_local_worker_claim(bigint)
 from public,anon,authenticated;
grant execute on function public.kaurivo_local_worker_claim(bigint)
 to service_role;

-- Extend the EXISTING private checkpoint authority to include the exact
-- signed-in locally enrolled worker without exposing any checkpoint to users.
create or replace function public.kaurivo_worker_checkpoint_can_write(
 p_id uuid,p_run_id bigint
) returns boolean
language sql security definer set search_path=''
as $$
 select exists (
  select 1 from public.kaurivo_demo_build_jobs j
  where j.id=p_id and j.github_run_id=p_run_id
    and p_run_id>0 and j.status in ('researching','building','qa')
 );
$$;
revoke all on function public.kaurivo_worker_checkpoint_can_write(uuid,bigint)
 from public,anon,authenticated;
grant execute on function public.kaurivo_worker_checkpoint_can_write(uuid,bigint)
 to service_role;

-- Internal preview QA URL is a real locally generated report stored beside
-- the verifiable static preview, not a fabricated GitHub Actions run URL.
create or replace function public.kaurivo_worker_update_demo(
 p_id uuid,p_run_id bigint,p_status text,
 p_progress text default '',p_preview_url text default '',
 p_qa_url text default '',p_release_sha text default '',
 p_error_code text default ''
) returns boolean
language plpgsql security definer set search_path=''
as $$
declare previous_status text;
declare worker_kind text;
declare current_day_claims integer;
declare next_attempt timestamptz;
begin
 select j.status,j.runner_kind,j.retry_claims_today
 into previous_status,worker_kind,current_day_claims
 from public.kaurivo_demo_build_jobs j
 where j.id=p_id and j.github_run_id=p_run_id for update;
 if not found or previous_status not in
   ('researching','building','qa','publishing') then return false; end if;
 if p_status='queued' then
   if p_error_code not in
      ('free_ai_capacity_unavailable','free_ai_rate_limit',
       'research_network_unavailable','network_unavailable',
       'source_http_rate_limited','stage_timeout','runner_stale_timeout')
      then return false; end if;
   if current_day_claims>=3 or p_error_code='free_ai_capacity_unavailable' then
     next_attempt:=(date_trunc('day',now() at time zone 'UTC')
                          +interval '1 day 10 minutes') at time zone 'UTC';
   elsif p_error_code in ('free_ai_rate_limit','source_http_rate_limited') then
     next_attempt:=now()+interval '35 minutes';
   else next_attempt:=now()+interval '15 minutes'; end if;
   update public.kaurivo_demo_build_jobs
   set status='queued',progress=left(coalesce(p_progress,''),300),
       error_code=p_error_code,next_eligible_at=next_attempt,
       finished_at=null,updated_at=now()
   where id=p_id;
   return true;
 end if;
 if p_status not in ('researching','building','qa','publishing',
                     'internal_preview','hold','failed') then return false; end if;
 if p_status='internal_preview' then
   if previous_status not in ('qa','publishing')
     or p_preview_url !~ '^https://(k4k33[.]github[.]io|[A-Za-z0-9-]+[.]onrender[.]com)/'
     or p_release_sha !~ '^[0-9a-f]{40}$' then return false; end if;
   if worker_kind='local' then
     if p_qa_url !~ '^https://kaurivo-auto-demos-2026[.]onrender[.]com/[a-z0-9-]+/qa[.]html$'
       or replace(p_qa_url,'/qa.html','/index.html')<>p_preview_url
       then return false; end if;
   elsif p_qa_url !~ '^https://github[.]com/K4K33/website-builder-agent/actions/runs/[0-9]+$'
      then return false;
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

-- A scheduled GitHub backup must not steal a pending job while the Windows
-- machine is actively heartbeating; and a job previously handled locally
-- must return to explicit 'github' mode if the cloud backup takes over.
create or replace function public.kaurivo_worker_claim_specific_demo(
 p_run_id bigint,p_run_url text,p_job_id uuid
) returns table(id uuid,company_name text,business_id text,
                original_url text,website_language text)
language plpgsql security definer set search_path=''
as $$
declare record_id uuid;
declare utc_today date := (now() at time zone 'UTC')::date;
begin
 if p_run_id is null or p_run_id<=0
 or p_run_url <> ('https://github.com/K4K33/website-builder-agent/actions/runs/'||p_run_id::text)
 then raise exception 'invalid worker identity' using errcode='22023'; end if;
 update public.kaurivo_demo_build_jobs j
 set status='queued',error_code='runner_stale_timeout',
     progress='Rakentaja katkesi. Työ jatkuu viimeisestä tarkistetusta vaiheesta.',
     next_eligible_at=now()+interval '10 minutes',
     updated_at=now(),finished_at=null
 where j.status in ('researching','building','qa','publishing')
   and j.updated_at<now()-interval '70 minutes';
 select j.id into record_id from public.kaurivo_demo_build_jobs j
 where j.status='queued'
   and (p_job_id is null or j.id=p_job_id)
   and (j.next_eligible_at is null or j.next_eligible_at<=now())
   and (j.retry_day is distinct from utc_today or j.retry_claims_today<3)
   and (p_job_id is not null or not exists (
     select 1 from kaurivo_internal.local_worker_devices d
     where d.ai_ready=true and d.expires_at>now()
       and d.last_seen_at>now()-interval '20 seconds'))
 order by j.created_at
 for update skip locked limit 1;
 if record_id is null then return; end if;
 update public.kaurivo_demo_build_jobs j
 set status='researching',
     progress='Tutkitaan yritystä ja alkuperäistä verkkosivua',
     error_code='',next_eligible_at=null,dispatch_error_code='',
     github_run_id=p_run_id,github_run_url=p_run_url,runner_kind='github',
     started_at=now(),updated_at=now(),attempt=attempt+1,
     retry_claims_today=case when retry_day=utc_today
                             then retry_claims_today+1 else 1 end,
     retry_day=utc_today
 where j.id=record_id;
 return query select j.id,j.company_name,j.business_id,j.original_url,
                     j.website_language
 from public.kaurivo_demo_build_jobs j where j.id=record_id;
end;
$$;
revoke all on function public.kaurivo_worker_claim_specific_demo(bigint,text,uuid)
 from public,anon,authenticated;
grant execute on function public.kaurivo_worker_claim_specific_demo(bigint,text,uuid)
 to service_role;

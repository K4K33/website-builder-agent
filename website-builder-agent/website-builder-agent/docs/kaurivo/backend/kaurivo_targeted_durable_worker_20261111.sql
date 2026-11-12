-- Kaurivo resilient free-only queue. Preserve jobs through transient faults;
-- target the exact owner-selected UUID on workflow_dispatch (oldest-first cron
-- remains the backup). This does NOT assert a runner started until OIDC claim.
-- Never retry an objectively rejected QA or unverified business/source indefinitely.
alter table public.kaurivo_demo_build_jobs
  add column if not exists retry_day date,
  add column if not exists retry_claims_today integer not null default 0;
alter table public.kaurivo_demo_build_jobs
  add constraint kaurivo_demo_retry_claims_nonnegative check (retry_claims_today>=0);

create or replace function public.kaurivo_worker_claim_specific_demo(
 p_run_id bigint, p_run_url text, p_job_id uuid
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
 -- A dead GitHub runner must not permanently strand a checkpointed build.
 -- Its old run can no longer update the job once the state is queued.
 update public.kaurivo_demo_build_jobs j
 set status='queued',error_code='runner_stale_timeout',
     progress='Edellinen rakentaja katkesi. Työ jatkuu viimeisestä tarkistetusta vaiheesta.',
     next_eligible_at=now()+interval '10 minutes',
     updated_at=now(),finished_at=null
 where j.status in ('researching','building','qa','publishing')
   and j.updated_at<now()-interval '70 minutes';

 select j.id into record_id from public.kaurivo_demo_build_jobs j
 where j.status='queued'
   and (p_job_id is null or j.id=p_job_id)
   and (j.next_eligible_at is null or j.next_eligible_at<=now())
   and (j.retry_day is distinct from utc_today or j.retry_claims_today<3)
 order by j.created_at
 for update skip locked limit 1;
 if record_id is null then return; end if;
 update public.kaurivo_demo_build_jobs j
 set status='researching',
     progress='Tutkitaan yritystä ja alkuperäistä verkkosivua',
     error_code='',next_eligible_at=null,dispatch_error_code='',
     github_run_id=p_run_id,github_run_url=p_run_url,
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

create or replace function public.kaurivo_worker_claim_demo(
 p_run_id bigint, p_run_url text
) returns table(id uuid,company_name text,business_id text,
                original_url text,website_language text)
language sql security definer set search_path=''
as $$
 select * from public.kaurivo_worker_claim_specific_demo(p_run_id,p_run_url,null::uuid);
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
language plpgsql security definer set search_path=''
as $$
declare previous_status text;
declare current_day_claims integer;
declare utc_today date := (now() at time zone 'UTC')::date;
declare next_attempt timestamptz;
begin
 select j.status,j.retry_claims_today into previous_status,current_day_claims
 from public.kaurivo_demo_build_jobs j
 where j.id=p_id and j.github_run_id=p_run_id for update;
 if not found or previous_status not in
   ('researching','building','qa','publishing') then return false; end if;

 if p_status='queued' then
   -- Retry only transient failures; never spin on bad verified source,
   -- invalid business data, insecure images or independent QA failure.
   if p_error_code not in
      ('free_ai_capacity_unavailable','free_ai_rate_limit',
       'research_network_unavailable','network_unavailable',
       'source_http_rate_limited','stage_timeout','runner_stale_timeout')
      then return false; end if;
   if p_error_code='free_ai_capacity_unavailable' or current_day_claims>=3 then
     next_attempt:=(date_trunc('day',now() at time zone 'UTC')
                       + interval '1 day 10 minutes') at time zone 'UTC';
   elsif p_error_code in ('free_ai_rate_limit','source_http_rate_limited') then
     next_attempt:=now()+interval '35 minutes';
   else
     next_attempt:=now()+interval '15 minutes';
   end if;
   update public.kaurivo_demo_build_jobs j
   set status='queued',
       progress=left(coalesce(p_progress,''),300),
       error_code=p_error_code,
       next_eligible_at=next_attempt,finished_at=null,
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
      or p_release_sha !~ '^[0-9a-f]{40}$' then return false; end if;
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

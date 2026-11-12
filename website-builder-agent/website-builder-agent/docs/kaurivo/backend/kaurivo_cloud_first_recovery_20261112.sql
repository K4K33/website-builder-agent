-- Kaurivo cloud-first recovery while the owner cannot run local Ollama.
-- Reuse the existing exact-job OIDC gate; retain strict, bounded retries and
-- never trust an unverified/old Codex heartbeat as a ready local builder.
-- A local Codex-quota failure may migrate to cloud ONE TIME that UTC day.
-- The old job, identity, research and private checkpoints are preserved.
alter table public.kaurivo_demo_build_jobs
  add column if not exists cloud_recovery_day date;

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

 -- Leave this recovery bounded and scoped to the actually stale cloud job.
 update public.kaurivo_demo_build_jobs j
 set status='queued',error_code='runner_stale_timeout',
     progress='Pilvirakentaja katkesi. Työ jatkuu tallennetusta vaiheesta.',
     next_eligible_at=now()+interval '10 minutes',
     updated_at=now(),finished_at=null
 where j.runner_kind='github'
   and j.status in ('researching','building','qa','publishing')
   and j.updated_at<now()-interval '70 minutes';

 select j.id into record_id
 from public.kaurivo_demo_build_jobs j
 where j.status='queued'
   and (p_job_id is null or j.id=p_job_id)
   and (
     ((j.next_eligible_at is null or j.next_eligible_at<=now())
        and (j.retry_day is distinct from utc_today or j.retry_claims_today<3))
     or
     (j.runner_kind='local'
      and j.error_code in ('free_ai_rate_limit','free_ai_capacity_unavailable')
      and j.retry_day=utc_today and j.retry_claims_today>=3
      and j.cloud_recovery_day is distinct from utc_today)
   )
   -- Only a PROVEN local Ollama instance can outrank a scheduled cloud run.
   -- Legacy Codex/unverified heartbeats cannot prevent cloud progress.
   and (p_job_id is not null or not exists (
     select 1 from kaurivo_internal.local_worker_devices d
     where d.ai_ready=true and d.inference_backend='ollama'
       and d.expires_at>now()
       and d.last_seen_at>now()-interval '55 seconds'))
 order by
   case when j.runner_kind='local'
         and j.error_code in ('free_ai_rate_limit','free_ai_capacity_unavailable')
         and j.cloud_recovery_day is distinct from utc_today
        then 0 else 1 end,
   j.dispatch_requested_at desc nulls last,j.created_at
 for update skip locked limit 1;
 if record_id is null then return; end if;

 update public.kaurivo_demo_build_jobs j
 set status='researching',
     progress='Pilvirakentaja aloitti yrityksen tutkimuksen; nykyinen Mestari-Prompt voimassa',
     cloud_recovery_day=case
       when j.runner_kind='local'
        and j.error_code in ('free_ai_rate_limit','free_ai_capacity_unavailable')
        and j.retry_day=utc_today and j.retry_claims_today>=3
       then utc_today else j.cloud_recovery_day end,
     error_code='',next_eligible_at=null,dispatch_error_code='',
     github_run_id=p_run_id,github_run_url=p_run_url,runner_kind='github',
     started_at=now(),updated_at=now(),attempt=attempt+1,
     retry_claims_today=case when retry_day=utc_today
                             then retry_claims_today+1 else 1 end,
     retry_day=utc_today
 where j.id=record_id;

 return query
 select j.id,j.company_name,j.business_id,j.original_url,j.website_language
 from public.kaurivo_demo_build_jobs j where j.id=record_id;
end;
$$;
revoke all on function public.kaurivo_worker_claim_specific_demo(bigint,text,uuid)
 from public,anon,authenticated;
grant execute on function public.kaurivo_worker_claim_specific_demo(bigint,text,uuid)
 to service_role;

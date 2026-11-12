-- Keep Windows build leases tied to the actual living subprocess, not to
-- an idle daemon that might have lost/crashed its child.
-- Never mark a demo complete without authenticated QA and a real preview.
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
   update kaurivo_internal.local_worker_devices
   set last_seen_at=now(),ai_ready=coalesce(p_ready,ai_ready),updated_at=now()
   where token_hash=p_digest and expires_at>now()
     and (last_seen_at is null
          or last_seen_at<now()-interval '8 seconds'
          or (p_ready is not null and ai_ready is distinct from p_ready));
 end if;
 -- Deliberately NEVER refresh an active job merely because a daemon token
 -- exists: the build subprocess may have exited even while polling continues.
 return result_id;
end;
$$;
revoke all on function public.kaurivo_local_worker_validate(text,boolean)
 from public,anon,authenticated;
grant execute on function public.kaurivo_local_worker_validate(text,boolean)
 to service_role;

create or replace function public.kaurivo_local_worker_heartbeat(
 p_id uuid,p_run_id bigint
) returns boolean language plpgsql security definer set search_path=''
as $$
declare found_id uuid;
begin
 if not exists (select 1 from kaurivo_internal.local_worker_devices d
                 where d.run_id=p_run_id and d.expires_at>now()
                   and d.last_seen_at>now()-interval '30 seconds')
 then return false; end if;
 update public.kaurivo_demo_build_jobs j
 set updated_at=now()
 where j.id=p_id and j.github_run_id=p_run_id and j.runner_kind='local'
   and j.status in ('researching','building','qa','publishing')
   and j.updated_at<now()-interval '12 seconds'
 returning j.id into found_id;
 return found_id is not null or exists (
   select 1 from public.kaurivo_demo_build_jobs j
   where j.id=p_id and j.github_run_id=p_run_id and j.runner_kind='local'
     and j.status in ('researching','building','qa','publishing'));
end;
$$;
revoke all on function public.kaurivo_local_worker_heartbeat(uuid,bigint)
 from public,anon,authenticated;
grant execute on function public.kaurivo_local_worker_heartbeat(uuid,bigint)
 to service_role;

create or replace function public.kaurivo_local_worker_release(
 p_id uuid,p_run_id bigint
) returns boolean language plpgsql security definer set search_path=''
as $$
declare found_id uuid;
begin
 -- Called only when the actual child process ended. An already finished
 -- or QA-held demo is NOT requeued, so the quality gate remains intact.
 update public.kaurivo_demo_build_jobs j
 set status='queued',error_code='runner_stale_timeout',
     progress='Windows-rakentaja keskeytyi. Työ jatkuu tallennetusta vaiheesta.',
     next_eligible_at=case
       when j.retry_claims_today>=3 and
         j.retry_day=(now() at time zone 'UTC')::date then
           ((date_trunc('day',now() at time zone 'UTC')
             +interval '1 day 10 minutes') at time zone 'UTC')
       else now()+interval '20 seconds' end,
     finished_at=null,updated_at=now()
 where j.id=p_id and j.github_run_id=p_run_id and j.runner_kind='local'
   and j.status in ('researching','building','qa','publishing')
 returning j.id into found_id;
 return found_id is not null;
end;
$$;
revoke all on function public.kaurivo_local_worker_release(uuid,bigint)
 from public,anon,authenticated;
grant execute on function public.kaurivo_local_worker_release(uuid,bigint)
 to service_role;

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
 -- Recovery cannot depend on GitHub: a free-only Windows installation may
 -- have GitHub completely unavailable. Sweep genuinely stale child leases
 -- while the actual daemon is online, then resume from private checkpoints.
 update public.kaurivo_demo_build_jobs j
 set status='queued',error_code='runner_stale_timeout',
     progress='Windows-rakentaja katkesi. Työ palautetaan jatkettavaksi.',
     next_eligible_at=now()+interval '10 seconds',
     updated_at=now(),finished_at=null
 where j.runner_kind='local'
   and j.status in ('researching','building','qa','publishing')
   and j.updated_at<now()-interval '70 minutes';

 select j.id into record_id
 from public.kaurivo_demo_build_jobs j
 where j.status='queued'
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
     retry_claims_today=case when retry_day=utc_today
                             then retry_claims_today+1 else 1 end,
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

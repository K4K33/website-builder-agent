-- Private, no-CRM-data Windows wakeups through Supabase Realtime.
-- A single random 256-bit token-derived topic is never exposed in the web app.
-- Anonymous users cannot predict the private-device topic, but the broadcast
-- itself is deliberately public: it only carries a fixed {ready:true} flag.
-- The worker STILL must authenticate via private bearer and lock the job.
create or replace function kaurivo_internal.notify_local_demo_worker()
returns trigger language plpgsql security definer set search_path=''
as $$
declare d record;
begin
 if new.status<>'queued' then return new; end if;
 for d in
   select token_hash from kaurivo_internal.local_worker_devices
   where ai_ready=true and expires_at>now()
     and last_seen_at>now()-interval '55 seconds'
 loop
   begin
     -- No company name, prospect id, job id, owner id, prompt or content.
     perform realtime.send(jsonb_build_object('ready',true),
        'wake','kaurivo-demo-local-'||left(d.token_hash,48),false);
   exception when others then
     -- A disconnected Realtime channel cannot block the owner's explicit
     -- demo request. The rare missed signal is caught by the 90s fallback.
     null;
   end;
 end loop;
 return new;
end;
$$;
revoke all on function kaurivo_internal.notify_local_demo_worker()
 from public,anon,authenticated;

drop trigger if exists kaurivo_demo_local_wakeup on public.kaurivo_demo_build_jobs;
create trigger kaurivo_demo_local_wakeup
 after insert on public.kaurivo_demo_build_jobs
 for each row execute function kaurivo_internal.notify_local_demo_worker();

-- Presence remains fresh at 20-second intervals; do not claim the local
-- machine is offline between two healthy heartbeats.
create or replace function public.kaurivo_local_worker_online()
returns boolean language sql security definer set search_path=''
as $$
 select (select kaurivo_internal.is_kaurivo_admin()) is true
 and exists (
   select 1 from kaurivo_internal.local_worker_devices
   where owner_id=auth.uid() and ai_ready=true
     and last_seen_at>now()-interval '55 seconds' and expires_at>now()
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
                 and last_seen_at>now()-interval '55 seconds') then
   return;
 end if;
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

-- Never steal a new request from the owner-enrolled desktop on the scheduled
-- Github backup path when a heartbeat says Windows is ready.
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
       and d.last_seen_at>now()-interval '55 seconds'))
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

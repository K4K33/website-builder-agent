-- Kaurivo: authenticate actual Ollama runtime before a one-click claim.
-- Existing enrolled secrets stay untouched; old Codex daemons are unverified.
alter table kaurivo_internal.local_worker_devices
  add column if not exists inference_backend text not null default 'unverified';
alter table public.kaurivo_demo_build_jobs
  add column if not exists offline_recovery_day date;

-- No browser role may read the private worker capability.
revoke all on kaurivo_internal.local_worker_devices from public, anon, authenticated;

create or replace function public.kaurivo_local_worker_validate_v2(
  p_digest text, p_ready boolean default null, p_backend text default null
) returns bigint
language plpgsql security definer set search_path=''
as $$
declare result_id bigint;
begin
  if p_digest !~ '^[0-9a-f]{64}$' or
     (p_backend is not null and p_backend <> 'ollama') then
    return null;
  end if;
  select run_id into result_id
  from kaurivo_internal.local_worker_devices
  where token_hash=p_digest and expires_at>now();
  if result_id is not null then
    update kaurivo_internal.local_worker_devices
    set last_seen_at=now(),
        ai_ready=coalesce(p_ready,ai_ready),
        inference_backend=case when p_ready is not null then
             coalesce(p_backend,'unverified') else inference_backend end,
        updated_at=now()
    where token_hash=p_digest and expires_at>now()
      and (last_seen_at is null or last_seen_at<now()-interval '8 seconds'
           or (p_ready is not null and (ai_ready is distinct from p_ready
                  or inference_backend is distinct from coalesce(p_backend,'unverified'))));
  end if;
  return result_id;
end;
$$;
revoke all on function public.kaurivo_local_worker_validate_v2(text,boolean,text)
 from public,anon,authenticated;
grant execute on function public.kaurivo_local_worker_validate_v2(text,boolean,text)
 to service_role;

create or replace function public.kaurivo_local_worker_online()
returns boolean language sql security definer set search_path=''
as $$
  select (select kaurivo_internal.is_kaurivo_admin()) is true
  and exists (
    select 1 from kaurivo_internal.local_worker_devices
    where owner_id=auth.uid() and ai_ready=true
      and inference_backend='ollama'
      and last_seen_at>now()-interval '55 seconds' and expires_at>now()
  );
$$;
revoke all on function public.kaurivo_local_worker_online() from public,anon;
grant execute on function public.kaurivo_local_worker_online() to authenticated;

-- Owner selection is made durable so the local worker prefers the exact
-- company whose Rakenna demo button was pressed. No company data is
-- sent over Realtime (the signal still contains only a wake event).
create or replace function public.kaurivo_local_worker_wakeup(p_job_id uuid)
returns boolean language plpgsql security definer set search_path=''
as $$
declare d record; sent boolean:=false;
begin
  if (select kaurivo_internal.is_kaurivo_admin()) is not true
    or auth.uid() is null then
    raise exception 'not authorized' using errcode='42501';
  end if;
  update public.kaurivo_demo_build_jobs j
  set dispatch_requested_at=now()
  where j.id=p_job_id and j.status='queued' and j.requested_by=auth.uid();
  if not found then return false; end if;
  for d in select token_hash from kaurivo_internal.local_worker_devices
    where owner_id=auth.uid() and ai_ready=true
      and inference_backend='ollama' and expires_at>now()
      and last_seen_at>now()-interval '55 seconds'
  loop
    begin
      perform realtime.send(jsonb_build_object('ready',true),
       'wake','kaurivo-demo-local-'||left(d.token_hash,48),false);
      sent:=true;
    exception when others then null;
    end;
  end loop;
  return sent;
end;
$$;
revoke all on function public.kaurivo_local_worker_wakeup(uuid) from public,anon;
grant execute on function public.kaurivo_local_worker_wakeup(uuid) to authenticated;

-- A migrated local job may have used its 3 attempts against Codex quota.
-- Permit precisely ONE offline migration claim that same day, only when
-- an authenticated enrolled Ollama worker is ready. Never uncap retries.
create or replace function public.kaurivo_local_worker_claim(p_run_id bigint)
returns table(id uuid,company_name text,business_id text,
              original_url text,website_language text)
language plpgsql security definer set search_path=''
as $$
declare record_id uuid;
declare utc_today date := (now() at time zone 'UTC')::date;
begin
  if not exists (
    select 1 from kaurivo_internal.local_worker_devices
    where run_id=p_run_id and expires_at>now() and ai_ready=true
      and inference_backend='ollama'
      and last_seen_at>now()-interval '55 seconds'
  ) then return; end if;
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
  where j.status='queued' and (
    (j.next_eligible_at is null or j.next_eligible_at<=now()
       or j.error_code='free_ai_capacity_unavailable')
    and (j.retry_day is distinct from utc_today or j.retry_claims_today<3)
    or (
      j.error_code in ('free_ai_rate_limit','free_ai_capacity_unavailable')
      and j.retry_day=utc_today and j.retry_claims_today=3
      and j.offline_recovery_day is distinct from utc_today
    )
  )
  order by j.dispatch_requested_at desc nulls last,j.created_at desc
  for update skip locked limit 1;
  if record_id is null then return; end if;

  update public.kaurivo_demo_build_jobs j
  set status='researching',
      progress='Paikallinen AI aloitti tutkimuksen; Mestari-Prompt V6 voimassa',
      offline_recovery_day=case when
        j.retry_day=utc_today and j.retry_claims_today=3
        then utc_today else j.offline_recovery_day end,
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
grant execute on function public.kaurivo_local_worker_claim(bigint) to service_role;

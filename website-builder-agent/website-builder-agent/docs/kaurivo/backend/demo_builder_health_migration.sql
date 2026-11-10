-- Fail-closed global Kaurivo demo-builder health, owner-only visibility.
-- The GitHub Actions worker checks the actual OpenRouter inference API key
-- without generating tokens. An invalid key pauses new jobs at INSERT/RPC.
create table if not exists public.kaurivo_demo_builder_health (
  singleton boolean primary key default true check(singleton is true),
  status text not null check(status in ('ok','blocked','unknown')),
  error_code text not null default '',
  checked_at timestamptz not null default now(),
  github_run_url text not null default ''
);
alter table public.kaurivo_demo_builder_health enable row level security;
revoke all on public.kaurivo_demo_builder_health from anon,authenticated;
grant select on public.kaurivo_demo_builder_health to authenticated;
grant all on public.kaurivo_demo_builder_health to service_role;
drop policy if exists kaurivo_admin_reads_builder_health on public.kaurivo_demo_builder_health;
create policy kaurivo_admin_reads_builder_health
 on public.kaurivo_demo_builder_health for select to authenticated
 using ((select kaurivo_internal.is_kaurivo_admin()));
insert into public.kaurivo_demo_builder_health
 (singleton,status,error_code,checked_at,github_run_url)
values (true,'blocked','free_ai_key_invalid',now(),
 'https://github.com/K4K33/website-builder-agent/actions/runs/42807280159')
on conflict (singleton) do nothing;

-- Only the GitHub-OIDC-verified server bridge, using service_role, can set
-- health. The reported HTTP code is mapped to non-sensitive server values.
create or replace function public.kaurivo_worker_record_health(
 p_run_id bigint,p_http_status integer
) returns boolean language plpgsql security definer set search_path = ''
as $$
declare v_status text;
declare v_code text;
begin
 if p_run_id is null or p_run_id<=0 or p_http_status is null then
   raise exception 'invalid health observation' using errcode='22023';
 end if;
 v_status := case p_http_status when 200 then 'ok'
            when 401 then 'blocked' when 403 then 'blocked'
            else 'unknown' end;
 v_code := case p_http_status when 200 then ''
           when 401 then 'free_ai_key_invalid'
           when 403 then 'free_ai_key_forbidden'
           else 'free_ai_key_validation_unavailable' end;
 insert into public.kaurivo_demo_builder_health
   (singleton,status,error_code,checked_at,github_run_url)
 values (true,v_status,v_code,now(),
   'https://github.com/K4K33/website-builder-agent/actions/runs/'||p_run_id::text)
 on conflict (singleton) do update
 set status=excluded.status,error_code=excluded.error_code,
     checked_at=excluded.checked_at,github_run_url=excluded.github_run_url;
 return true;
end;
$$;
revoke all on function public.kaurivo_worker_record_health(bigint,integer)
 from public,anon,authenticated;
grant execute on function public.kaurivo_worker_record_health(bigint,integer)
 to service_role;

-- Also protect direct privileged INSERTs, not just the browser button.
-- User can requeue automatically after a valid key check arrives.
create or replace function public.kaurivo_demo_require_healthy_worker()
returns trigger language plpgsql security invoker set search_path = ''
as $$
begin
 if not exists (
   select 1 from public.kaurivo_demo_builder_health h
   where h.singleton=true and h.status='ok'
     and h.checked_at>=now()-interval '2 hours'
 ) then
   raise exception 'demo builder disabled: OpenRouter key or scheduler unavailable'
      using errcode='22023';
 end if;
 return new;
end;
$$;
drop trigger if exists kaurivo_demo_health_before_insert
 on public.kaurivo_demo_build_jobs;
create trigger kaurivo_demo_health_before_insert
 before insert on public.kaurivo_demo_build_jobs
 for each row execute function public.kaurivo_demo_require_healthy_worker();

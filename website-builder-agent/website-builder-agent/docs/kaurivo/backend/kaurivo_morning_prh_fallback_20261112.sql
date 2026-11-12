create extension if not exists pg_cron with schema pg_catalog;
create extension if not exists pg_net with schema extensions;

select vault.create_secret(
  replace(gen_random_uuid()::text || gen_random_uuid()::text, '-', ''),
  'kaurivo_prh_morning_fallback_token',
  'Dedicated credential for the Kaurivo morning PRH fallback'
)
where not exists (
  select 1 from vault.secrets where name = 'kaurivo_prh_morning_fallback_token'
);

create table if not exists public.kaurivo_morning_prh_claims (
  run_day date not null,
  attempt integer not null check (attempt in (1, 2)),
  primary key (run_day, attempt)
);
alter table public.kaurivo_morning_prh_claims enable row level security;
revoke all on public.kaurivo_morning_prh_claims from public, anon, authenticated;

create or replace function public.kaurivo_authorize_morning_prh(p_token text)
returns integer
language plpgsql
security definer
set search_path = ''
as $$
declare
  local_time timestamp := statement_timestamp() at time zone 'Europe/Helsinki';
  run_day date := local_time::date;
  slot integer;
  claimed integer;
begin
  if p_token is null or not exists (
    select 1 from vault.decrypted_secrets
    where name = 'kaurivo_prh_morning_fallback_token'
      and pg_catalog.sha256(pg_catalog.convert_to(decrypted_secret, 'UTF8'))
        = pg_catalog.sha256(pg_catalog.convert_to(p_token, 'UTF8'))
  ) then
    return -1;
  end if;

  if local_time::time >= time '07:05' and local_time::time < time '07:15' then
    slot := 1;
  elsif local_time::time >= time '07:35' and local_time::time < time '07:45' then
    slot := 2;
  else
    return 0;
  end if;

  if exists (
    select 1 from public.kaurivo_pipeline_events
    where event_day = run_day and outcome = 'success'
      and (component = 'national_search' or (component = 'manual_search' and records > 0))
  ) then
    return 0;
  end if;

  insert into public.kaurivo_morning_prh_claims values (run_day, slot)
  on conflict do nothing
  returning attempt into claimed;
  return coalesce(claimed, 0);
end;
$$;
revoke all on function public.kaurivo_authorize_morning_prh(text) from public, anon, authenticated;
grant execute on function public.kaurivo_authorize_morning_prh(text) to service_role;

select cron.schedule('kaurivo-prh-morning-fallback', '5,35 4,5 * * *', $cron$
  select net.http_post(
    url := 'https://xhsfbcwpwbgdbatrcyuk.supabase.co/functions/v1/kaurivo-manual-scan',
    headers := jsonb_build_object('Content-Type','application/json',
      'X-Kaurivo-Scheduler-Token', secret.decrypted_secret),
    timeout_milliseconds := 90000
  )
  from vault.decrypted_secrets as secret
  where secret.name = 'kaurivo_prh_morning_fallback_token'
    and (now() at time zone 'Europe/Helsinki')::date >= date '2026-11-13'
    and (now() at time zone 'Europe/Helsinki')::time >= time '07:05'
    and (now() at time zone 'Europe/Helsinki')::time < time '07:45'
    and not exists (
      select 1 from public.kaurivo_pipeline_events
      where event_day = (now() at time zone 'Europe/Helsinki')::date and outcome = 'success'
        and (component = 'national_search' or (component = 'manual_search' and records > 0))
    );
$cron$);

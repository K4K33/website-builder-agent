-- 2026-11-11: Allow owners to queue Kaurivo demos despite delayed GitHub cron.
-- The worker still performs live credential verification before claiming jobs.
-- Explicit invalid/unknown health states and missing health records remain blocked.
-- The QA, owner-review, version-pin and actual live preview gates are untouched.
create or replace function public.kaurivo_demo_require_healthy_worker()
returns trigger language plpgsql security invoker set search_path = ''
as $$
begin
  if not exists (
    select 1 from public.kaurivo_demo_builder_health h
    where h.singleton = true
      and h.status = 'ok'
      and h.checked_at <= now()
  ) then
    raise exception 'demo builder disabled: OpenRouter key last verification failed or missing'
      using errcode = '22023';
  end if;
  return new;
end;
$$;

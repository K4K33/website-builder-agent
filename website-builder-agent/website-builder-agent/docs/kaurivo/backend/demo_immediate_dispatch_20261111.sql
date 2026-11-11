-- Kaurivo private one-click demo dispatch: owner can request GitHub Actions
-- immediately rather than relying on delayed/dropped scheduled cron events.
-- This timestamp limits repeated dispatches; it is NOT a build completion flag.
alter table public.kaurivo_demo_build_jobs
  add column if not exists dispatch_requested_at timestamptz;

create or replace function public.kaurivo_claim_demo_dispatch(p_job_id uuid)
returns boolean language plpgsql security definer set search_path=''
as $$
declare claimed uuid;
begin
  if (select kaurivo_internal.is_kaurivo_admin()) is not true then
    raise exception 'not authorized' using errcode='42501';
  end if;
  update public.kaurivo_demo_build_jobs
  set dispatch_requested_at=now()
  where id=p_job_id and status='queued'
    and (dispatch_requested_at is null
      or dispatch_requested_at<now()-interval '90 seconds')
  returning id into claimed;
  return claimed is not null;
end;
$$;
revoke all on function public.kaurivo_claim_demo_dispatch(uuid) from public,anon;
grant execute on function public.kaurivo_claim_demo_dispatch(uuid) to authenticated;

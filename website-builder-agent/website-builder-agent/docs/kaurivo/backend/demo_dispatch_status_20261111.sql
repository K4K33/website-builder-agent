-- Record the real dispatch result separately from the actual build stage.
-- This is admin-only and cannot forge completed QA or preview links.
alter table public.kaurivo_demo_build_jobs
  add column if not exists dispatch_error_code text not null default '',
  add column if not exists dispatch_checked_at timestamptz,
  add column if not exists dispatch_accepted_at timestamptz;

create or replace function public.kaurivo_report_demo_dispatch(
 p_job_id uuid, p_error_code text, p_accepted boolean default false
) returns boolean language plpgsql security definer set search_path=''
as $$
declare found_id uuid;
begin
 if (select kaurivo_internal.is_kaurivo_admin()) is not true then
   raise exception 'not authorized' using errcode='42501';
 end if;
 if p_accepted is null or p_error_code is null or
    (p_accepted and p_error_code <> '') or
    (not p_accepted and p_error_code not in
      ('github_token_not_configured','github_token_permissions',
       'github_rate_limited','github_unreachable','github_dispatch_failed',
       'dispatch_claim_failed','db_unavailable','backend_unavailable')) then
   raise exception 'invalid dispatch result' using errcode='22023';
 end if;
 update public.kaurivo_demo_build_jobs
 set dispatch_checked_at=now(),
     dispatch_error_code=p_error_code,
     dispatch_accepted_at=case when p_accepted then now() else null end,
     -- An unaccepted GitHub dispatch must be immediately retriable after
     -- the missing secret/permission is fixed. No build attempt was spent.
     dispatch_requested_at=case when p_accepted then dispatch_requested_at else null end,
     updated_at=now()
 where id=p_job_id and status='queued'
 returning id into found_id;
 return found_id is not null;
end;
$$;
revoke all on function public.kaurivo_report_demo_dispatch(uuid,text,boolean)
 from public,anon;
grant execute on function public.kaurivo_report_demo_dispatch(uuid,text,boolean)
 to authenticated;

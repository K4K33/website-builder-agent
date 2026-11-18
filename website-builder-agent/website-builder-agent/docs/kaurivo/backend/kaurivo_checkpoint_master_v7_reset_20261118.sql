-- V7 checkpoint recovery: only the currently claimed authenticated runner
-- may invalidate its own stale-content checkpoint by exact SHA256.
-- DO NOT relax the monotonic stage record function: stale reset is a
-- separate compare-and-delete privilege, never a silent downgrade.
create or replace function public.kaurivo_worker_checkpoint_reset(
    p_id uuid, p_run_id bigint, p_current_checksum text
) returns boolean
language plpgsql security definer set search_path=''
as $$
begin
  if p_run_id is null or p_run_id<=0 or
     p_current_checksum is null or
     p_current_checksum !~ '^[0-9a-f]{64}$'
  then
    return false;
  end if;
  -- Serialize with checkpoint_record, reject stale runners and terminal jobs.
  perform 1 from public.kaurivo_demo_build_jobs j
  where j.id=p_id and j.github_run_id=p_run_id
    and j.status in ('researching','building','qa')
  for update;
  if not found then
    return false;
  end if;
  -- Exact-digest optimistic concurrency: do not erase a new checkpoint
  -- written by another worker/attempt after this runner restored it.
  delete from public.kaurivo_demo_checkpoints c
  where c.job_id=p_id and c.checksum=p_current_checksum;
  return found;
end;
$$;
revoke all on function public.kaurivo_worker_checkpoint_reset(uuid,bigint,text)
  from public,anon,authenticated;
grant execute on function public.kaurivo_worker_checkpoint_reset(uuid,bigint,text)
  to service_role;

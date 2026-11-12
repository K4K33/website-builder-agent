-- Extend the existing job-scoped PRIVATE, OIDC-authenticated checkpoint API
-- with one non-final research stage. No public read/write permissions change.
-- The edge function and Python archive validation must be deployed together.
alter table public.kaurivo_demo_checkpoints
  drop constraint if exists kaurivo_demo_checkpoints_stage_check;
alter table public.kaurivo_demo_checkpoints
  add constraint kaurivo_demo_checkpoints_stage_check
  check (stage in ('research_partial','researched','concepts','selected',
                   'built','revised_1','revised_2'));

create or replace function public.kaurivo_worker_checkpoint_record(
  p_id uuid, p_run_id bigint, p_stage text, p_checksum text, p_bytes integer
) returns boolean
language plpgsql security definer set search_path=''
as $$
declare old_stage text;
declare old_rank integer;
declare new_rank integer;
begin
 if p_run_id is null or p_run_id<=0
    or p_checksum !~ '^[0-9a-f]{64}$'
    or p_bytes not between 1 and 31457280 then return false; end if;

 new_rank=array_position(array[
  'research_partial','researched','concepts','selected','built',
  'revised_1','revised_2'
 ]::text[],p_stage);
 if new_rank is null then return false; end if;

 -- A different run cannot write to an old claim. All archives are privately
 -- tied to exactly one prospect job with a SHA256-verified object path.
 perform 1 from public.kaurivo_demo_build_jobs j
 where j.id=p_id and j.github_run_id=p_run_id
   and j.status in ('researching','building','qa')
 for update;
 if not found then return false; end if;
 select c.stage into old_stage
 from public.kaurivo_demo_checkpoints c where c.job_id=p_id for update;
 if found then
  old_rank=array_position(array[
   'research_partial','researched','concepts','selected','built',
   'revised_1','revised_2'
  ]::text[],old_stage);
  if old_rank is null or new_rank<old_rank then return false; end if;
 end if;

 insert into public.kaurivo_demo_checkpoints(
   job_id,stage,checksum,object_path,byte_count,last_run_id,updated_at)
 values(p_id,p_stage,p_checksum,p_id::text||'/'||p_checksum||'.zip',
        p_bytes,p_run_id,now())
 on conflict (job_id) do update set
   stage=excluded.stage,checksum=excluded.checksum,
   object_path=excluded.object_path,byte_count=excluded.byte_count,
   last_run_id=excluded.last_run_id,updated_at=now();
 return true;
end;
$$;
revoke all on function public.kaurivo_worker_checkpoint_record(uuid,bigint,text,text,integer)
 from public,anon,authenticated;
grant execute on function public.kaurivo_worker_checkpoint_record(uuid,bigint,text,text,integer)
 to service_role;

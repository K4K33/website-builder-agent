-- Private, bounded, source-faithful stage checkpoints for owner-selected demos.
-- A checkpoint is not a completed website. It cannot bypass fresh QA.
-- All blob bytes live in a PRIVATE Supabase Storage bucket, never public Git.
insert into storage.buckets(id,name,public,file_size_limit,allowed_mime_types)
values('kaurivo-demo-checkpoints','kaurivo-demo-checkpoints',false,31457280,
       array['application/zip']::text[])
on conflict (id) do nothing;

create table if not exists public.kaurivo_demo_checkpoints (
 job_id uuid primary key references public.kaurivo_demo_build_jobs(id) on delete cascade,
 stage text not null check (stage in
   ('researched','concepts','selected','built','revised_1','revised_2')),
 checksum text not null check (checksum ~ '^[0-9a-f]{64}$'),
 object_path text not null,
 byte_count integer not null check (byte_count between 1 and 31457280),
 last_run_id bigint not null,
 updated_at timestamptz not null default now(),
 constraint kaurivo_checkpoint_exact_object_path check (
   object_path=job_id::text||'/'||checksum||'.zip')
);
alter table public.kaurivo_demo_checkpoints enable row level security;
revoke all on public.kaurivo_demo_checkpoints from public,anon,authenticated;
grant all on public.kaurivo_demo_checkpoints to service_role;

-- Access to Storage operations is granted only to the exact OIDC-verified
-- GitHub/main run that currently owns an active job; never to browser/admin JWT.
create or replace function public.kaurivo_worker_checkpoint_can_write(
 p_id uuid,p_run_id bigint
) returns boolean
language sql security definer set search_path=''
as $$
 select exists (
  select 1 from public.kaurivo_demo_build_jobs j
  where j.id=p_id and j.github_run_id=p_run_id
  and p_run_id>0 and j.status in ('researching','building','qa')
 );
$$;
revoke all on function public.kaurivo_worker_checkpoint_can_write(uuid,bigint)
 from public,anon,authenticated;
grant execute on function public.kaurivo_worker_checkpoint_can_write(uuid,bigint)
 to service_role;

create or replace function public.kaurivo_worker_checkpoint_get(
 p_id uuid,p_run_id bigint
) returns table(stage text, checksum text, object_path text, byte_count integer)
language sql security definer set search_path=''
as $$
 select c.stage,c.checksum,c.object_path,c.byte_count
 from public.kaurivo_demo_checkpoints c
 join public.kaurivo_demo_build_jobs j on j.id=c.job_id
 where c.job_id=p_id and j.github_run_id=p_run_id and p_run_id>0
 and j.status in ('researching','building','qa');
$$;
revoke all on function public.kaurivo_worker_checkpoint_get(uuid,bigint)
 from public,anon,authenticated;
grant execute on function public.kaurivo_worker_checkpoint_get(uuid,bigint)
 to service_role;

create or replace function public.kaurivo_worker_checkpoint_record(
 p_id uuid,p_run_id bigint,p_stage text,p_checksum text,p_bytes integer
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
  'researched','concepts','selected','built','revised_1','revised_2'
 ]::text[],p_stage);
 if new_rank is null then return false; end if;

 -- Row lock prevents a previous worker from advancing the new run.
 perform 1 from public.kaurivo_demo_build_jobs j
 where j.id=p_id and j.github_run_id=p_run_id
   and j.status in ('researching','building','qa')
 for update;
 if not found then return false; end if;
 select c.stage into old_stage
 from public.kaurivo_demo_checkpoints c where c.job_id=p_id for update;
 if found then
  old_rank=array_position(array[
   'researched','concepts','selected','built','revised_1','revised_2'
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
revoke all on function public.kaurivo_worker_checkpoint_record(
 uuid,bigint,text,text,integer) from public,anon,authenticated;
grant execute on function public.kaurivo_worker_checkpoint_record(
 uuid,bigint,text,text,integer) to service_role;

-- Storage RLS: no anon/authenticated user can list/read/write checkpoint objects.
-- Storage service-role calls are made only *after* GitHub OIDC + DB run checks.

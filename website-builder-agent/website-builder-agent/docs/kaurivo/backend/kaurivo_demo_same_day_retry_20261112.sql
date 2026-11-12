CREATE OR REPLACE FUNCTION public.kaurivo_worker_update_demo(p_id uuid, p_run_id bigint, p_status text, p_progress text DEFAULT ''::text, p_preview_url text DEFAULT ''::text, p_qa_url text DEFAULT ''::text, p_release_sha text DEFAULT ''::text, p_error_code text DEFAULT ''::text)
 RETURNS boolean
 LANGUAGE plpgsql
 SECURITY DEFINER
 SET search_path TO ''
AS $function$
declare previous_status text;
declare worker_kind text;
declare current_day_claims integer;
declare next_attempt timestamptz;
begin
 select j.status,j.runner_kind,j.retry_claims_today
 into previous_status,worker_kind,current_day_claims
 from public.kaurivo_demo_build_jobs j
 where j.id=p_id and j.github_run_id=p_run_id for update;
 if not found or previous_status not in
   ('researching','building','qa','publishing') then return false; end if;
 if p_status='queued' then
   if p_error_code not in
      ('free_ai_capacity_unavailable','free_ai_rate_limit',
       'research_network_unavailable','network_unavailable',
       'source_http_rate_limited','stage_timeout','runner_stale_timeout')
      then return false; end if;
   if current_day_claims>=3 or p_error_code='free_ai_capacity_unavailable' then
     next_attempt:=(date_trunc('day',now() at time zone 'UTC')
                          +interval '1 day 10 minutes') at time zone 'UTC';
   elsif p_error_code='free_ai_rate_limit' then
     -- A temporary provider limit can clear during this same day.
     next_attempt:=now()+case when current_day_claims=1 then interval '10 minutes'
                              else interval '25 minutes' end;
   elsif p_error_code='source_http_rate_limited' then
     next_attempt:=now()+interval '35 minutes';
   else next_attempt:=now()+interval '15 minutes'; end if;
   update public.kaurivo_demo_build_jobs
   set status='queued',progress=left(coalesce(p_progress,''),300),
       error_code=p_error_code,next_eligible_at=next_attempt,
       finished_at=null,updated_at=now()
   where id=p_id;
   return true;
 end if;
 if p_status not in ('researching','building','qa','publishing',
                     'internal_preview','hold','failed') then return false; end if;
 if p_status='internal_preview' then
   if previous_status not in ('qa','publishing')
     or p_preview_url !~ '^https://(k4k33[.]github[.]io|[A-Za-z0-9-]+[.]onrender[.]com)/'
     or p_release_sha !~ '^[0-9a-f]{40}$' then return false; end if;
   if worker_kind='local' then
     if p_qa_url !~ '^https://kaurivo-auto-demos-2026[.]onrender[.]com/[a-z0-9-]+/qa[.]html$'
       or replace(p_qa_url,'/qa.html','/index.html')<>p_preview_url
       then return false; end if;
   elsif p_qa_url !~ '^https://github[.]com/K4K33/website-builder-agent/actions/runs/[0-9]+$'
      then return false;
   end if;
 end if;
 update public.kaurivo_demo_build_jobs
 set status=p_status,progress=left(coalesce(p_progress,''),300),
     preview_url=case when p_status='internal_preview' then p_preview_url else preview_url end,
     qa_url=case when p_status='internal_preview' then p_qa_url else qa_url end,
     release_sha=case when p_status='internal_preview' then p_release_sha else release_sha end,
     error_code=case when p_status in ('hold','failed') then left(p_error_code,100) else '' end,
     finished_at=case when p_status in ('internal_preview','hold','failed') then now() else finished_at end,
     updated_at=now()
 where id=p_id;
 return true;
end;
$function$
;

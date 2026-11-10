-- Ensure runner death/cancellation never leaves a demo marked 'rakenteilla' forever.
-- Called at each 5-minute OIDC worker claim; never auto retries stale designs.
create or replace function public.kaurivo_worker_claim_demo(
 p_run_id bigint,p_run_url text
) returns table(
 id uuid,company_name text,business_id text,original_url text,
 website_language text
) language plpgsql security definer set search_path = ''
as $$
declare record_id uuid;
begin
 if p_run_id is null or p_run_id<=0
 or p_run_url <> ('https://github.com/K4K33/website-builder-agent/actions/runs/'||p_run_id::text)
 then raise exception 'invalid worker identity' using errcode='22023';
 end if;
 update public.kaurivo_demo_build_jobs j
 set status='hold',error_code='runner_stale_timeout',
     progress='Rakennustyö keskeytyi tai ei saanut valmista tarkistusta. Vaatii uuden yrityskohtaisen tarkistuksen.',
     finished_at=now(),updated_at=now()
 where j.status in ('researching','building','qa','publishing')
   and j.updated_at<now()-interval '70 minutes';
 select j.id into record_id from public.kaurivo_demo_build_jobs j
 where j.status='queued' order by j.created_at
 for update skip locked limit 1;
 if record_id is null then return; end if;
 update public.kaurivo_demo_build_jobs j
 set status='researching',
     progress='Tutkitaan yritystä ja alkuperäistä verkkosivua',
     github_run_id=p_run_id,github_run_url=p_run_url,
     started_at=now(),updated_at=now(),attempt=attempt+1
 where j.id=record_id;
 return query select j.id,j.company_name,j.business_id,j.original_url,j.website_language
 from public.kaurivo_demo_build_jobs j where j.id=record_id;
end;
$$;
revoke all on function public.kaurivo_worker_claim_demo(bigint,text) from public,anon,authenticated;
grant execute on function public.kaurivo_worker_claim_demo(bigint,text) to service_role;

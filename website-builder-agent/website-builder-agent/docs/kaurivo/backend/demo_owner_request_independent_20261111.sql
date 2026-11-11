-- 2026-11-11: The admin's explicit private demo request is independent of
-- commercial/lead eligibility. No selected business is emailed or published.
-- Do not gate queueing on delayed/broken free-model provider health: the
-- exact free-only GitHub worker independently verifies credentials BEFORE AI.
-- An unsuccessful source audit or QA never produces a 'ready' preview.
create or replace function public.kaurivo_request_demo_build(p_prospect_id uuid)
returns uuid
language plpgsql
security definer
set search_path = ''
as $$
declare
 p record;
 old_id uuid;
 made_id uuid;
 chosen_url text;
 chosen_language text;
begin
 if (select kaurivo_internal.is_kaurivo_admin()) is not true then
   raise exception 'not authorized' using errcode = '42501';
 end if;
 select id, business_id, company_name, marketing_opt_out,
        website_found_url, website_listed_url, website_candidate_url,
        website_languages, review_status
 into p
 from public.kaurivo_crm_prospects
 where id=p_prospect_id
 for share;
 if not found then
   raise exception 'company not found' using errcode = '22023';
 end if;
 -- Owner's explicit demo instruction is independent of SALES selection,
 -- prior skip state, marketing permission and potential customer solvency.
 -- Outreach and contact permissions are enforced by separate gates.
 select id into old_id from public.kaurivo_demo_build_jobs
 where prospect_id=p_prospect_id and status in
   ('queued','researching','building','qa','publishing')
 order by created_at desc limit 1;
 if old_id is not null then return old_id; end if;
 -- The free-provider constraint belongs to the WORKER, not the button.
 -- Every owner request is recorded in the queue; models stay FREE_ONLY.
 chosen_url := coalesce(nullif(trim(p.website_found_url), ''),
                        nullif(trim(p.website_listed_url), ''),
                        nullif(trim(p.website_candidate_url), ''), '');
 -- Unusable registry links must not prevent the owner from requesting work.
 -- The worker will research independently, then require real source evidence.
 if chosen_url <> '' and
    (chosen_url !~ '^https://[A-Za-z0-9]' or
      chosen_url ~ '[[:space:]@]' or char_length(chosen_url)>1500) then
    chosen_url := '';
 end if;
 chosen_language := coalesce(nullif(trim(p.website_languages), ''),
                              'undetermined');
 -- Missing websites remain legitimate research jobs, but the worker must
 -- prove an independent verified-no-site source before generating a website.
 insert into public.kaurivo_demo_build_jobs(
   prospect_id,requested_by,business_id,company_name,original_url,
   website_language,status,progress)
 values (
   p_prospect_id,(select auth.uid()),p.business_id,p.company_name,
   chosen_url,chosen_language,'queued',
   case when chosen_url='' then
     'Jonossa: selvitetään alkuperäinen sivu tai julkinen yritysaineisto'
   else 'Jonossa: alkuperäinen verkkosivu tutkitaan ennen rakentamista' end
 )
 returning id into made_id;
 return made_id;
exception
 when unique_violation then
   select id into old_id from public.kaurivo_demo_build_jobs
   where prospect_id=p_prospect_id and status in
   ('queued','researching','building','qa','publishing')
   order by created_at desc limit 1;
   if old_id is not null then return old_id; end if;
   raise;
end;
$$;

create or replace function public.kaurivo_demo_require_healthy_worker()
returns trigger language plpgsql security invoker set search_path = ''
as $$
begin
 return new;
end;
$$;


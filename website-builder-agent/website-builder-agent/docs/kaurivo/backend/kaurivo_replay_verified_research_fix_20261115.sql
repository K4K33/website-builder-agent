-- Keep the daily cap for routine retries and provider failures. A privileged
-- operator can separately requeue a saved research job after deploying a fix.
-- The claim consumes its one-shot marker atomically with the normal row lock.
-- Neither the authenticated admin UI nor the worker retry endpoint can set it.
DO $migration$
DECLARE
    original text := pg_get_functiondef(
        'public.kaurivo_worker_claim_specific_demo(bigint,text,uuid)'::regprocedure
    );
    previous constant text := $old$
      and j.retry_day=utc_today and j.retry_claims_today=3
      and j.cloud_recovery_day is distinct from utc_today
      and exists (
        select 1 from public.kaurivo_demo_checkpoints c
        where c.job_id=j.id and c.stage='research_partial')$old$;
    updated constant text := $new$
      and exists (
        select 1 from public.kaurivo_demo_checkpoints c
        where c.job_id=j.id and c.stage='research_partial')$new$;
BEGIN
    IF has_table_privilege('authenticated', 'public.kaurivo_demo_build_jobs', 'UPDATE')
       OR has_function_privilege('authenticated',
           'public.kaurivo_worker_claim_specific_demo(bigint,text,uuid)', 'EXECUTE')
    THEN
        RAISE EXCEPTION 'Kaurivo research recovery must remain server-only';
    END IF;
    IF strpos(original, previous) = 0 THEN
        IF strpos(original, 'and j.error_code=''research_fix_deployed''
      and j.next_eligible_at<=now()' || updated) > 0 THEN
            RETURN;
        END IF;
        RAISE EXCEPTION 'Unexpected Kaurivo private claim function';
    END IF;
    IF (length(original) - length(replace(original, previous, ''))) <> length(previous)
    THEN
        RAISE EXCEPTION 'Ambiguous Kaurivo research recovery clause';
    END IF;
    EXECUTE replace(original, previous, updated);
END $migration$;

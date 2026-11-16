-- Permit the existing server-only verified-fix marker to restore a job
-- whose research has passed and whose concept page drafts were checkpointed.
-- Ordinary retries and provider quotas are still enforced independently.
DO $migration$
DECLARE
    original text := pg_get_functiondef(
        'public.kaurivo_worker_claim_specific_demo(bigint,text,uuid)'::regprocedure
    );
    previous constant text := $old$and j.error_code='research_fix_deployed'
      and j.next_eligible_at<=now()
      and exists (
        select 1 from public.kaurivo_demo_checkpoints c
        where c.job_id=j.id and c.stage='research_partial')$old$;
    updated constant text := replace(previous,
        $$c.stage='research_partial'$$, $$c.stage in ('research_partial','researched')$$);
BEGIN
    IF has_table_privilege('authenticated', 'public.kaurivo_demo_build_jobs', 'UPDATE')
       OR has_table_privilege('anon', 'public.kaurivo_demo_build_jobs', 'UPDATE')
       OR has_function_privilege('authenticated',
           'public.kaurivo_worker_claim_specific_demo(bigint,text,uuid)', 'EXECUTE')
       OR has_function_privilege('anon',
           'public.kaurivo_worker_claim_specific_demo(bigint,text,uuid)', 'EXECUTE')
    THEN
        RAISE EXCEPTION 'Kaurivo verified-fix recovery must remain server-only';
    END IF;
    IF strpos(original, updated) > 0 THEN
        RETURN;
    END IF;
    IF (length(original) - length(replace(original, previous, ''))) <> length(previous)
    THEN
        RAISE EXCEPTION 'Unexpected Kaurivo verified-fix claim clause';
    END IF;
    EXECUTE replace(original, previous, updated);
END $migration$;

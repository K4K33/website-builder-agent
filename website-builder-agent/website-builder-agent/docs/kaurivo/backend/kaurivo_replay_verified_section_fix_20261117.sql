-- Allow a server-issued, inspected code-fix replay to restore a checkpoint
-- containing an independently selected design and a blocked final build.
-- This never permits an unverified client to bypass quotas or the browser gates.
DO $migration$
DECLARE
    original text := pg_get_functiondef(
      'public.kaurivo_worker_claim_specific_demo(bigint,text,uuid)'::regprocedure);
    previous constant text := $$c.stage in ('research_partial','researched','concepts')$$;
    updated constant text := $$c.stage in ('research_partial','researched','concepts','selected')$$;
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
        RAISE EXCEPTION 'Unexpected Kaurivo verified-fix checkpoint clause';
    END IF;
    EXECUTE replace(original, previous, updated);
END $migration$;

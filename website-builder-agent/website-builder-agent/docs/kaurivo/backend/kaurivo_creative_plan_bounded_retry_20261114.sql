-- Apply to Kaurivo production once, only AFTER matching Edge OIDC allowlist.
-- Extend the EXISTING current security-definer update function by precisely
-- one recoverable creative-plan error. Preserve the deployed runner_kind,
-- local QA URL checks, quota backoff and all original security permissions.
-- No table data, job status, daily quota, RLS or other function changes.
DO $migration$
DECLARE
    old_definition text;
    new_definition text;
    old_fragment constant text :=
        '''source_http_rate_limited'',''stage_timeout'',''runner_stale_timeout''';
    new_fragment constant text :=
        '''source_http_rate_limited'',''stage_timeout'',''runner_stale_timeout'',''research_creative_plan_needs_repair''';
BEGIN
    SELECT pg_get_functiondef(p.oid) INTO old_definition
    FROM pg_proc p JOIN pg_namespace n ON n.oid=p.pronamespace
    WHERE n.nspname='public' AND p.proname='kaurivo_worker_update_demo'
      AND pg_get_function_identity_arguments(p.oid) LIKE '%p_error_code%'
    LIMIT 1;
    IF old_definition IS NULL THEN
        RAISE EXCEPTION 'Kaurivo private demo update function missing';
    END IF;
    IF position(new_fragment IN old_definition) > 0 THEN
        RAISE NOTICE 'Creative plan retry allowlist already applied';
        RETURN;
    END IF;
    IF position(old_fragment IN old_definition) = 0
       OR (length(old_definition) - length(replace(old_definition,old_fragment,''))) / length(old_fragment) <> 1
    THEN
        RAISE EXCEPTION 'Unexpected Kaurivo live update function: manual review required';
    END IF;
    new_definition := replace(old_definition,old_fragment,new_fragment);
    EXECUTE new_definition;
END $migration$;

-- This function remains private to service_role as it was before.
-- Existing 3-claims-per-day, RLS and exact GitHub OIDC are unchanged.

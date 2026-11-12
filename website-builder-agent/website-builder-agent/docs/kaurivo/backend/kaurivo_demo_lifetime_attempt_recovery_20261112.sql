-- Kaurivo: preserve a lifetime count without imposing an obsolete 3-job-attempt
-- ceiling. The previous constraint attempt<=3 caused a 503 on a valid cloud
-- continuation after three local Codex claims. Daily limits are enforced by
-- kaurivo_worker_claim_specific_demo using retry_day/retry_claims_today.
-- This migration never resets or deletes a job, its audit history, QA or source.
alter table public.kaurivo_demo_build_jobs
  drop constraint if exists kaurivo_demo_build_jobs_attempt_check;
alter table public.kaurivo_demo_build_jobs
  add constraint kaurivo_demo_build_jobs_attempt_check check (attempt >= 0);

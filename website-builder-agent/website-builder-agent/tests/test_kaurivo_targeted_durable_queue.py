"""Safeguards for exact owner-selected demo and durable *bounded* retries.

All tests are offline; no CRM/API credentials, GitHub jobs or AI usage.
"""
from pathlib import Path
import unittest
from scripts.run_kaurivo_demo_queue import TRANSIENT_RETRY_CODES

ROOT=Path(__file__).resolve().parents[1]
FLOW=ROOT.parents[1]/".github/workflows/kaurivo-demo-worker.yml"
SITE=ROOT/"docs/kaurivo"
DURABLE=SITE/"backend/kaurivo_targeted_durable_worker_20261111.sql"
EDGE=SITE/"backend/demo_worker_edge.ts"
DISPATCH=SITE/"backend/demo_immediate_dispatch_edge.ts"
PANEL=SITE/"assets/demo-jobs.js"
RUNNER=ROOT/"scripts/run_kaurivo_demo_queue.py"


class KaurivoDurableQueueSafetyTests(unittest.TestCase):
    def test_one_click_targets_selected_job_not_oldest_other_client(self):
        dispatch=DISPATCH.read_text(encoding="utf-8")
        bridge=EDGE.read_text(encoding="utf-8")
        flow=FLOW.read_text(encoding="utf-8")
        sql=DURABLE.read_text(encoding="utf-8")
        self.assertIn('inputs:{job_id:jobId}',dispatch)
        self.assertIn('job_id:',flow)
        self.assertIn('REQUESTED_JOB_ID: ${{ inputs.job_id',flow)
        self.assertIn('CLAIM_BODY=',flow)
        self.assertIn('kaurivo_worker_claim_specific_demo',bridge)
        self.assertIn('p_job_id:data.job_id',bridge)
        self.assertIn('p_job_id is null or j.id=p_job_id',sql)
        self.assertIn('for update skip locked limit 1',sql)
        # A new runner claim still requires EXACT allowed GitHub OIDC claims.
        self.assertIn('jwtVerify(',bridge)
        self.assertIn('WORKFLOW_REF',bridge)
        self.assertIn('repository_owner_id',bridge)
        self.assertIn('repository_id',bridge)
        self.assertIn('payload.ref!=="refs/heads/main"',bridge)
        self.assertIn('"workflow_dispatch"',bridge)
        self.assertNotIn('SUPABASE_SERVICE_ROLE_KEY:',flow)

    def test_scheduled_backup_uses_same_scoped_lock_without_job_override(self):
        flow=FLOW.read_text(encoding="utf-8")
        sql=DURABLE.read_text(encoding="utf-8")
        self.assertIn('"schedule"',EDGE.read_text(encoding="utf-8"))
        self.assertIn('CLAIM_BODY=\'{"action":"claim"}\'',flow)
        self.assertIn('kaurivo_worker_claim_specific_demo(p_run_id,p_run_url,null::uuid)',sql)

    def test_retries_continue_across_days_with_strict_daily_bounds(self):
        sql=DURABLE.read_text(encoding="utf-8")
        self.assertIn('retry_claims_today<3',sql)
        self.assertIn('retry_day is distinct from utc_today',sql)
        self.assertIn('retry_claims_today+1',sql)
        self.assertIn('retry_day=utc_today',sql)
        self.assertIn('next_eligible_at<=now()',sql)
        self.assertNotIn('j.attempt<3',sql)
        self.assertNotIn('previous_attempt>=3',sql)
        self.assertIn('runner_stale_timeout',sql)
        self.assertIn('interval \'70 minutes\'',sql)
        self.assertIn('interval \'1 day 10 minutes\'',sql)
        self.assertIn('interval \'35 minutes\'',sql)
        self.assertIn('interval \'15 minutes\'',sql)
        self.assertIn("p_error_code='free_ai_capacity_unavailable'",sql)
        self.assertIn("p_status='queued'",sql)
        self.assertIn('status=\'queued\'',sql)
        # No automatic success without exact trusted evidence.
        self.assertIn('p_status=\'internal_preview\'',sql)
        self.assertIn('p_release_sha !~',sql)
        self.assertIn('p_qa_url !~',sql)

    def test_retries_only_known_transient_not_bad_qa_or_made_up_source(self):
        accepted={
            "free_ai_capacity_unavailable","free_ai_rate_limit",
            "research_network_unavailable","network_unavailable",
            "source_http_rate_limited","stage_timeout",
            "runner_stale_timeout","research_creative_plan_needs_repair",
        }
        self.assertEqual(TRANSIENT_RETRY_CODES,accepted)
        for bad in ("quality_gate_not_approved","source_research_incomplete",
                    "remote_image_rights_not_proven","source_http_access_blocked",
                    "free_ai_key_invalid","building_failed"):
            self.assertNotIn(bad,TRANSIENT_RETRY_CODES)
        text=RUNNER.read_text(encoding="utf-8")
        self.assertIn('if error.code in TRANSIENT_RETRY_CODES:',text)
        self.assertIn('update("queued"',text)
        self.assertIn('save_private_checkpoint("built"',text)
        self.assertIn('restore_private_checkpoint(',text)
        self.assertIn('update("internal_preview"',text)
        bridge=EDGE.read_text(encoding="utf-8")
        self.assertIn('"free_ai_rate_limit"',bridge)
        self.assertIn('"source_http_rate_limited"',bridge)
        self.assertIn('"stage_timeout"',bridge)
        self.assertIn('"research_creative_plan_needs_repair"',bridge)
        self.assertIn("'research_creative_plan_needs_repair'",
                      DURABLE.read_text(encoding="utf-8"))
        self.assertIn('invalid_defer_code',bridge)

    def test_private_admin_and_no_billable_models(self):
        sql=DURABLE.read_text(encoding="utf-8")
        self.assertIn('to service_role',sql)
        self.assertIn('from public,anon,authenticated',sql)
        self.assertNotIn('grant execute on function public.kaurivo_worker_claim_specific_demo(bigint,text,uuid)\n to authenticated',sql)
        flow=FLOW.read_text(encoding="utf-8")
        self.assertIn('FREE_ONLY: "1"',flow)
        self.assertIn('OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}',flow)
        self.assertIn('cache: pip',flow)
        self.assertIn('run-name:',flow)
        panel=PANEL.read_text(encoding="utf-8")
        self.assertIn('Jatkuu automaattisesti',panel)
        self.assertIn('Vanhat tarkistuspisteet säilyvät',panel)
        self.assertNotIn('service_role',panel)


if __name__=="__main__":
    unittest.main()

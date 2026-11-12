"""Cloud-first Kaurivo demo queue regression tests (offline, no AI tokens).

The owner's laptop cannot run Ollama; the cloud worker must not be blocked
by an old/unverified Codex heartbeat. Owner jobs retain their real QA gates.
"""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/"docs/kaurivo"
SQL=(SITE/"backend/kaurivo_cloud_first_recovery_20261112.sql").read_text(encoding="utf-8")
JS=(SITE/"assets/demo-jobs.js").read_text(encoding="utf-8")
HTML=(SITE/"admin/index.html").read_text(encoding="utf-8")
RUNNER=(ROOT/"scripts/run_kaurivo_demo_queue.py").read_text(encoding="utf-8")
FLOW=(ROOT.parents[1]/".github/workflows/kaurivo-demo-worker.yml").read_text(encoding="utf-8")


class CloudFirstDemoTests(unittest.TestCase):
    def test_unverified_codex_daemon_does_not_block_cloud_claim(self):
        self.assertIn("d.inference_backend='ollama'", SQL)
        self.assertIn("d.ai_ready=true", SQL)
        self.assertNotIn("where d.ai_ready=true and d.expires_at>now()",SQL)
        self.assertIn("d.last_seen_at>now()-interval '55 seconds'",SQL)
        self.assertIn("kaurivo_worker_claim_specific_demo",SQL)

    def test_only_one_previous_local_quota_job_can_be_recovered_per_utc_day(self):
        for required in (
            "cloud_recovery_day date", "j.runner_kind='local'",
            "j.error_code in ('free_ai_rate_limit','free_ai_capacity_unavailable')",
            "j.retry_claims_today>=3",
            "j.cloud_recovery_day is distinct from utc_today",
            "then utc_today else j.cloud_recovery_day end",
            "retry_claims_today+1", "retry_day=utc_today",
            "for update skip locked limit 1",
        ):
            with self.subTest(required=required):
                self.assertIn(required,SQL)
        self.assertIn("(p_job_id is null or j.id=p_job_id)",SQL)
        self.assertIn("where j.runner_kind='github'",SQL)

    def test_oidc_targeting_and_restricted_database_privileges_remain(self):
        self.assertIn("p_run_url <> ('https://github.com/K4K33/",SQL)
        self.assertIn("p_run_id is null or p_run_id<=0",SQL)
        self.assertIn("security definer set search_path=''",SQL)
        self.assertIn("from public,anon,authenticated",SQL)
        self.assertIn("to service_role",SQL)
        self.assertNotIn("to authenticated;", SQL)
        self.assertIn('inputs:{job_id:jobId}',(SITE/"backend/demo_immediate_dispatch_edge.ts").read_text(encoding="utf-8"))

    def test_ui_is_cloud_first_without_installing_local_ai(self):
        self.assertIn("const CLOUD_FIRST=true;",JS)
        self.assertIn("if(!CLOUD_FIRST)",JS)
        self.assertIn("Pilvirakentaja käytössä",JS)
        self.assertIn('"Jatka pilvessä"',JS)
        self.assertIn("cloudRecovery",JS)
        self.assertIn("cloud_recovery_day",JS)
        self.assertIn('verifyBuildStart(options.db,job.id)',JS)
        self.assertIn("demo-jobs.js?v=20261112-cloud-first4",HTML)
        self.assertNotIn("window.open(",JS)
        self.assertNotIn("service_role",JS)

    def test_cloud_stays_free_and_premium_qa_stays_fail_closed(self):
        self.assertIn('FREE_ONLY: "1"',FLOW)
        self.assertIn("AI_BACKEND: openrouter",FLOW)
        self.assertIn("OPENROUTER_API_KEY: ${{ secrets.OPENROUTER_API_KEY }}",FLOW)
        self.assertIn("Known exhausted free daily quota:",FLOW)
        for evidence in ("save_private_checkpoint(", "restore_private_checkpoint(",
                         "quality_gate_not_approved",
                         "quality_gate_build_version_mismatch",
                         "verify_public(url,marker,routes)",
                         'update("internal_preview"'):
            self.assertIn(evidence,RUNNER)


if __name__=="__main__":
    unittest.main()

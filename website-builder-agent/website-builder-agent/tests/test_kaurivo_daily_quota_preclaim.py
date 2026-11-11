"""Regression: never claim a production job on a provably empty free-day budget.

Offline source assertions; does not use any account, AI credits or API token.
"""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[3]
FLOW=ROOT/".github/workflows/kaurivo-demo-worker.yml"
WORKER=Path(__file__).resolve().parents[1]/"scripts/run_kaurivo_demo_queue.py"


class DailyQuotaClaimGuards(unittest.TestCase):
    def test_no_job_claim_if_key_returns_zero_remaining(self):
        workflow=FLOW.read_text(encoding="utf-8")
        self.assertIn("https://openrouter.ai/api/v1/key",workflow)
        self.assertIn('free_model_daily_requests',workflow)
        self.assertIn('remaining<=0',workflow)
        self.assertIn('free_quota_empty',workflow)
        self.assertLess(workflow.index('if [[ "${{ steps.keycheck.outputs.free_quota_empty }}" == "true" ]]'),
                        workflow.index('--data \'{"action":"claim"}\''))
        self.assertIn('has_job=false',workflow)
        self.assertIn('RESEARCH_FALLBACK_MODELS',workflow)
        self.assertIn('BUILDER_FALLBACK_MODELS',workflow)
        self.assertIn('QA_FALLBACK_MODELS',workflow)

    def test_worker_still_uses_private_resume_and_mandatory_qa(self):
        script=WORKER.read_text(encoding="utf-8")
        self.assertIn('restore_private_checkpoint(',script)
        self.assertIn('save_private_checkpoint("researched"',script)
        self.assertIn('save_private_checkpoint("built"',script)
        self.assertIn('run_cli(["qa",agent_slug]',script)
        self.assertIn('verify_public(url,marker,routes)',script)
        self.assertIn('config.stage_model_candidates(phase)',script)


if __name__=="__main__":
    unittest.main()

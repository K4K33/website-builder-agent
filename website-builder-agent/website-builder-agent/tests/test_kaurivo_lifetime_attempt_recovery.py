"""Prevent Kaurivo from reintroducing the 3-attempt lifetime job deadlock."""
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[1]
SQL=(ROOT/"docs/kaurivo/backend/kaurivo_demo_lifetime_attempt_recovery_20261112.sql").read_text(encoding="utf-8")
QUEUE=(ROOT/"docs/kaurivo/backend/kaurivo_cloud_first_recovery_20261112.sql").read_text(encoding="utf-8")
RUNNER=(ROOT/"scripts/run_kaurivo_demo_queue.py").read_text(encoding="utf-8")

class LifetimeAttemptRecoveryTests(unittest.TestCase):
    def test_audit_attempts_can_exceed_three_without_erasing_history(self):
        self.assertIn("drop constraint if exists kaurivo_demo_build_jobs_attempt_check",SQL)
        self.assertIn("check (attempt >= 0)",SQL)
        self.assertNotIn("check (attempt <= 3)",SQL.lower())
        self.assertNotIn("update public.kaurivo_demo_build_jobs",SQL.lower())
        self.assertNotIn("delete from",SQL.lower())

    def test_daily_bounded_retries_and_qa_remain(self):
        self.assertIn("retry_claims_today<3",QUEUE)
        self.assertIn("j.cloud_recovery_day is distinct from utc_today",QUEUE)
        self.assertIn("retry_claims_today+1",QUEUE)
        self.assertIn("for update skip locked limit 1",QUEUE)
        self.assertIn("quality_gate_build_version_mismatch",RUNNER)
        self.assertIn("verify_public(url,marker,routes)",RUNNER)

if __name__=="__main__":
    unittest.main()

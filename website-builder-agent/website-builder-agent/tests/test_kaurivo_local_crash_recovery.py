"""The local daemon must not mark a crashed builder as still running.

Only local source and mock behavior are used here. No API keys, demos, cloud
charges, GitHub dispatches or customer records are accessed.
"""
from pathlib import Path
import unittest
from unittest.mock import Mock,patch

from scripts.kaurivo_local_worker import execute_claim

BASE=Path(__file__).resolve().parents[1]
EDGE=(BASE/"docs/kaurivo/backend/demo_worker_edge.ts").read_text(encoding="utf-8")
SQL=(BASE/"docs/kaurivo/backend/kaurivo_local_crash_recovery_20261112.sql").read_text(
    encoding="utf-8")
DAEMON=(BASE/"scripts/kaurivo_local_worker.py").read_text(encoding="utf-8")
PANEL=(BASE/"docs/kaurivo/assets/demo-jobs.js").read_text(encoding="utf-8")
UUID="22111111-2222-4333-8444-555555555555"


class LocalCrashRecoveryTests(unittest.TestCase):
    def test_subprocess_success_releases_only_exact_active_job(self):
        active={"id":None}
        with patch("scripts.kaurivo_local_worker.run_claim") as child,\
             patch("scripts.kaurivo_local_worker.server",return_value={
                 "ok":True,"requeued":False}) as rpc:
            execute_claim(Mock(),"kvl_"+"a"*64,{"id":UUID},2000000000000123,
                          {"builder":"model","qa":"vision"},active)
        self.assertIsNone(active["id"])
        child.assert_called_once()
        self.assertEqual(rpc.call_args.args[2],"release")
        self.assertEqual(rpc.call_args.kwargs,{"job_id":UUID})

    def test_crashed_subprocess_releases_before_propagating_failure(self):
        active={"id":None}
        with patch("scripts.kaurivo_local_worker.run_claim",
                   side_effect=OSError("simulated exit")) as child,\
             patch("scripts.kaurivo_local_worker.server",return_value={
                 "ok":True,"requeued":True}) as rpc:
            with self.assertRaises(OSError):
                execute_claim(Mock(),"kvl_"+"a"*64,{"id":UUID},
                              2000000000000123,{},active)
        self.assertIsNone(active["id"])
        child.assert_called_once()
        self.assertEqual(rpc.call_args.kwargs["job_id"],UUID)

    def test_idle_daemon_does_not_keep_failed_build_alive(self):
        self.assertIn('const leaseActive=typeof data.job_id==="string"',EDGE)
        self.assertIn('"kaurivo_local_worker_heartbeat"',EDGE)
        self.assertIn('"kaurivo_local_worker_release"',EDGE)
        fn=SQL.split("create or replace function public.kaurivo_local_worker_validate(")[1].split("$$;")[0]
        self.assertNotIn("update public.kaurivo_demo_build_jobs",fn)
        self.assertIn("j.id=p_id and j.github_run_id=p_run_id",SQL)
        self.assertIn("j.runner_kind='local'",SQL)
        self.assertIn('active_job={"id":None}',DAEMON)
        self.assertIn('**({"job_id":lease} if lease else {})',DAEMON)

    def test_release_only_requeues_active_not_qa_approved_or_hard_hold(self):
        section=SQL.split("create or replace function public.kaurivo_local_worker_release(")[1]
        section=section.split("$$;")[0]
        self.assertIn("j.status in ('researching','building','qa','publishing')",section)
        self.assertNotIn("'internal_preview'",section)
        self.assertNotIn("'hold'",section)
        self.assertNotIn("'failed'",section)
        self.assertIn("retry_claims_today>=3",section)
        self.assertIn("next_eligible_at",section)
        self.assertIn("runner_stale_timeout",section)
        self.assertIn("return found_id is not null",section)

    def test_idle_worker_sweeps_stale_leases_even_without_github(self):
        claim=SQL.split("create or replace function public.kaurivo_local_worker_claim(")[1]
        self.assertIn("updated_at<now()-interval '70 minutes'",claim)
        self.assertIn("status='queued'",claim)
        self.assertIn("for update skip locked limit 1",claim)
        self.assertIn("retry_claims_today<3",claim)
        self.assertIn("kaurivo_local_worker_claim",EDGE)

    def test_windows_enrollment_survives_admin_refresh_without_storage(self):
        self.assertIn('let pendingWindowsToken=""',PANEL)
        self.assertIn("if(pendingWindowsToken)",PANEL)
        self.assertIn("showWindowsToken(container,pendingWindowsToken",PANEL)
        self.assertIn('pendingWindowsToken="";input.value=""',PANEL)
        self.assertNotIn("localStorage.setItem",PANEL)
        self.assertNotIn("sessionStorage.setItem",PANEL)


if __name__=="__main__":
    unittest.main()

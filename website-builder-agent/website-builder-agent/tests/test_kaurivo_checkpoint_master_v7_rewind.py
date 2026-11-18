"""Stale V7 checkpoint reset must remain exact-job, exact-SHA and authenticated."""
from pathlib import Path
import unittest

BASE=Path(__file__).resolve().parents[1]
SQL=(BASE/"docs/kaurivo/backend/kaurivo_checkpoint_master_v7_reset_20261118.sql").read_text()
EDGE=(BASE/"docs/kaurivo/backend/demo_worker_edge.ts").read_text()
RUNNER=(BASE/"scripts/run_kaurivo_demo_queue.py").read_text()
PREVIOUS=(BASE/"docs/kaurivo/backend/kaurivo_research_partial_checkpoint_20261112.sql").read_text()


class V7CheckpointRewindTests(unittest.TestCase):
    def test_sql_explicit_claim_and_checksum_guards(self):
        self.assertIn("kaurivo_worker_checkpoint_reset",SQL)
        self.assertIn("j.github_run_id=p_run_id",SQL)
        self.assertIn("j.status in ('researching','building','qa')",SQL)
        self.assertIn("c.checksum=p_current_checksum",SQL)
        self.assertIn("for update;",SQL)
        self.assertIn("return found;",SQL)
        self.assertIn("from public,anon,authenticated",SQL)
        self.assertIn("to service_role;",SQL)
        self.assertNotIn("grant execute on function public.kaurivo_worker_checkpoint_reset(uuid,bigint,text) to authenticated",SQL)
        # Existing strict monotonic progression stays untouched.
        self.assertIn("if old_rank is null or new_rank<old_rank then return false;",PREVIOUS)

    def test_edge_checks_exact_previous_sha_after_authentication(self):
        self.assertIn('if(data.action==="checkpoint_reset")',EDGE)
        self.assertIn('Object.keys(data).length!==3',EDGE)
        self.assertIn('current.checksum!==data.checksum',EDGE)
        self.assertIn('kaurivo_worker_checkpoint_can_write',EDGE)
        self.assertIn('p_current_checksum:data.checksum',EDGE)
        self.assertIn('const {payload,protectedHeader}=await jwtVerify',EDGE)
        self.assertIn('payload.ref!=="refs/heads/main"',EDGE)
        self.assertIn("checkpoint_not_claimed",EDGE)
        self.assertNotIn("SUPABASE_SERVICE_ROLE_KEY",str(BASE/"docs/kaurivo/assets/demo-jobs.js"))

    def test_runner_research_and_strict_gates_repaired(self):
        self.assertIn('needs_research_restart(',RUNNER)
        self.assertIn('current_checkpoint.get("stage") != resume',RUNNER)
        self.assertIn('reset_reply=call_worker(',RUNNER)
        self.assertIn('resume = None',RUNNER)
        self.assertIn('run_cli(["research",agent_slug]',RUNNER)
        self.assertIn('verify_design_handoff(load_company(agent_slug),selected=False)',RUNNER)
        self.assertIn('verify_public(url,marker,routes)',RUNNER)


if __name__=="__main__":
    unittest.main()

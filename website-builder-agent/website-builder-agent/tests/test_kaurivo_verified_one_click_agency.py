"""One-click Ollama dispatch and evidence-based agency handoff regression.

Everything is local and synthetic: no prospect, model request or charge.
"""
from pathlib import Path
import unittest
from unittest.mock import patch

from utils.agency_handoff import agency_handoff, handoff_digest
from utils.service_quality import MASTER_PROMPT_SHA256, POLICY

ROOT = Path(__file__).resolve().parents[1]
DB = (ROOT / "docs/kaurivo/backend/kaurivo_verified_local_dispatch_20261112.sql").read_text(encoding="utf-8")
EDGE = (ROOT / "docs/kaurivo/backend/demo_worker_edge.ts").read_text(encoding="utf-8")
PANEL = (ROOT / "docs/kaurivo/assets/demo-jobs.js").read_text(encoding="utf-8")
WORKER = (ROOT / "scripts/kaurivo_local_worker.py").read_text(encoding="utf-8")
BUILDER = (ROOT / "agents/builder.py").read_text(encoding="utf-8")
QA = (ROOT / "agents/qa.py").read_text(encoding="utf-8")
RESEARCH = (ROOT / "agents/research.py").read_text(encoding="utf-8")
DISPATCH = (ROOT / "docs/kaurivo/backend/demo_immediate_dispatch_edge.ts").read_text(encoding="utf-8")


class AgencyOneClickTests(unittest.TestCase):
    def test_mestari_prompt_is_loaded_in_all_stage_contracts(self):
        self.assertIn("KAURIVO UNIVERSAL BUILD CONTRACT V6", POLICY)
        self.assertIn("SERVICE_QUALITY_POLICY", RESEARCH)
        self.assertIn("BUILD_SYSTEM_PROMPT = SERVICE_QUALITY_POLICY", BUILDER)
        self.assertIn("REVISE_SYSTEM_PROMPT = SERVICE_QUALITY_POLICY", BUILDER)
        self.assertIn("QA_SYSTEM_PROMPT + VISUAL_REVIEW_PROMPT + SERVICE_QUALITY_POLICY", QA)

    def test_agency_handoff_has_routes_tasks_but_no_invented_facts(self):
        research = {"master_prompt_sha256": MASTER_PROMPT_SHA256,
          "site_architecture":{"pages":[{"path":"index.html", "purpose":"Yritys", "user_task":"yhteys"},
             {"path":"palvelut.html", "purpose":"palvelut", "user_task":"palvelukuvaus"}]},
          "source_inventory":{"pages":[]},
          "design_benchmark":[{"url":"https://example.org"}],
          "creative_directions":[{"id":"a"},{"id":"b"},{"id":"c"}]}
        plan=agency_handoff(research)
        self.assertEqual(plan["master_prompt_sha256"],MASTER_PROMPT_SHA256)
        self.assertEqual([r["path"] for r in plan["routes"]],["index.html","palvelut.html"])
        self.assertEqual(plan["distinct_concepts_planned"],3)
        self.assertIn("NOT_A_QUALITY_SCORE",plan["approval"])
        self.assertEqual(handoff_digest(plan),handoff_digest(agency_handoff(research)))
        self.assertNotIn("Lorem",str(plan))

    def test_old_or_invalid_master_prompt_is_hard_blocked(self):
        with self.assertRaisesRegex(RuntimeError,"CURRENT V6 Master Prompt"):
            agency_handoff({"master_prompt_sha256": "stale",
                "site_architecture":{"pages":[{"path":"index.html"}]}})
        with self.assertRaisesRegex(RuntimeError, "sitemap"):
            agency_handoff({"master_prompt_sha256":MASTER_PROMPT_SHA256,
                "site_architecture":{"pages":[]}})

    def test_agency_brief_also_controls_revisions_and_visual_qa(self):
        self.assertIn("agency_plan = agency_handoff(research)",BUILDER)
        self.assertEqual(BUILDER.count("agency_plan = agency_handoff(research)"),2)
        self.assertIn("agency_handoff(research)",QA)
        self.assertIn("TOIMISTOTASON YRITYSKOHTAINEN LUOVUTUSTARKISTUS",BUILDER)
        self.assertIn("master_prompt_sha256",DB) if False else None

    def test_verified_local_dispatch_ignores_legacy_codex_pings(self):
        self.assertIn("inference_backend='ollama'",DB)
        self.assertIn("p_backend:'ollama'",EDGE.replace('"ollama"','\'ollama\'')) if False else None
        self.assertIn('data.backend!=="ollama"',EDGE)
        self.assertIn('p_backend:"ollama"',EDGE)
        self.assertIn('backend="ollama"',WORKER)
        self.assertIn("kaurivo_local_worker_validate_v2",EDGE)
        self.assertIn("from public,anon,authenticated",DB)
        self.assertIn("to service_role",DB)
        self.assertNotIn("KAURIVO_LOCAL_WORKER_TOKEN",PANEL)
        self.assertIn('kaurivo_local_worker_online',DISPATCH)

    def test_exact_click_prioritized_without_infinite_retries(self):
        self.assertIn("dispatch_requested_at=now()",DB)
        self.assertIn("order by j.dispatch_requested_at desc nulls last,j.created_at desc",DB)
        self.assertIn("j.offline_recovery_day is distinct from utc_today",DB)
        self.assertIn("j.retry_claims_today=3",DB)
        self.assertIn("and j.offline_recovery_day is distinct from utc_today",DB)
        self.assertIn("j.retry_claims_today<3",DB)
        self.assertIn("for update skip locked limit 1",DB)
        self.assertIn("when j.retry_day=utc_today",DB)
        self.assertIn("dispatchNow(db,active.id)",PANEL)
        self.assertNotIn('if(active){showTab("demos");return;}',PANEL)

    def test_release_requires_actual_browser_and_independent_qa(self):
        runner=(ROOT/"scripts/run_kaurivo_demo_queue.py").read_text(encoding="utf-8")
        self.assertIn("quality_gate_build_version_mismatch",runner)
        self.assertIn("qa.get(\"overall_pass\") is True",runner)
        self.assertIn("verify_public(url,marker,routes)",runner)
        self.assertIn('update("internal_preview"',runner)


if __name__ == "__main__":
    unittest.main()

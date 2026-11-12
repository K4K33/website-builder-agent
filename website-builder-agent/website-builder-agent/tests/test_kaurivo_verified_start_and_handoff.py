"""Kaurivo professional design preflight + real-start UI safety regressions.

Runs without customer sources, Supabase, model calls or paid credentials.
"""
from pathlib import Path
import os
import unittest
from unittest.mock import patch
from scripts import run_kaurivo_demo_queue as demo_queue

from utils.agency_preflight import verify_design_handoff, safe_preflight_reason
from utils.creative_directions import FIELDS
from utils.service_quality import MASTER_PROMPT_SHA256

ROOT = Path(__file__).resolve().parents[1]
RUNNER = (ROOT/"scripts/run_kaurivo_demo_queue.py").read_text(encoding="utf-8")
PANEL = (ROOT/"docs/kaurivo/assets/demo-jobs.js").read_text(encoding="utf-8")
HTML = (ROOT/"docs/kaurivo/admin/index.html").read_text(encoding="utf-8")

def example_company():
    directions = []
    for i in range(3):
        item = {key: "Distinct business anchored design decisions " + key
                for key in FIELDS}
        item["id"] = "concept-" + str(i)
        directions.append(item)
    return {
        "url": "https://example.fi",
        "research": {
            "master_prompt_sha256": MASTER_PROMPT_SHA256,
            "company_facts": {"name": "Test business", "industry": "testing"},
            "source_inventory": {"pages": [{"url": "https://example.fi",
                                          "text": "Verified test source"}]},
            "site_architecture": {"pages": [{
                "path": "index.html",
                "purpose": "Show evidence-backed company services",
                "user_task": "Find and request a service at this business",
                "section_ids": ["home", "services"]}]},
            "design_benchmark": [{}, {}, {}],
            "creative_directions": directions,
            "creative_selection": {"selected_id": "concept-0"},
        },
    }


class AgencyPreflightTests(unittest.TestCase):
    def test_master_prompt_stale_research_is_rejected_not_published(self):
        company=example_company()
        company["research"]["master_prompt_sha256"]="old-version"
        with self.assertRaisesRegex(RuntimeError, "CURRENT V6 Master Prompt"):
            verify_design_handoff(company)

    def test_three_company_specific_directions_and_references_are_mandatory(self):
        company=example_company()
        company["research"]["creative_directions"].pop()
        with patch("utils.agency_preflight.validate_source_plan"), \
             patch("utils.agency_preflight.validate_brand_preservation_plan"), \
             patch("utils.agency_preflight.validate_design_plan"), \
             patch("utils.agency_preflight.validate_site_architecture",
                   return_value={"page_paths":["index.html"]}):
            with self.assertRaisesRegex(RuntimeError, "three distinct concepts"):
                verify_design_handoff(company)

    def test_separate_research_and_selected_art_direction_guards(self):
        company=example_company()
        with patch("utils.agency_preflight.validate_source_plan") as source, \
             patch("utils.agency_preflight.validate_brand_preservation_plan") as brand, \
             patch("utils.agency_preflight.validate_design_plan") as benchmark, \
             patch("utils.agency_preflight.validate_site_architecture",
                   return_value={"page_paths":["index.html"]}) as sitemap, \
             patch("utils.agency_preflight.validate_creative_directions") as choice, \
             patch("utils.agency_preflight.derive_brand_site_blueprint",
                   return_value={"sitemap_and_wireframes":[{"route":"index.html"}]}) as blueprint:
            handoff=verify_design_handoff(company)
            self.assertEqual(handoff["industry_references_evidenced"],3)
            self.assertTrue(handoff["routes"])
            choice.assert_not_called()
            blueprint.assert_not_called()
            verify_design_handoff(company,selected=True)
            source.assert_called_with(company["research"],source_url="https://example.fi")
            brand.assert_called_with(company["research"])
            benchmark.assert_called_with(company["research"],target_url="https://example.fi")
            sitemap.assert_called()
            choice.assert_called_once_with(company["research"])
            blueprint.assert_called_once_with(company["research"])

    def test_broken_selected_art_direction_fails_before_build(self):
        company=example_company()
        with patch("utils.agency_preflight.validate_source_plan"), \
             patch("utils.agency_preflight.validate_brand_preservation_plan"), \
             patch("utils.agency_preflight.validate_design_plan"), \
             patch("utils.agency_preflight.validate_site_architecture",
                   return_value={"page_paths":["index.html"]}), \
             patch("utils.agency_preflight.validate_creative_directions",
                   side_effect=RuntimeError("not a real winner")):
            with self.assertRaisesRegex(RuntimeError, "not a real winner"):
                verify_design_handoff(company, selected=True)

    def test_direct_local_runner_rejects_codex_backend(self):
        with patch.object(demo_queue, "LOCAL_WORKER", True), \
             patch.dict(os.environ, {"FREE_ONLY":"1", "AI_BACKEND":"codex"}):
            with self.assertRaisesRegex(demo_queue.HoldError, "local_models_required"):
                demo_queue.free_model_configured()

    def test_private_source_urls_never_leave_the_preflight_gate(self):
        raw = RuntimeError("Source content missing from https://private.example/secret")
        self.assertEqual(safe_preflight_reason(raw), "original_source")
        self.assertNotIn("private.example", safe_preflight_reason(raw))
        self.assertEqual(safe_preflight_reason(
            RuntimeError("Canonical Master Prompt outdated")), "master_prompt_version")

    def test_worker_enforces_handoff_when_restoring_checkpoints(self):
        self.assertIn("verify_design_handoff(load_company(agent_slug),selected=False)",RUNNER)
        self.assertIn("verify_design_handoff(load_company(agent_slug),selected=True)",RUNNER)
        self.assertIn('HoldError("design_handoff_incomplete","research:"+safe_preflight_reason(exc))',RUNNER)
        self.assertIn('HoldError("design_handoff_incomplete","selected_concept:"+safe_preflight_reason(exc))',RUNNER)
        self.assertLess(RUNNER.index('selected=False)'),
                        RUNNER.index('run_cli(["concept-previews"'))
        self.assertLess(RUNNER.index('selected=True)'),
                        RUNNER.index('run_cli(["build"'))
        self.assertIn('quality_gate_build_version_mismatch',RUNNER)

    def test_ui_reports_real_claim_only_not_dispatch_acceptance(self):
        self.assertIn('async function verifyBuildStart(db,jobId)',PANEL)
        self.assertIn('.select("status").eq("id",jobId).maybeSingle()',PANEL)
        self.assertIn('if(data.status==="internal_preview")return "ready";',PANEL)
        self.assertIn('if(["hold","failed"].includes(data.status))return "blocked";',PANEL)
        self.assertIn('return "queued";',PANEL)
        self.assertIn('dispatchFeedback(dispatch,toast,confirmed)',PANEL)
        self.assertIn('dispatchFeedback(result,toast,confirmed)',PANEL)
        self.assertIn('dispatchFeedback(status,options.toast,confirmed)',PANEL)
        self.assertIn('demo-jobs.js?v=20261112-openrouter-status5',HTML)
        self.assertNotIn("Rakennustyö valmis","Rakenna demo")

if __name__=="__main__":
    unittest.main()

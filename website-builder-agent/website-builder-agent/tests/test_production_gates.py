"""Offline production gates: no OpenRouter, Tavily, external websites or paid AI calls."""
import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

import config
import main
from agents import builder, qa
from utils import publisher, state

HTML = """<!doctype html><html lang="fi"><head><title>Demo yritys</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Demo yritys"></head>
<body><header><nav><a href="#main">Etusivu</a></nav></header>
<main id="main"><h1>Demo yritys</h1><p>Huolellinen paikallinen palvelu.</p></main>
<footer>Yhteystiedot pyydettäessä.</footer></body></html>"""

URLS = ["https://a-reference.fi", "https://b-reference.fi", "https://c-reference.fi"]
DIMENSIONS = ("first_view", "service_hierarchy", "contact_path", "mobile")


def research_fixture(directory, industry):
    image = Path(directory) / "reference.png"
    image.write_bytes(b"offline fixture: the AI call is mocked, not a real image")
    refs = [
        {"url": url, "screenshots": {"desktop": str(image), "mobile": str(image)},
         "site_text": "The operator provides the same industry service.",
         "industry_match": {"same_industry": True, "target_industry": industry,
                            "reason": "Same sector", "evidence_quote": "same industry service"},
         "observations": ["Visible services"], "apply": ["Clear hierarchy"],
         "avoid": ["Never copy claims"]}
        for url in URLS
    ]
    decisions = [
        {"id": name, "dimension": name, "reference_url": URLS[i % 3],
         "observation": "Visible services", "adaptation": "Target-specific hierarchy",
         "section_id": "main", "acceptance_check": "Main content visible"}
        for i, name in enumerate(DIMENSIONS)
    ]
    return {
        "company_facts": {"name": "Demo yritys", "industry": industry},
        "design_benchmark": refs, "design_decisions": decisions,
        "design_recommendations": {"motion_plan": {
            "purpose": "Clarity", "implementation": "Static intentionally",
            "reduced_motion": "All content remains visible", "verification": "Inspect desktop and mobile"}}
    }


def approved_review():
    return {"content_ok": True, "issues": [],
            "reference_comparison": {"reviewed_urls": URLS, "company_specific": True,
                                      "remaining_gaps": [], "ready_for_client_review": True},
            "design_checks": [{"id": name, "passed": True, "evidence": "Visible main content"}
                              for name in DIMENSIONS],
            "visual_review": {
                **{name: 90 for name in ("desktop", "tablet", "mobile", "small_mobile",
                                        "brand_specificity", "typography", "hierarchy",
                                        "art_direction", "imagery", "motion")},
                "blockers": [], "improvements": []}}


class ProductionGates(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.data = self.root / "data"
        self.output = self.root / "output"
        for key, value in (("DATA_DIR", str(self.data)),
                           ("COMPANIES_FILE", str(self.data / "companies.json")),
                           ("OUTPUT_DIR", str(self.output))):
            scope = patch.object(config, key, value)
            scope.start()
            self.addCleanup(scope.stop)
        self.cwd = os.getcwd()
        os.chdir(self.root)
        self.addCleanup(os.chdir, self.cwd)

    def create_build(self, industry="transport", slug="demo"):
        state.upsert_company(slug, {
            "name": "Demo yritys", "url": "https://demo-example.fi", "status": "researched",
            "research": research_fixture(self.root, industry)
        })
        path = builder._write_html(slug, HTML)
        state.upsert_company(slug, {"status": "built", "build": {
            "version": 1, "output_path": str(path), "generation_mode": "offline_fixture"}})
        return Path(path)

    def qa_and_approve(self):
        with patch.object(qa, "ask_claude_json", return_value=approved_review()):
            result = qa.run_qa("demo")
        if any("Browser QA unavailable" in issue for issue in result["browser"]["issues"]):
            if os.getenv("REQUIRE_BROWSER_TESTS") == "1":
                self.fail(str(result["browser"]["issues"]))
            self.skipTest("Chromium missing locally")
        self.assertTrue(result["overall_pass"], result)
        qa.approve_company("demo")
        return result

    def test_authorization_blocks_live_calls_before_lookup(self):
        args = SimpleNamespace(confirm_live_run=False)
        with patch.object(main.scout, "run_scout") as scout:
            with self.assertRaisesRegex(RuntimeError, "confirm-live-run"):
                main.cmd_pipeline(args)
            scout.assert_not_called()

    def test_unapproved_cannot_publish(self):
        self.create_build()
        with self.assertRaisesRegex(RuntimeError, "QA"):
            publisher.publish_site("demo")

    def test_approved_site_publishes_only_unchanged_bytes(self):
        path = self.create_build()
        result = self.qa_and_approve()
        record = state.get_company("demo")[1]
        self.assertEqual(record["approval"]["build_version"], 1)
        self.assertEqual(record["approval"]["html_sha256"], hashlib.sha256(path.read_bytes()).hexdigest())
        self.assertEqual(result["html_sha256"], record["approval"]["html_sha256"])
        url = publisher.publish_site("demo")
        self.assertIn("/demos/demo/", url)
        self.assertEqual((self.root / "docs/demos/demo/index.html").read_bytes(), path.read_bytes())
        path.write_text(HTML + "<!-- changed after approval -->")
        with self.assertRaisesRegex(RuntimeError, "changed since QA"):
            publisher.publish_site("demo")

    def test_approval_rejects_post_qa_changes(self):
        path = self.create_build()
        with patch.object(qa, "ask_claude_json", return_value=approved_review()):
            result = qa.run_qa("demo")
        if not result["overall_pass"]:
            if os.getenv("REQUIRE_BROWSER_TESTS") == "1":
                self.fail(str(result))
            self.skipTest("Chromium missing locally")
        path.write_text(HTML + "<!-- modified -->")
        with self.assertRaisesRegex(RuntimeError, "muutettu QA"):
            qa.approve_company("demo")

    def test_external_rebuild_revokes_approval(self):
        self.create_build()
        self.qa_and_approve()
        response = self.root / "response.html"
        response.write_text(HTML)
        builder.run_build_from_response("demo", str(response), "offline fixture")
        company = state.get_company("demo")[1]
        self.assertEqual(company["build"]["version"], 2)
        self.assertIsNone(company["qa"])
        self.assertIsNone(company["approval"])
        self.assertIsNone(company["outreach"])
        with self.assertRaisesRegex(RuntimeError, "QA"):
            publisher.publish_site("demo")

    def test_offline_pipeline_failure_exits_nonzero(self):
        args = SimpleNamespace(confirm_live_run=True, count=1,
                               industry="ravintola", location="Tampere", max_revisions=0)
        state.upsert_company("demo", {"name": "Demo yritys", "url": "https://demo-example.fi"})
        with patch.object(config, "model_for_stage", return_value="fixed/mock"), \
             patch.dict(os.environ, {"OPENROUTER_API_KEY": "fixture", "TAVILY_API_KEY": "fixture"}), \
             patch.object(main.scout, "run_scout", return_value=[{"slug": "demo"}]), \
             patch.object(main.research, "run_research"), \
             patch.object(main.builder, "run_build"), \
             patch.object(main.qa, "run_qa", return_value={"overall_pass": False, "browser": {"issues": []}, "content_review": {}}):
            with self.assertRaisesRegex(RuntimeError, "failed QA"):
                main.cmd_pipeline(args)


if __name__ == "__main__":
    unittest.main()

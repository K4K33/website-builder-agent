"""One bounded source-preserving independent review repair, no publish bypass."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from tests.test_concept_previews import fixture, fake_renderer
from utils.concept_previews import write_concepts, load_verified_set, blind_order
from utils.kaurivo_staged_visual_review import VisualReviewRevisionRequired
from utils.kaurivo_visual_review_recovery import revise_one_rejected_direction


class VisualReviewRecoveryTests(unittest.TestCase):
    def test_revises_only_rejected_route_and_creates_new_immutable_browser_proof(self):
        research, original = fixture()
        with TemporaryDirectory() as temp:
            root = Path(temp)
            ref = write_concepts(
                json.dumps(original), research,
                output_parent=root / "_concept_previews",
                producer="external-fixture-builder", renderer=fake_renderer)
            path, manifest = load_verified_set(ref, research, allowed_root=root)
            order = blind_order(manifest)
            selected = order["A"]
            target_route = selected["views"][0]["route"]
            reviews = {
                "A": {"passing_views": 3, "critical_issues": [],
                      "source_comparison": "The original company logo and "
                         "dark palette appear in desktop and mobile screen "
                         "views and are retained in the concept."},
                "B": {"passing_views": 2, "critical_issues": [],
                      "source_comparison": "Verified source comparison with both original screens."},
                "C": {"passing_views": 1, "critical_issues": [],
                      "source_comparison": "Verified source comparison with both original screens."},
            }
            assessments = {}
            for alias, entry in order.items():
                for index, view in enumerate(entry["views"]):
                    assessments[view["id"]] = {
                        "verdict": "needs_revision" if alias != "A" or index == 0 else "pass",
                        "brand_evidence": "Official client brand source palette remains intact.",
                        "composition_evidence": "Responsive layout requires more consistent hierarchy.",
                        "media_evidence": "Real source imagery remains visible in page content.",
                    }
            rejection = VisualReviewRevisionRequired(reviews, assessments)
            calls = []

            def fake_draft(**kwargs):
                calls.append(kwargs)
                self.assertEqual(len(kwargs["routes"]), 1)
                route = kwargs["routes"][0]
                self.assertEqual(route, target_route)
                packet = json.loads(kwargs["prompt_for"](route))
                self.assertEqual(packet["route"], target_route)
                self.assertEqual(packet["direction"]["id"], selected["id"])
                self.assertIn("independent_critique", packet)
                content = packet["current_html"]
                return {route: content.replace(
                    "</style>", "/* source-preserving visual revision */</style>")}

            with patch.dict("os.environ",
                            {"KAURIVO_QUEUED_DEMO_ID": "review-test-job"}), \
                 patch("utils.demo_page_drafts.draft_pages",
                       side_effect=fake_draft), \
                 patch("utils.browser_qa.inspect_site",
                       side_effect=fake_renderer) as browser, \
                 patch("utils.kaurivo_visual_review_recovery.upsert_company") as saved, \
                 patch("utils.kaurivo_visual_review_recovery.config.MEDIA_INTAKE_DIR",
                       root):
                refreshed, new_path, new_manifest = revise_one_rejected_direction(
                    slug="studio", company={"media_intake": None},
                    reference=ref, research=research, manifest=manifest,
                    order=order, critique=rejection, root=root)
            self.assertEqual(len(calls), 1)
            self.assertEqual(refreshed["status"], "ready_for_comparison")
            self.assertNotEqual(new_path, path)
            self.assertTrue(path.is_file())
            self.assertEqual(len(browser.call_args_list), 6)
            self.assertEqual(len(new_manifest["entries"]), 3)
            self.assertEqual(sum(len(e["views"]) for e in new_manifest["entries"]), 12)
            self.assertIn("concept_previews", saved.call_args.args[1])
            self.assertNotIn("selection_sha256", refreshed)
            self.assertNotIn("premium_approval", refreshed)


    def test_repairs_new_contrast_after_model_fixes_browser_overflow(self):
        def renderer(file, **kwargs):
            from bs4 import BeautifulSoup

            report = fake_renderer(file, **kwargs)
            html = file.read_text(encoding="utf-8")
            if "min-width:1200px" in html:
                report["issues"] = ["mobile: horizontal overflow"]
            elif 'style="color:#bbb;background-color:#fff"' in html:
                node = BeautifulSoup(html, "html.parser").find("h1")
                selector = [node.parent.name + ":nth-of-type(1)", "h1:nth-of-type(1)"]
                report["issues"] = ["mobile: measurable WCAG AA text contrast failures: "
                    + json.dumps([{"selector": "body > main:nth-of-type(1) > " + " > ".join(selector),
                                   "tag": "H1", "text": "Instrument Studio",
                                   "suggestedTextColor": "#000000"}])]
            report["pass"] = not report["issues"]
            return report

        self._assert_new_contrast_repaired(renderer)

    def test_repairs_new_measured_contrast_with_chromium(self):
        from utils.browser_qa import inspect_site

        self._assert_new_contrast_repaired(inspect_site)

    def _assert_new_contrast_repaired(self, renderer):
        research, original = fixture()
        with TemporaryDirectory() as temp:
            root = Path(temp)
            ref = write_concepts(
                json.dumps(original), research,
                output_parent=root / "_concept_previews",
                producer="external-fixture-builder", renderer=renderer)
            if any("Browser QA unavailable" in item
                   for by_route in ref["private_repair_evidence"].values()
                   for failures in by_route.values() for item in failures):
                self.skipTest("Chromium is not available in this environment.")
            _, manifest = load_verified_set(ref, research, allowed_root=root)
            order = blind_order(manifest)
            entry = order["A"]
            target_route = entry["views"][0]["route"]
            assessments = {}
            for alias, value in order.items():
                for idx, view in enumerate(value["views"]):
                    assessments[view["id"]] = {
                        "verdict": "needs_revision" if alias != "A" or idx == 0 else "pass",
                        "brand_evidence": "Actual company logo and colors preserved.",
                        "composition_evidence": "One mobile layout remains visually inconsistent.",
                        "media_evidence": "Original company photography remains unchanged.",
                    }
            critique = VisualReviewRevisionRequired(
                {alias: {"passing_views": 3 if alias == "A" else 1,
                         "critical_issues": [],
                         "source_comparison": "The original desktop and mobile "
                             "show the recognizable official brand header and "
                             "photography; these remain in the concept."}
                 for alias in order}, assessments)
            phases = []

            def fake_draft(**kwargs):
                phase = kwargs["phase"]
                phases.append(phase)
                self.assertEqual(kwargs["routes"], [target_route])
                packet = json.loads(kwargs["prompt_for"](target_route))
                page = packet["current_html"]
                if "independent-browser" in phase:
                    self.assertIn("horizontal overflow", str(packet["verified_browser_failures"]))
                    return {target_route: page.replace("main{min-width:1200px}", "")
                            .replace("<h1>", '<h1 style="color:#bbb;background-color:#fff">')}
                return {target_route: page.replace("</style>", "main{min-width:1200px}</style>")}

            with patch.dict("os.environ",
                            {"KAURIVO_QUEUED_DEMO_ID": "review-browser-job"}), \
                 patch("utils.demo_page_drafts.draft_pages",
                       side_effect=fake_draft), \
                 patch("utils.browser_qa.inspect_site", side_effect=renderer), \
                 patch("utils.kaurivo_visual_review_recovery.upsert_company") as saved, \
                 patch("utils.kaurivo_visual_review_recovery.config.MEDIA_INTAKE_DIR",
                       root):
                refreshed, path, built = revise_one_rejected_direction(
                    slug="studio", company={"media_intake": None},
                    reference=ref, research=research, manifest=manifest,
                    order=order, critique=critique, root=root)
            self.assertEqual(refreshed["status"], "ready_for_comparison")
            self.assertEqual(len(phases), 2)
            self.assertIn("independent-visual", phases[0])
            self.assertIn("independent-browser", phases[1])
            self.assertEqual(len(built["entries"]), 3)
            self.assertEqual(sum(len(e["views"]) for e in built["entries"]), 12)
            saved.assert_called_once()
            corrected = next(item for item in built["entries"] if item["id"] == entry["id"])
            html = (path.parent / corrected["folder"] / target_route).read_text(encoding="utf-8")
            self.assertIn("color:#000000 !important", html)
            self.assertIn("Instrument Studio</h1>", html)
            self.assertNotIn("min-width:1200px", html)
            self.assertEqual(
                {item["id"]: item["site_sha256"] for item in manifest["entries"]
                 if item["id"] != entry["id"]},
                {item["id"]: item["site_sha256"] for item in built["entries"]
                 if item["id"] != entry["id"]},
            )

    def test_repair_requires_a_live_private_queue_context(self):
        research, _ = fixture()
        with patch.dict("os.environ", {"KAURIVO_QUEUED_DEMO_ID": ""}):
            with self.assertRaisesRegex(RuntimeError, "private worker required"):
                revise_one_rejected_direction(
                    slug="studio", company={}, reference={}, research=research,
                    manifest={}, order={}, critique=None, root=Path("/tmp"))


if __name__ == "__main__":
    unittest.main()

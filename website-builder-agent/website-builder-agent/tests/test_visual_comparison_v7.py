"""V7 cross-company first-screen visual evidence and bounded repair regressions."""
from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from utils.visual_comparison import build_visual_comparison, VIEWPORTS
from utils.visual_revision import decide_revision


SOURCE = "https://example.org/"


def fixtures(root: Path):
    original, generated = root / "old", root / "new"
    original.mkdir(parents=True, exist_ok=True)
    generated.mkdir(parents=True, exist_ok=True)
    # Hash-only unit tests do not need to load these placeholder bytes into a browser.
    src, dst = {}, {}
    for name, _, _ in VIEWPORTS:
        before = original / (name + ".png")
        after = generated / (name + ".png")
        before.write_bytes(b"not-a-decoded-image:original:" + name.encode())
        after.write_bytes(b"not-a-decoded-image:redesign:" + name.encode())
        src[name], dst[name] = str(before), str(after)
    old_fold = {
        name: {"measured": True, "viewportWidth": width,
               "viewportHeight": height, "firstFoldVisibleMediaArea": 75000}
        for name, width, height in VIEWPORTS
    }
    new_fold = {
        name: {"measured": True, "viewportWidth": width,
               "viewportHeight": height, "firstFoldVisibleMediaArea": 0,
               "heroHasCssBackground": False}
        for name, width, height in VIEWPORTS
    }
    src["first_fold_observations"] = old_fold
    dst = {"screenshots": dst, "first_fold_observations": new_fold}
    research = {
        "company_facts": {"name": "Synthetic Florist", "industry": "kukkakauppa"},
        "source_inventory": {"pages": [{
            "url": SOURCE, "source_identity": {
                "original_content_photos": [{"src": SOURCE + "flowers.jpg"}],
            },
        }]},
    }
    return src, dst, research, original


class VisualComparisonTests(unittest.TestCase):
    def test_four_matching_screens_produce_private_evidence_manifest(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            src, new, research, original = fixtures(root)
            result = build_visual_comparison(
                src, new, {"index.html": "<main>Flowers</main>"}, research,
                report_dir=root/"private", render_panels=False,
                source_capture_root=original,
            )
            self.assertEqual(result["status"], "repair_suggested")
            self.assertEqual(set(result["pairs"]), {name for name, _, _ in VIEWPORTS})
            self.assertEqual(len(result["repair_hints"]), 2)
            self.assertTrue(Path(result["comparison_html"]).is_file())
            manifest = json.loads(Path(result["report_path"]).read_text("utf-8"))
            self.assertEqual(len(manifest["pairs"]), 4)
            self.assertEqual(len(manifest["pairs"]["mobile"]["original_sha256"]), 64)
            self.assertEqual(manifest["build_sha256"], result["build_sha256"])
            self.assertNotIn("independent score", str(result.get("quality_score")))

    def test_missing_screenshot_cannot_be_silently_declared_verified(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            src, new, research, original = fixtures(root)
            del src["small_mobile"]
            report = build_visual_comparison(
                src, new, {"index.html": "<main>Flowers</main>"}, research,
                report_dir=root/"private", render_panels=False,
                source_capture_root=original,
            )
            self.assertEqual(report["status"], "review_required")
            self.assertIn("Original small_mobile screenshot missing.", report["missing"])

    def test_original_image_cannot_be_loaded_from_arbitrary_local_directory(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            src, new, research, original = fixtures(root)
            src["mobile"] = str((root / "outside.png"))
            (root / "outside.png").write_bytes(b"secrets")
            report = build_visual_comparison(
                src, new, {"index.html": "<main>Flowers</main>"}, research,
                report_dir=root/"private", render_panels=False,
                source_capture_root=original,
            )
            self.assertEqual(report["status"], "review_required")
            self.assertNotIn("mobile", report["pairs"])

    def test_text_first_service_business_is_not_forced_to_use_flower_hero(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            src, new, research, original = fixtures(root)
            research["company_facts"]["industry"] = "kirjanpitopalvelut"
            report = build_visual_comparison(
                src, new, {"index.html": "<main>Services</main>"}, research,
                report_dir=root/"private", render_panels=False,
                source_capture_root=original,
            )
            self.assertEqual(report["status"], "paired_for_human_review")
            self.assertEqual(report["repair_hints"], [])

    def test_css_photo_background_is_a_review_not_false_media_block(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            src, new, research, original = fixtures(root)
            for view in new["first_fold_observations"].values():
                view["heroHasCssBackground"] = True
            report = build_visual_comparison(
                src, new, {"index.html": "<main>Flowers</main>"}, research,
                report_dir=root/"private", render_panels=False,
                source_capture_root=original,
            )
            self.assertFalse(report["repair_hints"])
            self.assertTrue(report["human_comparison_required"])

    def test_real_chromium_pair_image_is_rendered_from_real_viewports(self):
        from playwright.sync_api import sync_playwright
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            src, new, research, original = fixtures(root)
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                try:
                    page = browser.new_page(viewport={"width": 320, "height": 740})
                    page.set_content("<main style='height:740px;background:#ffddee'>Old</main>")
                    page.screenshot(path=src["small_mobile"], full_page=True)
                    page.set_content("<main style='height:740px;background:#661122;color:white'>New</main>")
                    page.screenshot(path=new["screenshots"]["small_mobile"], full_page=True)
                    page.close()
                finally:
                    browser.close()
            # Other 3 placeholder images may fail to decode: the successful
            # small_mobile comparison must still be preserved, failures explicit.
            result = build_visual_comparison(
                src, new, {"index.html": "<main>Flowers</main>"}, research,
                report_dir=root/"private", render_panels=True,
                source_capture_root=original,
            )
            paired = result["pairs"]["small_mobile"].get("comparison_image")
            self.assertTrue(paired, result)
            self.assertGreater(Path(paired).stat().st_size, 100)
            self.assertTrue(result["render_errors"])

    def test_no_original_website_does_not_fabricate_comparison(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            src, new, research, original = fixtures(root)
            research["source_inventory"] = {"pages": []}
            result = build_visual_comparison(
                {}, new, {"index.html": "<main>Services</main>"}, research,
                report_dir=root/"private", render_panels=False,
                source_capture_root=original,
            )
            self.assertEqual(result["status"], "no_original_site")
            self.assertFalse(result["human_comparison_required"])


class BoundedRevisionTests(unittest.TestCase):
    def test_actionable_visual_regression_yields_one_revision(self):
        qa = {"overall_pass": False,
              "visual_comparison": {
                  "status": "repair_suggested",
                  "comparison_html": "local-visual-report.html",
                  "repair_hints": [{
                      "viewport": "mobile", "kind": "source_photo_hidden",
                      "suggestion": "Real florist photos are not visible on the first screen."
                  }],
              }}
        first = decide_revision(qa)
        self.assertTrue(first["revise"])
        self.assertIn("source_photo_hidden",
                      str(first["feedback"]["visual_evidence"]["first_fold_repair_hints"]))
        second = decide_revision(qa, {first["signature"]})
        self.assertFalse(second["revise"])
        self.assertEqual(second["reason"], "no_progress_same_actionable_issues")

    def test_missing_original_images_and_client_approval_never_trigger_paid_retries(self):
        result = decide_revision({"overall_pass": False,
                                  "visual_comparison": {"status": "review_required"},
                                  "automated": {"automated_issues": ["Broken CTA"]}})
        self.assertFalse(result["revise"])
        self.assertEqual(result["reason"], "original_or_new_screenshot_evidence_missing")
        pending = decide_revision({
            "overall_pass": False, "visual_comparison": {"status": "paired_for_human_review"},
            "universal_quality": {"pending_categories": ["approved_domain_and_rights"]},
        })
        self.assertFalse(pending["revise"])
        self.assertEqual(pending["reason"], "only_unverified_human_or_client_evidence")

    def test_multimodal_brand_and_layout_blockers_are_actual_repair_inputs(self):
        result = decide_revision({
            "overall_pass": False,
            "visual_comparison": {"status": "paired_for_human_review"},
            "content_review": {
                "issues": [],
                "visual_review": {"blockers": [
                    "The source's handwritten wordmark became a bold black slogan."
                ]},
                "reference_comparison": {"remaining_gaps": [
                    "Original shop photographs are hidden behind two text sections."
                ]},
            },
        })
        self.assertTrue(result["revise"])
        self.assertEqual(len(result["feedback"]["qa_visual_blockers"]), 1)
        self.assertEqual(len(result["feedback"]["benchmark_remaining_gaps"]), 1)

    def test_specific_browser_failure_can_trigger_repair_without_visual_issue(self):
        result = decide_revision({
            "overall_pass": False,
            "visual_comparison": {"status": "paired_for_human_review"},
            "browser": {"issues": ["mobile: horizontal overflow"]},
        })
        self.assertTrue(result["revise"])
        self.assertIn("horizontal overflow", result["feedback"]["actionable_defects"][0])


if __name__ == "__main__":
    unittest.main()

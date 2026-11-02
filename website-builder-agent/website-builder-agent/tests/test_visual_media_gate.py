"""Free reusable media preflight tests across unrelated industries."""
from pathlib import Path
import struct
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from utils.visual_media_gate import audit_visual_media


class VisualMediaGateTests(unittest.TestCase):
    def test_unverified_external_hero_is_not_owner_preview_ready(self):
        html = (
            '<main><section class="hero">'
            '<img src="https://supplier.example/photo.jpg" alt="Actual work">'
            '</section></main>'
        )
        result = audit_visual_media(html)
        self.assertTrue(result["static_pass"])
        self.assertFalse(result["owner_preview_ready"])
        self.assertTrue(any("remote image unverified" in x
                            for x in result["needs_public_verification"]))
        self.assertTrue(audit_visual_media(
            html, verified_public_images={"https://supplier.example/photo.jpg"}
        )["owner_preview_ready"])

    def test_broken_local_hero_stops_preview(self):
        with TemporaryDirectory() as directory:
            html_path = Path(directory) / "index.html"
            html_path.write_text('<section class="hero"><img src="assets/missing.jpg" alt="Workshop"></section>')
            result = audit_visual_media(html_path.read_text(), html_path=html_path)
            self.assertFalse(result["static_pass"])
            self.assertFalse(result["owner_preview_ready"])
            self.assertIn("missing local image", str(result["blockers"]))

    def test_low_resolution_header_logo_stops_preview(self):
        with TemporaryDirectory() as directory:
            html_path = Path(directory) / "index.html"
            # The width is read from the real PNG header, without guessing
            # from file size or invoking OCR/external image services.
            logo = Path(directory) / "brand.png"
            logo.write_bytes(
                b"\x89PNG\r\n\x1a\n" + b"\x00\x00\x00\x0dIHDR"
                + struct.pack(">II", 96, 48) + b"\x08\x06\x00\x00\x00"
                + b"\x00\x00\x00\x00"
            )
            html = '<header><a class="brand"><img src="brand.png" alt="Company logo"></a></header>'
            result = audit_visual_media(html, html_path=html_path)
            self.assertFalse(result["owner_preview_ready"])
            self.assertIn("96px wide", str(result["blockers"]))

    def test_valid_local_brand_and_text_only_hero_are_allowed(self):
        with TemporaryDirectory() as directory:
            html_path = Path(directory) / "index.html"
            (Path(directory) / "brand.svg").write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 400 100"></svg>'
            )
            html = (
                '<header><a class="brand"><img src="brand.svg" alt="Company logo"></a></header>'
                '<main><section class="hero"><h1>Professional service</h1></section></main>'
            )
            self.assertTrue(audit_visual_media(html, html_path=html_path)["owner_preview_ready"])

    def test_traversal_and_empty_source_are_not_silently_accepted(self):
        with TemporaryDirectory() as directory:
            path = Path(directory) / "index.html"
            html = '<main><img src="../../missing.jpg" alt="A"><img src="" alt="B"></main>'
            result = audit_visual_media(html, html_path=path)
            self.assertEqual(len(result["blockers"]), 2)
            self.assertFalse(result["owner_preview_ready"])

    def test_unverified_hero_blocks_qa_before_any_paid_ai_review(self):
        from agents import qa
        with TemporaryDirectory() as directory:
            page = Path(directory) / "index.html"
            page.write_text(
                '<!doctype html><html lang="fi"><head><title>Sample</title>'
                '<meta name="viewport" content="width=device-width">'
                '<meta name="description" content="Sample"></head>'
                '<body><main><h1>Professional service</h1>'
                '<section class="hero"><img src="https://media.example/hero.jpg"'
                ' alt="Service photo"></section></main></body></html>',
                encoding="utf-8",
            )
            company = {
                "name": "Generic Test Business", "url": "",
                "research": {},
                "build": {"output_path": str(page), "version": 1},
            }
            with (
                patch.object(qa, "get_company", return_value=("generic", company)),
                patch.object(qa, "audit_content_parity",
                             return_value={"pass": True, "missing": [], "review_required": []}),
                patch.object(qa, "audit_universal_standards",
                             return_value={"automated_pass": True, "blocking_problems": {}}),
                patch.object(qa, "_automated_checks",
                             return_value={"automated_pass": True, "automated_issues": []}),
                patch.object(qa, "inspect_site") as browser,
                patch.object(qa, "ask_claude_json") as ai,
                patch.object(qa, "load_ledger", return_value={"issues": {}}),
                patch.object(qa, "save_ledger"),
                patch.object(qa, "record_qa_findings"),
                patch.object(qa, "universal_rules_pending_implementation", return_value=[]),
                patch.object(qa, "upsert_company"),
                patch.object(qa, "set_status"),
            ):
                result = qa.run_qa("generic")
                self.assertFalse(result["overall_pass"])
                self.assertFalse(result["visual_media"]["owner_preview_ready"])
                browser.assert_not_called()
                ai.assert_not_called()

    def test_owner_preview_requires_95_in_each_dimension(self):
        from agents.qa import owner_preview_visual_passes
        dimensions = (
            "desktop", "tablet", "mobile", "small_mobile",
            "brand_specificity", "typography", "hierarchy",
            "art_direction", "imagery", "motion",
        )
        review = {
            "content_ok": True, "issues": [],
            "reference_comparison": {
                "reviewed_urls": ["https://a.example", "https://b.example", "https://c.example"],
                "company_specific": True, "ready_for_client_review": True,
                "remaining_gaps": [],
            },
            "visual_review": {**{dimension: 96 for dimension in dimensions},
                              "blockers": [], "improvements": []},
        }
        self.assertTrue(owner_preview_visual_passes(review))
        review["visual_review"]["imagery"] = 90
        self.assertFalse(owner_preview_visual_passes(review))
        review["visual_review"]["imagery"] = 96
        review["visual_review"]["mobile"] = 94
        self.assertFalse(owner_preview_visual_passes(review))

    def test_no_company_template_is_encoded_in_the_gate(self):
        source = (Path(__file__).resolve().parents[1] /
                  "utils" / "visual_media_gate.py").read_text(encoding="utf-8")
        for company in ("TE-Service", "Rosanne", "RI-LI", "Kotifixi"):
            self.assertNotIn(company, source)


if __name__ == "__main__":
    unittest.main()

"""Free reusable media preflight tests across unrelated industries."""
from pathlib import Path
import struct
from tempfile import TemporaryDirectory
import unittest

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

    def test_no_company_template_is_encoded_in_the_gate(self):
        source = (Path(__file__).resolve().parents[1] /
                  "utils" / "visual_media_gate.py").read_text(encoding="utf-8")
        for company in ("TE-Service", "Rosanne", "RI-LI", "Kotifixi"):
            self.assertNotIn(company, source)


if __name__ == "__main__":
    unittest.main()

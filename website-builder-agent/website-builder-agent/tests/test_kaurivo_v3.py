"""Kaurivo V3 contract tests (zero credits, no duplicate 20-page browser suite).

Comprehensive Playwright browser checks are in test_kaurivo_site_v2.py.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] / "docs" / "kaurivo"
PAGES = ("index.html", "services/index.html", "process/index.html", "faq/index.html", "contact/index.html")
ALIASES = ("services", "process", "faq", "contact")


class V3Tests(unittest.TestCase):
    def test_shared_assets_and_separate_pages(self):
        for name in PAGES:
            with self.subTest(page=name):
                text = (ROOT / name).read_text(encoding="utf-8")
                prefix = "../" if name != "index.html" else ""
                self.assertIn('id="main"', text)
                self.assertIn(prefix + "assets/site-v3.css", text)
                self.assertIn(prefix + "assets/site-v3.js", text)
                self.assertIn(prefix + "assets/kaurivo-mark.webp", text)
                self.assertIn(prefix + "faq/", text)
                self.assertIn(prefix + "contact/", text)
        self.assertGreaterEqual((ROOT / "faq" / "index.html").read_text().count("<details>"), 8)
        self.assertNotIn("<details>", (ROOT / "index.html").read_text())
        self.assertNotIn('id="enquiry-form"', (ROOT / "index.html").read_text())
        self.assertTrue((ROOT / "assets" / "kaurivo-mark.webp").is_file())

    def test_smooth_purposeful_motion_and_accessibility(self):
        css = (ROOT / "assets" / "site-v3.css").read_text()
        js = (ROOT / "assets" / "site-v3.js").read_text()
        self.assertIn("prefers-reduced-motion", css)
        self.assertNotIn("IntersectionObserver", js)
        self.assertIn("@keyframes identity-reveal", css)
        self.assertIn("scroll-behavior:auto", css)
        self.assertIn("delivery-panel", (ROOT / "index.html").read_text())
        self.assertNotIn("pointermove", js)
        self.assertNotIn("pointerleave", js)
        self.assertIn("v4-window", css)
        self.assertIn("prefers-reduced-motion", css)
        self.assertIn("data-stage-button", js)
        self.assertNotIn("getContext(", js)
        self.assertNotIn("WebGL", js)
        self.assertNotIn("420vh", css)
        self.assertIn("transform", css)
        self.assertIn("@keyframes", css)

    def test_legacy_html_urls_redirect_to_current_pages(self):
        for name in ALIASES:
            with self.subTest(alias=name):
                old = (ROOT / (name + ".html")).read_text()
                self.assertIn('http-equiv="refresh"', old)
                self.assertIn('href="' + name + '/"', old)


if __name__ == "__main__":
    unittest.main()

"""Zero-credit regression checks: owner-brand integrity and real demo form.

Remote contact POST verification runs separately, once, in an isolated CI workflow.
"""
from pathlib import Path
from collections import Counter
import re
import unittest
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1] / "docs" / "kaurivo" / "demos" / "kotifixi-v5"
PAGES = ["index.html", "palvelut/index.html", "hinnasto/index.html",
         "meista/index.html", "yhteys/index.html"]


class KotifixiOwnerFeedbackTests(unittest.TestCase):
    def test_no_decorative_arrows_on_any_page(self):
        for rel in PAGES:
            with self.subTest(rel=rel):
                s = (ROOT / rel).read_text(encoding="utf-8")
                for ch in ("↗", "→", "➜", "➝"):
                    self.assertNotIn(ch, s)

    def test_simplified_services_contact_path(self):
        home = BeautifulSoup((ROOT / "index.html").read_text(), "html.parser")
        services = BeautifulSoup((ROOT / "palvelut/index.html").read_text(), "html.parser")
        self.assertIsNone(home.select_one(".process-section"))
        self.assertIsNone(home.select_one(".highlight-section"))
        self.assertEqual(len(home.select(".service-tile")), 3)
        self.assertEqual(len(services.select(".detail-row")), 3)
        self.assertEqual(len(services.select(".detail-row a[href*='yhteys']")), 0)
        self.assertEqual(len(services.select(".muted-cta a[href*='yhteys']")), 1)

    def test_coherent_editorial_photo_selection(self):
        images = []
        for rel in PAGES:
            soup = BeautifulSoup((ROOT / rel).read_text(), "html.parser")
            images.extend(img.get("src", "").split("?")[0] for img in soup.select("img[src]"))
        self.assertEqual(len(images), len(set(images)), "Do not repeat photos")
        self.assertLessEqual(len(images), 2, "Do not fill company with mismatched stock")
        self.assertFalse(any("9462732" in img or "5691544" in img for img in images))

    def test_real_test_backend_replaces_fake_form(self):
        contact = (ROOT / "yhteys/index.html").read_text(encoding="utf-8")
        js = (ROOT / "assets/app.js").read_text(encoding="utf-8")
        self.assertIn("contact-form", contact)
        self.assertIn("test_consent", contact)
        self.assertIn('name="website"', contact)
        self.assertIn("kaurivo-kotifixi-demo-contact", js)
        self.assertIn("fetch(endpoint", js)
        self.assertIn("result.reference", js)
        self.assertIn("test_consent:fd.get", js)
        self.assertNotIn("window.location.href='mailto:", js)
        self.assertNotIn("Avaa sähköpostiviesti", contact)
        self.assertIn("ei lähde Kotifixille", contact)

    def test_preserve_real_name_and_locked_slogan(self):
        for rel in PAGES:
            soup = BeautifulSoup((ROOT / rel).read_text(), "html.parser")
            self.assertEqual(len(soup.select(".site-header a.brand")), 1)
            self.assertIsNone(soup.select_one("svg.brand-logo"))
        self.assertIn("Helpompi arki alkaa meistä.", (ROOT / "index.html").read_text())


if __name__ == "__main__":
    unittest.main()

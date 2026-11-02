"""No-credit release checks for Kotifixi V7 editorial redesign."""
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit
import re
import unittest
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1] / "docs" / "kaurivo" / "demos" / "kotifixi-v7"
FILES = ("index.html", "palvelut/index.html", "hinnasto/index.html",
         "meista/index.html", "yhteys/index.html")


class KotifixiV7ReleaseTests(unittest.TestCase):
    def test_five_real_pages_and_navigation(self):
        for filename in FILES:
            with self.subTest(filename=filename):
                p = ROOT / filename
                self.assertTrue(p.exists())
                soup = BeautifulSoup(p.read_text(encoding="utf-8"), "html.parser")
                self.assertEqual(len(soup.select("h1")), 1)
                self.assertEqual(len(soup.select(".site-nav a[href]")), 5)
                self.assertEqual(len(soup.select(".mobile-menu a[href]")), 6)
                self.assertTrue(soup.select_one('meta[name="robots"][content*="noindex"]'))
                self.assertTrue(soup.select_one('a[href^="tel:"]'))
                self.assertTrue(soup.select_one("main#main"))
                self.assertTrue(soup.select_one("footer.site-footer"))
                self.assertIsNotNone(soup.select_one(".brand[aria-label]"))
                for link in soup.select("nav.site-nav a[href], nav.mobile-menu a[href]"):
                    href = link["href"]
                    if href.startswith(("mailto:", "tel:", "http:", "https:")):
                        continue
                    target = (p.parent / href).resolve()
                    self.assertTrue(str(target).startswith(str(ROOT.resolve())), href)
                    if target.is_dir():
                        target /= "index.html"
                    self.assertTrue(target.is_file(), (filename, href))

    def test_mobile_preview_disclaimer_remains_visible(self):
        stylesheet = (ROOT / "assets/style.css").read_text(encoding="utf-8")
        for filename in FILES:
            page = (ROOT / filename).read_text(encoding="utf-8")
            self.assertIn("Kaurivon suunnitteluesikatselu", page)
            self.assertIn("Ei Kotifixin virallinen sivusto", page)
        self.assertNotIn(".concept-strip>.container span:last-child{display:none}", stylesheet)
        self.assertIn(".concept-strip>.container span:last-child{display:inline}", stylesheet)
        self.assertIn("@media(max-width:360px)", stylesheet)

    def test_hero_conversion_restored_but_arrows_not_added(self):
        soup = BeautifulSoup((ROOT / "index.html").read_text(encoding="utf-8"), "html.parser")
        self.assertEqual(soup.select_one(".hero-copy .button-primary").get_text(strip=True), "Kysy arviota")
        self.assertEqual(soup.select_one(".hero-copy .button-secondary").get_text(strip=True), "Katso palvelut")
        self.assertEqual(len(soup.select(".editorial-card[href]")), 3)
        # The old tagline-heavy band was intentionally removed.
        self.assertEqual(len(soup.select(".intro-band")), 0)
        self.assertNotIn("Vähemmän tekemättömiä töitä", str(soup))
        self.assertNotIn("KOTIFIXIN IDEA", str(soup))
        self.assertIn("Tarvitsetko apua", soup.select_one("h1").get_text(" ", strip=True))
        self.assertIn("hinnastoon", soup.select_one(".approach-section").get_text(" ",strip=True))
        self.assertNotIn("photo-caption", str(soup))
        self.assertIn("apua", soup.select_one(".hero-copy h1").get_text(" ", strip=True).lower())
        for filename in FILES:
            text = (ROOT / filename).read_text(encoding="utf-8")
            for arrow in ("↗", "→", "➜", "➝"):
                self.assertNotIn(arrow, text)

    def test_picture_set_curated_no_repeated_photo_ids(self):
        assets = []
        for filename in FILES:
            soup = BeautifulSoup((ROOT / filename).read_text(encoding="utf-8"), "html.parser")
            for image in soup.select("img"):
                self.assertTrue(image.get("alt"), (filename, image))
                u = urlsplit(image.get("src", ""))
                self.assertEqual(u.hostname, "images.pexels.com")
                self.assertRegex(u.path, r"/photos/\d+/pexels-photo-\d+\.jpeg$")
                assets.append(u.path)
        self.assertEqual(len(assets), 5)
        self.assertEqual(len(set(assets)), 5)
        self.assertIn("Kuvat ovat havainnollistavia", (ROOT / "index.html").read_text())
        for filename in FILES:
            self.assertIn("Ei Kotifixin virallinen", (ROOT / filename).read_text())
            self.assertIn("Esimerkkikuvat: Pexels.", (ROOT / filename).read_text())

    def test_services_no_repeated_contact_ctas_per_card(self):
        soup = BeautifulSoup((ROOT / "palvelut/index.html").read_text(), "html.parser")
        self.assertEqual(len(soup.select(".service-row")), 3)
        self.assertEqual(len(soup.select(".service-row a[href*='yhteys']")), 0)
        self.assertEqual(len(soup.select(".service-outro a[href*='yhteys']")), 1)
        for category in ("piha", "koti", "korjaukset"):
            self.assertTrue(soup.select_one("#" + category))

    def test_honest_prices_and_contact_backend(self):
        price = (ROOT / "hinnasto/index.html").read_text()
        self.assertIn("1.11.2026", price)
        self.assertIn("39,90 € / h", price)
        self.assertIn("kotifixi.com/hinnasto/", price)
        contact = (ROOT / "yhteys/index.html").read_text()
        js = (ROOT / "assets/app.js").read_text()
        self.assertIn('id="contact-form"', contact)
        self.assertIn('name="test_consent"', contact)
        self.assertIn('name="website"', contact)
        self.assertIn("ei lähde Kotifixille", contact)
        self.assertIn("kaurivo-kotifixi-demo-contact", js)
        self.assertIn("result.reference", js)
        self.assertIn("fetch(endpoint", js)
        self.assertNotIn("window.location.href='mailto:", js)
        self.assertIn("prefers-reduced-motion:reduce", (ROOT / "assets/style.css").read_text())


if __name__ == "__main__":
    unittest.main()

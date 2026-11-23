import json
import re
import unittest
from pathlib import Path

SITE = Path(__file__).resolve().parents[1] / "docs" / "kaurivo"
PUBLIC = ("index.html", "about/index.html", "services/index.html", "process/index.html", "work/index.html",
          "faq/index.html", "contact/index.html", "privacy/index.html", "hinnat/index.html")


class FinnishFirstSiteTests(unittest.TestCase):
    def test_public_pages_are_finnish_indexable_html(self):
        for page in PUBLIC:
            with self.subTest(page=page):
                src = (SITE / page).read_text(encoding="utf-8")
                self.assertIn('<html lang="fi"', src)
                self.assertIn('content="index,follow"', src)
                self.assertIn('rel="canonical" href="https://kaurivo.com/', src)
                title = re.search(r"<title>([^<]+)</title>", src).group(1)
                self.assertIn("Kaurivo", title)
                self.assertNotRegex(title, r"\b(Services|Contact|Process|Frequently|Privacy|Premium)\b")
                self.assertIn('data-lang-set="fi" lang="fi" aria-pressed="true"', src)

    def test_english_is_the_translated_view(self):
        js = (SITE / "assets" / "i18n.js").read_text(encoding="utf-8")
        self.assertIn('let chosen="fi"', js)
        self.assertIn('lang==="en"?en[key]:null', js)

    def test_structured_data_robots_and_sitemap(self):
        home = (SITE / "index.html").read_text(encoding="utf-8")
        ld = json.loads(re.search(r'<script type="application/ld\+json">(.+?)</script>', home).group(1))
        self.assertEqual(ld["url"], "https://kaurivo.com/")
        self.assertEqual(ld["email"], "hello@kaurivo.com")
        robots = (SITE / "robots.txt").read_text()
        self.assertIn("Disallow: /admin/", robots)
        self.assertIn("Sitemap: https://kaurivo.com/sitemap.xml", robots)
        self.assertIn("<loc>https://kaurivo.com/faq/</loc>", (SITE / "sitemap.xml").read_text())


class PricingPageTests(unittest.TestCase):
    def test_price_list_is_public_and_linked(self):
        page = (SITE / "hinnat" / "index.html").read_text(encoding="utf-8")
        for price in ("alkaen 990\u00a0€", "1\u00a0900–3\u00a0500\u00a0€", "alkaen 3\u00a0500\u00a0€", "alv 0\u00a0%"):
            self.assertIn(price, page)
        self.assertIn('"@type": "Offer"', page)
        self.assertIn("../hinnat/", (SITE / "faq" / "index.html").read_text(encoding="utf-8"))
        self.assertIn('href="hinnat/">Hinnat</a>', (SITE / "index.html").read_text(encoding="utf-8"))
        self.assertIn("<loc>https://kaurivo.com/hinnat/</loc>", (SITE / "sitemap.xml").read_text())


if __name__ == "__main__":
    unittest.main()

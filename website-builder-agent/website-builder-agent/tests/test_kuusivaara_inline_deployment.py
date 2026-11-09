"""Regression: prevent Render publishing this demo without its visual design.

The public site previously had working HTML and huge unsized logo, because its
external CSS did not reach the browser. This asserts the full current design and
progressive enhancement are included in the HTML itself.
"""
from pathlib import Path
from bs4 import BeautifulSoup
import unittest

HERE = Path(__file__).resolve().parents[1]
DEMO = HERE / "docs/kaurivo/demos/kuusivaara-v1"
ROUTES = [
    "", "palvelut/", "tyot/", "tekijat/", "tarinamme/", "yhteys/",
    "en/", "en/services/", "en/work/", "en/people/", "en/story/", "en/contact/"
]

class KuusivaaraStaticDeliveryTests(unittest.TestCase):
    def test_css_and_js_are_self_contained_on_every_route(self):
        css = (DEMO / "assets/site.css").read_text(encoding="utf-8")
        js = (DEMO / "assets/site.js").read_text(encoding="utf-8")
        self.assertGreater(len(css), 10000)
        self.assertGreater(len(js), 1000)
        for route in ROUTES:
            with self.subTest(route=route or "/"):
                html = (DEMO / route / "index.html").read_text(encoding="utf-8")
                soup = BeautifulSoup(html, "html.parser")
                style = soup.select_one("style[data-kaurivo-critical-styles='inline-v1']")
                script = soup.select_one("script[data-kaurivo-enhancement='inline-v1']")
                self.assertIsNotNone(style)
                self.assertIsNotNone(script)
                self.assertEqual(style.get_text().strip(), css.strip())
                self.assertEqual(script.get_text().strip(), js.strip())
                self.assertFalse(soup.select("link[rel=stylesheet],script[src]"))
                self.assertIn(".hero-art img", style.get_text())
                self.assertIn("@media(max-width:530px)", style.get_text())
                self.assertIn("prefers-reduced-motion", style.get_text())
                self.assertEqual(soup.select_one("html").get("lang"), "en" if route.startswith("en/") else "fi")
                self.assertEqual(soup.select_one("html").get("data-kaurivo-release"), "kv-20261109-render-fingerprint-v4")
                self.assertEqual(len(soup.select("header .brand .brand-logo")), 1)

if __name__ == "__main__":
    unittest.main()

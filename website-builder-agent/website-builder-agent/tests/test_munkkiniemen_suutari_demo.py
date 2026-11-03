"""Source-bound QA for a fresh, unseen six-page Munkkiniemen Suutari concept.

Use no business brand photos, customer reviews or prices unless rights and
live source evidence are independently verified. Functional mobile/browser QA
is part of the normal CI, not a self-declared independent 9.5 score.
"""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "docs" / "kaurivo" / "demos" / "munkkiniemen-suutari-v1"
ROUTES = ("", "palvelut", "tuotteet", "roots-ltd", "soitinhihnat", "tilaustyot")
SOURCE_IDS = {
    "": ["Munkkiniemen Suutari", "1943", "Munkkiniemen puistotie 18"],
    "palvelut": ["Kenkien korjaus", "Avainpalvelut", "Ortopediset työt",
                 "Vetoketjut", "teroitus"],
    "tuotteet": ["Nahanhoito", "pohjallisia", "kengännauhoja", "lepolestejä",
                 "kalosseja", "työessuja"],
    "roots-ltd": ["Roots LTD", "Shure-mikrofonista", "höyryvetureiden"],
    "soitinhihnat": ["Vario Pro", "Lucky Seven", "Joustavuus", "pituus"],
    "tilaustyot": ["saamenkäsityön", "metallisepän", "suutarin",
                   "lentokoneiden", "nukketeatterin"],
}


def page(route):
    f = SITE / route / "index.html" if route else SITE / "index.html"
    return f.read_text(encoding="utf-8")


class MunkkiniemenDemoSourceGate(unittest.TestCase):
    def test_six_real_route_files_have_specific_original_content(self):
        for route, labels in SOURCE_IDS.items():
            text = page(route)
            for label in labels:
                with self.subTest(route=route, label=label):
                    self.assertIn(label.casefold(), text.casefold())

    def test_every_page_identifies_itself_as_unofficial_demo(self):
        for route in ROUTES:
            text = page(route)
            self.assertIn('noindex,nofollow,noarchive', text)
            self.assertIn('ei yrityksen virallinen', text.casefold())
            self.assertIn('https://www.munkkiniemensuutari.fi/', text)

    def test_every_route_links_to_all_other_real_pages_and_contacts(self):
        for route in ROUTES:
            html = page(route)
            self.assertIn('tel:+3589487286', html)
            self.assertIn('mailto:pietusuutari@gmail.com', html)
            for target in ROUTES:
                href = ("../" if route else "") + (target + "/" if target else ("./" if not route else ""))
                self.assertIn('href="' + href + '"', html,
                              f"Missing {target} in {route} navigation")
            for match in re.finditer(r'href="([^"]+)"', html):
                url = match.group(1)
                if url.startswith(("http:", "https:", "tel:", "mailto:", "#")):
                    continue
                base = SITE / route if route else SITE
                path, *_ = url.split("#", 1)
                resolved = (base / path).resolve() if path else base
                self.assertTrue(resolved.is_relative_to(SITE.resolve()))
                self.assertTrue(
                    (resolved / "index.html").is_file() if path.endswith("/")
                    else resolved.is_file(),
                    f"Broken internal href {url} in route {route}")

    def test_only_original_created_graphics_not_copied_unlicensed_brand_media(self):
        asset_files = [x for x in SITE.rglob("*") if x.is_file()]
        self.assertEqual(
            {x.suffix for x in asset_files}, {".html", ".css", ".js"})
        home = page("")
        self.assertIn("nahkakenkäkuvitus", home)
        self.assertIn("ei yrityksen valokuva", home.casefold())
        for route in ROUTES:
            text = page(route)
            self.assertNotIn("schema.org/Review", text)
            self.assertNotIn("aggregateRating", text)
            self.assertNotIn("⭐⭐⭐⭐⭐", text)

    def test_real_contact_and_location_evidence_is_not_lost(self):
        for route in ROUTES:
            html = page(route)
            self.assertIn("00330 Helsinki", html)
            self.assertIn("Munkkiniemen puistotie 18", html)
            self.assertIn("09 487 286", html)

    def test_css_contains_mobile_accessibility_and_motion_guards(self):
        css = (SITE / "assets/site.css").read_text(encoding="utf-8")
        js = (SITE / "assets/site.js").read_text(encoding="utf-8")
        self.assertIn("max-width:550px", css)
        self.assertIn("max-width:820px", css)
        self.assertIn("prefers-reduced-motion:reduce", css)
        self.assertIn("aria-expanded", js)
        self.assertIn("Escape", js)

    def test_home_and_five_pages_render_without_horizontal_scroll(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            self.skipTest("Playwright is not installed; separate CI browser QA required.")
        with sync_playwright() as playwright:
            try:
                browser = playwright.chromium.launch(headless=True)
            except Exception as exc:
                if __import__("os").getenv("REQUIRE_BROWSER_TESTS") == "1":
                    self.fail("Chromium missing for mandatory demo mobile QA: "+str(exc))
                self.skipTest("Chromium unavailable")
            try:
                for route in ROUTES:
                    filename = SITE / route / "index.html" if route else SITE/"index.html"
                    for width in (320, 390, 768, 1440):
                        with self.subTest(route=route, width=width):
                            page_ = browser.new_page(viewport={"width":width,"height":850})
                            page_.route("https://fonts.googleapis.com/**",lambda r:r.abort())
                            page_.route("https://fonts.gstatic.com/**",lambda r:r.abort())
                            page_.goto(filename.resolve().as_uri(),wait_until="domcontentloaded")
                            page_.locator("h1").first.wait_for(state="visible")
                            measures = page_.evaluate("""() => ({
                                scroll: document.documentElement.scrollWidth,
                                width: window.innerWidth,
                                h1: document.querySelector('h1').getBoundingClientRect().width
                            })""")
                            self.assertLessEqual(measures["scroll"], measures["width"] + 2,
                                                 f"Horizontal overflow at {width}: {route}")
                            self.assertGreater(measures["h1"], 0)
                            if width == 390:
                                toggle=page_.locator("[data-menu-toggle]")
                                self.assertTrue(toggle.is_visible())
                                toggle.click()
                                self.assertEqual(toggle.get_attribute("aria-expanded"),"true")
                                self.assertTrue(page_.locator("#mobile-menu").is_visible())
                                page_.keyboard.press("Escape")
                                self.assertEqual(toggle.get_attribute("aria-expanded"),"false")
                            page_.close()
            finally:
                browser.close()


if __name__=="__main__":
    unittest.main()

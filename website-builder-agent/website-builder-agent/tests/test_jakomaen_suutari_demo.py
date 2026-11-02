"""New-company demo content, link and mobile QA; uses zero paid API credits."""
from __future__ import annotations

import os
import unittest
from pathlib import Path
from urllib.parse import urlsplit, unquote

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1] / "docs" / "kaurivo" / "demos" / "jakomaen-suutari-ja-pyora-v1"
ROUTES = ("index.html", "suutari-hinnasto/index.html",
          "pyorahuolto-hinnasto/index.html", "yhteystiedot/index.html")


class JakomaenFirstPassQA(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pages = {name: BeautifulSoup((ROOT / name).read_text(encoding="utf-8"),
                                        "html.parser") for name in ROUTES}

    def test_all_four_source_pages_retained(self):
        self.assertEqual(len(self.pages), 4)
        for route, soup in self.pages.items():
            with self.subTest(route=route):
                self.assertEqual(soup.html.get("lang"), "fi")
                self.assertEqual(len(soup.select("main h1")), 1)
                self.assertIsNotNone(soup.select_one('meta[name="viewport"]'))
                self.assertIsNotNone(soup.select_one("header.site-header"))
                self.assertIsNotNone(soup.select_one("footer"))
                self.assertIsNotNone(soup.select_one('a[href^="tel:"]'))
                self.assertNotIn("↗", soup.get_text(" ", strip=True))

    def test_no_dead_internal_navigation_or_missing_static_assets(self):
        for route, soup in self.pages.items():
            with self.subTest(route=route):
                base = (ROOT / route).parent
                for tag in soup.select("a[href],link[href],script[src]"):
                    href = tag.get("href") or tag.get("src")
                    parsed = urlsplit(href)
                    if parsed.scheme or href.startswith("#"):
                        continue
                    target = (base / unquote(parsed.path)).resolve()
                    if target.is_dir():
                        target = target / "index.html"
                    self.assertTrue(target.is_relative_to(ROOT.resolve()), href)
                    self.assertTrue(target.is_file(), (route, href))

    def test_exact_pricing_row_counts_and_service_categories(self):
        counts = {"suutari-hinnasto/index.html": (63, 12),
                  "pyorahuolto-hinnasto/index.html": (37, 10)}
        for route, (rows, groups) in counts.items():
            with self.subTest(route=route):
                soup = self.pages[route]
                self.assertEqual(len(soup.select(".price-group")), groups)
                self.assertEqual(len(soup.select(".price-table tr")), rows)
                self.assertEqual(len(soup.select(".price-table td")), rows * 2)
                self.assertIsNotNone(soup.select_one("#priceSearch"))
                self.assertIn("Uudet hinnastot tulevat pian", soup.get_text(" ", strip=True))
        shoe = self.pages["suutari-hinnasto/index.html"].get_text(" ", strip=True)
        bike = self.pages["pyorahuolto-hinnasto/index.html"].get_text(" ", strip=True)
        for phrase in ("Abloy avain", "Nahkapohjat", "Kengät 10", "Kenkien venytys",
                       "Varsien kavennus", "Kärjet asennettuna", "Pätkävahvike"):
            self.assertIn(phrase, shoe)
        for phrase in ("Jarrulänkiparin asennus", "Fauber-keskiön huolto",
                       "Takanapa, 4", "Irtovanteen rihtaus", "Lukon murto",
                       "Tavaratelineen asennus"):
            self.assertIn(phrase, bike)

    def test_source_notices_are_truthful_and_no_reviews_invented(self):
        text = " ".join(soup.get_text(" ", strip=True) for soup in self.pages.values())
        self.assertIn("1377762-8", text)
        self.assertIn("Huokotie 1", text)
        self.assertIn("Ruokatauko", text)
        self.assertIn("040 163", text)
        self.assertIn("ei yrityksen hyväksymä", text.lower())
        self.assertNotIn("★★★★★", text)
        self.assertNotIn("arvostelumme", text.lower())
        self.assertIn("päiväämätön kesälomailmoitus", text.lower())

    def test_image_sources_are_original_and_alt_describes_illustration(self):
        for route, soup in self.pages.items():
            for image in soup.select("img"):
                with self.subTest(route=route):
                    self.assertTrue(str(image.get("alt") or "").strip())
                    self.assertTrue(image.get("src", "").startswith(
                        "https://www.jakomaensuutari.fi/wp-content/uploads/"))
        self.assertIn("käyttö", (ROOT/"index.html").read_text(encoding="utf-8").lower())

    def test_real_mobile_browser_no_overflow_or_dead_menu(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            self.fail(f"Browser QA must be installed: {exc}")
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                for width, height in ((320, 720), (390, 844), (768, 1000), (1440, 900)):
                    context = browser.new_context(viewport={"width": width, "height": height},
                                                  reduced_motion="reduce")
                    # No external network is needed for layout verification.
                    context.route("https://www.jakomaensuutari.fi/**",
                                  lambda route: route.abort())
                    try:
                        page = context.new_page()
                        for route in ROUTES:
                            with self.subTest(width=width, route=route):
                                page.goto((ROOT / route).as_uri(), wait_until="domcontentloaded")
                                page.wait_for_timeout(30)
                                overflow = page.evaluate(
                                    "document.documentElement.scrollWidth > innerWidth + 2"
                                )
                                self.assertFalse(overflow, f"overflow: {width}px {route}")
                                self.assertTrue(page.locator("main h1").is_visible())
                        if width <= 768:
                            page.goto((ROOT/"index.html").as_uri())
                            toggle = page.locator(".menu-toggle")
                            self.assertTrue(toggle.is_visible())
                            toggle.click()
                            self.assertEqual(toggle.get_attribute("aria-expanded"), "true")
                            self.assertTrue(page.locator(".mobile-nav a").first.is_visible())
                            page.keyboard.press("Escape")
                            self.assertEqual(toggle.get_attribute("aria-expanded"), "false")
                        price = page
                        price.goto((ROOT/"suutari-hinnasto/index.html").as_uri())
                        price.locator("#priceSearch").fill("Abloy")
                        self.assertEqual(price.locator(".price-table tr:visible").count(), 1)
                        self.assertIn("Abloy", price.locator(".price-table tr:visible").first.inner_text())
                    finally:
                        context.close()
            finally:
                browser.close()


if __name__ == "__main__":
    unittest.main()

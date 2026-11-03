"""Offline V16 review-preview integration and width tests.

Exercises copied GitHub Pages snapshot; does not use live customer contact
endpoint or any paid API. Browser smoke requires Playwright Chromium in CI.
"""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from threading import Thread
import unittest

from bs4 import BeautifulSoup

SITE = Path(__file__).resolve().parents[1] / "docs" / "kaurivo" / "demos" / "kotifixi-v16"
ROUTES = ("", "palvelut/", "hinnasto/", "meista/", "yhteys/")
WIDTHS = (320, 360, 390, 430, 768, 940, 960, 1024, 1180, 1280, 1440, 1920)


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass


class VersionedPreviewTests(unittest.TestCase):
    def test_all_pages_navigation_and_factual_title(self):
        self.assertTrue((SITE / "assets/style.css").is_file())
        self.assertTrue((SITE / "assets/app.js").is_file())
        home = BeautifulSoup((SITE / "index.html").read_text(encoding="utf-8"),
                             "html.parser")
        self.assertEqual(
            home.select_one("h1").get_text(" ", strip=True),
            "Tarvitsetko apua kotitöissä tai pihatöissä?",
        )
        self.assertIn("hero-visual-3d", str(home))
        for route in ROUTES:
            doc = BeautifulSoup((SITE / route / "index.html").read_text(encoding="utf-8"),
                                "html.parser")
            self.assertEqual(doc.html.get("lang"), "fi")
            self.assertIsNotNone(doc.select_one("meta[name=robots][content*=noindex]"))
            self.assertEqual(len(doc.select(".site-nav a")), 5)
            self.assertEqual(len(doc.select(".mobile-menu a")), 6)
            self.assertIn("Ei Kotifixin virallinen sivusto", doc.get_text(" ", strip=True))
        css = (SITE / "assets/style.css").read_text(encoding="utf-8")
        js = (SITE / "assets/app.js").read_text(encoding="utf-8")
        self.assertIn("grid-template-columns:max-content minmax(0,1fr) max-content", css)
        self.assertIn("justify-content:space-between", css)
        self.assertIn(".site-header .header-action-set{", css)
        self.assertIn("html{scroll-behavior:auto", css)
        self.assertNotIn("window.addEventListener('scroll'", js)
        self.assertIn("prefers-reduced-motion: reduce", js)
        self.assertIn("IntersectionObserver", js)

    def test_final_images_and_motion_are_cohesive(self):
        home = BeautifulSoup((SITE / "index.html").read_text(encoding="utf-8"),
                             "html.parser")
        about = BeautifulSoup((SITE / "meista/index.html").read_text(encoding="utf-8"),
                              "html.parser")
        self.assertEqual(len(home.select(".editorial-card img")), 3)
        self.assertEqual(len(home.select(".hero-photo-frame img")), 1)
        for img in home.select(".editorial-card img, .hero-photo-frame img"):
            self.assertTrue(img.get("srcset"), img.get("src"))
            self.assertTrue(img.get("sizes"), img.get("src"))
            self.assertTrue(img.get("width"), img.get("src"))
            self.assertTrue(img.get("height"), img.get("src"))
            self.assertTrue(img.get("alt"), img.get("src"))
        self.assertTrue(about.select_one(".about-photo img").get("srcset"))
        self.assertTrue(about.select_one(".about-photo img").get("sizes"))
        css = (SITE / "assets/style.css").read_text(encoding="utf-8")
        self.assertIn("/* V16 final editorial finish", css)
        self.assertIn("scale(1.025)", css)
        self.assertIn(".editorial-card-content p{", css)
        self.assertIn("font-size:15px;line-height:1.67", css)
        self.assertIn("@media(prefers-reduced-motion:reduce)", css)
        js = (SITE / "assets/app.js").read_text(encoding="utf-8")
        self.assertNotIn("window.addEventListener('scroll'", js)
        self.assertNotIn("addEventListener('wheel'", js)

    def test_all_viewports_no_blank_navigation_region_or_horizontal_overflow(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            self.skipTest("Playwright missing locally; CI installs Chromium")
        server = ThreadingHTTPServer(("127.0.0.1", 0),
                                     partial(QuietHandler, directory=str(SITE)))
        worker = Thread(target=server.serve_forever, daemon=True)
        worker.start()
        base = "http://127.0.0.1:" + str(server.server_port) + "/"
        try:
            with sync_playwright() as pw:
                try:
                    browser = pw.chromium.launch(headless=True)
                except Exception as exc:
                    self.skipTest("Chromium unavailable: " + str(exc))
                try:
                    for width in WIDTHS:
                        with self.subTest(width=width):
                            context = browser.new_context(
                                viewport={"width": width, "height": 860},
                                reduced_motion="reduce",
                            )
                            context.route("**/*", lambda req: (
                                req.continue_()
                                if req.request.url.startswith(base) else req.abort()
                            ))
                            page = context.new_page()
                            try:
                                for route in ROUTES:
                                    with self.subTest(route=route):
                                        response = page.goto(base + route, wait_until="domcontentloaded")
                                        self.assertEqual(response.status, 200)
                                        self.assertTrue(page.locator("h1").is_visible())
                                        self.assertLessEqual(
                                            page.evaluate("document.documentElement.scrollWidth - innerWidth"), 1,
                                            (width, route),
                                        )
                                        self.assertEqual(page.locator(".scroll-reveal").count(), 0)
                                        actions_group = page.locator(".site-header .header-action-set")
                                        self.assertTrue(actions_group.is_visible())
                                        self.assertEqual(actions_group.locator("a[href]").count(), 2)
                                        self.assertEqual(
                                            actions_group.locator(".phone-link").get_attribute("href"),
                                            "tel:+358443632429"
                                        )
                                        if width >= 1280:
                                            self.assertTrue(actions_group.locator(".phone-link").is_visible())
                                            call = actions_group.locator(".phone-link").bounding_box()
                                            quote = actions_group.locator(".header-cta").bounding_box()
                                            self.assertLessEqual(
                                                abs(call["y"] + call["height"]/2 -
                                                    quote["y"] - quote["height"]/2), 2)
                                            self.assertLessEqual(
                                                quote["x"] - call["x"] - call["width"], 5)
                                        else:
                                            self.assertFalse(actions_group.locator(".phone-link").is_visible())
                                        if width <= 940:
                                            self.assertTrue(page.locator(".menu-toggle").is_visible())
                                            self.assertFalse(page.locator(".site-nav").is_visible())
                                        else:
                                            self.assertTrue(page.locator(".site-nav").is_visible())
                                            brand = page.locator(".site-header .brand").first.bounding_box()
                                            first = page.locator(".site-header .site-nav a").first.bounding_box()
                                            last = page.locator(".site-header .site-nav a").last.bounding_box()
                                            actions = page.locator(".site-header .header-right").bounding_box()
                                            inner = page.locator(".site-header .header-inner").bounding_box()
                                            left_gap = first["x"] - (brand["x"] + brand["width"])
                                            right_gap = actions["x"] - (last["x"] + last["width"])
                                            self.assertGreaterEqual(left_gap, 6, (width, route, left_gap))
                                            self.assertGreaterEqual(right_gap, 6, (width, route, right_gap))
                                            self.assertLessEqual(left_gap, 50, (width, route, left_gap))
                                            self.assertLessEqual(right_gap, 50, (width, route, right_gap))
                                            self.assertLessEqual(
                                                abs(inner["x"] + inner["width"] -
                                                    actions["x"] - actions["width"]), 2)
                                            self.assertGreaterEqual(
                                                page.locator(".site-nav a").first.evaluate(
                                                    "(el)=>parseFloat(getComputedStyle(el).fontSize)"
                                                ), 16)
                                        if width == 390 and route == "":
                                            button = page.locator(".menu-toggle")
                                            button.click()
                                            self.assertTrue(page.locator("#mobile-menu").is_visible())
                                            page.keyboard.press("Escape")
                                            self.assertFalse(page.locator("#mobile-menu").is_visible())
                            finally:
                                page.close()
                                context.close()
                finally:
                    browser.close()
        finally:
            server.shutdown()
            server.server_close()
            worker.join(timeout=5)

    def test_original_company_prices_service_categories_and_honest_test_form(self):
        home = (SITE / "index.html").read_text(encoding="utf-8")
        services = (SITE / "palvelut/index.html").read_text(encoding="utf-8")
        prices = (SITE / "hinnasto/index.html").read_text(encoding="utf-8")
        about = (SITE / "meista/index.html").read_text(encoding="utf-8")
        contact = (SITE / "yhteys/index.html").read_text(encoding="utf-8")
        js = (SITE / "assets/app.js").read_text(encoding="utf-8")
        self.assertIn("Helpompi arki alkaa meistä.", home)
        self.assertIn('class="task-shortcuts"', home)
        self.assertIn("Pihakalusteiden kunnostus", services)
        self.assertIn("joulukuusen poishaku", services)
        self.assertIn("lampunvaihto", services.casefold())
        self.assertIn("keittiöapu", services.casefold())
        self.assertIn("Autonpesu", prices)
        self.assertIn("Joulukuusen poishaku", prices)
        self.assertIn("Kalusteiden kunnostus", prices)
        self.assertIn("Ei vähennyskelpoinen", prices)
        self.assertIn("40 %", prices)
        self.assertIn("20 €", prices)
        self.assertIn("MobilePay", about)
        self.assertIn("ei Kotifixille", contact)
        self.assertIn("kaurivo-kotifixi-demo-contact", js)
        self.assertIn("allowedServices", js)
        for page in ROUTES:
            content = (SITE / page / "index.html").read_text(encoding="utf-8")
            self.assertIn("Ei Kotifixin virallinen sivusto", content)
            self.assertNotIn("⭐⭐⭐⭐⭐", content)

    def test_service_shortcut_prefills_test_form_without_sending_real_data(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            self.skipTest("Playwright is required")
        server = ThreadingHTTPServer(("127.0.0.1", 0),
                                     partial(QuietHandler, directory=str(SITE)))
        worker = Thread(target=server.serve_forever, daemon=True)
        worker.start()
        base = "http://127.0.0.1:" + str(server.server_port) + "/"
        try:
            with sync_playwright() as pw:
                try:
                    browser = pw.chromium.launch(headless=True)
                except Exception as exc:
                    self.skipTest("Chromium unavailable: " + str(exc))
                try:
                    page = browser.new_page(viewport={"width": 390, "height": 844})
                    page.route("**/*", lambda req: (
                        req.continue_() if req.request.url.startswith(base) else req.abort()
                    ))
                    page.goto(base + "yhteys/?palvelu=Pihaty%C3%B6t", wait_until="domcontentloaded")
                    self.assertEqual(page.locator("#cust-service").input_value(), "Pihatyöt")
                    self.assertTrue(page.locator(".form-submit").is_visible())
                    self.assertIn("ei Kotifixille", page.locator(".contact-test").inner_text())
                    page.goto(base + "yhteys/?palvelu=%3Cscript%3E", wait_until="domcontentloaded")
                    self.assertEqual(page.locator("#cust-service").input_value(), "")
                finally:
                    browser.close()
        finally:
            server.shutdown()
            server.server_close()
            worker.join(timeout=5)


if __name__ == "__main__":
    unittest.main()

"""Real Chromium UI smoke test for a 5-page Kotifixi *unlisted preview*.

Offline/localhost only, requests to external sites blocked to avoid API spending.
The test validates responsive geometry and navigation, not image licensing,
real public image availability, CMS editing or real-user Core Web Vitals.
"""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
import unittest


ROOT = Path(__file__).resolve().parents[1] / "docs" / "kaurivo" / "demos" / "kotifixi-v5"
ROUTES = ("/", "/palvelut/", "/hinnasto/", "/meista/", "/yhteys/")


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        pass


class BrowserPreviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise unittest.SkipTest("Playwright not installed") from exc
        cls.playwright_context = sync_playwright()
        cls.pw = cls.playwright_context.start()
        try:
            cls.browser = cls.pw.chromium.launch(headless=True)
        except Exception as exc:
            cls.playwright_context.stop()
            raise unittest.SkipTest("Browser unavailable: " + str(exc)) from exc
        cls.http = ThreadingHTTPServer(("127.0.0.1", 0),
                                       partial(Handler, directory=str(ROOT)))
        cls.thread = threading.Thread(target=cls.http.serve_forever, daemon=True)
        cls.thread.start()
        cls.base = "http://127.0.0.1:" + str(cls.http.server_port)

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.http.server_close()
        cls.thread.join(timeout=5)
        cls.browser.close()
        cls.playwright_context.stop()

    def test_real_browser_all_pages_four_viewports(self):
        for width in (320, 390, 768, 1440):
            with self.subTest(width=width):
                context = self.browser.new_context(
                    viewport={"width": width, "height": 850},
                    reduced_motion="reduce")
                # Do not spend network requests retrieving remote preview imagery/fonts.
                context.route("**/*", lambda route: (
                    route.continue_() if route.request.url.startswith(self.base)
                    else route.abort()))
                page = context.new_page()
                errors = []
                page.on("pageerror", lambda e: errors.append(str(e)))
                for path in ROUTES:
                    with self.subTest(route=path):
                        response = page.goto(self.base + path, wait_until="domcontentloaded")
                        self.assertEqual(response.status, 200)
                        self.assertEqual(page.locator("h1").count(), 1)
                        self.assertTrue(page.locator("h1").is_visible())
                        self.assertLessEqual(page.evaluate(
                            "document.documentElement.scrollWidth - innerWidth"), 1)
                        self.assertTrue(page.locator("a.brand").is_visible())
                        self.assertEqual(page.locator(".desktop-nav a[href]").count(), 5)
                        if width <= 768:
                            button = page.locator("#menu-btn")
                            self.assertTrue(button.is_visible())
                            button.click()
                            self.assertEqual(button.get_attribute("aria-expanded"), "true")
                            self.assertTrue(page.locator("#mobile-nav").is_visible())
                            button.click()
                            self.assertFalse(page.locator("#mobile-nav").is_visible())
                        self.assertEqual(errors, [], errors)
                page.close()
                context.close()


if __name__ == "__main__":
    unittest.main()

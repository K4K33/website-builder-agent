"""Real Chromium UI smoke tests for five-page Kotifixi concept preview.

Browser lifetime is scoped to ONE test to avoid leaking Playwright event-loop
state into existing production gate tests. No paid or external network calls.
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
    def test_real_browser_all_pages_four_viewports(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise unittest.SkipTest("Playwright not installed") from exc
        http = ThreadingHTTPServer(("127.0.0.1", 0),
                                   partial(Handler, directory=str(ROOT)))
        thread = threading.Thread(target=http.serve_forever, daemon=True)
        thread.start()
        base = "http://127.0.0.1:" + str(http.server_port)
        try:
            with sync_playwright() as pw:
                try:
                    browser = pw.chromium.launch(headless=True)
                except Exception as exc:
                    raise unittest.SkipTest("Chromium unavailable: " + str(exc)) from exc
                try:
                    for width in (320, 390, 768, 1440):
                        with self.subTest(width=width):
                            context = browser.new_context(
                                viewport={"width": width, "height": 850},
                                reduced_motion="reduce")
                            context.route("**/*", lambda route: (
                                route.continue_() if route.request.url.startswith(base)
                                else route.abort()))
                            page = context.new_page()
                            errors = []
                            page.on("pageerror", lambda e: errors.append(str(e)))
                            try:
                                for path in ROUTES:
                                    with self.subTest(route=path):
                                        response = page.goto(base + path, wait_until="domcontentloaded")
                                        self.assertEqual(response.status, 200)
                                        self.assertEqual(page.locator("h1").count(), 1)
                                        self.assertTrue(page.locator("h1").is_visible())
                                        width_error=page.evaluate("document.documentElement.scrollWidth - innerWidth")
                                        if width_error>1:
                                            offenders=page.evaluate("""() => [...document.querySelectorAll('*')]
                                              .filter(e => e.getBoundingClientRect().right > innerWidth + 2)
                                              .map(e => ({tag:e.tagName,cls:e.className, txt:(e.innerText||'').slice(0,35),
                                                         right:Math.round(e.getBoundingClientRect().right),
                                                         width:Math.round(e.getBoundingClientRect().width)})).slice(0,20)""")
                                            print("OVERFLOW_DIAGNOSTIC",path,width,width_error,offenders,flush=True)
                                        self.assertLessEqual(width_error,1)
                                        self.assertTrue(page.locator(".site-header a.brand").is_visible())
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
                            finally:
                                page.close()
                                context.close()
                finally:
                    browser.close()
        finally:
            http.shutdown()
            http.server_close()
            thread.join(timeout=5)


if __name__ == "__main__":
    unittest.main()

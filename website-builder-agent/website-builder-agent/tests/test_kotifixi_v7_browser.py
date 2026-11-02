"""Real Playwright Chromium multi-viewport smoke on Kotifixi V7.

Zero external API/photo requests; contact POST intercepted by test route.
"""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import threading
import unittest

ROOT = Path(__file__).resolve().parents[1] / "docs" / "kaurivo" / "demos" / "kotifixi-v7"
ROUTES = ("/", "/palvelut/", "/hinnasto/", "/meista/", "/yhteys/")


class Handler(SimpleHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass


class KotifixiV7BrowserTests(unittest.TestCase):
    def test_responsive_navigation_and_mock_form(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise unittest.SkipTest("Playwright unavailable") from exc
        server = ThreadingHTTPServer(("127.0.0.1", 0),
                                     partial(Handler, directory=str(ROOT)))
        runner = threading.Thread(target=server.serve_forever, daemon=True)
        runner.start()
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            with sync_playwright() as pw:
                try:
                    browser = pw.chromium.launch(headless=True)
                except Exception as exc:
                    raise unittest.SkipTest("Chromium unavailable: " + str(exc)) from exc
                try:
                    for width in (320, 360, 390, 430, 768, 940, 960, 1024, 1180, 1280, 1440, 1920):
                        with self.subTest(width=width):
                            context = browser.new_context(
                                viewport={"width": width, "height": 850},
                                reduced_motion="reduce",
                            )
                            context.route("**/*", lambda route: (
                                route.continue_() if route.request.url.startswith(base)
                                else route.abort()
                            ))
                            page = context.new_page()
                            errors = []
                            page.on("pageerror", lambda exc: errors.append(str(exc)))
                            try:
                                for route in ROUTES:
                                    with self.subTest(route=route):
                                        res = page.goto(base + route, wait_until="domcontentloaded")
                                        self.assertEqual(res.status, 200)
                                        self.assertTrue(page.locator("h1").is_visible())
                                        self.assertEqual(page.locator(".site-nav a").count(), 5)
                                        # The concept/legal status must remain visible on real phones.
                                        warning = page.get_by_text("Ei Kotifixin virallinen sivusto", exact=True)
                                        self.assertTrue(warning.is_visible())
                                        box = warning.bounding_box()
                                        self.assertIsNotNone(box)
                                        self.assertGreaterEqual(box["x"], 0)
                                        self.assertLessEqual(box["x"] + box["width"], width + 1)
                                        overflow = page.evaluate(
                                            "document.documentElement.scrollWidth - window.innerWidth")
                                        if overflow > 1:
                                            offenders = page.evaluate("""() => [...document.querySelectorAll('body *')]
                                            .filter(e => e.getBoundingClientRect().right > innerWidth+1)
                                            .map(e=>({tag:e.tagName,cls:String(e.className).slice(0,60),
                                              right:Math.round(e.getBoundingClientRect().right)})).slice(0,10)""")
                                            print("KOTIFIXI_V7_OVERFLOW", route, width, overflow, offenders, flush=True)
                                        self.assertLessEqual(overflow, 1)
                                        if width <= 940:
                                            nav = page.locator("#mobile-menu")
                                            btn = page.locator("#menu-toggle")
                                            self.assertTrue(btn.is_visible())
                                            btn.click()
                                            self.assertTrue(nav.is_visible())
                                            self.assertEqual(btn.get_attribute("aria-expanded"), "true")
                                            page.keyboard.press("Escape")
                                            self.assertFalse(nav.is_visible())
                                        else:
                                            self.assertTrue(page.locator(".site-nav").is_visible())
                                        if width >= 1024:
                                            # Distributed-header V13: actual nav links
                                            # should fill the formerly stranded dead gap.
                                            nav_box = page.locator(".site-header .site-nav").bounding_box()
                                            inner_box = page.locator(".site-header .header-inner").bounding_box()
                                            logo_box = page.locator(".site-header .brand").first.bounding_box()
                                            actions_box = page.locator(".site-header .header-right").bounding_box()
                                            first_link = page.locator(".site-header .site-nav a").first.bounding_box()
                                            last_link = page.locator(".site-header .site-nav a").last.bounding_box()
                                            self.assertIsNotNone(nav_box)
                                            left_gap = first_link["x"] - (logo_box["x"] + logo_box["width"])
                                            right_gap = actions_box["x"] - (last_link["x"] + last_link["width"])
                                            self.assertGreaterEqual(left_gap, 6)
                                            self.assertGreaterEqual(right_gap, 6)
                                            self.assertLessEqual(left_gap, 50, (width, "left gap", left_gap))
                                            self.assertLessEqual(right_gap, 50, (width, "right gap", right_gap))
                                            self.assertLessEqual(
                                                abs((actions_box["x"] + actions_box["width"])
                                                    - (inner_box["x"] + inner_box["width"])), 2
                                            )
                                            self.assertLessEqual(
                                                logo_box["x"] + logo_box["width"],
                                                nav_box["x"] - 3
                                            )
                                            self.assertLessEqual(
                                                nav_box["x"] + nav_box["width"],
                                                actions_box["x"] - 3
                                            )
                                            nav_type = page.locator(".site-nav a").first.evaluate(
                                                """(el) => ({
                                                  fontSize: parseFloat(getComputedStyle(el).fontSize),
                                                  fontWeight: getComputedStyle(el).fontWeight,
                                                  family: getComputedStyle(el).fontFamily
                                                })"""
                                            )
                                            self.assertEqual(nav_type["fontWeight"], "600")
                                            self.assertIn("DM Sans", nav_type["family"])
                                            self.assertGreaterEqual(nav_type["fontSize"],
                                                                    17 if width >= 1280 else 16)
                                            font_px = page.locator(".site-nav a").first.evaluate(
                                                "(el) => parseFloat(getComputedStyle(el).fontSize)"
                                            )
                                            self.assertGreaterEqual(font_px, 15)
                                            if width >= 1280:
                                                phone = page.locator(".site-header .phone-link")
                                                self.assertTrue(phone.is_visible())
                                                self.assertIn("Soita", phone.inner_text())
                                        self.assertEqual(page.locator(".scroll-reveal").count(), 0)
                                        if route == "/":
                                            self.assertTrue(page.locator(".hero-copy .button-primary").is_visible())
                                            self.assertEqual(page.locator(".editorial-card").count(), 3)
                                        if route == "/yhteys/":
                                            self.assertTrue(page.locator("#contact-form").is_visible())
                                        self.assertEqual(errors, [], errors)
                            finally:
                                page.close()
                                context.close()
                    # Mock backend response to verify UI success state without
                    # spending Supabase calls or storing any synthetic customer data.
                    context = browser.new_context(viewport={"width": 390, "height": 850})
                    context.route("**/*", lambda route: (
                        route.continue_() if route.request.url.startswith(base)
                        else route.abort()
                    ))
                    page = context.new_page()
                    try:
                        page.goto(base + "/yhteys/", wait_until="domcontentloaded")
                        page.route("**/kaurivo-kotifixi-demo-contact", lambda route: route.fulfill(
                            status=201, content_type="application/json",
                            body='{"ok":true,"test":true,"reference":"12345678-aaaa-bbbb-cccc-123456789abc"}',
                            headers={"access-control-allow-origin":"*"}
                        ))
                        page.locator("#cust-name").fill("Testi Käyttäjä")
                        page.locator("#cust-email").fill("testi@example.invalid")
                        page.locator("#cust-service").select_option(label="Pihatyöt")
                        page.locator("#cust-message").fill("Tämä on vain tekninen testiviesti.")
                        page.locator('input[name="test_consent"]').check()
                        page.locator(".form-submit").click()
                        page.locator("#form-status").filter(has_text="Testiviesti tallennettu").wait_for()
                        self.assertIn("ei lähetetty Kotifixille", page.locator("#form-status").inner_text())
                    finally:
                        page.close()
                        context.close()
                finally:
                    browser.close()
        finally:
            server.shutdown()
            server.server_close()
            runner.join(timeout=5)


    def test_v11_pointer_3d_depth_does_not_intercept_native_scroll(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError as exc:
            raise unittest.SkipTest("Playwright unavailable") from exc
        server = ThreadingHTTPServer(("127.0.0.1", 0),
                                     partial(Handler, directory=str(ROOT)))
        worker = threading.Thread(target=server.serve_forever, daemon=True)
        worker.start()
        base = f"http://127.0.0.1:{server.server_port}"
        try:
            with sync_playwright() as pw:
                try:
                    browser = pw.chromium.launch(headless=True)
                except Exception as exc:
                    raise unittest.SkipTest("Chromium unavailable: " + str(exc)) from exc
                try:
                    context = browser.new_context(
                        viewport={"width": 1440, "height": 860},
                        reduced_motion="no-preference",
                    )
                    context.route("**/*", lambda route: (
                        route.continue_() if route.request.url.startswith(base)
                        else route.abort()
                    ))
                    page = context.new_page()
                    page.goto(base + "/", wait_until="domcontentloaded")
                    self.assertTrue(page.locator(".hero-visual-3d").is_visible())
                    self.assertEqual(page.evaluate("scrollY"), 0)
                    frame = page.locator(".hero-photo-frame")
                    box = frame.bounding_box()
                    page.mouse.move(box["x"] + box["width"] * .75,
                                    box["y"] + box["height"] * .35)
                    page.wait_for_function("""() => {
                        const el=document.querySelector('.hero-photo-frame');
                        return el.style.getPropertyValue('--hero-tilt-y') !== '';
                    }""")
                    self.assertNotEqual(
                        frame.evaluate("(el)=>el.style.getPropertyValue('--hero-tilt-y')"), ""
                    )
                    self.assertEqual(page.evaluate("scrollY"), 0)
                    page.mouse.wheel(0, 550)
                    page.wait_for_function("window.scrollY > 0")
                    self.assertGreater(page.evaluate("scrollY"), 0)
                    self.assertEqual(page.evaluate("getComputedStyle(document.documentElement).scrollBehavior"),
                                     "auto")
                    page.close()
                    context.close()
                    motionless = browser.new_context(
                        viewport={"width": 390, "height": 844},
                        reduced_motion="reduce", has_touch=True,
                    )
                    motionless.route("**/*", lambda route: (
                        route.continue_() if route.request.url.startswith(base)
                        else route.abort()
                    ))
                    mobile = motionless.new_page()
                    mobile.goto(base + "/", wait_until="domcontentloaded")
                    self.assertEqual(mobile.locator(".scroll-reveal").count(), 0)
                    self.assertEqual(mobile.locator(".hero-photo-frame").evaluate(
                        "(el) => getComputedStyle(el).transform"
                    ), "none")
                    self.assertTrue(mobile.locator("h1").is_visible())
                    mobile.close()
                    motionless.close()
                finally:
                    browser.close()
        finally:
            server.shutdown()
            server.server_close()
            worker.join(timeout=5)



if __name__ == "__main__":
    unittest.main()

"""Offline browser checks for the private Kaurivo feedback page.

All outbound form requests are mocked; tests never send feedback or spend credits.
"""
import json
import os
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] / "docs" / "kaurivo"
PAGE = ROOT / "feedback" / "index.html"
JS = ROOT / "assets" / "customer-feedback.js"


class FeedbackMarkupTests(unittest.TestCase):
    def test_form_has_five_local_stars_and_real_fields(self):
        html = PAGE.read_text(encoding="utf-8")
        script = JS.read_text(encoding="utf-8")
        self.assertIn('id="customer-feedback-form"', html)
        self.assertEqual(html.count('name="rating"'), 5)
        self.assertIn('name="message"', html)
        self.assertIn('name="email"', html)
        self.assertIn('name="company"', html)
        self.assertIn('name="privacy_ack"', html)
        self.assertIn("xhsfbcwpwbgdbatrcyuk.supabase.co/functions/v1/kaurivo-feedback-submit", html)
        self.assertIn("data.success === true", script)
        self.assertIn('get("invite")', script)
        self.assertNotIn("formsubmit.co", html)
        self.assertIn("event.preventDefault()", script)
        self.assertIn("feedback-status-error", (ROOT / "assets" / "site-v3.css").read_text())
        self.assertNotIn("mailto:", script)

    def test_browser_feedback_flow(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            if os.environ.get("REQUIRE_BROWSER_TESTS") == "1":
                self.fail("Playwright is required")
            self.skipTest("Playwright not installed")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--disable-gpu"])
            try:
                for width in (320, 390, 1440):
                    with self.subTest(width=width):
                        page = browser.new_page(viewport={"width": width, "height": 850})
                        errors = []
                        page.on("pageerror", lambda e: errors.append(str(e)))
                        page.route("https://fonts.googleapis.com/**", lambda r: r.abort())
                        page.route("https://fonts.gstatic.com/**", lambda r: r.abort())
                        # All submissions are locally faked. No actual customer data goes out.
                        page.add_init_script("""window.__feedbackMockSuccess=false;
window.fetch=async () => ({
    ok:true,
    json:async()=>({success:window.__feedbackMockSuccess})
});""")
                        page.goto(PAGE.as_uri() + "?lang=fi&rating=2#invite=" + "A"*43,
                                  wait_until="domcontentloaded")
                        page.wait_for_timeout(90)
                        self.assertEqual(page.locator("html").get_attribute("lang"), "fi")
                        self.assertEqual(page.locator('input[name="rating"]:checked').input_value(), "2")
                        page.locator(".feedback-star-options label").nth(3).click()
                        self.assertEqual(page.locator('input[name="rating"]:checked').input_value(), "4")
                        self.assertEqual(page.locator(".feedback-star-options label.is-lit").count(), 4)
                        self.assertIn("#invite=", page.url)
                        page.locator("#feedback-message").fill("Hyvin alkanut yhteistyö.")
                        page.locator("#feedback-company").fill("Demo Oy")
                        page.locator("#feedback-email").fill("demo@example.invalid")
                        page.locator('input[name="privacy_ack"]').check()
                        page.locator("#feedback-submit").click()
                        page.wait_for_timeout(120)
                        self.assertFalse(page.locator(".customer-feedback-form").evaluate(
                            "(f) => f.classList.contains('feedback-sent')"))
                        self.assertTrue(page.locator(".feedback-status-error").is_visible())
                        page.evaluate("window.__feedbackMockSuccess=true")
                        page.locator("#feedback-submit").click()
                        page.wait_for_timeout(120)
                        self.assertTrue(page.locator(".feedback-status-success").is_visible())
                        self.assertTrue(page.locator("#feedback-submit").is_disabled())
                        self.assertNotIn("#invite=", page.url)
                        self.assertEqual(errors, [])
                        overflow = page.evaluate(
                            "Math.max(document.documentElement.scrollWidth, document.body.scrollWidth) - innerWidth")
                        self.assertLessEqual(overflow, 2, (width, overflow))
                        page.close()
            finally:
                browser.close()


if __name__ == "__main__":
    unittest.main()

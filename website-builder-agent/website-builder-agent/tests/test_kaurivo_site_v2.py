"""Kaurivo public V2 landing: offline browser and content regression tests.

Zero API usage, email sending, image generation or third-party deployment.
"""
from pathlib import Path
import unittest
from html.parser import HTMLParser

SITE = Path(__file__).resolve().parents[1] / "docs" / "kaurivo" / "index.html"


class AuditParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.links = []
        self.forms = 0
        self.details = 0
        self.images = []

    def handle_starttag(self, tag, attrs):
        attributes = dict(attrs)
        if "id" in attributes:
            self.ids.add(attributes["id"])
        if tag == "a":
            self.links.append(attributes.get("href", ""))
        if tag == "form":
            self.forms += 1
        if tag == "details":
            self.details += 1
        if tag == "img":
            self.images.append(attributes.get("src", ""))


class KaurivoV2Tests(unittest.TestCase):
    def test_content_and_lightweight_interaction_contract(self):
        src = SITE.read_text(encoding="utf-8")
        tags = AuditParser()
        tags.feed(src)
        self.assertEqual(tags.forms, 1)
        self.assertGreaterEqual(tags.details, 6)
        self.assertTrue({"top", "services", "process", "faq", "contact", "enquiry-form"}.issubset(tags.ids))
        for phrase in (
            "Need a new premium website for your business?",
            "Can I update the website myself?",
            "Website redesigns",
            "Prepare email enquiry",
            "Your enquiry is <strong>not sent</strong>",
            "hello.kaurivo@gmail.com",
        ):
            self.assertIn(phrase, src)
        for marker in ("getContext(", "requestAnimationFrame(", "assembly-3d", "SCROLL TO ASSEMBLE", "CONCEPT STUDY", "floating-tag"):
            self.assertNotIn(marker, src)
        self.assertIn("prefers-reduced-motion", src)
        self.assertIn("form.reportValidity()", src)
        self.assertIn("mailto:hello.kaurivo@gmail.com?subject=", src)
        self.assertTrue(all(not h.startswith("http") for h in tags.links))
        self.assertTrue((SITE.parent / "assets" / "kaurivo-mark.webp").exists())

    def test_responsive_actual_browser_smoke(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            if __import__("os").environ.get("REQUIRE_BROWSER_TESTS") == "1":
                self.fail("Playwright is needed in CI for browser test")
            self.skipTest("Playwright unavailable outside CI")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--disable-gpu"])
            try:
                for width, height in ((320, 740), (390, 844), (768, 1024), (1440, 900)):
                    with self.subTest(width=width):
                        page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
                        errors = []
                        page.on("pageerror", lambda exception: errors.append(str(exception)))
                        page.goto(SITE.as_uri(), wait_until="domcontentloaded")
                        page.wait_for_timeout(520)
                        overflow = page.evaluate("Math.max(document.documentElement.scrollWidth,document.body.scrollWidth)-innerWidth")
                        self.assertLessEqual(overflow, 2, f"Horizontal overflow: {width}px: {overflow}")
                        self.assertEqual(errors, [])
                        self.assertTrue(page.locator("header .brand-icon").is_visible())
                        self.assertTrue(page.get_by_role("heading", name="Good questions. Clear answers.").count() > 0)
                        # FAQ disclosures work without animation or JS.
                        faq = page.locator("#faq details").first
                        faq.locator("summary").click()
                        self.assert_true_open(faq)
                        page.locator('a[href="#contact"]').first.click()
                        self.assertTrue(page.locator("#enquiry-form").count() == 1)
                        page.close()
            finally:
                browser.close()

    def assert_true_open(self, locator):
        self.assertTrue(locator.evaluate("(el) => el.open"))


if __name__ == "__main__":
    unittest.main()

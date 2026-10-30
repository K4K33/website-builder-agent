"""Quality and interaction checks for Kaurivo's two fictional demo sites.

Uses only local HTML, browser mocks for external images/fonts and no paid APIs.
"""
from pathlib import Path
import os
import unittest
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1] / "docs" / "kaurivo" / "lab"
SITES = {"hearth": ROOT / "service" / "index.html", "stillform": ROOT / "editorial" / "index.html"}


class Tags(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.ids = set()
        self.imgs = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        if tag == "a":
            self.links.append(attrs.get("href", ""))
        if tag == "img":
            self.imgs.append(attrs)


class DesignStudyTests(unittest.TestCase):
    def test_studies_are_original_and_truthful(self):
        for label, file in SITES.items():
            with self.subTest(site=label):
                src = file.read_text(encoding="utf-8")
                parser = Tags()
                parser.feed(src)
                self.assertIn("noindex,nofollow", src)
                self.assertIn("FICTIONAL", src)
                self.assertIn("KAURIVO", src)
                self.assertIn("unsplash.com/license", src)
                self.assertIn('href="../../"', src)
                self.assertIn('href="../../contact/"', src)
                self.assertIn("prefers-reduced-motion:reduce", src)
                self.assertNotIn("scroll-jacking", src)
                self.assertNotIn("getContext(", src)
                self.assertGreaterEqual(len(parser.imgs), 3)
                for image in parser.imgs:
                    if image.get("id") == "lightbox-img":
                        continue  # Source and alt are set when a gallery image opens.
                    self.assertTrue(image.get("alt", "").strip())
                    self.assertTrue(image.get("src", "").startswith("https://images.unsplash.com/"))
                for href in parser.links:
                    if href.startswith("#"):
                        self.assertIn(href[1:], parser.ids, (label, href))
                    elif href.startswith(("http://", "https://", "mailto:")):
                        continue
                    elif href:
                        self.assertTrue((file.parent / href).resolve().exists(), (label, href))

    def test_stillform_gallery_functions_exist(self):
        src = SITES["stillform"].read_text(encoding="utf-8")
        self.assertEqual(src.count('class="project" data-category='), 3)
        self.assertIn('data-filter="space"', src)
        self.assertIn('data-filter="material"', src)
        self.assertIn('role="dialog"', src)
        self.assertIn('aria-modal="true"', src)
        self.assertIn('aria-pressed="true"', src)
        self.assertIn("previous.focus()", src)

    def test_browser_interactions_and_mobile_layout(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            if os.environ.get("REQUIRE_BROWSER_TESTS") == "1":
                self.fail("Playwright required")
            self.skipTest("Playwright unavailable")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--disable-gpu"])
            try:
                for width, height in ((320, 740), (390, 844), (768, 1024), (1440, 900)):
                    for name, filepath in SITES.items():
                        with self.subTest(width=width, site=name):
                            page = browser.new_page(viewport={"width": width, "height": height})
                            errors = []
                            page.on("pageerror", lambda error: errors.append(str(error)))
                            # All images/fonts have CSS fallbacks; prevent quota or network use.
                            page.route("https://images.unsplash.com/**", lambda route: route.abort())
                            page.route("https://fonts.googleapis.com/**", lambda route: route.abort())
                            page.route("https://fonts.gstatic.com/**", lambda route: route.abort())
                            page.goto(filepath.as_uri(), wait_until="domcontentloaded")
                            page.wait_for_timeout(80)
                            self.assertEqual(errors, [], (name, width, errors))
                            overflow = page.evaluate("Math.max(document.body.scrollWidth, document.documentElement.scrollWidth)-innerWidth")
                            self.assertLessEqual(overflow, 2, (name, width, overflow))
                            self.assertTrue(page.locator('a[href="../../"]').first.is_visible())
                            if width < 760:
                                toggle = page.locator(".menu-button" if name == "hearth" else ".menu")
                                self.assertTrue(toggle.is_visible())
                                toggle.click()
                                self.assertEqual(toggle.get_attribute("aria-expanded"), "true")
                                nav = page.locator(".nav-links" if name == "hearth" else "#stillform-nav")
                                self.assertTrue(nav.is_visible())
                                toggle.click()
                                self.assertEqual(toggle.get_attribute("aria-expanded"), "false")
                            if name == "stillform":
                                self.assertEqual(page.locator(".project:visible").count(), 3)
                                page.locator('button[data-filter="material"]').click()
                                self.assertEqual(page.locator(".project:visible").count(), 1)
                                page.locator('button[data-filter="space"]').click()
                                self.assertEqual(page.locator(".project:visible").count(), 2)
                                page.locator('button[data-filter="all"]').click()
                                self.assertEqual(page.locator(".project:visible").count(), 3)
                                page.locator(".project-image").first.click()
                                self.assertEqual(page.locator("#lightbox").get_attribute("aria-hidden"), "false")
                                page.keyboard.press("Escape")
                                self.assertEqual(page.locator("#lightbox").get_attribute("aria-hidden"), "true")
                            page.close()
            finally:
                browser.close()


if __name__ == "__main__":
    unittest.main()

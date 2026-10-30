"""Kaurivo V3 multi-page design and mobile browser regression checks.

Offline only. No API, email, payment or AI credits used.
"""
from html.parser import HTMLParser
from pathlib import Path
import os
import unittest

SITE = Path(__file__).resolve().parents[1] / "docs" / "kaurivo"
PAGES = {
    "home": SITE / "index.html",
    "services": SITE / "services" / "index.html",
    "process": SITE / "process" / "index.html",
    "faq": SITE / "faq" / "index.html",
    "contact": SITE / "contact" / "index.html",
}


class PageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.links = []
        self.headers = 0
        self.details = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if a.get("id"):
            self.ids.add(a["id"])
        if tag == "a":
            self.links.append(a.get("href", ""))
        if tag == "header":
            self.headers += 1
        if tag == "details":
            self.details += 1


class KaurivoWebsiteTests(unittest.TestCase):
    def test_every_page_reuses_brand_and_valid_local_assets(self):
        self.assertTrue((SITE / "assets" / "site-v3.css").exists())
        self.assertTrue((SITE / "assets" / "site-v3.js").exists())
        self.assertTrue((SITE / "assets" / "kaurivo-mark.webp").exists())
        for name, path in PAGES.items():
            with self.subTest(page=name):
                src = path.read_text(encoding="utf-8")
                tags = PageParser()
                tags.feed(src)
                self.assertEqual(tags.headers, 1)
                self.assertIn("main", tags.ids)
                self.assertIn("KAURIVO", src)
                self.assertIn("kaurivo-mark.webp", src)
                self.assertIn("site-v3.js", src)
                self.assertIn("site-v3.css", src)
                for link in tags.links:
                    if not link or link.startswith(("mailto:", "#")):
                        continue
                    self.assertFalse(link.startswith("http"), (name, link))
                    self.assertTrue((path.parent / link).resolve().exists(), (name, link))

    def test_faq_contact_and_process_are_separate_pages(self):
        home = PAGES["home"].read_text(encoding="utf-8")
        faq = PAGES["faq"].read_text(encoding="utf-8")
        process = PAGES["process"].read_text(encoding="utf-8")
        contact = PAGES["contact"].read_text(encoding="utf-8")
        self.assertNotIn("Can I update my website myself?", home)
        self.assertNotIn('id="enquiry-form"', home)
        self.assertNotIn('id="faq-list"', home)
        self.assertIn('id="faq-list"', faq)
        self.assertIn("Can I update my website myself?", faq)
        self.assertGreaterEqual(faq.count("<details>"), 8)
        self.assertIn("data-stage-button", process)
        self.assertIn('id="enquiry-form"', contact)
        self.assertIn('href="faq/"', home)
        for name in ("services", "process", "faq", "contact"):
            page_text = PAGES[name].read_text(encoding="utf-8")
            self.assertIn('class="back-home" href="../"', page_text)
            self.assertIn("Back to Home", page_text)
        self.assertNotIn('class="back-home"', home)
        self.assertIn('href="../faq/"', process)

    def test_animations_present_but_no_heavy_background_loop(self):
        css=(SITE/"assets/site-v3.css").read_text(encoding="utf-8")
        js=(SITE/"assets/site-v3.js").read_text(encoding="utf-8")
        self.assertIn("@keyframes enter", css)
        self.assertIn("@keyframes markdraw", css)
        self.assertIn("@keyframes accent-slide", css)
        self.assertIn("prefers-reduced-motion:reduce", css)
        self.assertIn("IntersectionObserver", js)
        self.assertIn("data-stage-button", js)
        self.assertNotIn("getContext(", js)
        self.assertNotIn("WebGL", js)
        self.assertNotIn("420vh", css)
        self.assertNotIn("backdrop-filter", css)
        self.assertIn("#cad5df", css)
        self.assertNotIn("#1162df", css)
        self.assertNotIn("#2281ff", css)
        self.assertNotIn("pointermove", js)

    def test_responsive_browser_and_working_interactions(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            if os.getenv("REQUIRE_BROWSER_TESTS") == "1":
                self.fail("Playwright required in CI")
            self.skipTest("Playwright unavailable locally")
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True, args=["--disable-gpu"])
            try:
                for width,height in [(320,740),(390,844),(768,1024),(1440,900)]:
                    for name,path in PAGES.items():
                        with self.subTest(width=width,page=name):
                            page=browser.new_page(viewport={"width":width,"height":height})
                            errors=[]
                            page.on("pageerror", lambda error: errors.append(str(error)))
                            page.goto(path.as_uri(),wait_until="domcontentloaded")
                            page.wait_for_timeout(90)
                            overflow=page.evaluate("Math.max(document.documentElement.scrollWidth, document.body.scrollWidth)-innerWidth")
                            self.assertLessEqual(overflow,2,(width,name,overflow))
                            self.assertEqual(errors,[],(width,name,errors))
                            self.assertTrue(page.locator("header .brand-icon").is_visible())
                            if name != "home":
                                back = page.get_by_role("link", name="Back to Home page")
                                self.assertTrue(back.is_visible())
                                self.assertEqual(back.get_attribute("href"), "../")
                            if name=="faq":
                                details=page.locator("#faq-list details").first
                                details.locator("summary").click()
                                self.assertTrue(details.evaluate("(el)=>el.open"))
                            if name=="process":
                                tabs=page.locator("[data-stage-button]")
                                tabs.nth(2).click()
                                self.assertEqual(page.locator(".prototype-window").get_attribute("data-state"),"ready")
                            if name=="contact":
                                self.assertEqual(page.locator("#enquiry-form").count(),1)
                            if width==390 and name=="home":
                                t=page.locator(".mobile-toggle")
                                t.click()
                                self.assertEqual(t.get_attribute("aria-expanded"),"true")
                                self.assertTrue(page.locator('.nav-menu a[href="faq/"]').is_visible())
                            page.close()
            finally:
                browser.close()


if __name__=="__main__":
    unittest.main()

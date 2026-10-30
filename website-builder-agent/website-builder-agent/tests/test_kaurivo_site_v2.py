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
    "work": SITE / "work" / "index.html",
    "privacy": SITE / "privacy" / "index.html",
    "thanks": SITE / "thanks" / "index.html",
    "about": SITE / "about" / "index.html",
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
        self.assertTrue((SITE / "assets" / "i18n.js").exists())
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
                self.assertIn("i18n.js", src)
                self.assertIn("work/", src)
                self.assertIn("about/", src)
                self.assertIn("data-lang-set", src)
                for link in tags.links:
                    if not link or link.startswith(("mailto:", "#")):
                        continue
                    if link.startswith("https://formsubmit.co/"):
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
        self.assertIn('id="selected-work"', home)
        self.assertIn('href="lab/service/"', home)
        self.assertIn('href="lab/editorial/"', home)
        self.assertIn("performance targets, not measured results", process.lower())
        self.assertIn('id="enquiry-form"', contact)
        self.assertIn('href="faq/"', home)
        for name in ("services", "process", "faq", "contact", "work", "about", "privacy", "thanks"):
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
        self.assertIn(".reveal,.reveal.is-visible{opacity:1!important", css)
        self.assertNotIn("IntersectionObserver", js)
        self.assertNotIn('addEventListener("scroll"', js)
        self.assertIn("scroll-behavior:auto", css)
        self.assertIn("v6-logo-complete", css)
        self.assertIn("@keyframes v6-part-a", css)
        self.assertIn("v6-logo-part-three", PAGES["home"].read_text(encoding="utf-8"))
        self.assertNotIn("v4-window-headline", PAGES["home"].read_text(encoding="utf-8"))
        self.assertIn("data-stage-button", js)
        self.assertNotIn("getContext(", js)
        self.assertNotIn("WebGL", js)
        self.assertNotIn("420vh", css)
        self.assertNotIn("backdrop-filter", css)
        self.assertIn("#cad5df", css)
        self.assertNotIn("#1162df", css)
        self.assertNotIn("#2281ff", css)
        self.assertNotIn("pointermove", js)

    def test_original_study_links_and_accessibility(self):
        from html.parser import HTMLParser
        for kind in ("service","editorial"):
            path=SITE/"lab"/kind/"index.html"
            with self.subTest(concept=kind):
                src=path.read_text(encoding="utf-8")
                self.assertIn("noindex,nofollow", src)
                self.assertIn("Fictional", src)
                self.assertIn('href="../../"', src)
                self.assertIn('href="../../contact/"', src)
                self.assertNotIn("getContext(", src)

    def test_iphone_only_mobile_refinement(self):
        css=(SITE/"assets/site-v3.css").read_text(encoding="utf-8")
        js=(SITE/"assets/site-v3.js").read_text(encoding="utf-8")
        i18n=(SITE/"assets/i18n.js").read_text(encoding="utf-8")
        self.assertIn("iPhone/mobile-only refinement", css)
        self.assertIn("@media (max-width:600px)", css)
        self.assertIn("v6-mobile-appear", css)
        self.assertIn("onPhone.matches", js)
        self.assertIn("mobile-menu-open", css)
        self.assertIn('replace(/↗/g,"↗︎")', i18n)
        self.assertNotIn("IntersectionObserver", js)
        self.assertNotIn('addEventListener("scroll"', js)

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
                for width,height in [(320,740),(375,812),(390,844),(430,932),(768,1024),(960,900),(1440,900)]:
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
                            if name == "home":
                                mark = page.locator(".v6-logo-complete")
                                mark.wait_for(state="visible", timeout=3500)
                                self.assertTrue(mark.is_visible())
                                self.assertTrue(page.locator(".delivery-panel").count() == 1)
                                self.assertEqual(page.locator(".v6-work-card").count(), 2)
                                self.assertEqual(page.locator(".service-card").count(), 3)
                            if name != "home":
                                back = page.get_by_role("link", name="Back to Home page")
                                self.assertTrue(back.is_visible())
                                self.assertEqual(back.get_attribute("href"), "../")
                            if name == "contact":
                                form = page.locator("#enquiry-form")
                                self.assertEqual(form.get_attribute("method"), "POST")
                                self.assertIn("formsubmit.co", form.get_attribute("action"))
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
                                self.assertTrue(page.locator("body").evaluate("(b)=>b.classList.contains('mobile-menu-open')"))
                                self.assertEqual(round(page.locator("header").bounding_box()["height"]),64)
                                self.assertEqual(round(page.locator(".nav-menu").bounding_box()["y"]),64)
                                self.assertTrue(page.locator('.nav-menu a[href="about/"]').is_visible())
                                fi = page.locator("[data-lang-set=fi]")
                                fi.click()
                                self.assertEqual(page.locator("html").get_attribute("lang"), "fi")
                                self.assertIn("Verkkosivut", page.locator("#hero-heading").inner_text())
                                t.click()
                                self.assertFalse(page.locator("body").evaluate("(b)=>b.classList.contains('mobile-menu-open')"))
                                self.assertFalse(page.locator(".nav-menu").is_visible())
                            if name=="work":
                                self.assertEqual(page.locator(".v6-work-card").count(),2)
                                self.assertEqual(page.locator('.nav-menu a[href="../faq/"]').count(),1)
                            if width == 1440 and name == "home":
                                self.assertTrue(page.locator(".nav-menu").is_visible())
                                self.assertFalse(page.locator(".mobile-toggle").is_visible())
                                self.assertGreater(page.locator(".v6-logo-stage").bounding_box()["height"],400)
                            if width == 390 and name == "home":
                                self.assertLess(page.locator(".v6-logo-stage").bounding_box()["height"],225)
                            if width == 960 and name == "home":
                                toggle=page.locator(".mobile-toggle")
                                self.assertTrue(toggle.is_visible())
                                toggle.click()
                                self.assertTrue(page.locator(".nav-menu").is_visible())
                                nav_box=page.locator(".nav-menu").bounding_box()
                                header_box=page.locator("header").bounding_box()
                                self.assertGreaterEqual(nav_box["y"], header_box["y"]+header_box["height"]-2)
                                self.assertLessEqual(page.evaluate("document.documentElement.scrollWidth - innerWidth"),2)
                            page.close()
            finally:
                browser.close()


if __name__=="__main__":
    unittest.main()

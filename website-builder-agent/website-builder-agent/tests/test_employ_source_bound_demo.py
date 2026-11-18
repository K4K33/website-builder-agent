"""Employ concept: all pages render offline on real mobile and desktop viewports.

This deliberately does NOT approve fidelity to an inaccessible original brand.
It only tests navigability, local assets, accessible menu, functional contact
action and that no contact data is falsely sent to a server.
"""
from pathlib import Path
import mimetypes
from urllib.parse import unquote, urlsplit
import unittest
import os

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"
BASE = "/website-builder-agent/kaurivo/demos/employ-engineering-concept-v1/"
PAGES = ["", "palvelut/", "toimintatapa/", "yhteys/"]


class EmployConceptTests(unittest.TestCase):
    def test_source_bound_content_and_no_fabricated_references(self):
        folder = DOCS / "kaurivo/demos/employ-engineering-concept-v1"
        for suffix in PAGES:
            html=(folder/suffix/"index.html").read_text(encoding="utf-8")
            self.assertIn('lang="fi"',html)
            self.assertIn('name="robots" content="noindex,nofollow"',html)
            self.assertIn("Insinööritoimisto",html)
            self.assertIn("050 526 1303",html)
            self.assertNotIn("Kaurivon itsenäinen demo",html)
            self.assertNotIn("Tämä on sivuston sisältöehdotus",html)
            self.assertNotIn("Alkuperäistä palveluluetteloa",html)
            self.assertNotIn('aria-hidden="true">↗',html)
            self.assertNotIn("Lorem ipsum",html)
            self.assertNotIn("⭐⭐⭐⭐⭐",html)
        home=(folder/"index.html").read_text(encoding="utf-8")
        services=(folder/"palvelut/index.html").read_text(encoding="utf-8")
        process=(folder/"toimintatapa/index.html").read_text(encoding="utf-8")
        self.assertIn("faq-grid",home)
        self.assertIn("Miten suunnittelutarpeen voi kuvata?",home)
        self.assertIn("Varmista suunnittelutehtävän rajaus.",services)
        self.assertIn("Seuraava vaihe alkaa yhteydenotosta.",process)
        for suffix in PAGES:
            page_text=(folder/suffix/"index.html").read_text(encoding="utf-8")
            self.assertNotIn("Kaurivon ehdottama",page_text)
            self.assertNotIn('aria-hidden="true">↗',page_text)
        js=(folder/"assets/site.js").read_text(encoding="utf-8")
        self.assertIn("navigator.clipboard.writeText",js)
        self.assertNotIn("fetch(",js)
        self.assertNotIn("sendBeacon",js)

    def test_all_real_browser_routes_and_responsive_overflow(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            if os.getenv("REQUIRE_BROWSER_TESTS")=="1":
                self.fail("Playwright browser tests are mandatory")
            self.skipTest("Playwright is not installed")
        def serve(route):
            url=urlsplit(route.request.url)
            requested=unquote(url.path)
            if not requested.startswith(BASE):
                route.fulfill(status=404,content_type="text/plain",body="Not found")
                return
            rel=requested.removeprefix("/website-builder-agent/")
            file=(DOCS/rel)
            if file.is_dir():
                file=file/"index.html"
            if not file.is_file() or DOCS.resolve() not in file.resolve().parents:
                route.fulfill(status=404,content_type="text/plain",body="Not found")
                return
            mime=mimetypes.guess_type(file.name)[0] or "text/plain"
            route.fulfill(status=200,body=file.read_bytes(),content_type=mime)
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True,args=["--disable-gpu"])
            try:
                for width,height in [(320,740),(390,844),(768,1024),(1440,900)]:
                    page=browser.new_page(viewport={"width":width,"height":height})
                    errs=[]
                    page.on("pageerror",lambda e:errs.append(str(e)))
                    page.route("**/*",serve)
                    for suffix in PAGES:
                        with self.subTest(width=width,page=suffix):
                            response=page.goto("http://test.local"+BASE+suffix,
                                               wait_until="domcontentloaded")
                            self.assertEqual(response.status,200)
                            self.assertTrue(page.locator("main h1").is_visible())
                            # Optional private browser-image review evidence.
                            # The source-based premium approval gate remains separate.
                            if (os.getenv("KAURIVO_EMPLOY_VISUAL_REVIEW")=="1"
                                    and width in (320,390,1440)
                                    and suffix in ("","palvelut/","yhteys/")
                                    and (width != 320 or suffix=="")):
                                import base64
                                suffix_name=suffix.replace("/","") or "home"
                                jpeg=page.screenshot(type="jpeg",quality=58,full_page=True,
                                    animations="disabled")
                                print("EMPLOY_VISUAL_"+suffix_name+"_"+str(width)
                                    +"_BEGIN:"+base64.b64encode(jpeg).decode("ascii")
                                    +":EMPLOY_VISUAL_END",flush=True)
                            self.assertTrue(page.locator("a[href^='tel:']").count()>0)
                            if width <= 760:
                                header_phone=page.locator(".header-call")
                                self.assertTrue(header_phone.is_visible())
                                font_size=page.evaluate("parseFloat(getComputedStyle(document.querySelector('.header-call')).fontSize)")
                                self.assertGreaterEqual(font_size,10)
                                rect=header_phone.bounding_box()
                                self.assertGreater(rect["width"],65)
                                self.assertLessEqual(rect["x"]+rect["width"],width+1)
                            overflow=page.evaluate(
                                "document.documentElement.scrollWidth-window.innerWidth"
                            )
                            if overflow > 3:
                                offenders=page.evaluate("""() => Array.from(document.querySelectorAll('body *'))
                                  .map(e => ({tag:e.tagName,cls:String(e.className).slice(0,80),
                                    text:(e.textContent||'').trim().slice(0,60),
                                    right:Math.round(e.getBoundingClientRect().right),
                                    width:Math.round(e.getBoundingClientRect().width)}))
                                  .filter(o=>o.right>window.innerWidth+3)
                                  .slice(0,16)""")
                                print("EMPLOY_OVERFLOW_DEBUG",width,suffix,
                                      offenders,flush=True)
                            self.assertLessEqual(overflow,3,
                                f"Unexpected sideways scroll: {width}px {suffix}: {overflow}")
                            for link in page.locator(".site-nav a").all():
                                href=link.get_attribute("href")
                                self.assertTrue((DOCS / href.removeprefix("/website-builder-agent/") /
                                    "index.html").exists() if href.endswith("/") else True)
                    if width==390:
                        page.goto("http://test.local"+BASE,wait_until="domcontentloaded")
                        page.locator(".menu-toggle").click()
                        self.assertEqual(page.locator(".menu-toggle").get_attribute("aria-expanded"),"true")
                        self.assertTrue(page.locator(".site-nav").is_visible())
                        page.keyboard.press("Escape")
                        self.assertFalse(page.locator(".site-nav").is_visible())
                    page.goto("http://test.local"+BASE+"yhteys/",wait_until="domcontentloaded")
                    page.locator('[name="hanke"]').select_option(label="Koneensuunnitteluun liittyvä tarve")
                    page.locator('[name="tarve"]').fill("Testataan yhteydenottojen sisällön kokoamista.")
                    page.locator('#brief-form button[type="submit"]').click()
                    page.locator("#form-message").wait_for(state="visible")
                    self.assertTrue(page.locator("#form-message").inner_text())
                    self.assertEqual(errs,[])
                    page.close()
            finally:
                browser.close()


if __name__ == "__main__":
    unittest.main()

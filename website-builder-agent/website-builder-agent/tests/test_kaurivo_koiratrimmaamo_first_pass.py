"""First-pass blind-company demo tests: multi-page facts, links and real browser.

No outreach, Tavily, LLM, API credits, fake reservations or fake team photos.
Live external illustrative Unsplash images are checked only in separate
screenshot artifact review; core content must work if they are slow.
"""
from __future__ import annotations
import http.server
from functools import partial
from pathlib import Path
import re
import threading
import unittest
from urllib.parse import urlsplit, unquote

from bs4 import BeautifulSoup

BASE=Path(__file__).resolve().parents[1]/"docs"/"kaurivo"/"demos"/"helsingin-koiratrimmaamo-v1"
PAGES=(
 "index.html","palvelut/index.html","hinnasto/index.html",
 "trimmaajat/index.html","tarina/index.html",
 "sijainti/index.html","ajanvaraus/index.html",
)
BOOKING="https://www.varaaheti.fi/helsinginkoiratrimmaamo/fi"

class HtmlEvidence(unittest.TestCase):
    def test_all_seven_real_new_pages_exist_with_semantic_content(self):
        for name in PAGES:
            with self.subTest(route=name):
                file=BASE/name
                self.assertTrue(file.is_file(),file)
                html=file.read_text(encoding="utf-8")
                soup=BeautifulSoup(html,"html.parser")
                self.assertTrue(html.lower().startswith("<!doctype html"))
                self.assertEqual(len(soup.find_all("h1")),1)
                for t in ("header","main","footer","nav"):
                    self.assertIsNotNone(soup.find(t),name+" "+t)
                self.assertTrue(soup.find("meta",attrs={"name":"description"}))
                self.assertTrue(soup.find("meta",attrs={"name":"viewport"}))
                self.assertTrue(soup.find("a",href="mailto:helsingin.koiratrimmaamo@gmail.com"))
                self.assertTrue(soup.find("a",href="tel:+35891462431"))
                self.assertIn("Viipurinkatu 18",html)
                self.assertIn("konsepti",html.casefold())

    def test_local_page_links_and_local_css_js_always_exist(self):
        for name in PAGES:
            soup=BeautifulSoup((BASE/name).read_text("utf-8"),"html.parser")
            for el in soup.find_all(["a","img","script","link"]):
                attr="href" if el.name in ("a","link") else "src"
                raw=str(el.get(attr) or "")
                if not raw or raw.startswith(("#","mailto:","tel:","http:","https:","data:")):
                    continue
                parsed=urlsplit(raw)
                if parsed.scheme or parsed.netloc: continue
                local=(BASE/name).parent/unquote(parsed.path)
                if local.is_dir():
                    local=local/"index.html"
                with self.subTest(page=name,link=raw):
                    self.assertTrue(local.is_file(),str(local))
                    if parsed.fragment:
                        target=BeautifulSoup(local.read_text("utf-8"),"html.parser")
                        self.assertIsNotNone(target.find(id=parsed.fragment))

    def test_actual_price_table_preserved_instead_of_sample_prices(self):
        soup=BeautifulSoup((BASE/"hinnasto/index.html").read_text("utf-8"),"html.parser")
        text=soup.get_text(" ",strip=True)
        for fact in ("93–120 €","96–130 €","110–160 €","75–100 €",
                     "109–145 €","45–65 €","35–40 €","15 €","13 €","25,5 %","24 tuntia","50 %"):
            with self.subTest(fact=fact):
                self.assertIn(fact,text)
        self.assertGreaterEqual(len(soup.find_all("table")),6)

    def test_real_business_history_team_accessibility_and_restrictions(self):
        pages={name:BeautifulSoup((BASE/name).read_text("utf-8"),"html.parser").get_text(" ",strip=True)
               for name in PAGES}
        self.assertIn("1975",pages["tarina/index.html"])
        self.assertIn("Anja Luoso",pages["tarina/index.html"])
        self.assertIn("2013",pages["tarina/index.html"])
        self.assertIn("Emilia Savolainen",pages["trimmaajat/index.html"])
        self.assertIn("Eveliina Tissari",pages["trimmaajat/index.html"])
        self.assertIn("20 kg",pages["palvelut/index.html"])
        self.assertIn("kaksi porrasta",pages["sijainti/index.html"])
        self.assertIn("24 tuntia",pages["ajanvaraus/index.html"])
        self.assertIn("50 %",pages["ajanvaraus/index.html"])
        # Do not invent a back-end booking system; use the existing provider.
        self.assertIn(BOOKING,(BASE/"ajanvaraus/index.html").read_text("utf-8"))
        self.assertNotIn("<form",(BASE/"ajanvaraus/index.html").read_text("utf-8"))
        self.assertNotIn("https://koiratrimmaamo.fi/palvelut",(BASE/"palvelut/index.html").read_text("utf-8"))

    def test_no_generic_ai_antitheses_and_no_fake_company_portraits(self):
        for name in PAGES:
            soup=BeautifulSoup((BASE/name).read_text("utf-8"),"html.parser")
            text=soup.get_text(" ",strip=True).casefold()
            self.assertNotRegex(text,r"vähemmän .{3,60} enemmän ")
            self.assertNotRegex(text,r"ei vain .{3,60} vaan ")
            if name=="trimmaajat/index.html":
                self.assertEqual(len(soup.find_all("img")),0)
            for img in soup.find_all("img"):
                self.assertTrue(img.get("alt"))
                self.assertIn("kuvituskuva",str(img.get("alt")).casefold())
            self.assertIn('name="robots"',str(soup))
        self.assertIn("Kuvituskuvat", (BASE/"index.html").read_text("utf-8"))

class BrowserFirstPass(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from playwright.sync_api import sync_playwright
        cls.server=http.server.ThreadingHTTPServer(
            ("127.0.0.1",0),
            partial(http.server.SimpleHTTPRequestHandler,directory=str(BASE))
        )
        cls.server_thread=threading.Thread(target=cls.server.serve_forever,daemon=True)
        cls.server_thread.start()
        cls.base="http://127.0.0.1:"+str(cls.server.server_address[1])+"/"
        cls.playwright=sync_playwright().start()
        cls.browser=cls.playwright.chromium.launch(headless=True,args=["--no-sandbox"])

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.playwright.stop()
        cls.server.shutdown()
        cls.server.server_close()

    def test_responsive_layout_does_not_overflow_or_hide_main_content(self):
        for width in (320,390,768,1440):
            ctx=self.browser.new_context(viewport={"width":width,"height":870},
                                         reduced_motion="reduce")
            page=ctx.new_page()
            try:
                for name in PAGES:
                    with self.subTest(width=width,page=name):
                        page.goto(self.base+name,wait_until="domcontentloaded",timeout=30000)
                        page.wait_for_timeout(100)
                        self.assertTrue(page.locator("main h1").first.is_visible())
                        ratio=page.evaluate("""() => ({
                          pageWidth:document.documentElement.scrollWidth,
                          viewport:window.innerWidth,
                          mainHeight:document.querySelector('main').getBoundingClientRect().height
                        })""")
                        self.assertLessEqual(ratio["pageWidth"],width+2,
                            f"{width}px {name}: {ratio}")
                        self.assertGreater(ratio["mainHeight"],200)
            finally:
                ctx.close()

    def test_mobile_navigation_is_keyboard_accessible(self):
        context=self.browser.new_context(viewport={"width":390,"height":844})
        page=context.new_page()
        try:
            page.goto(self.base,wait_until="domcontentloaded")
            button=page.locator("[data-menu-toggle]")
            self.assertTrue(button.is_visible())
            self.assertEqual(button.get_attribute("aria-label"),"Avaa valikko")
            button.click()
            self.assertEqual(button.get_attribute("aria-expanded"),"true")
            self.assertTrue(page.locator("#mobiili-nav").is_visible())
            page.keyboard.press("Escape")
            self.assertEqual(button.get_attribute("aria-expanded"),"false")
            button.click()
            page.locator("#mobiili-nav a[href='palvelut/']").click()
            self.assertIn("/palvelut/",page.url)
            self.assertFalse(page.locator("body").evaluate("(el)=>el.classList.contains('menu-open')"))
        finally:
            context.close()

if __name__=="__main__":
    unittest.main()

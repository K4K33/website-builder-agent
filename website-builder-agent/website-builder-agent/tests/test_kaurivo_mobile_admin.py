"""Kaurivo mobile-first admin: local offline Playwright UI checks.

Uses synthetic authenticated client and empty private data; no Supabase,
Gmail, PRH, AI credits or real network calls.
"""
from pathlib import Path
import os
import unittest

SITE=Path(__file__).resolve().parents[1]/"docs"/"kaurivo"
HTML=SITE/"admin"/"index.html"
CSS=SITE/"assets"/"crm.css"
JS=SITE/"assets"/"crm.js"

MOCK=r"""
window.__mockAdmin=true;
window.supabase={createClient:()=>({
 auth:{
  getUser:async()=>({data:{user:{id:'demo',email:'hello.kaurivo@gmail.com',email_confirmed_at:'2026-10-31T00:00:00Z'}},error:null}),
  signOut:async()=>({error:null}),
  onAuthStateChange:()=>({data:{subscription:{unsubscribe:()=>{}}}})
 },
 from:()=>({
  select:()=>({
   eq(){return this;},
   order(){return this;},
   limit:async()=>({data:[],error:null})
  })
 })
})};
"""


class MobileAdminTests(unittest.TestCase):
    def test_mobile_navigation_has_all_six_sections(self):
        html=HTML.read_text(encoding="utf-8")
        js=JS.read_text(encoding="utf-8")
        self.assertIn('id="mobile-dock"',html)
        self.assertIn('id="mobile-more-panel"',html)
        for name in ("prospects","clients","projects","sales","queue","reviews"):
            self.assertIn('data-mobile-tab="'+name+'"',html)
        self.assertIn("navigateMobile",js)
        self.assertIn("closeMobileMore",js)
        self.assertIn('data-count="feedback"',html)
        self.assertIn('id="prospect-list"',html)
        self.assertIn('id="enable-push"',html)
        self.assertIn('id="import-prospects"',html)
        self.assertIn('prefers-reduced-motion',CSS.read_text(encoding="utf-8"))

    def test_mobile_first_screen_and_navigation_with_no_overflow(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            if os.getenv("REQUIRE_BROWSER_TESTS")=="1":
                self.fail("Playwright unavailable")
            self.skipTest("Playwright unavailable")
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True,args=["--disable-gpu"])
            try:
                for width in (320,375,390,430,768,1280):
                    with self.subTest(width=width):
                        page=browser.new_page(viewport={"width":width,"height":844},
                                              device_scale_factor=2)
                        errs=[]
                        page.on("pageerror",lambda error:errs.append(str(error)))
                        page.add_init_script(MOCK)
                        page.route("https://cdn.jsdelivr.net/**",lambda route:route.abort())
                        page.route("https://fonts.googleapis.com/**",lambda route:route.abort())
                        page.route("https://fonts.gstatic.com/**",lambda route:route.abort())
                        page.goto(HTML.as_uri(),wait_until="domcontentloaded")
                        page.wait_for_function("document.querySelector('#m-clients').textContent==='0'")
                        self.assertTrue(page.locator("#tab-prospects").is_visible())
                        if width<=850:
                            self.assertTrue(page.locator("#mobile-dock").is_visible())
                            self.assertFalse(page.locator(".workspace>.tabs").is_visible())
                            self.assertFalse(page.locator("#mobile-more-panel").is_visible())
                            self.assertTrue(page.locator("#morning-summary").is_visible())
                            # Morning leads precede large CRM statistics and notification setup.
                            self.assertLess(
                                page.locator("#tab-prospects").evaluate("(node)=>node.getBoundingClientRect().top"),
                                page.locator("#dashboard>.metrics").evaluate("(node)=>node.getBoundingClientRect().top"))
                            self.assertLess(
                                page.locator("#prospect-list").evaluate("(node)=>node.getBoundingClientRect().top"),
                                page.locator(".push-settings").evaluate("(node)=>node.getBoundingClientRect().top"))
                            for nav in ("prospects","clients","projects"):
                                b=page.locator('#mobile-dock [data-mobile-tab="'+nav+'"]')
                                self.assertGreaterEqual(b.evaluate("(node)=>node.getBoundingClientRect().height"),44)
                                b.click()
                                self.assertTrue(page.locator("#tab-"+nav).is_visible())
                            page.locator("#mobile-more-button").click()
                            self.assertTrue(page.locator("#mobile-more-panel").is_visible())
                            for nav in ("sales","queue","reviews"):
                                page.locator("#mobile-more-button").click() if not page.locator("#mobile-more-panel").is_visible() else None
                                page.locator('#mobile-more-panel [data-mobile-tab="'+nav+'"]').click()
                                self.assertTrue(page.locator("#tab-"+nav).is_visible())
                                self.assertFalse(page.locator("#mobile-more-panel").is_visible())
                            page.locator("#mobile-more-button").click()
                            self.assertEqual(page.locator('[data-count="clients"]').inner_text(),"0")
                            page.locator("#mobile-more-close").click()
                            self.assertFalse(page.locator("#mobile-more-panel").is_visible())
                        else:
                            self.assertFalse(page.locator("#mobile-dock").is_visible())
                            self.assertTrue(page.locator(".workspace>.tabs").is_visible())
                            page.locator('[data-tab="projects"]').click()
                            self.assertTrue(page.locator("#tab-projects").is_visible())
                        self.assertEqual(errs,[])
                        diff=page.evaluate(
                            "Math.max(document.documentElement.scrollWidth,document.body.scrollWidth)-innerWidth")
                        self.assertLessEqual(diff,2,(width,diff))
                        page.close()
            finally:
                browser.close()


if __name__=="__main__":
    unittest.main()

"""Offline quality checks for Kaurivo's separate, admin-only CRM.

No real authentication, API requests, customer data or AI credits are used.
"""
from pathlib import Path
import os
import unittest

ROOT=Path(__file__).resolve().parents[1]/"docs"/"kaurivo"
HTML=ROOT/"admin"/"index.html"
JS=ROOT/"assets"/"crm.js"
CSS=ROOT/"assets"/"crm.css"


class KaurivoCRMTests(unittest.TestCase):
    def test_access_control_and_separation_markers(self):
        html=HTML.read_text(encoding="utf-8")
        js=JS.read_text(encoding="utf-8")
        css=CSS.read_text(encoding="utf-8")
        self.assertIn("noindex,nofollow",html)
        self.assertIn('id="login"',html)
        self.assertIn('id="dashboard" hidden',html)
        self.assertIn('id="invite-dialog"',html)
        for name in ("clients","projects","sales","queue","reviews"):
            self.assertIn('id="tab-'+name+'"',html)
        self.assertIn("sb_publishable_",js)
        self.assertIn("xhsfbcwpwbgdbatrcyuk",js)
        self.assertIn("hello.kaurivo@gmail.com",js)
        self.assertIn("getUser()",js)
        self.assertIn("email_confirmed_at",js)
        self.assertIn("signInWithOtp(",js)
        self.assertIn("kaurivo_prepare_feedback_invitation",js)
        self.assertIn('crypto.getRandomValues',js)
        self.assertIn('crypto.subtle.digest',js)
        self.assertIn('window.confirm(',js)
        self.assertIn('status:"proposal"',js)
        self.assertIn('source_verified:true',js)
        self.assertIn('status:"sent"',js)
        self.assertIn('[hidden]{display:none!important}',css)
        self.assertNotIn("service_role",js.lower())
        self.assertNotIn("OAVIR",html)
        self.assertNotIn("innerHTML",js)
        self.assertNotIn("eval(",js)

    def test_browser_access_and_mobile_layout(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            if os.getenv("REQUIRE_BROWSER_TESTS")=="1":
                self.fail("Playwright unavailable")
            self.skipTest("Playwright unavailable")
        mock_js=r"""
window.supabase={createClient:()=>({
  auth:{
    getUser:async()=>({data:{user:window.__mockAdmin?
       {email:'hello.kaurivo@gmail.com',email_confirmed_at:'2026-10-31T12:00:00Z'}:
       {email:'other@example.invalid',email_confirmed_at:'2026-10-31T12:00:00Z'}},error:null}),
    signOut:async()=>({error:null}),
    signInWithOtp:async()=>({error:null}),
    onAuthStateChange:()=>({data:{subscription:{unsubscribe:()=>{}}}})
  },
  from:(name)=>({select:()=>({order:()=>({limit:async()=>({data:[],error:null})})})})
})};
"""
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True,args=["--disable-gpu"])
            try:
                for width in (375,1280):
                    for admin in (True,False):
                        with self.subTest(width=width,admin=admin):
                            page=browser.new_page(viewport={"width":width,"height":860})
                            page.add_init_script("window.__mockAdmin="+("true" if admin else "false"))
                            page.add_init_script(mock_js)
                            page.route("https://cdn.jsdelivr.net/**",lambda r:r.abort())
                            page.route("https://fonts.googleapis.com/**",lambda r:r.abort())
                            page.route("https://fonts.gstatic.com/**",lambda r:r.abort())
                            errors=[]
                            page.on("pageerror",lambda e:errors.append(str(e)))
                            page.goto(HTML.as_uri(),wait_until="domcontentloaded")
                            page.wait_for_timeout(220)
                            if admin:
                                self.assertTrue(page.locator("#dashboard").is_visible())
                                self.assertFalse(page.locator("#login").is_visible())
                                self.assertEqual(page.locator("#m-clients").inner_text(),"0")
                                page.locator('[data-tab="projects"]').click()
                                self.assertTrue(page.locator("#tab-projects").is_visible())
                                self.assertFalse(page.locator("#tab-clients").is_visible())
                            else:
                                self.assertTrue(page.locator("#login").is_visible())
                                self.assertFalse(page.locator("#dashboard").is_visible())
                            self.assertEqual(errors,[])
                            overflow=page.evaluate(
                                "Math.max(document.body.scrollWidth,document.documentElement.scrollWidth)-innerWidth"
                            )
                            self.assertLessEqual(overflow,2,(width,overflow))
                            page.close()
            finally:
                browser.close()


if __name__=="__main__":
    unittest.main()

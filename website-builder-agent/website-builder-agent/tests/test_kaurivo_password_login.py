"""Offline, fake-Auth Kaurivo regression: password flow bypasses mail-send quota.

No real email, credentials, network requests or AI credits are consumed.
"""
import os
from pathlib import Path
import unittest

SITE=Path(__file__).resolve().parents[1]/"docs"/"kaurivo"
HTML=SITE/"admin"/"index.html"
JS=SITE/"assets"/"crm.js"

FAKE_AUTH=r"""
window.__signedIn=Boolean(window.__openAsAdmin);
window.__mailRequests=0;
window.__passwordWasSet=false;
window.__passwordLogins=0;
const account={id:'admin-001',email:'hello.kaurivo@gmail.com',
               email_confirmed_at:'2026-10-31T12:00:00Z'};
const auth={
 getUser:async()=>({data:{user:window.__signedIn?account:null},error:null}),
 signInWithPassword:async({email,password})=>{
  window.__passwordLogins++;
  if(email===account.email && password==="a-new-unique-password")
    {window.__signedIn=true;return {data:{user:account},error:null};}
  return {data:{user:null},error:{message:'Invalid credentials'}};
 },
 signInWithOtp:async()=>{window.__mailRequests++;return {error:{code:"over_email_send_rate_limit",
                 message:"email rate limit exceeded"}};},
 updateUser:async({password})=>{
  window.__passwordWasSet=password==="a-new-unique-password";
  return {error:window.__passwordWasSet?null:{message:"weak password"}};
 },
 signOut:async()=>{window.__signedIn=false;return {error:null};},
 onAuthStateChange:()=>({data:{subscription:{unsubscribe:()=>{}}}})
};
window.supabase={createClient:()=>({
 auth,
 from:()=>({select:()=>({eq(){return this;},order(){return this;},
                          limit:async()=>({data:[],error:null})})})
})};
"""


class PasswordLoginTests(unittest.TestCase):
    def test_no_secrets_and_ui_is_explicit(self):
        html=HTML.read_text(encoding="utf-8")
        js=JS.read_text(encoding="utf-8")
        for x in ('id="password-login-form"','id="admin-password"',
                  'id="password-dialog"','id="new-admin-password"',
                  'id="confirm-admin-password"','autocomplete="new-password"'):
            self.assertIn(x,html)
        self.assertIn("auth.updateUser({password})",js)
        self.assertIn("auth.signInWithPassword({email,password})",js)
        self.assertIn("shouldCreateUser:false",js)
        self.assertNotIn("sb_secret_",js)
        self.assertNotIn("innerHTML",js)

    def test_existing_safari_admin_can_set_password_and_pwa_signs_in(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            if os.getenv("REQUIRE_BROWSER_TESTS")=="1":
                self.fail("Playwright unavailable")
            self.skipTest("Playwright unavailable")
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True,args=["--disable-gpu"])
            try:
                for safari in (True,False):
                    page=browser.new_page(viewport={"width":390,"height":844})
                    errors=[]
                    page.on("pageerror",lambda e:errors.append(str(e)))
                    page.add_init_script("window.__openAsAdmin="+("true" if safari else "false"))
                    page.add_init_script(FAKE_AUTH)
                    page.route("https://cdn.jsdelivr.net/**",lambda r:r.abort())
                    page.route("https://fonts.googleapis.com/**",lambda r:r.abort())
                    page.goto(HTML.as_uri(),wait_until="domcontentloaded")
                    if safari:
                        page.wait_for_function("document.querySelector('#dashboard').hidden === false")
                        page.locator("#mobile-more-button").click()
                        page.locator("#mobile-password-setup").click()
                        self.assertTrue(page.locator("#password-dialog").is_visible())
                        page.locator("#new-admin-password").fill("a-new-unique-password")
                        page.locator("#confirm-admin-password").fill("a-new-unique-password")
                        page.locator("#save-password").click()
                        page.wait_for_function("window.__passwordWasSet === true")
                        self.assertFalse(page.locator("#password-dialog").is_visible())
                        self.assertEqual(page.evaluate("window.__mailRequests"),0)
                    else:
                        page.wait_for_function("document.querySelector('#login').hidden === false")
                        page.locator("#admin-password").fill("a-new-unique-password")
                        page.locator("#password-login").click()
                        page.wait_for_function("document.querySelector('#dashboard').hidden === false")
                        self.assertEqual(page.evaluate("window.__passwordLogins"),1)
                        self.assertEqual(page.evaluate("window.__mailRequests"),0)
                        self.assertEqual(page.evaluate("document.querySelector('#admin-password').value"),"")
                    self.assertFalse(errors,errors)
                    self.assertLessEqual(page.evaluate(
                        "Math.max(document.body.scrollWidth,document.documentElement.scrollWidth)-innerWidth"),2)
                    page.close()
            finally:
                browser.close()


if __name__=="__main__":
    unittest.main()

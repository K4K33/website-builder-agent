"""Kaurivo CRM: offline security and browser tests, no billable API calls."""
import unittest
from pathlib import Path
from functools import partial
from threading import Thread
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

SITE = Path(__file__).resolve().parents[1]/"docs"/"kaurivo"
PAGE = SITE/"admin"/"index.html"
JS = SITE/"assets"/"kaurivo-admin.js"
CSS = SITE/"assets"/"kaurivo-admin.css"

class AdminSurfaceTests(unittest.TestCase):
 def test_admin_private_not_linked_into_public_navigation(self):
  page=PAGE.read_text(encoding="utf-8")
  js=JS.read_text(encoding="utf-8")
  css=CSS.read_text(encoding="utf-8")
  self.assertIn('noindex,nofollow,noarchive',page)
  self.assertIn('id="login-screen"',page)
  self.assertIn('id="app"',page)
  self.assertIn('class="admin-shell" hidden',page)
  self.assertIn('type="module"',page)
  self.assertIn('id="clients-list"',page)
  self.assertIn('id="projects-list"',page)
  self.assertIn('id="sales-list"',page)
  self.assertIn('id="feedback-reviews"',page)
  self.assertIn('id="feedback-queue"',page)
  self.assertIn("sb_publishable_",js)
  self.assertNotIn("service_role",js)
  self.assertNotIn("sb_secret_",js)
  self.assertIn("supabase.auth.getUser()",js)
  self.assertIn("kaurivo_crm_prepare_invitation",js)
  self.assertIn("window.confirm",js)
  self.assertIn("Kaurivo",css)

 def test_browser_login_gate_and_layout(self):
  try:
   from playwright.sync_api import sync_playwright
  except ImportError:
   self.skipTest("Playwright missing")
  class QuietHandler(SimpleHTTPRequestHandler):
   def log_message(self,*args):pass
  server=ThreadingHTTPServer(("127.0.0.1",0),partial(QuietHandler,directory=str(SITE)))
  thread=Thread(target=server.serve_forever,daemon=True)
  thread.start()
  with sync_playwright() as p:
   browser=p.chromium.launch(headless=True,args=["--disable-gpu"])
   try:
    for width in (320,390,1440):
     with self.subTest(width=width):
      page=browser.new_page(viewport={"width":width,"height":820})
      page.route("https://fonts.googleapis.com/**",lambda r:r.abort())
      page.route("https://fonts.gstatic.com/**",lambda r:r.abort())
      page.route("https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2.95.0/+esm",
       lambda r:r.fulfill(status=200,content_type="text/javascript",body="""export function createClient(){
return { auth:{
 async getUser(){return {data:{user:null},error:null}},
 async signInWithOtp(){return {error:null}},
 async signOut(){return {error:null}}
 }};
}""",headers={"Access-Control-Allow-Origin":"*"}))
      page.goto(f"http://127.0.0.1:{server.server_port}/admin/",wait_until="domcontentloaded")
      page.wait_for_timeout(140)
      self.assertTrue(page.locator("#login-screen").is_visible())
      self.assertFalse(page.locator("#app").is_visible())
      page.locator("#login-email").fill("wrong@example.invalid")
      page.locator("#login-btn").click()
      self.assertIn("vain Kaurivon ylläpitotilille",page.locator("#login-status").inner_text())
      self.assertFalse(page.locator("#app").is_visible())
      over=page.evaluate("Math.max(document.documentElement.scrollWidth,document.body.scrollWidth)-innerWidth")
      self.assertLessEqual(over,2,(width,over))
      page.close()
   finally:
    browser.close()
    server.shutdown()
    server.server_close()

if __name__=="__main__":unittest.main()

"""Smoke checks for all three standalone demo previews, no external credits."""
from pathlib import Path
import unittest
from functools import partial
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from threading import Thread

ROOT=Path(__file__).resolve().parents[1]/"docs"/"kaurivo"/"demos"
SITES={
"te-service-v1":("","palvelut/","yritys/","yhteys/"),
"ravintola-rosanne-v1":("","lounas/","juhlat/","yhteys/"),
"rakennuspalvelu-rili-v1":("","palvelut/","kohteet/","yhteys/"),
}
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
class BrowserSmoke(unittest.TestCase):
 def test_layout_and_menu(self):
  try:from playwright.sync_api import sync_playwright
  except ImportError:self.skipTest("Playwright not available")
  server=ThreadingHTTPServer(("127.0.0.1",0),partial(Quiet,directory=str(ROOT)))
  th=Thread(target=server.serve_forever,daemon=True);th.start()
  base="http://127.0.0.1:"+str(server.server_port)
  try:
   with sync_playwright() as pw:
    try:browser=pw.chromium.launch(headless=True)
    except Exception as e:self.skipTest("Chromium unavailable: "+str(e))
    try:
     for site,routes in SITES.items():
      for width in (320,390,768,1024,1440):
       ctx=browser.new_context(viewport={"width":width,"height":850},reduced_motion="reduce")
       ctx.route("**/*",lambda route:route.continue_()
                 if route.request.url.startswith(base) else route.abort())
       page=ctx.new_page()
       try:
        for route in routes:
         with self.subTest(site=site,width=width,route=route):
          response=page.goto(base+"/"+site+"/"+route,wait_until="domcontentloaded")
          self.assertEqual(response.status,200)
          self.assertTrue(page.locator("h1").is_visible())
          self.assertEqual(page.locator(".nav a").count(),4)
          self.assertLessEqual(page.evaluate("document.documentElement.scrollWidth-innerWidth"),1)
          self.assertEqual(page.evaluate("getComputedStyle(document.documentElement).scrollBehavior"),"auto")
          if width<=900:
           self.assertTrue(page.locator(".toggle").is_visible())
           page.locator(".toggle").click()
           self.assertTrue(page.locator(".nav").is_visible())
           self.assertEqual(page.locator(".toggle").get_attribute("aria-expanded"),"true")
           page.keyboard.press("Escape")
           self.assertFalse(page.locator(".nav").is_visible())
          else:self.assertTrue(page.locator(".nav").is_visible())
       finally:page.close();ctx.close()
    finally:browser.close()
  finally:server.shutdown();server.server_close();th.join(timeout=5)
if __name__=="__main__":unittest.main()

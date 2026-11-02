"""Actual new-business visual screenshots; images are external concept illustrations."""
from __future__ import annotations
from functools import partial
from pathlib import Path
from threading import Thread
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
import base64
import sys
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]/"docs"/"kaurivo"/"demos"/"helsingin-koiratrimmaamo-v1"
DEST=Path(__file__).resolve().parents[1]/"output"/"_koiratrimmaamo_qa_shots"
DEST.mkdir(parents=True,exist_ok=True)
server=ThreadingHTTPServer(("127.0.0.1",0),partial(SimpleHTTPRequestHandler,directory=str(ROOT)))
runner=Thread(target=server.serve_forever,daemon=True)
runner.start()
base="http://127.0.0.1:"+str(server.server_address[1])+"/"
try:
 with sync_playwright() as playwright:
  browser=playwright.chromium.launch(headless=True,args=["--no-sandbox"])
  for route,width,height,label in [
      ("",1280,880,"home_desktop"),
      ("",390,860,"home_mobile"),
      ("hinnasto/",1160,850,"pricing_desktop"),
      ("palvelut/",390,850,"services_mobile")]:
   ctx=browser.new_context(viewport={"width":width,"height":height},device_scale_factor=1,reduced_motion="reduce")
   page=ctx.new_page()
   page.goto(base+route,wait_until="domcontentloaded",timeout=30000)
   page.wait_for_timeout(2300)
   loaded=page.locator("main img").evaluate_all(
       "(imgs)=>imgs.map(i=>({url:i.src,loaded:i.complete&&i.naturalWidth>0}))")
   print("KAURIVO_IMAGES",label,loaded)
   file=DEST/(label+".jpg")
   page.screenshot(path=str(file),type="jpeg",quality=61,full_page=False)
   print("QA_SCREENSHOT_"+label.upper()+"_BEGIN")
   print(base64.b64encode(file.read_bytes()).decode("ascii"))
   print("QA_SCREENSHOT_"+label.upper()+"_END")
   ctx.close()
  browser.close()
finally:
 server.shutdown()
 server.server_close()
print("Kaurivo first-pass visual screenshots stored in",DEST)

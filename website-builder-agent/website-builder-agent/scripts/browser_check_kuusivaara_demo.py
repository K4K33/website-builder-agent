"""Evidence-grade real-browser checks for Kuusivaara concept. No customer contact."""
from __future__ import annotations
import json, sys, threading
from pathlib import Path
from functools import partial
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/"docs/kaurivo/demos/kuusivaara-v1"
OUT=ROOT/"output/kuusivaara-browser"
SOURCE=[
 "https://www.verhoomokuusivaara.fi/",
 "https://www.verhoomokuusivaara.fi/Palvelut/",
 "https://www.verhoomokuusivaara.fi/YRITYKSEMME/",
 "https://www.verhoomokuusivaara.fi/Tarinamme/",
 "https://www.verhoomokuusivaara.fi/en/",
]
ROUTES=["","palvelut/","tyot/","tekijat/","tarinamme/","yhteys/","en/","en/services/","en/work/","en/people/","en/story/","en/contact/"]
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*a):pass

def main():
 OUT.mkdir(parents=True,exist_ok=True)
 srv=ThreadingHTTPServer(("127.0.0.1",0),partial(Quiet,directory=str(SITE)))
 threading.Thread(target=srv.serve_forever,daemon=True).start()
 url=f"http://127.0.0.1:{srv.server_port}/"
 report={"source":[],"new":[],"errors":[],"image_delivery":[],"source_complete":False}
 try:
  with sync_playwright() as p:
   browser=p.chromium.launch(headless=True)
   for width in (390,1440):
    ctx=browser.new_context(viewport={"width":width,"height":860},locale="fi-FI")
    page=ctx.new_page()
    for i,source in enumerate(SOURCE):
     record={"source_url":source,"width":width}
     try:
      response=page.goto(source,wait_until="domcontentloaded",timeout=33000)
      page.wait_for_timeout(700)
      record.update(status=response.status if response else None,final_url=page.url,title=page.title(),images=page.locator("img").count())
      record["file"]=f"original-{width}-{i}.png"
      page.screenshot(path=str(OUT/record["file"]),full_page=True,timeout=25000,animations="disabled")
      if record["status"]!=200: report["errors"].append(f"Source HTTP not 200: {record}")
     except Exception as e: report["errors"].append(f"Source {width} {source}: {type(e).__name__} {str(e)[:120]}")
     report["source"].append(record)
    ctx.close()
   for width in (320,390,768,1440):
    ctx=browser.new_context(viewport={"width":width,"height":860},locale="fi-FI")
    page=ctx.new_page()
    for i,route in enumerate(ROUTES):
     record={"route":route,"width":width}
     try:
      response=page.goto(url+route,wait_until="load",timeout=22000)
      record.update(status=response.status if response else None,language=page.locator("html").get_attribute("lang"),
       h1=page.locator("main h1").count(),nav_links=page.locator(".nav a").count(),
       overflow=page.evaluate("document.documentElement.scrollWidth > innerWidth + 2"),
       failed_images=page.evaluate("Array.from(document.images).filter(i=>i.complete && i.naturalWidth===0).length"))
      record["file"]=f"new-{width}-{i}.png"
      page.screenshot(path=str(OUT/record["file"]),full_page=True,animations="disabled",timeout=22000)
      if record["status"]!=200 or record["h1"]!=1 or record["nav_links"]!=6 or record["overflow"]:
       report["errors"].append(f"Bad new route {record}")
      if record["language"]!=("en" if route.startswith("en/") else "fi"):
       report["errors"].append(f"Wrong language {record}")
      if record["failed_images"]:
       report["image_delivery"].append(record)
     except Exception as e:
      report["errors"].append(f"New {width} {route}: {type(e).__name__} {str(e)[:130]}")
     report["new"].append(record)
    ctx.close()
   ctx=browser.new_context(viewport={"width":390,"height":844})
   page=ctx.new_page()
   try:
    page.goto(url+"palvelut/",wait_until="load")
    page.locator("[data-menu]").click()
    if not page.locator("[data-nav]").evaluate("(el)=>el.classList.contains('open')"):
     report["errors"].append("Mobile menu failed to open")
    page.locator("[data-nav] a").first.click()
    page.goto(url+"palvelut/",wait_until="load")
    if page.locator("section.service > .photo").count()!=3:
     report["errors"].append("Service images must be sibling columns, never nested inside text")
    if page.locator("[data-material]").get_attribute("data-material")!="webbing":
     report["errors"].append("Material demo default visual state missing")
    page.locator("[data-fabric] button[data-tab='leather']").click()
    if page.locator("[data-material]").get_attribute("data-material")!="leather":
     report["errors"].append("Material demo not interactive")
    page.goto(url+"tyot/",wait_until="load")
    page.locator("[data-filters] button[data-filter='history']").click()
    if page.locator("[data-gallery]:visible").count()!=3:
     report["errors"].append("Gallery filter returned incorrect count")
    archival=page.locator("[data-gallery]:visible").first
    if not archival.get_attribute("href") or "verhoomokuusivaara.fi/Tarinamme" not in archival.get_attribute("href"):
     report["errors"].append("Unavailable historic photos need working original archive links")
    page.locator("[data-filters] button[data-filter='service']").click()
    if page.locator("[data-gallery]:visible").count()!=3:
     report["errors"].append("Service gallery filter returned incorrect count")
    page.locator("[data-gallery]:visible").first.click()
    if not page.locator("#photo-dialog").evaluate("el=>el.open"):
     report["errors"].append("Service photo dialog failed to open")
    page.locator("[data-close]").click()
    if page.locator("#photo-dialog").evaluate("el=>el.open"):
     report["errors"].append("Photo dialog failed to close")
    page.emulate_media(reduced_motion="reduce")
    page.goto(url,wait_until="load")
    if page.locator("main h1").count()!=1:
     report["errors"].append("Reduced-motion fallback missing")
   except Exception as e: report["errors"].append(f"Interaction failure {type(e).__name__}: {str(e)[:160]}")
   ctx.close()
   # Candidate royalty-free example photos: record exact CDN availability.
   samples=[
    "https://images.pexels.com/photos/34563854/pexels-photo-34563854.jpeg",
    "https://images.pexels.com/photos/29224637/pexels-photo-29224637.jpeg",
    "https://images.pexels.com/photos/36801652/pexels-photo-36801652.jpeg",
    "https://images.pexels.com/photos/31567147/pexels-photo-31567147.jpeg",
   ]
   report["licensed_sample_probes"]=[]
   for target in samples:
    try:
     response=p.request.new_context().get(target,timeout=16000)
     report["licensed_sample_probes"].append({"url":target,"status":response.status,"type":response.headers.get("content-type",""),"size":len(response.body())})
    except Exception as exc:
     report["licensed_sample_probes"].append({"url":target,"error":type(exc).__name__+": "+str(exc)[:80]})
   browser.close()
 finally: srv.shutdown()
 report["source_complete"]=(len(report["source"])==10 and all(i.get("status")==200 and i.get("file") for i in report["source"]))
 manifest_path=ROOT/"data/demo_provenance/kuusivaara-v1.json"
 if manifest_path.exists():
  sys.path.insert(0,str(ROOT))
  from utils.content_parity import source_inventory_sha256
  inventory=json.loads(manifest_path.read_text(encoding="utf-8"))["source_inventory"]
  print("SOURCE_INVENTORY_SHA256",source_inventory_sha256(inventory))

 (OUT/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
 print("LICENSED_IMAGE_PROBES "+json.dumps(report.get("licensed_sample_probes",[])))
 print("KUUSIVAARA_BROWSER_SUMMARY "+json.dumps({"source_captures":len(report["source"]),"new_captures":len(report["new"]),"errors":report["errors"][:20],"image_delivery":report["image_delivery"][:14],"source_complete":report["source_complete"]},ensure_ascii=False))
 return int(bool(report["errors"]))
if __name__=="__main__":sys.exit(main())

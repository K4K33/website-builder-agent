"""Source-only screenshot and structured manifest probe for Penny Lane. No AI/API credits.

The original source browser is observed before a redesign. Results are evidence,
not copyright permission or visual design approval.
"""
from __future__ import annotations
import json
from datetime import datetime,timezone
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

SOURCE="https://pennylane.fi/"
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/"qa-evidence"/"pennylane"/"source"
OUT.mkdir(parents=True,exist_ok=True)

def main():
    observations={}
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        try:
            for width in (390,1440):
                page=browser.new_page(viewport={"width":width,"height":844 if width==390 else 900},device_scale_factor=1)
                page.goto(SOURCE,wait_until="domcontentloaded",timeout=60000)
                page.wait_for_timeout(1400)
                page.evaluate("""async () => {
                  for(const img of document.images) img.loading='eager';
                  window.scrollTo(0,document.body.scrollHeight); await new Promise(r=>setTimeout(r,500));
                  window.scrollTo(0,0); await new Promise(r=>setTimeout(r,500));
                }""")
                page.screenshot(path=str(OUT/f"source-{width}.png"),full_page=True,animations="disabled",timeout=60000)
                probe=page.evaluate("""() => {
                  const elements=[...document.querySelectorAll('body,section,header,main,article,div')].slice(0,650);
                  return {
                    title:document.title, url:location.href,
                    html:document.documentElement.outerHTML,
                    images:[...document.images].map(i=>({
                      src:i.currentSrc||i.src,alt:i.alt,
                      width:i.naturalWidth,height:i.naturalHeight,
                      box:{x:Math.round(i.getBoundingClientRect().x),
                           y:Math.round(i.getBoundingClientRect().y),
                           width:Math.round(i.getBoundingClientRect().width),
                           height:Math.round(i.getBoundingClientRect().height)},
                      ancestor:i.parentElement?.className||''})),
                    videos:[...document.querySelectorAll('video,iframe[src]')].map(x=>({tag:x.tagName,src:x.src||''})),
                    background_images:elements.map(e=>getComputedStyle(e).backgroundImage).filter(s=>s&&s!=='none').slice(0,35),
                    links:[...document.querySelectorAll('a[href]')].map(a=>({text:a.innerText.slice(0,90),url:a.href})).slice(0,150),
                    h1:[...document.querySelectorAll('h1')].map(x=>x.innerText.slice(0,150)),
                    colors:{body:getComputedStyle(document.body).backgroundColor,
                            text:getComputedStyle(document.body).color},
                    visible_text:document.body.innerText.slice(0,20000)
                  }
                }""")
                markup=probe.pop("html","")
                (OUT/f"source-{width}.html").write_text(markup,encoding="utf-8")
                observations[str(width)]=probe
                print("PROBE",width,"images",len(probe["images"]),"backgrounds",len(probe["background_images"]),"videos",probe["videos"],flush=True)
                print("IMAGE_SAMPLE",json.dumps(probe["images"][:18],ensure_ascii=False),flush=True)
                page.close()
        finally:browser.close()
    (OUT/"observations.json").write_text(json.dumps({"checked_at":datetime.now(timezone.utc).isoformat(),
               "source_url":SOURCE,"observations":observations},ensure_ascii=False,indent=2),encoding="utf-8")
    print("SOURCE_CAPTURE_COMPLETE",len(observations),flush=True)
if __name__=="__main__":main()

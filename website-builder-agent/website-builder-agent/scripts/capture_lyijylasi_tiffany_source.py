#!/usr/bin/env python3
"""Capture *actual* public source/new browser evidence for human review.

Only real rendered Playwright pages may create observed data. This script never
turns a failed capture into approved provenance, sends forms or contacts clients.
"""
from __future__ import annotations

import json
import re
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

ORIGINAL = "https://www.lyijylasijatiffany.fi/"
GALLERY = "https://www.lyijylasijatiffany.fi/referenssit"
PREVIEW = "http://127.0.0.1:8765/"
ROUTES = {"home": "", "services": "palvelut/", "works": "tyot/",
          "ordering": "tilaaminen/", "contact": "yhteystiedot/"}
ROOT = Path(__file__).resolve().parents[1]
EVIDENCE = ROOT / "qa-evidence" / "lyijylasi-tiffany" / "source-pair"
EVIDENCE.mkdir(parents=True, exist_ok=True)
manifest = json.loads((ROOT/"data/demo_provenance/lyijylasi-tiffany-v1.json").read_text())
ids = {value for group in manifest["gallery_source_ids"].values() for value in group}
if len(ids) != 23:
    raise RuntimeError("Expected 23 distinct source-gallery media IDs")

all_observations = []
issues = []
def browser_observation(page, source_url: str, target: str, width: int):
    # Collect rendered DOM only. Do not silently invent role or source color.
    data = page.evaluate("""() => {
      const imgs=[...document.images].map(i=>{
        const b=i.getBoundingClientRect();
        return {src:i.currentSrc||i.src, alt:i.alt,
          natural_width:i.naturalWidth,natural_height:i.naturalHeight,
          visible_width:Math.round(b.width), visible_height:Math.round(b.height),
          top:Math.round(b.top), in_header:!!i.closest('header'),
          in_footer:!!i.closest('footer')};
      });
      const computed=getComputedStyle(document.body);
      const cssMotion=[...document.querySelectorAll('*')].filter(e=>{
        const s=getComputedStyle(e);
        return s.animationName!=='none' && s.animationDuration!=='0s';
      }).slice(0,25).map(e=>({tag:e.tagName,cls:String(e.className).slice(0,100)}));
      return {
        title:document.title,
        description:document.querySelector('meta[name="description"]')?.content||'',
        headings:[...document.querySelectorAll('h1,h2,h3')].slice(0,90).map(e=>({level:e.tagName,text:(e.innerText||'').slice(0,220)})),
        page_text:(document.body.innerText||'').slice(0,24000),
        links:[...document.querySelectorAll('a[href]')].slice(0,180).map(e=>({href:e.href,text:(e.innerText||e.getAttribute('aria-label')||'').slice(0,160)})),
        images:imgs, video_count:document.querySelectorAll('video').length,
        iframes:[...document.querySelectorAll('iframe')].map(i=>i.src),
        svg_count:document.querySelectorAll('svg').length,
        canvas_count:document.querySelectorAll('canvas').length,
        css_motion_examples:cssMotion, body_background:computed.backgroundColor,
        fonts:computed.fontFamily, body_scroll_width:document.documentElement.scrollWidth,
        viewport_width:innerWidth
      };
    }""")
    data.update({"source_url":source_url,"target":target,"viewport":width,
                 "observed_at_utc":time.strftime("%Y-%m-%dT%H:%M:%SZ",time.gmtime())})
    return data

with sync_playwright() as pw:
    browser = pw.chromium.launch(headless=True)
    tasks = [("original-home", ORIGINAL), ("original-gallery", GALLERY)] + [
        ("redesign-"+key, PREVIEW+suffix) for key,suffix in ROUTES.items()
    ]
    for label,url in tasks:
        for width,height in [(390,844),(1440,900)]:
            context=browser.new_context(viewport={"width":width,"height":height},
                                        device_scale_factor=1,reduced_motion="reduce")
            page=context.new_page()
            page_errors=[]
            page.on("pageerror",lambda exc:page_errors.append(str(exc)))
            try:
                response=page.goto(url,wait_until="domcontentloaded",timeout=45000)
                page.wait_for_timeout(1200)
                # Scroll to force below-the-fold Wix image loading. Keep captures stable.
                page.evaluate("""async () => {
                  const step=Math.max(440, Math.round(innerHeight*.8));
                  const cap=Math.min(document.documentElement.scrollHeight,25000);
                  for(let y=0;y<cap;y+=step) {
                    window.scrollTo(0,y);
                    await new Promise(r=>setTimeout(r,95));
                  }
                  window.scrollTo(0,0);
                }""")
                page.wait_for_timeout(950)
                obs=browser_observation(page,url,label,width)
                obs["http_status"]=response.status if response else None
                obs["page_errors"]=page_errors
                path=EVIDENCE/f"{label}-{width}.png"
                page.screenshot(path=str(path),full_page=True,
                                animations="disabled",timeout=45000)
                obs["screenshot"]=str(path.relative_to(ROOT))
                all_observations.append(obs)
                print("CAPTURED",label,width,"HTTP",obs["http_status"],
                      "IMG",len(obs["images"]),
                      "DECODED",sum(bool(i["natural_width"]) for i in obs["images"]),
                      "VIDEOS",obs["video_count"],"CANVAS",obs["canvas_count"])
                if obs["http_status"]!=200:
                    issues.append(f"{label} {width}: HTTP {obs['http_status']}")
                if not obs["images"] and label=="original-gallery":
                    issues.append(f"{label} {width}: zero original gallery images")
                if not path.is_file() or path.stat().st_size<2000:
                    issues.append(f"{label} {width}: missing or tiny screenshot")
                if obs["body_scroll_width"]>width+4 and label.startswith("redesign"):
                    issues.append(f"{label} {width}: horizontal overflow")
            except Exception as exc:
                issues.append(f"{label} {width}: {type(exc).__name__}: {exc}")
                print("CAPTURE ERROR",label,width,repr(exc))
            finally:
                context.close()
    browser.close()

original_galleries=[o for o in all_observations if o["target"]=="original-gallery"]
source_ids=set()
for o in original_galleries:
    for i in o["images"]:
        match=re.search(r"7e296a_([0-9a-f]{32})~mv2",i["src"] or "")
        if match:source_ids.add(match.group(1))
missing=sorted(ids-source_ids)
extra=sorted(source_ids-ids)
if missing:
    issues.append("Source gallery browser DOM missing mapped image IDs: "+",".join(missing))
if len(original_galleries)!=2:
    issues.append("Both original-gallery viewport captures required")
if len(all_observations)!=2*len(tasks):
    issues.append(f"Incomplete browser observation set {len(all_observations)}/{2*len(tasks)}")
report={
    "capture_type":"real_playwright_browser_observations_not_independent_approval",
    "original_source_urls":[ORIGINAL,GALLERY],
    "observed_original_gallery_media_ids":sorted(source_ids),
    "source_manifest_ids":sorted(ids),
    "missing_declared_source_photo_ids":missing,
    "unexpected_original_photo_ids":extra,
    "original_and_new_observations":all_observations,
    "issues":issues,
    "read_me":"Capture is browser evidence, not photo rights, aesthetic signoff, or CMS validation."
}
(EVIDENCE/"capture.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
summary={
    "observations":len(all_observations),"expected":2*len(tasks),
    "source_gallery_media_found":len(source_ids),
    "source_gallery_media_missing":len(missing),"issues":issues,
    "capture_json":str(EVIDENCE/"capture.json"),
    "source_desktop":"original-home-1440.png",
    "source_mobile":"original-home-390.png",
    "redesign_desktop":"redesign-home-1440.png",
    "redesign_mobile":"redesign-home-390.png",
    "original_gallery_desktop":"original-gallery-1440.png",
    "original_gallery_mobile":"original-gallery-390.png"
}
(EVIDENCE/"summary.json").write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding="utf-8")
print("BROWSER SOURCE PAIR SUMMARY:",json.dumps(summary,ensure_ascii=False))
raise SystemExit(1 if issues else 0)

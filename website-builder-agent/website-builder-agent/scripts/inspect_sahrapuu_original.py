"""Sahrapuu source page browser inventory for honest parity work.

Source URLs, anchors, header graphics and first-fold screenshots are recorded.
No source media are copied into any demo or sent to customers.
This is evidence collection, NOT copyright permission or client signoff.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
from playwright.sync_api import sync_playwright

OUT=Path("output/sahrapuu-original-audit")
OUT.mkdir(parents=True,exist_ok=True)
DATA={"source":"https://www.sahrapuu.fi/","checked_at":datetime.now(timezone.utc).isoformat(),"captures":[]}
with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True)
    for width in (390,1440):
        context=browser.new_context(viewport={"width":width,"height":900},device_scale_factor=1,reduced_motion="reduce")
        page=context.new_page()
        err=[]
        page.on("pageerror",lambda e:err.append(str(e)[:300]))
        response=page.goto(DATA["source"],wait_until="domcontentloaded",timeout=40000)
        page.wait_for_timeout(800)
        page.screenshot(path=str(OUT/f"original-{width}.png"),full_page=True,animations="disabled",timeout=30000)
        info=page.evaluate("""() => ({
          title:document.title,
          h1:[...document.querySelectorAll('h1')].map(e=>e.innerText.trim()),
          anchorLinks:[...document.querySelectorAll('a[href]')].map(a=>({
            text:(a.innerText||a.getAttribute('aria-label')||a.getAttribute('title')||'').trim().slice(0,140),
            url:a.href, image:a.querySelector('img')?.src || null
          })),
          images:[...document.querySelectorAll('img')].map(img=>({
            src:img.currentSrc||img.src, alt:img.alt,
            width:img.naturalWidth,height:img.naturalHeight,
            visible:img.getBoundingClientRect().width>5 && img.getBoundingClientRect().height>5
          })),
          headers:[...document.querySelectorAll('header,.site-header,.custom-header')].map(e=>({
            tag:e.tagName,classes:e.className,
            background:getComputedStyle(e).backgroundImage,
            text:(e.innerText||'').trim().slice(0,500)
          })),
          social:[...document.querySelectorAll('a[href*="instagram"],a[href*="facebook"]')].map(a=>({
            href:a.href,text:(a.innerText||a.getAttribute('aria-label')||'').trim()
          })),
          bodyFont:getComputedStyle(document.body).fontFamily,
          bodyBackground:getComputedStyle(document.body).backgroundColor,
          bodyText:document.body.innerText.slice(0,12000)
        })""")
        image=OUT/f"original-{width}.png"
        DATA["captures"].append({"viewport":width,"status":response.status if response else None,
             "final_url":page.url,"screenshot_sha256":hashlib.sha256(image.read_bytes()).hexdigest(),
             "page_errors":err,"observation":info})
        context.close()
    browser.close()
(OUT/"source-inventory.json").write_text(json.dumps(DATA,ensure_ascii=False,indent=2),encoding="utf-8")
for c in DATA["captures"]:
    ob=c["observation"]
    print("SOURCE_CAPTURE",json.dumps({
        "viewport":c["viewport"],"status":c["status"],"title":ob["title"],
        "h1":ob["h1"],"headers":ob["headers"],
        "anchorLinks":ob["anchorLinks"],"images":ob["images"],
        "social":ob["social"],"bodyFont":ob["bodyFont"],
        "bodyBackground":ob["bodyBackground"],
        "screenshot_sha256":c["screenshot_sha256"],
        "page_errors":c["page_errors"]
    },ensure_ascii=False)[:17000])

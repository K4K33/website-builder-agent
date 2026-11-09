#!/usr/bin/env python3
"""WOODTOOL real-source-vs-preview browser smoke / editorial evidence.

No human-premium-score fabrication. Captures real upstream original and every
FI/SV redesign route at desktop & mobile; tests navigation, gallery, image
delivery, real pointer response, reduced motion and no horizontal overflow.
"""
from __future__ import annotations
import json
import time
import os
from pathlib import Path

from playwright.sync_api import sync_playwright
from utils.content_parity import source_inventory_sha256

BASE="http://127.0.0.1:8765/"
SOURCE="https://woodtool.fi/"
SVSOURCE="https://woodtool.fi/sv/"
ROUTES=[
    "","palvelut/","tyot/","verstas/","yhteys/",
    "sv/","sv/tjanster/","sv/referenser/","sv/verkstaden/","sv/kontakt/",
]
OUTPUT=Path("qa-evidence/woodtool-v1")
OUTPUT.mkdir(parents=True,exist_ok=True)
manifest=json.loads(Path("data/demo_provenance/woodtool-v1.json").read_text(encoding="utf-8"))
digest=source_inventory_sha256(manifest["source_inventory"])
print("SOURCE_SHA256",digest,flush=True)
results=[]
issues=[]

def note(*args):
    print(*args,flush=True)

def scroll_original(page):
    height=min(page.evaluate("document.documentElement.scrollHeight"),32000)
    for y in range(0,height,850):
        page.evaluate("(y)=>window.scrollTo(0,y)",y)
        page.wait_for_timeout(45)
    page.evaluate("window.scrollTo(0,0)")
    page.wait_for_timeout(650)

with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,args=["--no-sandbox"])
    # Original live source, both official languages; never replace with a
    # generic reference shot when the real site is unavailable.
    for label,url in (("original-fi",SOURCE),("original-sv",SVSOURCE)):
        for width,height in ((390,844),(1440,900)):
            context=browser.new_context(viewport={"width":width,"height":height},locale="fi-FI" if "fi" in label else "sv-SE")
            page=context.new_page()
            try:
                response=page.goto(url,wait_until="domcontentloaded",timeout=60000)
                page.wait_for_timeout(1600)
                text=page.locator("body").inner_text(timeout=7000)
                if not response or response.status>=400 or "WOODTOOL" not in text.upper():
                    issues.append(f"{label} {width}: source not available (HTTP {response.status if response else 'none'})")
                scroll_original(page)
                page.screenshot(path=str(OUTPUT/f"{label}-{width}.png"),full_page=True,timeout=60000,animations="disabled")
                diagnostics=page.evaluate("""() => ({
                    title:document.title,
                    photos:[...document.images].slice(0,15).map(i=>({src:i.currentSrc||i.src,width:i.naturalWidth})),
                    hasVideo:!!document.querySelector('video'),
                    imagesTotal:document.images.length,
                    firstText:document.body.innerText.slice(0,1200)
                })""")
                (OUTPUT/f"{label}-{width}.json").write_text(json.dumps(diagnostics,ensure_ascii=False,indent=2))
                note("ORIGINAL_CAPTURE",label,width,response.status if response else "none",diagnostics["imagesTotal"])
            except Exception as error:
                issues.append(f"{label} {width}: source browser exception: {type(error).__name__}: {error}")
            finally:context.close()
    for width,height in ((320,740),(390,844),(768,900),(1440,900)):
        context=browser.new_context(
            viewport={"width":width,"height":height},
            device_scale_factor=1,
            reduced_motion="reduce",
            locale="fi-FI",
        )
        page=context.new_page()
        errors=[]
        page.on("pageerror",lambda err: errors.append(str(err)))
        targets=ROUTES if width in (390,1440) else ["","palvelut/","tyot/","yhteys/","sv/","sv/tjanster/","sv/referenser/","sv/kontakt/"]
        for route in targets:
            try:
                response=page.goto(BASE+route,wait_until="domcontentloaded",timeout=45000)
                page.evaluate("""() => document.querySelectorAll('img[loading="lazy"]').forEach(i=>i.loading='eager')""")
                page.wait_for_timeout(1000)
                page.evaluate("""async () => await Promise.race([
                  Promise.all([...document.images].map(i=>i.decode().catch(()=>null))),
                  new Promise(done=>setTimeout(done,15000))])""")
                state=page.evaluate("""() => ({
                    heading:document.querySelectorAll('main h1').length,
                    language:document.documentElement.lang,
                    nav:document.querySelectorAll('.main-nav a').length,
                    active:document.querySelectorAll('.main-nav [aria-current=page]').length,
                    overflow:document.documentElement.scrollWidth-innerWidth,
                    hiddenOnReduce:[...document.querySelectorAll('[data-reveal]')].filter(
                        e=>getComputedStyle(e).opacity==='0').length,
                    images:document.images.length,
                    broken:[...document.images].filter(i=>!i.naturalWidth).map(i=>i.currentSrc||i.src).slice(0,12),
                    sourceImgs:[...document.images].filter(i=>(i.currentSrc||i.src).includes('woodtool.fi/wp-content/')).length,
                    links:[...document.querySelectorAll('.main-nav a')].map(a=>a.getAttribute('href'))
                })""")
                name=route.replace("/","_").strip("_") or "fi-home"
                if not response or response.status!=200:issues.append(f"{route or 'home'} {width}: HTTP {response.status if response else None}")
                if state["heading"]!=1 or state["nav"]!=5 or state["active"]!=1:
                    issues.append(f"{name} {width}: main/navigation structure wrong: {state['heading']} h1 / {state['nav']} nav / {state['active']} active")
                if state["overflow"]>3: issues.append(f"{name} {width}: horizontal overflow {state['overflow']}px")
                if state["hiddenOnReduce"]:issues.append(f"{name} {width}: reduced motion hides content")
                if state["broken"]:issues.append(f"{name} {width}: broken images {state['broken'][:3]}")
                if route.startswith("sv/") and state["language"]!="sv":issues.append(f"{name}: Swedish language absent")
                if not route.startswith("sv/") and state["language"]!="fi":issues.append(f"{name}: Finnish language absent")
                if width in (390,1440):
                    page.screenshot(path=str(OUTPUT/f"new-{name}-{width}.png"),full_page=True,timeout=60000,animations="disabled")
                if width==390:
                    menu=page.locator("[data-menu]")
                    menu.click()
                    if menu.get_attribute("aria-expanded")!="true": issues.append(f"{name}: menu does not open")
                    page.keyboard.press("Escape")
                    if menu.get_attribute("aria-expanded")!="false":issues.append(f"{name}: Escape does not close menu")
                if route in ("tyot/","sv/referenser/") and width==390:
                    filters=page.locator("[data-filter]")
                    gallery=page.locator("[data-category]")
                    if filters.count()!=5 or gallery.count()<8:issues.append(f"{name}: gallery incomplete")
                    page.locator('[data-filter="portaat"]').click()
                    if not (page.locator('[data-category="portaat"]:visible').count()>0 and
                            page.locator('[data-category="ovet"]:visible').count()==0):
                        issues.append(f"{name}: project filter not working")
                    page.locator('[data-filter="all"]').click()
                    page.locator("[data-image-open]").first.click()
                    if page.locator("dialog[open]").count()!=1:issues.append(f"{name}: lightbox cannot open")
                    page.locator("[data-close-dialog]").click()
                    if page.locator("dialog[open]").count()!=0:issues.append(f"{name}: lightbox cannot close")
                results.append({"route":route,"width":width,"http":response.status if response else None,**state})
                note("PAGE_CHECK",name,width,"broken",len(state["broken"]),"overflow",state["overflow"])
            except Exception as error:
                issues.append(f"{route or 'home'} {width}: {type(error).__name__}: {str(error)[:240]}")
        if errors: issues.append("JavaScript page errors width="+str(width)+": "+repr(errors[:3]))
        context.close()
    # No-preference/real pointer render test, with mobile reduction preserving
    # content. Does not make an aesthetic or frame-rate claim.
    context=browser.new_context(viewport={"width":1440,"height":900},reduced_motion="no-preference")
    page=context.new_page()
    try:
        page.goto(BASE,wait_until="load",timeout=50000)
        v=page.locator('[data-premium-interaction="pointer-depth"]')
        box=v.bounding_box()
        if not box:issues.append("hero depth target missing")
        else:
            page.mouse.move(box["x"]+box["width"]*.25,box["y"]+box["height"]*.22)
            page.wait_for_timeout(500)
            first=v.evaluate("(el)=>getComputedStyle(el).getPropertyValue('--px').trim()")
            page.mouse.move(box["x"]+box["width"]*.76,box["y"]+box["height"]*.68)
            page.wait_for_timeout(500)
            second=v.evaluate("(el)=>getComputedStyle(el).getPropertyValue('--px').trim()")
            if not first or first==second:issues.append("premium material-light motion is visually inert")
            results.append({"route":"fi-home","width":1440,"test":"pointer-depth","before":first,"after":second})
            note("POINTER_DEPTH",first,second)
    except Exception as error:issues.append(f"Depth browser test: {error}")
    finally:context.close();browser.close()
report={"source_inventory_sha256":digest,"checks":results,"issues":issues,
        "independent_review":"NOT VERIFIED",
        "media_rights":"NOT VERIFIED","client_editable_CMS":"NOT VERIFIED",
        "end_to_end_delivery":"N/A: source uses direct phone/email; no form observed"}
(OUTPUT/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
note("RESULT",len(results),"browser checks;",len(issues),"issues")
for issue in issues:note("FAIL",issue)
raise SystemExit(1 if issues else 0)

#!/usr/bin/env python3
"""Real Chromium source/new browser audit for Kati first-pass concept.

Purpose: verify pixels, media, nav, gallery and reduced-motion; subjective
premium review and image-rights/true CMS validation remain separate.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
from playwright.sync_api import sync_playwright

BASE="http://127.0.0.1:8765/"
PAGES={"etusivu":"","palvelut":"palvelut/","tyot":"tyot/","tekija":"tekija/","yhteys":"yhteys/"}
OUT=Path("qa-evidence/erikoismaalari-kati-v1")
OUT.mkdir(parents=True,exist_ok=True)
issues,checks=[],[]
with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True,args=["--no-sandbox"])
    # Original source: verify actual browser-displayed source and save comparison
    for width,height in ((390,844),(1440,900)):
        ctx=browser.new_context(viewport={"width":width,"height":height},locale="fi-FI")
        page=ctx.new_page()
        try:
            resp=page.goto("https://erikoismaalari.fi/",wait_until="domcontentloaded",timeout=45000)
            page.wait_for_timeout(1600)
            source=page.evaluate("""() => ({
              title:document.title, images:[...document.images].map(x=>({url:x.src,naturalWidth:x.naturalWidth})),
              text:document.body.innerText.slice(0,1300)
            })""")
            page.screenshot(path=str(OUT/f"alkuperainen-{width}.png"),full_page=True,timeout=45000,animations="disabled")
            (OUT/f"alkuperainen-{width}.json").write_text(json.dumps(source,ensure_ascii=False,indent=2))
            if not resp or resp.status>=400:issues.append(f"Original site {width}: HTTP {resp.status if resp else None}")
            if "Kati" not in source["text"]:issues.append(f"Original site {width}: company identity absent")
        except Exception as exc:issues.append(f"Original browser capture {width}: {exc}")
        finally:ctx.close()

    for name,route in PAGES.items():
        for width,height in ((320,740),(390,844),(768,900),(1440,900)):
            ctx=browser.new_context(viewport={"width":width,"height":height},locale="fi-FI",
                                    reduced_motion="reduce",device_scale_factor=1)
            page=ctx.new_page()
            runtime=[]
            page.on("pageerror",lambda error:runtime.append(str(error)))
            try:
                resp=page.goto(BASE+route,wait_until="domcontentloaded",timeout=40000)
                page.evaluate("""() => document.querySelectorAll('img[loading="lazy"]').forEach(i=>i.loading='eager')""")
                page.wait_for_timeout(1300)
                page.evaluate("""async () => await Promise.race([
                  Promise.all([...document.images].map(i=>i.decode().catch(()=>null))),
                  new Promise(done=>setTimeout(done,11000))])""")
                result=page.evaluate("""() => ({
                  h1:document.querySelectorAll('main h1').length,
                  nav:document.querySelectorAll('nav.nav a').length,
                  active:document.querySelectorAll('nav.nav a[aria-current="page"]').length,
                  overflow:document.documentElement.scrollWidth-innerWidth,
                  images:document.images.length,
                  failedImages:[...document.images].filter(i=>i.naturalWidth===0).map(i=>i.src),
                  reduced:matchMedia('(prefers-reduced-motion: reduce)').matches,
                  revealVisible:[...document.querySelectorAll('[data-reveal]')].every(el=>getComputedStyle(el).opacity==='1'),
                  logoOriginal:[...document.images].some(i=>i.src.includes('erikoismaalari.fi/assets/images/image03.png'))
                })""")
                checks.append({"page":name,"viewport":width,"http":resp.status if resp else None,**result})
                if result["overflow"]>3:issues.append(f"{name} {width}: horizontal overflow {result['overflow']}")
                if result["h1"]!=1 or result["nav"]!=5 or result["active"]!=1:
                    issues.append(f"{name} {width}: navigation or single H1 invalid: {result}")
                if result["failedImages"]:issues.append(f"{name} {width}: broken source image {result['failedImages'][:2]}")
                if not result["logoOriginal"]:issues.append(f"{name} {width}: source logo missing")
                if not result["reduced"] or not result["revealVisible"]:
                    issues.append(f"{name} {width}: prefers-reduced-motion does not show main content")
                if runtime:issues.append(f"{name} {width}: JS runtime errors {runtime}")
                if width==390:
                    page.screenshot(path=str(OUT/f"uusi-{name}-{width}.png"),full_page=True,animations="disabled",timeout=45000)
                if width==1440:
                    page.screenshot(path=str(OUT/f"uusi-{name}-{width}.png"),full_page=True,animations="disabled",timeout=45000)
                if width==390:
                    menu=page.locator("[data-menu]")
                    menu.click()
                    if menu.get_attribute("aria-expanded")!="true":
                        issues.append(f"{name}: mobile menu cannot open")
                    page.keyboard.press("Escape")
                    if menu.get_attribute("aria-expanded")!="false":
                        issues.append(f"{name}: mobile menu Escape broken")
                if name=="tyot" and width==390:
                    if page.locator("[data-open-image]").count()!=3:
                        issues.append("Gallery must contain exact 3 original site photographs")
                    page.locator("[data-open-image]").first.click()
                    if not page.locator("dialog[open]").count():
                        issues.append("Gallery viewer cannot be opened")
                    page.locator("dialog [data-close]").click()
                    if page.locator("dialog[open]").count():
                        issues.append("Gallery viewer cannot be closed")
            except Exception as exc:issues.append(f"{name} {width}: exception {exc}")
            finally:ctx.close()
    # Separate real pointer test; never fake a 3D browser interaction screenshot
    ctx=browser.new_context(viewport={"width":1440,"height":900},reduced_motion="no-preference")
    page=ctx.new_page()
    try:
        page.goto(BASE,wait_until="domcontentloaded",timeout=40000)
        box=page.locator(".hero").bounding_box()
        page.mouse.move(box["x"]+box["width"]*.35,box["y"]+box["height"]*.35)
        page.wait_for_timeout(300)
        mx=page.locator(".hero").evaluate("(e)=>getComputedStyle(e).getPropertyValue('--mx').trim()")
        if not mx:issues.append("Pointer-controlled material lighting did not react")
        checks.append({"page":"hero-pointer","viewport":1440,"light_x":mx})
    except Exception as exc: issues.append(f"Pointer enhancement test: {exc}")
    finally:ctx.close()
    browser.close()

report={"checks":checks,"issues":issues,
        "independent_premium_score":"NOT VERIFIED",
        "client_cms_edit_save_publish":"NOT IMPLEMENTED",
        "media_reuse_permission":"NOT VERIFIED"}
(OUT/"browser-report.json").write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
print(f"KATI BROWSER: {len(checks)} checks, {len(issues)} issues",flush=True)
for i in issues: print("FAIL:",i,flush=True)
raise SystemExit(1 if issues else 0)

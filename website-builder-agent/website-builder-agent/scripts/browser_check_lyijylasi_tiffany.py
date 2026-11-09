#!/usr/bin/env python3
"""Browser QA evidence, not a substitute for independent premium or CMS acceptance."""
import json, os
from pathlib import Path
from playwright.sync_api import sync_playwright
BASE="http://127.0.0.1:8765/"
PAGES={"home":"","services":"palvelut/","works":"tyot/","ordering":"tilaaminen/","contact":"yhteystiedot/"}
OUT=Path("qa-evidence/lyijylasi-tiffany");OUT.mkdir(parents=True,exist_ok=True)
errors=[];results=[]
with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True)
    for name,route in PAGES.items():
        for width,height in [(320,740),(390,844),(768,1024),(980,900),(1440,900)]:
            ctx=browser.new_context(viewport={"width":width,"height":height},device_scale_factor=1,reduced_motion="reduce",accept_downloads=False)
            page=ctx.new_page();runtime=[]
            page.on("pageerror",lambda e:runtime.append(str(e)))
            try:
                response=page.goto(BASE+route,wait_until="domcontentloaded",timeout=35000)
                page.wait_for_timeout(550)
                state=page.evaluate("""() => ({
                  h1:document.querySelectorAll('main h1').length,
                  active:document.querySelectorAll('nav.primary a[aria-current="page"]').length,
                  horizontal:document.documentElement.scrollWidth-innerWidth,
                  nav:document.querySelectorAll('nav.primary a').length,
                  img:document.images.length,
                  broken:[...document.images].filter(i=>i.complete&&i.naturalWidth===0&&i.hasAttribute('src')&&i.getAttribute('src')!=='').map(i=>i.currentSrc).slice(0,5)
                })""")
                row={"page":name,"width":width,"http":response.status if response else None,**state,"errors":runtime}
                if width in (390,1440):
                    page.evaluate("""() => {document.querySelectorAll('img[loading="lazy"]').forEach(i=>i.loading='eager')}""")
                    page.evaluate("""async () => {
                      await Promise.race([
                        Promise.all([...document.images].filter(i=>i.getAttribute('src')).map(i=>i.decode().catch(()=>null))),
                        new Promise(resolve=>setTimeout(resolve,15000))
                      ])
                    }""")
                    if width==1440:
                        # The source often contains original Wix photographs as narrow as 470 px.
                        # Compare the *actual* source pixels to the CSS object-fit render scale.
                        row["photo_scale_risks"]=page.evaluate("""() => [...document.querySelectorAll('main img')].filter(i=>i.naturalWidth>0&&i.naturalHeight>0).flatMap(i=>{
                          const r=i.getBoundingClientRect();
                          const fit=getComputedStyle(i).objectFit;
                          const sx=r.width/i.naturalWidth, sy=r.height/i.naturalHeight;
                          const scale=fit==='contain'?Math.min(sx,sy):Math.max(sx,sy);
                          return (scale>1.04 && r.width>250)?[{src:i.currentSrc||i.src, natural:[i.naturalWidth,i.naturalHeight], displayed:[Math.round(r.width),Math.round(r.height)], fitted_scale:Number(scale.toFixed(2))}]:[];
                        })""")
                        if row["photo_scale_risks"]:
                            errors.append(f"{name} {width}: source photos stretched past actual pixels: {row['photo_scale_risks'][:4]}")
                    row["images_loaded"]=page.evaluate("""() => [...document.images].filter(i=>i.getAttribute('src')&&i.naturalWidth>0).length""")
                    row["all_images"]=page.evaluate("""() => [...document.images].filter(i=>i.getAttribute('src')).length""")
                    if width==390 and row["images_loaded"]<row["all_images"]:
                        errors.append(f"{name} 390: some source photos failed to decode: {row['images_loaded']}/{row['all_images']}")
                if width in (390,1440):
                    page.screenshot(path=str(OUT/f"{name}-{width}.png"),full_page=True,animations="disabled",timeout=45000)
                if row["http"]!=200: errors.append(f"{name} {width}: HTTP {row['http']}")
                if row["h1"]!=1 or row["active"]!=1 or row["nav"]!=5:
                    errors.append(f"{name} {width}: missing heading, active link or nav")
                if row["horizontal"]>3:errors.append(f"{name} {width}: horizontal overflow {row['horizontal']}px")
                if runtime:errors.append(f"{name} {width}: JS errors {runtime}")
                if name=="works" and width==390:
                    if page.locator("figure[data-category]").count()!=23:errors.append("gallery lost source images")
                    page.get_by_role("button",name="Ovet",exact=True).click()
                    if page.locator("figure[data-category]:visible").count()!=7:errors.append("gallery filter doors broken")
                    page.get_by_role("button",name="Kaikki kuvat").click()
                    page.locator("figure[data-category] [data-enlarge]").first.click()
                    if not page.locator("dialog[open]").count():errors.append("gallery lightbox not open")
                    page.locator("dialog[open] [data-close]").click()
                if width in (390,980):
                    page.get_by_role("button",name="Avaa tai sulje valikko").click()
                    if not page.locator("nav.primary.is-open").count():errors.append(f"{name}: mobile nav did not open")
                    page.keyboard.press("Escape")
                results.append(row)
            except Exception as exc:errors.append(f"{name} {width}: browser check exception {exc}")
            finally:ctx.close()
    browser.close()
(OUT/"report.json").write_text(json.dumps({"results":results,"failures":errors,"visual_review":"PENDING","independent_review":"PENDING","cms_editing":"PENDING"},indent=2,ensure_ascii=False),encoding="utf-8")
print("BROWSER QA",len(results),"route-viewport combinations /",len(errors),"failures")
for problem in errors:print("FAIL",problem)
raise SystemExit(1 if errors else 0)

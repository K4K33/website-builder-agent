"""Browser QA for source-grounded Settimedia owner demo; no credentials used."""
from __future__ import annotations
from pathlib import Path
import json
import sys
from urllib.parse import urlsplit
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]/"docs"/"kaurivo"/"owner-previews"/"settimedia-v8"
OUT=Path(__file__).resolve().parents[1]/"output"/"settimedia-demo-smoke"
PAGES=("index.html","palvelut.html","meista.html","yhteys.html")

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    results, errors=[],[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True,args=["--no-sandbox"])
        for width,height,label in ((1440,900,"desktop"),(390,844,"mobile")):
            context=browser.new_context(viewport={"width":width,"height":height},device_scale_factor=1)
            for file in PAGES:
                page=context.new_page()
                console=[]
                page.on("pageerror",lambda error:console.append(str(error)[:200]))
                page.goto((ROOT/file).as_uri(),wait_until="domcontentloaded",timeout=25000)
                page.wait_for_timeout(2600)
                name=file.replace(".html","")+"-"+label
                page.screenshot(path=str(OUT/(name+".png")),full_page=True)
                facts=page.evaluate("""() => ({
                    title: document.title,
                    h1: document.querySelector('h1')?.textContent?.trim() || '',
                    overflow: document.documentElement.scrollWidth > innerWidth+2,
                    navCount: document.querySelectorAll('nav a').length,
                    images: [...document.querySelectorAll('main img')].map(i=>({
                       src:i.currentSrc, loaded:i.complete&&i.naturalWidth>0,
                       width:i.naturalWidth,height:i.naturalHeight}))
                })""")
                if not facts["h1"] or facts["navCount"]<4:errors.append(name+": missing content/navigation")
                if facts["overflow"]:errors.append(name+": horizontal overflow")
                if console:errors.append(name+": page errors "+str(console))
                # Every public navigation link stays a real working page.
                hrefs=page.locator('nav a[href]').evaluate_all("(els)=>els.map(e=>e.getAttribute('href'))")
                for href in hrefs:
                    if href and not urlsplit(href).scheme and not (ROOT/href).is_file():
                        errors.append(name+": broken nav link "+href)
                if label=="mobile" and file=="index.html":
                    button=page.locator(".menu-toggle")
                    button.click()
                    if button.get_attribute("aria-expanded")!="true" or not page.locator("nav").is_visible():
                        errors.append("mobile menu failed to open")
                image_info=[x["loaded"] for x in facts["images"]]
                print(name,"images",str(sum(image_info))+"/"+str(len(image_info)),
                      "overflow",facts["overflow"],"browser_errors",console,flush=True)
                results.append({"page":name,**facts,"page_errors":console})
                page.close()
            context.close()
        browser.close()
    (OUT/"report.json").write_text(json.dumps({
        "pages":results,"errors":errors,
        "source_media_images_are_external_and_rights_are_not_verified":True,
        "owner_presentation_not_client_publication":True
    },ensure_ascii=False,indent=2),encoding="utf-8")
    # Unloaded sourced images MUST be acknowledged in the report. They may be
    # blocked by the third-party site, and this is NOT evidence of image rights.
    if errors:
        print("FAIL",json.dumps(errors,ensure_ascii=False))
        return 1
    print("PASS",len(results),"real browser viewport/page checks; photographic reliability separate")
    return 0

if __name__=="__main__":
    sys.exit(main())

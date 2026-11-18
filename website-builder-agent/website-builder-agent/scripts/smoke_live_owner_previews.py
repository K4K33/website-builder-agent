"""Actual browser verification of every hosted owner-preview route, not a local file test."""
from __future__ import annotations
import json,os,re,sys,time
from pathlib import Path
from urllib.parse import urljoin
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
BASE="https://k4k33.github.io/website-builder-agent/kaurivo/owner-previews/"
OUTPUT=Path(os.getenv("KAURIVO_BROWSER_EVIDENCE_DIR","/tmp/kaurivo-owner-preview-screenshots"))


def main(slug):
    evidence=json.loads((ROOT/"data/owner_previews"/(slug+".json")).read_text(encoding="utf-8"))
    if evidence.get("stage")!="owner_preview":
        raise RuntimeError("Not a real source verified owner-preview release")
    routes=evidence["release_routes"]
    if len(routes)<2 or "index.html" not in routes:
        raise RuntimeError("Missing complete route manifest")
    url=BASE+slug+"/"
    OUTPUT.mkdir(parents=True,exist_ok=True)
    errors=[]
    with sync_playwright() as p:
        browser=p.chromium.launch(headless=True)
        for width in (390,768,1440):
            context=browser.new_context(viewport={"width":width,"height":850},
                                        reduced_motion="reduce",device_scale_factor=1)
            for route in routes:
                page=context.new_page()
                page_errors=[]
                failures=[]
                assets=[]
                page.on("pageerror",lambda e:page_errors.append(str(e)))
                page.on("requestfailed",lambda req: failures.append(str(req.url)))
                page.on("response",lambda response: assets.append((response.url,response.status)))
                target=url if route=="index.html" else url+route
                last=None
                for attempt in range(4):
                    try:
                        response=page.goto(target,wait_until="load",timeout=35000)
                        if response and response.status==200:break
                        last=f"HTTP {response.status if response else 'no response'}"
                    except Exception as exc:
                        last=str(exc)[:200]
                    if attempt<3:time.sleep(8)
                else:
                    errors.append(f"{route}@{width} unavailable: {last}")
                    page.close()
                    continue
                page.wait_for_timeout(600)
                checks=page.evaluate("""() => ({
                  title:document.title,
                  revision:document.documentElement.getAttribute('data-kaurivo-release'),
                  lang:document.documentElement.lang,
                  scroll:document.documentElement.scrollWidth,
                  h1:document.querySelectorAll('main h1').length,
                  disclaimer:document.querySelector('.demo-band')?.innerText || '',
                  favicon:document.querySelector('link[rel~=icon]')?.href || '',
                  styles:([...document.styleSheets].filter(x=>x.href).length),
                  images:[...document.images].map(i=>({ok:i.complete&&i.naturalWidth>0,src:i.src})),
                  headerBackground:getComputedStyle(document.querySelector('header.header')).backgroundColor
                })""")
                if evidence["company_name"] not in checks["title"]:
                    errors.append(f"{route}@{width} wrong browser tab title")
                if checks["revision"]!="rasanen-v2-20261118":
                    errors.append(f"{route}@{width} stale or missing revision")
                if checks["lang"]!="fi" or checks["h1"]!=1:
                    errors.append(f"{route}@{width} language/headings broken")
                if checks["scroll"]>width+2:
                    errors.append(f"{route}@{width} horizontal overflow: {checks['scroll']}")
                if "ei ole yrityksen virallinen sivu" not in checks["disclaimer"].lower():
                    errors.append(f"{route}@{width} independent-review banner missing")
                if not checks["favicon"] or "preview-favicon.svg" not in checks["favicon"]:
                    errors.append(f"{route}@{width} wrong favicon")
                if checks["styles"]<1:
                    errors.append(f"{route}@{width} styles not loaded")
                for img in checks["images"]:
                    if not img["ok"]:errors.append(f"{route}@{width} broken image "+img["src"])
                if not re.search(r"\b16,\s*19,\s*24\b",checks["headerBackground"]):
                    errors.append(f"{route}@{width} header brand CSS not rendered")
                if page_errors:errors.append(f"{route}@{width} JS errors: "+str(page_errors)[:200])
                if failures:errors.append(f"{route}@{width} asset requests failed: "+str(failures[:3]))
                for resource in ("site.css","site.js","brake-technical.svg","engine-technical.svg","preview-favicon.svg"):
                    if width==390 and route=="index.html":
                        expected=url+"assets/"+resource
                        if not any(a==expected and status==200 for a,status in assets):
                            # Not every SVG is requested by every route: request directly in browser
                            res=page.request.get(expected,timeout=20000)
                            if res.status!=200 or len(res.body())<100:
                                errors.append("Live shared asset unavailable: "+resource)
                if width==390 and route=="index.html":
                    page.locator("#menu-trigger").click()
                    if page.locator("#mobile-nav").is_hidden():
                        errors.append("Mobile navigation does not open")
                    page.keyboard.press("Escape")
                    if page.locator("#mobile-nav").is_visible():
                        errors.append("Mobile navigation does not close")
                if width in (390,1440):
                    page.screenshot(path=str(OUTPUT/(f"{slug}-{width}-{route.replace('/','-')}.png")),
                                    full_page=True)
                print("BROWSER_CHECK",slug,route,width,checks["title"],checks["revision"])
                page.close()
            context.close()
        browser.close()
    if errors:
        for err in errors:print("BLOCK",err)
        raise RuntimeError(f"Live browser owner preview failed {len(errors)} distinct checks")
    print("LIVE_OWNER_PREVIEW_PASS",url,len(routes),"routes; human owner approval still pending")
    return 0


if __name__=="__main__":
    sys.exit(main(sys.argv[1]))

"""Live (public) and local browser verification for Etikki multi-page concept.

Does not claim licensed photography, source-content completeness or independent design rating.
"""
from __future__ import annotations
import argparse
import json
from pathlib import Path
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
LIVE="https://k4k33.github.io/website-builder-agent/kaurivo/demos/verhoomo-etikki-v1/"
ROUTES=("", "palvelut/", "tyot/", "hinnasto/", "meista/", "ajankohtaista/", "yhteys/")
WIDTHS=(320,390,768,1440)

def scan(base: str):
    target=ROOT/"qa-evidence"/"etikki-v1"
    target.mkdir(parents=True,exist_ok=True)
    rows=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True)
        context=browser.new_context(reduced_motion="reduce", device_scale_factor=1,
                                    viewport={"width":1440,"height":900})
        try:
            for route in ROUTES:
                for width in WIDTHS:
                    page=context.new_page()
                    page.set_viewport_size({"width":width,"height":850 if width<800 else 900})
                    url=base+route
                    errors=[]
                    page.on("pageerror",lambda error:errors.append(str(error)))
                    resp=page.goto(url,wait_until="domcontentloaded",timeout=45000)
                    assert resp and resp.status==200,("HTTP_STATUS",url,resp.status if resp else None)
                    page.wait_for_timeout(350)
                    result=page.evaluate("""() => {
                      const overflow=document.documentElement.scrollWidth > innerWidth+2;
                      const off=[...document.body.querySelectorAll('*')].filter(el=>{
                        const r=el.getBoundingClientRect();
                        return r.width>0 && (r.left < -3 || r.right > innerWidth+3) &&
                          getComputedStyle(el).position!=='absolute' &&
                          getComputedStyle(el).position!=='fixed';
                      }).slice(0,8).map(el=>({tag:el.tagName,cl:String(el.className||'').slice(0,55),
                        right:Math.round(el.getBoundingClientRect().right),
                        left:Math.round(el.getBoundingClientRect().left)}));
                      const h1=document.querySelector('main h1');
                      const header=document.querySelector('.site-header');
                      const topImgs=[...document.querySelectorAll('main img')].filter(i=>i.getBoundingClientRect().top < innerHeight && i.getBoundingClientRect().bottom > 0);
                      const localLinks=[...document.querySelectorAll('main a[href]')].filter(a=>a.href.startsWith(location.origin+location.pathname.split('/verhoomo-etikki-v1/')[0]+'/verhoomo-etikki-v1/'));
                      return { overflow, off, h1:document.querySelectorAll('main h1').length,
                        h1Text:h1?.innerText, header:!!header,
                        css:getComputedStyle(document.body).backgroundColor,
                        title:document.title,
                        preview:document.body.innerText.includes('KONSEPTIDEMO'),
                        topImgs:topImgs.length,
                        totalImgs:document.querySelectorAll('main img').length,
                        localLinks:localLinks.length,
                        emptyAnchors:[...document.querySelectorAll('a[href]')].filter(a=>a.getAttribute('href')=='#').length};
                    }""")
                    assert not result["overflow"],("HORIZONTAL_OVERFLOW",route,width,result["off"])
                    assert result["h1"]==1,("WRONG_H1",route,width,result)
                    assert result["header"] and result["preview"],("IDENTITY_OR_PREVIEW",route,width,result)
                    assert result["emptyAnchors"]==0,("PLACEHOLDER_LINKS",route,width,result)
                    assert result["css"]=="rgb(244, 240, 233)",("SITE_CSS_MISSING",route,width,result)
                    assert not errors,("JAVASCRIPT_ERRORS",route,width,errors)
                    if width in (320,390):
                        btn=page.locator('[data-menu-toggle]')
                        assert btn.is_visible(),("MOBILE_BUTTON_NOT_VISIBLE",route,width)
                        btn.click()
                        assert btn.get_attribute('aria-expanded')=="true",("MOBILE_MENU_NOT_OPEN",route,width)
                        assert page.locator('[data-menu]').is_visible(),("MOBILE_NAV_HIDDEN",route,width)
                        page.keyboard.press("Escape")
                        assert btn.get_attribute('aria-expanded')=="false",("MOBILE_MENU_ESCAPE_FAILED",route,width)
                    if not route and width in (390,1440):
                        img=page.locator(".hero-photo img")
                        img.scroll_into_view_if_needed()
                        page.wait_for_function("() => {let i=document.querySelector('.hero-photo img');return i&&i.complete&&i.naturalWidth>0}",timeout=15000)
                    if route=="tyot/" and width in (390,1440):
                        img=page.locator(".craft-grid figure img").first
                        img.scroll_into_view_if_needed()
                        page.wait_for_function("() => {let i=document.querySelector('.craft-grid img');return i&&i.complete&&i.naturalWidth>0}",timeout=15000)
                        assert page.locator('.craft-grid img').count()>=8,("GALLERY_TOO_SMALL",width)
                    if not route and width in (390,1440):
                        logos=page.locator('.partner-logo img')
                        assert logos.count()==11,("MISSING_SOURCE_PARTNERS",width)
                        page.locator('.partner-zone').scroll_into_view_if_needed()
                        page.wait_for_timeout(1800)
                        status=logos.evaluate_all("(imgs) => imgs.map(i => ({alt:i.alt,ok:i.complete&&i.naturalWidth>0,url:i.currentSrc||i.src}))")
                        failed=[item for item in status if not item["ok"]]
                        assert not failed,("UNLOADED_SOURCE_LOGOS",width,failed)
                    if route=="tyot/" and width in (390,1440):
                        imgs=page.locator('.craft-grid img')
                        imgs.evaluate_all("(items) => items.forEach(img => img.loading='eager')")
                        page.wait_for_timeout(1600)
                        state=imgs.evaluate_all("(items) => items.map(i=>({alt:i.alt,ok:i.complete&&i.naturalWidth>0}))")
                        assert all(i["ok"] for i in state),("MISSING_AUTHENTIC_GALLERY_IMAGES",width,state)
                    if (route in ("", "tyot/", "palvelut/", "hinnasto/", "meista/", "yhteys/")) and width in (390,1440):
                        page.screenshot(path=str(target/((route.strip('/') or 'etusivu')+'-'+str(width)+'.png')),
                            full_page=True, animations="disabled",timeout=35000)
                    row={"route":route or "/", "width":width, "h1":result["h1Text"],
                         "imgs":result["totalImgs"],"overflow":False,"menu":"pass" if width<400 else "n/a"}
                    rows.append(row)
                    print("PASS "+json.dumps(row,ensure_ascii=False),flush=True)
                    page.close()
        finally:
            context.close()
            browser.close()
    (target/"results.json").write_text(json.dumps(rows,ensure_ascii=False,indent=2),encoding="utf-8")
    print(f"ETIKKI_BROWSER_PASS {len(rows)}/28 across 7 routes x 4 viewports",flush=True)
    # Evidence for a human side-by-side identity review, not an automated score.
    try:
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True)
            try:
                for width,height in ((390,844),(1440,900)):
                    page=browser.new_page(viewport={"width":width,"height":height},reduced_motion="reduce")
                    try:
                        response=page.goto("https://etikki.fi/",wait_until="domcontentloaded",timeout=35000)
                        page.wait_for_timeout(1900)
                        page.screenshot(path=str(target/f"original-etikki-{width}-fold.png"),
                                        full_page=False,animations="disabled",timeout=30000)
                        print("SOURCE_FOLD_CAPTURED",width,response.status if response else None,flush=True)
                    except Exception as error:
                        print("SOURCE_FOLD_REVIEW_REQUIRED",width,str(error)[:260],flush=True)
                    finally:
                        page.close()
            finally:
                browser.close()
    except Exception as error:
        print("SOURCE_SCREENSHOT_REVIEW_REQUIRED",str(error)[:260],flush=True)

if __name__=="__main__":
    ap=argparse.ArgumentParser()
    ap.add_argument("--live",action="store_true")
    args=ap.parse_args()
    if not args.live:
        ap.error("pass --live")
    scan(LIVE)

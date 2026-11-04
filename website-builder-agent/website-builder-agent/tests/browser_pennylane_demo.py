"""Real Chromium QA for the Penny Lane independent source-faithful concept.

Includes all public routes, original logo/image load, no overflow and mobile nav.
Does not assert image reuse rights or an independent aesthetic score.
"""
from __future__ import annotations
import http.server
import json
import socketserver
import subprocess
import sys
import time
from pathlib import Path

from playwright.sync_api import sync_playwright
ROOT=Path(__file__).resolve().parents[1]
SERVE=ROOT/"docs"/"kaurivo"/"demos"
SLUG="penny-lane-vintage-v1"
OUT=ROOT/"qa-evidence"/"pennylane"/"new"
PORT=8765
ROUTES=("", "valikoima/", "myyntitili/", "vuokraus/", "myymala/")
WIDTHS=(320,390,768,1440)
SOURCE_LOGO="https://pennylane.fi/wp-content/uploads/2016/08/cropped-penny-lane-logo-with-shadow.png"

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    server=subprocess.Popen([sys.executable,"-m","http.server",str(PORT),"--bind","127.0.0.1"],
                            cwd=SERVE,stdout=subprocess.DEVNULL,stderr=subprocess.STDOUT)
    failures=[]
    report=[]
    try:
        time.sleep(1.3)
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True)
            try:
                for route in ROUTES:
                    for width in WIDTHS:
                        context=browser.new_context(viewport={"width":width,"height":850 if width<900 else 900},
                                                    reduced_motion="reduce")
                        page=context.new_page()
                        errors=[]
                        page.on("pageerror",lambda e:errors.append(str(e)))
                        url=f"http://127.0.0.1:{PORT}/{SLUG}/{route}"
                        response=page.goto(url,wait_until="domcontentloaded",timeout=30000)
                        assert response and response.status==200,(route,width,response.status if response else None)
                        page.wait_for_timeout(400)
                        data=page.evaluate("""() => ({
                          h1:[...document.querySelectorAll('main h1')].map(x=>x.innerText),
                          logo:[...document.querySelectorAll('header img')].map(x=>({src:x.src,ok:x.complete&&x.naturalWidth>0})),
                          mainImages:[...document.querySelectorAll('main img')].map(x=>({src:x.src,alt:x.alt})),
                          overflow:document.documentElement.scrollWidth>window.innerWidth+2,
                          scroll:document.documentElement.scrollWidth,
                          links:[...document.querySelectorAll('a[href]')].filter(x=>x.getAttribute('href')==='#').length,
                          demo:document.querySelector('.demo-flag')?.innerText||'',
                          font:getComputedStyle(document.querySelector('main h1')).fontFamily,
                          bg:getComputedStyle(document.body).backgroundColor
                        })""")
                        assert len(data["h1"])==1,("H1_COUNT",route,width,data["h1"])
                        assert not data["overflow"],("HORIZONTAL_OVERFLOW",route,width,data["scroll"])
                        assert data["links"]==0,("DEAD_LINKS",route,width)
                        assert data["logo"] and data["logo"][0]["src"]==SOURCE_LOGO,("BRAND_LOGO_CHANGED",route,width,data["logo"])
                        assert data["logo"][0]["ok"],("SOURCE_LOGO_NOT_LOADED",route,width)
                        assert data["demo"] and "konsepti" in data["demo"].lower(),("UNLABELLED_INDEPENDENT_DEMO",route,width)
                        assert not errors,("BROWSER_JS_ERRORS",route,width,errors)
                        if width in (320,390):
                            btn=page.locator('[data-menu-btn]')
                            assert btn.is_visible(),("MOBILE_MENU_BUTTON",route,width)
                            btn.click()
                            assert btn.get_attribute("aria-expanded")=="true",("MOBILE_MENU_OPEN",route,width)
                            assert page.locator('[data-mobile-nav]').is_visible(),("MOBILE_NAV_HIDDEN",route,width)
                            page.keyboard.press("Escape")
                            assert btn.get_attribute("aria-expanded")=="false",("MOBILE_ESCAPE",route,width)
                        if width in (390,1440):
                            # Scroll to all original photos and await their actual loads.
                            page.locator("main img").evaluate_all("(imgs)=>imgs.forEach(i=>{i.loading='eager';i.decoding='sync'})")
                            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                            page.wait_for_timeout(2100)
                            state=page.locator("main img").evaluate_all(
                                "(imgs)=>imgs.map(i=>({src:i.currentSrc||i.src,ok:i.complete&&i.naturalWidth>0,width:i.naturalWidth}))")
                            assert all(i["ok"] for i in state),("BROKEN_SOURCE_PHOTOS",route,width,state)
                            page.evaluate("window.scrollTo(0,0)")
                            page.wait_for_timeout(250)
                            page.screenshot(path=str(OUT/((route.strip("/") or "etusivu")+f"-{width}.png")),
                                            full_page=True,animations="disabled",timeout=45000)
                        report.append({"route":route or "/","width":width,"images":len(data["mainImages"]),"result":"PASS"})
                        print("PASS",route or "/",width,"image_count",len(data["mainImages"]),flush=True)
                        page.close();context.close()
            finally: browser.close()
    finally:
        server.terminate()
        try:server.wait(timeout=3)
        except subprocess.TimeoutExpired:server.kill()
    (OUT/"results.json").write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding="utf-8")
    print(f"PENNY_LANE_CHROMIUM_PASS {len(report)}/{len(ROUTES)*len(WIDTHS)}",flush=True)
if __name__=="__main__":main()

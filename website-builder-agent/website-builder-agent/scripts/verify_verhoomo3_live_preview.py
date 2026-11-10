"""Fail-closed real browser audit of independent Verhoomo 3 Ässää preview.

Records tested public HTML, CSS, JS, key original image assets, six pages at
390/768/1440, accessible controls, content and A/B/C concept first-folds.
No automated client release; no autonomous rights or aesthetic certification.
"""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin
import hashlib
import json
import os
import sys
from playwright.sync_api import sync_playwright, Error as PlaywrightError

BASE=os.environ.get("KAURIVO_PREVIEW_URL", "https://kaurivo-verhoomo-3assaa-2026.onrender.com").rstrip("/")
RELEASE="verhoomo3-20261110-a1"
ROUTES=[
 ("/index.html","rgb(255, 250, 243)",["lempituolille", "verhoomo 3 ässää", "2021"]),
 ("/palvelut/index.html","rgb(234, 216, 199)",["huonekalujen", "ajoneuvojen", "veneiden", "lauritzon", "annala", "nevotex", "orient occident", "svensson", "leathered"]),
 ("/tyonaytteet/index.html","rgb(245, 235, 222)",["ennen", "jälkeen", "huonekalujen verhoilu", "ajoneuvoverhoilu"]),
 ("/hinnasto/index.html","rgb(51, 44, 44)",["60 €", "66 €", "50 €", "45 €", "200 €", "80 €", "300 €", "180 €"]),
 ("/tekijat/index.html","rgb(77, 50, 53)",["silvana", "sini", "suski", "2023", "rosebud", "grasslake"]),
 ("/yhteys/index.html","rgb(235, 213, 194)",["045 357 1510", "verhoomo3assaa@gmail.com", "aropelto 87", "01840 klaukkala", "verhoomo rosebud", "verhoilupaja grasslake"]),
]
WIDTHS=[390,768,1440]
OUT=Path("output/verhoomo3-live-smoke")
OUT.mkdir(parents=True,exist_ok=True)
report={"public_base":BASE,"release_marker":RELEASE,
 "tested_at":datetime.now(timezone.utc).isoformat(),
 "views":[],"concepts":[],"errors":[]}
with sync_playwright() as pw:
    browser=pw.chromium.launch(headless=True)
    for width in WIDTHS:
        context=browser.new_context(
            viewport={"width":width,"height":900},
            device_scale_factor=1,
            reduced_motion="reduce",
            locale="fi-FI",
        )
        page=context.new_page()
        errors=[]
        broken=[]
        def on_error(err):
            errors.append("page error: "+str(err)[:220])
        def on_console(msg):
            if msg.type=="error" and "favicon.ico" not in msg.text:
                errors.append("console: "+msg.text[:220])
        def on_response(resp):
            if resp.status>=400 and resp.request.resource_type in ("image","script","stylesheet","font"):
                broken.append(str(resp.status)+" "+resp.url[:210])
        page.on("pageerror",on_error)
        page.on("console",on_console)
        page.on("response",on_response)
        for route, expected_bg, terms in ROUTES:
            errors.clear()
            broken.clear()
            observation={"route":route,"width":width,"status":"pending"}
            try:
                response=page.goto(BASE+route,wait_until="domcontentloaded",timeout=45000)
                assert response and response.status==200,f"Unexpected HTTP {response.status if response else None}"
                page.evaluate("document.querySelectorAll('img[loading=lazy]').forEach(i=>i.loading='eager')")
                page.wait_for_load_state("networkidle",timeout=45000)
                page.wait_for_timeout(170)
                details=page.evaluate("""() => {
                    const h=document.querySelector("main h1");
                    const lead=document.querySelector(".hero,.subhero,.work-heading,.price-hero,.people-hero,.contact-hero");
                    const logo=document.querySelector(".site-header .brand strong");
                    return {
                        release: document.documentElement.getAttribute("data-kaurivo-release"),
                        cssLoaded: [...document.styleSheets].some(s=>s.href&&s.href.endsWith("/styles.css")),
                        bg: lead?getComputedStyle(lead).backgroundColor:"",
                        title: h?h.innerText:"",
                        titleSize: h?parseFloat(getComputedStyle(h).fontSize):0,
                        brandName:logo?logo.innerText:"",
                        horizontalOverflow:document.documentElement.scrollWidth>innerWidth+2,
                        brokenImages:[...document.images].filter(i=>i.complete&&!i.naturalWidth).map(i=>i.src),
                        imagesTotal:document.images.length,
                        navLinks:document.querySelectorAll("#site-nav a").length,
                        bodyText:document.body.innerText.toLocaleLowerCase("fi-FI"),
                        hasNoIndex: document.querySelector('meta[name="robots"]')?.content.includes("noindex")||false,
                        appPresent:[...document.scripts].some(s=>s.src.endsWith("/app.js")),
                    };
                }""")
                observation["http_status"]=response.status
                observation["url"]=page.url
                observation["marker"]=details["release"]
                observation["computed_background"]=details["bg"]
                observation["image_count"]=details["imagesTotal"]
                observation["broken_images"]=details["brokenImages"][:8]
                assert details["release"]==RELEASE,"Stale or missing release marker"
                assert details["cssLoaded"],"External stylesheet missing; site may be unstyled"
                assert details["appPresent"],"Interactivity script missing"
                assert details["bg"]==expected_bg, f"Unexpected computed hero bg {details['bg']} != {expected_bg}"
                assert details["title"] and details["titleSize"]>=48,"Hero title missing or unstyled"
                assert details["brandName"]=="3 Ässää","Brand name missing"
                assert details["hasNoIndex"],"Public unsolicited demo must be noindex"
                assert not details["horizontalOverflow"],"Horizontal overflow"
                assert details["navLinks"]>=7,"Navigation links missing"
                assert not details["brokenImages"],"Broken image(s): "+repr(details["brokenImages"][:4])
                assert not broken, "Failed image/CSS/JS resources: "+repr(broken[:5])
                for term in terms:
                    assert term in details["bodyText"],"Missing source-backed information: "+term
                # Confirm real source image rather than repeated placeholder data URIs.
                if route in ("/index.html","/palvelut/index.html","/tyonaytteet/index.html","/tekijat/index.html"):
                    assert page.locator('img[src^="https://verhoomo3assaa.com/wp-content/uploads/"]').count()>=1,"Source photos missing"
                if width<=768:
                    menu=page.locator("#menu-toggle")
                    menu.click(timeout=6000)
                    assert menu.get_attribute("aria-expanded")=="true","Mobile menu not opened"
                    assert page.locator("#site-nav").is_visible(),"Mobile navigation hidden"
                    page.keyboard.press("Escape")
                    assert menu.get_attribute("aria-expanded")=="false","Escape did not close mobile menu"
                if route in ("/index.html","/tyonaytteet/index.html"):
                    comparisons=page.locator(".comparison")
                    assert comparisons.count()==(1 if route=="/index.html" else 4),"Incorrect before/after pair count"
                    for k in range(comparisons.count()):
                        control=comparisons.nth(k).locator('input[type=range]')
                        control.focus()
                        control.press("ArrowRight")
                        assert control.input_value()=="51","Slider keyboard movement failed"
                        assert comparisons.nth(k).evaluate(
                            "(e)=>e.style.getPropertyValue('--split')"
                        )=="51%","Before/after reveal not moving"
                if route=="/tyonaytteet/index.html":
                    assert page.locator(".gallery-item").count()==31,"Source work image gallery incomplete"
                    page.locator('button[data-filter="ajoneuvot"]').click()
                    assert page.locator(".gallery-item:not([hidden])").count()==10,"Vehicle filter broken"
                    page.locator('button[data-filter="kalusteet"]').click()
                    assert page.locator(".gallery-item:not([hidden])").count()==21,"Furniture filter broken"
                    page.locator('button[data-filter="kaikki"]').click()
                    assert page.locator(".gallery-item:not([hidden])").count()==31,"Reset filter broken"
                if route=="/yhteys/index.html":
                    assert page.locator('a[href="tel:+358453571510"]').count()>=1,"Phone missing"
                    assert page.locator('a[href="mailto:verhoomo3assaa@gmail.com"]').count()>=1,"Email missing"
                    assert page.locator('a[href="https://wa.me/358453571510"]').count()>=1,"WhatsApp missing"
                    assert page.locator('a[href="https://www.instagram.com/verhoomo_3assaa/"]').count()>=1,"Instagram missing"
                    assert page.locator('a[href="https://www.facebook.com/verhoomo3assaa"]').count()>=1,"Facebook missing"
                    assert page.locator("form").count()==0,"Unknown form backend cannot be released"
                assert not errors,"Browser errors: "+repr(errors[:4])
                shot=OUT/f"live-{width}-{route.strip('/').replace('/','-')}.png"
                page.screenshot(path=str(shot),full_page=True,animations="disabled",timeout=35000)
                observation["screenshot_sha256"]=hashlib.sha256(shot.read_bytes()).hexdigest()
                observation["status"]="PASS"
            except Exception as exc:
                observation["status"]="FAIL"
                observation["error"]=str(exc)[:450]
                report["errors"].append(f"{route} @{width}: {exc}")
            report["views"].append(observation)
        context.close()
    # Three source-grounded materially different first-fold concepts: A (full
    # design), B (object/product), C (dark editorial photo collage).
    hashes=set()
    for width in (390,1440):
        cctx=browser.new_context(viewport={"width":width,"height":900},reduced_motion="reduce")
        cp=cctx.new_page()
        for concept,route in (("A","/index.html"),("B","/concepts/b/index.html"),("C","/concepts/c/index.html")):
            item={"concept":concept,"width":width,"url":BASE+route}
            try:
                resp=cp.goto(BASE+route,wait_until="networkidle",timeout=45000)
                assert resp and resp.status==200,"Concept HTTP not 200"
                assert cp.locator("h1").first.is_visible(),"Concept h1 hidden"
                assert cp.evaluate("document.documentElement.scrollWidth<=innerWidth+2"),"Concept horizontal overflow"
                bad_images=cp.evaluate("[...document.images].filter(i=>i.complete&&!i.naturalWidth).map(i=>i.src)")
                assert not bad_images,"Concept asset broken: "+repr(bad_images[:3])
                path=OUT/f"concept-{concept}-{width}.png"
                cp.screenshot(path=str(path),animations="disabled",full_page=True,timeout=35000)
                digest=hashlib.sha256(path.read_bytes()).hexdigest()
                assert digest not in hashes,"Reused identical concept screenshot"
                hashes.add(digest)
                item["sha256"]=digest
                item["status"]="PASS"
            except Exception as exc:
                item["status"]="FAIL"
                item["error"]=str(exc)[:450]
                report["errors"].append(f"Concept {concept} @{width}: {exc}")
            report["concepts"].append(item)
        cctx.close()
    # Check actual stylesheet and JS response including MIME.
    req=pw.request.new_context()
    for name,kind in (("styles.css","text/css"),("app.js","javascript")):
        try:
            res=req.get(BASE+"/"+name,timeout=25000)
            typ=res.headers.get("content-type","")
            report[name]={"status":res.status,"mime":typ,"bytes":len(res.body())}
            if res.status!=200 or kind not in typ or len(res.body())<200:
                report["errors"].append(f"Invalid {name} status/mime/body")
        except Exception as exc:
            report["errors"].append(f"Cannot retrieve {name}: {exc}")
    req.dispose()
    browser.close()
(OUT/"report.json").write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
print(json.dumps({
 "public_base":BASE,
 "views_tested":len(report["views"]),
 "views_passed":sum(x["status"]=="PASS" for x in report["views"]),
 "concepts_tested":len(report["concepts"]),
 "concepts_passed":sum(x["status"]=="PASS" for x in report["concepts"]),
 "styles":report.get("styles.css"),"javascript":report.get("app.js"),
 "failures":report["errors"]
},ensure_ascii=False))
sys.exit(1 if report["errors"] else 0)

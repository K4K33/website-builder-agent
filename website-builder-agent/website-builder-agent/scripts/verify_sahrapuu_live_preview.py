"""Real Chromium smoke of Sahrapuu preview. NO claims of independent visual signoff.

Run against publicly deployed exact URL. Record actual CSS MIME/status, rendered
computed styles, brand/menu, every route in three widths, JS/console/network.
"""
from __future__ import annotations
import hashlib
import json
import os
from pathlib import Path
import sys
from datetime import datetime, timezone

from playwright.sync_api import sync_playwright

BASE = os.environ.get("KAURIVO_PREVIEW_URL", "https://kaurivo-sahrapuu-concept-2026.onrender.com/release-r3").rstrip("/")
EXPECTED = "sahrapuu-20261109-release-r3"
ROUTES = ["/index.html", "/palvelut/index.html", "/tarina/index.html", "/yhteys/index.html"]
WIDTHS = [390, 768, 1440]
OUT = Path("output/sahrapuu-live-smoke")
OUT.mkdir(parents=True, exist_ok=True)
report = {"url": BASE, "tested_at": datetime.now(timezone.utc).isoformat(), "views": [], "errors": []}
with sync_playwright() as playwright:
    browser = playwright.chromium.launch(headless=True)
    for width in WIDTHS:
        ctx = browser.new_context(viewport={"width": width, "height": 900}, device_scale_factor=1, reduced_motion="reduce")
        page = ctx.new_page()
        for route in ROUTES:
            errors = []
            bad = []
            def onerror(err):
                errors.append("pageerror: " + str(err)[:150])
            def onconsole(msg):
                if msg.type == "error":
                    errors.append("console: " + msg.text[:150])
            def onresponse(resp):
                if resp.status >= 400 and resp.request.resource_type in ("stylesheet", "script", "image", "font"):
                    bad.append(str(resp.status) + " " + resp.url[:150])
            page.on("pageerror", onerror)
            page.on("console", onconsole)
            page.on("response", onresponse)
            item = {"route": route, "width": width}
            try:
                response = page.goto(BASE + route, wait_until="networkidle", timeout=45000)
                page.wait_for_timeout(200)
                result = page.evaluate("""() => {
                    const h1 = document.querySelector("main h1");
                    const logo = document.querySelector(".logo .wordmark");
                    const nav = document.getElementById("site-nav");
                    const hero = document.querySelector(".hero,.sub-hero,.contact-hero");
                    return {
                        marker: document.documentElement.getAttribute("data-kaurivo-release"),
                        cssHref: [...document.styleSheets].some(s => s.href && s.href.endsWith("/styles.css")),
                        h1: h1?.innerText || "",
                        h1size: h1 ? parseFloat(getComputedStyle(h1).fontSize) : 0,
                        logoText: logo?.innerText || "",
                        logoSize: logo ? parseFloat(getComputedStyle(logo).fontSize) : 0,
                        heroBg: hero ? getComputedStyle(hero).backgroundColor : "",
                        overflow: document.documentElement.scrollWidth > innerWidth + 2,
                        imagesBroken: [...document.images].filter(i => i.complete && !i.naturalWidth).length,
                        navLinks: nav ? nav.querySelectorAll("a").length : 0
                    };
                }""")
                item["observed"] = {"status": response.status if response else None,
                    "final_url": response.url if response else None,
                    "marker": result["marker"], "css_present": result["cssHref"],
                    "hero_bg": result["heroBg"], "overflow": result["overflow"]}
                if width <= 768:
                    toggle = page.locator("#menu-toggle")
                    toggle.click(timeout=5000)
                    result["menuOpened"] = (toggle.get_attribute("aria-expanded") == "true"
                                            and page.locator("#site-nav").is_visible())
                    toggle.click(timeout=5000)
                    result["menuClosed"] = (toggle.get_attribute("aria-expanded") == "false")
                else:
                    result["menuOpened"] = result["menuClosed"] = True
                shot = OUT / f"live-{width}-{route.strip('/').replace('/','_') or 'home'}.png"
                page.screenshot(path=str(shot), full_page=True, animations="disabled", timeout=30000)
                image_digest = hashlib.sha256(shot.read_bytes()).hexdigest()
                expected_bg = {
                    "/index.html": "rgb(28, 37, 31)",
                    "/palvelut/index.html": "rgb(38, 51, 41)",
                    "/tarina/index.html": "rgb(232, 229, 217)",
                    "/yhteys/index.html": "rgb(37, 49, 39)",
                }[route]
                assert response and response.status == 200, "Page not HTTP 200"
                assert result["marker"] == EXPECTED, "Stale or missing release marker"
                assert result["cssHref"], "External CSS did not load (regression: unstyled site)"
                assert result["heroBg"] == expected_bg, "Incorrect computed branded hero background"
                assert result["h1"] and result["h1size"] >= 48, "Missing unstyled/small heading"
                assert result["logoText"] == "Sahrapuu" and 30 <= result["logoSize"] <= 100, "Broken brand text sizing"
                assert result["navLinks"] >= 5, "Missing navigation"
                assert not result["overflow"], "Horizontal page overflow"
                assert result["imagesBroken"] == 0, "Broken image"
                assert result["menuOpened"] and result["menuClosed"], "Mobile menu broken"
                assert not errors and not bad, "JS errors or broken resources " + repr(errors + bad)
                item.update({"passed": True, "style": result, "screenshot_sha256": image_digest})
            except Exception as exc:
                item.update({"passed": False, "error": str(exc)[:350]})
                if width == 390:
                    try:
                        probe = page.request.get(BASE + route + "?release=" + EXPECTED,
                                                 timeout=10000)
                        snippet = probe.text()[:40000]
                        import re
                        marker = re.search(r'data-kaurivo-release="([^"]+)"', snippet)
                        item["cache_bust_probe"] = {"status":probe.status,
                            "marker":marker.group(1) if marker else None,
                            "bytes":len(snippet),
                            "x_cache":probe.headers.get("x-cache"),
                            "etag":probe.headers.get("etag")}
                    except Exception as diagnostic:
                        item["cache_bust_probe"] = {"error":str(diagnostic)[:130]}
                report["errors"].append(f"{route} @ {width}: {exc}")
            report["views"].append(item)
            page.remove_listener("pageerror", onerror)
            page.remove_listener("console", onconsole)
            page.remove_listener("response", onresponse)
        ctx.close()

    # A/B/C were coded as distinct first-fold concepts and captured in Chromium.
    # Real screenshots are NOT independent quality reviews or source fidelity proof.
    report["concept_captures"] = []
    hashes = set()
    for cw in (390,1440):
        concept_context=browser.new_context(viewport={"width":cw,"height":900},reduced_motion="reduce")
        concept_page=concept_context.new_page()
        for ident,path in (("A","/index.html"),("B","/_concepts/b/index.html"),("C","/_concepts/c/index.html")):
            try:
                response=concept_page.goto(BASE+path,wait_until="networkidle",timeout=45000)
                assert response and response.status == 200, "Concept source not HTTP 200"
                assert concept_page.locator("h1").first.is_visible(), "Concept heading not visible"
                assert concept_page.evaluate("document.documentElement.scrollWidth <= innerWidth+2"), "Concept horizontal overflow"
                path_img=OUT/f"concept-{ident}-{cw}.png"
                concept_page.screenshot(path=str(path_img),full_page=True,animations="disabled",timeout=30000)
                sha=hashlib.sha256(path_img.read_bytes()).hexdigest()
                assert sha not in hashes, "Same screenshot reused as different concept"
                hashes.add(sha)
                report["concept_captures"].append({"concept":ident,"viewport":cw,"sha256":sha,"passed":True})
            except Exception as error:
                report["concept_captures"].append({"concept":ident,"viewport":cw,"passed":False,"error":str(error)[:180]})
                report["errors"].append(f"Concept {ident} at {cw}: {error}")
        concept_context.close()
    if len(hashes) != 6:
        report["errors"].append("Not all six distinct real A/B/C concept renders exist")

    css_response = playwright.request.new_context().get(BASE + "/styles.css", timeout=25000)
    css_type = css_response.headers.get("content-type", "")
    report["stylesheet_response"] = {"status": css_response.status, "type": css_type,
                                     "length": len(css_response.body())}
    if css_response.status != 200 or "text/css" not in css_type:
        report["errors"].append("Stylesheet status or MIME invalid")
    browser.close()
(OUT/"report.json").write_text(json.dumps(report, indent=2, ensure_ascii=False), encoding="utf-8")
print(json.dumps({"url": BASE, "checked_views": len(report["views"]), "failures": report["errors"],
                  "stylesheet": report["stylesheet_response"],
                  "concept_captures":len(report["concept_captures"]),
                  "failed_diagnostics":[{"route":v["route"],"width":v["width"],
                    "observed":v.get("observed"),
                    "cache_bust_probe":v.get("cache_bust_probe")}
                    for v in report["views"] if not v["passed"]]}, ensure_ascii=False))
sys.exit(1 if report["errors"] else 0)

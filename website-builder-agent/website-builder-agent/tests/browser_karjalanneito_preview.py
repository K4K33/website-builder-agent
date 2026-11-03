"""Run real Chromium navigation/image/gallery checks against PR-local or published Pages.

Usage: python -m tests.browser_karjalanneito_preview --local
       python -m tests.browser_karjalanneito_preview --live

This produces screenshot artifacts and hard errors for browser bugs, but does
not claim visual aesthetics, copyright clearance or independent brand rating.
"""
from __future__ import annotations

import argparse
from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
from pathlib import Path
from threading import Thread

from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeoutError

ROOT = Path(__file__).resolve().parents[1]
SLUG = "/kaurivo/demos/kukkakauppa-karjalanneito-v1/"
LIVE = "https://k4k33.github.io/website-builder-agent" + SLUG
ROUTES = ("", "galleria/", "yhteystiedot/")
WIDTHS = (320, 390, 768, 1440)


@contextmanager
def preview_base(local: bool):
    if not local:
        yield LIVE
        return
    class Quiet(SimpleHTTPRequestHandler):
        def __init__(self, *args, **kwargs):
            super().__init__(*args, directory=str(ROOT / "docs"), **kwargs)
        def log_message(self, *args):
            return

    httpd = ThreadingHTTPServer(("127.0.0.1", 0), Quiet)
    thread = Thread(target=httpd.serve_forever, daemon=True)
    thread.start()
    try:
        yield "http://127.0.0.1:" + str(httpd.server_address[1]) + SLUG
    finally:
        httpd.shutdown()
        httpd.server_close()


def wait_source_image(page, selector: str):
    """Source-hosted imagery is externally managed; retry a transient failure once.

    A permanently missing source photo remains a real hard failure, with
    diagnostics. Repeated page contexts share the browser cache below to
    avoid hitting the original site with the same images 12 times.
    """
    query = "() => { const i=document.querySelector(" + repr(selector) + "); return i && i.complete && i.naturalWidth > 0; }"
    for attempt in (1, 2):
        try:
            page.wait_for_function(query, timeout=12000)
            return
        except PlaywrightTimeoutError:
            details = page.locator(selector).evaluate(
                "(el) => ({src:el.currentSrc||el.src,complete:el.complete,naturalWidth:el.naturalWidth})"
            )
            print("SOURCE_IMAGE_RETRY " + str((selector, attempt, details)), flush=True)
            if attempt == 2:
                raise AssertionError(("SOURCE_IMAGE_UNAVAILABLE", selector, details))
            page.reload(wait_until="domcontentloaded", timeout=40000)


def inspect(base: str, mode: str):
    evidence = ROOT / "qa-evidence" / ("karjalanneito-" + mode)
    evidence.mkdir(parents=True, exist_ok=True)
    records = []
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        context = browser.new_context(reduced_motion="reduce", device_scale_factor=1)
        try:
            for route in ROUTES:
                for width in WIDTHS:
                    page = context.new_page()
                    page.set_viewport_size({"width": width, "height": 850})
                    errors = []
                    page.on("pageerror", lambda e: errors.append(str(e)))
                    url = base + route
                    response = page.goto(url, wait_until="domcontentloaded", timeout=40000)
                    assert response is not None and response.status == 200, ("HTTP", url)
                    page.wait_for_timeout(600)
                    state = page.evaluate("""() => ({
                        overflow: document.documentElement.scrollWidth > innerWidth + 2,
                        h1: document.querySelectorAll('main h1').length,
                        disclosure: document.body.innerText.includes('KAURIVON ITSENÄINEN KONSEPTIDEMO'),
                        sourceLogo: [...document.querySelectorAll('.brand__icon img')]
                            .some(el => el.src.includes('cropped-logo_final_KN')),
                        css: getComputedStyle(document.body).fontFamily.includes('Arial'),
                        images: document.querySelectorAll('main img').length
                    })""")
                    if state["overflow"]:
                        offenders = page.evaluate("""() => [...document.querySelectorAll('body *')]
                          .filter(el => {
                              const r=el.getBoundingClientRect();
                              return r.width > 0 && (r.right > innerWidth+2 || r.left < -2) &&
                                getComputedStyle(el).position !== 'absolute';
                          }).slice(0,12).map(el => ({
                              tag:el.tagName, cls:String(el.className||'').slice(0,80),
                              right:Math.round(el.getBoundingClientRect().right),
                              left:Math.round(el.getBoundingClientRect().left),
                              width:Math.round(el.getBoundingClientRect().width)
                          }))""")
                        raise AssertionError(("HORIZONTAL_OVERFLOW", route, width,
                                              state, offenders))
                    assert state["h1"] == 1, ("MAIN_H1", route, width, state)
                    assert state["disclosure"] and state["sourceLogo"] and state["css"], (
                        "BRAND_OR_CSS", route, width, state
                    )
                    assert not errors, ("JS_ERRORS", route, width, errors)

                    if route == "":
                        assert state["images"] >= 8, ("MISSING_SOURCE_FLOWER_MEDIA", width)
                        wait_source_image(page, ".hero__main")
                    if route == "galleria/":
                        assert page.locator("[data-gallery-item]").count() == 45
                        page.locator('[data-gallery-filter="haakimput"]').click()
                        visible = page.locator("[data-gallery-item]:visible").count()
                        counter = page.locator("[data-gallery-count]").inner_text()
                        if visible != 4 or counter != "4 kuvaa":
                            diagnostic = page.evaluate("""() => ({
                                counter: document.querySelector('[data-gallery-count]').innerText,
                                pressed: [...document.querySelectorAll('[data-gallery-filter]')]
                                    .filter(b => b.getAttribute('aria-pressed') === 'true')
                                    .map(b => b.dataset.galleryFilter),
                                shown: [...document.querySelectorAll('[data-gallery-item]')]
                                    .filter(f=>!f.hidden).map(f=>({
                                        category:f.dataset.category,
                                        height:Math.round(f.getBoundingClientRect().height),
                                        display:getComputedStyle(f).display
                                    })).slice(0,8),
                                hidden:document.querySelectorAll('[data-gallery-item][hidden]').length
                            })""")
                            raise AssertionError(("FILTER", route, width, visible, counter,
                                                  diagnostic, errors))
                        page.locator("[data-gallery-item]:visible button").first.click()
                        dialog = page.locator("[data-lightbox]")
                        assert dialog.get_attribute("aria-hidden") == "false", (
                            "LIGHTBOX_OPEN", route, width
                        )
                        page.keyboard.press("ArrowRight")
                        page.keyboard.press("Escape")
                        assert dialog.get_attribute("aria-hidden") == "true", (
                            "LIGHTBOX_ESCAPE", route, width
                        )
                        page.locator('[data-gallery-filter="kaikki"]').click()
                        assert page.locator("[data-gallery-count]").inner_text() == "45 kuvaa"
                        first = page.locator("[data-gallery-item] img").first
                        first.scroll_into_view_if_needed()
                        wait_source_image(page, "[data-gallery-item] img")
                    if route == "yhteystiedot/":
                        wait_source_image(page, ".contact-hero > img")
                    if width in (320, 390):
                        toggle = page.locator("[data-nav-toggle]")
                        assert toggle.is_visible()
                        toggle.click()
                        assert toggle.get_attribute("aria-expanded") == "true"
                        assert page.locator("[data-mobile-nav]").get_attribute("data-open") == "true"
                        page.keyboard.press("Escape")
                        assert toggle.get_attribute("aria-expanded") == "false"
                    if width in (390, 1440):
                        name = route.rstrip("/") or "etusivu"
                        page.screenshot(
                            path=str(evidence / (name + "-" + str(width) + ".png")),
                            full_page=route != "galleria/", animations="disabled",
                        )
                    record = {"url": url, "route": route or "/",
                              "width": width, "source_images": state["images"],
                              "h1": 1, "overflow": False, "errors": []}
                    records.append(record)
                    print("PASS " + json.dumps(record, ensure_ascii=False), flush=True)
                    page.close()
        finally:
            context.close()
            browser.close()
    (evidence / "results.json").write_text(
        json.dumps(records, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print("BROWSER_PASS", len(records), mode)


def main():
    parser = argparse.ArgumentParser()
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--local", action="store_true")
    group.add_argument("--live", action="store_true")
    args = parser.parse_args()
    with preview_base(local=args.local) as base:
        inspect(base, "local" if args.local else "live")


if __name__ == "__main__":
    main()

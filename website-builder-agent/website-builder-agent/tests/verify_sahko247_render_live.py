"""Verify exact published Sähkö247 demo routes across desktop and mobile.

The GitHub Pages/Render deployment state alone is not proof of a live site.
This checks real HTTP responses, content, responsive navigation, anchors,
browser errors, CSS, and no horizontal overflow before linking it publicly.
"""
from __future__ import annotations
from urllib.parse import urljoin, urlsplit
import os
import time
import requests
from playwright.sync_api import sync_playwright

BASE = "https://kaurivo-auto-demos-2026.onrender.com/sahko247-premium-20261113/"
PAGES = {
    "index.html": ("Sähköä,", "20 vuoden"),
    "palvelut.html": ("Sähköasennukset", "Helvar Designer"),
    "hinnasto.html": ("60,24 €/h", "120,48 €/hälytys"),
    "yhteystiedot.html": ("045 173 8377", 'id="contact-form"'),
    "ukk.html": ("Usein kysytyt", "Paljonko sähkötyö maksaa?"),
    "tietosuoja.html": ("Tietosuoja", "Kaurivon suunnitteludemo"),
}
ASSETS = {"assets/theme.css": "--bg:#10171a", "assets/site.js": "mailto:asiakaspalvelu@sahko247.fi"}
session = requests.Session()
session.headers["User-Agent"] = "Kaurivo owner-only preview QA / HTTP verification"


def fetch(path: str, marker: str, tries: int = 9) -> str:
    url = urljoin(BASE, path)
    response = None
    for i in range(tries):
        try:
            response = session.get(url, timeout=22, allow_redirects=True)
            if (
                response.status_code == 200
                and marker in response.text
                and urlsplit(response.url).hostname == "kaurivo-auto-demos-2026.onrender.com"
            ):
                return response.text
            print(f"{path} public HTTP={response.status_code}, marker={marker in response.text}, try {i+1}", flush=True)
        except requests.RequestException as exc:
            print(f"{path} temporary {type(exc).__name__}, try {i+1}", flush=True)
        time.sleep(5)
    raise AssertionError(f"Public release missing, stale or broken: {url}")


def main():
    source={}
    for path, markers in PAGES.items():
        body=fetch(path, markers[0])
        for marker in markers:
            assert marker in body, f"{path} missing grounded source fact: {marker}"
        assert 'name="robots" content="noindex' in body, f"{path} published to search"
        assert '<main id="sisalto">' in body and '</main>' in body, path
        assert 'Kaurivon suunnitteludemo' in body, path
        source[path]=body
    for path, marker in ASSETS.items():
        source[path]=fetch(path, marker)

    assert len(PAGES)>=6
    for page, content in source.items():
        if not page.endswith(".html"):
            continue
        assert 'href="./assets/theme.css' in content, page
        assert 'src="./assets/site.js' in content, page

    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        try:
            for width in (390, 768, 1440):
                context = browser.new_context(
                    viewport={"width": width, "height": 900},
                    reduced_motion="reduce",
                    device_scale_factor=1,
                )
                try:
                    page = context.new_page()
                    errors = []
                    page.on("pageerror", lambda e: errors.append(str(e)[:250]))
                    for path in PAGES:
                        response = page.goto(urljoin(BASE,path),wait_until="domcontentloaded",timeout=35000)
                        assert response and response.status==200,(width,path,"HTTP")
                        page.wait_for_timeout(180)
                        state = page.evaluate("""() => {
                          let header=document.querySelector('.site-header');
                          let main=document.querySelector('main');
                          let title=main?.querySelector('h1');
                          let stylesheet=document.querySelector('link[rel=stylesheet]');
                          return {
                            stylesheet:!!stylesheet?.sheet,
                            h1:!!title && title.getBoundingClientRect().height>0,
                            oneTitle:main?.querySelectorAll('h1').length===1,
                            header:!!header && header.getBoundingClientRect().height>0,
                            overflow:document.documentElement.scrollWidth>innerWidth+2,
                            brokenImages:[...document.images].filter(i=>!i.complete||!i.naturalWidth).length,
                            links:[...document.querySelectorAll('a[href]')].map(x=>x.getAttribute('href')),
                            missingAnchors:[...document.querySelectorAll('a[href^="#"]')].filter(a=>!document.querySelector(a.getAttribute('href'))).length
                          };
                        }""")
                        assert state["stylesheet"] and state["h1"] and state["oneTitle"],(width,path,state)
                        assert state["header"] and not state["overflow"],(width,path,state)
                        assert state["brokenImages"]==0 and state["missingAnchors"]==0,(width,path,state)
                        assert not errors,(width,path,errors)
                        for href in state["links"]:
                            if href.startswith("./") and "#" not in href:
                                suffix=href.removeprefix("./")
                                assert suffix in PAGES or suffix in ASSETS,(path,href)
                        if width < 1180:
                            toggle=page.locator(".mobile-toggle")
                            assert toggle.is_visible(),(width,path,"menu toggle")
                            assert toggle.get_attribute("aria-expanded")=="false"
                            toggle.click()
                            assert toggle.get_attribute("aria-expanded")=="true"
                            assert page.locator(".main-nav").is_visible()
                            page.keyboard.press("Escape")
                            assert toggle.get_attribute("aria-expanded")=="false"
                        else:
                            assert page.locator(".main-nav").is_visible(),(width,path)
                        if path=="yhteystiedot.html":
                            assert page.locator("#contact-form").count()==1
                            assert page.locator("#field-message").get_attribute("required") is not None
                finally:
                    context.close()
        finally:
            browser.close()
    print(f"PASS: {len(PAGES)} authentic routes + {len(ASSETS)} assets, desktop/tablet/mobile, navigation, console, links, content and contact form")
    print(BASE+"index.html")


if __name__=="__main__":
    main()

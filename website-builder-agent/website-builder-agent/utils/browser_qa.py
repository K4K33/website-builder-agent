"""Render generated pages locally; never contact third parties or submit forms."""

import json
from pathlib import Path
from playwright.sync_api import sync_playwright


def inspect_site(path):
    source = Path(path).resolve()
    issues, screenshots = [], {}
    viewports = (("desktop", 1440, 900), ("tablet", 768, 1024),
                 ("mobile", 390, 844), ("small_mobile", 320, 740))
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            try:
                for name, width, height in viewports:
                    context = browser.new_context(viewport={"width": width, "height": height},
                                                  reduced_motion="reduce", service_workers="block")
                    # Generated code is untrusted: block all network access.
                    context.route("**/*", lambda route: route.continue_()
                                  if route.request.url.startswith(("file:", "data:")) else route.abort())
                    page = context.new_page()
                    errors = []
                    page.on("pageerror", lambda error: errors.append(str(error)))
                    try:
                        page.goto(source.as_uri(), wait_until="load", timeout=15000)
                        page.wait_for_timeout(150)
                        findings = page.evaluate("""() => {
                            const visible = el => !!(el.getClientRects().length &&
                                getComputedStyle(el).visibility !== 'hidden');
                            const controls = [...document.querySelectorAll('a,button,input,textarea,select')];
                            return {
                                overflow: document.documentElement.scrollWidth > innerWidth + 2,
                                tiny: controls.filter(visible).filter(el => {
                                    const r = el.getBoundingClientRect();
                                    return (el.matches('button,input,select') || el.getAttribute('role') === 'button') &&
                                        (r.width < 24 || r.height < 24);
                                }).length,
                                brokenImages: [...document.images].filter(el => !el.complete || !el.naturalWidth).length,
                                emptyMain: !document.querySelector('main')?.innerText.trim(),
                            };
                        }""")
                        for key, message in (("overflow", "horizontal overflow"),
                                             ("tiny", "undersized controls"),
                                             ("brokenImages", "broken images"),
                                             ("emptyMain", "empty main content")):
                            if findings[key]:
                                issues.append(f"{name}: {message}")
                        # Exercise disclosure/menu controls without invoking external CTAs.
                        menus = page.locator('button[aria-expanded][aria-controls]')
                        for i in range(menus.count()):
                            button = menus.nth(i)
                            if not button.is_visible():
                                continue
                            before = button.get_attribute("aria-expanded")
                            target = button.get_attribute("aria-controls")
                            button.focus()
                            page.keyboard.press("Enter")
                            page.wait_for_timeout(80)
                            if button.get_attribute("aria-expanded") == before:
                                issues.append(f"{name}: disclosure does not update aria-expanded")
                            opened = button.get_attribute("aria-expanded") == "true"
                            panel = page.locator('[id=' + json.dumps(target) + ']')
                            if opened and (panel.count() != 1 or not panel.is_visible()):
                                issues.append(f"{name}: disclosure target is not visible")
                            page.keyboard.press("Escape")
                        if errors:
                            issues.extend(f"{name}: JavaScript error: {e[:180]}" for e in errors[:3])
                        destination = source.parent / "qa" / f"{name}.png"
                        destination.parent.mkdir(exist_ok=True)
                        # Cap extreme generated pages to a useful review image.
                        full_height = page.evaluate("document.documentElement.scrollHeight")
                        if full_height > 16000:
                            issues.append(f"{name}: excessive page height; visual review incomplete")
                        page.screenshot(path=str(destination), full_page=True,
                                        animations="disabled", timeout=15000)
                        screenshots[name] = str(destination)
                    finally:
                        context.close()
            finally:
                browser.close()
    except Exception as error:
        issues.append(f"Browser QA unavailable or failed: {type(error).__name__}: {str(error)[:200]}")
    return {"pass": not issues and len(screenshots) == len(viewports),
            "issues": issues, "screenshots": screenshots}

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
                        # Make below-fold lazy images load before measuring or
                        # screenshotting. External requests remain blocked in
                        # offline mode; they must be packaged locally or be
                        # separately proven by exact live-preview checks.
                        page.evaluate("""async () => {
                            const images = [...document.images];
                            for (const image of images) image.loading = 'eager';
                            await Promise.all(images.map(image => image.decode().catch(() => null)));
                        }""")
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
                                brokenImages: [...document.images]
                                    .filter(el => !el.complete || !el.naturalWidth)
                                    .map(el => (el.currentSrc || el.src || '[missing src]').slice(0,180)).slice(0,8),
                                lowResolutionLogos: [...document.querySelectorAll('header img')]
                                    .filter(el => {
                                        const parent = el.closest('[class*="logo"],[class*="brand"],[class*="identity"]');
                                        return !!parent || /logo/i.test(el.alt || '');
                                    })
                                    .filter(el => el.naturalWidth > 0 && el.getBoundingClientRect().width >= 60 &&
                                        el.naturalWidth < el.getBoundingClientRect().width * 1.5)
                                    .map(el => ({
                                        sourceWidth: el.naturalWidth,
                                        displayedWidth: Math.round(el.getBoundingClientRect().width),
                                        src: (el.currentSrc || el.src).slice(0,120)
                                    })).slice(0,5),
                                emptyMain: !document.querySelector('main')?.innerText.trim(),
                            };
                        }""")
                        if findings["lowResolutionLogos"]:
                            issues.append(
                                f"{name}: pixelated primary brand logo (insufficient source pixels): "
                                + json.dumps(findings["lowResolutionLogos"], ensure_ascii=False)
                            )
                        # WCAG AA contrast on genuinely measurable solid backgrounds.
                        # Image/gradient/translucent layers are intentionally sent to
                        # visual review rather than given an invented CSS score.
                        color_review = page.evaluate("""() => {
                            const parse = value => {
                                const m = /^rgba?\\(\\s*(\\d+)[, ]+\\s*(\\d+)[, ]+\\s*(\\d+)(?:[, /]+([\\d.]+))?\\s*\\)$/.exec(value);
                                if (!m) return null;
                                if (m[4] !== undefined && Number(m[4]) < 0.999) return null;
                                return [Number(m[1]),Number(m[2]),Number(m[3])];
                            };
                            const lum = rgb => {
                                const c = rgb.map(x => x / 255).map(x =>
                                    x <= 0.04045 ? x / 12.92 : Math.pow((x + 0.055) / 1.055, 2.4));
                                return c[0]*0.2126 + c[1]*0.7152 + c[2]*0.0722;
                            };
                            const ratio = (a,b) => (Math.max(lum(a),lum(b))+0.05) /
                                                    (Math.min(lum(a),lum(b))+0.05);
                            const visible = e => !!e.getClientRects().length
                                && getComputedStyle(e).visibility !== 'hidden';
                            let checked=0, skipped=0, poor=[];
                            const nodes = [...document.querySelectorAll(
                                'h1,h2,h3,h4,p,li,a,button,label,small,span')].slice(0,650);
                            for (const el of nodes) {
                                if (!visible(el) || !el.textContent?.trim()) continue;
                                // Sample only text-owning elements, not wrapper blocks
                                // that would repeat the same color measurements.
                                if ([...el.children].some(ch => ch.textContent?.trim())) continue;
                                const style = getComputedStyle(el), foreground=parse(style.color);
                                if (!foreground) {skipped++;continue;}
                                let bg=null, uncertain=false, current=el;
                                while(current && current.nodeType===1) {
                                    const st=getComputedStyle(current);
                                    if(st.backgroundImage!=='none' || st.opacity!=='1') {
                                        uncertain=true;break;
                                    }
                                    const candidate=parse(st.backgroundColor);
                                    if(candidate) { bg=candidate;break; }
                                    if(st.backgroundColor !== 'rgba(0, 0, 0, 0)' &&
                                       st.backgroundColor !== 'transparent') { uncertain=true;break; }
                                    current=current.parentElement;
                                }
                                if (uncertain) {skipped++;continue;}
                                if (!bg) bg=[255,255,255];
                                const size=parseFloat(style.fontSize), weight=parseFloat(style.fontWeight)||400;
                                const large=size >= 24 || (size>=18.66 && weight>=700);
                                const required=large?3:4.5, value=ratio(foreground,bg);
                                checked++;
                                if (value+0.02<required && poor.length<8)
                                    poor.push({tag:el.tagName,text:el.textContent.trim().slice(0,70),
                                               ratio:Math.round(value*100)/100, required});
                            }
                            const root=getComputedStyle(document.documentElement);
                            const body=getComputedStyle(document.body);
                            const scrollBlocked=document.documentElement.scrollHeight>innerHeight+100 &&
                                (root.overflowY==='hidden'||body.overflowY==='hidden');
                            return {poor,checked,skipped,scrollBlocked};
                        }""")
                        if color_review["poor"]:
                            issues.append(f"{name}: measurable WCAG AA text contrast failures: "
                                          + json.dumps(color_review["poor"], ensure_ascii=False))
                        if color_review["scrollBlocked"]:
                            issues.append(f"{name}: native vertical scrolling blocked")
                        for key, message in (("overflow", "horizontal overflow"),
                                             ("tiny", "undersized controls"),
                                             ("brokenImages", "broken images"),
                                             ("emptyMain", "empty main content")):
                            if findings[key]:
                                detail = (
                                    ": " + json.dumps(findings[key], ensure_ascii=False)
                                    if key == "brokenImages" else ""
                                )
                                issues.append(f"{name}: {message}{detail}")
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

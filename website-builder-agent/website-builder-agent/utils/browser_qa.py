"""Render generated pages locally; never contact third parties or submit forms."""

import json
from pathlib import Path
from playwright.sync_api import sync_playwright


def inspect_site(path, *, first_view_requirement: dict | None = None):
    source = Path(path).resolve()
    issues, screenshots, visual_review_flags = [], {}, []
    first_fold_observations = {}
    viewports = (("desktop", 1440, 900), ("tablet", 768, 1024),
                 ("mobile", 390, 844), ("small_mobile", 320, 740))
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            try:
                for name, width, height in viewports:
                    context = browser.new_context(viewport={"width": width, "height": height},
                                                  is_mobile=width <= 390,
                                                  has_touch=width <= 390,
                                                  device_scale_factor=1,
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
                                // Passing image-loaded checks does NOT prove the
                                // photo has enough native pixels at display size.
                                // Only report materially enlarged source images;
                                // intentional pixel-art/product crops need a human.
                                lowResolutionContentPhotos: [...document.querySelectorAll('main img')]
                                    .filter(el => {
                                        const rect = el.getBoundingClientRect();
                                        return rect.width >= 240 && rect.height >= 180
                                          && el.naturalWidth > 0 && el.naturalHeight > 0
                                          && (el.naturalWidth < rect.width * .92
                                           || el.naturalHeight < rect.height * .92);
                                    })
                                    .map(el => ({
                                        sourceSize: [el.naturalWidth, el.naturalHeight],
                                        displayedSize: [
                                            Math.round(el.getBoundingClientRect().width),
                                            Math.round(el.getBoundingClientRect().height)
                                        ],
                                        src: (el.currentSrc || el.src).slice(0,140),
                                    })).slice(0,8),
                                // A tall almost-empty column next to substantial
                                // content is a human layout-review candidate,
                                // NOT a numeric automatic design verdict.
                                columnImbalance: innerWidth < 768 ? [] :
                                  [...document.querySelectorAll('main section,main [class*="grid"],main [class*="split"],main [class*="columns"]')]
                                    .slice(0,100).filter(el => {
                                        const display=getComputedStyle(el).display;
                                        return display==='grid'||display==='flex';
                                    }).map(el => {
                                        const children=[...el.children].filter(ch => visible(ch)
                                            && ch.getBoundingClientRect().width >= 180);
                                        if(children.length!==2) return null;
                                        const rects=children.map(ch=>ch.getBoundingClientRect());
                                        const maxH=Math.max(...rects.map(r=>r.height));
                                        if(maxH<500 || Math.min(...rects.map(r=>r.width))<180) return null;
                                        const textEnds=children.map((ch,i) => {
                                            const candidates=[...ch.querySelectorAll('h1,h2,h3,p,li,a,button,table')];
                                            const ends=candidates.filter(visible)
                                                .map(n=>n.getBoundingClientRect().bottom);
                                            return ends.length?Math.max(...ends):rects[i].top;
                                        });
                                        const blanks=rects.map((r,i)=>r.bottom-textEnds[i]);
                                        if(Math.max(...blanks)<360 || Math.abs(blanks[0]-blanks[1])<300) return null;
                                        return {
                                            element: el.tagName.toLowerCase(),
                                            className: String(el.className||'').slice(0,90),
                                            columnBlankPixels: blanks.map(x=>Math.round(x)),
                                            note:'Editorial whitespace imbalance requires screenshot inspection'
                                        };
                                    }).filter(Boolean).slice(0,6),
                                emptyMain: !document.querySelector('main')?.innerText.trim(),
                            };
                        }""")
                        # A visible source product in the first phone screen
                        # is a design observation, never a universal mandate.
                        # Text-first service sites, CSS hero backgrounds and
                        # intentional editorial layouts need human judgement.
                        first_fold = page.evaluate("""() => {
                            const main=document.querySelector('main');
                            if (!main) return {measured:false,reason:'No main landmark'};
                            const viewport={w:innerWidth,h:innerHeight};
                            const rect=main.getBoundingClientRect();
                            const candidates=[...main.querySelectorAll('img,picture,video')];
                            const media=candidates.filter(el=>{
                                const r=el.getBoundingClientRect(),s=getComputedStyle(el);
                                return r.width>0 && r.height>0 && s.visibility!=='hidden'
                                    && s.display!=='none';
                            });
                            const intersects=el=>{
                                const r=el.getBoundingClientRect();
                                return Math.max(0,Math.min(r.right,viewport.w)-Math.max(0,r.left))
                                  *Math.max(0,Math.min(r.bottom,viewport.h)-Math.max(0,r.top));
                            };
                            const above=media.filter(el=>intersects(el)>250);
                            const h1=main.querySelector('h1');
                            const hero=h1?.closest('section,article') || main;
                            const mediaAfter=media.filter(el=>el.getBoundingClientRect().top>=viewport.h);
                            const bgHero=[hero,...hero.querySelectorAll('*')].slice(0,60)
                              .some(el=>getComputedStyle(el).backgroundImage.includes('url('));
                            return {
                                measured:true,viewportWidth:viewport.w,viewportHeight:viewport.h,
                                visibleMainMedia:above.length,allMainMedia:media.length,
                                mainMediaBelowFold:mediaAfter.length,
                                firstFoldVisibleMediaArea:Math.round(above.reduce(
                                  (s,el)=>s+intersects(el),0)),
                                hasMainHeading:!!h1,
                                titleBottom:h1?Math.round(h1.getBoundingClientRect().bottom):null,
                                headerHeight:Math.round(Math.max(0,rect.top)),
                                heroHasCssBackground:!!bgHero,
                            };
                        }""")
                        first_fold_observations[name] = first_fold
                        # Pure HTML may contain a product image after 900px of
                        # oversized headings. Check REAL pixels at each width,
                        # not just whether an <img> exists somewhere in hero.
                        requirement = first_view_requirement or {}
                        if requirement.get("product_media_required") is True:
                            real_area = int(first_fold.get("firstFoldVisibleMediaArea") or 0)
                            threshold = int(width * height * 0.035)
                            if real_area < threshold:
                                issues.append(
                                    f"{name}: source-rich {requirement.get('role', 'product')} "
                                    "route lacks meaningful merchandise/work imagery "
                                    f"in the first viewport ({real_area}px² visible, "
                                    f"at least {threshold}px² required). "
                                    "Reduce oversized headings/empty hero and move "
                                    "real products into the actual initial screen."
                                )
                        if (width <= 390 and first_fold.get("measured")
                                and first_fold.get("allMainMedia", 0) > 0
                                and first_fold.get("visibleMainMedia", 0) == 0
                                and first_fold.get("mainMediaBelowFold", 0) > 0
                                ):
                            visual_review_flags.append({
                                "viewport": name,
                                "kind": "first_view_business_media_below_fold",
                                "observation": first_fold,
                                "note": "Business img/video elements begin below the first phone viewport. "
                                        "Review genuine product/work visibility; a CSS image "
                                        "or gradient alone cannot prove source photo priority. "
                                        "Do not automatically reject text-first businesses.",
                            })
                        if findings.get("columnImbalance"):
                            visual_review_flags.extend([
                                {"viewport": name, **candidate}
                                for candidate in findings["columnImbalance"]
                            ])
                        if ((first_view_requirement or {}).get("product_media_required")
                                and findings.get("lowResolutionContentPhotos")):
                            # A 225px thumbnail blown up to 500px is not an
                            # acceptable premium merchandise photo. Flag only
                            # GROSS upscaling, not subtle 1x-vs-retina issues.
                            severe = [
                                item for item in findings["lowResolutionContentPhotos"]
                                if (item["sourceSize"][0] < item["displayedSize"][0] * .50
                                    or item["sourceSize"][1] < item["displayedSize"][1] * .50)
                            ]
                            if severe:
                                issues.append(
                                    f"{name}: low-resolution original product photography "
                                    "severely enlarged in public-facing product view: "
                                    + json.dumps(severe[:4],ensure_ascii=False)
                                )
                        if findings.get("lowResolutionContentPhotos"):
                            visual_review_flags.append({
                                "viewport": name,
                                "kind": "upscaled_original_content_photography",
                                "evidence": findings["lowResolutionContentPhotos"],
                                "note": "Actual image native dimensions are smaller than "
                                        "the rendered dimensions. Check product/staff photo "
                                        "sharpness in real screenshots and seek licensed "
                                        "higher-resolution originals. This is an aesthetic "
                                        "review flag, not an automatic resolution claim.",
                            })
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
                            let checked=0, skipped=0, poor=[], ambiguous=[], tinyText=[];
                            const nodes = [...document.querySelectorAll(
                                'h1,h2,h3,h4,p,li,a,button,label,small,span')].slice(0,650);
                            for (const el of nodes) {
                                if (!visible(el) || !el.textContent?.trim()) continue;
                                // Sample only text-owning elements, not wrapper blocks
                                // that would repeat the same color measurements.
                                if ([...el.children].some(ch => ch.textContent?.trim())) continue;
                                const style = getComputedStyle(el), foreground=parse(style.color);
                                const size=parseFloat(style.fontSize);
                                // Core content should remain legible at standard mobile size.
                                if (size < 12 && el.matches('p,a,button,li,label')
                                    && tinyText.length<8) {
                                    tinyText.push({tag:el.tagName,text:el.textContent.trim().slice(0,70),
                                                   fontSize:Math.round(size*10)/10});
                                }
                                if (!foreground) {skipped++;continue;}
                                let bg=null, uncertain=false, current=el, complexLayer=false;
                                while(current && current.nodeType===1) {
                                    const st=getComputedStyle(current);
                                    if(st.backgroundImage!=='none' || st.opacity!=='1') {
                                        uncertain=true;complexLayer=true;break;
                                    }
                                    const candidate=parse(st.backgroundColor);
                                    if(candidate) { bg=candidate;break; }
                                    if(st.backgroundColor !== 'rgba(0, 0, 0, 0)' &&
                                       st.backgroundColor !== 'transparent') {
                                        uncertain=true;complexLayer=true;break;
                                    }
                                    current=current.parentElement;
                                }
                                if (uncertain) {
                                    skipped++;
                                    if(complexLayer && ambiguous.length<12)
                                        ambiguous.push({tag:el.tagName,text:el.textContent.trim().slice(0,70),
                                            reason:'image/gradient/translucent layer; requires visual proof'});
                                    continue;
                                }
                                if (!bg) bg=[255,255,255];
                                const weight=parseFloat(style.fontWeight)||400;
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
                            return {poor,checked,skipped,ambiguous,tinyText,scrollBlocked};
                        }""")
                        if color_review["poor"]:
                            issues.append(f"{name}: measurable WCAG AA text contrast failures: "
                                          + json.dumps(color_review["poor"], ensure_ascii=False))
                        if color_review["tinyText"]:
                            issues.append(f"{name}: essential copy below readable 12px floor: "
                                          + json.dumps(color_review["tinyText"], ensure_ascii=False))
                        # A contrast ratio cannot be inferred from CSS when text
                        # is layered over a photo, gradient, or translucent panel.
                        # Do not quietly count it as a pass; demand an actual
                        # screenshot check or make the text panel solid.
                        if color_review["ambiguous"]:
                            issues.append(f"{name}: text/background contrast NOT VERIFIABLE; "
                                          "use a legible opaque text panel or independently "
                                          "review the real rendered image: "
                                          + json.dumps(color_review["ambiguous"], ensure_ascii=False))
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
            "issues": issues, "screenshots": screenshots,
            "visual_review_flags": visual_review_flags,
            "first_fold_observations": first_fold_observations,
            "note": "Whitespace/layout flags need independently reviewed full-page screenshots."}

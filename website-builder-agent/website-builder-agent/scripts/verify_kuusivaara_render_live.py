"""External Chromium proof: the actual Render URL must LOOK styled, not just be HTTP 200.

Run only after Render's new deployment is live. Screenshot and computed-style
evidence are written to output/render-live-smoke. Independent aesthetic
quality and client media-rights review remain separate acceptance gates.
"""
from __future__ import annotations
import json, os, sys
from pathlib import Path
from playwright.sync_api import sync_playwright

URL = os.environ.get("KUUSIVAARA_PUBLIC_URL", "https://kaurivo-kuusivaara-demo-2026.onrender.com/").rstrip("/")
OUT = Path(__file__).resolve().parents[1] / "output/kuusivaara-render-live-smoke"

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    audit = {"target": URL, "pages": [], "errors": [], "warnings": []}
    with sync_playwright() as pw:
        browser = pw.chromium.launch(headless=True)
        for width in (390, 1440):
            ctx = browser.new_context(viewport={"width": width, "height": 850}, device_scale_factor=1)
            page = ctx.new_page()
            for route in ("", "palvelut/", "tyot/", "en/services/"):
                entry = {"route": route, "width": width}
                try:
                    response = page.goto(URL + "/" + route, wait_until="domcontentloaded", timeout=40000)
                    page.wait_for_timeout(500)
                    metrics = page.evaluate("""() => {
                      const hero=document.querySelector('section.hero, section.page-head, .gallery-firstfold');
                      const brand=document.querySelector('header .brand');
                      const image=document.querySelector('header .brand-logo');
                      const style=document.querySelector('style[data-kaurivo-critical-styles="inline-v1"]');
                      const bodyStyle=getComputedStyle(document.body);
                      const heroStyle=hero?getComputedStyle(hero):null;
                      const nav=document.querySelector('header nav');
                      return {
                        hasInlineCSS:!!style && style.textContent.length>10000,
                        hasInlineJS:!!document.querySelector('script[data-kaurivo-enhancement="inline-v1"]'),
                        hasLinkedCSS:!!document.querySelector('link[rel="stylesheet"][href]'),
                        hasLinkedJS:!!document.querySelector('script[src]'),
                        heroBrandGeometry:(() => {
                          const name=document.querySelector('.hero-brand-type strong');
                          const stage=document.querySelector('.hero-art');
                          if(!name || !stage) return {ok:false,reason:'title missing'};
                          const style=getComputedStyle(name);
                          const range=document.createRange();
                          range.selectNodeContents(name);
                          const ink=Array.from(range.getClientRects()).filter(r=>r.width>0 && r.height>0);
                          const bounds=name.getBoundingClientRect();
                          const canvas=stage.getBoundingClientRect();
                          const isSingleLine=ink.length===1;
                          const inside=ink.every(r=>r.left>=canvas.left+8 && r.right<=canvas.right-8);
                          const ok=style.whiteSpace==='nowrap' && isSingleLine && inside
                              && name.scrollWidth<=name.clientWidth+1;
                          return {
                            ok,
                            lines:ink.length,
                            text:name.textContent.trim(),
                            fontSize:style.fontSize,
                            whiteSpace:style.whiteSpace,
                            rectWidth:Math.round(bounds.width),
                            clientWidth:name.clientWidth,
                            scrollWidth:name.scrollWidth,
                            stageWidth:Math.round(canvas.width),
                            textRight:ink[0]?Math.round(ink[0].right):null,
                            stageRight:Math.round(canvas.right)
                          };
                        })(),
                        heroBrandVisible:(() => {
                            const e=document.querySelector('.hero-brand-type');
                            if(!e)return false;
                            const b=e.getBoundingClientRect(), style=getComputedStyle(e);
                            return style.display!=='none' && style.visibility!=='hidden' &&
                                   b.width>150 && b.height>60;
                        })(),
                        bodyFont:bodyStyle.fontFamily,
                        bodyBg:bodyStyle.backgroundColor,
                        heroBg:heroStyle?.backgroundColor || null,
                        navDisplay:nav?getComputedStyle(nav).display:null,
                        brandWidth:brand?.getBoundingClientRect().width||0,
                        logoWidth:image?.getBoundingClientRect().width||0,
                        overflow:document.documentElement.scrollWidth>innerWidth+2,
                        horizontalScroll:document.documentElement.scrollWidth,
                        viewport:innerWidth
                      };
                    }""")
                    entry.update(metrics)
                    entry["status"] = response.status if response else None
                    entry["file"] = f"live-{width}-{route.replace('/','_') or 'home'}.png"
                    page.screenshot(path=str(OUT / entry["file"]), full_page=True, timeout=30000, animations="disabled")
                    if entry["status"] != 200:
                        audit["errors"].append(f"{width} {route}: HTTP {entry['status']}")
                    if not metrics["hasInlineCSS"]:
                        if not metrics["hasLinkedCSS"] or metrics["bodyBg"]!="rgb(244, 240, 232)":
                            audit["errors"].append(f"{width} {route}: neither inline nor functional external CSS")
                        else:
                            audit["warnings"].append(f"{width} {route}: older external CSS response still cached; site styled but exact deployment freshness pending")
                    if not metrics["hasInlineJS"] and not metrics["hasLinkedJS"]:
                        audit["errors"].append(f"{width} {route}: no live JavaScript for interactive menu")
                    if route=="" and not metrics["heroBrandVisible"]:
                        audit["errors"].append(f"{width} homepage: brand typography fallback NOT VISIBLE; empty hero")
                    if route=="" and not metrics["heroBrandGeometry"]["ok"]:
                        audit["errors"].append(f"{width} homepage: business name wrap or clipping {metrics['heroBrandGeometry']}")
                    if metrics["bodyFont"] in ("Times New Roman", '"Times New Roman"', "serif"):
                        audit["errors"].append(f"{width} {route}: DEFAULT BROWSER TYPOGRAPHY -- STYLES FAILED")
                    if metrics["logoWidth"] > 110 or metrics["brandWidth"] > 340:
                        audit["errors"].append(f"{width} {route}: HUGE UNSIZED BRAND ASSET")
                    if metrics["overflow"]:
                        audit["errors"].append(f"{width} {route}: HORIZONTAL OVERFLOW")
                    if route=="" and metrics["heroBg"] not in ("rgb(14, 44, 35)", "rgb(14, 44, 35)"):
                        audit["errors"].append(f"{width} {route}: HERO BACKGROUND NOT STYLED ({metrics['heroBg']})")
                except Exception as error:
                    audit["errors"].append(f"{width} {route}: {type(error).__name__}: {str(error)[:250]}")
                audit["pages"].append(entry)
            if width==390:
                try:
                    page.goto(URL + "/palvelut/", wait_until="domcontentloaded", timeout=40000)
                    toggle = page.locator("button[data-menu]")
                    toggle.click()
                    if not page.locator("nav[data-nav]").evaluate("(e)=>e.classList.contains('open')"):
                        audit["errors"].append("Live mobile navigation JS not functioning")
                except Exception as error:
                    audit["errors"].append(f"Live mobile interaction failed: {type(error).__name__}: {str(error)[:250]}")
            ctx.close()
        browser.close()
    (OUT/"report.json").write_text(json.dumps(audit,indent=2,ensure_ascii=False),encoding="utf-8")
    print("RENDER_LIVE_SMOKE",json.dumps({"pages":len(audit["pages"]),"errors":audit["errors"],"warnings":audit["warnings"],"snapshots":OUT.as_posix()}))
    return 1 if audit["errors"] else 0

if __name__=="__main__":
    sys.exit(main())

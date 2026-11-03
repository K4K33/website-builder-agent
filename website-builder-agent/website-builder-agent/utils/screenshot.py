"""Capture original-company screenshots without any paid AI or search API.

The source capture is compared with real generated-site screenshots at identical
viewport sizes. Screenshots are evidence for judgement, not permission to reuse
photographs or an automatic visual rating. Failed captures never count as pass.
"""
from __future__ import annotations

import ipaddress
from pathlib import Path
from datetime import datetime, timezone
from urllib.parse import urlsplit

from playwright.sync_api import sync_playwright


OUTPUT_DIR = "output/screenshots"
VIEWPORTS = (
    ("desktop", 1440, 900),
    ("tablet", 768, 1024),
    ("mobile", 390, 844),
    ("small_mobile", 320, 740),
)


def _safe_filename(name: str) -> str:
    value = (name or "website").strip()
    safe = "".join(c if c.isalnum() or c in "-_" else "_" for c in value)
    return safe.strip("_") or "website"


def _safe_remote_url(url: str) -> bool:
    """Reject obvious local/private URL targets; no user-controlled file URLs."""
    parsed = urlsplit(str(url or ""))
    host = (parsed.hostname or "").casefold().rstrip(".")
    if parsed.scheme not in ("http", "https") or not host:
        return False
    if host in {"localhost", "localhost.localdomain"} or host.endswith(".local"):
        return False
    try:
        ip = ipaddress.ip_address(host)
        return ip.is_global
    except ValueError:
        return True


FIRST_VIEW_SCRIPT = """() => {
    const main = document.querySelector('main') || document.body;
    const viewportWidth = innerWidth, viewportHeight = innerHeight;
    const nodes = [...main.querySelectorAll('img, picture, video')];
    const visible = el => {
        const r = el.getBoundingClientRect(), s = getComputedStyle(el);
        return r.width > 0 && r.height > 0 && s.display !== 'none' &&
            s.visibility !== 'hidden';
    };
    const area = el => {
        const r = el.getBoundingClientRect();
        return Math.max(0, Math.min(r.right, viewportWidth) - Math.max(0, r.left)) *
               Math.max(0, Math.min(r.bottom, viewportHeight) - Math.max(0, r.top));
    };
    const present = nodes.filter(visible);
    return {
        measured: true, viewportWidth, viewportHeight,
        visibleMainMedia: present.filter(el => area(el) > 250).length,
        allMainMedia: present.length,
        mainMediaBelowFold: present.filter(el =>
            el.getBoundingClientRect().top >= viewportHeight).length,
        firstFoldVisibleMediaArea: Math.round(present.reduce(
            (total, el) => total + area(el), 0)),
    };
}"""


def capture_website(url: str, company_name: str) -> dict | None:
    """Capture full-page source and DOM first-view metadata at four dimensions.

    The old desktop/mobile keys are retained for existing research/QA callers.
    """
    if not _safe_remote_url(url):
        print("  [screenshot] Original capture refused: invalid or local URL.")
        return None
    folder = Path(OUTPUT_DIR).resolve()
    folder.mkdir(parents=True, exist_ok=True)
    filename = _safe_filename(company_name)
    results = {}
    metrics = {}
    print("  [screenshot] Original source capture: " + str(url))
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            try:
                for name, width, height in VIEWPORTS:
                    context = browser.new_context(
                        viewport={"width": width, "height": height},
                        device_scale_factor=1,
                        is_mobile=width <= 390,
                        has_touch=width <= 390,
                        reduced_motion="reduce",
                        service_workers="block",
                    )
                    try:
                        page = context.new_page()
                        page.goto(url, wait_until="domcontentloaded", timeout=25000)
                        page.wait_for_timeout(750)
                        try:
                            metrics[name] = page.evaluate(FIRST_VIEW_SCRIPT)
                        except Exception:
                            metrics[name] = {"measured": False}
                        target = folder / (filename + "_" + name + ".png")
                        page.screenshot(path=str(target), full_page=True,
                                        animations="disabled", timeout=20000)
                        results[name] = str(target)
                        print("  [screenshot] " + name + ": OK")
                    except Exception as error:
                        print("  [screenshot] " + name + ": unavailable (" +
                              type(error).__name__ + ")")
                    finally:
                        context.close()
            finally:
                browser.close()
    except Exception as error:
        print("  [screenshot] Browser unavailable: " + type(error).__name__)
        return None

    if not results:
        return None
    results["first_fold_observations"] = metrics
    results["captured_at"] = datetime.now(timezone.utc).isoformat()
    results["capture_url"] = str(url)
    return results

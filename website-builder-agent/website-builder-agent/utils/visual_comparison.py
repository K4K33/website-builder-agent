"""Source-versus-redesign visual evidence and bounded, explicit repair hints.

Browser screenshots and first-fold observations are evidence, not design scores.
This module never certifies screenshot similarity, copyright or client consent.
The generated HTML contact sheet is for human / independent model review.
"""
from __future__ import annotations

import hashlib
import html
import json
import os
from pathlib import Path

from utils.content_parity import source_inventory_sha256
from utils.premium_quality_gate import site_digest


VIEWPORTS = (
    ("small_mobile", 320, 740),
    ("mobile", 390, 844),
    ("tablet", 768, 1024),
    ("desktop", 1440, 900),
)
IMAGE_LED_SECTORS = (
    "kukka", "florist", "flower", "salon", "kampa", "parturi",
    "hius", "beauty", "kauneu", "restaurant", "ravintol", "cafe",
    "kahvila", "leipomo", "bakery", "food", "ruoka", "puutarha",
    "garden", "photograph", "valokuva", "design", "sisustus",
    "puku", "vaate", "boutique", "jewellery", "koru", "art", "taide",
)


def _existing_image(value: object) -> Path | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        item = Path(value).expanduser().resolve()
        if item.is_file() and item.suffix.lower() in (".png", ".jpg", ".jpeg", ".webp"):
            return item
    except (OSError, ValueError):
        return None
    return None


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as file:
        for block in iter(lambda: file.read(1024 * 512), b""):
            h.update(block)
    return h.hexdigest()


def _relative(path: Path, relative_to: Path) -> str:
    return Path(os.path.relpath(path, relative_to)).as_posix()


def _industry_is_image_led(research: dict) -> bool:
    facts = research.get("company_facts") or {}
    value = str(facts.get("industry") or "").casefold()
    return bool(value and any(word in value for word in IMAGE_LED_SECTORS))


def _first_fold_repair_hints(source: dict, redesigned: dict, research: dict) -> list[dict]:
    """Suggest repairs only when comparable measured first screens justify it."""
    if not _industry_is_image_led(research):
        return []
    original = source.get("first_fold_observations") or {}
    replacement = redesigned.get("first_fold_observations") or {}
    evidence = []
    for name, width, height in VIEWPORTS[:2]:
        before, after = original.get(name), replacement.get(name)
        if not isinstance(before, dict) or not isinstance(after, dict):
            continue
        if not (before.get("measured") is True and after.get("measured") is True):
            continue
        if before.get("viewportWidth") != width or after.get("viewportWidth") != width:
            continue
        # The photo-rich baseline must be explicitly visible. A CSS background
        # or lazy-loaded source image may be missing from DOM accounting.
        before_ratio = (float(before.get("firstFoldVisibleMediaArea") or 0)
                        / max(1, width * height))
        after_ratio = (float(after.get("firstFoldVisibleMediaArea") or 0)
                       / max(1, width * height))
        if before_ratio >= 0.09 and after_ratio < 0.02:
            evidence.append({
                "kind": "image_led_mobile_first_fold_regression",
                "severity": "review_and_repair",
                "viewport": name,
                "source_visible_media_fraction": round(before_ratio, 3),
                "redesign_visible_media_fraction": round(after_ratio, 3),
                "original_first_fold": before,
                "redesign_first_fold": after,
                "suggestion": (
                    "Real source photos dominate the old first view but the new "
                    "first view has almost no visible img/video. Review screenshots "
                    "and give genuine business imagery earlier visual priority; "
                    "preserve truthful main heading, brand and contact actions. "
                    "Do not invent media or assume CSS backgrounds prove source fidelity."
                ),
            })
    return evidence


def _generate_panel(browser, *, name: str, width: int, height: int,
                    old: Path, new: Path, destination: Path) -> bool:
    """Create an ACTUAL first-viewport two-column PNG from real captured files."""
    old_src = html.escape(_relative(old, destination.parent), quote=True)
    new_src = html.escape(_relative(new, destination.parent), quote=True)
    panel_html = destination.with_suffix(".html")
    panel_html.write_text(
        '<!doctype html><html><head><meta charset="utf-8"><style>'
        '*{box-sizing:border-box}body{margin:0;background:#f3f1ed;'
        'font:14px Arial,sans-serif;color:#181818}'
        '.pair{display:flex;gap:16px;padding:16px;width:max-content}'
        '.view{width:' + str(width) + 'px;flex-shrink:0}'
        '.label{font-weight:700;height:32px;line-height:32px}'
        '.fold{height:' + str(height) + 'px;overflow:hidden;background:white;'
        'border:1px solid #ddd}.fold img{display:block;width:' + str(width) +
        'px;height:auto;max-width:none}</style></head><body><div class="pair">'
        '<div class="view"><div class="label">ALKUPERÄINEN · ' + html.escape(name) +
        '</div><div class="fold"><img src="' + old_src + '"></div></div>'
        '<div class="view"><div class="label">UUSI · ' + html.escape(name) +
        '</div><div class="fold"><img src="' + new_src +
        '"></div></div></div></body></html>', encoding="utf-8"
    )
    page = browser.new_page(viewport={"width": width * 2 + 48,
                                     "height": height + 64},
                            device_scale_factor=1)
    try:
        # The sheet is local and may not load any remote asset.
        page.route("**/*", lambda route: route.continue_()
                   if route.request.url.startswith(("file:", "data:")) else route.abort())
        page.goto(panel_html.as_uri(), wait_until="load", timeout=12000)
        loaded = page.evaluate("""() => [...document.images].length === 2 &&
            [...document.images].every(i => i.complete && i.naturalWidth > 0)""")
        if not loaded:
            return False
        page.locator(".pair").screenshot(path=str(destination), animations="disabled",
                                          timeout=12000)
        return True
    finally:
        page.close()


def build_visual_comparison(
    original_screenshots: dict | None,
    browser_home: dict | None,
    rendered_pages: dict[str, str],
    research: dict,
    *,
    report_dir: str | Path,
    render_panels: bool = True,
) -> dict:
    """Emit original/new paired evidence; never substitute source screenshots.

    The original screenshot capture can be absent because some source sites
    reject a headless browser. Such a build stays pending visual review.
    """
    source = original_screenshots if isinstance(original_screenshots, dict) else {}
    current = browser_home if isinstance(browser_home, dict) else {}
    destination = Path(report_dir).resolve()
    destination.mkdir(parents=True, exist_ok=True)
    source_inventory = research.get("source_inventory") or {}
    has_original_site = bool(source_inventory.get("pages"))
    source_hash = source_inventory_sha256(source_inventory) if has_original_site else ""
    digest = site_digest(rendered_pages)
    old_shots = source.get("screenshots") if isinstance(source.get("screenshots"), dict) else source
    new_shots = current.get("screenshots") or {}
    pairs = {}
    evidence_missing = []
    for name, width, height in VIEWPORTS:
        old = _existing_image(old_shots.get(name))
        new = _existing_image(new_shots.get(name))
        if has_original_site and not old:
            evidence_missing.append("Original " + name + " screenshot missing.")
        if not new:
            evidence_missing.append("Redesign " + name + " screenshot missing.")
        if old and new:
            pairs[name] = {
                "viewport": {"width": width, "height": height},
                "original": str(old), "redesign": str(new),
                "original_sha256": _sha(old), "redesign_sha256": _sha(new),
            }
    hints = _first_fold_repair_hints(source, current, research) if has_original_site else []
    # Preserve the screenshots for independent source-vs-new review even when
    # no static metric suggests a defect. A visual mismatch can be subjective.
    panel_errors = []
    if render_panels and pairs:
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as pw:
                browser = pw.chromium.launch(headless=True)
                try:
                    for name, width, height in VIEWPORTS:
                        if name not in pairs:
                            continue
                        dest = destination / ("first-fold-" + name + ".png")
                        try:
                            if _generate_panel(
                                browser, name=name, width=width, height=height,
                                old=Path(pairs[name]["original"]),
                                new=Path(pairs[name]["redesign"]),
                                destination=dest,
                            ):
                                pairs[name]["comparison_image"] = str(dest)
                                pairs[name]["comparison_sha256"] = _sha(dest)
                            else:
                                panel_errors.append(name + ": source/new images did not load")
                        except Exception as error:
                            panel_errors.append(name + ": " + type(error).__name__)
                finally:
                    browser.close()
        except Exception as error:
            panel_errors.append("Comparison renderer unavailable: " + type(error).__name__)
    if render_panels and has_original_site and not pairs:
        panel_errors.append("No source-versus-redesign screenshots available to compare.")
    # No numeric design score: screenshot pixel difference is not a proxy for
    # improvement and stronger photo contrast is not always brand-correct.
    status = (
        "review_required" if has_original_site and (evidence_missing or panel_errors) else
        "repair_suggested" if hints else
        "paired_for_human_review" if has_original_site else
        "no_original_site"
    )
    report = {
        "status": status,
        "source_sha256": source_hash,
        "build_sha256": digest,
        "pairs": pairs,
        "missing": evidence_missing,
        "render_errors": panel_errors,
        "repair_hints": hints,
        "human_comparison_required": has_original_site,
        "note": (
            "These are source and generated screenshots at matching widths, "
            "not an independent visual score or verified licence. "
            "Human review must check identity, photo priority, voice and "
            "layout against the original before client release."
        ),
    }
    manifest_path = destination / "visual-comparison.json"
    manifest_path.write_text(json.dumps(report, ensure_ascii=False, indent=2),
                             encoding="utf-8")
    report["report_path"] = str(manifest_path)
    sheet = [
        '<!doctype html><html lang="fi"><head><meta charset="utf-8"><title>'
        'Kaurivo · alkuperäinen vs uusi</title><style>'
        'body{font:16px system-ui,sans-serif;max-width:1100px;margin:2rem auto;'
        'padding:0 1.5rem;color:#171717;background:#f7f5f2}'
        'p{line-height:1.6}.pair{margin:2rem 0}img{display:block;max-width:100%;'
        'height:auto;border:1px solid #ccc;background:white}'
        'code{overflow-wrap:anywhere}a{color:#134568}</style></head><body>'
        '<h1>Kaurivo · sivustojen visuaalinen vertailu</h1>'
        '<p>Alkuperäinen vasemmalla, uusi oikealla. Kuvissa näkyy vastaava '
        'ensimmäinen näyttö, ei arvosanaa eikä automaattista hyväksyntää.</p>'
    ]
    for name, _, _ in VIEWPORTS:
        if name in pairs:
            p = pairs[name]
            sheet.append('<section class="pair"><h2>' + html.escape(name) + '</h2>')
            if p.get("comparison_image"):
                sheet.append('<img alt="Alkuperäinen ja uusi rinnakkain" src="' +
                             html.escape(_relative(Path(p["comparison_image"]), destination),
                                         quote=True) + '">')
            else:
                for label in ("original", "redesign"):
                    sheet.append('<h3>' + label + '</h3><img src="' +
                                 html.escape(_relative(Path(p[label]), destination),
                                             quote=True) + '">')
            sheet.append('</section>')
    if evidence_missing or panel_errors:
        sheet.append("<h2>Puuttuva näyttö</h2><ul>" + "".join(
            "<li>" + html.escape(x) + "</li>"
            for x in evidence_missing + panel_errors
        ) + "</ul>")
    if hints:
        sheet.append("<h2>Korjausehdotukset, tarkistettava kuvista</h2><ul>" + "".join(
            "<li>" + html.escape(x["suggestion"]) + " (" +
            html.escape(x["viewport"]) + ")</li>" for x in hints
        ) + "</ul>")
    sheet.append("<p>Rakennuksen SHA-256: <code>" + html.escape(digest) +
                 "</code></p></body></html>")
    html_path = destination / "index.html"
    html_path.write_text("".join(sheet), encoding="utf-8")
    report["comparison_html"] = str(html_path)
    return report

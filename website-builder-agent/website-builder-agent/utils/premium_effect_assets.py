"""Full-site, local-asset aware art-direction motion inspection.

This does not score aesthetics or claim that a third-party script was inspected.
Resolve only safe local CSS/JS paths and keep unavailable/external scripts pending.
"""
from __future__ import annotations

from pathlib import Path
from urllib.parse import urlsplit, unquote

from bs4 import BeautifulSoup

from utils.visual_direction import audit_visual_motion


def audit_premium_effect_assets(pages: dict[str, str], site_root: str | Path) -> dict:
    """Report all-site source motion risks using actual linked asset contents."""
    root = Path(site_root).resolve()
    styles, scripts, missing, external, inspected = [], [], [], [], set()
    for route, html in (pages or {}).items():
        soup = BeautifulSoup(html or "", "html.parser")
        refs = [
            ("css", str(tag.get("href") or ""))
            for tag in soup.select('link[rel~="stylesheet"][href]')
        ] + [
            ("js", str(tag.get("src") or ""))
            for tag in soup.select("script[src]")
        ]
        for kind, raw in refs:
            parts = urlsplit(raw)
            if parts.scheme or parts.netloc or raw.startswith("//"):
                external.append(f"{route}: {raw}")
                continue
            if not parts.path:
                missing.append(f"{route}: empty local {kind} asset")
                continue
            try:
                decoded = unquote(parts.path)
                target = (root / decoded.lstrip("/") if decoded.startswith("/")
                          else root / route / ".." / decoded).resolve()
                if not target.is_relative_to(root):
                    missing.append(f"{route}: asset path escapes site root: {raw}")
                    continue
                if not target.is_file() or target.suffix.lower() != "." + kind:
                    missing.append(f"{route}: missing {kind} asset: {raw}")
                    continue
                if target in inspected:
                    continue
                inspected.add(target)
                source = target.read_text(encoding="utf-8")
            except (OSError, UnicodeError, ValueError):
                missing.append(f"{route}: unreadable {kind} asset: {raw}")
                continue
            (styles if kind == "css" else scripts).append(source)

    report = audit_visual_motion(
        pages, css_text="\n".join(styles), js_text="\n".join(scripts),
        assets_complete=not external and not missing,
    )
    if missing:
        report["blocking"].extend(missing)
    if external:
        report["pending"].append(
            "External JS/CSS effects were not statically inspected: " +
            "; ".join(external[:6])
        )
    report["observations"].update({
        "inspected_local_assets": len(inspected),
        "missing_local_assets": missing,
        "external_assets_pending": external,
    })
    return report

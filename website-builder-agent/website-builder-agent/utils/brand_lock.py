"""Kaurivo source-first identity lock: no generated company marks by default.

A planning prompt alone cannot guarantee brand fidelity. This deterministic
guard checks recognisable brand slots across *all* generated routes against
the source inventory and explicit client-approved asset mappings.

It does NOT claim that a copied URL grants intellectual-property rights,
that a name or URL proves authenticity, or that the site looks on-brand.
Missing source/usage evidence stays visible as pending instead of an invented
pass. Never call a model or a paid external API from this module.
"""
from __future__ import annotations

import re
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup

from utils.content_parity import source_inventory_sha256
from utils.premium_quality_gate import site_digest


BRAND_HINT = re.compile(
    r"(?:^|[\s\-_])(?:brand|logo|wordmark|lettermark|monogram|emblem|"
    r"identity|site-mark|site-logo|tunnus|liikemerkki|merkki)(?:$|[\s\-_])",
    re.I,
)
# SVGs used for navigation (menu/search/close) are not business logos.
NAVIGATION_HINT = re.compile(
    r"(?:menu|hamburger|search|close|chevron|arrow|cart|user|"
    r"navigation|toggle|magnif)", re.I,
)


def _text(value: object) -> str:
    return " ".join(str(value or "").split())


def _source_assets(research: dict) -> tuple[set[str], set[str], str]:
    inventory = research.get("source_inventory") or {}
    originals: set[str] = set()
    favicons: set[str] = set()
    for page in inventory.get("pages") or []:
        if not isinstance(page, dict):
            continue
        source = _text(page.get("url"))
        identity = page.get("source_identity") or {}
        if not isinstance(identity, dict):
            continue
        for original in identity.get("original_logo_candidates") or []:
            if isinstance(original, str) and original.strip():
                originals.add(urljoin(source, original.strip()))
        for original in identity.get("original_favicon_candidates") or []:
            if isinstance(original, str) and original.strip():
                favicons.add(urljoin(source, original.strip()))
    asset_record = research.get("brand_assets") or {}
    approved = _text(asset_record.get("approved_original_logo_url"))
    if approved:
        originals.add(approved)
    approved_favicon = _text(asset_record.get("approved_favicon_url"))
    if approved_favicon:
        favicons.add(approved_favicon)
    return originals, favicons, source_inventory_sha256(inventory) if inventory.get("pages") else ""


def _signed(record: object, *, digest: str, source_hash: str) -> bool:
    if not isinstance(record, dict):
        return False
    if not (
        record.get("approved") is True
        and record.get("reviewer_kind") == "client"
        and _text(record.get("reviewer"))
        and _text(record.get("checked_at"))
        and record.get("build_sha256") == digest
    ):
        return False
    if source_hash:
        return record.get("source_sha256") == source_hash
    return bool(record.get("source_evidence"))


def _valid_replacements(research: dict, originals: set[str], *,
                        digest: str, source_hash: str) -> set[str]:
    """Only exact-client-approved current-build aliases are trusted.

    A filename like logo-final.svg, a CSS background, or a model-predicted
    replacement are NOT evidence. The reviewer must confirm the source asset
    and its transformed result independently.
    """
    result = set()
    for item in research.get("approved_asset_replacements") or []:
        if not _signed(item, digest=digest, source_hash=source_hash):
            continue
        origin = _text(item.get("original_src"))
        if origin not in originals:
            continue
        replacement = _text(item.get("replacement_src"))
        if replacement and item.get("rights_verified") is True and item.get("visual_match_verified") is True:
            result.add(replacement)
    return result


def _mark_elements(header) -> list[tuple[object, str]]:
    """Recognise explicit brand-mark slots without catching navigation icons."""
    if header is None:
        return []
    found = []
    for node in header.find_all(["img", "svg", "canvas", "span", "div", "strong", "b"]):
        attrs = " ".join([
            " ".join(node.get("class") or []), _text(node.get("id")),
            _text(node.get("role")), _text(node.get("aria-label")),
            _text(node.get("alt")), _text(node.get("title")),
        ])
        parent = node.parent
        if parent and parent is not header:
            attrs += " " + " ".join(parent.get("class") or [])
        if node.name == "img":
            # A header image without an identity role remains subject to
            # existing media QA. Do not mistake a search icon for a logo.
            if BRAND_HINT.search(attrs):
                found.append((node, "image"))
        elif node.name in {"svg", "canvas"}:
            if BRAND_HINT.search(attrs) and not NAVIGATION_HINT.search(attrs):
                found.append((node, "generated_graphic"))
        elif BRAND_HINT.search(attrs):
            text = _text(node.get_text(" ", strip=True))
            # A full company name in a brand element is a valid fallback;
            # the unexplained 1-3-character seal is not.
            if 1 <= len(text) <= 3 and text.isalpha():
                found.append((node, "short_mark"))
    return found


def audit_brand_lock(rendered_pages: dict[str, str],
                     research: dict | None = None) -> dict:
    """Detect invented brand marks, silent logo swaps and favicon mismatch.

    Original source logo observations do not prove a licence. Source logos
    without explicit identity/rights signoff are reported as pending.
    Where the client explicitly approved the original logo, its absence
    from any route's header is a blocking design regression.
    """
    research = research or {}
    originals, favicons, source_hash = _source_assets(research)
    digest = site_digest(rendered_pages)
    brand_assets = research.get("brand_assets") or {}
    approved_primary = _text(brand_assets.get("approved_original_logo_url"))
    approved_favicon = _text(brand_assets.get("approved_favicon_url"))
    allowed_new = _signed(research.get("approved_new_brand_mark"),
                          digest=digest, source_hash=source_hash)
    allowed = originals | _valid_replacements(research, originals,
                                              digest=digest, source_hash=source_hash)
    blocked, pending, routes = [], [], {}
    for route, html in rendered_pages.items():
        soup = BeautifulSoup(html, "html.parser")
        header = soup.find("header") or soup.find(attrs={"role": "banner"})
        marks = _mark_elements(header)
        approved_found = False
        for element, kind in marks:
            if kind == "image":
                src = _text(element.get("src") or element.get("data-src"))
                # A direct absolute source asset is identifiable from the
                # source snapshot. Relative output paths need a signed
                # replacement (or an explicit approved local primary path).
                if src in allowed:
                    approved_found = True
                    continue
                if allowed_new:
                    continue
                blocked.append({
                    "category": "unsourced_header_logo",
                    "route": route, "src": src[:200],
                    "issue": "Header logo has no original-source identity or current client-approved replacement.",
                })
            elif not allowed_new:
                blocked.append({
                    "category": "invented_graphic_brand_mark",
                    "route": route, "kind": kind,
                    "issue": "Unapproved SVG/canvas/initial mark in the business brand area.",
                })

        if approved_primary and not approved_found and not allowed_new:
            blocked.append({
                "category": "approved_original_logo_missing_from_header",
                "route": route,
                "issue": "The explicitly approved original logo is absent from this page's header.",
            })
        elif originals and not approved_found and not allowed_new:
            pending.append({
                "category": "original_brand_fallback_review",
                "route": route,
                "issue": "Original logo observed but no source-matched header mark; verify text-only fallback, rights and owner preference.",
            })

        if not approved_primary and approved_found:
            pending.append({
                "category": "source_logo_rights_review", "route": route,
                "issue": "Source asset identity found; lawful logo use and client signoff still require verification.",
            })
        icon_links = soup.select(
            'link[rel~="icon"],link[rel~="apple-touch-icon"],'
            'link[rel~="shortcut"][rel~="icon"]'
        )
        for tag in icon_links:
            href = _text(tag.get("href"))
            if not href:
                continue
            if approved_favicon:
                if href != approved_favicon and not allowed_new:
                    blocked.append({
                        "category": "approved_favicon_replaced", "route": route,
                        "href": href[:200],
                    })
            elif favicons and href not in favicons:
                pending.append({
                    "category": "favicon_identity_review", "route": route,
                    "issue": "New favicon differs from observed original; verify logo and rights.",
                })
            elif not favicons and href.startswith("data:image/svg+xml"):
                pending.append({
                    "category": "generated_favicon_review", "route": route,
                    "issue": "Generated SVG favicon has no source-linked identity evidence.",
                })
        routes[route] = {
            "brand_mark_slots_checked": len(marks),
            "original_logo_in_header": approved_found,
            "favicons_checked": len(icon_links),
        }
    return {
        "pass": not blocked and not pending,
        "blocking": blocked, "pending": pending,
        "routes": routes,
        "original_logo_candidates": len(originals),
        "original_favicon_candidates": len(favicons),
        "note": (
            "DOM/source evidence only; not visual equality, file-byte authenticity "
            "or ownership proof. Header CSS backgrounds and dynamically rendered "
            "marks require a separate browser/asset review."
        ),
    }

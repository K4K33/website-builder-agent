"""Source-bound design brief: site map -> section wireframes -> shared brand kit.

Informed by documented workflows from Relume, Webflow and Wix Harmony.
This module creates a *planning contract*, not unlicensed brand artwork,
HTML components, visual score or a substitute for independent visual QA.
It makes all planned pages and style decisions visible before a Build credit.
"""
from __future__ import annotations

from collections import defaultdict
import re
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

from utils.content_parity import source_inventory_sha256


def _one(value: object, maxlen: int = 480) -> str:
    return " ".join(str(value or "").strip().split())[:maxlen]


def derive_brand_site_blueprint(research: dict) -> dict:
    """Generate stable, original-company first brief without guessing colors."""
    arch = research.get("site_architecture") or {}
    pages = arch.get("pages") or []
    choices = research.get("creative_directions") or []
    selected = str((research.get("creative_selection") or {}).get("selected_id") or "").strip()
    selected_direction = next(
        (direction for direction in choices
         if isinstance(direction, dict) and direction.get("id") == selected), None
    )
    if not pages or selected_direction is None:
        raise RuntimeError("Missing chosen creative direction or researched site map.")
    inventory = research.get("source_inventory") or {}
    snapshots = [page for page in inventory.get("pages") or []
                 if isinstance(page, dict)]
    brand_colors: dict[str, list[str]] = defaultdict(list)
    authentic_logo = {}
    photos = {}
    for page in snapshots:
        url = str(page.get("url") or "")
        identity = page.get("source_identity") or {}
        if not isinstance(identity, dict):
            continue
        color = str(identity.get("theme_color") or "").strip()
        if color and url and url not in brand_colors[color]:
            brand_colors[color].append(url)
        for logo in identity.get("original_logo_candidates") or []:
            if isinstance(logo, str) and logo:
                authentic_logo.setdefault(logo, []).append(url)
        for photo in identity.get("original_content_photos") or []:
            if isinstance(photo, dict) and photo.get("src"):
                photos.setdefault(photo["src"], []).append(url)
    rec = research.get("design_recommendations") or {}
    source_map = {
        str(row.get("target") or ""): row
        for row in (research.get("source_content_map") or {}).get("pages") or []
        if isinstance(row, dict)
    }
    architecture = []
    for page in pages:
        route = str(page.get("path") or "")
        origin = [
            str(item.get("source_url") or "")
            for item in (research.get("source_content_map") or {}).get("pages") or []
            if isinstance(item, dict)
            and str(item.get("target") or "").split("#", 1)[0] == route
        ]
        architecture.append({
            "route": route, "purpose": _one(page.get("purpose")),
            "visitor_task": _one(page.get("user_task")),
            "wireframe_section_ids": list(page.get("section_ids") or []),
            "relevant_source_urls": list(dict.fromkeys(origin)),
        })
    source_sha = source_inventory_sha256(inventory) if snapshots else ""
    return {
        "protocol": "company_source_to_sitemap_wireframe_brand_style_2026-11",
        "source_sha256": source_sha,
        "company_name": _one((research.get("company_facts") or {}).get("name")),
        "sitemap_and_wireframes": architecture,
        "selected_direction": {
            "id": selected, "concept": _one(selected_direction.get("concept")),
            "source_anchor": _one(selected_direction.get("source_anchor")),
            "first_view": _one(selected_direction.get("first_view")),
            "information_architecture": _one(selected_direction.get("information_architecture")),
            "navigation": _one(selected_direction.get("navigation")),
        },
        "shared_brand_system": {
            "sourced_original_theme_colors": [
                {"color": color, "source_urls": urls}
                for color, urls in sorted(brand_colors.items())
            ],
            "original_logo_candidates": [
                {"url": url, "source_urls": list(dict.fromkeys(origins))}
                for url, origins in sorted(authentic_logo.items())
            ],
            "original_photo_candidates": [
                {"url": url, "source_urls": list(dict.fromkeys(origins))}
                for url, origins in sorted(photos.items())
            ][:25],
            "typography_direction": _one(rec.get("typography_scale")),
            "spacing_and_layout": _one(rec.get("spacing_and_layout")),
            "mobile_plan": _one(rec.get("mobile_plan")),
            "color_use_requires_source_or_approved_plan": True,
            "original_identity_comes_first": True,
            "never_auto_generate_client_logo": True,
            "sitewide_consistency_required": True,
            "not_a_rights_license": True,
        },
        "source_diligence": {
            "failed_urls": list(inventory.get("failed_urls") or []),
            "priority_unvisited_urls": list(inventory.get("priority_unvisited_urls") or []),
            "no_website": research.get("research_mode") == "verified_no_website",
        },
        "note": (
            "Separate business facts from internal citations and QA notes. "
            "Produce the planned routes from the company-specific brief, use "
            "the same coherent style tokens across them, keep edits possible "
            "through a verified CMS. Do not copy external provider components. "
            "True source meaning, art rights and 9.5 visual quality require review."
        ),
    }


def _declared_identity_tokens(html: str) -> dict[str, str]:
    """Read explicit global CSS brand tokens, not contextual section styling.

    This intentionally ignores external stylesheets and dynamic CSS. Only
    contradictory values found in comparable inline :root declarations are
    definitive static failures; missing values remain outside this check.
    """
    soup = BeautifulSoup(html, "html.parser")
    declared: dict[str, set[str]] = defaultdict(set)
    for tag in soup.find_all("style"):
        css = re.sub(r"/\\*.*?\\*/", "", tag.get_text(" ", strip=False), flags=re.S)
        for block in re.findall(r"(?<![\\w-]):root\\s*\\{([^{}]*)\\}", css, flags=re.I | re.S):
            for match in re.finditer(r"(--[a-z][\\w-]*)\\s*:\\s*([^;{}]+)", block, flags=re.I):
                key, value = match.group(1).lower(), " ".join(match.group(2).split()).lower()
                # These deliberately name the site-wide identity. Do not
                # compare generic section/seasonal/background utility colors.
                if key.startswith(("--brand-", "--identity-")) or key in {
                    "--color-primary", "--color-accent", "--font-brand",
                    "--font-heading", "--font-body",
                }:
                    declared[key].add(value.removesuffix("!important").strip())
    # If a token has several values on one page (e.g. an adaptive override),
    # the static test cannot confidently select the effective value.
    return {key: next(iter(values)) for key, values in declared.items() if len(values) == 1}


def audit_sitewide_brand_consistency(rendered_pages: dict[str, str]) -> dict:
    """Fail on contradictory global identity tokens across the site's pages.

    An individual subpage may use a distinct composition, hero color or
    background. An explicitly declared global --brand-primary or heading font
    must not silently switch to a different business identity by route.
    """
    themes: dict[str, str] = {}
    tokens_by_page: dict[str, dict[str, str]] = {}
    for route, html in rendered_pages.items():
        soup = BeautifulSoup(html, "html.parser")
        tag = soup.find("meta", attrs={"name": "theme-color"})
        if tag:
            theme = str(tag.get("content") or "").strip().lower()
            if theme:
                themes[route] = theme
        tokens_by_page[route] = _declared_identity_tokens(html)

    issues = []
    if len(set(themes.values())) > 1:
        issues.append("Inconsistent theme-color across new business site routes.")
    comparable_tokens = sorted({key for tokens in tokens_by_page.values() for key in tokens})
    for key in comparable_tokens:
        found = {route: values[key] for route, values in tokens_by_page.items()
                 if key in values}
        if len(found) > 1 and len(set(found.values())) > 1:
            issues.append(
                f"Conflicting global identity token {key} across routes: "
                + ", ".join(f"{route}={value}" for route, value in sorted(found.items()))
            )
    return {
        "pass": not issues,
        "issues": issues,
        "theme_colors_by_page": themes,
        "identity_tokens_by_page": tokens_by_page,
        "note": (
            "Checked browser theme and comparable inline :root brand tokens only. "
            "External stylesheets, permitted page-specific compositions, "
            "typography and aesthetics still require screenshot review."
        ),
    }

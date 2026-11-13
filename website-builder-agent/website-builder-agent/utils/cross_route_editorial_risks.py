"""Detect cross-route editorial repetition invisible to responsive and brand-mark QA.

This module deliberately returns REVIEW FLAGS, not subjective design scores
or automatic failures: a reused hero photo or shared CTA can be valid, but
multiple repeats on a short brand-rich site require source/new screenshot
inspection. No network, API credits, media licensing or inferred aesthetics.
"""
from __future__ import annotations

from collections import defaultdict
import re
from urllib.parse import urljoin, urlsplit

from bs4 import BeautifulSoup


def _normalize(value: object) -> str:
    return " ".join(str(value or "").casefold().split())


def _media_key(src: str, route: str) -> str:
    """Keep real asset identity; relative paths are resolved against route."""
    value = str(src or "").strip()
    if not value or value.startswith(("data:", "blob:", "javascript:")):
        return ""
    if value.startswith(("http://", "https://", "//")):
        return value.split("#", 1)[0]
    return urljoin("https://local.example/" + str(route).lstrip("/"), value).split("#", 1)[0]


def _photo_rich_original(research: dict) -> bool:
    photos = set()
    for page in (research.get("source_inventory") or {}).get("pages") or []:
        if not isinstance(page, dict):
            continue
        ident = page.get("source_identity") or {}
        for row in ident.get("original_content_photos") or []:
            if isinstance(row, dict) and row.get("src"):
                photos.add(row["src"])
    return len(photos) >= 3



def _localized_page_groups(pages: dict[str, str]) -> dict[str, str]:
    """Count reciprocal hreflang translations as one editorial visitor task.

    A company's FI/SV versions legitimately reuse the SAME photographs.
    Merely naming a locale cannot bypass repetition checks: pages must link
    reciprocally to the exact real counterparts with different HTML language.
    """
    routes = set(pages)
    languages = {}
    alternates: dict[str, set[str]] = {}
    for route, raw in pages.items():
        soup = BeautifulSoup(raw or "", "html.parser")
        languages[route] = str((soup.find("html") or {}).get("lang") or "").lower()
        refs = set()
        for link in soup.select('head link[rel~="alternate"][hreflang][href]'):
            href = str(link.get("href") or "").strip()
            resolved = urlsplit(urljoin("https://local.example/" + route, href))
            if resolved.hostname != "local.example":
                continue
            path = resolved.path.lstrip("/")
            if not path or path.endswith("/"):
                path += "index.html"
            if path in routes and path != route:
                refs.add(path)
        alternates[route] = refs
    parent = {route: route for route in routes}

    def find(route):
        while parent[route] != route:
            parent[route] = parent[parent[route]]
            route = parent[route]
        return route

    for route, targets in alternates.items():
        for target in targets:
            if route not in alternates.get(target, set()):
                continue
            if not languages[route] or not languages[target] or languages[route] == languages[target]:
                continue
            a, b = find(route), find(target)
            parent[max(a, b)] = min(a, b)
    return {route: find(route) for route in routes}


def _is_work_collection(route: str, main) -> bool:
    """Portfolio grids naturally reuse actual work featured elsewhere.

    Do not exempt a page solely because its URL says portfolio: require
    actual collection controls plus original work images, or a substantial
    photo-rich collection layout. Images remain counted for media variety,
    license dependencies and real gallery completeness.
    """
    images = main.find_all("img")
    has_filters = bool(main.select("[data-filter]")) and bool(main.select("[data-category]"))
    visual_grid = len(images) >= 7 and bool(main.select("figure,button[data-image-open]"))
    return len(images) >= 5 and (has_filters or visual_grid)



def audit_cross_route_editorial_risks(pages: dict[str, str],
                                     research: dict | None = None) -> dict:
    """Flags structural monotony and repeated visual assets across all routes.

    Individual legitimate brand choices are never prohibited. Only flag a
    meaningful repeated combination, and require visual proof before premium
    approval. Do not claim to measure natural image size or human aesthetics.
    """
    research = research or {}
    if not isinstance(pages, dict) or len(pages) < 3:
        return {"pending": [], "observations": {"routes": len(pages or {})}}
    original_hosts = {
        (urlsplit(str(page.get("url") or "")).hostname or "").lower().removeprefix("www.")
        for page in (research.get("source_inventory") or {}).get("pages") or []
        if isinstance(page, dict) and page.get("url")
    }
    original_hosts.discard("")
    image_routes: dict[str, set[str]] = defaultdict(set)
    all_image_assets: set[str] = set()
    localized_groups = _localized_page_groups(pages)
    image_mentions = 0
    repeated_heading_routes: dict[str, set[str]] = defaultdict(set)
    repeated_decorated_hero_routes: dict[str, set[str]] = defaultdict(set)
    text_hero_routes = set()
    routes = []
    for route, raw in pages.items():
        if not isinstance(raw, str):
            continue
        soup = BeautifulSoup(raw, "html.parser")
        main = soup.find("main")
        if main is None:
            continue
        routes.append(route)
        images = main.find_all("img")
        collection = _is_work_collection(route, main)
        editorial_group = localized_groups.get(route, route)
        for img in images:
            # Lazy-load placeholders often occupy src while the actual
            # original photo is data-src/data-lazy-src. Count the REAL
            # asset, not a transparent tracking or placeholder data URI.
            value = ""
            for attr in ("data-src", "data-lazy-src", "data-original", "src"):
                candidate = str(img.get(attr) or "").strip()
                if candidate and not candidate.startswith(("data:", "blob:", "javascript:")):
                    value = candidate
                    break
            key = _media_key(value, route)
            if key:
                all_image_assets.add(key)
                if not collection:
                    image_routes[key].add(editorial_group)
                image_mentions += 1
        first = main.find("section")
        if first is not None:
            h1 = first.find("h1")
            if (h1 and not first.find(["img", "video", "picture"])
                    and len(h1.get_text(" ", strip=True).split()) <= 9):
                text_hero_routes.add(editorial_group)
                classes = " ".join(sorted(str(x).lower()
                                          for x in (first.get("class") or [])))
                italic_title = bool(h1.find(["em", "i"]) or
                                    h1.select_one(".serif, .italic, [class*=italic]"))
                kicker = bool(first.select_one(".eyebrow, .overline, .kicker"))
                # This is a narrowly identifiable repeated agency template,
                # not an opinion about whether italic headings are beautiful.
                if classes and italic_title and kicker:
                    repeated_decorated_hero_routes[classes].add(editorial_group)
        unique_headings = set()
        for header in main.select("h2,h3"):
            heading = _normalize(header.get_text(" ", strip=True))
            if len(heading) >= 20:
                unique_headings.add(heading)
        for heading in unique_headings:
            repeated_heading_routes[heading].add(route)

    pending = []
    if len(routes) < 3:
        return {"pending": [], "observations": {"routes": len(routes)}}
    repetitions = sorted(((img, sorted(where)) for img, where in image_routes.items()
                          if len(where) >= 3),
                         key=lambda row: (-len(row[1]), row[0]))
    source_hotlinks = sorted(
        asset for asset in all_image_assets
        if (urlsplit(asset).hostname or "").lower().removeprefix("www.")
        in original_hosts
    )
    if source_hotlinks:
        pending.append({
            "category": "original_hosted_media_dependency",
            "issue": "The new site still loads company photos from the old site's "
                     "server. Confirm redistribution rights and package/download "
                     "licensed assets into owner-controlled hosting before replacing "
                     "the original site; deleting the old host could break the redesign.",
            "external_source_asset_count": len(source_hotlinks),
            "example_assets": source_hotlinks[:4],
        })
    if repetitions:
        pending.append({
            "category": "recycled_business_photography",
            "issue": "The same real product/work photo appears across three or more "
                     "distinct pages. Review whether each route has enough "
                     "purpose-specific visual evidence rather than repeatedly "
                     "using one attractive source picture.",
            "examples": [{"asset": img, "routes": where} for img, where in repetitions[:6]],
        })
    unique_count = len(all_image_assets)
    if len(routes) >= 4 and image_mentions >= 10 and unique_count > 0 and image_mentions >= 2.6 * unique_count:
        pending.append({
            "category": "low_media_variety",
            "issue": "The redesign repeatedly stretches a small source photo set "
                     "over multiple pages. Check source full gallery depth, real "
                     "new photography availability and photo resolution before release.",
            "unique_photos": unique_count,
            "total_image_placements": image_mentions,
        })
    # The exact failure from repeated dark title screens can happen even for
    # a site with zero authentic photos. Three distinct route types sharing
    # identical kicker + italic short-title hero structure is not customized
    # route art direction. Do NOT reject one or two pages or FI/SV translations.
    for class_name, where in repeated_decorated_hero_routes.items():
        if len(where) >= 3:
            pending.append({
                "category": "repeated_decorated_headline_hero",
                "issue": "Three or more different pages start with the same "
                         "classed text-only kicker + italic-title hero. "
                         "Give each visitor task an original first-fold "
                         "layout and real information hierarchy.",
                "template_classes": class_name,
                "routes": sorted(where),
            })
    if _photo_rich_original(research) and len(text_hero_routes) >= 3:
        pending.append({
            "category": "repeated_text_only_subpage_openings",
            "issue": "Photo-rich original business has three or more new routes "
                     "opening with short, text-only headline sections. Check "
                     "whether every page repeats the same oversized editorial "
                     "intro instead of showing relevant merchandise, staff, "
                     "services or booking information promptly.",
            "routes": sorted(text_hero_routes),
        })
    heading_repeats = sorted(((heading, sorted(where))
                              for heading, where in repeated_heading_routes.items()
                              if len(where) >= 3),
                             key=lambda row: (-len(row[1]), row[0]))
    if heading_repeats:
        pending.append({
            "category": "repeated_full_width_call_to_action_copy",
            "issue": "The same substantial section heading appears on three "
                     "or more routes. Verify that repeated CTA strips do not "
                     "make unrelated pages feel like one copied template.",
            "examples": [
                {"text": heading[:140], "routes": where}
                for heading, where in heading_repeats[:5]
            ],
        })
    return {
        "pending": pending,
        "observations": {
            "routes": len(routes),
            "distinct_main_image_assets": unique_count,
            "image_placements": image_mentions,
            "same_photo_on_3plus_routes": len(repetitions),
            "old_site_hotlinked_photo_assets": len(source_hotlinks),
            "text_only_first_sections": sorted(text_hero_routes),
        },
        "note": "Editorial review candidates, NOT pixel-level proof, copyright clearance or a numerical design score.",
    }

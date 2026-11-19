"""Authentic-media-first production art direction, not a ban on animation.

A real photograph, filmed product, client asset or intentionally text-first
composition beats an unsupported SVG/CSS counterfeit of a real-world object.
High-quality photo/video transitions, proven source 3D and useful interactive
diagrams remain allowed. Static inspection cannot certify motion quality.
"""
from __future__ import annotations

from pathlib import Path
import re
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

_BITMAP = (".jpg", ".jpeg", ".png", ".webp", ".avif", ".heic", ".gif")
_OBJECT_ART = re.compile(
    r"(?:^|[^a-z0-9])(?:tire|tyre|rengas|wheel|rim|spoke|gear|"
    r"engine|motor|car-drawing|vehicle-shape|blueprint|"
    r"technical-schematic|technical-illustration|fake-map|"
    r"road-outline|cargo-hatch)(?:$|[^a-z0-9])", re.I,
)
_DRAWN_CSS = re.compile(
    r"(?:conic-gradient|radial-gradient|border-radius\s*:\s*50%|"
    r"clip-path\s*:|box-shadow\s*:)", re.I,
)
_CSS_RULE = re.compile(r"([^{}]{1,250})\{([^{}]{1,1500})\}", re.S)
_PHOTO_URL = re.compile(r"url\([^)]*\.(?:jpe?g|png|webp|avif|gif)(?:[?#)'\" ]|$)", re.I)


def _painted_product_selector(css: str, nodes: list) -> bool:
    """Evidence that the *actual object* is CSS-painted, not a nearby fade."""
    selectors = set()
    for node in nodes:
        classes = node.get("class") or []
        selectors.update("." + label for label in classes if isinstance(label, str))
        if node.get("id"):
            selectors.add("#" + str(node["id"]))
        inline = str(node.get("style") or "")
        if _DRAWN_CSS.search(inline) and not _PHOTO_URL.search(inline):
            return True
    if not selectors:
        return False
    for rule in _CSS_RULE.finditer(css):
        selector, body = rule.group(1), rule.group(2)
        if (any(token in selector for token in selectors)
                and _DRAWN_CSS.search(body) and not _PHOTO_URL.search(body)):
            return True
    return False
_SVG_DIMS = re.compile(r"-?\d+(?:\.\d+)?")


def source_media_evidence(research: dict | None, media_items: list | None = None) -> dict:
    """Report original real-world media separately from actual usage rights.

    Research source candidates are observations, not permission to republish.
    media_items are staged assets with independently recorded rights status.
    """
    research = research if isinstance(research, dict) else {}
    observed, original_vector = set(), set()
    for page in (research.get("source_inventory") or {}).get("pages") or []:
        if not isinstance(page, dict):
            continue
        identity = page.get("source_identity") or {}
        photos = list(identity.get("original_content_photos") or [])
        photos += [x for x in (page.get("images") or []) if isinstance(x, dict)]
        for item in photos:
            if not isinstance(item, dict):
                continue
            src = str(item.get("src") or "").strip()
            if not src:
                continue
            extension = urlsplit(src).path.lower()
            if extension.endswith(_BITMAP):
                observed.add(src)
            elif extension.endswith(".svg"):
                original_vector.add(src)
        for src in identity.get("original_logo_candidates") or []:
            if isinstance(src, str):
                original_vector.add(src)
    usable, approved_vectors = set(), set()
    for item in media_items or []:
        if not isinstance(item, dict):
            continue
        src = str(item.get("src") or "").strip()
        status = str(item.get("rights_status") or "")
        if not src or status not in ("client_approved", "licensed", "internal_demo_only"):
            continue
        if urlsplit(src).path.lower().endswith(_BITMAP):
            usable.add(src)
        elif urlsplit(src).path.lower().endswith(".svg"):
            approved_vectors.add(src)
    return {
        "original_photo_candidate_count": len(observed),
        "staged_real_photo_count": len(usable),
        "original_vector_candidate_count": len(original_vector),
        "original_photos_are_not_licensed_by_observation": True,
        "original_photo_candidates": sorted(observed)[:25],
        "staged_photo_sources": sorted(usable)[:25],
        "observed_source_vectors": sorted(original_vector)[:25],
        "staged_vectors": sorted(approved_vectors)[:25],
        "default": "real_media_or_clean_typography_before_illustrated_facsimile",
        "animation_policy": "purposeful_photo_video_motion_allowed",
    }


def _first_section(html: str):
    soup = BeautifulSoup(html, "html.parser")
    main = soup.find("main")
    if main is None:
        return None
    return next((part for part in main.find_all(["section", "article"], recursive=False)), main)


def _big_svg(svg) -> bool:
    if svg.get("width") and re.fullmatch(r"\s*\d+(?:\.\d+)?(?:px)?\s*", str(svg["width"])):
        if float(re.findall(r"\d+(?:\.\d+)?", str(svg["width"]))[0]) <= 80:
            return False
    viewbox = _SVG_DIMS.findall(str(svg.get("viewbox") or ""))
    if len(viewbox) >= 4:
        return float(viewbox[2]) >= 180 and float(viewbox[3]) >= 150
    width = re.findall(r"\d+(?:\.\d+)?", str(svg.get("width") or ""))
    height = re.findall(r"\d+(?:\.\d+)?", str(svg.get("height") or ""))
    return bool(width and height and float(width[0]) >= 180 and float(height[0]) >= 150)


def _local_styles(html: str, site_root: Path | None, route: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    content = "\n".join(
        [el.get_text() for el in soup.find_all("style")]
        + [str(el.get("style") or "") for el in soup.select("[style]")])
    if site_root is not None:
        # Read only the generated site's own stylesheets, never public URLs.
        from urllib.parse import unquote
        root = Path(site_root).resolve()
        parent = (root / route).resolve().parent
        if parent.is_relative_to(root):
            for link in soup.select('link[rel~="stylesheet"][href]'):
                raw = str(link.get("href") or "")
                parsed = urlsplit(raw)
                if not parsed.path or parsed.scheme or parsed.netloc:
                    continue
                local = (parent / unquote(parsed.path)).resolve()
                if (local.is_relative_to(root) and local.is_file()
                        and local.suffix.lower() == ".css"
                        and local.stat().st_size < 400_000):
                    content += "\n" + local.read_text(encoding="utf-8")
    return content[:900_000]


def audit_hero_media(
    pages: dict[str, str],
    research: dict | None,
    *, site_root: Path | None = None,
    media_items: list | None = None,
) -> dict:
    """Specific, repairable false-product-illustration defects.

    All real-world-object drawings require human/screenshot scrutiny, but
    block only high-confidence *hero* substitutions. Does NOT enforce that
    every page include an image, nor reject genuine source vector brand marks,
    ordinary SVG icons, photo animation, video, or approved 3D files.
    """
    research = research if isinstance(research, dict) else {}
    strict = research.get("v8_visual_protocol") == "v8"
    evidence = source_media_evidence(research, media_items)
    approved_vectors = set(evidence["observed_source_vectors"] + evidence["staged_vectors"])
    blockers, review, observations = [], [], {}
    for route, html in (pages or {}).items():
        hero = _first_section(html)
        if hero is None:
            continue
        img = hero.select("img[src],picture img[src]")
        photos = [x for x in img
                  if urlsplit(str(x.get("src") or "")).path.lower().endswith(_BITMAP)]
        video = hero.select("video[src],video source[src]")
        # A website may have meaningful *actual* photography yet no licence.
        # Do not infer rights from the presence of <img> here.
        has_real_world_media = bool(photos or video)
        css = _local_styles(html, site_root, route)
        candidates = []
        for svg in hero.find_all("svg"):
            if not _big_svg(svg):
                continue
            label = " ".join([
                str(svg.get("class") or ""), str(svg.get("id") or ""),
                str(svg.get("aria-label") or ""), str(svg.parent.get("class") if svg.parent else ""),
                " ".join(str(x.get("class") or "") for x in svg.find_all(True)[:20])
            ])
            # Large custom scene art, generally not a company photograph.
            if _OBJECT_ART.search(label) or (
                    len(svg.find_all(["path", "ellipse", "circle", "polygon"])) >= 7
                    and not re.search(r"logo|brand|wordmark", label, re.I)):
                candidates.append("large_inline_object_scene")
        for item in img:
            src = str(item.get("src") or "")
            if urlsplit(src).path.lower().endswith(".svg") and src not in approved_vectors:
                text = " ".join([src, str(item.get("alt") or "")])
                if _OBJECT_ART.search(text):
                    candidates.append("unverified_svg_product_illustration")
        # Detect HTML/CSS-drawn wheel/rim/tire objects. No name-only guess:
        # also require painting geometry in CSS plus a rendered object node.
        object_nodes = [
            element for element in hero.find_all(True)
            if element.name not in ("svg", "path", "circle", "ellipse")
            and _OBJECT_ART.search(
                " ".join([str(element.get("id") or ""),
                          " ".join(element.get("class") or [])]))
        ]
        if object_nodes and _painted_product_selector(css, object_nodes):
            # With a genuine photo in the same fold, retain the screenshot
            # critic's right to accept a purposeful branded interaction, but
            # do not silently ignore an apparently drawn product overlay.
            candidates.append("css_drawn_real_world_object")
        candidates = sorted(set(candidates))
        observations[route] = {
            "first_section_real_photo_count": len(photos),
            "first_section_video_count": len(video),
            "illustration_substitution_patterns": candidates,
            "source_photo_candidate_count": evidence["original_photo_candidate_count"],
        }
        if not candidates:
            continue
        finding = {
            "route": route,
            "code": "fake_real_world_object_hero",
            "evidence": candidates,
            "repair": (
                "Remove the improvised SVG/CSS tire, wheel, gear or product scene. "
                "Use genuinely approved real company photos/video if available; "
                "otherwise build an elegant text-first hero and request real assets. "
                "Good motion on real images/video is welcome with reduced-motion "
                "fallback. Do NOT invent an image or pretend rights are verified."
            ),
        }
        if strict and not has_real_world_media:
            blockers.append(finding)
        else:
            review.append(finding)
    return {
        "protocol": "authentic-real-world-media-v1",
        "pass": not blockers,
        "blocking": blockers,
        "review_required": review,
        "media_evidence": evidence,
        "route_observations": observations,
        "real_motion_is_not_banned": True,
        "visual_quality_not_certified_by_static_check": True,
    }

"""Evidence-bound art direction and motion safety for every Kaurivo site.

The original business defines subject matter and brand constraints, not a ceiling
on tasteful visual depth. A static site may be excellent; an effect counter is
not an aesthetic score. Visual review and real-device smoothness remain pending
until independently demonstrated.
"""
from __future__ import annotations

import re
from bs4 import BeautifulSoup
from utils.source_experience import source_experience_brief

_CSS_MOTION = re.compile(r"@keyframes\b|\banimation(?:-name|-duration|-delay)?\s*:", re.I)
_CSS_DEPTH = re.compile(r"perspective\s*:|preserve-3d|translateZ\s*\(|rotate[XY]\s*\(|matrix3d\s*\(", re.I)
_CSS_REDUCED = re.compile(r"@media\s*\(\s*prefers-reduced-motion\s*:\s*reduce\s*\)", re.I)
_JS_TRACKING = re.compile(
    r'''(?:addEventListener\s*\(\s*['"](?:pointermove|mousemove|scroll)['"]|'''
    r'''\.on(?:pointermove|mousemove|scroll)\s*=|requestAnimationFrame\s*\()''', re.I,
)
_JS_REDUCED = re.compile(r"prefers-reduced-motion\s*:\s*reduce", re.I)

def visual_direction_plan(research: dict, creative: dict, architecture: dict) -> dict:
    """Create a specific PRE-BUILD design brief from an already validated choice.

    This creates no fabricated image, brand mark, animation, or licensing claim.
    The selected creative concept and source media are the ground truth.
    """
    selected = creative.get("selected") or {}
    required = ("concept", "business_reason", "source_anchor", "first_view",
                "image_strategy", "typography", "brand_continuity", "mobile_behavior")
    if not all(str(selected.get(k) or "").strip() for k in required):
        raise RuntimeError("Visual direction needs a verified, selected creative proposal.")
    source = source_experience_brief(research)
    paths = architecture.get("page_paths") or [
        x.get("path") for x in architecture.get("pages", []) if isinstance(x, dict)
    ]
    paths = [str(x) for x in paths if x]
    if not paths:
        raise RuntimeError("Visual direction requires a real multi-page architecture.")

    source_pages = (research.get("source_inventory") or {}).get("pages") or []
    images = set()
    for page in source_pages:
        for item in (page.get("source_identity") or {}).get("original_content_photos") or []:
            src = item.get("src") if isinstance(item, dict) else None
            if src:
                images.add(str(src))
    photo_rich = len(images) >= 3
    motion_budget = source.get("motion_budget", "undetermined")
    depth = (
        "Consider subtle source-photo parallax, light/material layering or "
        "pointer-aware depth only where the photographed work benefits; "
        "do not fabricate a 3D model of the product."
        if photo_rich else
        "Use authentic brand typography, composition, elevation and subtle "
        "surface lighting; do not invent a product photograph or a 3D asset."
    )
    return {
        "selected_concept": selected["concept"],
        "business_reason": selected["business_reason"],
        "source_anchor": selected["source_anchor"],
        "first_view": selected["first_view"],
        "image_strategy": selected["image_strategy"],
        "typography": selected["typography"],
        "brand_lock": selected["brand_continuity"],
        "route_tasks": paths,
        "per_route_rule": (
            "Give each route its own composition for its real customer task. "
            "Avoid repeating hero split, numbered cards, CTA strips and empty title bands."
        ),
        "depth_direction": depth,
        "motion_budget_from_source": motion_budget,
        "motion_decision": (
            "Propose at least one brand-relevant interaction or explain why "
            "the work is better served by restraint. Original motion is a baseline, "
            "not a rule against improving a restrained original."
        ),
        "motion_safety": (
            "Progressive enhancement: static readable fallback, keyboard and touch "
            "operation, CSS reduced-motion override and JS reduced-motion check "
            "for pointer/scroll/RAF-driven effects. Prefer transform/opacity, "
            "never intercept scrolling, and assess performance at 320/390/768/1440px."
        ),
        "mobile_behavior": selected["mobile_behavior"],
        "media_rights": (
            "Original images are reference evidence, not a redistribution licence. "
            "Do not claim permission or replace original business imagery with fabricated work."
        ),
        "review_required": (
            "Compare actual full-page source/new renders, including mobile; judge "
            "depth, materiality, visual rhythm, legibility, smoothness and purpose. "
            "No automated effect count or stylistic self-score grants premium approval."
        ),
    }


def audit_visual_motion(
    pages: dict[str, str],
    research: dict | None = None,
    *,
    css_text: str = "",
    js_text: str = "",
    assets_complete: bool = False,
) -> dict:
    """Reject objectively unsafe motion; flag subjective visual work for review.

    Incomplete asset reads cannot prove an effect is absent. External styles and
    JS may load dynamically; real browser and independent evidence remain needed.
    """
    inline_css, inline_js, linked_assets = [], [], []
    for route, html in (pages or {}).items():
        soup = BeautifulSoup(html or "", "html.parser")
        inline_css.extend(tag.get_text() for tag in soup.find_all("style"))
        inline_css.extend(str(tag.get("style") or "") for tag in soup.find_all(style=True))
        inline_js.extend(tag.get_text() for tag in soup.find_all("script") if not tag.get("src"))
        linked_assets.extend(
            f"{route}: {tag.get('href') or tag.get('src')}"
            for tag in soup.select('link[rel~="stylesheet"][href],script[src]')
        )
    css = "\n".join([*inline_css, css_text or ""])
    js = "\n".join([*inline_js, js_text or ""])
    animated = bool(_CSS_MOTION.search(css))
    depth = bool(_CSS_DEPTH.search(css))
    scripted = bool(_JS_TRACKING.search(js))
    css_reduced = bool(_CSS_REDUCED.search(css))
    js_reduced = bool(_JS_REDUCED.search(js))
    blockers, pending = [], []
    if animated and not css_reduced:
        issue = "CSS keyframe/animation motion has no prefers-reduced-motion: reduce override."
        (blockers if assets_complete or not linked_assets else pending).append(issue)
    if scripted and not js_reduced:
        issue = "Pointer/scroll/requestAnimationFrame motion has no JS reduced-motion guard."
        (blockers if assets_complete or not linked_assets else pending).append(issue)
    if linked_assets and not assets_complete:
        pending.append(
            "External styles/scripts require full asset inspection and live-browser "
            "animation checks; HTML-only QA cannot certify motion safety."
        )
    if depth or animated or scripted:
        pending.append(
            "Visual depth and motion must be checked in a real browser for mobile "
            "smoothness, focus/touch support, keyboard usability, contrast and "
            "authenticity to the client's product."
        )
    else:
        pending.append(
            "No proven expressive depth or purposeful motion in inspected assets. "
            "Independent reviewer must check whether deliberate restraint or a "
            "more distinctive business-specific composition is appropriate."
        )
    return {
        "blocking": blockers, "pending": pending,
        "observations": {
            "css_animation": animated, "css_depth": depth,
            "js_pointer_scroll_or_raf": scripted,
            "css_reduced_motion": css_reduced,
            "js_reduced_motion": js_reduced,
            "linked_assets_seen": sorted(set(linked_assets)),
            "assets_complete": bool(assets_complete),
        },
        "note": "Static source checks only; no fabricated independent score.",
    }

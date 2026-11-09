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

# A high-confidence artificial photo spotlight: unlike an ordinary background
# gradient, this puts a movable or screen-blended radial glow on a photo overlay.
# Exact visual quality still requires source-versus-build browser comparison.
_PHOTO_OVERLAY_RULE = re.compile(r"(?P<selector>[^{}]+)\{(?P<body>[^{}]*)\}", re.I | re.S)
_DYNAMIC_LIGHT_POSITION = re.compile(
    r"var\(\s*--(?:px|py|mx|my|mouse-[xy]|pointer-[xy]|cursor-[xy]|glow-[xy])\b", re.I
)

def _synthetic_photo_spotlights(css: str, pages: dict[str, str]) -> list[str]:
    has_photography = any(
        BeautifulSoup(html or "", "html.parser").select_one("main img, main picture img, .hero img")
        for html in (pages or {}).values()
    )
    if not has_photography:
        return []
    flagged = []
    for rule in _PHOTO_OVERLAY_RULE.finditer(css):
        selector, declarations = rule.group("selector"), rule.group("body")
        if "radial-gradient" not in declarations.casefold():
            continue
        if not re.search(r"(?:::{0,1}(?:after|before)\b|\boverlay\b)", selector, re.I):
            continue
        blended = bool(re.search(r"mix-blend-mode\s*:\s*(?:screen|lighten|color-dodge)", declarations, re.I))
        following = bool(_DYNAMIC_LIGHT_POSITION.search(declarations))
        if blended or following:
            flagged.append(selector.strip()[:140])
    return sorted(set(flagged))


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
        "Let the actual subject, material, existing light and meaningful crop "
        "create visual depth. Consider optional very small photo translation "
        "or purposeful perspective only if it helps show the real work. "
        "Never add pointer-following radial light, screen-blend halos or "
        "fake light reflections above genuine photography. Do not fabricate "
        "a 3D model of the client's product."
        if photo_rich else
        "Create company-specific rhythm and depth using authentic typography, "
        "real materials, balanced space and carefully chosen elevation. "
        "Never invent a photograph, client product, or gratuitous 3D gimmick."
    )
    return {
        "selected_concept": selected["concept"],
        "business_reason": selected["business_reason"],
        "source_anchor": selected["source_anchor"],
        "first_view": selected["first_view"],
        "image_strategy": selected["image_strategy"],
        "typography": selected["typography"],
        "brand_lock": selected["brand_continuity"],
        "observed_brand_signatures": research.get("brand_signature_plan") or {
            "status": "original_visual_signature_unknown",
            "note": "Do not invent geometry, colors or logo; collect source evidence."
        },
        "source_media_priority": (
            "Give approved, genuine project photos and source brand motifs "
            "priority over anonymous gradient blocks. A stand-in material "
            "graphic is NOT the client's finished work."
        ),
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
    spotlights = _synthetic_photo_spotlights(css, pages)
    if spotlights:
        problem = ("Synthetic photo spotlight risk: radial halo overlay on real image "
                   "in " + ", ".join(spotlights[:4]) +
                   ". Remove the pointer-following/screen-blend light and preserve "
                   "authentic photographic light. Any exceptional client-authorized "
                   "treatment needs independent, source-based visual review.")
        # The offending CSS is actually present in the inspected source.
        # Unrelated uninspected third-party assets must not downgrade this
        # observed high-confidence flaw from blocker to pending.
        blockers.append(problem)
    if animated and not css_reduced:
        issue = "CSS keyframe/animation motion has no prefers-reduced-motion: reduce override."
        (blockers if assets_complete else pending).append(issue)
    if scripted and not js_reduced:
        issue = "Pointer/scroll/requestAnimationFrame motion has no JS reduced-motion guard."
        (blockers if assets_complete else pending).append(issue)
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
            "synthetic_photo_spotlights": spotlights,
        },
        "note": "Static source checks only; no fabricated independent score.",
    }

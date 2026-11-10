"""Known premium-experience regressions: objective fail-closed preflight.

This gate catches INVALID interaction semantics (decorative image handle that
cannot be dragged), empty CSS perspective masquerading as textile 3D, and
missing controls. It does not compute aesthetic scores; visual rhythm, image
alignment and real material quality require independent human/AI inspection of
the exact deployed build with source side-by-side evidence.
"""
from __future__ import annotations
import re
from bs4 import BeautifulSoup


def audit_premium_experience(
    pages: dict[str, str], *, css_text: str = "", js_text: str = "",
) -> dict:
    if not isinstance(pages, dict):
        raise TypeError("pages must be a route-to-HTML dict")
    blocking: list[dict] = []
    review_required: list[dict] = []
    observations: dict = {
        "comparison_widgets": 0,
        "material_scenes": 0,
        "text_first_sections": {},
        "requires_independent_visual_review": True,
    }
    js = str(js_text or "")
    css = str(css_text or "")
    js_has_direct_drag = (
        bool(re.search(r"""addEventListener\s*\(\s*['"]pointerdown['"]""", js))
        and bool(re.search(r"""addEventListener\s*\(\s*['"]pointermove['"]""", js))
        and ("--split" in js or "--position" in js)
        and (".comparison" in js or ".before-after" in js)
        and "setPointerCapture" in js
    )
    for route, html in pages.items():
        soup = BeautifulSoup(str(html), "html.parser")
        rhythm = []
        for section in soup.select("main section"):
            heading = section.select_one("h2,h3")
            if heading:
                rhythm.append({
                    "heading": heading.get_text(" ", strip=True)[:70],
                    "class": " ".join(section.get("class") or [])[:100],
                    "text_first": not bool(section.select_one("img,video,canvas,picture")),
                    "eyebrow": bool(section.select_one(".eyebrow")),
                })
        observations["text_first_sections"][route] = [
            item for item in rhythm if item["text_first"]
        ]
        repeated = sum(
            item["text_first"] and item["eyebrow"] for item in rhythm
        )
        if repeated >= 3:
            review_required.append({
                "kind": "repeating_full_width_text_band_rhythm",
                "route": route,
                "count": repeated,
                "reason": "Compare actual visual sections against source and other client websites.",
            })
        for widget in soup.select(".comparison, .before-after"):
            observations["comparison_widgets"] += 1
            canvas = widget.select_one(".comparison-canvas, .before-after-canvas")
            slider = widget.select_one('input[type="range"]')
            photos = (
                canvas.select("img") if canvas is not None else []
            )
            if canvas is None or len(photos) < 2:
                blocking.append({
                    "kind": "before_after_missing_real_pair",
                    "route": route,
                    "reason": "A real two-image visual comparison is required.",
                })
            if slider is None or not slider.get("aria-label"):
                blocking.append({
                    "kind": "before_after_missing_keyboard_control",
                    "route": route,
                    "reason": "Provide a real labelled keyboard-operable range control.",
                })
            # A range input inside the visual viewport can be a real draggable
            # image control. A detached slider below the picture with a painted
            # pseudo-handle does NOT meet the source's direct-drag semantics.
            has_overlay_input = bool(
                canvas is not None
                and canvas.select_one('input[type="range"]') is not None
            )
            if canvas is not None and not has_overlay_input and not js_has_direct_drag:
                blocking.append({
                    "kind": "comparison_handle_not_directly_draggable",
                    "route": route,
                    "reason": "Image itself must accept mouse/touch drag. "
                              "A separate slider below the image and CSS-only "
                              "handle are not feature-equivalent.",
                })
            review_required.append({
                "kind": "before_after_visual_alignment_unproven",
                "route": route,
                "reason": "Source vs new image geometry and 0/25/50/75/100 states "
                          "must be inspected visually, not inferred from input.value.",
            })
        for material in soup.select(
            ".fabric-rack, [data-material-3d], .material-scene"
        ):
            observations["material_scenes"] += 1
            material_images = material.select("img,picture,video,canvas,model-viewer")
            has_real_texture_css = bool(
                re.search(
                    r"""(?:\.fabric-rack|\.swatch|\.material-scene)[^{]*\{[^}]*"""
                    r"""(?:background-image\s*:\s*url\(|background\s*:\s*url\()""",
                    css,
                    flags=re.I | re.S,
                )
            )
            has_3d_model = bool(
                soup.select_one("model-viewer")
                or re.search(r"\.(?:glb|gltf)(?:[?'\"\s]|$)", html, re.I)
                or material.select_one("canvas")
            )
            has_fake_perspective = bool(
                "perspective" in css and material.select(".swatch")
            )
            if (has_fake_perspective and not material_images
                    and not has_real_texture_css and not has_3d_model):
                blocking.append({
                    "kind": "flat_css_cards_pretend_to_be_fabric_3d",
                    "route": route,
                    "reason": "Untextured flat color swatches tilted in CSS "
                              "cannot be certified as credible textile/material 3D. "
                              "Replace with authentic photographic detail or a "
                              "real licensed model; or remove the claimed depth effect.",
                })
            review_required.append({
                "kind": "material_realism_unverified",
                "route": route,
                "reason": "Inspect fibers, folds, light, roughness, shape, thickness "
                          "and mobile fallback in true screenshots/video.",
            })
    review_required.append({
        "kind": "source_vs_redesign_visual_quality_unverified",
        "reason": "A source site that already has a designed experience is the "
                  "visual floor. Compare first-fold, header, section rhythm "
                  "and interaction quality side by side at mobile and desktop.",
    })
    return {
        "blocking": blocking,
        "review_required": review_required,
        "observations": observations,
        "status": "HOLD" if blocking else "PENDING_INDEPENDENT_VISUAL_REVIEW",
        "note": "Static success NEVER certifies premium quality or source parity.",
    }

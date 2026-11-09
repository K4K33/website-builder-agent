"""Preserve observed client visual signatures before picking art direction.

Only source-observed marks, media, patterns and motion are recorded. A logo
URL is identity evidence, never copyright permission or proof that a redesign
visually matches. Browser and independent review remain separate.
"""
from __future__ import annotations


def derive_brand_signature_plan(research: dict) -> dict:
    pages = (research.get("source_inventory") or {}).get("pages") or []
    if research.get("research_mode") == "verified_no_website":
        return {"status": "no_original_site", "signatures": [],
                "note": "Do not invent a visual brand; use verified business facts."}
    signatures, found = [], set()

    def add(kind, url, description, implementation):
        key = (kind, url, description)
        if key not in found and url and description:
            found.add(key)
            signatures.append({
                "kind": kind, "source_url": url,
                "description": description,
                "implementation": implementation,
                "rights_status": "not_granted_by_observation",
            })

    for page in pages:
        if not isinstance(page, dict):
            continue
        url = str(page.get("url") or "")
        identity = page.get("source_identity") or {}
        for logo in identity.get("original_logo_candidates") or []:
            src = str(logo.get("src") or logo.get("url") or "") if isinstance(logo, dict) else str(logo)
            if src:
                add("original_logo", url,
                    "Actual source logo candidate: " + src[:220],
                    "Use exact client-approved brand mark rather than an invented monogram.")
        for wordmark in identity.get("original_header_wordmark_candidates") or []:
            value = str(wordmark).strip()
            if value:
                add("original_wordmark", url,
                    "Source header wordmark: " + value[:160],
                    "Preserve lettering, brand hierarchy and recognizable original lock-up.")
        theme = str(identity.get("theme_color") or "").strip()
        if theme:
            add("observed_theme_color", url,
                "Source-observed theme color: " + theme[:60],
                "Respect original palette energy and cross-page hierarchy, not just a related hue.")
        source_visual = identity.get("source_experience") or {}
        backgrounds = source_visual.get("observed_textured_backgrounds") or []
        for asset in backgrounds:
            if asset:
                add("original_background_texture", url,
                    "Observed source background texture: " + str(asset)[:220],
                    "Preserve recognizable background/motif with a permitted asset or verified reconstruction.")
        if source_visual.get("observed_3d") is True:
            add("source_3d", url, "Observed 3D elements on the original source page",
                "Do not reduce true source depth to flat blocks; inspect real browser playback.")
        if source_visual.get("observed_css_or_js_animation") is True:
            add("source_motion", url, "Original page contained observed CSS/JS motion",
                "Document the meaningful animated visual behavior and preserve or purposefully improve it.")
    original_browser = research.get("original_experience_profile") or {}
    features = original_browser.get("features") or {}
    if pages:
        url = str(pages[0].get("url") or "")
        if (features.get("textured_background") or {}).get("present") is True:
            add("browser_observed_texture", url,
                "Browser-observed distinctive textured or geometric background",
                "Inspect source screenshot and preserve geometric motif, position and visual mood.")
    return {
        "status": "source_inventory_recorded_browser_signoff_pending" if signatures
                  else "source_visual_signature_unverified",
        "signatures": signatures,
        "note": "Independent source/new browser image comparison and rights are mandatory.",
    }

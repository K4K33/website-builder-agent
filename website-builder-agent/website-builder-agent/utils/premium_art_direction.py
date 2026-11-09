"""Evidence-aware premium art-direction checks for every newly researched client.

This module cannot tell whether a website is 'beautiful'. It blocks repeatable
source-relative mistakes and leaves actual aesthetic judgment to fresh,
independent reviews of EVERY rendered page. No AI scoring, new dependencies,
paid API requests, photo fabrication or fixed industry templates.
"""
from __future__ import annotations

import re
from collections import Counter
from bs4 import BeautifulSoup


_FILLER = re.compile(
    r"(?:graafinen materiaalitutkielma|abstrakti graafinen sommitelma|"
    r"graafinen tapettipinta|graphic material study|abstract graphic composition|"
    r"placeholder image|esimerkkikuva|kuvapaikka|coming soon image)",
    re.I,
)
_GENERIC_VISUAL_CLASSES = {
    "surface-abstract", "abstract-placeholder", "generic-illustration",
    "decorative-filler", "stock-placeholder", "filler-art",
}
_FORM_KEYS = ("original_form", "contact_form", "inquiry_form", "quote_form")


def observed_original_photos(research: dict) -> set[str]:
    photos: set[str] = set()
    for page in (research.get("source_inventory") or {}).get("pages") or []:
        if not isinstance(page, dict):
            continue
        for item in (page.get("source_identity") or {}).get("original_content_photos") or []:
            src = item.get("src") if isinstance(item, dict) else None
            if isinstance(src, str) and src.strip():
                photos.add(src.strip())
        for item in page.get("images") or []:
            if not isinstance(item, dict):
                continue
            src = item.get("src")
            if isinstance(src, str) and src.strip():
                photos.add(src.strip())
    return photos


def source_contact_form_evidence(research: dict) -> dict:
    """Only actual observed source form fields or an explicit observed flag.

    A generic source mention of 'contact us' does not prove a form existed.
    This evidence detects the recurrent mailto downgrade without fabricating
    back-end completion or silently accepting a link to the old site.
    """
    observed = []
    for page in (research.get("source_inventory") or {}).get("pages") or []:
        if not isinstance(page, dict):
            continue
        for form in page.get("forms") or []:
            if not isinstance(form, dict):
                continue
            fields = form.get("fields") or []
            kinds = {str(f.get("type") or "").lower() for f in fields if isinstance(f, dict)}
            if "email" in kinds and ("textarea" in kinds or "message" in kinds):
                observed.append(str(page.get("url") or ""))
        blocks = page.get("source_content_blocks") or {}
        if any(blocks.get(key) is True for key in _FORM_KEYS):
            observed.append(str(page.get("url") or ""))
    return {"present": bool(observed), "source_urls": sorted(set(observed))}


def audit_premium_art_direction(pages: dict[str, str], research: dict) -> dict:
    """Return deterministic blockers and separate pending visual judgments.

    Checks are stricter for source-rich v2 projects. Old static demo QA isn't
    retrospectively declared an aesthetic failure. Neither a CSS animation
    count nor image count is used as a premium score.
    """
    v2 = research.get("premium_visual_protocol") == "v2"
    blockers, pending, route_evidence = [], [], {}
    source_images = observed_original_photos(research)
    photo_rich = len(source_images) >= 3
    source_form = source_contact_form_evidence(research)
    seen_images = Counter()
    real_form_routes = []
    for route, html in sorted((pages or {}).items()):
        soup = BeautifulSoup(html or "", "html.parser")
        main = soup.find("main") or soup
        photos = [img for img in main.find_all("img") if str(img.get("src") or "").strip()]
        for img in photos:
            seen_images[str(img.get("src"))] += 1
        filler = []
        for element in main.find_all(True):
            if element.name not in ("div", "figure", "section", "aside", "figcaption", "img"):
                continue
            classes = set(element.get("class") or [])
            caption = " ".join((str(element.get("alt") or ""),
                                str(element.get("aria-label") or ""),
                                element.get_text(" ", strip=True)[:180] if element.name in
                                ("figcaption", "figure") else ""))
            if _FILLER.search(caption) or (classes & _GENERIC_VISUAL_CLASSES):
                filler.append({"element": element.name, "description": caption[:110],
                               "classes": sorted(classes & _GENERIC_VISUAL_CLASSES)})
        form_count = sum(
            bool(form.select_one('input[type="email"]')) and
            bool(form.find("textarea"))
            for form in main.find_all("form")
        )
        if form_count:
            real_form_routes.append(route)
        route_evidence[route] = {
            "real_img_elements": len(photos), "filler_candidates": filler[:6],
            "form_markup": form_count,
            "real_product_or_project_photos": [
                str(img.get("src"))[:150] for img in photos[:8]
            ],
            "note": "Image contents, licensing and actual browser appearance still require review.",
        }
        if filler and photo_rich and v2:
            blockers.append(
                f"{route}: generic decorative/filler panel substitutes for sourced client work; "
                "choose a specific licensed photograph or record an independently approved "
                "brand-signature exception."
            )
        elif filler:
            pending.append(
                f"{route}: review decorative panels against the client's original work and brand."
            )
    if source_form["present"] and v2 and not real_form_routes:
        blockers.append(
            "Original client site has an observed inquiry/contact form, "
            "but redesign has no real email+message form. A mailto draft or "
            "link to the old website is not equivalent lead capture."
        )
    if source_form["present"] and real_form_routes:
        pending.append(
            "Form markup is present, but end-to-end POST, delivery, privacy, "
            "validation and error/success states still need live browser tests."
        )
    if photo_rich and v2:
        repeated = [src for src, count in seen_images.items() if count >= 3]
        if repeated and len(pages) >= 3:
            pending.append(
                "Identical client photographs reused in 3+ page image elements; "
                "verify each is purpose-specific, not a substitute for original variety."
            )
    if v2:
        plan = research.get("brand_signature_plan") or {}
        signatures = plan.get("signatures") if isinstance(plan, dict) else None
        if (not isinstance(signatures, list) or not signatures) and research.get("research_mode") != "verified_no_website":
            pending.append(
                "No source-anchored visual signature inventory: examine original "
                "logo AND background patterns, palette mood, material textures, "
                "photographic style and typography before approving art direction."
            )
        else:
            for item in signatures:
                if not isinstance(item, dict) or not (
                    str(item.get("source_url") or "").strip() and
                    str(item.get("description") or "").strip() and
                    str(item.get("implementation") or "").strip()
                ):
                    blockers.append("Brand-signature plan includes an unsourced or unmapped item.")
                    break
            pending.append(
                "Review original/new screenshot pairs to verify every inventoried "
                "brand signature truly appears, rather than trusting textual mapping."
            )
        pending.append(
            "Every route requires independent original/new desktop and mobile "
            "visual assessment; technical QA and a strong home page cannot "
            "certify the service, portfolio, person or contact pages."
        )
    return {
        "blocking": blockers, "pending": pending,
        "source_photos": len(source_images),
        "source_contact_form": source_form,
        "route_evidence": route_evidence,
        "note": "Deterministic guardrails only, not a visual or premium score.",
    }

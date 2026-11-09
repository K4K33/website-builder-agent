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
    r"placeholder image|kuvapaikka|coming soon image)",
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
        # A generic source <img> list may include logos, icons and partner marks.
        # Do NOT count those as photographic client work and block legitimate
        # geometric branding merely because a site had several icon assets.
        # Content photographs must be inventoried by the source-identity step.
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


def audit_premium_art_direction(pages: dict[str, str], research: dict, *, company: dict | None = None) -> dict:
    """Return deterministic blockers and separate pending visual judgments.

    Checks are stricter for source-rich v2 projects. Old static demo QA isn't
    retrospectively declared an aesthetic failure. Neither a CSS animation
    count nor image count is used as a premium score.
    """
    v2 = research.get("premium_visual_protocol") == "v2"
    company = company or {}
    from utils.premium_quality_gate import (
        verify_independent_premium_reviews, site_digest,
    )
    from utils.content_parity import source_inventory_sha256
    build_sha = site_digest(pages)
    source_sha = source_inventory_sha256(research.get("source_inventory") or {})
    premium_approved = (
        verify_independent_premium_reviews(
            research.get("premium_independent_reviews"), pages, research
        )["pass"] if v2 else False
    )
    visual_signature_review = research.get("brand_signature_review") or {}
    signature_approved = bool(
        visual_signature_review.get("approved") is True
        and visual_signature_review.get("reviewer_kind") == "independent_human"
        and visual_signature_review.get("build_sha256") == build_sha
        and visual_signature_review.get("source_sha256") == source_sha
        and visual_signature_review.get("critical_issues") == []
        and str(visual_signature_review.get("evidence_reference") or "").strip()
    )
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
            bool(form.find("textarea")) and
            str(form.get("method") or "").lower() == "post" and
            not str(form.get("action") or "").lower().startswith(
                ("mailto:", "javascript:", "data:")
            )
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
        # A visibly identified, real third-party sample photograph is not
        # the same as an empty decorative placeholder. Ethical stock-photo
        # disclosure ("esimerkkikuva") is REQUIRED and must not itself be a
        # blocker. Actual rights/subject authenticity remain separate gates.
        disclosed_samples = [
            img for img in photos
            if "esimerkkikuva" in str(img.get("alt") or "").casefold()
            or "illustrative" in str(img.get("alt") or "").casefold()
        ]
        if disclosed_samples:
            pending.append(
                f"{route}: disclosed licensed-example photographs require "
                "rights and subject-context verification before client release."
            )
        if filler and photo_rich and v2:
            blockers.append(
                f"{route}: generic decorative/filler panel substitutes for sourced client work; "
                "choose a specific licensed photograph or remove generic filler."
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
    if (source_form["present"] and real_form_routes
            and (company.get("release_evidence") or {}).get("real_lead_delivery_verified") is not True):
        pending.append(
            "Form markup is present, but end-to-end POST, delivery, privacy, "
            "validation and error/success states still need live browser tests."
        )
    if photo_rich and v2:
        repeated = [src for src, count in seen_images.items() if count >= 3]
        photo_review = research.get("photo_role_review") or {}
        photo_reviewed = (
            photo_review.get("approved") is True
            and photo_review.get("build_sha256") == build_sha
            and photo_review.get("source_sha256") == source_sha
            and photo_review.get("reviewer_kind") == "independent_human"
        )
        if repeated and len(pages) >= 3 and not photo_reviewed:
            pending.append(
                "Identical client photographs reused in 3+ page image elements; "
                "verify each is purpose-specific, not a substitute for original variety."
            )
    if v2:
        plan = research.get("brand_signature_plan") or {}
        signatures = plan.get("signatures") if isinstance(plan, dict) else None
        if not isinstance(signatures, list) or not signatures:
            if research.get("research_mode") != "verified_no_website":
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
            if not signature_approved:
                pending.append(
                    "Review original/new screenshot pairs to verify every inventoried "
                    "brand signature truly appears, rather than trusting textual mapping."
                )
        if not premium_approved:
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

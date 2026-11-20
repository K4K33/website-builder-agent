"""Six questions every Kaurivo build must answer BEFORE any page is authored.

1. signature_moment  - the ONE memorable moment, and the technique that powers it
2. assets            - which real material exists (photos, video, 3D model)
3. brand_feel        - the brand's feel and the 2-3 reference sites
4. primary_action    - the one thing a visitor should do (call, book, email)
5. performance       - what the mobile page may cost to load
6. verified_facts    - which facts are verified; nothing else may be written

Derived deterministically from the validated research (no AI call, free).
The signature technique is chosen from the material that actually exists:
the reference sites look premium because of real video, real 3D models and
real photography, so a hand-coded procedural "3D" stand-in is forbidden.
"""
from __future__ import annotations

import re
from urllib.parse import urljoin, urlsplit

PROTOCOL = "kaurivo-pre-build-brief-v1"

_NOT_PHOTO = re.compile(
    r"logo|icon|favicon|sprite|flag|badge|avatar|pixel|spacer|blank|"
    r"placeholder|loader|arrow|social|facebook|instagram|linkedin|twitter|"
    r"whatsapp|youtube|tiktok|payment|visa|mastercard|klarna|cookie", re.I)
_PHOTO_EXT = re.compile(r"\.(?:jpe?g|png|webp|avif)$", re.I)
_VIDEO_EXT = re.compile(r"\.(?:mp4|webm|mov)$", re.I)
_MODEL_EXT = re.compile(r"\.(?:glb|gltf|usdz)$", re.I)

# Technique -> (minimum material, implementation note). Ordered by impact.
TECHNIQUES = {
    "video_scrub": "Signature hero engine (data-kaurivo-scrub): the company's own "
                   "video is drawn frame by frame as the visitor scrolls; poster first.",
    "product_3d": "Company's own GLB/GLTF model in Three.js with an HDR "
                  "environment; rotates with scroll or pointer; poster fallback.",
    "photo_sequence_scrub": "Signature hero engine (data-kaurivo-scrub): poster plus "
                            "up to 3 more real work photos in story order; the builder "
                            "renders frames and plays them with scroll.",
    "cinematic_photo_scroll": "Signature hero engine (data-kaurivo-scrub) with one strong "
                              "real photo; the builder renders a slow camera move.",
    "typographic_statement": "No usable photography: the headline itself is the "
                             "signature (variable-font weight/width driven by scroll).",
}

FORBIDDEN = (
    "procedural or hand-coded 3D objects that imitate the company's product, "
    "building or premises",
    "a second competing signature effect",
    "fade-and-slide-up entrance on every section",
    "stock, AI-generated or other companies' images presented as the company's",
)

PERFORMANCE_BUDGET = {
    "first_view_bytes_max": 400_000,
    "hero_total_bytes_max_mobile": 2_500_000,
    "scrub_frames_max_mobile": 90,
    "scrub_frames_max_desktop": 150,
    "javascript_bytes_max": 150_000,
    "device_pixel_ratio_cap": 2,
    "required": [
        "poster image visible before any script runs",
        "prefers-reduced-motion shows the poster and all text without motion",
        "no horizontal scroll at 360px width",
        "primary action reachable without scrolling the pinned section on mobile",
    ],
}


def _text(value) -> str:
    return str(value or "").strip()


def _pages(research: dict) -> list[dict]:
    pages = (research.get("source_inventory") or {}).get("pages") or []
    return [p for p in pages if isinstance(p, dict)]


def _media_inventory(research: dict) -> dict:
    photos, videos, models = [], [], []
    seen = set()
    for page in _pages(research):
        base = _text(page.get("url"))
        candidates = []
        for image in page.get("images") or []:
            if isinstance(image, dict):
                candidates.append((_text(image.get("src")), _text(image.get("alt"))))
        for link in page.get("links") or []:
            if isinstance(link, dict):
                candidates.append((_text(link.get("href")), _text(link.get("text"))))
        for src, label in candidates:
            if not src or src.startswith("data:"):
                continue
            full = urljoin(base, src).split("#")[0]
            if full in seen or urlsplit(full).scheme not in ("http", "https"):
                continue
            path = urlsplit(full).path
            if _VIDEO_EXT.search(path):
                seen.add(full); videos.append(full)
            elif _MODEL_EXT.search(path):
                seen.add(full); models.append(full)
            elif _PHOTO_EXT.search(path) and not (_NOT_PHOTO.search(path) or _NOT_PHOTO.search(label)):
                seen.add(full); photos.append(full)
    return {"photos": photos, "videos": videos, "models_3d": models}


def _choose_technique(assets: dict) -> str:
    if assets["videos"]:
        return "video_scrub"
    if assets["models_3d"]:
        return "product_3d"
    if len(assets["photos"]) >= 3:
        return "photo_sequence_scrub"
    if assets["photos"]:
        return "cinematic_photo_scroll"
    return "typographic_statement"


def _selected_direction(research: dict) -> dict:
    directions = research.get("creative_directions")
    choice = research.get("creative_selection") or {}
    selected = _text(choice.get("selected_id")).casefold()
    if isinstance(directions, list):
        for direction in directions:
            if isinstance(direction, dict) and _text(direction.get("id")).casefold() == selected:
                return direction
    return {}


def _references(research: dict) -> list[str]:
    urls = []
    records = list(research.get("reference_comparison") or []) + list(research.get("design_benchmark") or [])
    for record in records:
        if isinstance(record, dict):
            url = _text(record.get("url"))
            if url.startswith("https://") and url not in urls:
                urls.append(url)
    return urls[:3]


def _contact(facts: dict) -> dict:
    contact = facts.get("contact") if isinstance(facts.get("contact"), dict) else {}
    return {key: _text(contact.get(key) or facts.get("contact_" + key))
            for key in ("phone", "email", "address")}


def _primary_action(research: dict) -> dict:
    for journey in research.get("primary_user_journeys") or []:
        href = _text(journey.get("destination") or journey.get("href")) if isinstance(journey, dict) else ""
        if href:
            return {"kind": _text(journey.get("kind")), "href": href,
                    "label": _text(journey.get("label")),
                    "evidence": _text(journey.get("source_url"))}
    contact = _contact(research.get("company_facts") or {})
    phone = "".join(ch for ch in _text(contact.get("phone")) if ch.isdigit() or ch == "+")
    if len(phone) >= 6:
        return {"kind": "phone", "href": "tel:" + phone, "label": "",
                "evidence": "verified company_facts"}
    email = _text(contact.get("email"))
    if "@" in email:
        return {"kind": "email", "href": "mailto:" + email, "label": "",
                "evidence": "verified company_facts"}
    return {}


def _verified_facts(research: dict) -> dict:
    facts = research.get("company_facts") or {}
    contact = _contact(facts)
    offering = research.get("primary_offering_evidence") or {}
    return {
        "name": _text(facts.get("name")),
        "services": [s for s in (facts.get("services") or []) if isinstance(s, str) and s.strip()][:12],
        "location": _text(facts.get("location")),
        "contact": {k: v for k, v in contact.items() if v},
        "primary_offering_quote": _text(offering.get("quote")),
        "rule": "Only these facts and verbatim source text may appear as claims. "
                "Missing information stays missing; it is never invented.",
    }


def derive_pre_build_brief(research: dict, staged_media: list | None = None) -> dict:
    """staged_media: the files a page may actually use (concept/build stage).

    Observed source photos prove material exists; only staged files can be
    placed on a page, so when they are known they decide the technique.
    """
    research = research if isinstance(research, dict) else {}
    assets = _media_inventory(research)
    usable = dict(assets)
    if staged_media is not None:
        staged = [m for m in staged_media if isinstance(m, dict) and m.get("src")]
        usable["photos"] = [m["src"] for m in staged
                            if not _VIDEO_EXT.search(str(m["src"])) and not _MODEL_EXT.search(str(m["src"]))]
        usable["videos"] = [m["src"] for m in staged if _VIDEO_EXT.search(str(m["src"]))]
        usable["models_3d"] = [m["src"] for m in staged if _MODEL_EXT.search(str(m["src"]))]
    technique = _choose_technique(usable)
    direction = _selected_direction(research)
    identity = research.get("v8_identity_boundaries") or {}
    references = _references(research)
    action = _primary_action(research)
    facts = _verified_facts(research)
    brief = {
        "protocol": PROTOCOL,
        "q1_signature_moment": {
            "technique": technique,
            "implementation": TECHNIQUES[technique],
            "moment": _text(direction.get("first_view")),
            "why": _text(direction.get("business_reason")),
            "forbidden": list(FORBIDDEN),
        },
        "q2_assets": {
            "real_photos": len(assets["photos"]),
            "usable_on_page": {k: len(v) for k, v in usable.items()},
            "photo_urls": assets["photos"][:12],
            "videos": assets["videos"][:3],
            "models_3d": assets["models_3d"][:3],
            "generation_allowed": False,
            "rule": "Only the company's own material. Observing a file is not a "
                    "licence; rights are confirmed with the owner before publishing.",
        },
        "q3_brand_feel": {
            "feel": _text(direction.get("concept")),
            "typography": _text(direction.get("typography")),
            "brand_continuity": _text(direction.get("brand_continuity")),
            "verified_colors": [c.get("hex") for c in identity.get("verified_original_colors") or []
                                if isinstance(c, dict)],
            "verified_logo": bool(identity.get("verified_original_logos")),
            "references": references,
            "rule": "References inform layout, rhythm and motion only; never "
                    "their colours, text, images or identity.",
        },
        "q4_primary_action": action,
        "q5_performance": {**PERFORMANCE_BUDGET, "technique": technique},
        "q6_verified_facts": facts,
    }
    gaps = []
    if not brief["q1_signature_moment"]["moment"]:
        gaps.append("q1_signature_moment")
    if len(references) < 2:
        gaps.append("q3_brand_feel")
    if not action:
        gaps.append("q4_primary_action")
    if not facts["name"]:
        gaps.append("q6_verified_facts")
    brief["gaps"] = gaps
    return brief


def validate_pre_build_brief(brief: dict) -> dict:
    """Hard gate: no page is authored until all six questions are answered."""
    if not isinstance(brief, dict) or brief.get("protocol") != PROTOCOL:
        raise RuntimeError("PRE_BUILD_BRIEF_INCOMPLETE: missing")
    gaps = brief.get("gaps")
    if gaps:
        raise RuntimeError("PRE_BUILD_BRIEF_INCOMPLETE: " + ",".join(gaps))
    if brief["q1_signature_moment"]["technique"] not in TECHNIQUES:
        raise RuntimeError("PRE_BUILD_BRIEF_INCOMPLETE: q1_signature_moment")
    return brief


def ensure_pre_build_brief(research: dict, staged_media: list | None = None) -> dict:
    """Derive (or re-derive for older checkpoints) and validate in place."""
    brief = derive_pre_build_brief(research, staged_media)
    research["pre_build_brief"] = brief
    return validate_pre_build_brief(brief)


GAP_LABELS = {
    "missing": "Rakennusta edeltävä brief puuttuu",
    "q1_signature_moment": "tunnusmerkkihetki puuttuu",
    "q3_brand_feel": "alle 2 vertailusivustoa",
    "q4_primary_action": "ei vahvistettua yhteystoimintoa",
    "q6_verified_facts": "yrityksen nimi vahvistamatta",
}

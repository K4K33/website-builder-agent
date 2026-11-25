"""Kaurivo V7: company-first source passport, international reference *candidates*
and evidence-based generic-design preflight. No external calls or pretend scores.

The output feeds Research/Builder/QA. Visual appearance still requires a real
reviewer looking at the rendered company site. Candidate benchmark URLs NEVER
count as captured/comparable evidence and cannot bypass validate_benchmark.
"""
from __future__ import annotations

from collections import Counter
from hashlib import sha256
from pathlib import Path
import json
import re
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
MASTER_V7 = ROOT / "docs" / "KAURIVO_MASTER_V7.md"
REFERENCES_V7 = ROOT / "config" / "kaurivo_v7_reference_candidates.json"
V7_POLICY = MASTER_V7.read_text(encoding="utf-8")

VISUAL_EXECUTION_BRIEF = """
Build the first view around the customer's genuine subject and visitor task.
Choose distinct compositions for the three concepts: a single subject in
depth, an immersive real scene, an asymmetric visual grid, a type-led reveal,
or a source-specific alternative. Preserve the selected direction through the
first meaningful section and carry its visual language into the service route.
Treat reference work as evidence of a design principle. Record the URL,
principle, source asset, mobile crop and primary action when making a selection.

Choose motion only for a useful visual explanation. Prefer an ordered
source-photo sequence for genuine stages, an existing approved video for a
space or process, and an explicit gallery or comparison for material details.
Allow direct navigation and ordinary scrolling throughout. Keep primary copy,
actions and project evidence available with reduced motion and touch input.
Use real 3D only when approved source assets and the visitor task justify it.
Do not add a synthetic spotlight, decorative tilt or fake transformation.
Review the first view and next section on desktop and phone after rendering.
"""


VISUAL_PLAYBOOK = "\n\n".join(
    (ROOT / "docs" / name).read_text(encoding="utf-8")
    for name in ("KAURIVO_VISUAL_PLAYBOOK.md", "KAURIVO_COLOUR_GUIDE.md",
                 "KAURIVO_PURIST_COLOUR_RULES.md")
)
V7_SHA256 = sha256((V7_POLICY + "\n" + VISUAL_PLAYBOOK).encode("utf-8")).hexdigest()

CREATIVE_DIRECTION_BRIEF = """
Use the existing concept fields to record concrete decisions. In first_view,
specify the hero geometry, focal subject, offer and action. In image_strategy,
choose the source imagery, background treatment and useful motion or a still.
In brand_continuity, distinguish observed identity colours from proposals and
describe the palette strategy, dominant area, surface, ink and action roles.
Compare alternatives by lightness hierarchy, chroma, media compatibility and
the needs of the real visitor. Keep the approved identity anchor in each.
In information_architecture, specify the first service decision after the hero
and the destination page's distinct opening. In mobile_behavior, describe the
crop, reordering, touch controls and stable version when applicable.
"""

VISUAL_REVIEW_BRIEF = """
Ground observations in the supplied screenshots. Identify the dominant subject,
crop, text hierarchy, background and accent roles, then note whether they
support the customer's offer and action. Identify the component and surface
behind each colour defect, distinguish weak lightness from competing chroma,
and request a specific role or background correction. Check relevant state
and contrast evidence when available. Inspect the next meaningful section
and the service route for a coherent but task-specific composition. Flag
interchangeable imagery, cloned openings, noisy backgrounds, illegible text or
cropped subjects in the exact affected view. Judge motion only from browser
interaction evidence; screenshots establish static composition and fallback.
"""

# Sector match is only discovery routing, NEVER proof of a shared industry.
SECTOR_TERMS = {
    "auto_repair": ("autohuol", "autokorja", "korjaamo", "car repair", "auto service", "vehicle repair"),
    "restaurant": ("ravintol", "restaurant", "dining", "bistro", "pizzer"),
    "cafe": ("kahvil", "cafe", "café", "paahtimo", "coffee", "roast"),
    "bakery": ("leipomo", "bakery", "patisserie", "baker"),
    "dentist": ("hammas", "dental", "dentist", "odont"),
    "accounting": ("tilitoim", "kirjanpit", "accounting", "accountancy", "bookkeep", "redovisning"),
    "law": ("lakitoimisto", "asianaj", "jurist", "law firm", "legal service"),
    "architecture": ("arkkiteh", "architect", "visualis"),
    "construction": ("rakennus", "construction", "remont", "saneeraus", "builder"),
    "landscape": ("maisema", "viherrak", "pihasuunn", "landscap"),
    "fitness": ("kuntosal", "pilates", "fitness", "gym", "liikuntakesku"),
    "wellness": ("hieront", "spa", "wellness", "hyvinvoint", "massage"),
    "hotel": ("hotelli", "hotel", "majoitu", "guesthouse", "majoitus"),
    "real_estate": ("kiinteistönväl", "välitystoimisto", "real estate", "estate agent"),
    "furniture": ("kaluste", "huonekalu", "interior", "furniture", "sisustus"),
    "cleaning": ("siivous", "cleaning", "puhtaus", "toimitilahuol", "kiinteistöhuol"),
}


def reference_candidates(industry: str, *, limit: int = 3) -> list[dict]:
    """Offer leads for subsequent verified screenshot research, NEVER a 10/10 claim."""
    data = json.loads(REFERENCES_V7.read_text(encoding="utf-8"))
    phrase = str(industry or "").casefold()
    matches = [key for key, terms in SECTOR_TERMS.items()
               if any(term in phrase for term in terms)]
    picks = [record for record in data["industries"]
             if record["category"] in matches]
    return [
        {"url": r["url"], "country": r["country"],
         "category": r["category"], "design_lesson": r["design_lesson"],
         "status": "CANDIDATE_REQUIRES_REAL_BROWSER_CAPTURE",
         "copy_assets_or_layout": False}
        for r in picks[:max(0, min(limit, 5))]
    ]


def source_passport(research: dict, company: dict | None = None) -> dict:
    """Describe *observed* original-media candidates, never silently grant rights."""
    research = research if isinstance(research, dict) else {}
    company = company if isinstance(company, dict) else {}
    pages = (research.get("source_inventory") or {}).get("pages") or []
    observed, seen = [], set()
    for page in pages:
        if not isinstance(page, dict):
            continue
        identity = page.get("source_identity") or {}
        photos = identity.get("original_content_photos") or []
        for photo in photos:
            if not isinstance(photo, dict):
                continue
            url = str(photo.get("src") or "").strip()
            if not url or url in seen or url.startswith(("data:", "blob:", "javascript:")):
                continue
            seen.add(url)
            observed.append({
                "src": url, "found_on": str(page.get("url") or ""),
                "observed_subject": str(photo.get("alt") or photo.get("subject") or "")[:250],
                "rights_status": "PENDING_EXPLICIT_PERMISSION",
                "image_not_automatically_approved": True,
            })
    assets = research.get("brand_assets") or {}
    facts = research.get("company_facts") or {}
    inventory = research.get("source_inventory") or {}
    brand = {
        "business_name": str(facts.get("name") or company.get("name") or ""),
        "logo_candidate": str(assets.get("approved_original_logo_url") or ""),
        "logo_rights_source": "VERIFY_ASSET_LICENSE_AND_APPROVAL",
        "brand_signature_plan": research.get("brand_signature_plan") or {},
    }
    no_site = research.get("research_mode") == "verified_no_website"
    return {
        "protocol": "kaurivo-v7-source-passport",
        "original_url": str(company.get("url") or inventory.get("root_url") or ""),
        "research_mode": research.get("research_mode") or "existing_site",
        "no_site_does_not_mean_no_brand": bool(no_site),
        "source_page_count": len(pages),
        "photos": observed[:50],
        "available_source_photo_count": len(observed),
        "brand": brand,
        "rights_are_not_auto_granted": True,
        "missing_evidence": (
            (["No original website. Inspect genuine company-owned social, print and supplied brand material."]
             if no_site else [])
            + (["Original photos exist; owner must verify each reuse right and image relevance."]
               if observed else ["No verified original photographic material available; request client assets."])
        ),
    }


def design_brief(research: dict, company: dict | None = None) -> dict:
    """Run before HTML generation, derive a documented image-first art direction."""
    research = research if isinstance(research, dict) else {}
    facts = research.get("company_facts") or {}
    passport = source_passport(research, company)
    industry = str(facts.get("industry") or "")
    refs = reference_candidates(industry)
    return {
        "protocol": "kaurivo-v7-design-brief",
        "master_sha256": V7_SHA256,
        "business": passport["brand"]["business_name"],
        "industry": industry,
        "source_passport": passport,
        "reference_discovery_candidates_only": refs,
        "reference_evidence_gate": "Only screenshot-verified records in design_benchmark count as references.",
        "media_decision": (
            "Inspect actual original company photographs and usage rights BEFORE deciding hero/crops."
            if passport["photos"] else
            "Original photos not verified: request client assets; licensed, clearly illustrated "
            "provisional imagery permitted only with exact rights, never fake company work."
        ),
        "hero_direction": VISUAL_EXECUTION_BRIEF.strip(),
        "avoid_by_default": [
            "decorative sequential number tiles", "fake map", "oversized abstract vector hero",
            "generic repeated dark/grey/red bands", "fake staff/customer photos",
            "unverified badges", "very tight headline tracking", "stretched fonts",
            "generic research-report copy", "gratuitous pointer-following 3D light",
        ],
        "user_journeys": research.get("primary_user_journeys") or [],
        "source_floor": "Preserve useful source photography, logo, galleries, motion and business information.",
        "quality_not_self_certified": True,
    }


def visual_risks(pages: dict[str, str], *, css_text: str = "",
                 research: dict | None = None) -> dict:
    """Machine-detect obvious template hazards; NEVER invent visual scores."""
    blocking, review = [], []
    research = research if isinstance(research, dict) else {}
    passport = source_passport(research)
    for route, html in (pages or {}).items():
        soup = BeautifulSoup(str(html), "html.parser")
        styles = css_text + "\n" + "\n".join(
            el.get_text() for el in soup.select("style")
        )
        # A decorative fake-map grid with an invented location pin is not real
        # geography even when accompanied by an actual directions URL.
        if (soup.select_one('[class*="location-grid"],[class*="pseudo-map"]')
                and soup.select_one('[class*="location-pin"],[class*="grid-line"]')
                and not soup.select_one('iframe[src*="maps.google."],iframe[src*="openstreetmap."]')):
            blocking.append({
                "route": route, "code": "faux_geographic_map",
                "repair": "Remove fabricated street geometry; present the verified address and real directions link.",
            })
        if re.search(r"(?:scaleX\(\s*0\.\d+|font-stretch:\s*(?:ultra-|extra-|semi-)?condensed)", styles, re.I):
            review.append({"route": route, "code": "artificially_condensed_typography",
                           "repair": "Inspect real heading glyphs and use a properly licensed natural font/fallback."})
        if any(float("0." + value) >= .07 for value in
               re.findall(r"letter-spacing\s*:\s*-0?\.(\d+)em", styles, re.I)
               if value.isdigit()):
            review.append({"route": route, "code": "extreme_negative_letterspacing",
                           "repair": "Inspect actual 390/768/1440 screenshots, reduce squeezed headline tracking."})
        counters = [
            el.get_text(" ", strip=True)
            for el in soup.select('[class*="number"],[class*="counter"],[class*="index"],[class*="step"]')
            if re.fullmatch(r"\d{1,3}\+?|\d{2}", el.get_text(" ", strip=True))
        ]
        if len(counters) >= 2:
            review.append({"route": route, "code": "decorative_number_rhythm",
                           "evidence": counters[:6],
                           "repair": "Remove numbered graphics unless meaningful verified steps or measurements."})
        vector_media = [
            el.get("src") for el in soup.select("main img[src]")
            if re.search(r"(?:wheel|engine|gear|technical|abstract|blueprint|schematic).*\.svg", str(el.get("src") or ""), re.I)
        ]
        if vector_media:
            review.append({"route": route, "code": "schematic_over_real_photo",
                           "evidence": vector_media[:5],
                           "repair": "Compare with sourced authentic work photos; don't substitute generic SVG art for real craft."})
        if passport["photos"] and vector_media:
            review.append({"route": route, "code": "original_photographic_floor_at_risk",
                           "repair": "Source photo exists; verify rights and keep recognizable work photography whenever usable."})
    return {
        "status": "HOLD" if blocking else "REQUIRES_REAL_VISUAL_REVIEW" if review else "NO_STATIC_VISUAL_DEFECT_DETECTED",
        "blocking": blocking,
        "review_required": review,
        "human_visual_review_still_required": True,
        "note": "A static preflight is not a 9.5 score or independent premium approval.",
    }

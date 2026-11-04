"""Source-grounded purpose-first page layouts, enforced BEFORE saving HTML.

The previous QA kept original images somewhere but allowed enormous empty
title bands, recycled pictures and duplicated CTAs on every route. Known
failures on photo-rich businesses now BLOCK output; image-poor businesses
are never told to invent media. This is not a numeric aesthetic grade.
"""
from __future__ import annotations
import re
from bs4 import BeautifulSoup
from utils.content_parity import source_inventory_sha256
from utils.cross_route_editorial_risks import audit_cross_route_editorial_risks
from utils.premium_quality_gate import site_digest

ROLE_PATTERNS = (
    ("rental", re.compile(r"vuokra|rental|hire|juhlapuku", re.I)),
    ("contact", re.compile(r"yhteys|yhteystied|myym[aä]l[aä]|contact|visit|käynti|k[aä]ynti|osoite|aukiolo|location|directions|toimipiste", re.I)),
    ("collection", re.compile(r"valikoima|tuotte|product|mallisto|catalog|galler|gallery|referens|portfolio|ty[oö]t|projektit|collection|stock", re.I)),
    ("people", re.compile(r"meist[aä]|about us|tiimi|team|henkil[oö]st|tekij[aä]t|employees|our people", re.I)),
    ("booking", re.compile(r"ajanvara|booking|varaa aika|appointment", re.I)),
    ("service", re.compile(r"palvelu|huolto|myyntitili|myy vaatte|consign|repair|service|korja|asenn|tilaa", re.I)),
)
EXPECTATIONS = {
    "rental": "Show an authentic example product and a truthful enquiry route early.",
    "collection": "Show genuine products/work in first content section.",
    "contact": "Present verified address/contact details in the first content section.",
    "people": "Lead with real staff or workshop identity if sourced.",
    "booking": "Show the real booking action early.",
    "service": "Explain the specific service and its actual next step.",
    "general": "Explain this route's visitor task, without a reused agency hero.",
}

def source_photo_count(research: dict) -> int:
    seen = set()
    for page in (research.get("source_inventory") or {}).get("pages") or []:
        if isinstance(page, dict):
            ident = page.get("source_identity") or {}
            for p in ident.get("original_content_photos") or []:
                if isinstance(p, dict) and p.get("src"):
                    seen.add(str(p["src"]).strip())
    return len(seen)

def _route_role(page: dict) -> str:
    if str(page.get("path") or "") == "index.html":
        return "general"
    for text in (str(page.get("path") or ""), str(page.get("purpose") or ""),
                 str(page.get("user_task") or "")):
        for role, pattern in ROLE_PATTERNS:
            if pattern.search(text):
                return role
    return "general"

def derive_route_experience_contract(research: dict) -> dict:
    """Deterministic pre-build contract tied to actual planned visitor jobs."""
    count = source_photo_count(research)
    inv = research.get("source_inventory") or {}
    plan = (research.get("site_architecture") or {}).get("pages") or []
    routes = []
    for row in plan:
        if not isinstance(row, dict): continue
        role = _route_role(row)
        routes.append({
            "route": str(row.get("path") or ""),
            "role": role,
            "visitor_task": str(row.get("user_task") or "")[:280],
            "purpose": str(row.get("purpose") or "")[:280],
            "first_section_requirement": EXPECTATIONS[role],
            "product_media_required": count >= 3 and role in ("collection", "rental"),
            "contact_details_required": role == "contact",
        })
    return {
        "protocol": "purpose-first-route-v1",
        "source_sha256": source_inventory_sha256(inv) if inv.get("pages") else "",
        "source_photo_count": count,
        "photo_rich_source": count >= 3,
        "routes": routes,
        "rule": "Each route serves its own real visitor task. Product/rental "
                "routes with original photographs MUST open with relevant "
                "authentic media; contact routes with verified details MUST "
                "present contact information promptly. Do not reuse a single "
                "original photo or identical CTA across three unrelated routes. "
                "Don't invent photos when rights are absent."
    }

def _signed_exception(research: dict, pages: dict[str, str],
                      source_hash: str, issue: str) -> bool:
    """Specific reviewed exception cannot be invented once for every site."""
    current = site_digest(pages)
    for rec in research.get("route_composition_exceptions") or []:
        if not isinstance(rec, dict): continue
        if (rec.get("issue") == issue and rec.get("approved") is True
            and rec.get("reviewer_kind") == "independent_human"
            and str(rec.get("reviewer_id") or "").strip()
            and str(rec.get("screenshot_evidence") or "").strip()
            and len(str(rec.get("justification") or "").strip()) >= 30
            and rec.get("source_sha256") == source_hash
            and rec.get("build_sha256") == current):
            return True
    return False

def _first_section(raw: str):
    main = BeautifulSoup(raw, "html.parser").find("main")
    return (main.find(["section", "article"], recursive=False)
            or main.find(["section", "article"]) or main) if main else None

def _contact_evidence(first) -> bool:
    if first.select_one('address,a[href^="tel:"],a[href^="mailto:"]'):
        return True
    # Verified address may be presented beside a real route link.
    directions = first.select_one('a[href*="google.com/maps"],'
                                  'a[href*="maps.apple.com"],'
                                  'a[href*="openstreetmap.org"]')
    return bool(directions and len(first.get_text(" ", strip=True)) >= 20)

def audit_route_experience(pages: dict[str, str], research: dict) -> dict:
    contract = derive_route_experience_contract(research)
    blocking, pending = [], []
    if not pages or len(pages) < 2:
        return {"blocking": blocking, "pending": pending, "contract": contract}
    for row in contract["routes"]:
        route = row["route"]
        if route not in pages: continue  # Source architecture checks this.
        first = _first_section(pages[route])
        if first is None: continue
        if row["product_media_required"] and first.select_one(
            'img[src],img[data-src],picture img,video,iframe[src]'
        ) is None:
            issue = "product_media_missing_first_section:" + route
            if not _signed_exception(research,pages,contract["source_sha256"],issue):
                blocking.append({
                    "kind":"task_first_view_has_no_product_evidence",
                    "issue":issue, "route":route,
                    "detail":"Original photos exist but product/rental page starts "
                             "without merchandise evidence. A huge title and a "
                             "photo several sections later are not equivalent.",
                })
        if row["contact_details_required"]:
            facts = research.get("company_facts") or {}
            verified = any(facts.get(k) for k in
                           ("address","phone","email","opening_hours"))
            if verified and not _contact_evidence(first):
                issue = "real_contact_missing_first_section:" + route
                if not _signed_exception(research,pages,contract["source_sha256"],issue):
                    blocking.append({
                        "kind":"contact_page_hides_verified_visit_details",
                        "issue":issue, "route":route,
                        "detail":"Verified visitor information exists but is absent "
                                 "from the contact page's opening section.",
                    })
    editorial = audit_cross_route_editorial_risks(pages,research)
    hard = {"recycled_business_photography",
            "repeated_text_only_subpage_openings",
            "repeated_full_width_call_to_action_copy"}
    for risk in editorial["pending"]:
        kind = str(risk.get("category") or "")
        issue = "cross_route:" + kind
        if (kind in hard and contract["photo_rich_source"] and len(pages)>=3
            and not _signed_exception(research,pages,contract["source_sha256"],issue)):
            blocking.append({"kind":kind, "issue":issue,
                             "detail":risk.get("issue"),
                             "examples":risk.get("examples",risk.get("routes",[]))})
        else:
            pending.append(risk)
    return {
        "blocking":blocking, "pending":pending,"contract":contract,
        "editorial_observations":editorial.get("observations",{}),
        "note":"Deterministic task-specific evidence gate, not an aesthetic "
               "score. Actual browser folds, client media rights, and independent "
               "visual review still required.",
    }

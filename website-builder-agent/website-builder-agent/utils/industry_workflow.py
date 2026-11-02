"""Industry-first Kaurivo research and design preflight (no LLM credits).

Sector profiles describe what visitors need to accomplish and what evidence
must survive a redesign. They are NOT HTML templates or fixed page layouts.
The company-specific brief and competitor evidence determine the art direction.
"""
from __future__ import annotations

from collections import deque
import ipaddress
from urllib.parse import urljoin, urlsplit, urlunsplit

# Content requirements, never fixed "hero / four cards / CTA" designs.
SECTORS = {
    "automotive": {
        "terms": ("autokorja", "autohuol", "vehicle repair", "car repair", "garage"),
        "visitor_tasks": ("identify relevant repair or service", "find reliable contact/booking path",
                          "see specialisms, terms and practical drop-off information"),
        "source_focus": ("service categories", "booking links", "vehicle expertise",
                         "opening hours", "chain identity", "payment options"),
    },
    "restaurant": {
        "terms": ("ravintola", "restaurant", "kahvila", "cafe", "café", "lounas"),
        "visitor_tasks": ("see current complete menu and any dietary information",
                          "find opening hours and location", "contact about events if offered"),
        "source_focus": ("menus and their valid dates", "exact original G/L/M labels",
                         "allergen source/verification", "prices", "hours",
                         "booking/event information"),
    },
    "construction": {
        "terms": ("rakennus", "remont", "construction", "renovation", "urakoin"),
        "visitor_tasks": ("evaluate genuine completed projects", "understand specialties",
                          "submit a scoped project inquiry"),
        "source_focus": ("real project images", "verified before/after pairs",
                         "service coverage", "qualifications", "project inquiry"),
    },
    "retail": {
        "terms": ("kauppa", "myymälä", "shop", "store", "retail"),
        "visitor_tasks": ("browse actual products", "find delivery or pickup details",
                          "locate support and return information"),
        "source_focus": ("product categories", "prices", "stock status source",
                         "delivery", "returns", "physical store hours"),
    },
    "wellness": {
        "terms": ("hyvinvointi", "hieronta", "kauneus", "wellness", "salon"),
        "visitor_tasks": ("understand actual treatments", "find prices and booking/appointment path",
                          "assess appropriate practitioner qualifications"),
        "source_focus": ("service qualifications", "prices", "booking system",
                         "staff credentials if verified", "service limitations"),
    },
}

# A crawler may discover more content than its bounded safe fetch budget.
# Prioritize pages which tend to contain information that is costly to lose.
PRIORITY_WORDS = (
    "palvel", "service", "huol", "repair", "menu", "lounas", "ruokalist",
    "hinn", "price", "yhteys", "contact", "meist", "about", "yrity",
    "kohte", "referens", "project", "partner", "kumpp", "sponsor",
    "allergen", "ruokaval", "tiimi", "team", "faq", "kysymy",
)
SKIP_PATHS = ("/wp-admin", "/login", "/cart", "/checkout", "/feed",
              "/api/", "/cdn-cgi", "/privacy-policy", "/cookie")
SKIP_ENDINGS = (".pdf", ".jpg", ".jpeg", ".png", ".gif", ".webp",
                ".svg", ".zip", ".mp4", ".css", ".js", ".xml")


def sector_guidance(industry: str) -> dict:
    text = str(industry or "").casefold()
    for sector, data in SECTORS.items():
        if any(term in text for term in data["terms"]):
            return {
                "sector": sector,
                "visitor_tasks": list(data["visitor_tasks"]),
                "source_focus": list(data["source_focus"]),
                "layout_instructions": (
                    "Plan an original company-specific composition based on the "
                    "verified brand, actual content density and three source-backed "
                    "same-industry benchmarks. Do NOT reuse a sector template."
                ),
            }
    return {
        "sector": "other",
        "visitor_tasks": ["identify the target visitor's actual question",
                          "present verified offering and next step",
                          "retain existing company's practical information"],
        "source_focus": ["all existing important content and footer affiliations"],
        "layout_instructions": "Invent a source-led custom layout; no generic grid template.",
    }


def _safe_hostname(host: str | None) -> str:
    host = (host or "").lower().removeprefix("www.")
    if not host or host in {"localhost", "localhost.localdomain"} or host.endswith(".local"):
        return ""
    try:
        ipaddress.ip_address(host)
        return ""  # No direct IP or private-network destinations.
    except ValueError:
        return host if "." in host else ""


def _same_site_url(start: str, candidate: str) -> str:
    parsed_start = urlsplit(start)
    resolved = urlsplit(urljoin(start, candidate))
    if (resolved.scheme not in {"http", "https"} or resolved.username
            or resolved.password or not _safe_hostname(parsed_start.hostname)
            or _safe_hostname(resolved.hostname) != _safe_hostname(parsed_start.hostname)):
        return ""
    path = (resolved.path or "/").rstrip("/") or "/"
    if path.casefold().endswith(SKIP_ENDINGS) or any(
            path.casefold().startswith(prefix) for prefix in SKIP_PATHS):
        return ""
    # Strip tracking/refresh queries and in-page fragments for bounded crawl.
    return urlunsplit((resolved.scheme, resolved.netloc, path, "", ""))


def _priority(url: str) -> tuple[int, int, str]:
    path = urlsplit(url).path.casefold()
    score = 0 if any(word in path for word in PRIORITY_WORDS) else 1
    return score, path.count("/"), path


def crawl_original_website(
    url: str, fetch_page, *, first_page: dict | None = None, max_pages: int = 12
) -> dict:
    """Fetch ONLY bounded same-domain HTML pages with an injected fetcher.

    fetch_page defaults to existing analyze_url in Research, but is injected
    for unlimited offline tests. Never submits a form or invokes Tavily/AI.
    """
    start = _same_site_url(url, url)
    if not start:
        raise ValueError("Only public-looking http(s) site hostnames can be researched.")
    if not 1 <= max_pages <= 24:
        raise ValueError("Crawl cap must be 1..24")
    queue = [start]
    visited, pages, failed = set(), [], []
    known = {start}
    while queue and len(visited) < max_pages:
        queue.sort(key=lambda u: (0 if u == start and u not in visited else 1, _priority(u)))
        current = queue.pop(0)
        if current in visited:
            continue
        visited.add(current)
        data = first_page if current == start and first_page is not None else fetch_page(current)
        if not isinstance(data, dict) or data.get("success") is not True:
            failed.append(current)
            continue
        final = _same_site_url(start, str(data.get("final_url") or current))
        if not final:
            failed.append(current)
            continue
        links = data.get("links", [])
        for link in links if isinstance(links, list) else []:
            if not isinstance(link, dict):
                continue
            href = _same_site_url(current, str(link.get("href") or ""))
            if href and href not in known:
                known.add(href)
                queue.append(href)
        pages.append({
            "url": current,
            "title": str(data.get("title") or "")[:240],
            "text": str(data.get("visible_text") or "")[:6500],
            "headings": data.get("headings") if isinstance(data.get("headings"), dict) else {},
            "images": (data.get("images") or [])[:70],
            "forms": (data.get("forms") or [])[:15],
            "links": (links if isinstance(links, list) else [])[:150],
            "footer_assets": (data.get("footer_assets") or [])[:30],
            "footer_links": (data.get("footer_links") or [])[:75],
            "header_assets": (data.get("header_assets") or [])[:15],
        })
    unvisited = sorted(known - visited, key=_priority)
    priority_unvisited = [u for u in unvisited if _priority(u)[0] == 0]
    return {
        "mode": "multi_page_snapshot",
        "root_url": start,
        "pages": pages,
        "failed_urls": failed,
        "unvisited_urls": unvisited,
        "priority_unvisited_urls": priority_unvisited,
        "max_pages": max_pages,
        "note": "Evidence snapshot, not guaranteed exhaustive. Client and media rights review still required.",
    }


def validate_inventory(company: dict, research: dict) -> dict:
    """Require actual source coverage before spending credits in Builder.

    No-site companies use their separately verified factual profiles.
    """
    if research.get("research_mode") == "verified_no_website":
        if not research.get("fact_sources"):
            raise RuntimeError("No-site project lacks verified fact sources.")
        return {"mode": "verified_no_website", "pages": 0, "issues": []}
    if not (company.get("url") or company.get("website")):
        raise RuntimeError("Company has neither source website nor verified no-site profile.")
    inventory = research.get("source_inventory")
    if not isinstance(inventory, dict) or not isinstance(inventory.get("pages"), list):
        raise RuntimeError("Source inventory missing: rerun multi-page Research before Builder.")
    pages = inventory["pages"]
    if not pages or not all(
        isinstance(p, dict) and p.get("url")
        and (p.get("text") or p.get("images")
             or p.get("header_assets") or p.get("footer_assets"))
        for p in pages
    ):
        raise RuntimeError("Source inventory has no usable source-backed pages.")
    if inventory.get("priority_unvisited_urls"):
        raise RuntimeError(
            "Important source pages not researched: "
            + ", ".join(inventory["priority_unvisited_urls"][:5])
        )
    if inventory.get("failed_urls"):
        raise RuntimeError(
            "Original source pages failed to load: "
            + ", ".join(inventory["failed_urls"][:5])
        )
    return {"mode": "multi_page_snapshot", "pages": len(pages), "issues": []}


def create_industry_brief(company: dict, research: dict) -> dict:
    """Customer tasks + evidence obligations, never sector-specific HTML layout."""
    status = validate_inventory(company, research)
    facts = research.get("company_facts") or {}
    guidance = sector_guidance(facts.get("industry", ""))
    inventory = research.get("source_inventory") or {}
    pages = inventory.get("pages") or []
    # Preserve a bounded pointer to EVERY researched page, not only the homepage.
    source_pages = [{
        "url": p.get("url"),
        "title": p.get("title", ""),
        "headings": p.get("headings", {}),
        "evidence_excerpt": str(p.get("text", ""))[:1900],
        "image_candidates": (p.get("images") or [])[:14],
        "header_assets": (p.get("header_assets") or [])[:10],
        "footer_assets": (p.get("footer_assets") or [])[:16],
        "footer_links": (p.get("footer_links") or [])[:25],
        "form_count": len(p.get("forms") or []),
    } for p in pages]
    return {
        "company": str(company.get("name") or facts.get("name") or ""),
        **guidance,
        "inventory_status": status,
        "source_pages": source_pages,
        "must_preserve": [
            "real company logo and approved brand; no invented textual replacement",
            "all current services, price and contact facts from researched old pages",
            "footer sponsor/chain/certification marks only with correct roles and permissions",
            "real galleries and matched before/after only if true originals exist",
            "original menu G/L/M and allergen evidence when a restaurant menu exists",
            "true booking and lead-handling; never a dead form",
            "no repetitive decorative 01/02/03 card numbering",
        ],
        "proof_and_release": (
            "Human approval and source/right checks required for photos/logos, "
            "full content parity, independent visual review and editable CMS. "
            "This brief does not imply an accepted or customer-ready website."
        ),
    }

def validate_design_intent(research: dict) -> dict:
    """Reject a generic or empty visual plan before running the Builder model.

    This checks completeness, not artistic quality; a separate independent
    screenshot-based review is still mandatory.
    """
    recs = research.get("design_recommendations") or {}
    if not isinstance(recs, dict):
        raise RuntimeError("Missing customer-specific visual design recommendations.")
    required = ("visual_concept", "typography_scale", "spacing_and_layout", "mobile_plan")
    missing = [key for key in required if not isinstance(recs.get(key), str)
               or len(recs[key].strip()) < 20]
    if missing:
        raise RuntimeError("Customer-specific visual brief incomplete: " + ", ".join(missing))
    plan = recs.get("section_plan")
    if not isinstance(plan, list) or len(plan) < 2:
        raise RuntimeError("Client-specific section plan is missing or too generic.")
    seen = set()
    for item in plan:
        if not isinstance(item, dict):
            raise RuntimeError("Invalid client section plan entry.")
        key = str(item.get("id") or "").strip()
        purpose = str(item.get("purpose") or "").strip()
        layout = str(item.get("layout") or "").strip()
        if not key or key in seen or len(purpose) < 12 or len(layout) < 16:
            raise RuntimeError("Each section needs a unique id, reason and concrete layout.")
        seen.add(key)
    return {
        "visual_concept": recs["visual_concept"].strip(),
        "section_ids": sorted(seen),
        "layout_explanations": [p["layout"].strip() for p in plan],
        "note": "Structure verified; independently review visual originality.",
    }


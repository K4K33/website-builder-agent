"""Human-in-the-loop lead handoff with ZERO AI calls, network or email.

This is a review worklist, not a company-site verification system.
The owner choosing a candidate must NEVER be treated as proof that a site
is absent, that the company operates, or that outreach is lawful.
"""
from datetime import datetime, timezone
from urllib.parse import urlsplit

from utils.lead_queue import rank_leads
from utils.state import get_company, upsert_company

_DECISIONS = {"select", "later", "skip"}
_MAX_NOTE = 500


def record_decision(slug_or_name, decision, note=""):
    """Save an explicit owner decision. No auto-build, auto-publish or send."""
    if decision not in _DECISIONS:
        raise ValueError("Decision must be one of: select, later, skip.")
    if not isinstance(note, str) or len(note) > _MAX_NOTE:
        raise ValueError("Review note must contain at most 500 characters.")
    slug, company = get_company(slug_or_name)
    if company is None:
        raise ValueError("Company not in the saved queue. Discover it first.")
    reviewed = {
        "decision": decision,
        "note": note.strip(),
        "reviewed_at": datetime.now(timezone.utc).isoformat(),
        "selected_for_demo": decision == "select",
        "approval_to_contact": False,
    }
    upsert_company(slug, {"owner_review": reviewed})
    return {"company": slug, **reviewed}


def _source_url(value):
    if not isinstance(value, str) or len(value) > 2048:
        return ""
    parsed = urlsplit(value.strip())
    if parsed.scheme != "https" or not parsed.hostname or parsed.username or parsed.password:
        return ""
    return value.strip()


def _osm_url(company):
    # Only direct OSM object identities, not arbitrary user-supplied strings.
    osm_type = company.get("osm_type")
    osm_id = company.get("osm_id")
    if osm_type in {"node", "way", "relation"} and (
        isinstance(osm_id, int) and not isinstance(osm_id, bool) and osm_id > 0
    ):
        return f"https://www.openstreetmap.org/{osm_type}/{osm_id}"
    return ""


def shortlist(companies, *, limit=10, include_reviewed=False):
    """Produce a compact, source-traceable user review batch without IO.

    * No website listed is labelled unverified.
    * A record marked skip is excluded unless explicitly requested.
    * Verified currently active no-site firms come first via rank_leads.
    * Unknown active status is an invitation to verify, not proof of closure.
    * No contact data or unverified review/finance claims are fabricated.
    """
    if not isinstance(limit, int) or not 1 <= limit <= 100:
        raise ValueError("Shortlist limit must be 1..100.")
    rows = rank_leads(companies)
    cards = []
    for row in rows:
        company = companies.get(row["company"]) or {}
        decision = (company.get("owner_review") or {}).get("decision")
        if row["business_activity"] == "inactive":
            continue
        if not include_reviewed and decision in {"select", "skip"}:
            continue
        source = (
            _osm_url(company)
            or _source_url((company.get("registry_evidence") or {}).get("registry_source_url"))
            or _source_url((company.get("financials") or {}).get("registry_source_url"))
        )
        site = row["site_status"]
        cards.append({
            "company": row["company"],
            "name": row["name"],
            "industry": company.get("industry") or (company.get("company_profile") or {}).get("industry") or "unknown",
            "location": company.get("city") or company.get("location") or "unknown",
            "website_status": site,
            "website_url": _source_url(company.get("website") or company.get("url")),
            "current_business_activity": row["business_activity"],
            "source_url": source,
            "review_state": decision or "not_reviewed",
            "reason": (
                "Verified active; website absence independently reviewed"
                if row["bucket"] == "no_website_active_priority" else
                "No website listed; independently check for an existing site"
                if site == "website_not_listed" else
                "Website absence reviewed; business operation still needs evidence"
                if site == "confirmed_no_website" else
                "Optional existing-site redesign candidate"
            ),
            "checks_needed": [
                key for key, required in (
                    ("confirm_current_operations", row["business_activity"] != "active"),
                    ("verify_website_absence", site == "website_not_listed"),
                ) if required
            ],
            "builder_authorized": False,
            "outreach_authorized": False,
        })
        if len(cards) >= limit:
            break
    return cards


def format_markdown(cards):
    """Human-readable handoff with explicit uncertainty, never sales claims."""
    lines = ["# Kaurivo: yritykset tarkistettavaksi", ""]
    if not cards:
        return "# Kaurivo: yritykset tarkistettavaksi\n\nEi vielä sopivia tallennettuja liidejä.\n"
    for index, row in enumerate(cards, start=1):
        name = str(row["name"]).replace("\n", " ").replace("\r", " ")
        lines.extend([
            f"## {index}. {name}",
            f"- Tunniste: \`{row['company']}\`",
            f"- Ala ja sijainti: {row['industry']} · {row['location']}",
            f"- Aktiivinen toiminta: {row['current_business_activity']}",
            f"- Verkkosivutilanne: {row['website_status']}",
            f"- Lähde: {row['source_url'] or 'Ei lähdelinkkiä tallennettuna'}",
            f"- Nykyinen verkkosivu: {row['website_url'] or 'Ei tiedossa — ei todista sivuttomuutta'}",
            f"- Miksi mukana: {row['reason']}",
            f"- Tarkistettavat: {', '.join(row['checks_needed']) or 'Ei perustarkistuksia avoinna'}",
            "",
        ])
    lines.append("Valinta ei rakenna sivua eikä lähetä yhteydenottoja. Yritysfaktat ja demo hyväksytään erikseen.")
    return "\n".join(lines) + "\n"

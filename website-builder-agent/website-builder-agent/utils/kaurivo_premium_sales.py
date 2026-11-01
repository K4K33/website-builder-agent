"""Evidence-led Kaurivo demo, sales and delivery gates.

Pure functions; never search, send marketing, invoice, deploy, consume credits
or persist private prospect data. Every claim must be checked by a person.
"""
from __future__ import annotations

from urllib.parse import urlsplit
from utils.client_handover import client_design_brief, inspect_client_delivery
from utils.pitch_quality import assess_pitch_packet


def _https(value):
    if not isinstance(value, str) or len(value) > 2048:
        return False
    p = urlsplit(value)
    return p.scheme == "https" and bool(p.hostname) and not p.username and not p.password


def demo_improvement_packet(company):
    """Evidence before pitch: three verified peers, three specific improvements.

    "before" must describe an observation, not a speculative Lighthouse score.
    "after" is an intended design proposal, not a proven conversion result.
    All observations need URLs and human confirmation; we never scrape or guess.
    """
    company = company if isinstance(company, dict) else {}
    research = company.get("research") or {}
    facts = research.get("company_facts") or {}
    industry = str(facts.get("industry") or "").strip()
    name = str(facts.get("name") or "").strip()
    errors = []
    if not name or not industry:
        errors.append("Verified company name and industry required.")
    brand = client_design_brief(company)
    peers = []
    seen = set()
    for item in research.get("design_benchmark") or []:
        if not isinstance(item, dict):
            continue
        url = item.get("url")
        domain = urlsplit(url).hostname if _https(url) else None
        match = item.get("industry_match") or {}
        if (domain and domain not in seen and match.get("same_industry") is True
                and str(match.get("target_industry", "")).casefold() == industry.casefold()
                and item.get("observations") and item.get("apply") and item.get("avoid")):
            peers.append({"url": url, "observations": item["observations"][:3],
                          "adapt": item["apply"][:3], "avoid_copying": item["avoid"][:3]})
            seen.add(domain)
    if len(peers) < 3:
        errors.append("At least three reviewed same-industry design references required.")
    observations = []
    current_url = company.get("url") or company.get("website") or ""
    for item in research.get("verified_improvements") or []:
        if not isinstance(item, dict) or item.get("human_verified") is not True:
            continue
        before = str(item.get("before") or "").strip()
        after = str(item.get("after_proposal") or "").strip()
        source = str(item.get("source_url") or "").strip()
        if (len(before) >= 12 and len(after) >= 12 and _https(source)
                and (not current_url or urlsplit(source).hostname == urlsplit(current_url).hostname)):
            observations.append({"before": before[:350], "after_proposal": after[:350],
                                 "source_url": source, "benefit_type": "proposed_not_measured"})
    if len(observations) < 3:
        errors.append("Three source-attributed human-verified before/after proposals required.")
    return {
        "company": name,
        "ready_for_human_sales_review": not errors,
        "issues": errors,
        "design": brand,
        "references": peers[:3],
        "improvements": observations[:3],
        "send_authorized": False,
        "limitations": [
            "References and observations are recorded evidence, not independently rechecked live.",
            "Proposed design improvements are not guaranteed leads, ranking or revenue.",
            "Pitch quality, privacy and marketing compliance require separate approval.",
            "No demo or client data is published or emailed by this packet.",
        ],
    }


_REQUIRED_PROJECT_TERMS = (
    ("signed_or_explicit_written_acceptance", "Client has not accepted the exact proposal."),
    ("fixed_scope_and_page_count", "Deliverables/page count must be defined."),
    ("total_price_and_vat_treatment", "Total price and VAT treatment must be stated."),
    ("deposit_and_final_payment_terms", "Payment milestones and due dates must be agreed."),
    ("revision_rounds_and_change_requests", "Revisions and additional work must be defined."),
    ("approved_brand_and_content_rights", "Client rights to brand assets, copy and images missing."),
    ("hosting_domain_and_renewal_owner", "Domain, hosting and renewal responsibility missing."),
    ("cms_platform_and_editing_scope", "The client-editable CMS and scope must be agreed."),
    ("privacy_cookie_and_form_responsibilities", "Data controller, privacy, cookies and forms unassigned."),
    ("delivery_support_and_acceptance_terms", "Delivery, support and customer approval undefined."),
)


def agreement_gate(project):
    """Pre-work commercial checklist; never pretends to validate signatures."""
    project = project if isinstance(project, dict) else {}
    errors = [detail for field, detail in _REQUIRED_PROJECT_TERMS if project.get(field) is not True]
    if not isinstance(project.get("scope_version"), str) or not project["scope_version"].strip():
        errors.append("A versioned proposal/scope reference is required.")
    return {"ready_to_start_work": not errors, "issues": errors,
            "limitations": ["Boolean confirmations must be backed by a real written agreement.",
                            "This is not legal advice or proof of an enforceable contract."]}


def delivery_gate(company, site_audit):
    """Fail closed: a working static demo never counts as a delivered CMS."""
    delivery = inspect_client_delivery(company)
    site_audit = site_audit if isinstance(site_audit, dict) else {}
    problems = list(delivery["issues"])
    if site_audit.get("pass") is not True:
        problems.append("Automated HTML site preflight is not passing.")
    if site_audit.get("warnings"):
        problems.append("Site preflight warnings require human documented resolution.")
    return {"ready_to_deliver": not problems, "issues": sorted(set(problems)),
            "cms_platform": delivery["cms_platform"],
            "limitations": ["Recorded confirmations are not live independently verified.",
                            "Run real customer editing, publishing, rollback and device checks."]}


def funnel_metrics(companies):
    """Privacy-preserving counts, not made-up performance, spend or revenue.

    Does not infer sends from generated drafts or sales from proposals.
    Do not pass private CRM records to a publicly hosted analytics vendor.
    """
    counts = dict(discovered=0, owner_selected=0, demo_approved=0,
                  contacted=0, proposal=0, won=0, delivered=0)
    if not isinstance(companies, dict):
        return {"counts": counts, "conversion_rates": {}, "notes": ["Invalid dataset."]}
    for company in companies.values():
        if not isinstance(company, dict):
            continue
        counts["discovered"] += 1
        if (company.get("owner_review") or {}).get("decision") == "select":
            counts["owner_selected"] += 1
        if (company.get("approval") or {}).get("approved") is True:
            counts["demo_approved"] += 1
        # Explicit status/evidence only; not "email drafted" or "queued".
        if (company.get("outreach") or {}).get("sent_at") or company.get("status") in {"contacted", "negotiating"}:
            counts["contacted"] += 1
        if company.get("status") == "proposal" or (company.get("sale") or {}).get("status") == "proposal":
            counts["proposal"] += 1
        if (company.get("sale") or {}).get("status") == "won":
            counts["won"] += 1
        if (company.get("delivery") or {}).get("customer_acceptance") is True:
            counts["delivered"] += 1
    rate = lambda a, b: round(100 * counts[a] / counts[b], 1) if counts[b] else None
    return {"counts": counts,
            "conversion_rates": {"selected_per_discovered_pct": rate("owner_selected", "discovered"),
                                 "won_per_contacted_pct": rate("won", "contacted"),
                                 "delivered_per_won_pct": rate("delivered", "won")},
            "notes": ["Descriptive counts of locally recorded state; not audited CRM revenue.",
                      "Unknown stages are not inferred, and overlapping counts need not form a funnel.",
                      "No tracking pixels, third-party analytics or individual contact data."]}

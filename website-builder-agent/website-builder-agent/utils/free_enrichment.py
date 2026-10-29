"""Conservative, explicitly authorized free-source company enrichment.

Only PRH public open-data endpoints are contacted. At most two requests
per prospect (plus bounded XBRL pagination). No third-party ratings scraped,
no generative model calls, no auto-build, no sales messages.
"""
from datetime import datetime, timezone
import time

from utils.company_registry import lookup_by_business_id, lookup_by_name_and_location
from utils.lead_intelligence import evaluate_prospect, finnish_business_id
from utils.prh_financials import available_financial_periods
from utils.quality import canonical_url
from utils.state import load_companies, upsert_company


def enrich_one(company, lookup_id=lookup_by_business_id,
               lookup_name=lookup_by_name_and_location,
               lookup_periods=available_financial_periods):
    """Pure result update; caller persists only after checks succeed."""
    business_id = company.get("business_id") or (company.get("financials") or {}).get("business_id")
    name = str(company.get("name") or "").strip()
    city = str(company.get("city") or "").strip()
    if business_id and not finnish_business_id(business_id):
        return {"status": "manual_identity_check", "issues": ["invalid_business_id"], "updates": {}}
    if not business_id and not city:
        return {"status": "manual_identity_check", "issues": ["missing_exact_city_or_business_id"],
                "updates": {}}

    try:
        official = lookup_id(business_id) if business_id else lookup_name(name, city)
    except (ValueError, RuntimeError, KeyError) as exc:
        return {"status": "manual_identity_check", "issues": [str(exc)], "updates": {}}
    resolved_id = official.get("business_id")
    names = {str(x).strip().casefold() for x in official.get("official_names", [])}
    if not resolved_id or name.casefold() not in names:
        return {"status": "manual_identity_check", "issues": ["name_mismatch_with_prh"], "updates": {}}
    original_id = (company.get("financials") or {}).get("business_id")
    if original_id and original_id != resolved_id:
        return {"status": "manual_identity_check", "issues": ["existing_financial_identity_conflict"], "updates": {}}

    financials = dict(company.get("financials") or {})
    financials.update({
        "business_id": resolved_id,
        "business_id_verified": True,
        "registry_source_url": official["registry_source_url"],
    })
    if official.get("registration_ended"):
        financials["legal_status"] = "ended"
    if any(isinstance(item, dict) and item.get("type") in {"KONK", "SANE", "SELTILA"}
           and not item.get("endDate") for item in official.get("company_situations") or []):
        financials["insolvency_proceeding"] = True

    # Official PRH website is a hint, not proof it loads or belongs to the OSM entity.
    existing = canonical_url(company.get("website") or company.get("url"))
    official_web = canonical_url(official.get("official_website"))
    issues = []
    updates = {"business_id": resolved_id, "registry_evidence": official,
               "financials": financials, "enriched_at": datetime.now(timezone.utc).isoformat()}
    if official_web:
        if existing and existing != official_web:
            issues.append("official_site_conflicts_with_saved_site")
            updates["website_discovery"] = {"status": "conflict_needs_review",
                                            "official_candidate_url": official_web}
        elif not existing:
            # A website candidate is not promoted to verified site automatically.
            updates["website_discovery"] = {"status": "official_registry_candidate",
                                            "official_candidate_url": official_web}
    else:
        updates["website_discovery"] = {"status": "not_listed_in_prh"}

    try:
        periods = lookup_periods(resolved_id)
    except Exception as exc:
        # Network/PRH errors are unknown, not negative or a failed business.
        periods = {"status": "lookup_failed", "financial_figures_verified": False,
                   "reason": type(exc).__name__}
        issues.append("prh_financial_availability_lookup_failed")
    updates["financial_availability"] = periods

    refreshed = {**company, **updates}
    updates["lead_intelligence"] = evaluate_prospect(refreshed)
    return {"status": "enriched", "issues": issues, "updates": updates}


def enrich_queue(max_companies=5, pause_seconds=1, company_slug=None,
                 sleep=time.sleep, lookup_id=lookup_by_business_id,
                 lookup_name=lookup_by_name_and_location,
                 lookup_periods=available_financial_periods):
    """Bounded queue, saved incrementally. Public lookups are caller opt-in."""
    if not isinstance(max_companies, int) or isinstance(max_companies, bool) or not 1 <= max_companies <= 10:
        raise ValueError("max_companies must be 1..10")
    if not 0 <= pause_seconds <= 10:
        raise ValueError("pause_seconds must be 0..10")
    records = load_companies()
    if company_slug and company_slug not in records:
        raise RuntimeError("Company is missing from the lead queue")
    slugs = [company_slug] if company_slug else [
        slug for slug, company in records.items()
        if (company.get("status") in {"verification_pending", "found"}
            and not company.get("registry_evidence"))
    ]
    results = []
    for index, slug in enumerate(slugs[:max_companies]):
        if index:
            sleep(pause_seconds)
        result = enrich_one(records[slug], lookup_id, lookup_name, lookup_periods)
        results.append({"slug": slug, "status": result["status"], "issues": result["issues"]})
        if result["updates"]:
            upsert_company(slug, result["updates"])
    return results

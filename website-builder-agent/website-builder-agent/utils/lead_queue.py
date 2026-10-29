"""Deterministic prospect triage with no AI calls or unverifiable ratings.

Priority is not a prediction of buying intent. A firm without reviews or
accounts stays in a follow-up research queue, not a 'poor company' bin.
"""
from utils.lead_intelligence import evaluate_prospect


def rank_leads(companies, estimated_project_eur=1500):
    rows = []
    for slug, company in companies.items():
        info = evaluate_prospect(company, estimated_project_eur)
        reputation = info["reputation"]
        financial = info["financial"]
        capacity = info["purchase_capacity"]
        site = info["site_status"]
        has_report = (company.get("financial_availability") or {}).get("status") == "available"
        report_checked = (company.get("financial_statement_review") or {}).get("status") == "taxonomy_review_required"
        if capacity["status"] == "excluded":
            bucket, priority = "excluded_official_status", 0
        elif capacity["status"] == "strong_indicators" and reputation["strong"] and site in {
            "has_website", "confirmed_no_website"
        }:
            bucket, priority = "high_priority_manual_review", 6
        elif capacity["can_prioritize"] and reputation["strong"] and site == "confirmed_no_website":
            bucket, priority = "promising_no_site_manual_review", 5
        elif capacity["can_prioritize"] and reputation["strong"] and site == "website_not_listed":
            bucket, priority = "verify_website_absence", 4
        elif capacity["can_prioritize"] and site == "has_website":
            bucket, priority = "estimate_only_manual_review", 4
        elif capacity["status"] == "strong_indicators":
            bucket, priority = "verify_reputation_and_website", 3
        elif report_checked:
            bucket, priority = "review_xbrl_taxonomy_facts", 3
        elif has_report:
            bucket, priority = "inspect_available_prh_statement", 2
        elif site == "website_not_listed":
            bucket, priority = "verify_website_and_reputation", 1
        else:
            bucket, priority = "verify_financials_and_reputation", 1
        # Skip any automatic contact claim: the value is always human triage.
        rows.append({
            "company": slug, "name": company.get("name", slug),
            "site_status": site, "reputation_status": reputation["status"],
            "finance_status": financial["status"],
            "indicative_capacity": {
                "score": capacity["score"], "status": capacity["status"],
                "confidence": capacity["confidence"], "signals": capacity["signals"],
                "not_actual_solvency": True,
            },
            "financial_availability": (company.get("financial_availability") or {}).get("status", "unknown"),
            "next_step": bucket if bucket != "high_priority_manual_review"
            else "manual_lead_approval_required", "bucket": bucket,
            "priority": priority, "outreach_allowed": False,
        })
    return sorted(rows, key=lambda item: (-item["priority"], item["name"].casefold(), item["company"]))

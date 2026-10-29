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
        site = info["site_status"]
        if financial["status"] == "exclude":
            bucket = "excluded_official_status"
            priority = 0
        elif financial["status"] == "promising" and reputation["strong"] and site in {
            "has_website", "confirmed_no_website"
        }:
            bucket = "high_priority_manual_review"
            priority = 4
        elif financial["status"] == "promising" and site == "has_website":
            bucket = "verify_reputation"
            priority = 3
        elif site == "website_not_listed":
            bucket = "verify_website_and_reputation"
            priority = 2
        else:
            bucket = "verify_financials_and_reputation"
            priority = 1
        # Skip any automatic contact claim: the value is always human triage.
        rows.append({
            "company": slug, "name": company.get("name", slug),
            "site_status": site, "reputation_status": reputation["status"],
            "finance_status": financial["status"],
            "financial_availability": (company.get("financial_availability") or {}).get("status", "unknown"),
            "next_step": info["next_step"], "bucket": bucket,
            "priority": priority, "outreach_allowed": False,
        })
    return sorted(rows, key=lambda item: (-item["priority"], item["name"].casefold(), item["company"]))

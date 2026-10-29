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
        activity = info["business_activity"]
        # Business is not judged by stars or number of locations. Website
        # absence is the lead objective; verified activity is the deciding
        # factor for production, unknown activity stays in the review queue.
        if activity["status"] == "inactive":
            bucket, priority = "excluded_inactive_business", 0
        elif site == "confirmed_no_website" and activity["status"] == "active":
            bucket, priority = "no_website_active_priority", 70
        elif site == "confirmed_no_website":
            bucket, priority = "verify_business_activity", 60
        elif site == "website_not_listed" and activity["status"] == "active":
            bucket, priority = "verify_website_absence", 50
        elif site == "website_not_listed":
            bucket, priority = "verify_site_and_activity", 40
        elif activity["status"] == "active":
            bucket, priority = "existing_website_optional_redesign", 30
        else:
            bucket, priority = "existing_website_verify_activity", 20
        # Skip any automatic contact claim: the value is always human triage.
        rows.append({
            "company": slug, "name": company.get("name", slug),
            "site_status": site, "business_activity": activity["status"],
            "reputation_status": reputation["status"],
            "finance_status": financial["status"],
            "indicative_capacity": {
                "score": capacity["score"], "status": capacity["status"],
                "confidence": capacity["confidence"], "signals": capacity["signals"],
                "not_actual_solvency": True,
            },
            "financial_availability": (company.get("financial_availability") or {}).get("status", "unknown"),
            "next_step": bucket if bucket != "no_website_active_priority"
            else "manual_lead_approval_required", "bucket": bucket,
            "priority": priority, "outreach_allowed": False,
        })
    return sorted(rows, key=lambda item: (-item["priority"], item["name"].casefold(), item["company"]))

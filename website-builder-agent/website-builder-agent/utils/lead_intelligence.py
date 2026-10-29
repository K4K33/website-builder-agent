"""Evidence-based B2B prospecting gates; no paid APIs, scraping or speculative finance.

OpenStreetMap omitting a website does NOT prove the business has none.
A high rating requires an independently checked review count/source.
Turnover and operating profit are indicators, not an assertion of cash or budget.
Unknown information stays unknown; it never becomes a zero or negative score.
"""
import re
from datetime import date
from urllib.parse import urlsplit

from utils.quality import canonical_url


def _number(value):
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def _source(value):
    if not isinstance(value, str) or not value.strip():
        return False
    parsed = urlsplit(value.strip())
    return parsed.scheme == "https" and bool(parsed.hostname) and not parsed.username


def review_signal(reputation, today=None, min_rating=4.5, min_count=20):
    """Require traceable, fresh, explicitly human-verified third-party review evidence.

    Manual capture must obey the original provider's access and storage terms.
    No Google Places API content is fetched or stored by this module.
    """
    rep = reputation if isinstance(reputation, dict) else {}
    today = today or date.today()
    score, count = rep.get("rating"), rep.get("review_count")
    reasons = []
    if not (_number(score) and 0 <= score <= 5):
        reasons.append("review_rating_unverified")
    if not (isinstance(count, int) and not isinstance(count, bool) and count >= 0):
        reasons.append("review_count_unverified")
    if not (_source(rep.get("source_url")) and rep.get("verified_by_human") is True):
        reasons.append("review_source_needs_verification")
    try:
        checked = date.fromisoformat(rep["checked_at"])
        if (today - checked).days < 0 or (today - checked).days > 180:
            reasons.append("review_evidence_expired")
    except (KeyError, ValueError, TypeError):
        reasons.append("review_checked_at_missing")
    if reasons:
        return {"status": "unknown", "strong": False, "reasons": reasons}
    strong = score >= min_rating and count >= min_count
    return {"status": "strong" if strong else "weak", "strong": strong,
            "reasons": [] if strong else ["reviews_below_threshold"]}


def financial_signal(financials, estimated_project_eur=1500, today=None):
    """Conservative evidence for prioritization, never a solvency guarantee.

    Public financial figures, if recorded, need a year, official/authorized source URL
    and verified company identity. No data -> needs_review, not no_money.
    """
    today = today or date.today()
    data = financials if isinstance(financials, dict) else {}
    if data.get("legal_status") in {"ended", "bankrupt", "liquidation"}:
        return {"status": "exclude", "reasons": ["company_registration_or_operations_ended"]}
    if data.get("insolvency_proceeding") is True:
        return {"status": "exclude", "reasons": ["registered_insolvency_proceeding"]}
    if not (data.get("legal_status") == "active"
            and _source(data.get("registry_source_url"))
            and data.get("business_id_verified") is True):
        return {"status": "needs_review", "reasons": ["company_identity_or_activity_unverified"]}
    revenue, earnings = data.get("revenue_eur"), data.get("operating_profit_eur")
    year = data.get("financial_year")
    if not (_source(data.get("financial_source_url"))
            and data.get("financial_verified_by_human") is True
            and isinstance(year, int) and not isinstance(year, bool)
            and today.year - 2 <= year <= today.year
            and _number(revenue) and revenue >= 0
            and _number(earnings)):
        return {"status": "needs_review", "reasons": ["recent_financial_statement_not_available"]}
    # An operational filter, not financial advice or a claim of actual ability to pay.
    if revenue >= max(50000, 20 * estimated_project_eur) and earnings > 0:
        return {"status": "promising", "reasons": ["positive_profit_and_sales_scale"]}
    return {"status": "needs_review", "reasons": ["commercial_budget_requires_human_assessment"]}


def site_signal(candidate):
    raw = candidate.get("website") or candidate.get("url") or ""
    if canonical_url(raw):
        return "has_website"
    # OSM absence is not proof. Only explicit human verification upgrades the claim.
    v = candidate.get("site_verification") or {}
    if (isinstance(v, dict) and v.get("confirmed_absent") is True
            and v.get("verified_by_human") is True
            and _source(v.get("source_url"))):
        return "confirmed_no_website"
    return "website_not_listed"


def evaluate_prospect(candidate, estimated_project_eur=1500, today=None):
    site = site_signal(candidate)
    rep = review_signal(candidate.get("reputation"), today=today)
    finance = financial_signal(candidate.get("financials"), estimated_project_eur, today=today)
    # Bad website leads can still enter the existing UI QA pipeline, but never get
    # automatic sales contact until verified financial evidence is present.
    readiness = (
        "priority_for_human_review"
        if finance["status"] == "promising" and (
            site == "has_website" or (site == "confirmed_no_website" and rep["strong"])
        )
        else "verification_pending"
    )
    return {
        "site_status": site,
        "reputation": rep,
        "financial": finance,
        "outreach_gate": readiness,
        "outreach_allowed": False,  # Explicit owner decision remains mandatory.
        "next_step": (
            "verify_reviews_and_website_absence"
            if site != "has_website" and not rep["strong"] else
            "verify_financial_statements"
            if finance["status"] != "promising" else
            "manual_lead_approval_required"
        ),
    }


def finnish_business_id(value):
    """Format only; separate official registry identity match remains mandatory."""
    return isinstance(value, str) and re.fullmatch(r"\d{7}-\d", value.strip()) is not None

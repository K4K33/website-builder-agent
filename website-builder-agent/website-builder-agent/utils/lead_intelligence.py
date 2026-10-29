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


def business_activity_signal(candidate, today=None):
    """Business activity matters; independent evidence required to mark active.

    An OSM listing or a company ID alone is NOT proof of current trading.
    Missing activity evidence is unknown, never automatically 'closed'.
    """
    today = today or date.today()
    facts = candidate.get("financials") or {}
    registry = candidate.get("registry_evidence") or {}
    if (facts.get("legal_status") in {"ended", "bankrupt", "liquidation"}
            or facts.get("insolvency_proceeding") is True
            or registry.get("registration_ended") is True):
        return {"status": "inactive", "source": "registered_inactive_or_insolvency"}
    if (facts.get("legal_status") == "active"
            and facts.get("business_id_verified") is True
            and _source(facts.get("registry_source_url"))):
        return {"status": "active", "source": "verified_registry_status"}

    evidence = candidate.get("activity_evidence") or {}
    if (isinstance(evidence, dict)
            and evidence.get("active") is True
            and evidence.get("verified_by_human") is True
            and _source(evidence.get("source_url"))):
        try:
            checked = date.fromisoformat(evidence["checked_at"])
            if 0 <= (today - checked).days <= 180:
                return {"status": "active", "source": "recent_verified_operation"}
        except (ValueError, KeyError, TypeError):
            pass
    return {"status": "unknown", "source": "activity_needs_verification"}


def _verified_operating_scale(candidate, today=None):
    """Source-checked operational footprint; not a financial statement."""
    today = today or date.today()
    scale = candidate.get("operational_scale") or {}
    if (not isinstance(scale, dict)
            or scale.get("verified_by_human") is not True
            or not _source(scale.get("source_url"))):
        return {}
    try:
        checked = date.fromisoformat(scale["checked_at"])
        if not 0 <= (today - checked).days <= 365:
            return {}
    except (KeyError, ValueError, TypeError):
        return {}
    result = {}
    for key in ("location_count", "employee_count"):
        value = scale.get(key)
        if isinstance(value, int) and not isinstance(value, bool) and 0 <= value <= 100000:
            result[key] = value
    return result


def estimate_purchase_capacity(candidate, estimated_project_eur=1500, today=None):
    """Evidence-backed LEAD PRIORITY heuristic, not ability-to-pay prediction.

    Score 0..100 is an internal order-of-review index, never a probability or
    promise of solvency. No evidence means *unknown*, not a poor company.
    No inferred income, fabricated review counts, or paid/scraped data.
    """
    if not _number(estimated_project_eur) or not 100 <= estimated_project_eur <= 100000:
        raise ValueError("Estimated web project price must be EUR 100..100000")
    today = today or date.today()
    financial = financial_signal(candidate.get("financials"), estimated_project_eur, today=today)
    reviews = review_signal(candidate.get("reputation"), today=today)
    facts = candidate.get("financials") or {}
    reasons, score = [], 0
    if financial["status"] == "exclude":
        return {
            "status": "excluded", "score": 0, "confidence": "official_warning",
            "signals": ["registered_company_inactive_or_insolvency"],
            "estimated_project_eur": estimated_project_eur,
            "can_prioritize": False,
            "disclaimer": "Not a credit score or assessment of actual ability to pay.",
        }

    # Active operations are a much stronger lead signal than review stars.
    activity = business_activity_signal(candidate, today=today)
    if activity["status"] == "active":
        score += 35
        reasons.append("independently_verified_active_operation")

    # Independently confirmed turnover + positive profit is a strong signal.
    if financial["status"] == "promising":
        score += 55
        reasons.append("source_checked_recent_turnover_and_profit")
    elif (financial["status"] == "needs_review"
          and _source(facts.get("financial_source_url"))
          and facts.get("financial_verified_by_human") is True
          and _number(facts.get("operating_profit_eur"))
          and facts["operating_profit_eur"] <= 0):
        reasons.append("recent_non_positive_operating_profit_needs_context")

    # Official identity confirms business existence, not its spending power.
    if (facts.get("business_id_verified") is True
            and _source(facts.get("registry_source_url"))):
        score += 10
        reasons.append("official_company_identity")
        if facts.get("legal_status") == "active":
            score += 10
            reasons.append("active_registry_status")

    # Customer traction gives an *indirect* budget signal, not cash evidence.
    if reviews["strong"]:
        score += 10
        reasons.append("independently_checked_strong_customer_reputation")

    # Optional verified scale signals. OSM tags alone never count as proof.
    scale = _verified_operating_scale(candidate, today=today)
    if scale.get("employee_count", 0) >= 5:
        score += 15
        reasons.append("verified_team_size_at_least_five")

    score = min(100, score)
    evidence_categories = sum((
        financial["status"] == "promising",
        activity["status"] == "active",
        facts.get("business_id_verified") is True and _source(facts.get("registry_source_url")),
        reviews["strong"],
        bool(scale),
    ))
    if score >= 60:
        status = "strong_indicators"
    elif score >= 25:
        status = "some_indicators"
    else:
        status = "insufficient_evidence"
    return {
        "status": status,
        "score": score,
        "confidence": ("higher" if financial["status"] == "promising"
                       else "moderate" if evidence_categories >= 2 else "limited"),
        "signals": reasons,
        "estimated_project_eur": estimated_project_eur,
        "can_prioritize": score >= 25,
        "disclaimer": "A qualitative sales-priority heuristic, not a probability, credit rating, or verified budget.",
    }


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
    capacity = estimate_purchase_capacity(candidate, estimated_project_eur, today=today)
    # Bad website leads can still enter the existing UI QA pipeline, but never get
    # automatic sales contact until verified financial evidence is present.
    activity = business_activity_signal(candidate, today=today)
    readiness = (
        "priority_for_human_review"
        if activity["status"] == "active" and site in {"has_website", "confirmed_no_website"}
        else "verification_pending"
    )
    return {
        "site_status": site,
        "reputation": rep,
        "financial": finance,
        "business_activity": activity,
        "purchase_capacity": capacity,
        "outreach_gate": readiness,
        "outreach_allowed": False,  # Explicit owner decision remains mandatory.
        "next_step": (
            "verify_business_activity" if activity["status"] == "unknown" else
            "verify_website_absence" if site == "website_not_listed" else
            "manual_lead_approval_required"
        ),
    }


def finnish_business_id(value):
    """Format only; separate official registry identity match remains mandatory."""
    return isinstance(value, str) and re.fullmatch(r"\d{7}-\d", value.strip()) is not None

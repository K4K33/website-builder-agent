"""Bounded, no-fee official PRH iXBRL availability lookup.

PRH publishes only a small proportion (~5%) of annual accounts as iXBRL.
The listing contains dates, not trustworthy normalized EUR revenue/profit.
Never infer profitability or cash from availability, absence, company age,
tax registration or turnover elsewhere. The full statement is XML with
taxonomy-dependent definitions; this module DOES NOT interpret those figures.

Official OpenAPI:
https://avoindata.prh.fi/opendata-xbrl-api/v3/schema?lang=fi
"""
from datetime import date
import requests

from utils.lead_intelligence import finnish_business_id

API = "https://avoindata.prh.fi/opendata-xbrl-api/v3/financials"
STATEMENT = "https://avoindata.prh.fi/opendata-xbrl-api/v3/financial"
HEADERS = {"Accept": "application/json",
           "User-Agent": "KaurivoWebsiteBuilder/0.2 (PRH open-data attribution)"}


def available_financial_periods(business_id, timeout=12, max_pages=2):
    """Returns observed periods only. 404/empty is unknown, NOT bad finances.

    Fail on mismatched legal identity, malformed records and pagination
    beyond a small explicitly bounded number of pages.
    """
    if not finnish_business_id(business_id):
        raise ValueError("Finnish business ID format required")
    if not isinstance(max_pages, int) or isinstance(max_pages, bool) or not 1 <= max_pages <= 3:
        raise ValueError("max_pages must be 1..3")
    found = set()
    for page in range(1, max_pages + 1):
        response = requests.get(
            API,
            params={"businessId": business_id, "page": page},
            headers=HEADERS,
            timeout=timeout,
        )
        if response.status_code == 404:
            if page == 1:
                return {"status": "not_available", "financial_dates": [],
                        "source_url": API + "?businessId=" + business_id,
                        "financial_figures_verified": False}
            break
        response.raise_for_status()
        payload = response.json()
        if not isinstance(payload, dict) or not isinstance(payload.get("financials"), list):
            raise RuntimeError("Unexpected PRH financial period response; do not infer figures")
        rows = payload["financials"]
        if not rows:
            break
        for item in rows:
            if not isinstance(item, dict) or item.get("businessId") != business_id:
                raise RuntimeError("PRH financial period identity mismatch")
            stamp = item.get("financialDate")
            try:
                parsed = date.fromisoformat(stamp)
            except (ValueError, TypeError) as exc:
                raise RuntimeError("Invalid period date in PRH response") from exc
            if parsed > date.today():
                raise RuntimeError("Future period date in PRH response")
            found.add(stamp)
        if len(rows) < 100:
            break
    periods = sorted(found, reverse=True)
    return {
        "status": "available" if periods else "not_available",
        "financial_dates": periods,
        "latest_financial_date": periods[0] if periods else None,
        "source_url": API + "?businessId=" + business_id,
        "statement_url": (STATEMENT + "?businessId=" + business_id +
                          "&financialDate=" + periods[0]) if periods else None,
        "financial_figures_verified": False,
        "note": ("Official period metadata only; no revenue or profit parsed. "
                 "Missing data does not indicate weak financial health."),
    }

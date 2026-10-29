"""Explicit, no-fee Finnish PRH/YTJ registry verification.

This is NOT a financial statement API and does not estimate liquidity.
Only call this as an explicitly requested verification, never for all OSM hits.
PRH open data CC BY 4.0; attribute source, avoid PRH/YTJ brand impersonation.
Private traders are outside this particular public open-data API.
"""
import requests

from utils.lead_intelligence import finnish_business_id

BASE = "https://avoindata.prh.fi/opendata-ytj-api/v3/companies"


def lookup_by_business_id(business_id: str, timeout: int = 12):
    if not finnish_business_id(business_id):
        raise ValueError("Valid Finnish Y-tunnus format required.")
    response = requests.get(
        BASE,
        params={"businessId": business_id},
        headers={"Accept": "application/json",
                 "User-Agent": "KaurivoWebsiteBuilder/0.1 (non-commercial validation)"},
        timeout=timeout,
    )
    response.raise_for_status()
    payload = response.json()
    matches = [item for item in payload.get("companies", [])
               if isinstance(item, dict)
               and (item.get("businessId") or {}).get("value") == business_id]
    if len(matches) != 1:
        raise RuntimeError("No unique official PRH company match: do not infer identity.")
    record = matches[0]
    return _to_evidence(record, business_id)


def _to_evidence(record, business_id):
    website = (record.get("website") or {}).get("url", "")
    return {
        "business_id": business_id,
        "official_names": [item["name"] for item in record.get("names", [])
                           if isinstance(item, dict) and item.get("name")],
        "official_website": website if isinstance(website, str) else "",
        "registry_source_url": BASE + "?businessId=" + business_id,
        "business_id_verified": True,
        "registration_ended": bool(record.get("endDate")),
        "company_situations": record.get("companySituations") or [],
        "trade_register_status": record.get("tradeRegisterStatus"),
        "registered_status": record.get("status"),
        # Do not invent active status or revenue from sparse official metadata.
        "legal_status": "unknown",
    }


def lookup_by_name_and_location(name: str, city: str, timeout: int = 12):
    """Exact one-to-one business match. Ambiguous, absent address or similar names fail."""
    if not (isinstance(name, str) and name.strip()
            and isinstance(city, str) and city.strip()):
        raise ValueError("Company name and Finnish city are required for lookup.")
    response = requests.get(
        BASE,
        params={"name": name.strip(), "location": city.strip()},
        headers={"Accept": "application/json",
                 "User-Agent": "KaurivoWebsiteBuilder/0.1 (non-commercial validation)"},
        timeout=timeout,
    )
    response.raise_for_status()
    companies = response.json().get("companies", [])
    exact = []
    for item in companies:
        if not isinstance(item, dict):
            continue
        known_names = [n.get("name", "").strip().casefold()
                       for n in item.get("names", []) if isinstance(n, dict)]
        towns = [post.get("city", "").strip().casefold()
                 for addr in item.get("addresses", []) if isinstance(addr, dict)
                 for post in addr.get("postOffices", []) if isinstance(post, dict)]
        if name.strip().casefold() in known_names and city.strip().casefold() in towns:
            exact.append(item)
    if len(exact) != 1:
        raise RuntimeError("PRH search did not verify one exact company in this city.")
    business_id = (exact[0].get("businessId") or {}).get("value", "")
    if not finnish_business_id(business_id):
        raise RuntimeError("Matched record is missing a valid business ID.")
    result = _to_evidence(exact[0], business_id)
    result["registry_source_url"] = (
        BASE + "?name=" + requests.utils.quote(name.strip()) +
        "&location=" + requests.utils.quote(city.strip())
    )
    return result

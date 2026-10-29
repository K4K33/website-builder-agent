"""No-website prospect research requires externally verified business facts.

Never turn OSM category, PRH registry company name, map ratings or competitor
copy into claimed client services. Owner supplies reviewed source evidence.
This gate intentionally fails closed before paid research/build calls.
"""
from datetime import date
from urllib.parse import urlsplit

from utils.lead_intelligence import site_signal, finnish_business_id
from utils.quality import normalize_facts


def validate_verified_profile(company, profile=None, today=None):
    data = profile if profile is not None else (company.get("company_profile") or {})
    today = today or date.today()
    if site_signal(company) != "confirmed_no_website":
        raise RuntimeError("No-site company must have independently confirmed website absence")
    if not isinstance(data, dict) or data.get("verified_by_human") is not True:
        raise RuntimeError("No-site company profile requires manual factual verification")
    try:
        checked = date.fromisoformat(data["verified_at"])
        if not 0 <= (today - checked).days <= 180:
            raise ValueError()
    except (KeyError, TypeError, ValueError):
        raise RuntimeError("No-site profile verification date missing or expired")
    facts = normalize_facts(data.get("company_facts"))
    name = str(facts.get("name", "")).strip()
    industry = str(facts.get("industry", "")).strip()
    services = facts.get("services") or []
    if (not name or name.casefold() != str(company.get("name", "")).strip().casefold()
        or not industry or not isinstance(services, list) or not services
        or not all(isinstance(item, str) and item.strip() for item in services)):
        raise RuntimeError("Name, industry and documented services required for no-site profile")
    sources = data.get("fact_sources")
    required = {"name", "industry", "services"}
    if not isinstance(sources, dict) or not required.issubset(sources):
        raise RuntimeError("No-site profile requires traceable sources for name, industry, services")
    for field in required:
        urls = sources[field]
        if not isinstance(urls, list) or not urls:
            raise RuntimeError("Missing source for " + field)
        if not all(isinstance(url, str) and urlsplit(url).scheme == "https"
                   and urlsplit(url).hostname for url in urls):
            raise RuntimeError("Invalid HTTPS evidence URL for " + field)
    for key in ("contact_phone", "contact_email", "contact_address", "opening_hours"):
        value = facts.get(key)
        if value and key not in sources:
            raise RuntimeError("Unverified contact/opening-hours field: " + key)
    registry = company.get("registry_evidence") or {}
    id = company.get("business_id")
    if id and (not finnish_business_id(id)
               or not registry or registry.get("business_id") != id):
        raise RuntimeError("Company identity conflicts with saved PRH registry evidence")
    return {"facts": facts, "fact_sources": sources, "verified_at": data["verified_at"]}

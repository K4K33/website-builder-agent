"""
Yksinkertainen JSON-pohjainen tilanhallinta. companies.json toimii
"tietokantana", jossa jokainen yritys on avain (slug) ja arvona sen
koko historia (löytö, research, build, qa, outreach).

Ei riipu ulkoisesta tietokannasta -> helppo committaa Githubiin ja
tarkastella diffinä mitä agentit ovat tehneet.
"""
import json
import os
from slugify import slugify

import config


def _ensure_file():
    os.makedirs(config.DATA_DIR, exist_ok=True)
    if not os.path.exists(config.COMPANIES_FILE):
        with open(config.COMPANIES_FILE, "w", encoding="utf-8") as f:
            json.dump({}, f)


def load_companies() -> dict:
    _ensure_file()
    with open(config.COMPANIES_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_companies(data: dict) -> None:
    _ensure_file()
    with open(config.COMPANIES_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def make_slug(name: str) -> str:
    return slugify(name)


def get_company(slug_or_name: str) -> tuple[str, dict | None]:
    """Hakee yrityksen joko suoralla slugilla tai nimen perusteella (fuzzy)."""
    companies = load_companies()
    slug = make_slug(slug_or_name)
    if slug in companies:
        return slug, companies[slug]
    # yritetään löytää nimen perusteella jos slug ei täsmää suoraan
    for s, c in companies.items():
        if c.get("name", "").lower() == slug_or_name.lower():
            return s, c
    return slug, None


def upsert_company(slug: str, updates: dict) -> dict:
    companies = load_companies()
    existing = companies.get(slug, {})
    existing.update(updates)
    companies[slug] = existing
    save_companies(companies)
    return existing


def set_status(slug: str, status: str) -> None:
    companies = load_companies()
    if slug in companies:
        companies[slug]["status"] = status
        save_companies(companies)

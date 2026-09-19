"""
Yksinkertainen JSON-pohjainen tilanhallinta.

companies.json toimii projektin tietokantana.

Tämä versio osaa käsitellä sekä vanhaa listamuotoa
että nykyistä sanakirjamuotoa, jotta Scoutin jo tallentama
yritys ei katoa eikä Scoutia tarvitse ajaa uudelleen.
"""

import json
import os

from slugify import slugify

import config


def make_slug(name: str) -> str:
    return slugify(
        (name or "").strip()
    )


def _ensure_file():
    os.makedirs(
        config.DATA_DIR,
        exist_ok=True,
    )

    if not os.path.exists(
        config.COMPANIES_FILE
    ):
        with open(
            config.COMPANIES_FILE,
            "w",
            encoding="utf-8",
        ) as f:
            json.dump(
                {},
                f,
                ensure_ascii=False,
                indent=2,
            )


def _normalize_companies(data):
    """
    Muuntaa companies.jsonin aina sanakirjamuotoon.

    Hyväksyy:
    1. nykyisen dict-muodon
    2. vanhan/listamuodon
    """

    if isinstance(
        data,
        dict,
    ):
        return data

    if isinstance(
        data,
        list,
    ):
        normalized = {}

        for company in data:

            if not isinstance(
                company,
                dict,
            ):
                continue

            name = str(
                company.get(
                    "name",
                    "",
                )
            ).strip()

            slug = str(
                company.get(
                    "slug",
                    "",
                )
            ).strip()

            if not slug:
                slug = make_slug(
                    name
                )

            if not slug:
                continue

            company = dict(
                company
            )

            company["slug"] = slug

            normalized[slug] = company

        return normalized

    return {}


def load_companies() -> dict:
    _ensure_file()

    with open(
        config.COMPANIES_FILE,
        "r",
        encoding="utf-8",
    ) as f:

        try:
            data = json.load(f)
        except json.JSONDecodeError:
            data = {}

    normalized = _normalize_companies(
        data
    )

    # Jos vanha listamuoto löytyi,
    # tallennetaan se heti uudessa muodossa.
    if normalized != data:
        save_companies(
            normalized
        )

    return normalized


def save_companies(data: dict) -> None:
    _ensure_file()

    normalized = _normalize_companies(
        data
    )

    with open(
        config.COMPANIES_FILE,
        "w",
        encoding="utf-8",
    ) as f:

        json.dump(
            normalized,
            f,
            ensure_ascii=False,
            indent=2,
        )


def get_company(
    slug_or_name: str,
) -> tuple[str, dict | None]:

    companies = load_companies()

    slug = make_slug(
        slug_or_name
    )

    if slug in companies:
        return (
            slug,
            companies[slug],
        )

    search_name = (
        slug_or_name
        .strip()
        .lower()
    )

    for current_slug, company in (
        companies.items()
    ):

        if (
            str(
                company.get(
                    "name",
                    "",
                )
            )
            .strip()
            .lower()
            == search_name
        ):
            return (
                current_slug,
                company,
            )

    return (
        slug,
        None,
    )


def upsert_company(
    slug: str,
    updates: dict,
) -> dict:

    companies = load_companies()

    existing = companies.get(
        slug,
        {},
    )

    existing.update(
        updates
    )

    existing["slug"] = slug

    companies[slug] = existing

    save_companies(
        companies
    )

    return existing


def set_status(
    slug: str,
    status: str,
) -> None:

    companies = load_companies()

    if slug not in companies:
        return

    companies[slug]["status"] = status

    save_companies(
        companies
    )

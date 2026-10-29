"""
Demo Publisher.

Kopioi rakennetun verkkosivun GitHub Pages -julkaisua varten
docs/demos/<slug>/index.html -hakemistoon.

Tämä vaihe ei käytä AI:ta, Tavilya tai OpenRouteria.
"""

import os
import re
import shutil
import hashlib
from pathlib import Path

import config
from utils.state import (
    get_company,
    upsert_company,
)


PUBLISH_DIR = "docs/demos"

GITHUB_PAGES_BASE = (
    "https://k4k33.github.io/website-builder-agent"
)


def _safe_slug(slug: str) -> str:
    """
    Varmistaa, että slugia voidaan käyttää turvallisesti
    hakemistopolussa.
    """

    if not slug:
        raise RuntimeError(
            "Yrityksen slug puuttuu."
        )

    if not re.fullmatch(
        r"[a-z0-9][a-z0-9-]*",
        slug,
    ):
        raise RuntimeError(
            f"Virheellinen yrityksen slug: {slug}"
        )

    return slug


def _resolve_company(
    slug_or_name: str,
) -> tuple[str, dict]:

    slug, company = get_company(
        slug_or_name
    )

    if company is None:
        raise RuntimeError(
            f"Yritystä ei löytynyt: {slug_or_name}"
        )

    return slug, company


def _source_path(
    slug: str,
    company: dict,
) -> str:

    build = company.get(
        "build",
        {},
    )

    output_path = build.get(
        "output_path"
    )

    if output_path:
        path = output_path
    else:
        path = os.path.join(
            config.OUTPUT_DIR,
            slug,
            "index.html",
        )

    path = os.path.abspath(path)

    if not os.path.isfile(path):
        raise RuntimeError(
            "Rakennettua verkkosivua ei löytynyt: "
            f"{path}"
        )

    return path


def publish_site(
    slug_or_name: str,
) -> str:

    slug, company = _resolve_company(
        slug_or_name
    )

    slug = _safe_slug(slug)

    qa = company.get("qa") or {}
    approval = company.get("approval") or {}
    build = company.get("build") or {}
    if (qa.get("overall_pass") is not True
        or qa.get("build_version") != build.get("version")
        or approval.get("approved") is not True
        or approval.get("build_version") != build.get("version")
        or not qa.get("html_sha256")
        or approval.get("html_sha256") != qa.get("html_sha256")):
        raise RuntimeError("Demoa ei julkaista ilman nykyisen version QA:ta ja hyväksyntää.")
    source = _source_path(slug, company)
    # Prevent copying an arbitrary path from JSON state into the public Pages folder.
    expected = (Path(config.OUTPUT_DIR) / slug / "index.html").resolve()
    if Path(source).resolve() != expected or Path(source).is_symlink():
        raise RuntimeError("Build output path is outside the expected company directory.")
    with open(source, "rb") as source_file:
        actual_sha = hashlib.sha256(source_file.read()).hexdigest()
    if actual_sha != qa["html_sha256"]:
        raise RuntimeError("HTML changed since QA; refuse to publish a stale approval.")

    destination_dir = os.path.join(
        PUBLISH_DIR,
        slug,
    )

    destination = os.path.join(
        destination_dir,
        "index.html",
    )

    os.makedirs(
        destination_dir,
        exist_ok=True,
    )

    shutil.copy2(
        source,
        destination,
    )

    demo_url = (
        f"{GITHUB_PAGES_BASE}/demos/{slug}/"
    )

    upsert_company(
        slug,
        {
            "demo": {
                "path": destination,
                "url": demo_url,
                "published": True,
            }
        },
    )

    print()
    print(
        "========================================"
    )
    print(
        " DEMO JULKAISTU"
    )
    print(
        "========================================"
    )
    print()
    print(
        f"Yritys: {company.get('name', '')}"
    )
    print(
        f"Tiedosto: {destination}"
    )
    print()
    print(
        "Demo-URL:"
    )
    print(
        demo_url
    )
    print()
    print(
        "Huomio: URL toimii selaimessa sen jälkeen,"
    )
    print(
        "kun GitHub Pages on otettu käyttöön ja"
    )
    print(
        "docs-kansio on julkaistu GitHubiin."
    )
    print()

    return demo_url


def run_publish(
    slug_or_name: str,
) -> str:

    return publish_site(
        slug_or_name
    )

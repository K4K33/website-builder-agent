"""Kaurivo company-sector recognition checks and repeatable-layout signals.

Static HTML cannot certify whether a site visually resembles a university.
Two independently checked, exact-build logo-masked visual reviews are required.
"""
from __future__ import annotations

import re
from bs4 import BeautifulSoup
from utils.industry_workflow import sector_guidance
from utils.content_parity import source_inventory_sha256
from utils.premium_quality_gate import site_digest

BICYCLE_WORDS = re.compile(r"\b(?:pyör\w*|polkupyör\w*|fillar\w*|bicycle\w*|bikes?\b|cycling\b)", re.I)


def intro_text(html: str) -> str:
    soup = BeautifulSoup(html, "html.parser")
    main = soup.find("main")
    if main is None:
        return ""
    section = main.find(["section", "article"], recursive=False) or main
    pieces = section.find_all(["h1", "h2", "p", "a"], limit=5)
    return " ".join(piece.get_text(" ", strip=True) for piece in pieces)[:900]


def repeated_text_strips(html: str) -> list[dict]:
    soup = BeautifulSoup(html, "html.parser")
    main = soup.find("main")
    if not main:
        return []
    sections = main.find_all("section", recursive=False)
    if not sections:
        sections = main.find_all("section", limit=16)
    records = []
    for section in sections:
        if section.find(["img", "picture", "video", "table", "form"]):
            records.append(None)
            continue
        signature = (
            min(len(section.find_all(["h1", "h2", "h3"])), 3),
            min(len(section.find_all("p")), 4),
            min(len(section.find_all(["article", "li"])), 5),
        )
        records.append(signature if signature[0] > 0 and signature[2] <= 2 else None)
    warnings = []
    index = 0
    while index < len(records):
        sig = records[index]
        end = index + 1
        while sig is not None and end < len(records) and records[end] == sig:
            end += 1
        if sig is not None and end - index >= 3:
            warnings.append({"first": index + 1, "count": end - index})
        index = end
    return warnings


def check_blind_sector_reviews(records: object, pages: dict[str, str],
                               research: dict, sector: str) -> dict:
    if not isinstance(records, list):
        records = []
    source = research.get("source_inventory") or {}
    source_hash = source_inventory_sha256(source) if source.get("pages") else ""
    build_hash = site_digest(pages)
    valid = set()
    for record in records:
        if not isinstance(record, dict):
            continue
        reviewer = str(record.get("reviewer_id") or "").strip()
        if (not reviewer or record.get("reviewer_kind") not in
            ("independent_human", "external_ai")
            or record.get("independence_human_verified") is not True
            or record.get("logo_masked") is not True
            or record.get("recognized_service") is not True
            or record.get("wrong_industry_impression") is not False
            or record.get("brand_cues_recognized") is not True
            or record.get("company_specific_layout") is not True
            or record.get("build_sha256") != build_hash
            or (source_hash and record.get("source_sha256") != source_hash)
            or not str(record.get("evidence_reference") or "").strip()):
            continue
        if sector != "other" and record.get("recognized_sector") != sector:
            continue
        if sector == "other" and not str(record.get("recognized_sector") or "").strip():
            continue
        if set(record.get("routes_reviewed") or []) != set(pages):
            continue
        widths = record.get("viewport_widths") or []
        if not isinstance(widths, list) or not {320, 390, 768, 1440}.issubset(
            {w for w in widths if type(w) is int}
        ):
            continue
        valid.add(reviewer)
    return {"pass": len(valid) >= 2, "reviewers": len(valid),
            "source_sha256": source_hash, "build_sha256": build_hash}


def audit_sector_presence(pages: dict[str, str], research: dict | None = None) -> dict:
    research = research or {}
    facts = research.get("company_facts") or {}
    industry = str(facts.get("industry") or "")
    sector = sector_guidance(industry)["sector"]
    first = pages.get("index.html", next(iter(pages.values()), ""))
    opening = intro_text(first)
    blocked = []
    if sector == "bicycle" and not BICYCLE_WORDS.search(opening):
        blocked.append({
            "category": "missing_bicycle_first_view",
            "excerpt": opening[:180],
            "issue": "Bicycle service or sales must be obvious in the first content.",
        })
    bands = {route: repeated_text_strips(html) for route, html in pages.items()}
    blind = check_blind_sector_reviews(
        research.get("sector_identity_blind_reviews"), pages, research, sector
    )
    pending = []
    if not blind["pass"]:
        pending.append("Two independent exact-build logo-masked first-impression reviews required: correct business, sector, original brand and distinctive layout, all routes and four widths.")
        if any(bands.values()):
            pending.append("Repeated text-only section strips need human visual rhythm review.")
    return {"pass": not blocked and not pending, "blocking": blocked,
            "pending": pending, "sector": sector, "first_view": opening[:350],
            "repeated_text_strips": bands, "blind_review": blind,
            "note": "Static text and section shape are not proof of visual sector identity."}

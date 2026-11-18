"""Catch unsupported date relabeling across unrelated Kaurivo client sites.

A company's year of starting operations is not its legal registration year.
Use exact dated evidence, not a generic business-directory date interpreted
as incorporation. This detects one objective class of factual omission/error.
A PASS here never establishes full source fidelity or source authenticity.
"""
from __future__ import annotations

import re

from bs4 import BeautifulSoup

YEAR = r"(?:19[0-9]{2}|20[0-9]{2})"
STARTED = re.compile(
    r"(?:toiminta(?:n)?\s+käynnistynyt|toiminta\s+alkanut|"
    r"aloittanut\s+toimintansa|business\s+(?:operations\s+)?started)"
    r"\s*(?:vuonna\s*)?(" + YEAR + r")", re.I
)
REGISTERED = re.compile(
    r"(?:yritys\s+rekisteröity|rekisteröity|perustettu|"
    r"(?:company\s+)?registered|incorporated|founded)"
    r"\s*(?:vuonna\s*)?(" + YEAR + r")", re.I
)


def _evidence_text(research: dict) -> str:
    lines = []
    for page in ((research.get("source_inventory") or {}).get("pages") or []):
        if isinstance(page, dict):
            lines.append(str(page.get("text") or ""))
    for fact in (research.get("fact_sources") or []):
        if not isinstance(fact, dict):
            continue
        # Explicitly labeled date evidence may come from verified third-party
        # registers even if the original business website is inaccessible.
        kind = fact.get("kind")
        value = fact.get("value")
        if kind == "operations_started_year" and str(value).isdigit():
            lines.append("Toiminta käynnistynyt " + str(value))
        if kind == "registration_year" and str(value).isdigit():
            lines.append("Yritys rekisteröity " + str(value))
        for field in ("quote", "excerpt", "text"):
            if fact.get(field):
                lines.append(str(fact[field]))
    return "\n".join(lines)


def audit_temporal_claims(rendered_pages: dict[str, str], research: dict) -> dict:
    source = _evidence_text(research or {})
    started = set(STARTED.findall(source))
    legal = set(REGISTERED.findall(source))
    issues = []
    if not started:
        return {"pass": True, "issues": [], "source_operations_years": []}
    for route, html in rendered_pages.items():
        text = BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
        claims = set(REGISTERED.findall(text))
        for year in sorted((claims & started) - legal):
            issues.append(
                f"{route}: {year} was evidenced as business operations start, "
                "not as incorporation/registration. Verify distinct legal date."
            )
    return {"pass": not issues, "issues": issues,
            "source_operations_years": sorted(started)}

"""Bounded, source-safe correction of invented numeric copy in private prototypes.

This module never declares an unverifiable claim true. The production content
validator remains the authority and is rerun after each small change.
"""
import re
from bs4 import BeautifulSoup


_NUMERIC_CLAIM_PATTERNS = (
    r"(?:yli\s+)?\d+\s+vuoden kokem\w*",
    r"perustettu\s+\d{4}",
    r"vuodesta\s+\d{4}",
    r"yli\s+\d+\s+(?:asiakka|ammattila)\w*",
)
_REJECTED_FACT_MARKER = "keksitty yritysfakta:"


def _remove_exact_unverified_claim(html, claim, verified_name=""):
    if not any(re.fullmatch(pattern, claim, flags=re.I)
               for pattern in _NUMERIC_CLAIM_PATTERNS):
        raise RuntimeError("Unsupported numeric claim correction was rejected")

    document = BeautifulSoup(html, "html.parser")
    candidates = []
    for tag in document.select("main h1,main h2,main h3,main h4,main p,main li,"
                               "main figcaption,main span,main strong,main em,main a,"
                               "main div,main section"):
        visible = " ".join(tag.stripped_strings)
        if claim.casefold() in visible.casefold():
            candidates.append((len(visible), tag, visible))
    if not candidates:
        raise RuntimeError("Unsupported numeric claim was not isolated in visible copy")

    # Prefer the smallest copy element so the surrounding source-backed
    # brand, navigation, services and full page structure are retained.
    _, tag, visible = min(candidates, key=lambda candidate: candidate[0])
    remaining = re.sub(re.escape(claim), "", visible, flags=re.I)
    remaining = remaining.strip(" \t\n,;:|·–-")
    if remaining:
        tag.clear()
        tag.append(remaining)
    elif tag.name == "h1":
        tag.clear()
        tag.append(verified_name or "Tietoa yrityksestä")
    else:
        tag.decompose()

    # Never leave a blank primary heading when a nested unsupported claim
    # carried its complete copy (e.g. <h1><span>Yli 30...</span></h1>).
    for primary in document.select("main h1"):
        if not primary.get_text(" ", strip=True):
            primary.string = verified_name or "Tietoa yrityksestä"
    return str(document)


def prepare_verified_concept_copy(html, facts, validator, *, max_fixes=5):
    """Recover only named unsupported numeric claims and revalidate everything.

    Unknown validator errors, fabricated services, bad contacts and unsafe
    documents are still failures; they are never silently removed or approved.
    """
    result = html
    brand = str(facts.get("name") or facts.get("company_name")
                or facts.get("business_name") or "").strip()
    for _ in range(max_fixes):
        try:
            validator(result, facts)
            return result
        except RuntimeError as error:
            message = str(error)
            if _REJECTED_FACT_MARKER not in message:
                raise
            claim = message.split(_REJECTED_FACT_MARKER, 1)[1].strip()
            corrected = _remove_exact_unverified_claim(result, claim, brand)
            if corrected == result:
                raise
            result = corrected
    validator(result, facts)
    return result

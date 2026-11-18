"""Evidence-based unseen-company V7 measurement.

Do NOT count synthetic fixtures, repeated revisions of the same client or model
self-ratings as a real-world blind test. This evaluates submitted genuine records;
it cannot independently attest that a human or screenshot is authentic.
"""
from __future__ import annotations
from pathlib import Path
import hashlib

DIMENSIONS = {
    "brand_authenticity": 20,
    "composition": 20,
    "typography": 15,
    "media_motion": 15,
    "mobile_usability": 10,
    "natural_copy": 10,
    "micro_details": 10,
}
VIEWPORTS = ("mobile", "tablet", "desktop")
MIN_CLIENTS = 5


def weighted_quality_score(dimensions: dict) -> float | None:
    """Only score a complete reviewer record; no invented missing dimensions."""
    if not isinstance(dimensions, dict) or set(dimensions) != set(DIMENSIONS):
        return None
    for value in dimensions.values():
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not 0 <= value <= 10:
            return None
    return round(sum(dimensions[key] * weight for key, weight in DIMENSIONS.items()) / 100, 2)


def validate_blind_record(record: dict, *, evidence_root: Path) -> list[str]:
    if not isinstance(record, dict):
        return ["Review record missing."]
    errors = []
    for key in ("company_id", "industry", "source_url", "preview_url",
                "build_sha256", "source_sha256", "reviewer_id"):
        if not isinstance(record.get(key), str) or not record[key].strip():
            errors.append("Missing independently checkable " + key)
    for key in ("build_sha256", "source_sha256"):
        value = record.get(key)
        if not isinstance(value, str) or len(value) != 64 or not all(c in "0123456789abcdef" for c in value.lower()):
            errors.append("Invalid exact-build/source digest " + key)
    if record.get("synthetic") is not False or record.get("first_attempt") is not True:
        errors.append("Only actual first-attempt real companies count.")
    if record.get("reviewer_kind") not in ("independent_human", "external_review_service"):
        errors.append("Builder or its own QA model is not an independent reviewer.")
    if record.get("critical_issues") != []:
        errors.append("Critical issues remain unresolved.")
    quality = weighted_quality_score(record.get("dimensions"))
    if quality is None:
        errors.append("Complete scored design dimensions missing.")
    ai_look = record.get("ai_looking_risk")
    if (isinstance(ai_look, bool) or not isinstance(ai_look, (int, float))
            or not 0 <= ai_look <= 10):
        errors.append("AI-looking risk must be independently observed on a 0–10 scale.")
    sources = record.get("screenshots") or {}
    try:
        root = evidence_root.resolve()
        for page in ("original", "preview"):
            images = sources[page]
            for viewport in VIEWPORTS:
                raw = images[viewport]
                if not isinstance(raw, str):
                    raise ValueError("Screenshot path missing")
                file = (root / raw).resolve()
                if not file.is_relative_to(root) or not file.is_file() or file.stat().st_size < 24:
                    raise ValueError(f"Missing actual {page}/{viewport} screenshot")
                if file.read_bytes()[:8] != b"\x89PNG\r\n\x1a\n":
                    raise ValueError(f"{page}/{viewport} screenshot is not PNG")
        # File existence does not certify human observation: retained manifest
        # hash and independent review still must be verified externally.
    except (KeyError, TypeError, ValueError, OSError) as exc:
        errors.append(str(exc))
    if record.get("live_browser_verified") is not True:
        errors.append("Actual hosted customer route has not been live-browser verified.")
    return errors


def assess_blind_campaign(records: list[dict], *, evidence_root: Path) -> dict:
    """Never turn five versions of one site into five independent customers."""
    seen, sectors, valid, invalid = set(), set(), [], []
    for index, row in enumerate(records if isinstance(records, list) else []):
        issues = validate_blind_record(row, evidence_root=evidence_root)
        identity = str(row.get("company_id") or "").strip().casefold() if isinstance(row, dict) else ""
        sector = str(row.get("industry") or "").strip().casefold() if isinstance(row, dict) else ""
        if identity in seen or (identity and not issues and sector in sectors):
            issues.append("Requires distinct first-run company and sector, not another variant.")
        if issues:
            invalid.append({"index": index, "issues": issues})
        else:
            seen.add(identity)
            sectors.add(sector)
            valid.append(row)
    return {
        "status": "FIVE_REAL_COMPANIES_EVIDENCED" if len(valid) >= MIN_CLIENTS else "NOT_PROVEN",
        "valid_distinct_companies": len(valid),
        "distinct_sectors": len(sectors),
        "required": MIN_CLIENTS,
        "invalid_records": invalid,
        "quality_scores": [
            weighted_quality_score(row["dimensions"]) for row in valid
        ],
        "ai_looking_risks": [row["ai_looking_risk"] for row in valid],
        "9_5_maturity_achieved": (
            len(valid) >= MIN_CLIENTS
            and all((weighted_quality_score(row["dimensions"]) or 0) >= 9.5 for row in valid)
            and all(row["ai_looking_risk"] <= 2 for row in valid)
        ),
        "note": "This is a record/schema evidence checker, not an external human-authenticity verifier. Independently examine actual sites and source proof.",
    }

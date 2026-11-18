"""Evidence-bound final fact gate for Kaurivo's commercial demo outreach.

An owner saying the design looks good is NOT a statement that the business
facts, original site, photos, CTA destinations or proposed email are correct.

This offline checker verifies that a separate, human-reviewed fact-check record
is current for the exact built and QA-approved website. It cannot independently
authenticate external evidence; the reviewer must open and verify each source.
Do not put recipient addresses or private contact data in public GitHub files.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from hashlib import sha256
import json
from urllib.parse import urlsplit


REQUIRED_AREAS = (
    "business_identity",
    "services_and_scope",
    "public_contact_details",
    "original_content_coverage",
    "brand_and_media_rights",
    "reviews_and_credibility",
    "customer_actions",
    "outreach_claims",
)
OPTIONAL_WHEN_ABSENT = {"reviews_and_credibility", "brand_and_media_rights"}
MAX_AGE = timedelta(days=7)


def research_fingerprint(research: dict) -> str:
    """Invalidate old approval if any source/company fact or coverage map changes."""
    if not isinstance(research, dict):
        research = {}
    watched = {
        key: research.get(key) for key in (
            "source_inventory", "source_content_map", "company_facts",
            "fact_sources", "content_requirements", "current_site_weaknesses",
            "design_decisions", "no_site_fact_review",
        )
    }
    raw = json.dumps(watched, ensure_ascii=False, sort_keys=True, default=str)
    return sha256(raw.encode("utf-8")).hexdigest()


def _date(value: object, *, now: datetime) -> bool:
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
        return bool(dt.tzinfo and now - MAX_AGE <= dt <= now)
    except (ValueError, TypeError, OverflowError):
        return False


def _source(value: object) -> bool:
    try:
        parsed = urlsplit(value)
        return bool(parsed.scheme == "https" and parsed.hostname
                    and not parsed.username and not parsed.password)
    except (TypeError, ValueError):
        return False


def inspect_sales_fact_review(company: dict, *, now: datetime | None = None) -> dict:
    """Fail closed on a missing/stale/partial fact review; NEVER send a message."""
    now = now or datetime.now(timezone.utc)
    issues = []
    if not isinstance(company, dict):
        return {"ready": False, "issues": ["No company record."]}
    review = company.get("sales_fact_review")
    if not isinstance(review, dict):
        return {"ready": False, "issues": ["Final sales fact review missing after design approval."]}

    build = company.get("build") or {}
    qa = company.get("qa") or {}
    approval = company.get("approval") or {}
    research = company.get("research") or {}
    if (approval.get("approved") is not True
            or qa.get("overall_pass") is not True
            or approval.get("build_version") != build.get("version")
            or qa.get("build_version") != build.get("version")):
        issues.append("Current website needs completed QA and owner design approval.")
    for label in ("html_sha256", "site_sha256"):
        digest = qa.get(label)
        if not isinstance(digest, str) or len(digest) < 8:
            issues.append("Missing current QA bundle digest: " + label)
        elif approval.get(label) != digest or review.get(label) != digest:
            issues.append("Fact review does not match the current QA-approved build: " + label)
    if review.get("build_version") != build.get("version"):
        issues.append("Fact review belongs to another build version.")
    if review.get("research_sha256") != research_fingerprint(research):
        issues.append("Research/source facts have changed since the fact review.")
    if review.get("reviewer_kind") != "human" or not str(review.get("reviewer") or "").strip():
        issues.append("Named human reviewer must verify sources and rendered site.")
    if not _date(review.get("checked_at"), now=now):
        issues.append("Fact review missing, future-dated or older than seven days.")
    if review.get("status") != "verified":
        issues.append("Final fact review is not verified.")
    if review.get("missing_or_changed_facts") != []:
        issues.append("Unresolved, removed or changed company facts remain.")
    if review.get("unresolved_issues") != []:
        issues.append("Unresolved factual, media, content or functional issues remain.")

    # A directory's registration category is not proof of the actual services
    # or original branding. An unreachable original site is NOT 'no website'.
    inventory = (research.get("source_inventory") or {}).get("pages") or []
    original_status = review.get("original_site_status")
    if original_status == "confirmed_no_website":
        no_site = research.get("no_site_fact_review") or {}
        if (no_site.get("approved") is not True
                or no_site.get("reviewer_kind") != "human"
                or not str(no_site.get("source_url") or "").startswith("https://")):
            issues.append("A no-website claim needs independent recorded evidence.")
    elif original_status == "verified_existing_website":
        if not any(isinstance(p, dict) and _source(p.get("url")) for p in inventory):
            issues.append("Existing website source inventory is missing or inaccessible.")
    else:
        issues.append("Original website status unresolved. DNS failure is not evidence of no website.")

    fields = review.get("areas")
    if not isinstance(fields, dict):
        fields = {}
    for name in REQUIRED_AREAS:
        row = fields.get(name)
        if not isinstance(row, dict):
            issues.append("Fact check area not reviewed: " + name)
            continue
        status = row.get("status")
        if status == "not_applicable":
            permitted = name in OPTIONAL_WHEN_ABSENT or (
                name == "original_content_coverage" and original_status == "confirmed_no_website")
            if not permitted or len(str(row.get("reason") or "").strip()) < 12:
                issues.append("Unjustified omitted fact check area: " + name)
        elif status != "verified" or not _source(row.get("source_url")):
            issues.append("Missing reliable current source evidence: " + name)
        if not _date(row.get("checked_at"), now=now):
            issues.append("Fact check area was not reviewed recently: " + name)

    expected_routes = build.get("page_paths") or ["index.html"]
    reviewed = review.get("reviewed_routes")
    if (not isinstance(expected_routes, list)
            or not all(isinstance(r, str) and r.strip() for r in expected_routes)
            or not isinstance(reviewed, list)
            or len(reviewed) != len(expected_routes)
            or set(reviewed) != set(expected_routes)):
        issues.append("Final review must cover every route in the current website.")

    # Issues found at any stage must have an auditable resolution. Store a
    # reusable regression test identifier for a structural omission, so the
    # same missing information cannot simply recur in the next demo.
    history = review.get("corrections")
    if not isinstance(history, list):
        issues.append("Correction history must be recorded, even if empty.")
    else:
        for index, item in enumerate(history):
            if not isinstance(item, dict) or item.get("status") != "fixed" or not str(item.get("evidence") or "").strip():
                issues.append(f"Correction {index + 1} is not proven fixed.")
            elif item.get("reusable_rule") is True and not str(item.get("regression_test") or "").strip():
                issues.append(f"Correction {index + 1} lacks a reusable regression test.")

    return {"ready": not issues, "status": "FACT_VERIFIED" if not issues else "HOLD",
            "issues": list(dict.fromkeys(issues)), "checked_areas": len(REQUIRED_AREAS)}

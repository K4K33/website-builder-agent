"""Sale-stage visual acceptance, deliberately independent of the 9.5/10 goal.

Kaurivo's 9.5 external benchmark measures long-term agency maturity; it is
NOT a prerequisite to offer an already excellent and carefully reviewed
individual website. Sale-stage acceptance remains fail-closed for real defects,
missing source comparison, review scope or stale build evidence.

This checker does not review screenshots itself. A real owner must inspect
the recorded screenshots, evidence and complete site, and record the result.
A score, when present, is diagnostic and does not automatically pass a site.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from utils.content_parity import source_inventory_sha256

VIEWPORTS = (390, 1440)
MAX_REVIEW_AGE = timedelta(days=30)


def assess_commercial_visual_review(
    review: dict | None, *, site_sha256: str,
    routes: list[str] | set[str], source_inventory: dict | None = None,
    now: datetime | None = None,
) -> dict:
    review = review if isinstance(review, dict) else {}
    now = now or datetime.now(timezone.utc)
    problems = []
    if not isinstance(site_sha256, str) or len(site_sha256) != 64:
        problems.append("Reviewed website bundle digest missing.")
    if review.get("site_sha256") != site_sha256:
        problems.append("Owner visual review is missing or belongs to another website build.")
    if review.get("approved") is not True:
        problems.append("Owner has not accepted the current visual design.")
    if review.get("reviewer_kind") != "human" or not str(review.get("reviewer") or "").strip():
        problems.append("Named real owner/reviewer is required.")
    if not str(review.get("evidence_reference") or "").strip():
        problems.append("Rendered visual comparison evidence is missing.")
    try:
        checked = datetime.fromisoformat(str(review.get("checked_at")).replace("Z", "+00:00"))
        if not checked.tzinfo or checked > now or now - checked > MAX_REVIEW_AGE:
            raise ValueError("stale")
    except (ValueError, TypeError, OverflowError):
        problems.append("Review time must be recent and timezone-aware.")
    expected_routes = set(routes or [])
    if not expected_routes or set(review.get("routes_reviewed") or []) != expected_routes:
        problems.append("Owner must inspect every real route, including substantive subpages.")
    inspected_widths = review.get("viewports_reviewed")
    if (not isinstance(inspected_widths, list)
            or not all(isinstance(w, int) and not isinstance(w, bool) for w in inspected_widths)
            or not any(w <= 430 for w in inspected_widths)
            or not any(w >= 1200 for w in inspected_widths)):
        problems.append("Actual mobile and desktop views were not both inspected.")
    if review.get("critical_issues") != []:
        problems.append("Unresolved serious visual, usability or credibility defects remain.")
    for field in ("source_comparison_reviewed", "brand_and_media_reviewed",
                  "readability_and_mobile_reviewed", "commercial_journey_reviewed"):
        if review.get(field) is not True:
            problems.append("Missing owner visual acceptance check: " + field)
    sources = source_inventory if isinstance(source_inventory, dict) else {}
    if sources.get("pages") and review.get("source_sha256") != source_inventory_sha256(sources):
        problems.append("Visual acceptance does not match the latest original-site source evidence.")
    return {"approved": not problems,
            "status": "VISUALLY_APPROVED_FOR_SALES" if not problems else "HOLD",
            "issues": problems,
            "goal_9_5_is_required": False,
            "note": "No numeric score or portfolio size is an automatic sales gate. Actual quality and rights checks remain required."}

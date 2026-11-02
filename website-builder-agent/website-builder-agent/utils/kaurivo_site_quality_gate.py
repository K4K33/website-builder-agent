"""Kaurivo: offline copy checks and evidence-based external quality acceptance.

Uses no AI/network/credits. Never self-rates website design. An external
rating must be obtained independently and reviewed by a human.
Passing this gate is not proof of CMS, legal permission or client acceptance.
"""
from __future__ import annotations

from collections import Counter
from datetime import date
from pathlib import Path
import re

from bs4 import BeautifulSoup

CONTRAST_PATTERNS = (
    re.compile(r"\\bvähemmän\\b.{0,140}\\benemmän\\b|\\benemmän\\b.{0,140}\\bvähemmän\\b", re.I),
    re.compile(r"\\bei\\s+(?:vain|pelkästään)\\b.{0,130}\\bvaan\\b", re.I),
    re.compile(r"\\bnot\\s+(?:only|just)\\b.{0,130}\\bbut\\b", re.I),
)
MIN_INDEPENDENT_SCORE = 9.5
MIN_REFERENCE_CLIENTS = 3


def lint_site_copy(html_pages: dict[str, str], *, max_contrasts: int = 1) -> dict:
    """Detect repetitive copy and total contrast-pair usage across a SITE.

    Do not score visual design via regex: this catches only objective
    copy-writing patterns and requires separate editorial/browser review.
    """
    if not html_pages:
        return {"pass": False, "contrast_count": 0,
                "issues": ["No HTML pages provided for copy audit."]}
    contrast_count = 0
    contrast_examples: list[str] = []
    paragraphs: list[tuple[str, str]] = []
    issues: list[str] = []
    for page, html in html_pages.items():
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript", "header", "footer", "nav"]):
            tag.decompose()
        for elem in soup.select("h1,h2,h3,p"):
            raw = " ".join(elem.stripped_strings)
            raw = " ".join(raw.split())
            if not raw:
                continue
            if any(pattern.search(raw) for pattern in CONTRAST_PATTERNS):
                contrast_count += 1
                contrast_examples.append(f"{page}: {raw[:160]}")
            if elem.name == "p" and len(raw) >= 80:
                paragraphs.append((page, raw.casefold()))
    if contrast_count > max_contrasts:
        issues.append(
            f"Contrast-pair formula repeated sitewide {contrast_count} times, "
            f"limit {max_contrasts}: " + " | ".join(contrast_examples)
        )
    collisions = Counter(text for _page, text in paragraphs)
    for text, count in collisions.items():
        if count > 1:
            issues.append(f"Repeated paragraph across the site ({count}x): {text[:130]}")
    return {"pass": not issues, "contrast_count": contrast_count, "issues": issues}


def lint_site_directory(root: Path) -> dict:
    pages = {}
    for path in sorted(root.rglob("*.html")):
        if path.name != "index.html":
            continue
        pages[str(path.relative_to(root))] = path.read_text(encoding="utf-8")
    return lint_site_copy(pages)


def _review_issues(entry: dict) -> list[str]:
    """Review data may be untrusted. We check shape, not authenticity.

    An independent human must validate the reviewer source and supplied
    video/browser evidence before recording an approval.
    """
    issues = []
    name = entry.get("client_project_id")
    if not isinstance(name, str) or len(name.strip()) < 3:
        issues.append("Missing verifiable project id.")
    if entry.get("reviewer_kind") != "external_ai":
        issues.append("Review did not come from an independent external AI.")
    if entry.get("independence_human_verified") is not True:
        issues.append("Independent reviewer provenance not verified by a human.")
    reviewer = entry.get("reviewer_model")
    if not isinstance(reviewer, str) or len(reviewer.strip()) < 4:
        issues.append("Missing actual reviewer model identifier.")
    evidence = entry.get("evidence_reference")
    if not isinstance(evidence, str) or len(evidence.strip()) < 8:
        issues.append("No retrievable evidence reference for reviewer output.")
    try:
        reviewed = date.fromisoformat(entry["review_date"])
        if reviewed > date.today():
            issues.append("Review date is in the future.")
    except (ValueError, TypeError, KeyError):
        issues.append("Invalid review date.")
    commit = entry.get("reviewed_build")
    if not isinstance(commit, str) or len(commit.strip()) < 8:
        issues.append("Missing pinned reviewed build.")
    rating = entry.get("overall_score")
    if isinstance(rating, bool) or not isinstance(rating, (int, float)) or not 0 <= rating <= 10:
        issues.append("Invalid external rating.")
    elif rating < MIN_INDEPENDENT_SCORE:
        issues.append(f"External review {rating}/10 is below {MIN_INDEPENDENT_SCORE}/10.")
    pages = entry.get("pages_reviewed")
    if isinstance(pages, bool) or not isinstance(pages, int) or pages < 3:
        issues.append("Reviewer saw fewer than 3 real pages.")
    widths = entry.get("viewports_reviewed")
    if (not isinstance(widths, list)
            or not all(isinstance(w, int) and not isinstance(w, bool) for w in widths)
            or not any(w <= 430 for w in widths)
            or not any(w >= 1200 for w in widths)):
        issues.append("Both real mobile and desktop reviews required.")
    if entry.get("critical_issues") != []:
        issues.append("At least one critical issue remains or status is unknown.")
    if entry.get("sitewide_copy_check_passed") is not True:
        issues.append("Sitewide copy audit has not passed.")
    if entry.get("real_browser_checks_passed") is not True:
        issues.append("Real cross-viewport browser QA has not passed.")
    if entry.get("image_rights_checked") is not True:
        issues.append("Image licensing/source checks incomplete.")
    return issues


def assess_quality_consistency(reviews: list[dict], *, current_project_id: str,
                               reference_clients: int = MIN_REFERENCE_CLIENTS) -> dict:
    """Fail closed: >=9.5 on this site AND recent >=3 distinct client sites.

    A single excellent client demo cannot certify the *agency-wide* process.
    Review metadata is not cryptographically authenticated. Human verification
    is mandatory and must never be fabricated for tests or sales claims.
    """
    if not isinstance(reviews, list):
        reviews = []
    valid = [r for r in reviews if isinstance(r, dict)]
    current = [r for r in valid if r.get("client_project_id") == current_project_id]
    problems = []
    if not current:
        problems.append("Current client has no independent external AI review.")
    else:
        latest = sorted(current, key=lambda x: str(x.get("review_date", "")))[-1]
        problems.extend(_review_issues(latest))
    by_project = {}
    for r in valid:
        project = r.get("client_project_id")
        if isinstance(project, str) and project.strip():
            if project not in by_project or str(r.get("review_date", "")) >= str(by_project[project].get("review_date", "")):
                by_project[project] = r
    recent = sorted(by_project.values(), key=lambda x: str(x.get("review_date", "")), reverse=True)[:reference_clients]
    if len(recent) < reference_clients:
        problems.append(
            f"Agency-wide benchmark needs at least {reference_clients} distinct "
            f"client demos; currently {len(recent)} reviewed."
        )
    for r in recent:
        issues = _review_issues(r)
        if issues:
            problems.append(f"{r.get('client_project_id', '?')}: " + "; ".join(issues))
    return {
        "accepted": not problems,
        "status": "PASS" if not problems else "HOLD",
        "required_independent_score": MIN_INDEPENDENT_SCORE,
        "distinct_project_sample_size": len(recent),
        "required_distinct_project_sample_size": reference_clients,
        "issues": list(dict.fromkeys(problems)),
        "note": (
            "Independent reviewer evidence must be human-validated; "
            "this is not a model-generated score, legal clearance or customer sign-off."
        ),
    }

"""Evidence-aware premium acceptance matrix for every Kaurivo client.

These offline checks never invent subjective scores or fabricate live metrics.
Builds may be previewed with pending proofs; client-ready requires real,
source-bound independent review and field performance evidence.
"""
from __future__ import annotations

import hashlib
from pathlib import Path
from urllib.parse import urlsplit, urljoin

from bs4 import BeautifulSoup

from utils.content_parity import source_inventory_sha256
from utils.source_identity import audit_price_faq_preservation, audit_source_reviews
from utils.source_content_blocks import audit_source_content_blocks
from utils.source_fidelity import _headings, _page_key


SCORE_DIMENSIONS = (
    "visual_design", "originality", "brand_fidelity", "content_fidelity",
    "real_photography", "natural_copy", "usability", "mobile",
    "accessibility", "interaction_quality",
)
VIEWPORTS = ("desktop", "tablet", "mobile", "small_mobile")
# Independent reviewers must score EACH real route; strong home-page averages
# cannot conceal mediocre service, contact, staff or product pages.
PAGE_PREMIUM_DIMENSIONS = (
    "visual_design", "premium_appeal", "brand_signature",
    "image_authenticity", "interaction_quality", "usability",
    "mobile", "content_completeness",
)



def site_digest(rendered_pages: dict[str, str]) -> str:
    """Bind all audited HTML pages, not only the home page."""
    payload = "".join(str(route) + "\n" + rendered_pages[route] + "\n"
                      for route in sorted(rendered_pages))
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def source_coverage_matrix(rendered_pages: dict[str, str], research: dict) -> dict:
    """Report each source page/heading and every high-value observed content item.

    Mapped headings are not semantic proof: they require a human-reviewed
    source/build-specific signoff before the matrix is accepted.
    """
    inventory = research.get("source_inventory") or {}
    old_pages = [p for p in inventory.get("pages") or []
                 if isinstance(p, dict) and p.get("url")]
    if not old_pages:
        if research.get("research_mode") == "verified_no_website":
            return {"status": "no_original_site", "items": [],
                    "missing": [], "pending": ["Verify third-party factual sources."],
                    "source_pages": 0, "source_sha256": ""}
        return {"status": "missing_source", "items": [], "missing": [],
                "pending": ["Existing website inventory is unavailable."],
                "source_pages": 0, "source_sha256": ""}
    mapped = {str(item.get("source_url") or ""): item
              for item in (research.get("source_content_map") or {}).get("pages") or []
              if isinstance(item, dict)}
    missing, pending, items = [], [], []
    if inventory.get("failed_urls") or inventory.get("priority_unvisited_urls"):
        pending.append("Source crawl incomplete: unread original pages.")
    for original in old_pages:
        url = original["url"]
        record = mapped.get(url) or {}
        destination = str(record.get("target") or "")
        path = _page_key(destination)
        page_ok = (record.get("status") in {"retain", "merge"}
                   and path in rendered_pages)
        items.append({"source_url": url, "kind": "page",
                      "target": destination, "status": "mapped" if page_ok else "missing"})
        if not page_ok:
            missing.append({"source_url": url, "kind": "source_page", "target": destination})
        source_headings = _headings(original)
        sections = {str(item.get("source_heading") or "").casefold().strip(): item
                    for item in record.get("sections") or [] if isinstance(item, dict)}
        for heading in source_headings:
            target = sections.get(heading.casefold(), {}).get("target")
            ok = bool(target and page_ok)
            items.append({"source_url": url, "kind": "heading", "label": heading,
                          "target": target or "", "status": "mapped" if ok else "missing"})
            if not ok:
                missing.append({"source_url": url, "kind": "source_heading",
                                "label": heading})
        for field, kind in (("price_rows", "price_row"), ("faq_questions", "faq")):
            observed = (original.get("price_faq_evidence") or {}).get(field) or []
            for item in observed:
                label = item.get("label") if isinstance(item, dict) else item
                items.append({"source_url": url, "kind": kind, "label": str(label),
                              "status": "checked_by_static_evidence"})
        for item in (original.get("source_identity") or {}).get("reviews") or []:
            if isinstance(item, dict):
                items.append({"source_url": url, "kind": "review",
                              "label": str(item.get("quote") or "")[:100],
                              "status": "checked_by_static_evidence"})
    block_audit = audit_source_content_blocks(rendered_pages, research)
    if block_audit["pending"]:
        pending.append(
            f"{len(block_audit['pending'])} original content blocks need a source-to-build "
            "rewrite mapping and human review."
        )
    if block_audit["truncated_pages"]:
        pending.append("Source content block inventory was bounded; check pages manually: "
                       + ", ".join(block_audit["truncated_pages"][:5]))
    for report in (audit_source_reviews(rendered_pages, research),
                   audit_price_faq_preservation(rendered_pages, research)):
        missing.extend(report["missing"])
        pending.extend(report.get("pending") or [])
    source_hash = source_inventory_sha256(inventory)
    build_hash = site_digest(rendered_pages)
    review = research.get("content_inventory_review") or {}
    if not (
        review.get("approved") is True and review.get("reviewer_kind") == "human"
        and str(review.get("reviewer") or "").strip()
        and str(review.get("checked_at") or "").strip()
        and review.get("snapshot_sha256") == source_hash
        and review.get("build_sha256") == build_hash
        and set(review.get("source_urls") or []) >= {p["url"] for p in old_pages}
    ):
        pending.append("Human source-to-destination review is not tied to the complete current site.")
    return {"status": ("fail" if missing else "pending" if pending else "verified"),
            "items": items, "missing": missing, "pending": pending,
            "source_pages": len(old_pages), "source_sha256": source_hash,
            "build_sha256": build_hash, "observed_items": len(items), "content_blocks": block_audit}


def verify_independent_premium_reviews(
    evidence: dict | None, rendered_pages: dict[str, str], research: dict
) -> dict:
    """Two distinct independently evidenced reviews, every dimension >=9.5.

    These records need provenance checked separately by a human. Reusing the
    builder as its own reviewer is prohibited. Screenshots must be tangible.
    """
    evidence = evidence if isinstance(evidence, dict) else {}
    issues = []
    digest = site_digest(rendered_pages)
    if evidence.get("build_sha256") != digest:
        issues.append("Independent reviews are absent or refer to another build.")
    inventory = research.get("source_inventory") or {}
    if inventory.get("pages") and evidence.get("source_sha256") != source_inventory_sha256(inventory):
        issues.append("Independent review has stale original-source evidence.")
    reviews = evidence.get("reviewers")
    if not isinstance(reviews, list) or len(reviews) < 2:
        reviews = []
        issues.append("At least two independently verified reviewers are required.")
    identities = set()
    for index, review in enumerate(reviews):
        if not isinstance(review, dict):
            issues.append(f"Reviewer #{index+1} has no structured report.")
            continue
        identifier = str(review.get("reviewer_id") or "").strip()
        if not identifier or identifier in identities:
            issues.append("Independent reviewers must have distinct identities.")
        identities.add(identifier)
        if (review.get("independent_of_builder") is not True
                or review.get("provenance_human_verified") is not True
                or review.get("critical_issues") != []
                or not str(review.get("evidence_reference") or "").strip()):
            issues.append(f"Reviewer {identifier or index+1}: provenance or issue resolution missing.")
        scores = review.get("scores") or {}
        for key in SCORE_DIMENSIONS:
            score = scores.get(key)
            if (isinstance(score, bool) or not isinstance(score, (int, float))
                    or not 9.5 <= score <= 10):
                issues.append(f"Reviewer {identifier or index+1}: {key} below 9.5/10 or not reviewed.")
        screenshots = review.get("screenshots") or {}
        for vp in VIEWPORTS:
            file = screenshots.get(vp)
            if not isinstance(file, str) or not Path(file).is_file():
                issues.append(f"Reviewer {identifier or index+1}: missing {vp} screenshot evidence.")
        covered = review.get("pages_reviewed")
        if not isinstance(covered, list) or set(covered) != set(rendered_pages):
            issues.append(f"Reviewer {identifier or index+1}: not every page inspected.")
        # For research created under the stronger protocol, inspect every
        # rendered route and every viewport. Old review records cannot bypass
        # this merely by repeating a 9.5 overall score.
        if research.get("premium_visual_protocol") == "v2":
            page_scores = review.get("page_scores") or {}
            route_screenshots = review.get("route_screenshots") or {}
            observations = review.get("page_observations") or {}
            if set(page_scores) != set(rendered_pages):
                issues.append(f"Reviewer {identifier or index+1}: page-by-page scores missing.")
            if set(route_screenshots) != set(rendered_pages):
                issues.append(f"Reviewer {identifier or index+1}: per-route screenshots missing.")
            if set(observations) != set(rendered_pages):
                issues.append(f"Reviewer {identifier or index+1}: page-by-page evidence missing.")
            for route in rendered_pages:
                scores_by_route = page_scores.get(route) or {}
                for dimension in PAGE_PREMIUM_DIMENSIONS:
                    value = scores_by_route.get(dimension)
                    if (isinstance(value, bool) or not isinstance(value, (int, float))
                            or not 9.5 <= value <= 10):
                        issues.append(
                            f"Reviewer {identifier or index+1}: "
                            f"{route}: {dimension} below 9.5/10 or unreviewed."
                        )
                explanation = observations.get(route)
                if not isinstance(explanation, str) or len(explanation.strip()) < 45:
                    issues.append(f"Reviewer {identifier or index+1}: {route}: no concrete visual analysis.")
                shots = route_screenshots.get(route) or {}
                for vp in VIEWPORTS:
                    screenshot = shots.get(vp)
                    if not isinstance(screenshot, str) or not Path(screenshot).is_file():
                        issues.append(f"Reviewer {identifier or index+1}: {route}: {vp} screenshot missing.")
                    elif not Path(screenshot).read_bytes().startswith(b"\x89PNG\r\n\x1a\n"):
                        issues.append(f"Reviewer {identifier or index+1}: {route}: {vp} screenshot is not PNG.")

    return {"pass": not issues, "issues": issues,
            "reviewers_checked": len(reviews), "dimensions": SCORE_DIMENSIONS,
            "per_page_dimensions": PAGE_PREMIUM_DIMENSIONS if research.get("premium_visual_protocol") == "v2" else (),
            "build_sha256": digest}


def verify_field_performance(evidence: dict | None, rendered_pages: dict[str, str]) -> dict:
    """Use real 75th-percentile field metrics; never count simulated timings."""
    evidence = evidence if isinstance(evidence, dict) else {}
    problems = []
    if evidence.get("build_sha256") != site_digest(rendered_pages):
        problems.append("Field performance evidence does not match this site build.")
    if evidence.get("source") not in ("crux", "rum", "real_user_monitoring"):
        problems.append("Real-user field data is missing; synthetic speed is provisional.")
    if evidence.get("percentile") != 75:
        problems.append("Performance must report the 75th percentile.")
    for key, bound in (("lcp_ms", 2500), ("inp_ms", 200), ("cls", 0.1)):
        number = evidence.get(key)
        if isinstance(number, bool) or not isinstance(number, (float, int)) or not 0 <= number <= bound:
            problems.append(f"{key} missing or worse than its Core Web Vitals good threshold.")
    sample = evidence.get("sample_size")
    if isinstance(sample, bool) or not isinstance(sample, int) or sample < 30:
        problems.append("Field metric sample too small or unverified.")
    if evidence.get("human_evidence_verified") is not True:
        problems.append("Metric provenance not verified.")
    return {"pass": not problems, "issues": problems,
            "thresholds": {"lcp_ms": 2500, "inp_ms": 200, "cls": 0.1}}


def audit_primary_journeys(
    rendered_pages: dict[str, str], tasks: list[dict] | None
) -> dict:
    """Statically verify primary task links point to real routes / destinations.

    Does not execute booking, email sending, payments, or external navigation.
    """
    issues = []
    tasks = tasks if isinstance(tasks, list) else []
    for item in tasks:
        if not isinstance(item, dict):
            issues.append("Task record is malformed.")
            continue
        label = str(item.get("label") or "").strip()
        destination = str(item.get("destination") or "").strip()
        source = str(item.get("source_route") or "index.html")
        if not label or source not in rendered_pages or not destination:
            issues.append(f"Task {label or '[unnamed]'} missing a source page or destination.")
            continue
        soup = BeautifulSoup(rendered_pages[source], "html.parser")
        anchors = [a for a in soup.find_all("a", href=True)
                   if str(a.get("href") or "").strip() == destination]
        if not anchors:
            issues.append(f"Task {label}: exact destination link missing from {source}.")
            continue
        if not any(a.get_text(" ", strip=True) or a.get("aria-label") for a in anchors):
            issues.append(f"Task {label}: destination has no accessible label.")
        scheme = urlsplit(destination).scheme
        if scheme and scheme not in ("http", "https", "tel", "mailto"):
            issues.append(f"Task {label}: unsupported destination scheme.")
    return {"pass": not issues, "issues": issues,
            "tasks_checked": len(tasks),
            "note": "Destinations exist in markup; external completion requires a real browser check."}


def discover_source_journeys(research: dict) -> list[dict]:
    """Find exact observed booking/contact links without inventing destinations.

    Prioritize a real third-party booking page over generic old-site navigation;
    only source-backed mailto/tel and external booking URLs are returned.
    """
    output, seen_categories = [], set()
    source = (research.get("source_inventory") or {}).get("pages") or []
    proposals = []
    for page in source:
        if not isinstance(page, dict) or not page.get("url"):
            continue
        original = str(page["url"])
        host = (urlsplit(original).hostname or "").removeprefix("www.")
        for link in page.get("links") or []:
            if not isinstance(link, dict):
                continue
            label = str(link.get("text") or "").strip()
            href = str(link.get("href") or "").strip()
            if not href:
                continue
            absolute = urljoin(original, href)
            parsed = urlsplit(absolute)
            lower = (label + " " + href).casefold()
            category = None
            if (any(x in lower for x in ("ajanvaraus", "varaa aika", "booking", "book now"))
                    and parsed.scheme == "https"
                    and (parsed.hostname or "").removeprefix("www.") != host):
                category = "booking"
            elif parsed.scheme == "tel":
                category = "phone"
            elif parsed.scheme == "mailto":
                category = "email"
            if category:
                proposals.append(({"booking": 0, "phone": 1, "email": 2}[category],
                                  category, absolute, original, label))
    facts = research.get("company_facts") or {}
    if facts.get("contact_phone") and not any(item[1] == "phone" for item in proposals):
        phone = "".join(ch for ch in str(facts["contact_phone"]) if ch.isdigit() or ch == "+")
        if len(phone) >= 6:
            proposals.append((1, "phone", "tel:" + phone, "verified company_facts", "Call"))
    if facts.get("contact_email") and not any(item[1] == "email" for item in proposals):
        proposals.append((2, "email", "mailto:" + str(facts["contact_email"]).strip(),
                          "verified company_facts", "Email"))
    for _, category, destination, source_url, label in sorted(proposals):
        if category in seen_categories:
            continue
        seen_categories.add(category)
        output.append({"label": label or category, "kind": category,
                       "source_url": source_url, "source_route": "index.html",
                       "destination": destination})
    return output

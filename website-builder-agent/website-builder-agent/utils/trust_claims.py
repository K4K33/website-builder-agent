"""Source-bound social proof QA for *every* Kaurivo client.

Unlike checking that original reviews survived, this catches NEW testimonials
or rating summaries that the builder invented. Only recognizable customer
review components are hard-checked; ambiguous quotes remain a human task.
No external API calls, imagined reviewer approval, or numeric visual scoring.
"""
from __future__ import annotations

import re
from bs4 import BeautifulSoup

from utils.content_parity import source_inventory_sha256
from utils.premium_quality_gate import site_digest
from utils.source_identity import REVIEW_SELECTOR, QUOTE_SELECTOR, _stars, plain


AGGREGATE_SELECTOR = (
    '[itemtype*="AggregateRating"],[data-aggregate-rating],'
    '[class~="aggregate-rating"],[class~="rating-summary"],'
    '[class~="rating-badge"],[class~="review-score"]'
)
SCORE_RE = re.compile(
    r'(?<!\d)(?:[0-5](?:[.,]\d{1,2})?)\s*(?:/\s*5|(?:out of|of)\s*5|tähteä|stars?)'
    r'|[★⭐]{3,5}',
    re.I,
)


def _source_snapshot(research: dict) -> str:
    inventory = research.get("source_inventory") or {}
    return source_inventory_sha256(inventory) if inventory.get("pages") else ""


def _client_approved(record: object, pages: dict[str, str], research: dict) -> bool:
    """Approval cannot survive a different build, snapshot or unknown signer."""
    if not isinstance(record, dict):
        return False
    if not (
        record.get("approved") is True
        and record.get("reviewer_kind") == "client"
        and str(record.get("reviewer") or "").strip()
        and str(record.get("approved_at") or "").strip()
        and str(record.get("evidence_reference") or "").strip()
        and record.get("build_sha256") == site_digest(pages)
    ):
        return False
    snapshot = _source_snapshot(research)
    return not snapshot or record.get("source_sha256") == snapshot


def _quote_in_card(node) -> str:
    candidates = node.select(QUOTE_SELECTOR)
    candidates += node.select("p")
    for candidate in candidates:
        value = " ".join(candidate.get_text(" ", strip=True).split())
        if 12 <= len(value) <= 1000:
            return value
    if node.name in {"blockquote", "q"}:
        value = " ".join(node.get_text(" ", strip=True).split())
        if 12 <= len(value) <= 1000:
            return value
    return ""


def audit_trust_claims(rendered_pages: dict[str, str], research: dict | None = None) -> dict:
    """Block fabricated review text, upgraded stars and unsupported score badges.

    Evidence for NEW client-provided reviews:
      verified_additional_reviews = [{
        quote, stars (integer 1-5 or null), source_url (HTTPS),
        rights_verified: true
      }]
      additional_reviews_approval = {approved, reviewer_kind: client, reviewer,
        approved_at, evidence_reference, build_sha256, source_sha256 when sourced}

    Evidence for a numeric AGGREGATE rating badge:
      verified_aggregate_ratings = [{visible_text, source_url (HTTPS)}]
      aggregate_ratings_approval = same exact-build client approval shape.

    A generic quotation outside review-marked UI is not automatically a
    customer testimonial. Ratings in third-party dynamic widgets still need
    an independent rendered inspection; these checks inspect supplied HTML.
    """
    research = research or {}
    originals: dict[str, set[int | None]] = {}
    for source in (research.get("source_inventory") or {}).get("pages") or []:
        if not isinstance(source, dict):
            continue
        identity = source.get("source_identity") or {}
        for review in identity.get("reviews") or []:
            if not isinstance(review, dict) or not review.get("quote"):
                continue
            raw_stars = review.get("stars")
            stars = raw_stars if type(raw_stars) is int and 1 <= raw_stars <= 5 else None
            originals.setdefault(plain(review["quote"]), set()).add(stars)

    added: dict[str, set[int | None]] = {}
    if _client_approved(research.get("additional_reviews_approval"), rendered_pages, research):
        for item in research.get("verified_additional_reviews") or []:
            if not isinstance(item, dict) or not str(item.get("source_url") or "").startswith("https://"):
                continue
            if item.get("rights_verified") is not True:
                continue
            stars = item.get("stars")
            if stars is not None and (type(stars) is not int or not 1 <= stars <= 5):
                continue
            quote = plain(item.get("quote"))
            if quote:
                added.setdefault(quote, set()).add(stars)

    aggregate_evidence = set()
    if _client_approved(research.get("aggregate_ratings_approval"), rendered_pages, research):
        for item in research.get("verified_aggregate_ratings") or []:
            if (isinstance(item, dict)
                    and str(item.get("source_url") or "").startswith("https://")
                    and item.get("source_verified") is True):
                label = plain(item.get("visible_text"))
                if label:
                    aggregate_evidence.add(label)

    blocked, pending = [], []
    checked_reviews, checked_aggregates = 0, 0
    for route, html in rendered_pages.items():
        soup = BeautifulSoup(html, "html.parser")
        review_nodes = soup.select(REVIEW_SELECTOR)
        review_node_ids = {id(node) for node in review_nodes}
        for node in review_nodes:
            # BeautifulSoup.find_parent() accepts tag names, NOT CSS selectors;
            # compare ancestor identities to avoid double counting nested cards.
            if any(id(parent) in review_node_ids for parent in node.parents):
                continue
            quote = _quote_in_card(node)
            if not quote:
                pending.append({
                    "category": "unverified_review_widget", "route": route,
                    "issue": "Review component has no inspectable quote; verify rendered widget.",
                })
                continue
            checked_reviews += 1
            key = plain(quote)
            observed = _stars(node)
            source_ratings = originals.get(key)
            if source_ratings is not None:
                if observed not in source_ratings:
                    blocked.append({
                        "category": "changed_source_review_rating", "route": route,
                        "quote": quote[:135], "shown_stars": observed,
                        "original_stars": sorted(source_ratings, key=lambda n: -1 if n is None else n),
                    })
            elif observed not in added.get(key, set()):
                blocked.append({
                    "category": "unsourced_customer_review", "route": route,
                    "quote": quote[:135], "shown_stars": observed,
                    "issue": "No original source or exact-build client-approved review evidence.",
                })

        # Sitewide aggregate badges are different from the per-quote stars.
        # Restrict checks to explicit aggregate components to prevent
        # confusing decorative stars, product symbols, and icons for ratings.
        aggregate_nodes = soup.select(AGGREGATE_SELECTOR)
        aggregate_ids = {id(node) for node in aggregate_nodes}
        for node in aggregate_nodes:
            if any(id(parent) in review_node_ids or id(parent) in aggregate_ids
                   for parent in node.parents):
                continue
            claim = " ".join(node.get_text(" ", strip=True).split())
            if not claim and node.get("aria-label"):
                claim = str(node["aria-label"]).strip()
            if not SCORE_RE.search(claim):
                continue
            checked_aggregates += 1
            if plain(claim) not in aggregate_evidence:
                blocked.append({
                    "category": "unverified_aggregate_rating",
                    "route": route, "claim": claim[:160],
                    "issue": "Numeric social-proof badge requires cited source and current client approval.",
                })

    return {
        "pass": not blocked and not pending,
        "blocking": blocked,
        "pending": pending,
        "reviews_checked": checked_reviews,
        "aggregate_badges_checked": checked_aggregates,
        "note": (
            "Only identified review/aggregate components checked. Source authenticity, "
            "permission and dynamically inserted markup still need real human/browser review."
        ),
    }

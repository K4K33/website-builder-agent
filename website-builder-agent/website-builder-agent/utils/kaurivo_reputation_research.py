"""Kaurivo independent reputation screening for the daily PRH shortlist.

An approximately 4/5 reputation claim needs an actual public third-party
aggregate rating >= 4.0/5 from >= 10 reviews. Popularity (review volume)
is a separate, non-qualifying signal. Never infer an equivalent star score
from followers, company testimonials, an AI summary, or Tavily snippets.

Uses at most 8 additional *pre-reserved* free-plan Tavily search credits per
scheduled day; zero requests if verified no-billing free access is unavailable.
Reads only public structured AggregateRating data on trusted external review
platforms. No Google, login, personal reviews, or review text is collected.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import re
from urllib.parse import urlsplit
import unicodedata

from bs4 import BeautifulSoup
import requests
import config

from .kaurivo_website_research import (
    API, make_credit_reservation, MAX_PACKET_BYTES as BASE_PACKET_BYTES, tokens,
)
from .kaurivo_site_audit import candidate_public_site_verified

MAX_QUERIES = 8
MAX_HTML_BYTES = 256_000
MAX_PACKET_BYTES = 500_000
MIN_REVIEWS = 10
MIN_RATING = 4.0

# Only independent review sources with an explicit 5-star public aggregate.
# Google review scraping / Maps extraction is deliberately not supported.
REVIEW_HOSTS = {
    "trustpilot": ("trustpilot.com",),
    "tripadvisor": ("tripadvisor.com", "tripadvisor.fi", "tripadvisor.se"),
    "yelp": ("yelp.com",),
}

def _platform(url):
    try:
        u = urlsplit(url)
        if (u.scheme != "https" or not u.hostname or u.username or u.password
                or u.port not in (None, 443)):
            return ""
        h = u.hostname.lower().rstrip(".")
        for name, roots in REVIEW_HOSTS.items():
            if any(h == root or h.endswith("." + root) for root in roots):
                return name
    except (ValueError, TypeError):
        pass
    return ""

def _normalize(value):
    s = unicodedata.normalize("NFKD", str(value or "").casefold())
    return "".join(ch for ch in s if not unicodedata.combining(ch))

def _company_identity_matches(company, url, business_name="", title=""):
    """Do not attach an unrelated business's rating to a PRH company."""
    site = company.get("website_listed_url") or ""
    platform = _platform(url)
    host = (urlsplit(site).hostname or "").lower().removeprefix("www.")
    if platform == "trustpilot":
        # Trustpilot review pages are keyed by the actual business hostname.
        path = urlsplit(url).path.rstrip("/").lower()
        return bool(host and path == "/review/" + host)
    if platform not in ("tripadvisor", "yelp"):
        return False
    name = str(company.get("name", ""))
    significant = [t for t in tokens(name) if len(t) >= 5]
    title_text = _normalize(business_name + " " + title)
    matches = [t for t in significant if t in _normalize(title_text)]
    city = _normalize(company.get("city_hint", ""))
    # Same trade name + locality required for businesses without a direct
    # website-to-platform relationship. No anonymous one-token collisions.
    return bool(significant and len(matches) >= min(2, len(significant))
                and city and city in title_text)

def _walk_json(node):
    if isinstance(node, list):
        for item in node:
            yield from _walk_json(item)
    elif isinstance(node, dict):
        yield node
        for child in node.values():
            if isinstance(child, (dict, list)):
                yield from _walk_json(child)

def _aggregate_candidates(html):
    soup = BeautifulSoup(html, "html.parser")
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    for script in soup.find_all("script", type=re.compile(r"application/ld\+json", re.I), limit=35):
        try:
            raw = json.loads(script.string or script.get_text())
        except (ValueError, TypeError):
            continue
        for node in _walk_json(raw):
            aggregate = node.get("aggregateRating")
            if not isinstance(aggregate, dict):
                continue
            try:
                if "5" != str(aggregate.get("bestRating", "5")):
                    continue
                rating = float(aggregate.get("ratingValue"))
                count = int(str(aggregate.get("reviewCount", aggregate.get("ratingCount", ""))).replace(",", ""))
            except (ValueError, TypeError):
                continue
            if not (0 <= rating <= 5 and 0 <= count <= 2_000_000):
                continue
            name = node.get("name", "")
            if not isinstance(name, str):
                name = ""
            yield rating, count, name, title

def _source_snapshot(company, url, *, get=requests.get):
    platform = _platform(url)
    if not platform:
        return None
    try:
        with get(
            url,
            headers={"User-Agent": "KaurivoReputationResearch/1.0 (public structured metadata only)",
                     "Accept": "text/html,application/xhtml+xml"},
            timeout=(5, 12), allow_redirects=False, stream=True
        ) as response:
            if response.status_code != 200:
                return None
            if "text/html" not in response.headers.get("Content-Type", "").lower():
                return None
            pieces, size = [], 0
            for piece in response.iter_content(chunk_size=16384):
                size += len(piece)
                if size > MAX_HTML_BYTES:
                    return None
                pieces.append(piece)
            source = b"".join(pieces).decode(response.encoding or "utf-8", "replace")
    except (requests.RequestException, ValueError, UnicodeError, LookupError):
        return None
    for rating, review_count, name, title in _aggregate_candidates(source):
        if rating < MIN_RATING or review_count < MIN_REVIEWS:
            continue
        if not _company_identity_matches(company, url, name, title):
            continue
        return {
            "status": "qualified",
            "rating": round(rating, 2),
            "review_count": review_count,
            "platform": platform,
            "source_url": url,
            "checked_at": datetime.now(timezone.utc).isoformat(),
            "method": "direct_public_review_page_structured_rating",
            "popularity_tier": (
                "substantial" if review_count >= 100
                else "moderate" if review_count >= 30
                else "limited"
            )
        }
    return None

def _find_source(company, results, *, get=requests.get):
    for item in results[:8]:
        if not isinstance(item, dict):
            continue
        url = item.get("url")
        if not isinstance(url, str) or len(url) > 1200 or not _platform(url):
            continue
        if not _company_identity_matches(
            company, url, "", str(item.get("title", ""))[:300]
        ):
            continue
        snapshot = _source_snapshot(company, url, get=get)
        if snapshot:
            return snapshot
    return None

def enrich_reputation(packet_path, *, key="", claim=None, post=requests.post,
                      get=requests.get, max_queries=MAX_QUERIES):
    packet_path = Path(packet_path)
    if not packet_path.is_file() or packet_path.stat().st_size > MAX_PACKET_BYTES:
        raise ValueError("Invalid PRH shortlist packet")
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    if (packet.get("schema") != "kaurivo_prh_shortlist_v1"
            or packet.get("mode") != "pilot-live"
            or not isinstance(packet.get("candidates"), list)
            or len(packet["candidates"]) > 50):
        raise ValueError("Only source-bound daily shortlists are permitted")
    candidates = packet["candidates"]
    if not config.tavily_free_plan_confirmed(scheduled=True):
        return {"enabled": False, "searched": 0, "qualified": 0, "reason": "free_plan_not_confirmed"}
    if not key or claim is None:
        return {"enabled": False, "searched": 0, "qualified": 0, "reason": "no_free_search_access"}
    searched = qualified = 0
    limit = min(MAX_QUERIES, max(0, int(max_queries)))
    # Audit precedes reputation research. Do not spend a search credit on
    # private/unreachable/unverified webpages.
    for company in candidates:
        if searched >= limit:
            break
        if (not candidate_public_site_verified(company)
                or not (company.get("website_listed_url") or
                        (company.get("website_search_candidate") or {}).get("url"))):
            continue
        if not claim():
            break  # The private atomic ledger is authoritative.
        searched += 1
        query = (
            '"' + str(company.get("name", ""))[:100] + '" '
            + str(company.get("city_hint", ""))[:45]
            + " arvostelut kokemuksia Trustpilot Tripadvisor Yelp"
        )
        try:
            response = post(API, json={
                "query": query, "search_depth": "basic", "max_results": 8,
                "include_answer": False, "include_raw_content": False,
                "include_images": False, "topic": "general"
            }, headers={"Authorization": "Bearer " + key,
                        "Content-Type": "application/json"}, timeout=(6, 20))
            if response.status_code in (401, 402, 403, 429, 432, 433):
                break
            response.raise_for_status()
            results = response.json().get("results") or []
            snapshot = _find_source(company, results, get=get)
            if snapshot:
                company["reputation_evidence"] = snapshot
                qualified += 1
        except (requests.RequestException, ValueError, TypeError):
            break
    payload = json.dumps(packet, ensure_ascii=False, indent=2) + "\n"
    if len(payload.encode("utf-8")) > MAX_PACKET_BYTES:
        raise ValueError("Reputation packet exceeded size limit")
    packet_path.write_text(payload, encoding="utf-8")
    return {"enabled": True, "searched": searched, "qualified": qualified,
            "credits_reserved": searched, "marketing_sent": 0,
            "personal_reviews_copied": 0}

def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet", required=True)
    parser.add_argument("--max-queries", type=int, default=MAX_QUERIES)
    args = parser.parse_args(argv)
    import os
    key = os.environ.get("KAURIVO_TAVILY_API_KEY", "")
    claim = make_credit_reservation() if key else None
    result = enrich_reputation(args.packet, key=key, claim=claim,
                               max_queries=args.max_queries)
    print(json.dumps(result, ensure_ascii=False))

if __name__ == "__main__":
    main()

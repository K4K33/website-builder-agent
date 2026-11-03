"""Free source-backed industry reference discovery with reusable local cache.

No Tavily, OpenRouter, paid web search, browser automation of search engines,
fabricated competitor links or automatic public scrape loops. OSM's public
Overpass API is rate-limited and may fail: cache hits reduce public traffic.
Every returned operator is STILL live-validated and independently screened
by Research before entering the design benchmark.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re
from urllib.parse import urlsplit

from utils.quality import canonical_url

CACHE_DAYS = 14
# Explicit categories map to existing verified OSM tag query types.
# Anything unrecognized fails closed until real operator references are supplied.
INDUSTRY_ALIASES = {
    "kukkakauppa": "kukkakauppa", "florist": "kukkakauppa",
    "kampaamo": "kampaamo", "parturi": "kampaamo", "hairdresser": "kampaamo",
    "kauneushoitola": "kauneushoitola", "beauty salon": "kauneushoitola",
    "ravintola": "ravintola", "restaurant": "ravintola",
    "kahvila": "kahvila", "cafe": "kahvila",
    "autokorjaamo": "autokorjaamo", "car repair": "autokorjaamo",
    "hammaslääkäri": "hammaslääkäri", "dentist": "hammaslääkäri",
    "kuntosali": "kuntosali", "fitness centre": "kuntosali",
    "hotelli": "hotelli", "hotel": "hotelli",
    "sähköasentaja": "sähköasentaja", "electrician": "sähköasentaja",
    "putkimies": "putkimies", "plumber": "putkimies",
    "pyörähuolto": "pyöräliike", "pyöräliike": "pyöräliike",
    "bicycle shop": "pyöräliike", "bike repair": "pyöräliike",
    "suutari": "suutari", "shoemaker": "suutari",
    "leipomo": "leipomo", "bakery": "leipomo",
}

DEFAULT_REGIONS = ("Tampere", "Turku", "Helsinki", "Oulu")
MAX_PUBLIC_REGIONS_PER_LOOKUP = 2


def normalize_industry(raw: str) -> str:
    raw = " ".join(str(raw or "").casefold().split())
    if raw in INDUSTRY_ALIASES:
        return INDUSTRY_ALIASES[raw]
    for phrase, category in sorted(INDUSTRY_ALIASES.items(), key=lambda row: -len(row[0])):
        if len(phrase) >= 5 and phrase in raw:
            return category
    return ""


def _timestamp(value: str) -> datetime | None:
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt if dt.tzinfo else None
    except (ValueError, TypeError):
        return None


def _candidates(records: list, *, target_url: str = "", limit: int = 30) -> list[dict]:
    target_host = urlsplit(canonical_url(target_url)).hostname or ""
    chosen, hosts = [], {target_host}
    for row in records:
        if not isinstance(row, dict):
            continue
        u = str(row.get("url") or row.get("website") or "").strip()
        if not u:
            continue
        url = canonical_url(u)
        host = (urlsplit(url).hostname or "").casefold()
        if not host or host in hosts or not url.startswith(("http://", "https://")):
            continue
        if host in {"localhost", "127.0.0.1"} or host.endswith(".local"):
            continue
        hosts.add(host)
        chosen.append({
            "url": url,
            "title": str(row.get("title") or row.get("name") or "")[:200],
            "content": str(row.get("content") or "")[:1500],
        })
        if len(chosen) >= limit:
            break
    return chosen


def discover_free_references(
    industry: str, *,
    target_url: str = "",
    cache_path: str | Path = "output/_kaurivo_reference_cache.json",
    regions: tuple[str, ...] = DEFAULT_REGIONS,
    max_results: int = 10,
    fetch_osm=None,
    now: datetime | None = None,
) -> list[dict]:
    """Reuse an existing industry pool before a couple of fair-use OSM lookups.

    Never return unverified operator suitability: Research checks the websites,
    source quote and business category before selecting its three references.
    """
    category = normalize_industry(industry)
    if not category:
        raise RuntimeError(
            "No trustworthy free OSM mapping for this industry: " + str(industry)
            + ". Provide verified same-sector reference URLs or add a supported tag mapping."
        )
    if not 3 <= max_results <= 50:
        raise ValueError("max_results must be 3..50")
    now = now or datetime.now(timezone.utc)
    path = Path(cache_path)
    stored = {}
    if path.is_file():
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, dict):
                stored = data
        except (OSError, ValueError):
            stored = {}
    current = stored.get(category) or {}
    observed_at = _timestamp(current.get("updated_at") or "") if isinstance(current, dict) else None
    saved = (current.get("results") or []) if isinstance(current, dict) else []
    if observed_at and now - observed_at <= timedelta(days=CACHE_DAYS):
        results = _candidates(saved, target_url=target_url, limit=max_results)
        if len(results) >= 5:
            return results

    if fetch_osm is None:
        # Local import to avoid circular references and extra dependencies.
        from agents.scout import _fetch_osm_companies
        fetch_osm = _fetch_osm_companies

    gathered = list(saved) if observed_at and now - observed_at <= timedelta(days=CACHE_DAYS) else []
    # At most two public region lookups per cache refresh. No unlimited loop.
    for region in regions[:MAX_PUBLIC_REGIONS_PER_LOOKUP]:
        if len(_candidates(gathered, target_url=target_url, limit=50)) >= max_results:
            break
        try:
            candidates = fetch_osm(category, region) or []
        except (RuntimeError, ValueError, OSError) as error:
            print("[References] Public OSM query unavailable: " + type(error).__name__)
            continue
        for row in candidates:
            if isinstance(row, dict) and row.get("website"):
                gathered.append(row)
    results = _candidates(gathered, target_url=target_url, limit=50)
    if results:
        path.parent.mkdir(parents=True, exist_ok=True)
        saved_current = dict(stored)
        saved_current[category] = {
            "updated_at": now.isoformat(),
            "source": "openstreetmap_overpass_public",
            "results": results,
        }
        path.write_text(json.dumps(saved_current, ensure_ascii=False, indent=2),
                        encoding="utf-8")
    selected = _candidates(results, target_url=target_url, limit=max_results)
    if len(selected) < 3:
        raise RuntimeError(
            "Fewer than three live candidate websites from cached/open OSM sources "
            "for " + category + "; no fabricated industry references. "
            "Retry another region or supply verified reference URLs."
        )
    return selected

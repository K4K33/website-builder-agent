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
import ipaddress
from pathlib import Path
import re
from urllib.parse import urlsplit

from utils.quality import canonical_url

CACHE_DAYS = 14
# Categories use existing OSM tags or curated operator candidates.
INDUSTRY_ALIASES = {
    "kukkakauppa": "kukkakauppa", "florist": "kukkakauppa",
    "kampaamo": "kampaamo", "parturi": "kampaamo", "hairdresser": "kampaamo",
    "kauneushoitola": "kauneushoitola", "beauty salon": "kauneushoitola",
    "ravintola": "ravintola", "restaurant": "ravintola",
    "kahvila": "kahvila", "cafe": "kahvila", "coffee shop": "kahvila",
    "cafeteria": "kahvila", "kahvilapalvelut": "kahvila",
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
    "asianajotoimisto": "asianajotoimisto",
    "asianajopalvelut": "asianajotoimisto",
    "asianajaja": "asianajotoimisto",
    "lakitoimisto": "asianajotoimisto",
    "lakipalvelut": "asianajotoimisto",
    "lakiasiaintoimisto": "asianajotoimisto",
    "law firm": "asianajotoimisto",
    "legal services": "asianajotoimisto",
    "attorney": "asianajotoimisto",
    # Building/industrial surveyors and laser-scanning specialists use varied
    # Finnish industry labels, but their customer task is the same measured
    # survey / point-cloud / construction-layout service. Candidate websites
    # still require live exact-source and image QA.
    "mittauspalvelut": "mittauspalvelut",
    "mittauspalvelu": "mittauspalvelut",
    "maanmittaus": "mittauspalvelut",
    "maanmittauspalvelut": "mittauspalvelut",
    "rakennusmittaus": "mittauspalvelut",
    "rakennusmittaukset": "mittauspalvelut",
    "teollisuusmittaus": "mittauspalvelut",
    "teollisuuden mittaukset": "mittauspalvelut",
    "laserkeilaus": "mittauspalvelut",
    "3d-laserkeilaus": "mittauspalvelut",
    "mittaustyöt": "mittauspalvelut",
    "mittausalan": "mittauspalvelut",
    "surveying": "mittauspalvelut",
    "land surveying": "mittauspalvelut",
    "construction surveying": "mittauspalvelut",
    "industrial surveying": "mittauspalvelut",
    "teollisuusautomaatio": "teollisuusautomaatio",
    "teollisuuden automaatio": "teollisuusautomaatio",
    "automaatiosuunnittelu": "teollisuusautomaatio",
    "automaatio-ohjelmointi": "teollisuusautomaatio",
    "plc-ohjelmointi": "teollisuusautomaatio",
    "plc ohjelmointi": "teollisuusautomaatio",
    "industrial automation": "teollisuusautomaatio",
    "plc programming": "teollisuusautomaatio",
}

# Primary-source operator pages. These are candidates, not benchmark proof.
# Research still checks matching services, quotes and desktop/mobile evidence.
CURATED_REFERENCE_CANDIDATES = {
    # Real operators with independently discoverable primary websites.
    # These are only candidate URLs: the live site, relevant services,
    # source-exact evidence and two actual screenshots remain mandatory.
    # Especially valuable when public Overpass has few website-tagged cafés.
    "kahvila": (
        ("Cafe Engel", "https://www.cafeengel.fi/"),
        ("Hima & Sali", "https://www.himasali.com/kahvila/"),
        ("Kahvila Makiata", "https://www.makiata.fi/haaga/"),
        ("Cafe Cardemumma", "https://www.cafecardemumma.fi/"),
        ("Art Cafe Taideterassi", "https://artcafetaideterassi.fi/menu/"),
    ),
    "mittauspalvelut": (
        # Official source pages independently located on 13 Nov 2026.
        # They are candidates only, not pre-approved company references.
        ("Suomen GPS-Mittaus", "https://sgm.fi/palvelut/mittaustyot/laserkeilaus/"),
        ("Mitta Oy", "https://mitta.fi/palvelut/mittaus/laserkeilaus/"),
        ("MittausGroup Oy", "https://www.mittausgroup.fi/palvelut/rakennusmittaukset/"),
        ("Geo-Control Oy", "https://geo-control.fi/palvelut/"),
        ("Neotri", "https://www.neotri.fi/"),
        ("Aake Vision Ltd Oy", "https://aake.fi/palvelut/"),
        ("Uudenmaan Pohjatutkimus", "https://uudenmaanpohjatutkimus.fi/mittaukset/"),
    ),
    "teollisuusautomaatio": (
        ("Insinööritoimisto Antero", "https://www.plcantero.com/automaatiopalvelut/"),
        ("Insecon", "https://www.insecon.fi/palvelut/automaatioprojektit-ja-suunnittelu/"),
        ("Prodec Automation", "https://prodec.fi/"),
        ("PR-VISION", "https://www.prvision.fi/"),
        ("Automates", "https://www.automates.fi/"),
        ("CoE Group", "https://coegroup.fi/palvelut/sahko-ja-automaatiosuunnittelu/tuotantoautomaatio/"),
    ),
}

DEFAULT_REGIONS = ("Helsinki", "Tampere", "Turku", "Oulu")
# Only recognized municipality names may be interpolated into public OSM
# queries. The original site's location is a search hint, not evidence that
# any potential reference is a comparable business.
BENCHMARK_REGIONS = (
    "Helsinki", "Espoo", "Vantaa", "Tampere", "Turku", "Oulu",
    "Jyväskylä", "Lahti", "Kuopio", "Pori", "Joensuu", "Vaasa",
    "Rovaniemi", "Lappeenranta", "Hämeenlinna", "Seinäjoki",
    "Kotka", "Mikkeli", "Porvoo", "Salo", "Rauma", "Kajaani",
)
OSM_CATEGORIES = {
    "kampaamo", "kauneushoitola", "ravintola", "kahvila",
    "autokorjaamo", "hammaslääkäri", "kuntosali", "hotelli",
    "sähköasentaja", "putkimies", "kukkakauppa", "pyöräliike",
    "suutari", "leipomo", "asianajotoimisto",
}
MAX_PUBLIC_REGIONS_PER_LOOKUP = 2


def preferred_benchmark_regions(facts: dict | None = None, original_text: str = "") -> tuple[str, ...]:
    """Prefer a municipality visibly associated with the target company.

    Location only ranks candidate lookups. It does not prove the benchmark,
    supply any client facts, or relax the three source-backed operator gate.
    """
    facts = facts if isinstance(facts, dict) else {}
    hints = " ".join(str(facts.get(k) or "") for k in
                     ("city", "municipality", "location", "address", "street_address"))
    # A structured city explicitly supplied by the source takes priority.
    search_sources = (hints, str(original_text or "")[:10000])
    for raw in search_sources:
        for city in BENCHMARK_REGIONS:
            if re.search(r"(?<!\w)" + re.escape(city) + r"(?!\w)", raw, re.I):
                return (city,) + tuple(region for region in DEFAULT_REGIONS if region != city)
    return DEFAULT_REGIONS


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
        if (host in {"localhost", "localhost.localdomain"}
                or host.endswith((".local", ".internal", ".localhost"))):
            continue
        try:
            if not ipaddress.ip_address(host).is_global:
                continue
        except ValueError:
            pass
        hosts.add(host)
        chosen.append({
            "url": url,
            "title": str(row.get("title") or row.get("name") or "")[:200],
            "content": str(row.get("content") or "")[:1500],
        })
        if len(chosen) >= limit:
            break
    return chosen


def historical_verified_references(category: str) -> list[dict]:
    """Reuse actual source-verified benchmark operators for rare industries."""
    from utils.state import load_companies
    pool = []
    for company in (load_companies() or {}).values():
        if not isinstance(company, dict):
            continue
        research = company.get("research") or {}
        facts = research.get("company_facts") or {}
        raw = " ".join(str(facts.get("industry") or "").casefold().split())
        current_category = normalize_industry(raw) or raw
        if current_category != category:
            continue
        for row in research.get("design_benchmark") or []:
            if not isinstance(row, dict):
                continue
            match = row.get("industry_match") or {}
            quote, text = str(match.get("evidence_quote") or ""), str(row.get("site_text") or "")
            if match.get("same_industry") is True and quote.strip() and quote in text and row.get("url"):
                pool.append({
                    "url": row["url"], "title": row.get("title") or "",
                    "content": text[:1500],
                })
    return pool


def discover_free_references(
    industry: str, *,
    target_url: str = "",
    cache_path: str | Path = "output/_kaurivo_reference_cache.json",
    regions: tuple[str, ...] = DEFAULT_REGIONS,
    max_results: int = 10,
    fetch_osm=None,
    historic_lookup=None,
    now: datetime | None = None,
) -> list[dict]:
    """Reuse an existing industry pool before a couple of fair-use OSM lookups.

    Never return unverified operator suitability: Research checks the websites,
    source quote and business category before selecting its three references.
    """
    category = normalize_industry(industry)
    mapped_to_osm = category in OSM_CATEGORIES
    category = category or " ".join(str(industry or "").casefold().split())
    if not category:
        raise RuntimeError("Industry required for free reference research.")
    historic_lookup = historic_lookup or historical_verified_references
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
    curated = [{"title": name, "url": url}
               for name, url in CURATED_REFERENCE_CANDIDATES.get(category, ())]
    saved = _candidates(list(saved) + list(historic_lookup(category) or []) + curated,
                        target_url=target_url, limit=50)
    if observed_at and timedelta(0) <= now - observed_at <= timedelta(days=CACHE_DAYS):
        results = _candidates(saved, target_url=target_url, limit=max_results)
        # A validated pool of 3+ possible operator URLs can be reused across
        # clients, without re-querying public OSM for every business.
        if len(results) >= 3:
            return results
        # Negative cache: a 24-hour cool-down protects free public infrastructure
        # if this location/category has too few listed company sites.
        if now - observed_at < timedelta(hours=24):
            raise RuntimeError(
                "Insufficient source-backed operator URLs in recent cached "
                "public OSM search; no repeated immediate requests."
            )

    if not mapped_to_osm and len(saved) < 3:
        raise RuntimeError(
            "No trustworthy free OSM mapping or three prior source-verified "
            "references for industry: " + str(industry)
        )
    if fetch_osm is None and mapped_to_osm:
        from agents.scout import _fetch_osm_companies
        fetch_osm = _fetch_osm_companies

    gathered = list(saved)
    # At most two public region lookups, none for sectors satisfied by
    # previously verified operators. Do not flood public Overpass instances.
    for region in (regions[:MAX_PUBLIC_REGIONS_PER_LOOKUP] if mapped_to_osm else ()):
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
    # Save both successful and unsuccessful lookups. A missing operator is
    # never treated as valid, but it prevents hammering free OSM public servers.
    path.parent.mkdir(parents=True, exist_ok=True)
    saved_current = dict(stored)
    saved_current[category] = {
        "updated_at": now.isoformat(),
        "source": "openstreetmap_prior_verified_benchmarks_and_curated_candidates",
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

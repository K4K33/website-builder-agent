"""Kaurivo nightly prospecting pilot. NO AI, no email, no demo publishing.

At most ONE public Overpass request per pilot run. Zero OpenRouter/Tavily
credits. Candidate data is NOT verified business/site evidence. Commercial
production-scale scraping requires a compliant dedicated data source.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
import json
from pathlib import Path
import re

import requests
from utils.quality import canonical_url
from agents.scout import _build_overpass_query

# Deliberately conservative: one location / trade per night, rotating.
# No concurrent public Overpass requests, and no automatic retry.
ROTATION = (
    ("putkimies", "Tampere"),
    ("autokorjaamo", "Turku"),
    ("kampaamo", "Lahti"),
    ("sähköasentaja", "Jyväskylä"),
    ("kauneushoitola", "Kuopio"),
    ("kuntosali", "Oulu"),
    ("autokorjaamo", "Espoo"),
    ("putkimies", "Vantaa"),
    ("kampaamo", "Pori"),
    ("kahvila", "Joensuu"),
    ("ravintola", "Vaasa"),
    ("sähköasentaja", "Helsinki"),
)
PUBLIC_PILOT_URL = "https://overpass-api.de/api/interpreter"
MAX_RETURNED_ELEMENTS = 120
MAX_SAVED_HISTORY = 1000
USER_AGENT = "KaurivoNightlyPilot/0.1 (small-scale company discovery; no automatic email)"


def choose_rotation(day: date):
    return ROTATION[(day.toordinal() - 1) % len(ROTATION)]


def _one_line(text, limit=90):
    return re.sub(r"[\x00-\x1f\x7f]", " ", str(text or "")).strip()[:limit]


def normalize_candidate(element, city, industry):
    """Only OSM object identity, public business name and public site link."""
    if not isinstance(element, dict):
        return None
    kind, osm_id = element.get("type"), element.get("id")
    if kind not in {"node", "way", "relation"} or type(osm_id) is not int or osm_id <= 0:
        return None
    tags = element.get("tags") or {}
    if not isinstance(tags, dict):
        return None
    name = _one_line(tags.get("name") or tags.get("brand"))
    if len(name) < 2:
        return None
    web = canonical_url(tags.get("website") or tags.get("contact:website"))
    return {
        "identity": f"osm:{kind}:{osm_id}",
        "name": name,
        "industry_category_hint": industry,
        "city_hint": city,
        "website_listed_url": web,
        "site_discovery_status": "listed_needs_review" if web else "not_listed_needs_review",
        "business_activity": "unverified",
        "website_absence_verified": False,
        "brand_and_services_verified": False,
        "demo_authorized": False,
        "outreach_authorized": False,
        "source_url": f"https://www.openstreetmap.org/{kind}/{osm_id}",
    }


def parse_elements(elements, city, industry, *, seen=(), limit=5):
    if not isinstance(elements, list) or not 1 <= limit <= 10:
        raise ValueError("Expected an OSM element list and a limit in 1..10")
    old = set(seen)
    unique = {}
    for element in elements[:MAX_RETURNED_ELEMENTS]:
        candidate = normalize_candidate(element, city, industry)
        if not candidate:
            continue
        ident = candidate["identity"]
        if ident not in old and ident not in unique:
            unique[ident] = candidate
    # Missing OSM website tag is only a lookup priority, NOT proof of absence.
    rows = sorted(unique.values(), key=lambda v: (
        v["site_discovery_status"] != "not_listed_needs_review",
        v["name"].casefold(), v["identity"],
    ))
    return rows[:limit]


def query_once(day, *, post=requests.post):
    industry, city = choose_rotation(day)
    q = _build_overpass_query(industry, city)
    assert q.endswith("out center tags;\n")
    q = q.replace("out center tags;\n", f"out center tags {MAX_RETURNED_ELEMENTS};\n")
    response = post(
        PUBLIC_PILOT_URL,
        data=q.encode("utf-8"),
        headers={"User-Agent": USER_AGENT, "Accept": "application/json"},
        timeout=35,
    )
    # A 429 / 406 is a stopping condition; never retry another instance.
    response.raise_for_status()
    result = response.json()
    if not isinstance(result, dict) or not isinstance(result.get("elements"), list):
        raise RuntimeError("Unexpected or missing Overpass elements; results not trusted.")
    return city, industry, result["elements"]


def _load_seen(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        values = data.get("seen_ids") or []
        if not isinstance(values, list):
            raise ValueError()
        return [str(x) for x in values if re.fullmatch(r"osm:(node|way|relation):[0-9]+", str(x))][-MAX_SAVED_HISTORY:]
    except (FileNotFoundError, ValueError, TypeError, OSError):
        return []


def _save_json(path, obj):
    Path(path).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _md(s):
    return _one_line(s, 180).replace("|", "&#124;").replace("[", "&#91;").replace("]", "&#93;")


def make_report(rows, day, mode, city, industry, source_ok=True):
    lines = [
        f"# Kaurivo nightly prospecting — {day.isoformat()}",
        "",
        f"**Mode:** {mode}. **Area:** {city}. **Category hint:** {industry}.",
        f"**New companies for human review:** {len(rows)}.",
        "",
        "These are **leads to verify**, NOT confirmed firms needing redesigns.",
        "OSM missing website tags NEVER prove that a firm has no website.",
        "Check actual operations, ownership, services, affordability, website status,",
        "site quality, company brand rights and appropriateness of contact.",
        "",
        "| Company | Site listed? | Public source | Next step |",
        "|---|---|---|---|",
    ]
    for r in rows:
        status = "Listed URL" if r["website_listed_url"] else "No URL listed (unverified)"
        lines.append(
            f"| {_md(r['name'])} | {status} | [OSM record]({r['source_url']}) | "
            "Human identity + website verification |"
        )
    lines += [
        "", "## Premium demo and ethical outreach gates", "",
        "1. Independently verify business active and website/no-website status.",
        "2. Record the firm's real services, original approved logo, palette, photos and protected copy.",
        "3. Compare three real same-industry sites, with actual desktop/mobile screenshots.",
        "4. Make a bespoke premium demo: major visual improvement, brand kept on redesigns;",
        "   new sites get original design. All services and images grounded, no invented claims.",
        "5. Test links, responsive widths 320/390/768/1440, visual polish, motion and accessibility.",
        "6. Owner approves actual demo, business benefits and individualized outreach copy.",
        "7. Only after explicit per-recipient approval may Kaurivo Gmail send the message.",
        "",
        "**This run did not build or publish demos, draft or send email, use paid AI,",
        "or authorize marketing.** Source: public OpenStreetMap/Overpass, with attribution.",
        "Pilot only, never scale public Overpass for a commercial prospecting service.",
        "",
    ]
    return "\n".join(lines)


def run(*, mode="offline", output_dir="output/nightly", seen_path="data/nightly_seen.json",
        day=None, max_candidates=5, post=requests.post, fixture=None):
    """Run one night. offline/fixture make ZERO network calls, pilot-live makes ONE."""
    if mode not in {"offline", "fixture", "pilot-live"}:
        raise ValueError("Only offline, fixture and pilot-live modes are supported.")
    if not type(max_candidates) is int or not 1 <= max_candidates <= 10:
        raise ValueError("max_candidates must be an integer 1..10")
    today = day or date.today()
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    seen = _load_seen(seen_path)
    city, industry = choose_rotation(today)
    network_requests = 0
    if mode == "pilot-live":
        # Intentionally no TAVILY/AI token access, no retries or paid requests.
        network_requests = 1
        city, industry, elements = query_once(today, post=post)
        rows = parse_elements(elements, city, industry, seen=seen,
                              limit=max_candidates)
    elif mode == "fixture":
        if not fixture:
            raise ValueError("fixture mode needs an explicit local fixture.")
        data = json.loads(Path(fixture).read_text(encoding="utf-8"))
        rows = parse_elements(data["elements"], city, industry, seen=seen,
                              limit=max_candidates)
    else:
        # Offline mode tests the report process; never pretends to have
        # discovered companies or silently makes a public data request.
        rows = []
    new_ids = [r["identity"] for r in rows]
    seen_updated = (seen + new_ids)[-MAX_SAVED_HISTORY:]
    _save_json(out / "candidates.json", {
        "date": today.isoformat(), "mode": mode, "candidates": rows,
        "not_verified_for_outreach": True,
    })
    _save_json(out / "status.json", {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "mode": mode, "source": "OpenStreetMap/Overpass" if mode == "pilot-live" else "local",
        "new_candidates": len(rows), "one_public_request_cap": True,
        "external_requests_this_run": network_requests,
        "openrouter_requests": 0, "tavily_requests": 0,
        "demo_built": 0, "emails_drafted": 0, "emails_sent": 0,
        "outreach_or_approval": False,
    })
    (out / "shortlist.md").write_text(
        make_report(rows, today, mode, city, industry), encoding="utf-8"
    )
    sp = Path(seen_path)
    sp.parent.mkdir(parents=True, exist_ok=True)
    _save_json(sp, {"seen_ids": seen_updated})
    return {"count": len(rows), "requests": network_requests, "output": str(out)}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("offline", "fixture", "pilot-live"), default="offline")
    parser.add_argument("--output-dir", default="output/nightly")
    parser.add_argument("--seen-path", default="data/nightly_seen.json")
    parser.add_argument("--fixture")
    parser.add_argument("--max-candidates", type=int, default=5)
    args = parser.parse_args(argv)
    result = run(mode=args.mode, output_dir=args.output_dir, seen_path=args.seen_path,
                 fixture=args.fixture, max_candidates=args.max_candidates)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()

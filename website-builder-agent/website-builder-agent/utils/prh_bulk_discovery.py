"""National scale prospect discovery from ONE daily PRH bulk ZIP.

PRH/YTJ open data (CC BY 4.0):
https://avoindata.prh.fi/opendata-ytj-api/v3/all_companies
The ZIP contains businesses registered/pending with the trade register,
excluding private traders; NOT proof a business is currently operating.
No phone/email or website-absence evidence can be inferred from this feed.

All parsing happens offline from one downloaded archive. Network downloads
are permitted only by explicit --mode pilot-live; no hidden other requests.
"""
from __future__ import annotations

import argparse
from datetime import date, datetime, timezone
from hashlib import sha256
import heapq
import io
import json
from pathlib import Path
import re
import tempfile
from urllib.parse import urlsplit
import zipfile

import ijson
import requests

PRH_URL = "https://avoindata.prh.fi/opendata-ytj-api/v3/all_companies"
PRH_SOURCE = "https://avoindata.prh.fi/fi/ytj/swagger-ui"
MAX_ZIP_BYTES = 650 * 1024 * 1024
MAX_UNPACKED_BYTES = 3 * 1024 * 1024 * 1024
MAX_HISTORY = 250_000
MAX_BATCH = 5000
MAX_SHORTLIST = 50


def _one_line(text, max_length=150):
    return re.sub(r"[\x00-\x1f\x7f]", " ", str(text or "")).strip()[:max_length]


def _url(url):
    if not isinstance(url, str) or not url.strip():
        return ""
    url = url.strip()
    if "://" not in url:
        url = "https://" + url
    p = urlsplit(url)
    if p.scheme not in ("http", "https") or not p.hostname or p.username or p.password:
        return ""
    return "https://" + p.netloc.lower() + p.path.rstrip("/")


def _name(record):
    names = record.get("names") or []
    if not isinstance(names, list):
        return ""
    # PRH schema says version 1 is the CURRENT registered name.
    # Never choose an old trade name just because it appeared first.
    current = [n for n in names if isinstance(n, dict)
               and n.get("version") == 1
               and isinstance(n.get("name"), str) and n["name"].strip()
               and not n.get("endDate")]
    fallback = [n for n in names if isinstance(n, dict)
                and isinstance(n.get("name"), str) and n["name"].strip()
                and not n.get("endDate")]
    for n in current or fallback:
        return _one_line(n["name"], 110)
    return ""


def _city(record):
    addresses = record.get("addresses") or []
    if not isinstance(addresses, list):
        return ""
    for a in addresses:
        if not isinstance(a, dict):
            continue
        offices = a.get("postOffices") or []
        if not isinstance(offices, list):
            continue
        for item in offices:
            if isinstance(item, dict):
                name = item.get("city") or item.get("name")
                if isinstance(name, str) and name.strip():
                    return _one_line(name, 60)
    return ""


def normalize_company(record):
    """Keep minimal, source-referenced registry facts; nothing about poor sites."""
    if not isinstance(record, dict) or record.get("endDate"):
        return None
    obj = record.get("businessId") or {}
    business_id = obj.get("value") if isinstance(obj, dict) else ""
    if not isinstance(business_id, str) or not re.fullmatch(r"[0-9]{7}-[0-9]", business_id):
        return None
    name = _name(record)
    if len(name) < 2:
        return None
    website = record.get("website") or {}
    if isinstance(website, dict):
        website = website.get("url")
    if isinstance(website, str):
        try:
            website = _url(website)
        except ValueError:
            website = ""
    else:
        website = ""
    line = record.get("mainBusinessLine") or {}
    industry = _one_line(line.get("type"), 6) if isinstance(line, dict) else ""
    return {
        "identity": "prh:" + business_id,
        "business_id": business_id,
        "name": name,
        "city_hint": _city(record),
        "industry_code_hint": industry,
        "website_listed_url": website,
        "site_discovery_status": "listed_needs_review" if website else "not_listed_needs_review",
        "business_activity": "unverified",
        "website_absence_verified": False,
        "brand_and_services_verified": False,
        "demo_authorized": False,
        "outreach_authorized": False,
        "source_url": PRH_SOURCE,
        "prh_attribution": "Source: PRH/YTJ open data, CC BY 4.0",
    }


def iter_bulk_records(archive_path):
    """Stream the archive member instead of loading all companies in memory."""
    with zipfile.ZipFile(archive_path) as archive:
        files = [m for m in archive.infolist() if not m.is_dir()
                 and m.filename.lower().endswith(".json")]
        if len(files) != 1:
            raise RuntimeError("PRH archive must have exactly one JSON file")
        member = files[0]
        if member.file_size > MAX_UNPACKED_BYTES:
            raise RuntimeError("PRH archive exceeds uncompressed safety cap")
        # Reject absolute/relative archive paths, even though files are never
        # extracted, to make the source contract explicit.
        if Path(member.filename).is_absolute() or ".." in Path(member.filename).parts:
            raise RuntimeError("Unexpected archive member path")
        with archive.open(member) as zipped:
            buffered = io.BufferedReader(zipped)
            first = buffered.peek(4096).lstrip()
            if first.startswith(b"["):
                prefix = "item"
            elif first.startswith(b"{"):
                # Schema's /companies responses contain {"companies":[...]};
                # the bulk archive may use the same envelope.
                prefix = "companies.item"
            else:
                raise RuntimeError("Unknown PRH JSON root")
            yielded = 0
            for record in ijson.items(buffered, prefix):
                yielded += 1
                yield record
            if yielded == 0:
                raise RuntimeError("PRH archive was empty/unrecognized; do not claim full coverage")


def download_once(path, *, get=requests.get):
    """Only one HTTP GET; no retry, hard download and archive safety limits."""
    with get(
        PRH_URL, headers={"Accept": "application/zip",
                          "User-Agent": "KaurivoProspectResearch/0.1 (PRH attributed bulk open-data pilot)"},
        stream=True, timeout=(12, 160),
    ) as response:
        response.raise_for_status()
        size = 0
        path = Path(path)
        with path.open("wb") as out:
            for chunk in response.iter_content(chunk_size=1024*1024):
                if not chunk:
                    continue
                size += len(chunk)
                if size > MAX_ZIP_BYTES:
                    raise RuntimeError("PRH ZIP download hit hard safety limit")
                out.write(chunk)
    if not zipfile.is_zipfile(path):
        raise RuntimeError("PRH source did not return a valid ZIP")
    return size


def _read_seen(path):
    try:
        data = json.loads(Path(path).read_text(encoding="utf-8"))
        arr = data.get("ids") or []
        if not isinstance(arr, list):
            raise ValueError()
        return [a for a in arr if isinstance(a, str)
                and re.fullmatch(r"prh:[0-9]{7}-[0-9]", a)][-MAX_HISTORY:]
    except (OSError, ValueError, TypeError):
        return []


def _write(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                          encoding="utf-8")


def _offer(heap, item, max_size):
    # Deterministic daily pseudo-random sampling avoids always choosing
    # alphabetical firms and distributes across all source regions.
    neg_score, identity, company = item
    if len(heap) < max_size:
        heapq.heappush(heap, (neg_score, identity, company))
    elif item > heap[0]:
        heapq.heapreplace(heap, (neg_score, identity, company))


def rank_bulk(records, *, day, seen=(), max_candidates=5000, shortlist_size=50):
    if not 1 <= max_candidates <= MAX_BATCH or not 1 <= shortlist_size <= MAX_SHORTLIST:
        raise ValueError("Invalid batch/shortlist limits")
    old = set(seen)
    pools = {"no_url": [], "url_listed": []}
    scanned, valid, skipped = 0, 0, 0
    for raw in records:
        scanned += 1
        company = normalize_company(raw)
        if not company:
            continue
        valid += 1
        if company["identity"] in old:
            skipped += 1
            continue
        category = "url_listed" if company["website_listed_url"] else "no_url"
        payload = (day.isoformat() + "|" + company["identity"]).encode("utf-8")
        score = int.from_bytes(sha256(payload).digest()[:8], "big")
        _offer(pools[category], (-score, company["identity"], company), max_candidates)
    # Spread across both types: 70% unlisted URLs, 30% known-site leads.
    # Missing website tags do NOT prove no website exists.
    no_count = round(max_candidates * .7)
    both = [
        sorted(pools["no_url"], reverse=True)[:no_count],
        sorted(pools["url_listed"], reverse=True)[:max_candidates-no_count],
    ]
    selected = [v[2] for group in both for v in group]
    # Fill empty category capacity from the other pool without duplicates.
    if len(selected) < max_candidates:
        selected_ids = {v["identity"] for v in selected}
        rest = sorted((item for group in pools.values() for item in group
                       if item[2]["identity"] not in selected_ids), reverse=True)
        selected += [v[2] for v in rest[:max_candidates-len(selected)]]
    # Mix both kinds in the morning review list, rather than filling the
    # first 50 slots exclusively with companies lacking a PRH website tag.
    no_site = [c for c in selected if not c["website_listed_url"]]
    known_site = [c for c in selected if c["website_listed_url"]]
    shortlist = (no_site[:round(shortlist_size * .7)]
                 + known_site[:shortlist_size-round(shortlist_size * .7)])
    if len(shortlist) < shortlist_size:
        chosen = {c["identity"] for c in shortlist}
        shortlist += [c for c in selected if c["identity"] not in chosen][
            :shortlist_size-len(shortlist)
        ]
    return {
        "scanned_registry_records": scanned,
        "valid_registry_records": valid,
        "previously_seen_skipped": skipped,
        "new_candidates": selected,
        "shortlist": shortlist,
        "candidates_with_unlisted_url": sum(not x["website_listed_url"] for x in selected),
        "candidates_with_listed_url": sum(bool(x["website_listed_url"]) for x in selected),
    }


def report_md(data, day, *, mode):
    rows = [
        f"# Kaurivo national company discovery — {day.isoformat()}",
        "",
        f"**Mode:** {mode} | **Registry records examined:** {data['scanned_registry_records']:,} | "
        f"**New leads queued:** {len(data['new_candidates']):,} | "
        f"**Previously seen:** {data['previously_seen_skipped']:,}",
        "",
        "Source: PRH/YTJ open data, CC BY 4.0. https://avoindata.prh.fi/",
        "",
        "**Important:** No URL listed in PRH DOES NOT prove a missing website.",
        "The register alone DOES NOT prove business activity, financial capacity,",
        "web design quality, marketing permission or image rights.",
        "",
        "| Business | City hint | Website field | Reference |",
        "|---|---|---|---|",
    ]
    for company in data["shortlist"]:
        clean = lambda x: _one_line(x, 100).replace("|", "&#124;").replace("[", "&#91;")
        listed = "Listed" if company["website_listed_url"] else "Not listed (unverified)"
        rows.append(f"| {clean(company['name'])} | {clean(company['city_hint'])} | "
                    f"{listed} | {company['business_id']} |")
    rows += ["", "## Next step: verified needs and premium demo", "",
             "Check actual business, site status, brand identity and commercial relevance",
             "before any independent research, demo, email draft or client contact.",
             "Only build bespoke top-quality demos with actual sector benchmarks",
             "and full real-browser QA. Every final client delivery needs a working CMS.",
             "",
             "**This nightly run has NOT built demos, approved outreach or sent mail.**", ""]
    return "\n".join(rows)


def research_queue_md(shortlist, day):
    """Create research instructions using real registry hints, not invented site audits.

    The per-company brief is deliberately marked unverified until a reviewer
    inspects operating activity, the current website and three real peers.
    A published sales demo or marketing email must never be inferred.
    """
    lines = [
        "# Kaurivo — yksilölliset tutkimustehtävät / " + day.isoformat(),
        "",
        "Lähde: PRH/YTJ avoin data, CC BY 4.0.",
        "Nämä ovat taustatutkimustehtäviä, EIVÄT valmiita verkkosivudemoja.",
        "Vähintään kolme oikeaa saman alan kilpailija-/vertailusivua ja",
        "asiakkaan nykyinen visuaalinen ilme tarkistetaan ennen rakentamista.",
        "",
    ]
    for idx, c in enumerate(shortlist, 1):
        company = _one_line(c.get("name"), 110).replace("\\n", " ")
        city = _one_line(c.get("city_hint"), 80)
        sector = _one_line(c.get("industry_code_hint"), 16) or "ei listattu"
        site = c.get("website_listed_url") or "Ei PRH-listausta: ETSI verkosta ennen sivuttomuusväitettä"
        lines.extend([
            f"## {idx:02d}. {company} ({c['business_id']})",
            f"PRH-kaupunki: {city or 'ei tiedossa'} | Toimialakoodi: {sector}",
            f"PRH-verkkosivuvihje: {site}",
            "- [ ] Tarkista yrityksen aktiivinen toiminta ja juridinen tila",
            "- [ ] Selvitä todellinen verkkosivusto, mobiilikäyttö ja yhteydenoton polku",
            "- [ ] Tarkista yrityksen nykyiset logot, värit, palvelut ja kuvaoikeudet",
            "- [ ] Vertaa kolmeen oikeaan saman alan korkeatasoiseen sivustoon",
            "- [ ] Tarkista maksukyvyn suunta tilinpäätöksestä (ellei saatavilla: tuntematon)",
            "- [ ] Kirjaa yksi todellinen ongelma tai saavutettava asiakashyöty",
            "- [ ] Toteuta yksilöllinen responsive/CMS-valmis premium-demo, jos hyväksytty",
            "- [ ] Testaa työpöytä/mobiili, linkit, saavutettavuus ja reduced motion",
            "- [ ] Pyydä lopullinen visuaalinen laadun hyväksyntä ennen myyntiviestiä",
            "- [ ] Yhteystiedot, sähköpostin laillisuus ja lähetyslupa erikseen",
            "",
        ])
    lines.append("Ei automaattisia myyntiviestejä, väitettyjä referenssejä tai keksittyjä asiakaskuvia.")
    return "\\n".join(lines) + "\\n"


def run(*, mode="offline", archive=None, output_dir="output/nightly-prh",
        seen_path="data/prh_seen_ids.json", day=None,
        max_candidates=5000, shortlist_size=50, get=requests.get):
    if mode not in ("offline", "fixture", "pilot-live"):
        raise ValueError("Unsupported mode")
    today = day or date.today()
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    seen = _read_seen(seen_path)
    network_calls = 0
    with tempfile.TemporaryDirectory(prefix="prh-bulk-") as tmp:
        if mode == "pilot-live":
            network_calls = 1
            zip_path = Path(tmp) / "prh.zip"
            byte_count = download_once(zip_path, get=get)
        elif mode == "fixture":
            if not archive:
                raise ValueError("fixture requires --archive")
            zip_path = Path(archive)
            byte_count = zip_path.stat().st_size
        else:
            zip_path = None
            byte_count = 0
        if zip_path:
            result = rank_bulk(iter_bulk_records(zip_path), day=today,
                               seen=seen, max_candidates=max_candidates,
                               shortlist_size=shortlist_size)
        else:
            result = rank_bulk((), day=today, seen=seen,
                               max_candidates=max_candidates,
                               shortlist_size=shortlist_size)
    shortlist = result["shortlist"]
    selected = result["new_candidates"]
    # Keep prior IDs + genuinely selected new IDs, not *every* registry item
    # (otherwise businesses we have not yet evaluated would be lost).
    merged_seen = (seen + [c["identity"] for c in selected])[-MAX_HISTORY:]
    _write(out / "candidates.json", {
        "date": today.isoformat(), "mode": mode, "candidates": selected,
        "not_verified_for_outreach": True, "source": PRH_SOURCE,
    })
    # A private-CRM import packet contains only public PRH company data,
    # never personal contact info, invented financials or auto-approval.
    _write(out / "crm-shortlist.json", {
        "schema": "kaurivo_prh_shortlist_v1",
        "date": today.isoformat(),
        "mode": mode,
        "source": PRH_SOURCE,
        "source_attribution": "PRH/YTJ open data, CC BY 4.0",
        "review_required": True,
        "not_verified_for_outreach": True,
        "candidates": shortlist,
    })
    _write(out / "status.json", {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "mode": mode, "registry_records_scanned": result["scanned_registry_records"],
        "new_candidates": len(selected), "unlisted_site_candidates":
            result["candidates_with_unlisted_url"],
        "listed_site_candidates": result["candidates_with_listed_url"],
        "previously_seen_skipped": result["previously_seen_skipped"],
        "downloaded_zip_bytes": byte_count,
        "external_requests": network_calls, "ai_credits_used": 0,
        "demos_generated": 0, "emails_drafted": 0, "emails_sent": 0,
    })
    (out / "shortlist.md").write_text(report_md(result, today, mode=mode), encoding="utf-8")
    (out / "research-briefs.md").write_text(
        research_queue_md(shortlist, today), encoding="utf-8")
    seen_file = Path(seen_path)
    seen_file.parent.mkdir(parents=True, exist_ok=True)
    _write(seen_file, {"ids": merged_seen})
    return {"scanned": result["scanned_registry_records"], "new": len(selected),
            "shortlisted": len(shortlist), "requests": network_calls}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("offline", "fixture", "pilot-live"), default="offline")
    parser.add_argument("--archive", help="Local ZIP file only for fixture mode")
    parser.add_argument("--output-dir", default="output/nightly-prh")
    parser.add_argument("--seen-path", default="data/prh_seen_ids.json")
    parser.add_argument("--max-candidates", type=int, default=5000)
    parser.add_argument("--shortlist-size", type=int, default=50)
    args = parser.parse_args(argv)
    print(json.dumps(run(mode=args.mode, archive=args.archive,
                         output_dir=args.output_dir, seen_path=args.seen_path,
                         max_candidates=args.max_candidates,
                         shortlist_size=args.shortlist_size), ensure_ascii=False))


if __name__ == "__main__":
    main()

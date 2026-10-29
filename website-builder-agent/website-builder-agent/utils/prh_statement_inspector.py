"""Read one PRH public digital financial statement without guessing P&L figures.

Safe, size-bounded XML fact inventory. XBRL concept names are taxonomy identifiers:
a number can NEVER be labelled sales, profit, equity or cash without verifying the
appropriate taxonomy, reporting context and sign/scale convention.
No third-party API, generative AI, customer outreach or automated finance promotion.
"""
import hashlib
import re
import xml.etree.ElementTree as ET
from datetime import date

import requests

from utils.lead_intelligence import finnish_business_id
from utils.prh_financials import STATEMENT

MAX_BYTES = 2_000_000
MAX_FACTS = 80
MAX_CONCEPTS_SEEN = 20_000
ALLOWED_CONTENT_TYPES = ("text/xml", "application/xml", "application/xhtml+xml")
_HEADERS = {
    "Accept": "text/xml, application/xml",
    "User-Agent": "KaurivoWebsiteBuilder/0.3 (PRH open-data attribution)",
}


def _download_statement(business_id, period, timeout=12, max_bytes=MAX_BYTES):
    """Stream a single official source, bounded before parsing."""
    if not finnish_business_id(business_id):
        raise ValueError("Valid Finnish business ID required.")
    try:
        date_value = date.fromisoformat(period)
    except (ValueError, TypeError) as exc:
        raise ValueError("Valid financial period end YYYY-MM-DD required.") from exc
    if date_value > date.today():
        raise ValueError("Cannot fetch a future financial period.")
    if not isinstance(max_bytes, int) or isinstance(max_bytes, bool) or not 1024 <= max_bytes <= MAX_BYTES:
        raise ValueError("max_bytes must be 1024..2000000.")
    with requests.get(
        STATEMENT,
        params={"businessId": business_id, "financialDate": period},
        headers=_HEADERS,
        timeout=timeout,
        stream=True,
    ) as response:
        response.raise_for_status()
        mimetype = response.headers.get("Content-Type", "").split(";")[0].strip().lower()
        if mimetype not in ALLOWED_CONTENT_TYPES:
            raise RuntimeError("PRH statement did not return XML; refuse to parse.")
        byte_count = 0
        chunks = []
        for chunk in response.iter_content(chunk_size=65536):
            if not chunk:
                continue
            byte_count += len(chunk)
            if byte_count > max_bytes:
                raise RuntimeError("PRH XML statement is too large for safe inspection.")
            chunks.append(chunk)
        return b"".join(chunks)


def _local_tag(name):
    return name.rsplit("}", 1)[-1].casefold()


def inspect_xml_document(payload, business_id, financial_period):
    """Extract a bounded, unclassified inventory of report facts.

    No numeric amount is returned as verified. Inline-XBRL and XBRL instance
    elements are both supported for inspection, not accounting interpretation.
    """
    if not finnish_business_id(business_id):
        raise ValueError("Invalid business identity.")
    if not isinstance(payload, (bytes, bytearray)) or not payload or len(payload) > MAX_BYTES:
        raise ValueError("Statement must be non-empty bounded XML bytes.")
    prefix = bytes(payload[:1000]).upper()
    if b"<!DOCTYPE" in bytes(payload).upper() or b"<!ENTITY" in bytes(payload).upper():
        raise ValueError("External entities and DOCTYPE are not allowed.")
    try:
        tree = ET.fromstring(payload)
    except ET.ParseError as exc:
        raise RuntimeError("PRH response is not well-formed XML.") from exc

    # All returned facts are candidate inventory entries, not financial decisions.
    records, seen = [], set()
    scanned = 0
    for element in tree.iter():
        scanned += 1
        if scanned > MAX_CONCEPTS_SEEN:
            raise RuntimeError("XBRL XML is too complex for bounded inspection.")
        attrs = element.attrib
        tag = _local_tag(element.tag)
        is_inline = tag == "nonfraction" and ("name" in attrs or "name" in { _local_tag(k) for k in attrs })
        is_instance = (not is_inline and tag not in {"unit", "measure", "context", "instant", "startdate", "enddate", "identifier"}
                       and any(_local_tag(k) == "contextref" for k in attrs))
        if not (is_inline or is_instance):
            continue
        name = str(attrs.get("name", element.tag)).strip()
        context = next((str(v) for k, v in attrs.items() if _local_tag(k) == "contextref"), "")
        unit = next((str(v) for k, v in attrs.items() if _local_tag(k) == "unitref"), "")
        if not name or not context or not unit:
            # Money-like facts need context/unit references to be useful.
            continue
        rendered = "".join(element.itertext()).strip()
        rendered = re.sub(r"\s+", " ", rendered)
        if not rendered or len(rendered) > 80:
            continue
        key = (name, context, unit, rendered)
        if key in seen:
            continue
        seen.add(key)
        records.append({
            "taxonomy_concept": name[:150], "context_ref": context[:100],
            "unit_ref": unit[:80], "display_value": rendered[:80],
            "scale": str(attrs.get("scale", ""))[:16],
            "sign": str(attrs.get("sign", ""))[:8],
            "decimals": str(attrs.get("decimals", ""))[:16],
            "human_verified": False,
        })
        if len(records) == MAX_FACTS:
            break
    return {
        "status": "taxonomy_review_required",
        "business_id": business_id,
        "financial_period": financial_period,
        "source_url": STATEMENT + "?businessId=" + business_id + "&financialDate=" + financial_period,
        "sha256": hashlib.sha256(payload).hexdigest(),
        "fact_candidates": records,
        "financial_figures_verified": False,
        "currency_and_period_verified": False,
        "revenue_eur": None, "operating_profit_eur": None,
        "note": ("Taxonomy-dependent raw display values only. No amounts may be "
                 "used for commercial financial qualification before a "
                 "separate human review of context, units, scale and signs."),
    }


def inspect_latest_statement(company, downloader=_download_statement):
    financials = company.get("financials") or {}
    identity = company.get("registry_evidence") or {}
    business_id = financials.get("business_id")
    availability = company.get("financial_availability") or {}
    if not (business_id and financials.get("business_id_verified") is True
            and identity.get("business_id") == business_id):
        raise RuntimeError("Company must have independently verified PRH identity first.")
    if availability.get("status") != "available":
        raise RuntimeError("No official digital financial period is available.")
    period = availability.get("latest_financial_date")
    if not isinstance(period, str) or period not in availability.get("financial_dates", []):
        raise RuntimeError("Latest financial period is not tied to an official PRH lookup.")
    return inspect_xml_document(downloader(business_id, period), business_id, period)

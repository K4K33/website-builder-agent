"""Bound long free-cloud research inputs without discarding source evidence.

This is ONLY an AI-facing observation packet. The full unchanged original
site inventory, exact page headings, photos, assets, customer task manifest
and screenshot files remain in private checkpoints and mandatory QA.
Never infer absent facts from compact text, or pass a digest as content.
"""
from __future__ import annotations

import json
import re

MAX_RESEARCH_PACKET_CHARS = 85000
IMPORTANT = re.compile(
    r"(?i)(lounas|menu|ruokalist|allerg|gluteen|laktoos|vegaan|"
    r"aukiol|avoin|opening|contact|yhteys|osoite|address|"
    r"puhelin|phone|email|sähköpost|hinn|price|tuote|product|"
    r"tilaa|varaa|booking|reservation|tarjous|discount|"
    r"yhteistyö|partner|sponsor|arvio|review|gallery|"
    r"kuvagaller|ennen.?jälkeen|video|3d|animaatio|"
    r"toimitus|delivery|return|palautus|booking)"
)


def _short(value: object, cap: int) -> str:
    return str(value or "")[:cap]


def _evidence_fields(value: object, *, char_limit: int = 1050) -> object:
    """Return observed source snippets only; never create substitute claims."""
    if isinstance(value, dict):
        result = {}
        for k, v in value.items():
            if not isinstance(k, str) or len(result) >= 12:
                continue
            if isinstance(v, (str, int, float, bool)) or v is None:
                result[k] = v if not isinstance(v, str) else v[:175]
            elif isinstance(v, list):
                result[k] = [_evidence_fields(x, char_limit=180) for x in v[:4]]
            elif isinstance(v, dict):
                result[k] = _evidence_fields(v, char_limit=300)
        if len(json.dumps(result, ensure_ascii=False)) <= char_limit:
            return result
        # Do not cut through a URL or imply an incomplete evidence item is
        # accurate. Keep a smaller number of COMPLETE observed fields.
        while result and len(json.dumps(result, ensure_ascii=False)) > char_limit:
            result.pop(next(reversed(result)))
        return result
    if isinstance(value, list):
        out = [_evidence_fields(x, char_limit=200) for x in value[:4]]
        while out and len(json.dumps(out, ensure_ascii=False)) > char_limit:
            out.pop()
        return out
    return _short(value, min(char_limit, 175))


def _selected_site_text(source_text: object, cap: int) -> str:
    """Original-only text snippets: lead, source-critical lines and last text."""
    original = str(source_text or "")
    if len(original) <= cap:
        return original
    if cap < 300:
        return original[:cap]
    lead = original[: max(350, cap // 3)]
    tail = original[-max(180, cap // 7):]
    remaining = cap - len(lead) - len(tail) - 70
    sections = []
    seen = set()
    if remaining > 50:
        for line in original.splitlines():
            s=line.strip()
            if (s and IMPORTANT.search(s)
                    and s not in seen and s not in lead and s not in tail):
                if len(s) > remaining:
                    s = s[:remaining]
                sections.append(s)
                seen.add(s)
                remaining -= len(s) + 2
                if remaining < 50:
                    break
    return (lead + "\n[Other original text retained in source inventory]\n"
            + "\n".join(sections) + "\n" + tail)[:cap]


def _observed_headings(value: object) -> list[str]:
    """Original crawler stores h1/h2/h3 in a dict; fixtures may use lists.

    Never invent a heading or rewrite it. The full source manifest is still
    the authoritative section coverage evidence used for published QA.
    """
    if isinstance(value, dict):
        items = []
        for level in ("h1", "h2", "h3", "h4"):
            observed = value.get(level) or []
            if isinstance(observed, list):
                items.extend(observed)
            elif isinstance(observed, str):
                items.append(observed)
    elif isinstance(value, list):
        items = value
    elif isinstance(value, str):
        items = [value]
    else:
        items = []
    return [_short(x, 180) for x in items[:45] if isinstance(x, (str, int))]


def pack_research_source_excerpts(excerpts: list[dict], *,
                                   max_chars: int = MAX_RESEARCH_PACKET_CHARS
                                   ) -> list[dict]:
    """Cover EVERY page and keep original source identity in separate evidence.

    A compact packet is NOT the complete source; the original inventory and
    source_manifest still govern site copy, sections, branding and QA.
    """
    if not isinstance(excerpts, list) or not excerpts:
        raise ValueError("research source packet requires observed pages")
    if not 12000 <= max_chars <= MAX_RESEARCH_PACKET_CHARS:
        raise ValueError("research packet limit is invalid")
    if len(excerpts) > 30:
        raise ValueError("research packet has unbounded page count")
    if any(not isinstance(p, dict) or not p.get("url") for p in excerpts):
        raise ValueError("research packet contains a page without source URL")
    for text_cap in (3400, 2700, 2000, 1400, 900, 450):
        packet = []
        for i, source in enumerate(excerpts):
            per_cap = text_cap + (1500 if i == 0 else 0)
            obj = {
                "url": str(source["url"]),
                "title": _short(source.get("title"), 250),
                # All original headings are retained exactly in the
                # separate mandatory source_manifest, not pruned here.
                "headings": _observed_headings(source.get("headings")),
                "text_excerpts": _selected_site_text(source.get("text"), per_cap),
                "source_identity_observations": _evidence_fields(source.get("source_identity"), char_limit=900),
                "price_faq_observations": _evidence_fields(source.get("price_faq_evidence"), char_limit=500),
                "header_assets": _evidence_fields(source.get("header_assets"), char_limit=420),
                "footer_assets": _evidence_fields(source.get("footer_assets"), char_limit=420),
                "visible_block_samples": _evidence_fields(source.get("source_block_samples"), char_limit=400),
                "evidence_scope": "EXCERPTS ONLY; full real pages in retained source inventory and source manifest",
            }
            packet.append(obj)
        if len(json.dumps(packet, ensure_ascii=False)) <= max_chars:
            return packet
    raise RuntimeError("RESEARCH_CONTEXT_PACKET_TOO_LARGE: source manifest needs safe staged analysis")


def compact_reference_for_prompt(reference_evidence: list[dict]) -> list[dict]:
    """Keep original screenshot paths and evidence untouched; limit text sent to LLM."""
    if not isinstance(reference_evidence, list):
        raise TypeError("reference evidence expected")
    return [{
        "url": item.get("url"),
        "title": _short(item.get("title"), 240),
        "industry_match": item.get("industry_match"),
        "source_text_excerpt": _selected_site_text(item.get("site_text"), 1400),
        "screenshot_views": [
            view for view in ("desktop", "mobile")
            if isinstance(item.get("screenshots"), dict)
            and item["screenshots"].get(view)
        ],
    } for item in reference_evidence if isinstance(item, dict)]

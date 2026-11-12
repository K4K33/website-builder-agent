"""Source-exact quote IDs for free-model reference selection.

AI can rank a real operator's business fit, but cannot invent source quotes.
The independent reviewer sees exact original excerpts, not paraphrases.
"""
from __future__ import annotations

import re

MAX_QUOTE_OPTIONS = 10
MAX_QUOTE_CHARS = 240


def observed_quote_options(site_text: str, *, limit: int = MAX_QUOTE_OPTIONS) -> list[dict]:
    """Yield SHORT, exact, stable substrings from the live website text.

    Public website content is untrusted; this produces data, not instructions.
    Quotes remain verbatim substrings (no whitespace normalization or rewrites).
    """
    if not isinstance(site_text, str) or not site_text.strip():
        return []
    if not 1 <= limit <= 12:
        raise ValueError("quote limit outside safe range")
    text = site_text[:6000]
    # Requiring long-form evidence discourages navigation labels and generic
    # "contact" links. Use sentence/line spans with exact original indexes.
    spans = []
    for match in re.finditer(r"[^\r\n.!?]{18,700}(?:[.!?]|(?=[\r\n]|$))", text):
        raw = match.group(0)
        if not raw.strip():
            continue
        leading = len(raw) - len(raw.lstrip())
        start = match.start() + leading
        sample = text[start : min(start + MAX_QUOTE_CHARS, match.end())]
        if len(sample.strip()) < 24 or len(sample.split()) < 4:
            continue
        spans.append(sample)
    # Deterministic spread through the source, rather than repeatedly using
    # footer/navigation strings near the start of every company website.
    chosen, seen = [], set()
    if spans:
        indexes = list(range(min(4,len(spans))))
        if len(spans)>4:
            for step in range(4,limit):
                idx=round((step-3)* (len(spans)-1) / max(1,limit-3))
                indexes.append(min(len(spans)-1,idx))
        for idx in indexes:
            sample=spans[idx]
            if sample in seen:continue
            seen.add(sample)
            chosen.append({"quote_id":"q"+str(len(chosen)), "text":sample})
            if len(chosen)>=limit:break
    if not chosen:
        start=len(text)-len(text.lstrip())
        sample=text[start:start+MAX_QUOTE_CHARS].strip()
        if len(sample)>=24:
            chosen=[{"quote_id":"q0","text":sample}]
    return chosen


def verified_evidence_quote(candidate: dict, match: dict) -> str:
    """Resolve only source-exact quote ID or exact old-style source quote.

    Do not accept merely semantically similar AI quotes or a quote ID from
    a different candidate/operator; no fuzzy evidence may pass QA.
    """
    if not isinstance(candidate,dict) or not isinstance(match,dict):
        return ""
    source = candidate.get("site_text")
    if not isinstance(source,str) or not source:
        return ""
    quote_id = match.get("quote_id")
    if isinstance(quote_id,str):
        for item in candidate.get("quote_options") or []:
            if (isinstance(item,dict) and item.get("quote_id")==quote_id and
                    isinstance(item.get("text"),str) and
                    item["text"].strip() and item["text"] in source):
                return item["text"]
    literal = match.get("evidence_quote")
    if isinstance(literal,str) and literal.strip() and literal in source:
        return literal
    return ""

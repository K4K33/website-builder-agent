"""Source paragraph/list inventory with provenance and explicit rewrite review.

A paraphrase is NEVER deemed semantically equivalent by substring matching.
Original text can be reorganized, but every substantive block must be
accounted for before calling a client build content-complete.
"""
from __future__ import annotations
import hashlib
from bs4 import BeautifulSoup

MAX_BLOCKS = 220


def normalize(value: object) -> str:
    return " ".join(str(value or "").casefold().split())


def extract_source_content_blocks(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    main = soup.find("main") or soup.body or soup
    # Exclude navigation and shared furniture; preserve real site body text.
    main = BeautifulSoup(str(main), "html.parser")
    for element in main.select("nav,header,footer,script,style,noscript,template"):
        element.decompose()
    blocks, seen = [], set()
    candidates = main.select("p,li,dd,blockquote")
    for element in candidates:
        if element.name == "li" and element.find(["li", "ul", "ol"]):
            continue
        text = " ".join(element.get_text(" ", strip=True).split())
        minimum = 28 if element.name in ("li", "dd") else 55
        if len(text) < minimum or normalize(text) in seen:
            continue
        seen.add(normalize(text))
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]
        blocks.append({"id": digest, "kind": element.name, "text": text[:1600]})
        if len(blocks) >= MAX_BLOCKS:
            break
    return {"blocks": blocks, "truncated": len(candidates) > MAX_BLOCKS,
            "note": "Visible HTML text only, subject to JavaScript/content completeness review."}


def audit_source_content_blocks(
    rendered_pages: dict[str, str], research: dict
) -> dict:
    pages = (research.get("source_inventory") or {}).get("pages") or []
    source_blocks = [(str(page.get("url") or ""), item)
                     for page in pages if isinstance(page, dict)
                     for item in (page.get("source_content_blocks") or {}).get("blocks") or []
                     if isinstance(item, dict) and item.get("id") and item.get("text")]
    # This is a full-site exact text check, not a semantic similarity guess.
    generated = normalize(" ".join(
        BeautifulSoup(html, "html.parser").get_text(" ", strip=True)
        for html in rendered_pages.values()
    ))
    exact = []
    open_items = []
    for url, block in source_blocks:
        if normalize(block["text"]) in generated:
            exact.append({"source_url": url, "id": block["id"]})
        else:
            open_items.append({"source_url": url, "id": block["id"],
                               "excerpt": block["text"][:180]})
    truncated = [str(page.get("url") or "") for page in pages
                 if isinstance(page, dict) and (
                     page.get("source_content_blocks") or {}).get("truncated")]
    # Source/build specific manual approval must cover EACH changed paragraph,
    # not simply a blanket 'source content checked' boolean.
    review = research.get("rewritten_content_review") or {}
    from utils.content_parity import source_inventory_sha256
    from utils.premium_quality_gate import site_digest
    source_sha = source_inventory_sha256(research.get("source_inventory") or {})
    build_sha = site_digest(rendered_pages)
    approved_ids = set(review.get("verified_block_ids") or [])
    human_valid = (
        review.get("reviewer_kind") == "human"
        and str(review.get("reviewer") or "").strip()
        and str(review.get("checked_at") or "").strip()
        and review.get("source_sha256") == source_sha
        and review.get("build_sha256") == build_sha
    )
    pending = [item for item in open_items
               if not (human_valid and item["id"] in approved_ids)]
    return {
        "pass": not pending and not truncated,
        "observed": len(source_blocks), "preserved_verbatim": len(exact),
        "rewrites_verified": len(open_items) - len(pending),
        "pending": pending, "truncated_pages": truncated,
        "note": "Verbatim matches are evidence of visible copy only. Rewrites need exact-build human review.",
    }

"""Evidence-linked content parity gate for the Kaurivo build pipeline.

Determines whether important *verified* data survived the redesign, without
mistaking a matched keyword for proof that the complete former site survived.
Works offline; no AI/API calls. Human source-coverage signoff is a separate
requirement for declaring a real old-to-new redesign complete.
"""
from __future__ import annotations

from hashlib import sha256
import json
import re
import unicodedata
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

from utils.quality import normalize_facts


def _text(value: object) -> str:
    value = unicodedata.normalize("NFKC", str(value or ""))
    return " ".join(value.casefold().split())


def _flatten_visible(soup: BeautifulSoup) -> str:
    copy = BeautifulSoup(str(soup), "html.parser")
    for element in copy.select("script,style,noscript,template"):
        element.decompose()
    return _text(copy.get_text(" ", strip=True))


def _phone(value: object) -> str:
    digits = re.sub(r"\D", "", str(value or ""))
    if digits.startswith("00358"):
        digits = "0" + digits[5:]
    elif digits.startswith("358"):
        digits = "0" + digits[3:]
    return digits


def _service_names(services: object) -> list[str]:
    if not isinstance(services, list):
        return []
    items: list[str] = []
    for item in services:
        if isinstance(item, str):
            name = item.strip()
        elif isinstance(item, dict):
            name = str(item.get("name") or item.get("title") or "").strip()
        else:
            continue
        if name and name not in items:
            items.append(name)
    return items


def source_inventory_sha256(inventory: dict) -> str:
    """Stable digest of the researched pages; stale review is not acceptable."""
    pages = inventory.get("pages") or []
    records = [{
        "url": str(p.get("url") or ""),
        "text": str(p.get("text") or ""),
        "headings": p.get("headings") or {},
        "header_assets": p.get("header_assets") or [],
        "footer_assets": p.get("footer_assets") or [],
        "footer_links": p.get("footer_links") or [],
        "images": p.get("images") or [],
        "links": p.get("links") or [],
        "source_identity": p.get("source_identity") or {},
    } for p in pages if isinstance(p, dict)]
    raw = json.dumps(records, sort_keys=True, ensure_ascii=False, default=str)
    return sha256(raw.encode("utf-8")).hexdigest()


def _service_present(name: str, visible: str) -> bool:
    """Accept a literal service name or its constituent informative words.

    This deliberately cannot prove a paraphrase has the same meaning:
    unclear cases require review rather than a fabricated semantic verdict.
    """
    exact = _text(name)
    if exact in visible:
        return True
    tokens = [
        t for t in re.findall(r"[\wåäöÅÄÖ]{4,}", exact)
        if t not in {"sekä", "palvelut", "palvelu", "muut"}
    ]
    return len(tokens) >= 2 and all(t in visible for t in tokens)


def _explicit_review_approved(research: dict, pages: list[dict]) -> bool:
    approval = research.get("content_inventory_review")
    if not isinstance(approval, dict):
        return False
    if (approval.get("approved") is not True
            or approval.get("reviewer_kind") != "human"
            or not str(approval.get("reviewer") or "").strip()
            or not str(approval.get("checked_at") or "").strip()):
        return False
    inventory = research.get("source_inventory") or {}
    if approval.get("snapshot_sha256") != source_inventory_sha256(inventory):
        return False
    pages_reviewed = set(approval.get("source_urls") or [])
    return all(p.get("url") in pages_reviewed for p in pages)


def audit_content_parity(
    html: str, research: dict, *, require_source_review: bool = True,
    source_url: str = ""
) -> dict:
    """Check essential data and separately report source-coverage uncertainty.

    Optional research.content_requirements list:
      {label, value, kind: text|href|image, source_url}
    Entries without a matching researched source URL cannot silently become
    trusted requirements. No invented services, prices, menus or allergies.
    """
    facts = normalize_facts(research.get("company_facts") or {})
    soup = BeautifulSoup(html, "html.parser")
    visible = _flatten_visible(soup)
    hrefs = [str(a.get("href") or "").strip() for a in soup.find_all("a", href=True)]
    images = [str(img.get("src") or "").strip() for img in soup.find_all("img", src=True)]
    findings: list[dict] = []
    pending: list[str] = []
    checks = 0

    def check(label: str, kind: str, value: str, found: bool, source: str) -> None:
        nonlocal checks
        checks += 1
        if not found:
            findings.append({"field": kind, "label": label,
                             "expected": value[:160], "source": source})

    for name in _service_names(facts.get("services")):
        check(name, "service", name, _service_present(name, visible), "verified company_facts.services")
    email = str(facts.get("contact_email") or "").strip()
    if email:
        email_uri = "mailto:" + email.casefold()
        check("Sähköposti", "contact_email", email,
              any(h.casefold().split("?", 1)[0] == email_uri for h in hrefs),
              "verified company_facts.contact_email")
    phone = str(facts.get("contact_phone") or "").strip()
    if phone:
        normalized = _phone(phone)
        check("Puhelinnumero", "contact_phone", phone,
              any(h.casefold().startswith("tel:") and _phone(h[4:]) == normalized
                  for h in hrefs), "verified company_facts.contact_phone")
    address = str(facts.get("contact_address") or "").strip()
    if address:
        check("Osoite", "contact_address", address, _text(address) in visible,
              "verified company_facts.contact_address")

    inventory = research.get("source_inventory") or {}
    pages = [p for p in inventory.get("pages", []) if isinstance(p, dict)]
    old_site = bool(pages)
    if source_url and not old_site and research.get("research_mode") != "verified_no_website":
        pending.append(
            "Existing website has no researched source pages; cannot certify source parity."
        )
    original_urls = {str(p.get("url") or "") for p in pages}
    for entry in research.get("content_requirements") or []:
        if not isinstance(entry, dict):
            pending.append("Invalid content requirement; needs source-backed correction.")
            continue
        label = str(entry.get("label") or "").strip()
        value = str(entry.get("value") or "").strip()
        kind = str(entry.get("kind") or "text").strip()
        source = str(entry.get("source_url") or "").strip()
        if not label or not value or (old_site and source not in original_urls):
            pending.append(f"Unverified content requirement: {label or 'unnamed'}")
            continue
        if kind == "text":
            found = _text(value) in visible
        elif kind == "href":
            found = value in hrefs
        elif kind == "image":
            # Asset equivalence (new optimized copy vs original) needs a
            # reviewed asset map; exact string match is a safe initial check.
            found = value in images
        else:
            pending.append(f"Unsupported content requirement type: {kind}")
            continue
        check(label, kind, value, found, source or "verified factual profile")

    if old_site and require_source_review and not _explicit_review_approved(research, pages):
        pending.append(
            "Complete old-to-new page inventory requires human source-coverage "
            "review tied to this exact source snapshot (including original "
            "logos, partners, prices, dynamic menus, media rights and links)."
        )
    if inventory.get("failed_urls") or inventory.get("priority_unvisited_urls"):
        pending.append("Original site inventory has failed or unread important pages.")

    return {
        "pass": not findings and not pending,
        "automated_fields_checked": checks,
        "missing": findings,
        "review_required": pending,
        "source_pages": len(pages),
        "source_inventory_sha256": source_inventory_sha256(inventory) if old_site else "",
        "evidence_note": (
            "Automated checks verify explicit preserved facts only. "
            "No semantic or complete source-site parity claim is implied."
        ),
    }

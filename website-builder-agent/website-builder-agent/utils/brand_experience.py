"""Source-bound client brand-character and first-screen acceptance checks.

Static DOM and a logo URL cannot prove visual fidelity. This audit prevents
silently approving a new brand personality and requires source/build-bound
human comparison for the ORIGINAL wordmark, palette, image priority and voice.
The declared plan is not assumed accurate; undeclared changes stay review
required rather than incorrectly certified.
"""
from __future__ import annotations

from posixpath import dirname, join, normpath
from urllib.parse import urlsplit
from bs4 import BeautifulSoup

from utils.content_parity import source_inventory_sha256
from utils.premium_quality_gate import site_digest


REVIEW_WIDTHS = (320, 390, 1440)
REVIEW_ITEMS = (
    "full_wordmark",
    "palette_character",
    "first_mobile_view",
    "company_voice",
    "original_photo_priority",
    "cross_client_distinctness",
)


def _observations(research: dict) -> dict:
    source = (research.get("source_inventory") or {}).get("pages") or []
    logos, wordmarks, photos = [], [], []
    for page in source:
        if not isinstance(page, dict):
            continue
        identity = page.get("source_identity") or {}
        if not isinstance(identity, dict):
            continue
        logos.extend(str(s) for s in identity.get("original_logo_candidates") or []
                     if isinstance(s, str))
        wordmarks.extend(str(s) for s in identity.get("original_header_wordmark_candidates") or []
                         if isinstance(s, str))
        photos.extend(str(item["src"]) for item in identity.get("original_content_photos") or []
                      if isinstance(item, dict) and isinstance(item.get("src"), str))
    return {
        "source_pages": len(source),
        "observed_logos": len(set(logos)),
        "observed_wordmarks": list(dict.fromkeys(wordmarks))[:12],
        "observed_source_photos": len(set(photos)),
    }


def _linked_local_presentation_assets(pages: dict[str, str]) -> dict:
    """Identify local styles/scripts whose bytes must be in the site bundle.

    Relative references outside assets/ remain unsigned and require review.
    """
    bundled, unsigned = set(), set()
    for route, html in pages.items():
        soup = BeautifulSoup(html, "html.parser")
        links = list(soup.select('link[rel~="stylesheet"][href]'))
        links += list(soup.select('script[src]'))
        for node in links:
            uri = str(node.get("href") or node.get("src") or "").strip()
            if not uri or uri.startswith(("//", "data:", "#")):
                continue
            parsed = urlsplit(uri)
            if parsed.scheme or parsed.netloc:
                continue
            relative = (parsed.path.lstrip("/") if parsed.path.startswith("/") else
                        normpath(join(dirname(route), parsed.path)))
            if relative.startswith("assets/") and ".." not in relative.split("/"):
                bundled.add(relative)
            else:
                unsigned.add(relative)
    return {"bundled": sorted(bundled), "unsigned": sorted(unsigned)}


def _valid_human_comparison(record: object, *, digest: str,
                            source_hash: str, routes: list[str],
                            site_bundle_sha256: str | None,
                            needs_site_bundle: bool) -> list[str]:
    """Validate recorded evidence, not certify human independence or image pixels."""
    issues = []
    if not isinstance(record, dict):
        return ["No source-to-new first-screen visual comparison record."]
    if record.get("verified") is not True or record.get("reviewer_kind") != "independent_human":
        issues.append("Independent human screenshot comparison not recorded.")
    if not str(record.get("reviewer_id") or "").strip():
        issues.append("Human reviewer ID missing.")
    if not str(record.get("evidence_reference") or "").strip():
        issues.append("Evidence reference missing.")
    if record.get("build_sha256") != digest:
        issues.append("Comparison is not bound to this exact site build.")
    if source_hash and record.get("source_sha256") != source_hash:
        issues.append("Comparison is not bound to the original source snapshot.")
    if needs_site_bundle:
        if not site_bundle_sha256:
            issues.append("No full site bundle hash (including CSS and JS) supplied.")
        elif record.get("site_bundle_sha256") != site_bundle_sha256:
            issues.append("Visual comparison uses stale or unverified CSS/JS asset bundle.")
    screenshots = record.get("screenshots") or {}
    for width in REVIEW_WIDTHS:
        for side in ("original", "redesign"):
            key = f"{side}_{width}"
            value = screenshots.get(key) if isinstance(screenshots, dict) else ""
            # File paths or secure HTTP URLs are references, not proof of media.
            if (not isinstance(value, str) or len(value.strip()) < 5
                    or value.startswith(("data:", "javascript:"))):
                issues.append(f"Missing actual {key} screenshot reference.")
    checked = set(str(v) for v in record.get("routes_reviewed") or [])
    if not set(routes).issubset(checked):
        issues.append("The original-to-redesign review did not cover every route.")
    findings = record.get("findings") or {}
    for key in REVIEW_ITEMS:
        value = findings.get(key) if isinstance(findings, dict) else None
        if not isinstance(value, dict):
            issues.append(f"Missing comparison finding: {key}.")
            continue
        if value.get("ok") is not True:
            issues.append(f"Unresolved original brand comparison: {key}.")
        if len(str(value.get("explanation") or "").strip()) < 24:
            issues.append(f"Insufficient observed evidence for {key}.")
    return issues


def _approved_change(research: dict, pages: dict[str, str], source_hash: str,
                     *, site_bundle_sha256: str | None,
                     needs_site_bundle: bool) -> bool:
    approval = research.get("brand_character_change_approval") or {}
    return bool(
        isinstance(approval, dict)
        and approval.get("approved") is True
        and approval.get("reviewer_kind") == "client"
        and str(approval.get("reviewer") or "").strip()
        and str(approval.get("approval_reference") or "").strip()
        and approval.get("build_sha256") == site_digest(pages)
        and (not needs_site_bundle or (
            bool(site_bundle_sha256)
            and approval.get("site_bundle_sha256") == site_bundle_sha256))
        and (not source_hash or approval.get("source_sha256") == source_hash)
    )


def audit_brand_experience(rendered_pages: dict[str, str],
                           research: dict | None = None,
                           *, site_bundle_sha256: str | None = None) -> dict:
    research = research or {}
    pages = rendered_pages or {}
    inventory = research.get("source_inventory") or {}
    source_pages = inventory.get("pages") or []
    source_hash = source_inventory_sha256(inventory) if source_pages else ""
    digest = site_digest(pages)
    signals = _observations(research)
    dependencies = _linked_local_presentation_assets(pages)
    needs_bundle = bool(dependencies["bundled"] or dependencies["unsigned"])
    blocked, pending = [], []
    changed = research.get("brand_character_plan") or {}
    if not isinstance(changed, dict):
        changed = {}
    # A recorded intentional rebrand requires owner consent tied to both
    # revisions. A generic 'client likes it' note is not sufficient.
    requested = [
        label for key, label in (
            ("replace_wordmark", "original wordmark"),
            ("replace_brand_character", "brand palette/character"),
            ("replace_source_photography", "source photographic signature"),
        ) if changed.get(key) is True
    ]
    approved = _approved_change(research, pages, source_hash,
                                site_bundle_sha256=site_bundle_sha256,
                                needs_site_bundle=needs_bundle)
    if source_pages and requested and not approved:
        blocked.append({
            "category": "unapproved_visual_rebrand",
            "changes": requested,
            "issue": "Explicit change to original brand identity requires exact-build "
                     "and source-bound client permission.",
        })
    if source_pages and dependencies["unsigned"]:
        pending.append("Local CSS/JS references outside signed assets/ bundle: "
                       + ", ".join(dependencies["unsigned"][:5]))
    # An approved logo file alone never closes this new visual test.
    if source_pages and (signals["observed_logos"]
                         or signals["observed_wordmarks"]
                         or signals["observed_source_photos"]):
        review_issues = _valid_human_comparison(
            research.get("brand_experience_review"),
            digest=digest, source_hash=source_hash, routes=list(pages),
            site_bundle_sha256=site_bundle_sha256,
            needs_site_bundle=needs_bundle,
        )
        if review_issues:
            pending.extend(review_issues)
    elif source_pages:
        pending.append(
            "Source has no dependable observed wordmark/photo signature; "
            "human original-versus-new identity inspection still needed."
        )
    # Even a reviewed snapshot is not the customer's copyright licence.
    return {
        "pass": not blocked and not pending,
        "blocking": blocked, "pending": pending,
        "source_signals": signals,
        "approved_identity_change": approved,
        "source_sha256": source_hash,
        "build_sha256": digest,
        "site_bundle_sha256": site_bundle_sha256,
        "local_presentation_assets": dependencies,
        "note": (
            "Automated checks validate evidence fields, not screenshots or "
            "subjective brand faithfulness. Reviewer independence, client "
            "rights and 9.5 visual scores need separate human verification."
        ),
    }

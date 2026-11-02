"""Universal Kaurivo standards and evidence-aware offline QA.

Checks static facts where safe. A pending human or browser check is NEVER
reported as an automatically verified pass. There is no subjective AI scoring.
"""
from __future__ import annotations

import re
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

from utils.kaurivo_site_quality_gate import lint_site_copy
from utils.source_identity import audit_source_reviews, audit_price_faq_preservation


# Categories that apply across all sectors, not design layouts.
UNIVERSAL_STANDARDS = (
    ("source_coverage", "All important old pages and facts have source evidence", "research"),
    ("same_industry_inspiration", "Three sourced leading sector sites; original adaptation", "research"),
    ("unique_art_direction", "Distinctive brand-specific visual composition", "visual"),
    ("original_brand", "Original client logo and approved brand preserved", "brand"),
    ("sponsor_and_partner_marks", "Original relevant footer partner marks and links", "brand"),
    ("content_parity", "Current services, pricing, FAQ, contacts, hours and dynamic content", "content"),
    ("natural_copy", "Natural and non-repetitive language without source narration", "content"),
    ("no_decorative_numbering", "No gratuitous 01/02/03 cards", "content"),
    ("non_repetitive_cta_icons", "No repeated decorative arrows on links and calls to action", "visual"),
    ("real_testimonials", "No invented customer reviews, results or staff", "trust"),
    ("accurate_media", "Licensed, true company photos and paired before/after evidence", "media"),
    ("dietary_accuracy", "Full sourced menu and verified G/L/M or allergen details", "safety"),
    ("navigation_and_links", "Working navigation, real link destinations and no fake CTAs", "functional"),
    ("contact_and_forms", "Truthful lead delivery and error/success states", "functional"),
    ("contrast_and_accessibility", "AA contrast, keyboard, alt text and reduced motion", "visual"),
    ("responsive_performance", "Phone/tablet/desktop, no overflow, fast and native scroll", "visual"),
    ("editable_cms", "Customer edits real content with credentials and rollback", "release"),
    ("approved_domain_and_rights", "Branded HTTPS, rights, outreach legality and permission", "release"),
    ("verified_independent_review", "Independent exact-build multi-device quality review", "release"),
)


def _content(html: str) -> tuple[BeautifulSoup, str]:
    soup = BeautifulSoup(html, "html.parser")
    main = soup.find("main") or soup
    copy = BeautifulSoup(str(main), "html.parser")
    for element in copy.select("script,style,noscript,template"):
        element.decompose()
    return soup, " ".join(copy.get_text(" ", strip=True).split())


def audit_universal_standards(
    html: str,
    research: dict | None = None,
    *,
    company: dict | None = None,
    stage: str = "internal_demo",
    rendered_pages: dict[str,str] | None = None,
) -> dict:
    """Separate deterministic failures from evidence still requiring review.

    stage=internal_demo permits unfinished CMS/domain/rights, but it does
    not claim customer readiness. stage=client_release blocks on all proofs.
    """
    if stage not in ("internal_demo", "client_release"):
        raise ValueError("Unknown review stage")
    research = research or {}
    company = company or {}
    pages = rendered_pages if isinstance(rendered_pages, dict) and rendered_pages else {"index.html": html}
    # Run cross-site copy/brand audits on ALL routes, not just index.html.
    texts = []
    for page_html in pages.values():
        _, content = _content(page_html)
        texts.append(content)
    main_text = " ".join(texts)
    soup = BeautifulSoup("<html><body>" + "\n".join(pages.values()) + "</body></html>", "html.parser")
    lower = main_text.casefold()
    problems: dict[str, list[str]] = {}
    pending: dict[str, list[str]] = {}

    def fail(key: str, reason: str) -> None:
        problems.setdefault(key, []).append(reason)

    def needs(key: str, reason: str) -> None:
        pending.setdefault(key, []).append(reason)

    # User-validated cross-company rule: decorative ↗/→ in every CTA is
    # template-like visual noise. Count across ALL rendered pages, including
    # repeated headers/footers. Rare directional controls are allowed; recurring
    # arrow-labelled links fail before the demo can be approved.
    arrow_chars = "↗→➜⇒⟶⇢↪"
    arrow_links = []
    for route, page_html in pages.items():
        page_soup = BeautifulSoup(page_html, "html.parser")
        for link in page_soup.find_all("a"):
            label = " ".join(link.get_text(" ", strip=True).split())
            if any(char in label for char in arrow_chars):
                arrow_links.append((route, label))
    if len(arrow_links) > 2 or any(
        sum(label == other_label for _, other_label in arrow_links) > 1
        for _, label in arrow_links
    ):
        examples = ", ".join(f"{route}: {label[:72]}" for route, label in arrow_links[:4])
        fail("non_repetitive_cta_icons",
             f"Repeated decorative CTA arrows across site ({len(arrow_links)} links): {examples}. "
             "Use readable links and distinct button hierarchy without generic arrow suffixes.")

    source_detail_fidelity = audit_price_faq_preservation(pages, research)
    for item in source_detail_fidelity["missing"]:
        fail("content_parity", str(item))
    source_review_fidelity = audit_source_reviews(pages, research)
    for item in source_review_fidelity["missing"]:
        fail("real_testimonials", str(item))
    for item in source_review_fidelity["pending"]:
        needs("real_testimonials", item)

    copy_result = lint_site_copy(pages)
    for error in copy_result["issues"]:
        key = "no_decorative_numbering" if "decorative card numbering" in error else "natural_copy"
        fail(key, error)

    # Text that belongs in an internal research report, not a business site.
    if re.search(
        r"\byrityksen (?:nykyis|verkkosivui|sivui)[a-zäö]* "
        r"(?:kerrotaan|sanotaan|mainitaan|lukee)\b", lower
    ):
        fail("natural_copy", "Research-report language appears in customer-facing content.")

    # Explicit fabricated testimonials or example staff claims cannot look real.
    if re.search(r"\b(?:keksitty|fiktiivinen|esimerkki)(?:asiakas|arvostelu|palaute)\b", lower):
        fail("real_testimonials", "A fictional testimonial is present in website content.")

    # A before/after visual must reference real paired assets, not two
    # different projects or an artificially generated comparison.
    if soup.select(".before-after,.before-after-slider,[data-before-after]"):
        approved_pairs = research.get("verified_before_after_pairs") or []
        if not approved_pairs:
            fail("accurate_media", "Before/after widget has no verified same-project image pair.")

    # Social proof from the old site and asset permissions are source/evidence
    # checks; raw footer pictures are NOT proof of active sponsorship.
    inventory = research.get("source_inventory") or {}
    pages = inventory.get("pages") or []
    if company.get("url") and not pages:
        fail("source_coverage", "Company has a website but no multi-page research inventory.")
    if pages and (inventory.get("failed_urls") or inventory.get("priority_unvisited_urls")):
        fail("source_coverage", "Important original pages remain unresearched or failed.")
    if pages and not (research.get("content_inventory_review") or {}).get("approved"):
        needs("content_parity", "Human must verify complete old-to-new content inventory.")
    footer_media = [
        asset for page in pages if isinstance(page, dict)
        for asset in page.get("footer_assets") or []
        if isinstance(asset, dict) and asset.get("src")
    ]
    if footer_media and not (research.get("footer_affiliations_review") or {}).get("approved"):
        needs("sponsor_and_partner_marks",
              "Verify original footer logos, role, URL, ongoing relationship and reuse rights.")
    header_media = [
        asset for page in pages if isinstance(page, dict)
        for asset in page.get("header_assets") or []
        if isinstance(asset, dict) and asset.get("src")
    ]
    if header_media and not (research.get("brand_approval") or {}).get("approved"):
        needs("original_brand", "Verify actual client logo, brand fonts/colors and logo rights.")
    original_logo = str((research.get("brand_assets") or {}).get("approved_original_logo_url") or "")
    if original_logo:
        rendered = str(soup)
        # Optimized local copies need an explicit human-verified mapping.
        mapped = (research.get("brand_assets") or {}).get("approved_logo_aliases") or []
        if not any(asset and asset in rendered for asset in [original_logo, *mapped]):
            fail("original_brand", "Approved original logo is absent from generated HTML.")

    # The site may be a static owner demo, but menus and allergens must
    # come from the actual dated source, not model inference.
    industry = str((research.get("company_facts") or {}).get("industry") or "").casefold()
    if any(key in industry for key in ("ravintola", "restaurant", "lounas", "kahvila", "cafe")):
        if "lounas" in lower or "menu" in lower or "ruokalista" in lower:
            if not (research.get("menu_accuracy_review") or {}).get("approved"):
                needs("dietary_accuracy",
                      "Verify complete dated menu and original dietary/allergen markings with source.")
    if soup.find("form") and not (research.get("form_delivery_review") or {}).get("verified"):
        needs("contact_and_forms",
              "Real destination and error/success states have not been tested.")

    if not (research.get("independent_visual_review") or {}).get("verified"):
        needs("verified_independent_review",
              "Independent score, exact-build desktop/mobile images and reviewer not verified.")
    if not (research.get("browser_quality_review") or {}).get("verified"):
        needs("contrast_and_accessibility",
              "Actual browser contrast, focus, keyboard and reduced-motion not verified.")
        needs("responsive_performance",
              "Actual phone/tablet/desktop overflow, load speed and scroll not verified.")
        needs("navigation_and_links",
              "Functional navigation and exact CTA links need browser checks.")
    if not (research.get("three_industry_benchmarks_review") or {}).get("verified"):
        needs("same_industry_inspiration",
              "Three sourced same-industry website benchmarks require verification.")
    if not (research.get("visual_originality_review") or {}).get("verified"):
        needs("unique_art_direction",
              "Human side-by-side layout and brand review not verified.")

    # Release evidence always remains visible even for internal demos.
    release_manifest = company.get("release_evidence") or {}
    release = {
        "editable_cms": ("cms_edit_verified", "Client login, save, publish and restore"),
        "contact_and_forms": ("real_lead_delivery_verified", "End-to-end lead delivery"),
        "approved_domain_and_rights": ("branded_https_verified", "Approved brand HTTPS domain"),
    }
    for key, (field, description) in release.items():
        if release_manifest.get(field) is not True:
            needs(key, f"Customer release: {description} unverified.")
    for field, desc in (
        ("media_rights_verified", "Client logo and photo reuse permissions"),
        ("legal_and_outreach_reviewed", "Marketing, privacy, footer and lawful outreach"),
        ("client_approved", "Explicit client production approval"),
    ):
        if release_manifest.get(field) is not True:
            needs("approved_domain_and_rights", f"Customer release: {desc} unverified.")

    all_rules = {name: group for name, _, group in UNIVERSAL_STANDARDS}
    grouped = {
        key: {"group": group,
              "status": "fail" if key in problems else "pending" if key in pending else "no_static_defect",
              "problems": problems.get(key, []),
              "pending": pending.get(key, [])}
        for key, group in all_rules.items()
    }
    return {
        "automated_pass": not problems,
        "internal_review_ready": not problems,
        "client_release_ready": not problems and not pending,
        "stage": stage,
        "standards": grouped,
        "blocking_problems": problems,
        "pending_evidence": pending,
        "note": (
            "Checked = no automatic defect found, NOT an independent quality certification. "
            "Any pending evidence remains open. Internal demos are not customer releases."
        ),
    }

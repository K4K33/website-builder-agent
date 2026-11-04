"""Universal Kaurivo standards and evidence-aware offline QA.

Checks static facts where safe. A pending human or browser check is NEVER
reported as an automatically verified pass. There is no subjective AI scoring.
"""
from __future__ import annotations

import re
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

from utils.kaurivo_site_quality_gate import lint_site_copy
from utils.client_facing_integrity import audit_client_facing_integrity
from utils.brand_design_blueprint import audit_sitewide_brand_consistency
from utils.brand_lock import audit_brand_lock
from utils.brand_experience import audit_brand_experience
from utils.source_experience import audit_source_experience_parity
from utils.source_experience_gate import audit_experience_continuity
from utils.source_signature_lock import audit_source_signature_lock
from utils.cross_route_editorial_risks import audit_cross_route_editorial_risks
from utils.route_experience_contract import audit_route_experience
from utils.sector_presence import audit_sector_presence
from utils.source_identity import audit_source_reviews, audit_price_faq_preservation
from utils.trust_claims import audit_trust_claims
from utils.premium_quality_gate import (
    source_coverage_matrix, verify_independent_premium_reviews,
    verify_field_performance, audit_primary_journeys,
)


# Categories that apply across all sectors, not design layouts.
UNIVERSAL_STANDARDS = (
    ("source_coverage", "All important old pages and facts have source evidence", "research"),
    ("same_industry_inspiration", "Three sourced leading sector sites; original adaptation", "research"),
    ("unique_art_direction", "Distinctive brand-specific visual composition", "visual"),
    ("original_brand", "Original client logo and approved brand preserved", "brand"),
    ("source_experience_parity", "Original video, galleries, texture, motion and media depth", "visual"),
    ("source_browser_experience_continuity", "Live browser inventory of original video, 3-D, animation, photography and texture", "visual"),
    ("sponsor_and_partner_marks", "Original relevant footer partner marks and links", "brand"),
    ("content_parity", "Current services, pricing, FAQ, contacts, hours and dynamic content", "content"),
    ("natural_copy", "Natural and non-repetitive language without source narration", "content"),
    ("no_decorative_numbering", "No gratuitous 01/02/03 cards", "content"),
    ("non_repetitive_cta_icons", "No repeated decorative arrows on links and calls to action", "visual"),
    ("real_testimonials", "No invented customer reviews, results or staff", "trust"),
    ("source_bound_social_proof", "New testimonial and rating claims require exact-build proof", "trust"),
    ("accurate_media", "Licensed, true company photos and paired before/after evidence", "media"),
    ("dietary_accuracy", "Full sourced menu and verified G/L/M or allergen details", "safety"),
    ("navigation_and_links", "Working navigation, real link destinations and no fake CTAs", "functional"),
    ("contact_and_forms", "Truthful lead delivery and error/success states", "functional"),
    ("contrast_and_accessibility", "AA contrast, keyboard, alt text and reduced motion", "visual"),
    ("responsive_performance", "Phone/tablet/desktop, no overflow, fast and native scroll", "visual"),
    ("editable_cms", "Customer edits real content with credentials and rollback", "release"),
    ("approved_domain_and_rights", "Branded HTTPS, rights, outreach legality and permission", "release"),
    ("verified_independent_review", "Independent exact-build multi-device quality review", "release"),
    ("source_to_destination_matrix", "Each source page, section, price and review verified", "content"),
    ("independent_premium_consensus", "Two independent exact-build reviewers, all dimensions >=9.5", "release"),
    ("real_user_core_web_vitals", "Verified field p75 LCP, INP and CLS", "release"),
    ("primary_user_journeys", "Every planned main booking, shopping and contact path works", "functional"),
    ("customer_facing_copy", "Published copy contains no research notes or source narration", "content"),
    ("verified_brand_marks", "No invented logo monograms without client-linked proof", "brand"),
    ("brand_identity_lock", "Source-verified header marks and unchanged approved favicons on every route", "brand"),
    ("real_location_aids", "No decorative street maps masquerading as navigation aids", "functional"),
    ("editorial_visual_balance", "Human comparison of typography, whitespace and composition", "visual"),
    ("coherent_sitewide_brand_kit", "Consistent website-level brand tokens and theme across all routes", "brand"),
    ("sector_recognition", "First-view company industry recognisability", "visual"),
    ("company_voice_and_rhythm", "Company-specific voice and page layout", "visual"),
    ("original_brand_experience", "Full original wordmark, palette mood and voice are source-verified", "brand"),
    ("cross_route_visual_rhythm", "Photo diversity, substantive first views and non-repetitive CTA sections", "visual"),
    ("first_view_visual_priority", "Evidence-based first mobile viewport shows actual client work where appropriate", "visual"),


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
    site_bundle_sha256: str | None = None,
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

    integrity = audit_client_facing_integrity(pages, research, stage=stage)
    integrity_keys = {
        "research_leak": "customer_facing_copy",
        "visible_internal_note": "customer_facing_copy",
        "demo_note_in_release": "customer_facing_copy",
        "unsourced_brand_mark": "verified_brand_marks",
        "misleading_map": "real_location_aids",
    }
    for item in integrity["blocking"]:
        fail(integrity_keys.get(item["category"], "customer_facing_copy"), str(item))
    for item in integrity["pending"]:
        if item["category"] == "template_headlines":
            needs("natural_copy", str(item))
        # Visual/editorial proof is checked independently below by the
        # exact-build two-reviewer consensus. Never create a permanently
        # unresolvable pending flag once real evidence has passed.

    identity_lock = audit_brand_lock(pages, research)
    for issue in identity_lock["blocking"]:
        fail("brand_identity_lock", str(issue))
    for issue in identity_lock["pending"]:
        needs("brand_identity_lock", str(issue))

    # An image logo matching the source is not proof that the surrounding
    # typography, visual softness, first fold and brand story survived.
    brand_experience = audit_brand_experience(
        pages, research, site_bundle_sha256=site_bundle_sha256
    )
    for item in brand_experience["blocking"]:
        fail("original_brand_experience", str(item))
    for item in brand_experience["pending"]:
        needs("original_brand_experience", str(item))
    if (brand_experience["source_signals"]["observed_source_photos"]
            and brand_experience["pending"]):
        needs("first_view_visual_priority",
              "Compare the actual original/new 320px and 390px first screens; "
              "confirm industry-relevant photos appear at the right time. "
              "Some sectors legitimately need a text-first layout.")

    # A source photograph is not interchangeable with a generic image count.
    # Enforce original logo artwork, staff portraits, full work galleries and
    # videos BEFORE considering the site technically accepted.
    signature = audit_source_signature_lock(pages, research)
    for item in signature["blocking"]:
        fail("original_visual_assets", str(item))
    for item in signature["pending"]:
        needs("original_visual_assets", str(item))

    # A technically present gallery can still be repeated verbatim on four
    # unrelated routes. Surface that to an independent reviewer instead of
    # certifying a source-rich business as visually diversified.
    # Escalate known, source-grounded cross-page failures from soft warnings.
    route_experience = audit_route_experience(pages,research)
    for issue in route_experience["blocking"]:
        fail("route_specific_visual_composition",str(issue))
    editorial_risks = audit_cross_route_editorial_risks(pages, research)
    for risk in editorial_risks["pending"]:
        needs("cross_route_visual_rhythm", str(risk))

    source_experience = audit_source_experience_parity(pages, research)
    for issue in source_experience["blocking"]:
        fail("source_experience_parity", issue)
    for issue in source_experience["pending"]:
        needs("source_experience_parity", issue)

    # Complement source-HTML parity with actual original browser observations.
    # Inconclusive captures remain pending, never treated as no motion.
    browser_experience = audit_experience_continuity(
        rendered_pages if isinstance(rendered_pages, dict) and rendered_pages
        else {"index.html": html}, research,
    )
    for issue in browser_experience["blocking"]:
        fail("source_browser_experience_continuity", issue)
    for issue in browser_experience["pending"]:
        needs("source_browser_experience_continuity", issue)

    sector_presence = audit_sector_presence(pages, research)
    for item in sector_presence['blocking']:
        fail('sector_recognition', str(item))
    for message in sector_presence['pending']:
        needs('company_voice_and_rhythm' if 'strips' in message else 'sector_recognition', message)

    brand_consistency = audit_sitewide_brand_consistency(pages)
    for reason in brand_consistency["issues"]:
        fail("coherent_sitewide_brand_kit", reason)

    source_detail_fidelity = audit_price_faq_preservation(pages, research)
    for item in source_detail_fidelity["missing"]:
        fail("content_parity", str(item))
    source_review_fidelity = audit_source_reviews(pages, research)
    for item in source_review_fidelity["missing"]:
        fail("real_testimonials", str(item))
    for item in source_review_fidelity["pending"]:
        needs("real_testimonials", item)

    # Preservation alone is insufficient: a generated site can retain every
    # genuine quote AND append fabricated five-star endorsements.
    # Fail closed for clearly recognizable review cards and aggregate badges.
    social_proof = audit_trust_claims(
        rendered_pages if isinstance(rendered_pages, dict) and rendered_pages
        else {"index.html": html}, research
    )
    for item in social_proof["blocking"]:
        fail("source_bound_social_proof", str(item))
    for item in social_proof["pending"]:
        needs("source_bound_social_proof", str(item))

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
    # A redesigned company must account for real original staff/work photos.
    # Matching and reproduction rights require a source-bound human media map.
    source_photos = [
        photo for page in pages if isinstance(page, dict)
        for photo in (page.get("source_identity") or {}).get("original_content_photos") or []
        if isinstance(photo, dict) and photo.get("src")
    ]
    if source_photos and not (research.get("original_photo_continuity_review") or {}).get("approved"):
        needs("accurate_media",
              f"{len(source_photos)} original source content photos need a licensed "
              "retain/replace mapping and human review before client release.")

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

    # New proof-backed premium review matrix. Internal demo production is
    # allowed with visibly pending subjective/live evidence, never certified.
    coverage = source_coverage_matrix(rendered_pages if isinstance(rendered_pages, dict)
                                     and rendered_pages else {"index.html": html}, research)
    from utils.premium_quality_gate import site_digest
    premium_build_hash = site_digest(rendered_pages if isinstance(rendered_pages, dict)
                                     and rendered_pages else {"index.html": html})
    if coverage["status"] == "no_original_site":
        fact_review = research.get("no_site_fact_review") or {}
        valid_no_site = (
            bool(research.get("fact_sources"))
            and fact_review.get("approved") is True
            and fact_review.get("reviewer_kind") == "human"
            and str(fact_review.get("reviewer") or "").strip()
            and fact_review.get("build_sha256") == premium_build_hash
        )
        if not valid_no_site:
            needs("source_to_destination_matrix",
                  "No-site company: verified third-party factual inventory and "
                  "exact-build human signoff still required.")
    elif coverage["status"] != "verified":
        needs("source_to_destination_matrix",
              f"Original source/build coverage {coverage['status']}: "
              f"{len(coverage['missing'])} missing, {len(coverage['pending'])} pending.")
    independently_reviewed = verify_independent_premium_reviews(
        research.get("premium_independent_reviews"),
        rendered_pages if isinstance(rendered_pages, dict) and rendered_pages
        else {"index.html": html}, research
    )
    if not independently_reviewed["pass"]:
        needs("independent_premium_consensus",
              "; ".join(independently_reviewed["issues"][:5]))
    field_metrics = verify_field_performance(
        research.get("field_performance_evidence"),
        rendered_pages if isinstance(rendered_pages, dict) and rendered_pages
        else {"index.html": html}
    )
    if not field_metrics["pass"]:
        needs("real_user_core_web_vitals", "; ".join(field_metrics["issues"][:5]))
    journeys = audit_primary_journeys(
        rendered_pages if isinstance(rendered_pages, dict) and rendered_pages
        else {"index.html": html}, research.get("primary_user_journeys")
    )
    if research.get("primary_user_journeys"):
        for issue in journeys["issues"]:
            fail("primary_user_journeys", issue)
    else:
        needs("primary_user_journeys",
              "Company-specific booking/contact/purchase paths must be inventoried and tested.")

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
    # A checked box from last week's version cannot certify today's HTML:
    # bind the client's final signoff to BOTH exact build and source snapshot.
    release_manifest = company.get("release_evidence") or {}
    source_snapshot = (research.get("source_inventory") or {})
    from utils.content_parity import source_inventory_sha256
    expected_source_hash = (
        source_inventory_sha256(source_snapshot) if source_snapshot.get("pages") else ""
    )
    release_signature_valid = (
        isinstance(release_manifest, dict)
        and release_manifest.get("approved") is True
        and release_manifest.get("reviewer_kind") == "client"
        and str(release_manifest.get("reviewer") or "").strip()
        and str(release_manifest.get("approved_at") or "").strip()
        and str(release_manifest.get("client_approval_reference") or "").strip()
        and release_manifest.get("build_sha256") == premium_build_hash
        and (not expected_source_hash
             or release_manifest.get("source_sha256") == expected_source_hash)
    )
    if not release_signature_valid:
        needs(
            "approved_domain_and_rights",
            "Final client signoff lacks an approval reference or is not bound "
            "to this exact site build and original source snapshot."
        )
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
    # Report one usable cross-project decision rather than exposing a
    # misleading 'green' automation flag when human/source proof is still open.
    decision = ("blocked" if problems else
                "review_required" if pending else "client_ready")
    return {
        "quality_decision": decision,
        "blocking_categories": sorted(problems),
        "pending_categories": sorted(pending),
        "automated_pass": not problems,
        "internal_review_ready": not problems,
        "client_release_ready": not problems and not pending,
        "stage": stage,
        "standards": grouped,
        "blocking_problems": problems,
        "brand_consistency": brand_consistency,
        "brand_identity_lock": identity_lock,
        "brand_experience": brand_experience,
        "sector_presence": sector_presence,
        "source_browser_experience": browser_experience,
        "premium_evidence": {
            "coverage": coverage,
            "independent_review": independently_reviewed,
            "field_performance": field_metrics,
            "primary_user_journeys": journeys,
            "social_proof": social_proof,
        },
        "pending_evidence": pending,
        "note": (
            "Checked = no automatic defect found, NOT an independent quality certification. "
            "Any pending evidence remains open. Internal demos are not customer releases."
        ),
    }

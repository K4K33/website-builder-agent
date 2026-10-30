"""Client-first redesign and handover rules. Pure, offline, no API costs.

This is a *planning and locked-copy validation* layer, not a CMS.
A static HTML delivery alone cannot be described as customer-editable.
"""
import re
from datetime import date
from urllib.parse import urlsplit
from bs4 import BeautifulSoup


def _strings(values, limit=12, max_length=240):
    if not isinstance(values, list):
        return []
    result = []
    for value in values[:limit]:
        if isinstance(value, str) and value.strip() and len(value) <= max_length:
            result.append(value.strip())
    return result


def client_design_brief(company):
    """Return a small bounded brief to include in generation/revision prompts.

    Explicit user/owner confirmation is needed before changing brand, rather
    than interpreting a competitor reference's palette as client consent.
    All source images still require a right to use and local delivery plan.
    """
    prefs = company.get("client_preferences") or {}
    if not isinstance(prefs, dict):
        prefs = {}
    has_site = bool(company.get("url") or company.get("website"))
    approved = prefs.get("verified_with_client") is True
    mode = "keep_existing_identity" if has_site else "new_brand_design_requires_review"
    if approved and prefs.get("permission_to_rebrand") is True:
        mode = "client_explicitly_permits_brand_change"
    colors = _strings(prefs.get("existing_colors"), limit=8, max_length=24)
    color_hex = [c for c in colors if re.fullmatch(r"#[0-9a-fA-F]{6}", c)]
    locked_copy = _strings(prefs.get("locked_copy"), limit=12, max_length=240) if approved else []
    photo_policy = "retain_authorized_originals_or_request_rights"
    if approved and prefs.get("permission_to_replace_photos") is True:
        photo_policy = "client_permits_selected_replacement_photos"
    # Kaurivo delivery standard: EVERY client-owned finished site is
    # self-editable. A static demo is still allowed for pre-sales review.
    # No preference, default or agency-managed selection can silently
    # downgrade the final handover requirement.
    # This policy is not proof that the CMS has been implemented.
    return {
        "site_type": "redesign" if has_site else "new_site",
        "design_scope": (
            "major_visual_and_structural_redesign_keep_brand"
            if has_site else "original_full_site_design"
        ),
        "redesign_intensity": "substantial_visible_change",
        "layout_policy": (
            "rethink_navigation_hero_layout_content_hierarchy_typography_mobile"
            if has_site else "design_the_full_experience_from_scratch"
        ),
        "brand_policy": mode,
        "existing_colors_verified_by_client": color_hex if approved else [],
        "photo_policy": photo_policy,
        "keep_client_logo_by_default": has_site,
        "keep_original_claims_and_taglines_by_default": has_site,
        "locked_copy": locked_copy,
        "content_editing_goal": "client_self_service_required",
        "content_editing_fields": [
            "headings", "body_text", "services", "photos",
            "contact_details", "opening_hours", "prices_when_applicable"
        ],
        "final_delivery_requires_live_cms": True,
        "cms_status": "not_implemented_in_static_html",
        "cms_delivery": (
            "Before selling a client-editable site, choose a CMS and hosting/auth "
            "with the owner, integrate it, test edit/publish/media permissions and "
            "give the client their own login. Static HTML is not itself a CMS."
        ),
    }


def validate_locked_copy(html, brief):
    """Fail closed for client-approved exact slogans/copy, if any.

    Does not claim to verify logo, brand colors or actual media rights.
    Those require human preview and source asset checks.
    """
    locks = brief.get("locked_copy") or []
    if not locks:
        return
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    visible = " ".join(soup.stripped_strings)
    normalized = " ".join(visible.split()).casefold()
    for phrase in locks:
        if " ".join(phrase.split()).casefold() not in normalized:
            raise RuntimeError(
                "Client-approved protected copy is missing from the new page: "
                + phrase[:80]
            )

def _https_url(value):
    if not isinstance(value, str) or not value.strip() or len(value) > 2000:
        return False
    parts = urlsplit(value.strip())
    return (parts.scheme == "https" and bool(parts.hostname)
            and not parts.username and not parts.password)


def inspect_client_delivery(company, *, today=None):
    """Fail-closed, offline audit for CLIENT HANDOVER (not demo approval).

    Self-reported checkboxes and URLs cannot independently prove live CMS
    functionality. The operator must actually test and document the real
    client's login/edit/publish/image flow before setting these flags.
    This function never deploys, sends mail or calls APIs.
    """
    today = today or date.today()
    delivery = company.get("delivery") or {}
    build = company.get("build") or {}
    qa = company.get("qa") or {}
    approval = company.get("approval") or {}
    problems = []
    if not isinstance(delivery, dict):
        delivery = {}
    platform = delivery.get("cms_platform")
    allowed = {"wordpress", "webflow", "framer", "pages_cms",
               "decap_cms", "custom_cms"}
    if platform not in allowed:
        problems.append("An actual CMS platform must be selected and integrated.")
    if not _https_url(delivery.get("admin_url")):
        problems.append("A real HTTPS customer editor URL is missing.")
    if not _https_url(delivery.get("published_url")):
        problems.append("The published client website HTTPS URL is missing.")
    try:
        checked = date.fromisoformat(delivery["verified_at"])
        if not 0 <= (today - checked).days <= 60:
            raise ValueError("stale")
    except (KeyError, ValueError, TypeError):
        problems.append("A recent real-client handover verification date is missing.")
    for field, detail in (
        ("verified_by_human", "Human-reviewed CMS delivery evidence is required."),
        ("client_editor_login_tested", "Client's own editor login has not been tested."),
        ("text_edit_published_tested", "Client text change has not been saved and published."),
        ("image_edit_published_tested", "Client image change has not been saved and published."),
        ("contact_edit_published_tested", "Client contact information edit has not been tested."),
        ("mobile_layout_after_edit_tested", "Mobile view after edits is not tested."),
        ("backup_and_rollback_tested", "Backup and rollback have not been tested."),
        ("client_owns_editor_access", "Customer needs control of their own editing access."),
        ("owner_guide_delivered", "Client editing instructions have not been delivered."),
        ("customer_acceptance", "Customer has not confirmed the handover."),
    ):
        if delivery.get(field) is not True:
            problems.append(detail)
    if build.get("version") != delivery.get("build_version") or not isinstance(build.get("version"), int):
        problems.append("CMS handover does not match the current build version.")
    if qa.get("overall_pass") is not True or qa.get("build_version") != build.get("version"):
        problems.append("The current website build has not passed QA.")
    if (approval.get("approved") is not True
            or approval.get("build_version") != build.get("version")):
        problems.append("Owner's current build approval is missing.")
    # The digest ties handover evidence to the exact approved build.
    digest = qa.get("html_sha256")
    if (not isinstance(digest, str) or not digest
            or delivery.get("html_sha256") != digest
            or approval.get("html_sha256") != digest):
        problems.append("CMS handover is not bound to the current approved HTML.")
    return {
        "client_editable": True,
        "stage": "client_delivery",
        "ready_to_handover": not problems,
        "cms_platform": platform,
        "issues": problems,
        "limitations": (
            "This offline audit checks recorded review evidence, not live "
            "CMS behavior. A human must actually test the client login, "
            "editing, publishing, and rollback on the deployed website."
        ),
    }


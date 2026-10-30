"""Client-first redesign and handover rules. Pure, offline, no API costs.

This is a *planning and locked-copy validation* layer, not a CMS.
A static HTML delivery alone cannot be described as customer-editable.
"""
import re
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
    content_editing = prefs.get("content_editing") if approved else None
    # Content editing is offered as a real separate handover step; it is
    # *never* silently claimed to be installed by the single-HTML builder.
    return {
        "site_type": "redesign" if has_site else "new_site",
        "brand_policy": mode,
        "existing_colors_verified_by_client": color_hex if approved else [],
        "photo_policy": photo_policy,
        "keep_client_logo_by_default": has_site,
        "keep_original_claims_and_taglines_by_default": has_site,
        "locked_copy": locked_copy,
        "content_editing_goal": content_editing if content_editing in (
            "client_self_service", "agency_managed", "not_decided"
        ) else "client_self_service_offered",
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

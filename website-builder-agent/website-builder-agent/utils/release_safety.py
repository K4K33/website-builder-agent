"""Hard release boundary: passing tests never equals a client-ready website.

This module does not certify taste or authenticate self-entered records. It
requires independent, source- and build-bound evidence plus a verified actual
public URL before any Kaurivo workflow may declare a website client-ready.
Private, explicitly labeled drafts can exist in HOLD. No network/AI calls.
"""
from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlsplit
import hashlib
import re

import config
from utils.creative_directions import validate_creative_directions
from utils.concept_previews import validate_selected_concept
from utils.service_quality import MASTER_PROMPT_SHA256
from utils.site_integrity import site_sha256
from utils.site_architecture import route_path
from utils.premium_quality_gate import verify_independent_premium_reviews


MIN_VIEWPORTS = ("390", "1440")


def _sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def _current_artifact(company, problems):
    """Return source-identical pages only when full bundle and QA match."""
    build = company.get("build") or {}
    qa = company.get("qa") or {}
    approved = company.get("approval") or {}
    source = build.get("output_path")
    root = Path(config.OUTPUT_DIR).resolve()
    if not isinstance(source, str) or not source.strip():
        problems.append("No current build output. A demo link is not a delivered website.")
        return {}, None, None
    file = Path(source).resolve()
    try:
        if not file.is_file() or not file.is_relative_to(root):
            raise RuntimeError("Build output missing or outside authorized output root.")
        if file.name != "index.html" or file.parent.parent != root:
            raise RuntimeError("Build must have a dedicated customer output directory.")
        if Path(source).is_symlink():
            raise RuntimeError("A symlinked build cannot be approved.")
        routes = build.get("page_paths") or ["index.html"]
        if not isinstance(routes, list) or len(routes) != len(set(routes)):
            raise RuntimeError("Missing or duplicate routes.")
        pages = {route_path(p): (file.parent / route_path(p)).read_text(encoding="utf-8")
                 for p in routes}
        digest = site_sha256(file.parent, routes)
        if (qa.get("overall_pass") is not True
                or qa.get("build_version") != build.get("version")
                or approved.get("approved") is not True
                or approved.get("build_version") != build.get("version")
                or qa.get("html_sha256") != _sha(file)
                or approved.get("html_sha256") != _sha(file)):
            problems.append("Current build is missing matching QA and explicit owner approval.")
        if qa.get("site_sha256") != digest or approved.get("site_sha256") != digest:
            problems.append("Full route/media/site digest differs from the reviewed version.")
        return pages, digest, file.parent
    except (ValueError, OSError, RuntimeError, TypeError) as error:
        problems.append("Exact build unavailable: " + str(error))
        return {}, None, None


def check_actual_public_website(evidence, *, site_digest, routes, build_commit):
    """Fail on stale CDN HTML, broken resources, missing routes or mobile errors.

    Evidence is a machine-generated browser report with user-reviewed CI provenance.
    Merely setting a boolean 'passed' or reporting Render live is never enough.
    """
    problems = []
    evidence = evidence if isinstance(evidence, dict) else {}
    site = evidence.get("url")
    parsed = urlsplit(site) if isinstance(site, str) else None
    if (not parsed or parsed.scheme != "https" or not parsed.hostname
            or parsed.hostname.endswith((".invalid", ".example", ".test"))):
        problems.append("Real HTTPS public preview URL is absent.")
    if not site_digest or evidence.get("site_sha256") != site_digest:
        problems.append("Live proof does not match the exact reviewed multi-page bundle.")
    if not build_commit or evidence.get("commit_sha") != build_commit:
        problems.append("Live deployment commit is missing or differs from the build.")
    marker = evidence.get("release_marker")
    if not isinstance(marker, str) or len(marker.strip()) < 10:
        problems.append("Unique release marker is missing.")
    ci_run_url = evidence.get("ci_run_url")
    if (not isinstance(ci_run_url, str)
            or re.fullmatch(
                r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/actions/runs/[1-9][0-9]*(?:/attempts/[1-9][0-9]*)?",
                ci_run_url,
            ) is None
            or evidence.get("ci_verified_by_owner") is not True):
        problems.append("Human-verified, externally run browser evidence is missing.")
    timestamp = evidence.get("checked_at")
    try:
        checked = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        if (checked.tzinfo is None
                or checked > datetime.now(timezone.utc)
                or (datetime.now(timezone.utc) - checked).total_seconds() > 24*3600):
            raise ValueError("stale or future")
    except (AttributeError, TypeError, ValueError):
        problems.append("Live browser proof must be timezone-aware, after deployment, and <=24h old.")
    reports = evidence.get("pages")
    if not isinstance(reports, list):
        reports = []
    observed = {}
    for item in reports:
        if not isinstance(item, dict):
            problems.append("Malformed page evidence."); continue
        route = item.get("route")
        viewport = str(item.get("viewport"))
        key = (route, viewport)
        if key in observed:
            problems.append("Duplicate public route/viewport proof: " + repr(key))
        observed[key] = item
        if route not in routes or viewport not in MIN_VIEWPORTS:
            problems.append("Unknown public route or device evidence: " + repr(key))
        if (item.get("status") != 200
                or item.get("release_marker") != marker
                or item.get("computed_styles_valid") is not True
                or item.get("scripts_valid") is not True
                or item.get("navigation_valid") is not True
                or item.get("responsive_valid") is not True
                or item.get("visible_brand_valid") is not True
                or item.get("broken_images") != 0
                or item.get("page_errors") != []):
            problems.append("BROKEN or STALE PUBLIC PAGE: " + repr(key))
        if not isinstance(item.get("screenshot_sha256"), str) or re.fullmatch(r"[0-9a-f]{64}", item["screenshot_sha256"]) is None:
            problems.append("Public screenshot proof missing: " + repr(key))
    required = {(route, width) for route in routes for width in MIN_VIEWPORTS}
    for missing in sorted(required - set(observed)):
        problems.append("Public route or device was never inspected: " + repr(missing))
    if evidence.get("errors") != [] or evidence.get("warnings") != []:
        problems.append("Public browser test has errors or unresolved warnings.")
    return {"passed": not problems, "issues": problems, "checked_routes": len(required)}


def inspect_release_safety(company, *, customer_delivery=False):
    """Universal final gate: no proof = HOLD, regardless of technical test count."""
    company = company if isinstance(company, dict) else {}
    problems = []
    research = company.get("research") or {}
    build = company.get("build") or {}
    if (research.get("master_prompt_sha256") != MASTER_PROMPT_SHA256
            or research.get("quality_contract_version") != 6):
        problems.append("Active V6 master prompt was not bound to this exact research/build.")
    if (research.get("visual_concepts_protocol") != "v1"
            or research.get("premium_visual_protocol") != "v2"
            or research.get("premium_protocol") != "v2"):
        problems.append("Full modern Research/three-concept/visual-review protocol was bypassed.")
    try:
        validate_creative_directions(research)
        source = build.get("output_path") or ""
        root = Path(source).resolve().parent
        if not source or not root.is_relative_to(Path(config.OUTPUT_DIR).resolve()):
            raise RuntimeError("Verified three-concept preview root is missing.")
        if not (company.get("concept_previews") or {}).get("selection_sha256"):
            raise RuntimeError("No actual rendered/compared/selected three-concept proof.")
        if validate_selected_concept(company, allowed_root=root) is None:
            raise RuntimeError("The selected three rendered concepts were not verified.")
    except (RuntimeError, ValueError, OSError, TypeError, KeyError) as error:
        problems.append("Concept protocol HOLD: " + str(error))
    pages, digest, _ = _current_artifact(company, problems)
    if pages:
        try:
            independent = verify_independent_premium_reviews(
                research.get("premium_independent_reviews"), pages, research)
            if not independent.get("pass"):
                problems.append("Independent exact-build 9.5/10 review is missing or failed: "
                                + "; ".join(independent.get("issues", [])[:3]))
        except (TypeError, ValueError, OSError) as error:
            problems.append("Independent review cannot be validated: " + str(error))
    else:
        problems.append("Cannot verify the independent visual review without real current pages.")
    media = company.get("media_rights_review") or {}
    if (media.get("approved_by_owner") is not True
            or media.get("site_sha256") != digest
            or not str(media.get("evidence_reference") or "").strip()
            or not str(media.get("checked_at") or "").strip()
            or media.get("open_rights_issues") != []):
        problems.append("Current-build media rights and truthful image attribution are not approved.")
    live = check_actual_public_website(
        company.get("public_release_evidence"),
        site_digest=digest,
        routes=set(pages),
        build_commit=build.get("commit_sha"))
    problems.extend(live["issues"])

    # Distinct source business tasks (shop checkout, contact forms, booking,
    # quotes) must be tested against the same public release by an authorized
    # reviewer. An HTTP 200 or a styled screenshot cannot prove conversion.
    from utils.service_quality import source_tasks
    real_tasks = source_tasks(research)
    if real_tasks:
        business = company.get("business_task_live_review") or {}
        required_ids = {task["id"] for task in real_tasks}
        rows = business.get("tasks") or []
        actual_ids = {row.get("task_id") for row in rows if isinstance(row, dict)}
        if (business.get("site_sha256") != digest
                or business.get("release_marker") != (company.get("public_release_evidence") or {}).get("release_marker")
                or business.get("human_verified") is not True
                or actual_ids != required_ids
                or len(rows) != len(required_ids)
                or any(row.get("real_flow_passed") is not True
                       or not str(row.get("test_evidence") or "").strip()
                       for row in rows if isinstance(row, dict))):
            problems.append("Actual live booking/shop/quote/contact journeys not independently tested for this release.")

    if customer_delivery:
        from utils.client_handover import inspect_client_delivery
        cms = inspect_client_delivery(company)
        if cms.get("ready_to_handover") is not True:
            problems.extend(cms.get("issues") or ["Customer-editable CMS handover not verified."])
        signoff = company.get("client_signoff") or {}
        if (signoff.get("approved_current_release") is not True
                or signoff.get("site_sha256") != digest
                or signoff.get("release_marker") != (company.get("public_release_evidence") or {}).get("release_marker")
                or not str(signoff.get("approval_evidence") or "").strip()):
            problems.append("Customer has not approved this exact live site revision.")
    return {"status": "CLIENT_READY" if not problems and customer_delivery
            else "PRESENTATION_READY" if not problems else "HOLD",
            "approved": not problems, "issues": list(dict.fromkeys(problems)),
            "live": live,
            "note": ("Offline assertions inspect recorded evidence; screenshots, independent"
                     " reviewer identities and source rights still require genuine verification."
                     " Do not label the site ready before public smoke and owner review.")}

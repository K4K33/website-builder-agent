"""Premium demo sales gate: an incomplete or generic demo must NOT be pitched.

Offline validation of recorded evidence only; not a replacement for visual
inspection, client fact verification or marketing compliance.
"""
from datetime import date
from pathlib import Path
from urllib.parse import urlsplit


CHECKS = (
    ("brand_preservation_reviewed", "Retained brand or approved new identity not reviewed."),
    ("three_industry_peers_compared", "Three actual same-industry benchmarks are not confirmed."),
    ("bespoke_structure_verified", "Site is not visibly specific and restructured for this firm."),
    ("real_services_and_copy_checked", "Site copy/services are not checked against business sources."),
    ("image_rights_and_logos_checked", "Real image/logo rights and authentic logos are unverified."),
    ("desktop_visual_approved", "Desktop art direction lacks human approval."),
    ("mobile_visual_approved", "Mobile layout lacks human approval."),
    ("motion_and_reduced_motion_checked", "Interactions and reduced-motion alternatives unchecked."),
    ("real_links_and_cta_checked", "Contact links and CTAs are unverified."),
    ("benefit_in_email_matches_demo", "Sales copy claims an improvement not seen in the demo."),
    ("owner_approves_premium_quality", "Owner has not approved this specific premium demo."),
)


def _https(value):
    if not isinstance(value, str):
        return False
    p = urlsplit(value)
    return (p.scheme == "https" and bool(p.hostname)
            and not p.username and not p.password)


def assess_pitch_packet(company, *, today=None, check_local_files=True):
    """Conservatively gate the actual customer outreach stage.

    The signature/checks are deliberately strict: AI passing a prompt is not
    evidence of premium design. Customer-mail sending remains a separate
    explicit user action via the verified Kaurivo Gmail connector.
    """
    today = today or date.today()
    problems = []
    build = company.get("build") or {}
    qa = company.get("qa") or {}
    approve = company.get("approval") or {}
    research = company.get("research") or {}
    demo = company.get("demo") or {}
    quality = company.get("demo_quality_review") or {}
    version = build.get("version")
    digest = qa.get("html_sha256")
    if not isinstance(version, int) or version < 1:
        problems.append("Valid built demo version missing.")
    if not (qa.get("overall_pass") is True and qa.get("build_version") == version
            and isinstance(digest, str) and digest):
        problems.append("QA has not passed on the exact current demo.")
    if not (approve.get("approved") is True
            and approve.get("build_version") == version
            and approve.get("html_sha256") == digest):
        problems.append("User has not approved this exact demo build.")
    if not (demo.get("published") is True and _https(demo.get("url"))):
        problems.append("Public real HTTPS demo preview is missing.")
    refs = research.get("design_benchmark") or []
    if not isinstance(refs, list) or len({
        item.get("url") for item in refs
        if isinstance(item, dict) and _https(item.get("url"))
    }) < 3:
        problems.append("Three different actual industry benchmark URLs missing.")
    if not (research.get("company_facts") or {}).get("name"):
        problems.append("Verified business research identity missing.")
    shots = (qa.get("browser") or {}).get("screenshots") or {}
    for size in ("desktop", "tablet", "mobile", "small_mobile"):
        p = shots.get(size)
        if (not isinstance(p, str) or not p
                or (check_local_files and (not Path(p).is_file() or Path(p).stat().st_size <= 0))):
            problems.append("Missing actual rendered screenshot: " + size)
    if quality.get("build_version") != version or quality.get("html_sha256") != digest:
        problems.append("Premium human review is missing or for an obsolete version.")
    try:
        reviewed_date = date.fromisoformat(quality["reviewed_at"])
        if not 0 <= (today - reviewed_date).days <= 30:
            raise ValueError("stale")
    except (ValueError, KeyError, TypeError):
        problems.append("Current premium demo human review date missing.")
    for field, explanation in CHECKS:
        if quality.get(field) is not True:
            problems.append(explanation)
    return {
        "premium_demo_ready_for_outreach_review": not problems,
        "stage": "sales_demo_quality",
        "issues": problems,
        "limitations": (
            "Human flags must reflect real inspection. This offline gate does "
            "not produce a demo, validate evidence provenance, grant permission "
            "to email, or send anything."
        ),
    }

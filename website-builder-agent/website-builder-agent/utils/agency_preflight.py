"""Deterministic agency-style design handoff before costly demo AI steps.

Inspired by professional site workflows: source inventory -> sitemap and
route wireframes -> source-grounded art direction -> production -> browser QA.
This is NOT a visual score or a substitution for the existing independent QA.
Only existing verified research data is used. No network or model calls.
"""
from __future__ import annotations

from utils.agency_handoff import agency_handoff
from utils.brand_design_blueprint import derive_brand_site_blueprint
from utils.creative_directions import FIELDS, validate_creative_directions
from utils.design_benchmark import validate_design_plan
from utils.site_architecture import validate_site_architecture
from utils.source_fidelity import validate_source_plan
from utils.source_identity import validate_brand_preservation_plan


def safe_preflight_reason(error: BaseException) -> str:
    """Classify a failed gate without storing scraped text or site URLs.

    Full exception text may contain names or URLs from the original source.
    Only these fixed, non-sensitive categories are sent to the job table.
    """
    message = str(error).lower()
    for needle, code in (
        ("master prompt", "master_prompt_version"),
        ("benchmark", "reference_evidence"),
        ("industry", "reference_evidence"),
        ("creative", "creative_direction"),
        ("concept", "creative_direction"),
        ("brand", "original_brand"),
        ("logo", "original_brand"),
        ("source", "original_source"),
        ("content", "original_source"),
        ("site architecture", "sitemap"),
        ("route", "sitemap"),
        ("page plan", "sitemap"),
        ("motion", "motion_accessibility"),
    ):
        if needle in message:
            return code
    return "design_contract"

def verify_design_handoff(company: dict, *, selected: bool = False) -> dict:
    """Fail closed if a demo's research is not ready to become a real website.

    A proposed design must use the current canonical Master Prompt, three
    source-backed benchmarks, actual original pages, destination sitemap,
    differentiated concept plans and the original brand/experience. When the
    winner is selected it must be evidenced, not silently chosen by the Builder.
    """
    if not isinstance(company, dict):
        raise RuntimeError("Design preflight: company snapshot missing.")
    research = company.get("research")
    if not isinstance(research, dict) or not research:
        raise RuntimeError("Design preflight: researched company is missing.")
    # This fails on outdated master-prompt digests (including restored state).
    handoff = agency_handoff(research)
    if handoff.get("master_prompt_sha256") != research.get("master_prompt_sha256"):
        raise RuntimeError("Design preflight: wrong Master Prompt revision.")
    url = str(company.get("url") or "")
    validate_source_plan(research, source_url=url)
    validate_brand_preservation_plan(research)
    validate_design_plan(research, target_url=url)
    architecture = validate_site_architecture(
        research, no_site=research.get("research_mode") == "verified_no_website"
    )
    directions = research.get("creative_directions")
    if not isinstance(directions, list) or len(directions) != 3:
        raise RuntimeError("Design preflight: three distinct concepts required.")
    for direction in directions:
        if not isinstance(direction, dict) or any(
            not isinstance(direction.get(field), str) or
            not direction[field].strip() for field in FIELDS
        ):
            raise RuntimeError("Design preflight: concept art direction incomplete.")
    if handoff.get("industry_references_evidenced", 0) < 3:
        raise RuntimeError("Design preflight: three industry comparisons required.")
    if not handoff.get("routes") or not architecture.get("page_paths"):
        raise RuntimeError("Design preflight: sourced sitemap/wireframes missing.")
    if selected:
        validate_creative_directions(research)
        blueprint = derive_brand_site_blueprint(research)
        if not blueprint.get("sitemap_and_wireframes"):
            raise RuntimeError("Design preflight: route-specific blueprint missing.")
    return handoff

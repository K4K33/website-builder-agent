"""Validate a complete multi-page Kaurivo output before writing any HTML.

All site-wide content/brand checks receive all pages. Per-page semantics,
media and link resolution are checked for EVERY route. No network/LLM calls.
"""
from __future__ import annotations
from pathlib import Path
import os
import tempfile

from utils.site_architecture import (
    parse_generated_site, validate_site_architecture, validate_site_navigation,
    pages_for_validation,
)
from utils.creative_directions import validate_creative_directions
from utils.visual_direction import visual_direction_plan, audit_visual_motion
from utils.visual_originality import audit_design_originality
from utils.visual_media_gate import audit_visual_media
from utils.design_distinctness import assert_unique_against_output
from utils.content_parity import audit_content_parity
from utils.universal_quality import audit_universal_standards
from utils.route_experience_contract import audit_route_experience
from utils.source_fidelity import audit_source_fidelity
from utils.client_handover import client_design_brief, validate_locked_copy

def build_pages_from_response(raw: str, *, slug: str,
                              company: dict, output_root: str | Path) -> dict:
    from agents.builder import (_validate_generated_content, _validate_plan_sections)
    from agents.qa import _automated_checks

    research=company.get("research") or {}
    creative=validate_creative_directions(research)
    architecture=validate_site_architecture(
        research, no_site=research.get("research_mode")=="verified_no_website"
    )
    direction=visual_direction_plan(research, creative, architecture)
    pages=parse_generated_site(raw, architecture)
    # The creative preflight is now an explicit implementation contract,
    # not just a generic inspiration paragraph.
    if not direction.get("source_anchor") or not direction.get("depth_direction"):
        raise RuntimeError("Missing business-specific art direction.")
    linked_style_or_script = any(
        ('rel="stylesheet"' in html or "rel='stylesheet'" in html or
         '<script src=' in html) for html in pages.values()
    )
    motion=audit_visual_motion(pages, research, assets_complete=not linked_style_or_script)
    if motion["blocking"]:
        raise RuntimeError("Inaccessible motion effects: " + "; ".join(motion["blocking"][:4]))
    navigation=validate_site_navigation(pages, architecture)
    if not navigation["pass"]:
        raise RuntimeError("Incomplete real multi-page navigation: " +
                           "; ".join(navigation["issues"][:8]))
    facts=research.get("company_facts") or {}
    root=Path(output_root)/slug
    for route,html in pages.items():
        _validate_generated_content(html,facts)
        static=_automated_checks(html,page_path=route)
        if not static["automated_pass"]:
            raise RuntimeError(route+": invalid HTML: "+"; ".join(static["automated_issues"][:8]))
        media=audit_visual_media(html,html_path=root/route)
        if not media["static_pass"]:
            raise RuntimeError(route+": missing/broken real media: "+"; ".join(media["blockers"][:8]))
    # Per-route anchors are allowed to reuse the same short id; verify the
    # mapped page's true anchors in validate_site_navigation + source_fidelity.
    _validate_plan_sections(pages["index.html"],research,company.get("url",""),
                            rendered_pages=pages)
    combined=pages_for_validation(pages)
    validate_locked_copy(combined,client_design_brief(company))
    parity=audit_content_parity(
        combined,research,require_source_review=False,source_url=company.get("url","")
    )
    if parity["missing"] or parity["review_required"]:
        raise RuntimeError("Original content facts lost across site pages: "+
                           "; ".join([x["label"] for x in parity["missing"]]+
                                     list(parity["review_required"]))[:2000])
    fidelity=audit_source_fidelity(pages["index.html"],research,
                                   source_url=company.get("url",""),
                                   rendered_pages=pages,require_human_review=False)
    if fidelity["missing"]:
        raise RuntimeError("Original site pages, logos or customer journeys lost: "+
                           "; ".join(str(x.get("kind"))+":"+str(x.get("source","")) for x in fidelity["missing"][:8]))
    universal=audit_universal_standards(
        pages["index.html"],research,company=company,stage="internal_demo",
        rendered_pages=pages
    )
    if not universal["automated_pass"]:
        raise RuntimeError("Universal business content/brand failure: "+
                           "; ".join(x for arr in universal["blocking_problems"].values() for x in arr)[:1500])
    # Hard failure BEFORE writing: a source-rich shop cannot pass by moving
    # products beneath a giant title or recycling the same image/CTA everywhere.
    route_experience=audit_route_experience(pages,research)
    if route_experience["blocking"]:
        raise RuntimeError("Route-specific composition rejected: " + "; ".join(
            str(x.get("kind")) + " @ " + str(x.get("route") or x.get("issue"))
            for x in route_experience["blocking"][:10]))
    uniqueness=audit_design_originality(
        pages["index.html"],site_slug=slug,
        reference_demos=Path(__file__).resolve().parents[1]/"docs"/"kaurivo"/"demos",
    )
    if not uniqueness["pass"]:
        raise RuntimeError("Repeated generic agency layout/copy: "+
                           "; ".join(uniqueness["blocking_problems"]))
    assert_unique_against_output(pages["index.html"],slug,output_root)

    # All checks above complete BEFORE modifying any site HTML file.
    root.mkdir(parents=True,exist_ok=True)
    staging=[]
    try:
        for route,html in pages.items():
            destination=root/route
            destination.parent.mkdir(parents=True,exist_ok=True)
            with tempfile.NamedTemporaryFile(mode="w",encoding="utf-8",
                    dir=destination.parent,prefix=".validated-page-",
                    delete=False) as tmp:
                tmp.write(html)
                staging.append((Path(tmp.name),destination))
        for temporary,destination in staging:
            os.replace(temporary,destination)
    finally:
        for temporary,_ in staging:
            temporary.unlink(missing_ok=True)
    return {"output_path":str(root/"index.html"),"page_paths":sorted(pages),
            "visual_originality":uniqueness,"navigation":navigation,
            "route_experience":route_experience,
            "visual_direction":direction,
            "motion_preflight":motion}

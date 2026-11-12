"""Source-grounded agency-style design handoff for ALL Kaurivo demos.

No AI, network requests or fabricated services. This is a compact per-client
interface contract, not an aesthetic score, licence or a page template.
"""
from __future__ import annotations

import hashlib
import json

from utils.service_quality import MASTER_PROMPT_SHA256, source_tasks


def agency_handoff(research: dict) -> dict:
    """Give Research, Builder, Revision and visual QA the same requirements."""
    if not isinstance(research, dict) or research.get("master_prompt_sha256") != MASTER_PROMPT_SHA256:
        raise RuntimeError("Agency handoff requires the CURRENT V6 Master Prompt source")
    inventory = research.get("source_inventory") or {}
    architecture = research.get("site_architecture") or {}
    pages = architecture.get("pages") or []
    if not isinstance(pages, list) or not pages:
        raise RuntimeError("Agency handoff cannot invent a missing customer sitemap")
    if not isinstance(inventory.get("pages", []), list):
        raise RuntimeError("Agency handoff requires real source inventory")
    tasks = source_tasks(research)
    observed = research.get("original_experience_profile") or {}
    benchmark = research.get("design_benchmark") or []
    directions = research.get("creative_directions") or []
    if not isinstance(benchmark,list) or not isinstance(directions,list):
        raise RuntimeError("Industry and concept evidence must be structured")
    routes = []
    for page in pages:
        if not isinstance(page,dict):
            raise RuntimeError("Invalid route in agency handoff")
        path = page.get("path")
        if not isinstance(path,str) or not path.strip():
            raise RuntimeError("Missing route path in agency handoff")
        routes.append({
            "path":path,
            "purpose":page.get("purpose") or "SOURCE_REVIEW_REQUIRED",
            "visitor_task":page.get("user_task") or "SOURCE_REVIEW_REQUIRED",
        })
    features = {str(task["kind"]) for task in tasks}
    components = ["keyboard-accessible_navigation","responsive_typography"]
    if features.intersection({"shopping"}):
        components.append("real_product_cart_checkout_or_explicit_hold")
    if features.intersection({"booking","booking_form"}):
        components.append("verified_booking_flow")
    if features.intersection({"quotation","quotation_form","contact_form"}):
        components.append("real_form_delivery_or_explicit_demo_only_label")
    motion = str(observed.get("status") or "").strip()
    # The original browser probe, not aesthetic guesswork, chooses a
    # feature floor. Video/3D/gallery signals are NEVER automatic licences.
    return {
        "contract": "agency-design-handoff-v1",
        "master_prompt_sha256": MASTER_PROMPT_SHA256,
        "routes": routes,
        "required_source_tasks": [
            {"kind": task["kind"], "id": task["id"], "source": task["source_url"]}
            for task in tasks
        ],
        "source_experience_observed": bool(observed) and motion not in ("unverified","unknown"),
        "source_experience_status": motion or "REVIEW_REQUIRED",
        "industry_references_evidenced": len(benchmark),
        "distinct_concepts_planned": len(directions),
        "approved_component_patterns": components,
        "design_requirements": [
            "source brand and full logo first; no invented marks or claims",
            "one visitor job and distinctive composition per route, not repeated bars",
            "source photos/video/3D/galleries are a creative floor only where evidenced",
            "use relevant component patterns only; never copy competitor layouts",
            "real drag and touch interaction for before-after comparisons when used",
            "mobile keyboard and reduced-motion alternatives for every interaction",
            "old/new same-size screenshot comparison before release; weak redesign is HOLD",
            "record incomplete rights, CMS delivery and booking/form parity as HOLD",
        ],
        "approval": "NOT_A_QUALITY_SCORE; independent exact-build QA still required",
    }


def handoff_digest(plan: dict) -> str:
    return hashlib.sha256(json.dumps(plan,sort_keys=True,ensure_ascii=False,
                   separators=(",",":")).encode("utf-8")).hexdigest()

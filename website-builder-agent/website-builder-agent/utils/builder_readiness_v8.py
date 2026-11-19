"""V8 production gate: distinguish a verified current offering from a registry label.

Pure/offline: no AI call, no live network and no status writes. It is used
after Research and BEFORE any three-concept Builder credit is consumed.
"""
from __future__ import annotations

from utils.service_quality import validate_primary_offering


def assess_build_readiness(research: dict | None) -> dict:
    """Return explicit build eligibility, never infer current services from TOL."""
    if not isinstance(research, dict) or not research:
        return {"ready": False, "code": "source_research_missing",
                "stage": "source", "next_action": "Complete verified company research."}

    facts = research.get("company_facts")
    if not isinstance(facts, dict) or not str(facts.get("name") or "").strip():
        return {"ready": False, "code": "source_company_identity_missing",
                "stage": "facts", "next_action": "Verify the company's legal identity."}

    conflict = research.get("current_service_conflict")
    if isinstance(conflict, dict) and conflict.get("status") in {
        "unresolved", "contradictory_current_sources"
    }:
        return {"ready": False, "code": "source_current_service_conflict",
                "stage": "facts", "next_action": "Obtain current operator evidence for offered services."}

    if research.get("research_mode") == "verified_no_website":
        services = facts.get("services")
        sources = research.get("fact_sources") or {}
        service_sources = sources.get("services") if isinstance(sources, dict) else None
        # A verified no-site business must be sourced, not a fabricated no-site fallback.
        actual_sources = (
            service_sources if isinstance(service_sources, list) else
            [service_sources] if isinstance(service_sources, str) else []
        )
        if (not isinstance(services, list) or
            not any(isinstance(v, str) and v.strip() for v in services) or
            not any(isinstance(v, str) and v.startswith("https://")
                    for v in actual_sources)):
            return {"ready": False, "code": "source_no_site_service_unverified",
                    "stage": "facts",
                    "next_action": "Supply a current, independent service source for this no-site business."}
        return {"ready": True, "code": "ready_verified_no_website",
                "stage": "researched", "evidence": "reviewed_no_site_profile",
                "source_count": len(actual_sources),
                "owner_preview_only": True}

    inventory = research.get("source_inventory") or {}
    pages = inventory.get("pages")
    if not isinstance(pages, list) or not pages:
        return {"ready": False, "code": "source_original_site_unobserved",
                "stage": "source",
                "next_action": "Inspect the public original website; a PRH listing is not a site."}
    evidence = research.get("primary_offering_evidence")
    if not evidence:
        return {"ready": False, "code": "source_current_service_missing",
                "stage": "facts",
                "next_action": "Find an exact, current offering quote on the original company website."}
    try:
        checked = validate_primary_offering(evidence, pages)
    except (RuntimeError, TypeError, AttributeError):
        return {"ready": False, "code": "source_current_service_unverified",
                "stage": "facts",
                "next_action": "Require the exact same-URL service wording, not an industry code."}
    return {"ready": True, "code": "ready_source_verified",
            "stage": "researched", "evidence": {
                "source_url": checked["source_url"],
                "label": checked["label"]
            }, "owner_preview_only": True}


def require_build_readiness(research: dict) -> dict:
    result = assess_build_readiness(research)
    if not result["ready"]:
        # Consumed by the private worker's explicit HOLD taxonomy.
        raise RuntimeError("BUILD_READINESS_BLOCKED: " + result["code"])
    return result

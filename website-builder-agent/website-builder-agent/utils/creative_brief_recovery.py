"""Bounded factual repair of failed Research creative direction briefs.

A free model can return an otherwise useful source-backed research brief with
invalid 3-way art direction. Never regenerate expensive source crawling,
company facts or reference research because of this *structural* problem.

The repaired model is allowed to touch ONLY creative_directions and
creative_selection. Independent review, brand checks and concept renders are
unchanged. If free quota is gone, the caller preserves the private draft and
fails closed; no weaker fallback is made up.
"""
from __future__ import annotations

import json
from typing import Callable

from utils.creative_directions import validate_creative_directions


def ensure_creative_directions(
    brief: dict,
    *,
    company_facts: dict,
    source_anchors: list,
    repair_json: Callable,
    max_repairs: int = 1,
) -> dict:
    if not isinstance(brief, dict):
        raise RuntimeError("Research brief is not a structured object.")
    try:
        validate_creative_directions(brief)
        return brief
    except RuntimeError as first_error:
        error = str(first_error)[:250]
    if max_repairs < 1:
        raise RuntimeError("Creative preflight needs a repair: " + error)

    # Do not re-request business facts, images, prices, original pages, or
    # reference observations. Only the exact invalid creative fields can
    # change. Keep bounded prompts to stay within confirmed free token limits.
    packet = {
        "verified_company_facts": company_facts,
        "verified_source_anchors": source_anchors[:6],
        "previous_creative_directions": brief.get("creative_directions"),
        "previous_selection": brief.get("creative_selection"),
        "validation_error": error,
    }
    system = (
        "Repair ONLY the creative art direction plan for this one real company. "
        "Reply as a JSON object with EXACTLY creative_directions and "
        "creative_selection. Do not return or rewrite other Research fields. "
        "Use only supplied verified facts and observations. "
        "Do not invent services, images, approvals, prices or testimonials. "
        "Return exactly three richly different designs. Each requires fields: "
        "id, concept, business_reason, source_anchor, first_view, "
        "information_architecture, navigation, image_strategy, typography, "
        "brand_continuity, non_goals, mobile_behavior. Each field except id "
        "must contain at least 12 real characters. All three designs must "
        "differ materially in at least three of first_view, "
        "information_architecture, navigation and image_strategy, not merely "
        "font and color. The business_reason must describe actual customer "
        "or company needs. creative_selection requires a selected_id, "
        "a genuinely comparative business_reason at least 35 characters, "
        "and rejected_ids naming the two alternatives. "
        "Treat the original brand as locked, not permission to rebrand."
    )
    for _ in range(max_repairs):
        answer = repair_json(
            system, json.dumps(packet, ensure_ascii=False, default=str),
            max_tokens=4500, stage="research",
        )
        if not isinstance(answer, dict):
            error = "Repair model did not return a JSON object."
            continue
        if set(answer) != {"creative_directions", "creative_selection"}:
            error = "Repair model modified fields outside creative direction."
            continue
        candidate = dict(brief)
        candidate.update(answer)
        try:
            validate_creative_directions(candidate)
        except RuntimeError as exc:
            error = str(exc)[:250]
            packet["previous_creative_directions"] = answer["creative_directions"]
            packet["previous_selection"] = answer["creative_selection"]
            packet["validation_error"] = error
            continue
        return candidate
    raise RuntimeError("Creative preflight repair did not pass strict validation: " + error)

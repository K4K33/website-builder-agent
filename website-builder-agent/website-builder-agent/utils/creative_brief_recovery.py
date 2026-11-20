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

from utils.creative_directions import CreativeBusinessReasonError, validate_creative_directions
from utils.quality_v7 import CREATIVE_DIRECTION_BRIEF


def _with_consistent_choice(brief: dict) -> dict:
    """Derive the identifiers of the alternatives from the expressed choice."""
    directions = brief.get("creative_directions")
    choice = brief.get("creative_selection")
    if not isinstance(directions, list) or len(directions) != 3 or not isinstance(choice, dict):
        return brief
    identifiers = [item.get("id") if isinstance(item, dict) else None for item in directions]
    if not all(isinstance(identifier, str) and identifier.strip() for identifier in identifiers):
        return brief
    normalized = {identifier.strip().casefold(): identifier for identifier in identifiers}
    selected = choice.get("selected_id")
    if not isinstance(selected, str) or len(normalized) != 3:
        return brief
    selected_id = selected.strip().casefold()
    if selected_id not in normalized:
        return brief
    fixed_choice = {
        **choice,
        "selected_id": normalized[selected_id],
        "rejected_ids": [identifier for key, identifier in normalized.items() if key != selected_id],
    }
    return {**brief, "creative_selection": fixed_choice}


def ensure_creative_directions(
    brief: dict,
    *,
    company_facts: dict,
    source_anchors: list,
    repair_json: Callable,
    max_repairs: int = 2,
    save_draft: Callable[[dict], None] | None = None,
) -> dict:
    if not isinstance(brief, dict):
        raise RuntimeError("Research brief is not a structured object.")
    reason_index = None
    try:
        validate_creative_directions(brief)
        return brief
    except RuntimeError as first_error:
        error = str(first_error)[:250]
        if isinstance(first_error, CreativeBusinessReasonError):
            reason_index = first_error.index
    normalized = _with_consistent_choice(brief)
    if normalized is not brief:
        try:
            validate_creative_directions(normalized)
        except RuntimeError as exc:
            error = str(exc)[:250]
            reason_index = exc.index if isinstance(exc, CreativeBusinessReasonError) else None
        else:
            return normalized
    if max_repairs < 1:
        raise RuntimeError("Creative preflight needs a repair: " + error)

    # Do not re-request business facts, images, prices, original pages, or
    # reference observations. Only the exact invalid creative fields can
    # change. Keep bounded prompts to stay within confirmed free token limits.
    packet = {
        "verified_company_facts": company_facts,
        "verified_source_anchors": source_anchors[:6],
        "previous_creative_directions": brief.get("creative_directions"),
        "previous_selection": normalized.get("creative_selection"),
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
        "must be a string of at least 12 characters. Use one or two concrete "
        "sentences per field and short ids. Write each concept around a "
        "distinct verified customer task or a different way of completing it. "
        "Use visibly different opening compositions, page structures and "
        "navigation patterns. All three designs must "
        "differ materially in at least three of first_view, "
        "information_architecture, navigation and image_strategy, not merely "
        "font and color. The business_reason must describe actual customer "
        "or company needs. Name the audience explicitly, for example customer, "
        "asiakas, or kund, and explain their verified task. "
        "creative_selection requires a selected_id, "
        "a genuinely comparative business_reason at least 35 characters, "
        "and rejected_ids naming the two alternatives. "
        "Treat the original brand as locked, not permission to rebrand."
    )
    system += CREATIVE_DIRECTION_BRIEF
    candidate = normalized
    previous_reason_index = None
    for _ in range(max_repairs):
        # Feed the most recent validation failure back into the next call.
        # A new queue run would otherwise only see the original stale draft.
        packet["validation_error"] = error
        if reason_index is not None:
            direction = candidate["creative_directions"][reason_index]
            task = (
                "Write a fresh reason from the source. Explain what an actual customer needs "
                "to do and how the proposal helps them do it."
                if reason_index == previous_reason_index else
                "Repair only the indicated customer/business reason, preserving the design."
            )
            answer = repair_json(
                task + " Use verified facts and original excerpts only. Explicitly name the "
                "customer. Return a JSON object with the single key business_reason.",
                json.dumps({
                    "company_facts": company_facts,
                    "source_anchors": source_anchors[:6],
                    "direction": direction,
                    "validation_error": error,
                }, ensure_ascii=False, default=str),
                max_tokens=300, stage="research",
            )
            previous_reason_index = reason_index
            reason = answer.get("business_reason") if isinstance(answer, dict) else None
            if not isinstance(reason, str) or not reason.strip():
                continue
            directions = list(candidate["creative_directions"])
            directions[reason_index] = {**direction, "business_reason": reason}
            candidate = {**candidate, "creative_directions": directions}
        else:
            answer = repair_json(
                system, json.dumps(packet, ensure_ascii=False, default=str),
                max_tokens=4500, stage="research",
            )
            if not isinstance(answer, dict):
                error = "Repair model did not return a JSON object."
                continue
            candidate = _with_consistent_choice({
                **candidate,
                **{key: answer[key] for key in ("creative_directions", "creative_selection")
                   if key in answer},
            })
        try:
            validate_creative_directions(candidate)
        except RuntimeError as exc:
            error = str(exc)[:250]
            reason_index = exc.index if isinstance(exc, CreativeBusinessReasonError) else None
            if save_draft is not None:
                save_draft(candidate)
            packet["previous_creative_directions"] = candidate.get("creative_directions")
            packet["previous_selection"] = candidate.get("creative_selection")
            continue
        return candidate
    raise RuntimeError("Creative preflight repair did not pass strict validation: " + error)

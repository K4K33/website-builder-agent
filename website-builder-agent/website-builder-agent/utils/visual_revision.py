"""Bounded QA-driven revision planning; no automatic client approvals or API calls."""
from __future__ import annotations

from hashlib import sha256
import json


def decide_revision(qa: dict, seen_signatures: set[str] | None = None) -> dict:
    """Return an actionable repair plan, or an explicit stop with a reason.

    Used only inside the CLI's opt-in capped --max-revisions loop.
    Missing evidence/rights/reviewer signoff cannot be fixed by a model.
    """
    seen_signatures = seen_signatures or set()
    if qa.get("overall_pass") is True:
        return {"revise": False, "reason": "qa_passed"}
    if qa.get("unimplemented_global_feedback"):
        return {"revise": False, "reason": "global_rule_requires_real_checker"}
    visual = qa.get("visual_comparison") or {}
    if visual.get("status") == "review_required":
        return {"revise": False, "reason": "original_or_new_screenshot_evidence_missing",
                "evidence_path": visual.get("comparison_html")}
    if (qa.get("content_review") or {}).get("notes") == "AI review failed":
        return {"revise": False, "reason": "qa_model_unavailable"}
    browser_issues = list((qa.get("browser") or {}).get("issues") or [])
    if any("Browser QA unavailable" in str(x) for x in browser_issues):
        return {"revise": False, "reason": "browser_qa_unavailable"}

    visual_hints = [item for item in visual.get("repair_hints") or []
                    if isinstance(item, dict) and item.get("suggestion")]
    static = list((qa.get("automated") or {}).get("automated_issues") or [])
    content_missing = [
        str(item.get("label") or item) if isinstance(item, dict) else str(item)
        for item in (qa.get("content_parity") or {}).get("missing") or []
    ]
    source_missing = [
        str(item.get("kind") or "source") + ": " + str(item.get("source") or "")
        if isinstance(item, dict) else str(item)
        for item in (qa.get("source_fidelity") or {}).get("missing") or []
    ]
    ai_review = qa.get("content_review") or {}
    creative = list(ai_review.get("issues") or [])
    # The actual multimodal reviewer can detect wordmark/palette or generic
    # style regressions even when no static first-fold heuristic is triggered.
    visual_blockers = list((ai_review.get("visual_review") or {}).get("blockers") or [])
    benchmark_gaps = list((ai_review.get("reference_comparison") or {}).get("remaining_gaps") or [])
    layout = list((qa.get("layout_composition_review") or {}).get("issues") or [])
    # Avoid treating missing assets/licences as generic fixable page layout.
    browser_fixable = [
        str(issue) for issue in browser_issues
        if not any(word in str(issue).lower() for word in (
            "unverified", "source screenshot", "media rights",
            "licence", "browser qa unavailable",
        ))
    ]
    # Do not repeat huge QA payloads or unsupported guesses in paid prompts.
    actions = [
        *[str(x.get("viewport", "")) + ": " + str(x["suggestion"])
          for x in visual_hints],
        *[str(x) for x in static],
        *browser_fixable,
        *content_missing,
        *source_missing,
        *[str(x) for x in visual_blockers],
        *[str(x) for x in benchmark_gaps],
        *[str(x) for x in creative],
        *[str(x) for x in layout],
    ]
    actions = [item.strip()[:800] for item in actions if str(item).strip()][:30]
    if not actions:
        return {"revise": False, "reason": "only_unverified_human_or_client_evidence"}
    # Repeated identical repair sets after a revision indicate stagnation:
    # another paid retry without new evidence is not defensible.
    signature = sha256(json.dumps(sorted(set(actions)),
                                  ensure_ascii=False).encode("utf-8")).hexdigest()
    if signature in seen_signatures:
        return {"revise": False, "reason": "no_progress_same_actionable_issues",
                "signature": signature}
    return {
        "revise": True, "reason": "specific_fixable_failures",
        "signature": signature,
        "feedback": {
            "priority": "First resolve objectively observed source/new visual mismatches, "
                        "then specific browser/content defects. Preserve verified original "
                        "brand, source content and any approved customer photos. "
                        "Never fabricate rights or claim independent review.",
            "visual_evidence": {
                "status": visual.get("status"),
                "comparison_html": visual.get("comparison_html"),
                "source_sha256": visual.get("source_sha256"),
                "build_sha256": visual.get("build_sha256"),
                "first_fold_repair_hints": visual_hints[:6],
            },
            "actionable_defects": actions,
            "static": static[:12],
            "browser": browser_fixable[:10],
            "source_content_missing": source_missing[:10],
            "research_content_missing": content_missing[:10],
            "qa_visual_blockers": [str(x) for x in visual_blockers[:10]],
            "benchmark_remaining_gaps": [str(x) for x in benchmark_gaps[:10]],
            "qa_review_issues": [str(x) for x in creative[:10]],
            "layout_review": [str(x) for x in layout[:10]],
        },
    }

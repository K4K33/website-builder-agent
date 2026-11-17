"""Independent source-backed concept QA using bounded visual batches.

Every genuine concept viewport is assessed once with the original site's
visual evidence. A second independent (text-only) ranking compares the three
grounded assessments. No part of a missing/invalid model response is invented
or treated as a passing browser/visual review.
"""
import json


def _normalize_verified_variant(report, ids, has_source):
    """Normalize only explicit reviewed facts, never insert missing QA evidence."""
    if not isinstance(report, dict):
        return None, "missing_json"
    normalized = dict(report)
    assessments = normalized.get("view_assessments")
    if isinstance(assessments, list):
        # Some multimodal models return a list with explicit view_id fields.
        # Re-key only if the claimed exact IDs are unique and complete.
        if all(isinstance(item, dict) and isinstance(item.get("view_id"), str)
               for item in assessments):
            names = [item["view_id"] for item in assessments]
            if len(names) == len(set(names)) == 4:
                assessments = {item["view_id"]: {
                    key: value for key, value in item.items() if key != "view_id"}
                    for item in assessments}
                normalized["view_assessments"] = assessments
    if not isinstance(assessments, dict) or set(assessments) != set(ids):
        return None, "view_ids"
    observation = normalized.get("observation")
    if not isinstance(observation, str) or len(observation.strip()) < 35:
        return None, "observation"
    issues = normalized.get("critical_issues")
    if (not isinstance(issues, list) or any(
            not isinstance(value, str) or not value.strip() for value in issues)):
        return None, "critical_issues"
    if has_source and normalized.get("source_reference_reviewed") is not True:
        return None, "original_source_review"
    if has_source:
        source_proof = normalized.get("source_comparison")
        if not isinstance(source_proof, str) or len(source_proof.strip()) < 65:
            return None, "source_comparison"
    for assessment in assessments.values():
        if not isinstance(assessment, dict) or assessment.get("verdict") not in (
                "pass", "needs_revision"):
            return None, "individual_verdict"
        for dimension in ("brand_evidence", "composition_evidence", "media_evidence"):
            value = assessment.get(dimension)
            if not isinstance(value, str) or len(value.strip()) < 35:
                return None, "grounded_view_evidence"
    return normalized, None


def staged_concept_review(*, research, order, views, sources, ask, root):
    if set(order) != {"A", "B", "C"}:
        raise RuntimeError("VISUAL_QA_INCOMPLETE: expected three independent concept directions")
    if len(views) != 12 or len(sources) not in (0, 2):
        raise RuntimeError("VISUAL_QA_INCOMPLETE: required real concept/source view count")
    if research.get("research_mode") != "verified_no_website" and len(sources) != 2:
        raise RuntimeError("VISUAL_QA_INCOMPLETE: original-site screenshot evidence missing")
    if sources and [source.get("viewport") for source in sources] != [
            "desktop", "mobile"]:
        raise RuntimeError("VISUAL_QA_INCOMPLETE: original screenshot order must be desktop/mobile")
    seen = set()
    reports = {}
    all_assessments = {}
    for alias in ("A", "B", "C"):
        selected = [v for v in views if v.get("alias") == alias]
        ids = [v.get("id") for v in selected]
        if len(ids) != 4 or len(set(ids)) != 4 or any(v in seen for v in ids):
            raise RuntimeError("VISUAL_QA_INCOMPLETE: exact four unique view IDs per direction")
        seen.update(ids)
        # Three paired JPEG panels, not one seven-panel high-latency request.
        # All originals remain separate and the paired overview never replaces
        # the browser's actual, full-size source screenshots.
        image_paths = [str(root / v["path"]) for v in selected]
        image_paths.extend(s["path"] for s in sources)
        system = (
            "You are an independent expert website design reviewer, not the site "
            "author. Inspect all FOUR attached individual viewport screenshots "
            "for this single direction and BOTH ORIGINAL-company screenshots "
            "where available. The first FOUR attached images are new concept "
            "viewports. Image FIVE is the ORIGINAL company's desktop page. "
            "Image SIX is the ORIGINAL company's mobile page. Keep their "
            "visual evidence separate from concept-generated marketing copy. "
            "Do not fabricate inspection or mark uncertain evidence as pass. "
            "Return JSON object with observation (at least 35 characters), "
            "critical_issues (array), source_reference_reviewed (boolean), "
            "source_comparison (at least 65 characters describing concrete "
            "original desktop/mobile brand patterns and what this version "
            "keeps or loses; do not claim visual inspection if unavailable), "
            "and view_assessments (object indexed by EVERY provided view ID). "
            "Each view assessment must have verdict 'pass' or 'needs_revision', "
            "brand_evidence, composition_evidence and media_evidence (each at "
            "least 35 concrete characters). Reject missing logos, missing real "
            "content, inaccessible mobile layouts, or visual downgrades. "
            "Do not use the proposed design's own quality claims as evidence."
        )
        packet = {
            "direction": alias,
            "required_view_ids_in_order": ids,
            "verified_facts": research.get("company_facts"),
            "brand_preservation_plan": research.get("brand_preservation_plan"),
            "visitor_tasks": (research.get("site_architecture") or {}).get("pages"),
            "source_reference_views": [
                {"viewport": s.get("viewport"), "sha256": s.get("sha256")}
                for s in sources],
            "required_output_json_keys": {
                "observation": "At least 35 characters of concrete visual assessment",
                "critical_issues": ["Only actual visible critical problems, otherwise []"],
                "source_reference_reviewed": True if sources else False,
                "source_comparison": (
                    "Describe observable ORIGINAL DESKTOP AND MOBILE brand assets, "
                    "imagery, layout and what the redesign demonstrably preserves. "
                    "If original screenshot unavailable say it is unavailable."
                ) if sources else "No company website was verified.",
                "view_assessments": {
                    view_id: {
                        "verdict": "pass OR needs_revision",
                        "brand_evidence": "At least 35 visual evidence characters",
                        "composition_evidence": "At least 35 visual evidence characters",
                        "media_evidence": "At least 35 visual evidence characters",
                    } for view_id in ids
                },
            },
        }
        report = None
        issue_code = None
        for attempt in range(2):
            instructions = system
            if attempt:
                instructions += (
                    " The prior response missed REQUIRED JSON contract fields: "
                    + str(issue_code) +
                    ". Return one complete, self-contained assessment of the "
                    "same attached genuine screenshots, with EXACT view ID keys. "
                    "This is the only bounded correction attempt. Do not "
                    "invent any missing evidence or silently approve defects."
                )
            candidate = ask(instructions, json.dumps(packet, ensure_ascii=False),
                            image_paths=image_paths, max_tokens=2800)
            report, issue_code = _normalize_verified_variant(
                candidate, ids, bool(sources))
            if issue_code is None:
                break
        if issue_code is not None:
            raise RuntimeError("VISUAL_QA_INCOMPLETE: " + issue_code)
        assessments = report["view_assessments"]
        observation = report["observation"]
        issues = report["critical_issues"]
        reports[alias] = {
            "observation": observation.strip(),
            "critical_issues": issues,
            "source_comparison": report.get("source_comparison", ""),
            "passing_views": sum(v["verdict"] == "pass" for v in assessments.values()),
        }
        all_assessments.update(assessments)
    if len(seen) != 12 or len(all_assessments) != 12:
        raise RuntimeError("VISUAL_QA_INCOMPLETE: incomplete real screenshot evaluation")
    ranking = ask(
        "Independently compare THREE source-grounded visual reviews from a "
        "separate verified reviewer. Choose the strongest concept, not the "
        "first or the most enthusiastic. Never ignore reported critical issues "
        "or deficient viewports. Return JSON with selected_alias A/B/C and "
        "cross_comparison (at least 35 characters, comparing all three). "
        "If no complete candidate passes, return selected_alias null.",
        json.dumps({"visual_evidence_review": reports}, ensure_ascii=False),
        image_paths=None, max_tokens=700)
    if not isinstance(ranking, dict) or not isinstance(
            ranking.get("cross_comparison"), str) or len(
            ranking["cross_comparison"].strip()) < 35:
        raise RuntimeError("VISUAL_QA_INCOMPLETE: cross-concept ranking missing")
    selected = ranking.get("selected_alias")
    if selected not in reports:
        raise RuntimeError("VISUAL_QA_INCOMPLETE: no acceptable concept selected")
    if (reports[selected]["critical_issues"] or
        reports[selected]["passing_views"] != 4):
        raise RuntimeError("VISUAL_QA_INCOMPLETE: selected concept has unresolved visual defects")
    return {
        "selected_alias": selected,
        "observations": {alias: item["observation"] for alias, item in reports.items()},
        "critical_issues": {alias: item["critical_issues"] for alias, item in reports.items()},
        "reviewed_view_ids": sorted(seen),
        "view_assessments": all_assessments,
        "source_reference_reviewed": len(sources) == 2,
        "cross_comparison": ranking["cross_comparison"].strip(),
        "review_batches": 3,
    }

"""Independent source-backed concept QA using bounded visual batches.

Every genuine concept viewport is assessed once with the original site's
visual evidence. A second independent (text-only) ranking compares the three
grounded assessments. No part of a missing/invalid model response is invented
or treated as a passing browser/visual review.
"""
import json


def staged_concept_review(*, research, order, views, sources, ask, root):
    if set(order) != {"A", "B", "C"}:
        raise RuntimeError("VISUAL_QA_INCOMPLETE: expected three independent concept directions")
    if len(views) != 12 or len(sources) not in (0, 2):
        raise RuntimeError("VISUAL_QA_INCOMPLETE: required real concept/source view count")
    if research.get("research_mode") != "verified_no_website" and len(sources) != 2:
        raise RuntimeError("VISUAL_QA_INCOMPLETE: original-site screenshot evidence missing")
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
            "author. Inspect all FOUR attached real viewport screenshots for "
            "this single direction and BOTH original-company source screenshots "
            "where available. In the paired images, the first two panels are "
            "concept views 01/02, the next two are concept views 03/04, and "
            "the last two are original-site desktop/mobile, not concept views. "
            "Do not fabricate inspection or mark uncertain evidence as pass. "
            "Return JSON object with observation (at least 35 characters), "
            "critical_issues (array), source_reference_reviewed (boolean), "
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
        }
        report = ask(system, json.dumps(packet, ensure_ascii=False),
                     image_paths=image_paths, max_tokens=2800)
        if not isinstance(report, dict):
            raise RuntimeError("VISUAL_QA_INCOMPLETE: independent image assessment missing")
        assessments = report.get("view_assessments")
        observation = report.get("observation")
        issues = report.get("critical_issues")
        if (not isinstance(assessments, dict) or set(assessments) != set(ids)
            or not isinstance(observation, str) or len(observation.strip()) < 35
            or not isinstance(issues, list)
            or any(not isinstance(issue, str) or not issue.strip() for issue in issues)
            or (sources and report.get("source_reference_reviewed") is not True)):
            raise RuntimeError("VISUAL_QA_INCOMPLETE: source-backed variant report invalid")
        for view_id, assessment in assessments.items():
            if (not isinstance(assessment, dict) or
                assessment.get("verdict") not in ("pass", "needs_revision")):
                raise RuntimeError("VISUAL_QA_INCOMPLETE: individual visual verdict missing")
            for dimension in ("brand_evidence", "composition_evidence", "media_evidence"):
                value = assessment.get(dimension)
                if not isinstance(value, str) or len(value.strip()) < 35:
                    raise RuntimeError("VISUAL_QA_INCOMPLETE: specific visual evidence missing")
        reports[alias] = {
            "observation": observation.strip(),
            "critical_issues": issues,
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

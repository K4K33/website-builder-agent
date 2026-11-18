"""Evidence and design decisions required before generation, never an optional prompt."""

from pathlib import Path
from urllib.parse import urlsplit
from utils.quality import canonical_url

MIN_REFERENCES = 3
DESIGN_DIMENSIONS = {"first_view", "service_hierarchy", "contact_path", "mobile"}


def resolve_observation_indices(research):
    """Use only an existing observation from the decision's own reference."""
    decisions = research.get("design_decisions")
    if not isinstance(decisions, list):
        return
    observations_by_url = {
        canonical_url(record["url"]): record.get("observations")
        for record in research["design_benchmark"]
    }
    for decision in decisions:
        if not isinstance(decision, dict) or "observation_index" not in decision:
            continue
        index = decision.pop("observation_index")
        url = canonical_url(decision.get("reference_url"))
        observations = observations_by_url.get(url)
        if (type(index) is not int or not isinstance(observations, list)
                or not 1 <= index <= len(observations)):
            raise RuntimeError("Invalid design observation index for its reference.")
        decision["observation"] = observations[index - 1]


COMPARISON_FIELDS = ("observations", "apply", "avoid")


def _text_list(value):
    return isinstance(value, list) and bool(value) and all(
        isinstance(item, str) and item.strip() for item in value
    )


def merge_reference_comparisons(evidence, rows):
    """Take comparison notes only, matching each row to a captured URL."""
    by_url = {canonical_url(row.get("url")): row for row in rows
              if isinstance(row, dict)} if isinstance(rows, list) else {}
    return [
        {
            **record,
            **{key: by_url.get(canonical_url(record["url"]), {}).get(key, record.get(key, []))
               for key in COMPARISON_FIELDS},
        }
        for record in evidence
    ]


def validate_benchmark(research, target_url="", *, require_comparison=True):
    records = research.get("design_benchmark", []) if isinstance(research, dict) else []
    facts = research.get("company_facts") or {}
    industry = str(facts.get("industry", "")).strip().casefold()
    target = urlsplit(canonical_url(target_url)).hostname
    domains, accepted = set(), []
    blockers = set()
    for record in records:
        if not isinstance(record, dict):
            blockers.add("reference_record")
            continue
        url = canonical_url(record.get("url"))
        domain = urlsplit(url).hostname
        if not domain or domain == target or domain in domains:
            blockers.add("reference_domain")
            continue
        if require_comparison and missing_comparison_fields(record):
            blockers.update(missing_comparison_fields(record))
            continue
        match = record.get("industry_match")
        if (not isinstance(match, dict) or not industry or match.get("same_industry") is not True
                or str(match.get("target_industry", "")).strip().casefold() != industry
                or not isinstance(match.get("reason"), str) or not match["reason"].strip()):
            blockers.add("industry_match")
            continue
        quote, source = match.get("evidence_quote"), record.get("site_text")
        if not isinstance(quote, str) or not quote.strip() or not isinstance(source, str) or quote not in source:
            blockers.add("source_quote")
            continue
        shots = record.get("screenshots") or {}
        if not isinstance(shots, dict) or not all(
            isinstance(shots.get(view), str) and Path(shots[view]).is_file()
            for view in ("desktop", "mobile")
        ):
            blockers.add("screenshots")
            continue
        domains.add(domain)
        accepted.append(record)
    if len(accepted) < MIN_REFERENCES:
        raise RuntimeError(
            "Design benchmark incomplete: compare at least three independent same-industry "
            "operators with desktop/mobile screenshots, source-backed industry matches, "
            "observations, adaptations and exclusions. "
            "Missing checks: " + ",".join(sorted(blockers or {"reference_count"}))
        )
    return accepted


def missing_comparison_fields(record):
    return [key for key in COMPARISON_FIELDS if not _text_list(record.get(key))]


def validate_design_plan(research, target_url=""):
    benchmark = validate_benchmark(research, target_url)
    urls = {canonical_url(record["url"]): record for record in benchmark}
    recommendations = research.get("design_recommendations") or {}
    motion = recommendations.get("motion_plan")
    if not isinstance(motion, dict) or not all(
            isinstance(motion.get(key), str) and motion[key].strip()
            for key in ("purpose", "implementation", "reduced_motion", "verification")):
        raise RuntimeError("A purposeful motion plan with static fallback and verification is required.")
    decisions = research.get("design_decisions")
    if not isinstance(decisions, list) or not decisions:
        raise RuntimeError("A reference-informed design plan is required before building.")
    ids, dimensions, used = set(), set(), set()
    for item in decisions:
        if not isinstance(item, dict):
            raise RuntimeError("Invalid design decision.")
        for key in ("id", "dimension", "reference_url", "observation", "adaptation", "section_id", "acceptance_check"):
            if not isinstance(item.get(key), str) or not item[key].strip():
                raise RuntimeError("Incomplete design decision: " + key)
        url = canonical_url(item["reference_url"])
        if (item["id"] in ids or item["dimension"] not in DESIGN_DIMENSIONS or url not in urls
                or item["observation"] not in urls[url]["observations"]):
            raise RuntimeError("Design decisions must trace to observed references with unique IDs.")
        ids.add(item["id"]); dimensions.add(item["dimension"]); used.add(url)
    if dimensions != DESIGN_DIMENSIONS or used != set(urls):
        raise RuntimeError("Design plan must use every reference and cover first view, services, contact and mobile.")
    return decisions


def reference_image_inputs(benchmark):
    """Keep the actual visual inputs and their ordered labels together."""
    paths, labels = [], []
    for record in benchmark:
        for view in ("desktop", "mobile"):
            path = record["screenshots"][view]
            paths.append(path)
            labels.append({"image": len(paths), "url": record["url"], "viewport": view})
            # This is a contact sheet of FIVE actual sequential scroll
            # positions, not a hero screenshot or a design rating.
            timeline = ((record.get("screenshots") or {}).get("scroll_experience") or {}).get(view) or {}
            sheet = timeline.get("scroll_sequence_image")
            if isinstance(sheet,str) and Path(sheet).is_file():
                paths.append(sheet)
                labels.append({"image": len(paths), "url": record["url"],
                               "viewport": view, "kind": "five_step_live_scroll_sequence",
                               "read_direction": "left_to_right"})
    return paths, labels

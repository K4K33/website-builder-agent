"""Evidence and design decisions required before generation, never an optional prompt."""

from pathlib import Path
from urllib.parse import urlsplit
from utils.quality import canonical_url

MIN_REFERENCES = 3
DESIGN_DIMENSIONS = {"first_view", "service_hierarchy", "contact_path", "mobile"}


def validate_benchmark(research, target_url=""):
    records = research.get("design_benchmark", []) if isinstance(research, dict) else []
    facts = research.get("company_facts") or {}
    industry = str(facts.get("industry", "")).strip().casefold()
    target = urlsplit(canonical_url(target_url)).hostname
    domains, accepted = set(), []
    for record in records:
        if not isinstance(record, dict):
            continue
        url = canonical_url(record.get("url"))
        domain = urlsplit(url).hostname
        if not domain or domain == target or domain in domains:
            continue
        if not all(isinstance(record.get(key), list) and record[key]
                   and all(isinstance(item, str) and item.strip() for item in record[key])
                   for key in ("observations", "apply", "avoid")):
            continue
        match = record.get("industry_match") or {}
        if (not industry or match.get("same_industry") is not True
                or str(match.get("target_industry", "")).strip().casefold() != industry
                or not isinstance(match.get("reason"), str) or not match["reason"].strip()):
            continue
        quote, source = match.get("evidence_quote"), record.get("site_text")
        if not isinstance(quote, str) or not quote.strip() or not isinstance(source, str) or quote not in source:
            continue
        shots = record.get("screenshots") or {}
        if not isinstance(shots, dict) or not all(
            isinstance(shots.get(view), str) and Path(shots[view]).is_file()
            for view in ("desktop", "mobile")
        ):
            continue
        domains.add(domain)
        accepted.append(record)
    if len(accepted) < MIN_REFERENCES:
        raise RuntimeError(
            "Design benchmark incomplete: compare at least three independent same-industry "
            "operators with desktop/mobile screenshots, source-backed industry matches, "
            "observations, adaptations and exclusions. Research again before building."
        )
    return accepted


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
    return paths, labels

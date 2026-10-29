"""Conservative, offline-only release-readiness audit.

An offline/mock QA pass is NOT an autonomous paid-model benchmark. This
module inspects persistent evidence from independently authorized live runs.
It never calls an AI provider, publishes a site, or contacts a customer.
"""
from hashlib import sha256
from pathlib import Path

import config
from agents.qa import review_passes
from utils.design_benchmark import validate_benchmark, validate_design_plan

REQUIRED_VIEWS = ("desktop", "tablet", "mobile", "small_mobile")


def inspect_candidate(slug: str, company: dict) -> dict:
    problems = []
    build = company.get("build") or {}
    qa = company.get("qa") or {}
    approval = company.get("approval") or {}
    research = company.get("research") or {}
    url = company.get("url", "")
    facts = research.get("company_facts") or {}
    industry = str(facts.get("industry") or "").strip().casefold()
    model = str(build.get("model") or "").strip()
    mode = str(build.get("generation_mode") or "api").strip().casefold()

    if not industry:
        problems.append("Industry is missing from verified research.")
    if not url:
        problems.append("Source company URL is missing.")
    if (not model or model in {"openrouter/free", "test/model"}
            or model.endswith(":free") or mode != "api"):
        problems.append("No independently generated paid-model build evidence (offline/external builds excluded).")

    benchmark, decisions = [], []
    try:
        benchmark = validate_benchmark(research, url)
        decisions = validate_design_plan(research, url)
    except (RuntimeError, TypeError, ValueError) as exc:
        problems.append("Industry reference and traceable design evidence missing: " + str(exc))

    version = build.get("version")
    path = build.get("output_path")
    digest = None
    expected = (Path(config.OUTPUT_DIR) / slug / "index.html").resolve()
    try:
        target = Path(path) if path else None
        if target is None or target.is_symlink() or target.resolve() != expected or not target.is_file():
            raise ValueError("Expected versioned output file missing or unsafe path")
        digest = sha256(target.read_bytes()).hexdigest()
    except (OSError, ValueError, TypeError) as exc:
        problems.append("Current HTML artifact missing or unsafe: " + str(exc))
    if not isinstance(version, int) or version < 1:
        problems.append("Build version must be a positive integer.")
    if (qa.get("overall_pass") is not True
            or qa.get("build_version") != version
            or not digest or qa.get("html_sha256") != digest):
        problems.append("Current HTML does not have matching passing QA.")
    if (approval.get("approved") is not True
            or approval.get("build_version") != version
            or not digest or approval.get("html_sha256") != digest):
        problems.append("Human approval is missing or stale.")
    if (not (qa.get("automated") or {}).get("automated_pass")
            or not (qa.get("browser") or {}).get("pass")):
        problems.append("Passing static and browser validation evidence is missing.")

    screenshots = (qa.get("browser") or {}).get("screenshots") or {}
    for viewport in REQUIRED_VIEWS:
        file = screenshots.get(viewport)
        if not file or not Path(file).is_file() or not Path(file).stat().st_size:
            problems.append("Missing actual QA screenshot: " + viewport)

    if benchmark and decisions and not review_passes(
        qa.get("content_review"),
        [record["url"] for record in benchmark],
        decisions,
    ):
        problems.append("Comparative visual/content QA evidence is missing or below threshold.")

    return {"company": slug, "industry": industry, "eligible": not problems,
            "issues": problems, "build_version": version, "html_sha256": digest}


def readiness_report(companies: dict, min_industries: int = 3) -> dict:
    if min_industries < 3:
        raise ValueError("At least three independent sectors are required.")
    rows = [inspect_candidate(slug, company) for slug, company in sorted(companies.items())]
    eligible = [row for row in rows if row["eligible"]]
    industries = sorted({row["industry"] for row in eligible})
    return {
        "ready_for_review": len(industries) >= min_industries,
        "qualified_industries": industries,
        "required_industries": min_industries,
        "qualifying_companies": [row["company"] for row in eligible],
        "evaluated": rows,
        "limitations": [
            "This reads self-reported local files; it is not cryptographic proof of a provider API run.",
            "Even a passing score needs manual factual, accessibility, privacy, copyright and customer-acceptance review.",
            "A passed audit does not publish a site or authorize outreach.",
        ],
    }

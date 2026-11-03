"""Persist recurring Kaurivo quality issues, not fabricated autonomous fixes.

Automatic QA findings enter a cross-project ledger. A repeated issue becomes
a universal candidate. A new rule becomes enforceable only after a real
checker and regression test have been supplied. General owner feedback
is immediately tracked, while customer-specific tastes remain local.
"""
from __future__ import annotations

import json
from pathlib import Path
import re


CATEGORIES = {
    "sector_recognition": (
        "sector_recognition", "missing_bicycle_first_view",
        "wrong_industry_impression", "looks like a university",
        "yliopiston sivu", "toimialan tunnistettavuus",
    ),
    "company_voice_and_rhythm": (
        "company_voice_and_rhythm", "text strips", "repeated marketing copy",
        "sisältöpalkki", "samanlaista tekstiä", "institutional brochure",
    ),
    "source_bound_social_proof": (
        "source_bound_social_proof", "unsourced_customer_review",
        "changed_source_review_rating", "unverified_aggregate_rating",
        "arvostelun tähdet", "keksitty asiakaspalaute", "fake review rating",
    ),
    "no_decorative_numbering": ("numerointi", "decorative card numbering", "card-number"),
    "natural_copy": ("natural_copy", "source narration", "repeated paragraph",
                     "placeholder", "ai-roska", "contrast-pair"),
    "original_brand": ("original_brand", "original logo", "brand"),
    "sponsor_and_partner_marks": ("footer", "sponsor", "partner", "kumppani"),
    "content_parity": ("content_parity", "old-to-new", "source", "puuttuva palvelu"),
    "dietary_accuracy": ("dietary", "allergen", "g/l/m"),
    "accurate_media": ("photo", "before/after", "kuva"),
    "navigation_and_links": ("broken link", "empty link", "cta"),
    "contact_and_forms": ("form", "lomake", "lead"),
    "contrast_and_accessibility": ("contrast", "a11y", "aria", "keyboard"),
    "responsive_performance": ("mobile", "overflow", "scroll", "performance"),
    "unique_art_direction": ("similar layout", "reused customer", "same template"),
}


def classify_issue(message: str) -> str:
    text = str(message or "").casefold()
    for category, terms in CATEGORIES.items():
        if any(t.casefold() in text for t in terms):
            return category
    return "needs_classification"


def _base_ledger() -> dict:
    return {"schema_version": 1, "issues": {}, "user_rules": []}


def load_ledger(path: str | Path) -> dict:
    file = Path(path)
    if not file.is_file():
        return _base_ledger()
    value = json.loads(file.read_text(encoding="utf-8"))
    if not isinstance(value, dict) or value.get("schema_version") != 1:
        raise ValueError("Unsupported global Kaurivo quality ledger")
    return value


def save_ledger(path: str | Path, ledger: dict) -> None:
    file = Path(path)
    file.parent.mkdir(parents=True, exist_ok=True)
    tmp = file.with_suffix(file.suffix + ".tmp")
    tmp.write_text(json.dumps(ledger, indent=2, ensure_ascii=False, sort_keys=True)
                   + "\n", encoding="utf-8")
    tmp.replace(file)


def record_qa_findings(
    ledger: dict, company_slug: str, findings: list[str]
) -> dict:
    """Promote a category after recurrence in *different* client projects."""
    if not company_slug or not isinstance(findings, list):
        raise ValueError("Project id and QA findings required")
    known = ledger.setdefault("issues", {})
    for msg in findings:
        category = classify_issue(msg)
        entry = known.setdefault(category, {
            "project_slugs": [], "examples": [], "status": "observed",
        })
        projects = entry["project_slugs"]
        if company_slug not in projects:
            projects.append(company_slug)
            projects.sort()
        if msg not in entry["examples"] and len(entry["examples"]) < 10:
            entry["examples"].append(msg[:350])
        if len(projects) >= 2:
            entry["status"] = "universal_candidate"
    return ledger


def record_owner_feedback(
    ledger: dict, *,
    text: str, company_slug: str = "", applies_to_all: bool,
    regression_test: str = "", checker: str = "",
) -> dict:
    """Capture owner rule, but never claim unknown ideas already enforceable."""
    if not text.strip():
        raise ValueError("Feedback text is required")
    category = classify_issue(text)
    if not applies_to_all:
        # Do not spread one client's particular brand preferences.
        return {"scope": "company", "company_slug": company_slug,
                "rule": text.strip(), "status": "local_only"}
    known_checker = checker in CATEGORIES and checker == category
    # Test filenames are not sufficient without an actual checked-in source.
    relative = Path(regression_test)
    safe_path = (regression_test.startswith("tests/test_")
                 and regression_test.endswith(".py")
                 and ".." not in relative.parts)
    has_test = safe_path and (Path(__file__).resolve().parents[1] / relative).is_file()
    status = "active" if known_checker and has_test else "needs_implementation"
    rule = {"scope": "universal", "category": category, "rule": text.strip(),
            "status": status, "checker": checker, "regression_test": regression_test}
    if rule not in ledger.setdefault("user_rules", []):
        ledger["user_rules"].append(rule)
    return rule


def global_instructions(ledger: dict) -> str:
    """Feed accepted lessons and recurring cross-company failures to Builder.

    New unimplemented issues are presented as research/QA warnings, never as
    if an automatic detector or the final repair already exists.
    """
    entries = [r for r in ledger.get("user_rules", [])
               if r.get("scope") == "universal"]
    lines = [
        "- GLOBAL QUALITY RULE: " + str(r.get("rule") or "")[:450]
        + (" [checked by: " + str(r.get("checker")) + "]"
           if r.get("status") == "active"
           else " [requires implementation and regression test; do not claim done]")
        for r in entries
    ]
    for category, issue in (ledger.get("issues") or {}).items():
        if issue.get("status") != "universal_candidate":
            continue
        example = str((issue.get("examples") or [""])[0])[:180]
        lines.append(
            "- RECURRING CROSS-PROJECT QA PROBLEM: " + str(category)
            + "; evidence: " + example
            + ". Avoid repeating it. Classify, implement a real fix/test and "
              "do not claim the general problem is already corrected."
        )
    return "\n".join(lines)


def universal_rules_pending_implementation(ledger: dict) -> list[str]:
    return [str(r.get("rule") or "") for r in ledger.get("user_rules", [])
            if r.get("scope") == "universal" and r.get("status") != "active"]

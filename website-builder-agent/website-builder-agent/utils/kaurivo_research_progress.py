"""Private same-job partial research progress: never a finished design brief.

Research is costly: the 24-page original-site audit and first successful AI
calls must not be repeated merely because a later free provider returned 429.
Stored only in authenticated, digest-checked per-job private checkpoints.
"""
from __future__ import annotations

import json

from utils.state import upsert_company

MILESTONES = ("source", "facts", "references")
_MAX_JSON_BYTES = 16 * 1024 * 1024


def get_progress(company: dict, *, source_url: str, master_prompt_sha256: str) -> dict:
    raw = company.get("research_progress")
    if not isinstance(raw, dict):
        return {}
    if (raw.get("version") != 1 or raw.get("source_url") != source_url or
        raw.get("master_prompt_sha256") != master_prompt_sha256 or
        raw.get("milestone") not in MILESTONES or company.get("url") != source_url):
        # Old Master Prompt/source input must never silently pass through.
        return {}
    if not isinstance(raw.get("site_data"), dict):
        return {}
    inventory = raw.get("source_inventory")
    if not isinstance(inventory, dict) or not isinstance(inventory.get("pages"), list) or not inventory["pages"]:
        return {}
    if raw["milestone"] in ("facts", "references") and not isinstance(raw.get("extracted"), dict):
        return {}
    if raw["milestone"] == "references" and (
        not isinstance(raw.get("selected"), list) or len(raw["selected"]) != 3 or
        not isinstance(raw.get("references"), list) or
        not isinstance(raw.get("reference_evidence"), list) or len(raw["reference_evidence"]) != 3):
        return {}
    if len(json.dumps(raw, ensure_ascii=False).encode("utf-8")) > _MAX_JSON_BYTES:
        return {}
    return raw


def save_progress(slug: str, company: dict, *, milestone: str,
                  source_url: str, master_prompt_sha256: str,
                  **data) -> dict:
    if milestone not in MILESTONES:
        raise ValueError("unapproved research milestone")
    prior = get_progress(company, source_url=source_url,
                         master_prompt_sha256=master_prompt_sha256)
    if prior and MILESTONES.index(milestone) < MILESTONES.index(prior["milestone"]):
        raise ValueError("research checkpoint cannot regress")
    work = dict(prior)
    work.update(data)
    work.update({"version": 1, "milestone": milestone,
                 "source_url": source_url,
                 "master_prompt_sha256": master_prompt_sha256})
    if not isinstance(work.get("site_data"), dict) or not isinstance(work.get("source_inventory"), dict):
        raise ValueError("original source evidence missing")
    if milestone in ("facts", "references") and not isinstance(work.get("extracted"), dict):
        raise ValueError("fact extraction evidence missing")
    if milestone == "references" and (
        not isinstance(work.get("selected"), list) or len(work["selected"]) != 3 or
        not isinstance(work.get("reference_evidence"), list) or len(work["reference_evidence"]) != 3
    ):
        raise ValueError("three verified industry references required")
    if len(json.dumps(work, ensure_ascii=False).encode("utf-8")) > _MAX_JSON_BYTES:
        raise ValueError("research partial exceeds private checkpoint size")
    upsert_company(slug, {"research_progress": work})
    return work

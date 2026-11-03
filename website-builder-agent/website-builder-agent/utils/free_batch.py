"""Resumable local-only batch orchestrator; no per-company paid API charges.

The finite job queue is not silently truncated: limit=0 processes ALL eligible
entries. An unavailable model, missing rights or research blockers are recorded
as blocked, never disguised as a completed customer-ready site.
"""
from __future__ import annotations
from datetime import datetime, timezone
import json
from pathlib import Path
import time


SKIP_STATES = {"approved", "outreach_drafted", "outreach_approved", "qa_passed"}


def process_free_batch(queue: dict, process, *, status_path: str | Path,
                       limit: int = 0, retry_failed: bool = False,
                       now=None) -> dict:
    """Run saved candidates sequentially, checkpointing after every attempt.

    process(slug) should execute the already opt-in, local-only pipeline.
    Sequential local inference avoids GPU contention; scale via better hardware,
    not a hidden paid cloud fallback or inaccurate claims about throughput.
    """
    if not isinstance(queue, dict):
        raise TypeError("Saved company queue must be a dictionary.")
    if limit < 0:
        raise ValueError("limit must be >= 0 (0 = no artificial cap)")
    file = Path(status_path)
    state = {"jobs": {}}
    if file.is_file():
        try:
            previous = json.loads(file.read_text(encoding="utf-8"))
            if isinstance(previous, dict) and isinstance(previous.get("jobs"), dict):
                state = previous
        except (OSError, ValueError):
            raise RuntimeError("Invalid previous batch checkpoint; refusing to erase work.")
    started = time.monotonic()
    report = {"attempted": [], "skipped": [], "eligible": 0, "remaining": 0,
              "successful_runs": 0, "blocked_or_failed": 0, "seconds": 0,
              "estimated_per_8h_from_observed_run": None}
    items = []
    for slug, company in queue.items():
        if not isinstance(company, dict):
            continue
        if company.get("status") in SKIP_STATES:
            report["skipped"].append({"slug": slug, "reason": "already_approved"})
            continue
        existing = state["jobs"].get(slug) or {}
        if existing.get("status") in ("completed", "blocked") and not retry_failed:
            report["skipped"].append({"slug": slug, "reason": "already_attempted"})
            continue
        items.append(slug)
    report["eligible"] = len(items)
    selected = items[:limit] if limit else items
    report["remaining"] = len(items) - len(selected)
    for slug in selected:
        before = time.monotonic()
        try:
            process(slug)
            result = {"status": "completed", "message": "Pipeline returned normally"}
            report["successful_runs"] += 1
        except Exception as error:
            result = {"status": "blocked", "message": (
                type(error).__name__ + ": " + str(error)[:850])}
            report["blocked_or_failed"] += 1
        elapsed = max(0.0, time.monotonic() - before)
        result["seconds"] = round(elapsed, 2)
        result["attempted_at"] = (
            now or datetime.now(timezone.utc)
        ).isoformat()
        state["jobs"][slug] = result
        file.parent.mkdir(parents=True, exist_ok=True)
        file.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
        report["attempted"].append({"slug": slug, **result})
    report["seconds"] = round(time.monotonic() - started, 2)
    durations = [item["seconds"] for item in report["attempted"]
                 if item["seconds"] > 0 and item["status"] == "completed"]
    if durations:
        mean = sum(durations) / len(durations)
        report["estimated_per_8h_from_observed_run"] = int(28800 // mean)
    report["note"] = (
        "Completed means the single-company pipeline returned; it does NOT "
        "certify 9.5/10, brand/photo rights, independent human review or "
        "customer acceptance. Any capacity estimate is based on actual "
        "finished local jobs only, not a promise."
    )
    return report

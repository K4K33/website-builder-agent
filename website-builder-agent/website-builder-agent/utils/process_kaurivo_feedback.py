"""Anonymized, optional FormSubmit feedback monitor, no public customer data."""
from __future__ import annotations
from collections import Counter
from datetime import datetime, timezone, timedelta
from typing import Any
from urllib.request import Request, urlopen
import json
import os
from utils.customer_feedback import triage_feedback


def recent_archive_digest(response: dict[str, Any], *, now: datetime | None = None) -> dict:
    """Summarize the last 24 hours without exposing customer info or raw feedback."""
    if now is None:
        now = datetime.now(timezone.utc)
    if now.tzinfo is None:
        raise ValueError("Timezone-aware now required.")
    if not isinstance(response, dict) or not isinstance(response.get("submissions"), list):
        raise ValueError("Unexpected form provider response.")
    counts, topics, ratings = Counter(), Counter(), Counter()
    seen = set()
    for item in response["submissions"]:
        if not isinstance(item, dict):
            continue
        data = item.get("form_data")
        if not isinstance(data, dict) or data.get("feedback_stage") != "post_sale_experience":
            continue
        stamp = item.get("submitted_at")
        raw_date = stamp.get("date") if isinstance(stamp, dict) else stamp
        if not isinstance(raw_date, str):
            continue
        try:
            dt = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        diff = now.astimezone(timezone.utc) - dt.astimezone(timezone.utc)
        if not timedelta(0) <= diff <= timedelta(hours=24):
            continue
        message = data.get("message") or ""
        score = data.get("rating")
        if not isinstance(message, str) or len(message.strip()) < 3:
            counts["invalid"] += 1
            continue
        try:
            score = int(score)
        except (ValueError, TypeError):
            counts["invalid"] += 1
            continue
        if not 1 <= score <= 5:
            counts["invalid"] += 1
            continue
        key = (raw_date, str(data.get("review_reference")), message, score)
        if key in seen:
            continue
        seen.add(key)
        tag = triage_feedback(message, rating=score)
        counts["reviewed_unverified"] += 1
        counts[tag["priority"]] += 1
        ratings[score] += 1
        topics.update(tag["categories"])
    return {
        "period": "rolling_24_hours_utc",
        "feedback_received_unverified": counts["reviewed_unverified"],
        "invalid_records": counts["invalid"],
        "requires_urgent_human_review": counts["urgent_review"],
        "requires_clarification": counts["clarify"],
        "ratings": {str(i): ratings[i] for i in range(1, 6)},
        "topic_counts": dict(topics),
        "automatic_fixes_applied": 0,
        "personal_data_in_report": False,
        "note": "All submissions require source verification; no review is published automatically.",
    }


def get_archive(api_key: str) -> dict:
    """One API request; sensitive archive URL is never printed."""
    if not api_key or not all(c.isalnum() or c in "_-" for c in api_key):
        raise ValueError("Archive key missing or invalid.")
    request = Request(
        "https://formsubmit.co/api/get-submissions/" + api_key,
        headers={"Accept": "application/json", "User-Agent": "KaurivoFeedbackMonitor/1"}
    )
    try:
        with urlopen(request, timeout=18) as resp:
            if resp.status != 200:
                raise RuntimeError("Archive unavailable.")
            result = json.loads(resp.read(1200000).decode("utf-8"))
    except Exception:
        raise RuntimeError("Form archive check failed; check activation and quota.") from None
    if not isinstance(result, dict) or result.get("success") not in (True, "true"):
        raise RuntimeError("Form provider did not confirm an archive response.")
    return result


def main() -> None:
    key = os.environ.get("KAURIVO_FORMSUBMIT_API_KEY", "").strip()
    if not key:
        print("Kaurivo feedback monitor not activated; no API request made.")
        return
    try:
        result = recent_archive_digest(get_archive(key))
    except Exception:
        print("Feedback archive check failed; please check provider activation or quotas.")
        raise SystemExit(1) from None
    text = json.dumps(result, ensure_ascii=False, sort_keys=True, indent=2)
    print(text)
    summary_file = os.environ.get("GITHUB_STEP_SUMMARY", "")
    if summary_file:
        with open(summary_file, "a", encoding="utf-8") as f:
            f.write("Kaurivo customer feedback (anonymized)\n\n")
            f.write(text + "\n")


if __name__ == "__main__":
    main()

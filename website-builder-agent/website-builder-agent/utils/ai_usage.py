"""Count free AI provider requests per demo job, across worker subprocesses.

The demo worker runs research/build/QA as child processes, so an in-memory
counter would miss most calls. When KAURIVO_AI_USAGE_FILE is set, every HTTP
request sent to a model provider appends one line "backend<TAB>stage". Only
counts are ever reported: no prompts, models' answers or company data.
"""
from __future__ import annotations

import os
from collections import Counter

_ENV = "KAURIVO_AI_USAGE_FILE"


def record(backend: str, stage: str | None) -> None:
    path = os.environ.get(_ENV, "")
    if not path:
        return
    safe_backend = "".join(c for c in str(backend) if c.isalnum() or c in "_-")[:24] or "unknown"
    safe_stage = "".join(c for c in str(stage or "none") if c.isalnum() or c in "_-")[:24] or "none"
    try:
        with open(path, "a", encoding="utf-8") as handle:
            handle.write(safe_backend + "\t" + safe_stage + "\n")
    except OSError:
        pass  # Measurement must never break a build.


def summary(path: str | None = None) -> dict:
    path = path or os.environ.get(_ENV, "")
    by_backend: Counter = Counter()
    by_stage: Counter = Counter()
    if path and os.path.isfile(path):
        with open(path, encoding="utf-8") as handle:
            for line in handle:
                parts = line.rstrip("\n").split("\t")
                if len(parts) == 2:
                    by_backend[parts[0]] += 1
                    by_stage[parts[0] + ":" + parts[1]] += 1
    return {"total": sum(by_backend.values()),
            "by_backend": dict(by_backend), "by_stage": dict(by_stage)}


def format_summary(path: str | None = None) -> str:
    data = summary(path)
    parts = [f"{key}={value}" for key, value in sorted(data["by_stage"].items())]
    return "total=" + str(data["total"]) + (" " + " ".join(parts) if parts else "")

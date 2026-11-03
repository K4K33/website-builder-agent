"""Reuse truthful real operator screenshots across unrelated company projects.

Local filenames are deterministic per URL, TTL bounds staleness, byte digests
detect changed/missing evidence, and no model/search credits are used.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
import json


TTL_DAYS = 7


def capture_cached(url: str, capture, *, cache_root: str | Path,
                   now: datetime | None = None) -> dict | None:
    now = now or datetime.now(timezone.utc)
    root = Path(cache_root).resolve()
    root.mkdir(parents=True, exist_ok=True)
    identity = sha256(url.encode("utf-8")).hexdigest()[:24]
    manifest = root / (identity + ".json")
    if manifest.is_file():
        try:
            saved = json.loads(manifest.read_text(encoding="utf-8"))
            observed = datetime.fromisoformat(saved.get("captured_at", ""))
            if (observed.tzinfo and observed <= now
                    and now - observed <= timedelta(days=TTL_DAYS)
                    and saved.get("source_url") == url):
                files = saved.get("screenshots") or {}
                if all(
                    isinstance(files.get(view), str)
                    and Path(files[view]).is_file()
                    and sha256(Path(files[view]).read_bytes()).hexdigest()
                        == (saved.get("sha256") or {}).get(view)
                    for view in ("desktop", "mobile")
                ):
                    return files
        except (OSError, ValueError, TypeError):
            pass
    shots = capture(url, "reference-" + identity)
    if not isinstance(shots, dict):
        return None
    if not all(
        isinstance(shots.get(view), str) and Path(shots[view]).is_file()
        for view in ("desktop", "mobile")
    ):
        return None
    digests = {
        view: sha256(Path(shots[view]).read_bytes()).hexdigest()
        for view in ("desktop", "mobile")
    }
    manifest.write_text(json.dumps({
        "source_url": url, "captured_at": now.isoformat(),
        "screenshots": shots, "sha256": digests,
        "note": "Real public operator screenshots. Not image reuse permission.",
    }, ensure_ascii=False, indent=2), encoding="utf-8")
    return shots

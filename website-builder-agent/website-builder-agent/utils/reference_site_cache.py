"""Cache observed public operator facts for repeated free sector benchmarking.

Every entry is a dated copy of an actually fetched URL, not invented search
results. TTL is short and bad/missing results do not become positive evidence.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
import json


def cached_analyze(url, analyzer, *, root="output/_reference_site_cache",
                   now=None, ttl_days=7):
    now = now or datetime.now(timezone.utc)
    folder = Path(root)
    file = folder / (sha256(url.encode("utf-8")).hexdigest() + ".json")
    if file.is_file():
        try:
            record = json.loads(file.read_text(encoding="utf-8"))
            at = datetime.fromisoformat(record.get("observed_at") or "")
            result = record.get("result")
            if (record.get("url") == url and at.tzinfo and
                    now - timedelta(days=ttl_days) <= at <= now and
                    isinstance(result, dict) and result.get("success") is True
                    and str(result.get("visible_text") or "").strip()):
                return result
        except (OSError, ValueError, TypeError):
            pass
    result = analyzer(url)
    if (isinstance(result, dict) and result.get("success") is True
            and str(result.get("visible_text") or "").strip()):
        data = {
            "url": url,
            "observed_at": now.isoformat(),
            "result": {
                "success": True,
                "title": str(result.get("title") or "")[:300],
                "visible_text": str(result.get("visible_text") or "")[:15000],
            },
        }
        folder.mkdir(parents=True, exist_ok=True)
        file.write_text(json.dumps(data, ensure_ascii=False), encoding="utf-8")
    return result

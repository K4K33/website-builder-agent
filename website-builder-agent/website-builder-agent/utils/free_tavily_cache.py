"""Reuse free-tier Tavily basic-search candidates across company jobs.

Only metadata genuinely returned by a verified free-plan request may enter
this cache. Source validation still happens separately in Research, and a
missing/failed provider call never creates a fake positive result.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone
from hashlib import sha256
from pathlib import Path
import json


def cached_free_search(query: str, search, *, cache_root="output/_tavily_free_cache",
                       now=None, ttl_days=14) -> list[dict]:
    if not isinstance(query, str) or not query.strip():
        raise ValueError("A real search query is required.")
    now = now or datetime.now(timezone.utc)
    file = Path(cache_root) / (sha256(query.casefold().strip().encode("utf-8")).hexdigest() + ".json")
    if file.is_file():
        try:
            obj = json.loads(file.read_text(encoding="utf-8"))
            when = datetime.fromisoformat(obj.get("observed_at") or "")
            data = obj.get("results")
            if (when.tzinfo and now - timedelta(days=ttl_days) <= when <= now
                    and obj.get("query") == query and isinstance(data, list)):
                return [item for item in data if isinstance(item, dict)
                        and isinstance(item.get("url"), str)][:10]
        except (OSError, ValueError, TypeError):
            pass
    rows = search(query, max_results=8)
    if not isinstance(rows, list):
        raise RuntimeError("Tavily free search returned non-list candidates.")
    results = [
        {"url": item["url"], "title": str(item.get("title") or "")[:200],
         "content": str(item.get("content") or "")[:1500]}
        for item in rows if isinstance(item, dict) and isinstance(item.get("url"), str)
    ][:10]
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_text(json.dumps({"query": query, "observed_at": now.isoformat(),
                                "results": results}, ensure_ascii=False), encoding="utf-8")
    return results

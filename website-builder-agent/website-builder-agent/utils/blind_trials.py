"""Kaurivo blind first-pass trial protocol.

Only experimental demos consume a *new business identity each time*.
Client projects may be revised under their own review process; a failed
internal trial produces general rules then moves to a previously unseen site.
All methods are offline and avoid API, GitHub actions, or customer outreach.
"""
from __future__ import annotations
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import re
from tempfile import NamedTemporaryFile
from urllib.parse import urlsplit

def _normalize(value: str) -> str:
    return re.sub(r"[^a-z0-9]+","-",str(value or "").casefold()).strip("-")

def _domain(value: str) -> str:
    v=str(value or "").strip()
    p=urlsplit(v if "://" in v else "https://"+v) if v else None
    h=(p.hostname or "").lower().removeprefix("www.") if p else ""
    return h if "." in h and h!="example.com" else ""

def _identifiers(company: dict, slug: str = "") -> tuple[str,str]:
    return _normalize(slug or company.get("slug") or company.get("name") or ""), _domain(
        company.get("url") or company.get("website") or ""
    )

def trial_history(history_path: str | Path, registry_path: str | Path) -> list[dict]:
    results=[]
    for path in (history_path, registry_path):
        file=Path(path)
        if file.is_file():
            data=json.loads(file.read_text(encoding="utf-8"))
            if not isinstance(data,dict) or not isinstance(data.get("trials"),list):
                raise ValueError("Invalid Kaurivo trial history JSON")
            results.extend(x for x in data["trials"] if isinstance(x,dict))
    return results

def assess_new_company(
    company: dict, *, slug: str = "",
    history: list[dict] | None = None
) -> dict:
    ident,domain=_identifiers(company,slug)
    if not ident and not domain:
        raise ValueError("Trial company needs a name/slug or public site domain")
    used=history or []
    matches=[]
    for row in used:
        seen_slug,seen_domain=_identifiers(row,row.get("slug") or "")
        if (ident and seen_slug==ident) or (domain and seen_domain==domain):
            matches.append(row)
    return {
        "eligible":not matches,
        "slug":ident,"domain":domain,
        "reason":"unseen company" if not matches else "previously tested company/domain; choose a different business",
        "past_trials":len(matches),
    }

def reserve_blind_trial(
    company: dict, *, slug: str = "",
    registry_path: str | Path,
    history_path: str | Path,
    now: str = "",
) -> dict:
    """Atomically register each first build; never quietly retry old tests.

    Caller must invoke BEFORE Research/Build for an internal benchmark.
    Local single-runner workflow assumed; no distributed lock is claimed.
    """
    history=trial_history(history_path,registry_path)
    outcome=assess_new_company(company,slug=slug,history=history)
    if not outcome["eligible"]:
        raise RuntimeError("Blind Kaurivo trial refused: "+outcome["reason"])
    when=now or datetime.now(timezone.utc).isoformat()
    entry={
      "slug":outcome["slug"],"url":("https://"+outcome["domain"]) if outcome["domain"] else "",
      "started_at":when,"mode":"first_pass_unseen","status":"reserved",
      "revision_count":0,"quality_evidence":"not_verified",
      "sector":str((company.get("research") or {}).get("company_facts",{}).get("industry")
                   or company.get("industry") or "")[:100],
    }
    destination=Path(registry_path)
    destination.parent.mkdir(parents=True,exist_ok=True)
    current=json.loads(destination.read_text(encoding="utf-8")) if destination.is_file() else {"trials":[]}
    current.setdefault("trials",[]).append(entry)
    with NamedTemporaryFile(mode="w",encoding="utf-8",dir=destination.parent,
                            prefix=".blind-trial-",delete=False) as f:
        json.dump(current,f,ensure_ascii=False,indent=2)
        temp=f.name
    os.replace(temp,destination)
    return entry

def first_pass_metrics(history: list[dict]) -> dict:
    """Real results only; missing scores remain unverified, not zero or ten."""
    trials=[t for t in history if t.get("mode")=="first_pass_unseen"]
    evidenced=[t for t in trials if isinstance(t.get("independent_quality_score"),(int,float))
               and not isinstance(t.get("independent_quality_score"),bool)
               and t.get("quality_evidence")=="verified"]
    return {
        "first_pass_trials":len(trials),
        "independently_reviewed":len(evidenced),
        "over_95_first_pass":sum(float(x["independent_quality_score"])>=9.5 for x in evidenced),
        "pass_rate":(sum(float(x["independent_quality_score"])>=9.5 for x in evidenced)/len(evidenced))
                     if evidenced else None,
        "note":"Historic hand-built demos are excluded; unverified quality is never counted as passed.",
    }

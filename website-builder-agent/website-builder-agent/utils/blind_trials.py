"""Kaurivo blind first-pass trial protocol.

Only experimental demos consume a *new business identity each time*.
Client projects may be revised under their own review process; a failed
internal trial produces general rules then moves to a previously unseen site.
All methods are offline and avoid API, GitHub actions, or customer outreach.
"""
from __future__ import annotations
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import re
import unicodedata
from tempfile import NamedTemporaryFile
from urllib.parse import urlsplit

def _normalize(value: str) -> str:
    text = unicodedata.normalize('NFKD', str(value or '').casefold())
    return re.sub(r"[^a-z0-9]+", "-", text.encode('ascii', 'ignore').decode()).strip('-')

def _company_keys(company, slug=''):
    names = [slug, company.get('slug'), company.get('name')]
    names += company.get('aliases') or []
    keys = {_normalize(value) for value in names if value}
    keys |= {re.sub(r'-(?:v\d+|20\d{6})$', '', key) for key in keys}
    domains = {_domain(company.get(field)) for field in ('url', 'website')}
    domains |= {_domain(value) for value in company.get('website_aliases', [])}
    business_id = _normalize(company.get('business_id') or company.get('y_tunnus'))
    return keys, domains - {''}, business_id

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
    names, domains, business_id = _company_keys(company, slug)
    if not ident and not domain:
        raise ValueError("Trial company needs a name/slug or public site domain")
    used=history or []
    matches=[]
    for row in used:
        seen_names, seen_domains, seen_id = _company_keys(row)
        if names & seen_names or domains & seen_domains or (business_id and business_id == seen_id):
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
      "name": company.get('name', ''),
      "aliases": company.get('aliases') or [],
      "website_aliases": [company.get('website', '')] + (company.get('website_aliases') or []),
      "business_id": company.get('business_id') or company.get('y_tunnus') or '',
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
               and math.isfinite(t['independent_quality_score'])
               and 0 <= t['independent_quality_score'] <= 10
               and t.get("quality_evidence")=="verified"]
    sectors = sorted({str(t.get('sector') or 'unknown') for t in trials})
    return {
        "first_pass_trials":len(trials),
        "independently_reviewed":len(evidenced),
        "over_95_first_pass":sum(float(x["independent_quality_score"])>=9.5 for x in evidenced),
        "pass_rate":(sum(float(x["independent_quality_score"])>=9.5
                         and x.get('release_eligible') is True for x in evidenced)/len(evidenced))
                     if evidenced else None,
        "unreviewed": len(trials) - len(evidenced),
        "coverage_by_sector": {sector: {
            "trials": sum(str(t.get('sector') or 'unknown') == sector for t in trials),
            "independently_reviewed": sum(str(t.get('sector') or 'unknown') == sector for t in evidenced),
        } for sector in sectors},
        "note":"Historic hand-built demos are excluded; unverified quality is never counted as passed.",
    }

def record_first_pass_qa(registry_path: str | Path, *, slug: str,
                         qa_report: dict, build: dict | None = None) -> dict:
    """Persist first-pass evidence without inventing independent 9.5 scores.

    A follow-up build cannot rewrite the initial grade; only the first
    QA result for a reserved trial counts. Evidence stays on the host
    that owns the local ignored registry, not in the public repository.
    """
    path=Path(registry_path)
    if not path.is_file():
        raise RuntimeError("First-pass trial registry is missing.")
    data=json.loads(path.read_text(encoding="utf-8"))
    records=data.get("trials") or []
    matches=[t for t in records if t.get("slug")==_normalize(slug)]
    if len(matches)!=1 or matches[0].get("mode")!="first_pass_unseen":
        raise RuntimeError("No unique recorded first-pass experiment for this company.")
    trial=matches[0]
    if trial.get("first_pass_recorded_at"):
        raise RuntimeError("Cannot overwrite original first-pass evidence with a revised build.")
    from hashlib import sha256
    if not isinstance(qa_report,dict):
        raise TypeError("QA evidence must be structured.")
    evidence={
        "technical_qa_pass":qa_report.get("overall_pass") is True,
        "missing_original_content":len((qa_report.get("source_fidelity") or {}).get("missing") or []),
        "missing_verified_facts":len((qa_report.get("content_parity") or {}).get("missing") or []),
        "browser_issue_count":len((qa_report.get("browser") or {}).get("issues") or []),
        "originality_warnings":len((qa_report.get("originality") or {}).get("warnings") or []),
        "originality_blockers":len((qa_report.get("originality") or {}).get("blocking_problems") or []),
        "source_page_count":(qa_report.get("source_fidelity") or {}).get("manifest",{}).get("source_page_count",0),
        "generated_page_count":len(qa_report.get("site_pages") or []),
        "ai_style_risk":(qa_report.get("content_review") or {}).get("ai_style_review",{}).get("risk_score"),
        "internal_visual_review":(qa_report.get("content_review") or {}).get("visual_review") or {},
        "independent_quality_score":None,
        "independent_quality_evidence":"NOT VERIFIED",
        "quality_scorecard": (qa_report.get('universal_quality') or {}).get('quality_scorecard'),
    }
    trial.update({
        "status":"first_pass_evaluated",
        "first_pass_recorded_at":datetime.now(timezone.utc).isoformat(),
        "first_pass_metrics":evidence,
        "quality_evidence":"not_verified",
        "first_pass_build_sha256":(build or {}).get("html_sha256") or qa_report.get("html_sha256") or "",
        "first_pass_site_sha256": qa_report.get('site_sha256') or '',
    })
    with NamedTemporaryFile(mode="w",encoding="utf-8",dir=path.parent,
                             prefix=".trial-report-",delete=False) as handle:
        json.dump(data,handle,ensure_ascii=False,indent=2)
        temporary=handle.name
    os.replace(temporary,path)
    return evidence


def record_trial_review(registry_path, *, slug, qa_report):
    """Attach the first evidenced review only to the unchanged first build."""
    path = Path(registry_path)
    data = json.loads(path.read_text(encoding='utf-8'))
    rows = [row for row in data['trials'] if row.get('slug') == _normalize(slug)]
    card = (qa_report.get('universal_quality') or {}).get('quality_scorecard') or {}
    if len(rows) != 1 or not rows[0].get('first_pass_recorded_at'):
        return False
    row = rows[0]
    if row.get('quality_evidence') == 'verified':
        return False  # never overwrite the original independent result
    original = row.get('first_pass_site_sha256')
    if not original or qa_report.get('site_sha256') != original:
        raise RuntimeError('Independent review must describe the original first-pass site bundle.')
    if card.get('complete') is not True or type(card.get('mean')) not in (int, float):
        return False
    row.update({'quality_evidence': 'verified', 'independent_quality_score': card['mean'],
                'release_eligible': card.get('release_eligible') is True
                                    and qa_report.get('overall_pass') is True,
                'independent_scorecard': card})
    with NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        temporary = handle.name
    os.replace(temporary, path)
    return True


def claim_trial_build(company, *, registry_path, slug):
    """Consume a trial's single generation before any model call or import.

    Failed attempts remain consumed. Fix the general service and select a new
    company; do not turn a failed first pass into a silently revised pass.
    """
    if (company.get('quality_trial') or {}).get('mode') != 'first_pass_unseen':
        return
    path = Path(registry_path)
    data = json.loads(path.read_text(encoding='utf-8'))
    rows = [r for r in data['trials'] if r.get('slug') == _normalize(slug)]
    if len(rows) != 1 or rows[0].get('build_attempted_at') or rows[0].get('first_pass_recorded_at'):
        raise RuntimeError('Blind trial already attempted; choose a new company.')
    rows[0]['build_attempted_at'] = datetime.now(timezone.utc).isoformat()
    with NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent, delete=False) as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        temporary = handle.name
    os.replace(temporary, path)


def refuse_trial_revision(company):
    if (company.get('quality_trial') or {}).get('mode') == 'first_pass_unseen':
        raise RuntimeError('Blind quality experiments use a new company, not same-company revisions.')

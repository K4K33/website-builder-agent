"""Conservative Kaurivo prospect prefilter for official PRH records.

Only classifies whether business merits website research. Does not assert
website quality, economic health, activity, outreach permission or absence.
"""
from __future__ import annotations
import re
from hashlib import sha256

# Asset-holding and housing companies usually aren't website agency buyers.
EXCLUDED_INDUSTRY_PREFIXES = ("6820", "6810", "6420", "6430", "6499")
EXCLUDED_NAME = re.compile(
    r"(?:asunto[ -]?osake(?:yhtiö|yhtiö)|asunto[ -]?oy|\bas\.?\s*oy\b|"
    r"bostads(?:aktiebolag|\s*ab|\s*aktiebolag)|"
    r"kiinteistö(?:osake(?:yhtiö)?|[ -]+oy\b)|"
    r"keskinäinen\s+kiinteistö|fastighets(?:aktiebolag|\s*ab)|"
    r"\b(?:holding|investments?|sijoitusyhtiö|sijoitus\s*oy)\b)",
    re.IGNORECASE,
)
# Service-facing sectors: businesses that could genuinely benefit from clear
# customer acquisition, booking, quoting, portfolios or trust-building.
TARGET_INDUSTRY_PREFIXES = (
    "41", "42", "43", "45", "47", "49", "55", "56", "69", "71",
    "73", "74", "75", "77", "79", "80", "81", "82", "85", "86",
    "90", "93", "95", "96", "6831", "6832",
)
SECONDARY_INDUSTRY_PREFIXES = (
    "10", "11", "13", "14", "16", "18", "20", "22", "23", "25",
    "26", "27", "28", "29", "31", "32", "33", "46", "50", "52",
    "58", "59", "60", "62", "63", "70", "72",
)

def lead_score(name, industry):
    """Return None for excluded holding/property; score otherwise.

    Registry facts alone can't establish website quality or ability to pay.
    """
    name = str(name or "").strip()
    industry = str(industry or "").strip()
    if not name or EXCLUDED_NAME.search(name):
        return None
    if industry.startswith(EXCLUDED_INDUSTRY_PREFIXES):
        return None
    if industry.startswith(TARGET_INDUSTRY_PREFIXES):
        return 4
    if industry.startswith(SECONDARY_INDUSTRY_PREFIXES):
        return 2
    return 0

# Sales-first shortlisting: most prospects should have an existing site that
# Kaurivo can inspect and potentially improve. Missing PRH URL is NOT proof of
# no website. The reserve is for separately researched no-site opportunities.
EXISTING_SITE_SHARE = 0.70
MAX_PER_SECTOR = 8
TECHNICAL_HINT_WEIGHTS = {
    "viewport_missing": 8,
    "contact_link_missing": 7,
    "heading_missing": 5,
    "meta_description_missing": 4,
    "title_missing": 4,
}

def observed_technical_opportunity(company):
    """A 0..30 *research hint*, never a visual quality or sale score.

    Only an inspected public HTML page may provide technical evidence.
    Missing audits, redirects, uncertain identity and absent PRH URLs are
    unknown, not a negative website verdict. Finance and active operation
    always require independent verification.
    """
    audit=company.get("site_technical_audit") or {}
    if not isinstance(audit,dict) or audit.get("status")!="html_checked":
        return 0
    issues=audit.get("issues") or []
    if not isinstance(issues,list):
        issues=[]
    weights=sum(weight for issue,weight in TECHNICAL_HINT_WEIGHTS.items()
                if issue in issues)
    broken=audit.get("possible_broken_internal_links",0)
    if type(broken) is int:
        weights+=min(2,max(0,broken))*3
    return min(30,weights)


def sales_research_key(company, day=""):
    """Sort by observed improvement hints, then market/site access.

    A provisional *investigation order* is not evidence of solvency, active
    operations, conversion likelihood or poor visual design.
    """
    observed=observed_technical_opportunity(company)
    sector=lead_score(company.get("name"),company.get("industry_code_hint")) or 0
    known=int(bool(company.get("website_listed_url")))
    audit=company.get("site_technical_audit") or {}
    inspected=int(isinstance(audit,dict) and audit.get("status")=="html_checked")
    identity=str(company.get("business_id") or company.get("identity") or "")
    tie=int.from_bytes(sha256((day+"|"+identity).encode()).digest()[:8],"big")
    return (-observed,-sector,-known,-inspected,tie)


def choose_shortlist(candidates, size=50, day="", weights=None):
    """Sales-first, diverse and evidence-conservative PRH shortlist.

    Aim for 70% leads WITH a registered website and 30% for researching
    possible no-site businesses. Fall back safely when one source category
    is absent; don't fabricate a URL, financial health, or site assessment.
    """
    weights = weights if isinstance(weights, dict) else {}
    eligible=[c for c in candidates
              if (lead_score(c.get("name"),c.get("industry_code_hint")) or 0)>=2]
    def key(c):
        h=int.from_bytes(sha256((day+"|"+c["business_id"]).encode()).digest()[:8],"big")
        industry=str(c.get("industry_code_hint") or "")[:2]
        item=weights.get(industry,{})
        boost=item.get("boost",0) if isinstance(item,dict) else 0
        count=item.get("count",0) if isinstance(item,dict) else 0
        if type(count) is not int or count<8 or type(boost) is not int:
            boost=0
        boost=max(-4,min(4,boost))
        return (-(lead_score(c["name"],c.get("industry_code_hint"))*10+boost),
                -int(bool(c.get("website_listed_url"))),h)

    eligible.sort(key=key)
    with_site=[c for c in eligible if c.get("website_listed_url")]
    without_site=[c for c in eligible if not c.get("website_listed_url")]
    sector_counts={}
    selected=[]
    def take(pool, count):
        picked=[]
        deferred=[]
        for candidate in pool:
            sector=str(candidate.get("industry_code_hint") or "")[:2]
            if (len(picked)<count and
                sector_counts.get(sector,0)<MAX_PER_SECTOR):
                picked.append(candidate)
                sector_counts[sector]=sector_counts.get(sector,0)+1
            else:
                deferred.append(candidate)
        if len(picked)<count:
            # A single-sector market must not produce a needlessly empty list.
            needed=count-len(picked)
            picked.extend(deferred[:needed])
            deferred=deferred[needed:]
        return picked,deferred

    site_quota=round(min(size,len(eligible))*EXISTING_SITE_SHARE)
    known,remainder_known=take(with_site,min(site_quota,len(with_site)))
    unknown,remainder_unknown=take(without_site,min(size-len(known),len(without_site)))
    selected=known+unknown
    if len(selected)<size:
        remainder=remainder_known+remainder_unknown
        remainder.sort(key=key)
        selected.extend(remainder[:size-len(selected)])
    # Preserve the most promising known-site leads toward the front: the next
    # free bounded technical audit examines only the first 12 listed sites.
    selected.sort(key=key)
    return selected[:size]

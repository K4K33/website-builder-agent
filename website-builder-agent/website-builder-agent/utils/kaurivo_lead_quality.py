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

def choose_shortlist(candidates, size=50, day=""):
    """Select high-relevance businesses from all website categories.

    When registry URL data is absent, never fake known-website businesses.
    """
    eligible = [c for c in candidates
                if (lead_score(c.get("name"), c.get("industry_code_hint")) or 0)>=2]
    def key(c):
        # Website listing is a modest plus, but relevance is more important.
        h = int.from_bytes(sha256((day+"|"+c["business_id"]).encode()).digest()[:8],"big")
        return (-lead_score(c["name"], c.get("industry_code_hint")),
                -int(bool(c.get("website_listed_url"))), h)
    eligible.sort(key=key)
    # Interleave known and unknown URL where source metadata allows it.
    known=[c for c in eligible if c.get("website_listed_url")]
    unknown=[c for c in eligible if not c.get("website_listed_url")]
    selected=[]
    sector_counts={}
    deferred=[]
    # First pass: diversify major business groups when alternatives exist.
    # The source may have only one sector; a second pass fills available
    # capacity without inventing companies or failing on small samples.
    for i in range(min(len(eligible),size*10)):
        choices=(known,unknown) if i%2 else (unknown,known)
        group=next((pool for pool in choices if pool),None)
        if group is None: break
        company=group.pop(0)
        sector=str(company.get("industry_code_hint") or "")[:2]
        if sector_counts.get(sector,0)>=8:
            deferred.append(company)
            continue
        selected.append(company)
        sector_counts[sector]=sector_counts.get(sector,0)+1
        if len(selected)>=size: break
    if len(selected)<size:
        # Preserve balanced selection when the top list has a narrow market.
        remaining=deferred+known+unknown
        selected.extend(remaining[:size-len(selected)])
    return selected

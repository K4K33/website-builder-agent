"""One client, three genuinely different creative strategies, one evidenced choice.

No sector layout catalogue, company names, paid provider, or subjective score.
A superficial palette/font change does not constitute another direction.
"""
from __future__ import annotations
import re
from difflib import SequenceMatcher

FIELDS = (
    "id", "concept", "business_reason", "source_anchor",
    "first_view", "information_architecture", "navigation",
    "image_strategy", "typography", "brand_continuity",
    "non_goals", "mobile_behavior",
)
CREATIVE_AXES = ("first_view", "information_architecture", "navigation", "image_strategy")

def _normalized(value: str) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().casefold())

def validate_creative_directions(research: dict) -> dict:
    """Hard-gate prior to model Build: three distinctive, sourced proposals."""
    raw=research.get("creative_directions")
    if not isinstance(raw, list) or len(raw)!=3:
        raise RuntimeError("Creative preflight: provide exactly three company-specific directions.")
    ids=set()
    for index, direction in enumerate(raw,1):
        if not isinstance(direction,dict):
            raise RuntimeError(f"Creative direction #{index} is not structured.")
        missing=[name for name in FIELDS if len(str(direction.get(name) or "").strip())<12
                 and name!="id"]
        if not str(direction.get("id") or "").strip():
            missing.append("id")
        if missing:
            raise RuntimeError(f"Creative direction #{index} incomplete: {', '.join(missing)}")
        identifier=_normalized(direction["id"])
        if identifier in ids:
            raise RuntimeError("Creative directions have duplicated identifiers.")
        ids.add(identifier)
        if not any(word in _normalized(direction.get("business_reason")) for word in
                   ("yrity", "customer", "client", "asiakka", "palvel", "service",
                    "tuot", "product", "toimial", "business", "käyttäj")):
            raise RuntimeError("Creative direction must explain a customer/business reason, not a style trend.")
    # Similar descriptions across the important structural axes are rejected.
    # Three palette/font variants are not three creative proposals.
    for i in range(3):
        for j in range(i+1,3):
            left,right=raw[i],raw[j]
            different=sum(
                SequenceMatcher(None,_normalized(left[key]),_normalized(right[key]),autojunk=False).ratio()<.70
                for key in CREATIVE_AXES
            )
            if different<3:
                raise RuntimeError(
                    "Creative directions differ mostly by surface details. "
                    "Change first-view composition, navigation and real information architecture."
                )
    choice=research.get("creative_selection") or {}
    selected=_normalized(choice.get("selected_id"))
    reason=str(choice.get("business_reason") or "").strip()
    rejected=choice.get("rejected_ids")
    if selected not in ids or len(reason)<35 or not isinstance(rejected,list) or set(map(_normalized,rejected))!=ids-{selected}:
        raise RuntimeError("Creative selection needs a justified choice and explicit rejection of both alternatives.")
    selection=[d for d in raw if _normalized(d["id"])==selected][0]
    if _normalized(reason)==_normalized(selection.get("business_reason")):
        raise RuntimeError("Creative selection requires comparative reasoning, not copied promotional text.")
    return {"selected":selection,"alternatives":raw,"choice":choice,
            "note":"Three paths and an evidenced choice; not proof of an independent visual score."}

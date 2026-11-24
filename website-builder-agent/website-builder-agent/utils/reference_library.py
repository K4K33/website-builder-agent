"""The owner's reference library: examples become standing training material.

Every site or video the owner sends is studied once, written into
data/design_references.json as techniques (observed -> recipe -> needs ->
fits) and applied to every future build without the owner repeating it.
Owner feedback ("no boxes", "never two logos in one view") lives there too as
owner_rules, which every build prompt carries.
"""
from __future__ import annotations

import json
from pathlib import Path

PATH = Path(__file__).resolve().parents[1] / "data" / "design_references.json"


def load(path: Path = PATH) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def select(trade: str = "", *, limit: int = 12, path: Path = PATH) -> list[dict]:
    """Techniques that fit this trade first, then the generally useful ones."""
    words = (trade or "").lower()
    scored = []
    for ref in load(path)["references"]:
        fits = [f.lower() for f in ref.get("fits", [])]
        score = 2 if any(f in words for f in fits if f != "any") else (1 if "any" in fits else 0)
        for tech in ref["techniques"]:
            scored.append((score, ref["id"], tech))
    scored.sort(key=lambda row: -row[0])
    return [{"reference": rid, **tech} for _, rid, tech in scored[:limit]]


def brief(trade: str = "", *, path: Path = PATH) -> str:
    """Prompt block: the owner's rules plus the techniques that suit this business."""
    data = load(path)
    lines = ["OWNER REFERENCE LIBRARY (standing training material; apply without being asked):",
             "Owner rules:"] + [f"- {rule}" for rule in data["owner_rules"]]
    lines.append("Techniques that suit this business (pick those its real material supports):")
    for t in select(trade, path=path):
        lines.append(f"- {t['name']} [{t['reference']}]: {t['observed']}. Build: {t['recipe']}. Needs: {t['needs']}.")
    return "\n".join(lines)


def add_reference(entry: dict, *, path: Path = PATH) -> None:
    """Append a studied reference (validated) so every later build uses it."""
    required = {"id", "source", "techniques", "fits"}
    if not required <= set(entry):
        raise ValueError(f"reference needs {sorted(required)}")
    for tech in entry["techniques"]:
        if not {"name", "observed", "recipe", "needs"} <= set(tech):
            raise ValueError("each technique needs name, observed, recipe and needs")
    data = load(path)
    if any(r["id"] == entry["id"] for r in data["references"]):
        raise ValueError(f"reference {entry['id']} already exists")
    data["references"].append(entry)
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")

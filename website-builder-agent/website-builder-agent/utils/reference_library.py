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


# How much spectacle a business actually needs (owner: "kaikki ei välttämättä halua
# kaikista extra sivustoa"). Assessed before any technique is chosen.
LEVELS = {
    1: ("CALM", "Trust and clarity first: cinematic real photo or quiet typographic hero, gentle reveals, "
        "no 3D, no marquees, no cursor effects. Contact, prices and services are found in seconds."),
    2: ("CRAFTED", "One signature moment that shows the real work (before/after wipe, transition as scroll, "
        "photo sequence), page-wide gentle motion, otherwise calm and practical."),
    3: ("EXPRESSIVE", "The site itself is the showcase: full-bleed scenes, manifesto type, horizontal tracks, "
        "depth galleries, cursor-reactive subject. Still one idea per section and fast to the contact."),
}
_CALM = ("tilitoimisto", "kirjanpito", "accounting", "lakitoimisto", "asianajo", "law", "vakuutus", "insurance",
         "terveys", "lääkäri", "hammas", "clinic", "health", "hoiva", "care", "kiinteistöhuolto", "isännöinti",
         "siivous", "cleaning", "pankki", "bank", "seurakunta", "kunta", "municipal")
_EXPRESSIVE = ("studio", "agency", "toimisto design", "design", "creative", "luova", "muoti", "fashion", "ravintola",
               "restaurant", "hotelli", "hotel", "kampaamo", "salon", "tatuointi", "tattoo", "valokuva", "photo",
               "musiikki", "music", "event", "tapahtuma", "urheilija", "athlete", "kaurivo", "personal brand")


def intensity(trade: str = "", *, own_media: int = 0, wants: str = "") -> int:
    """1 calm, 2 crafted, 3 expressive. An explicit wish ('rauhallinen'/'näyttävä') wins; real
    material is required for 3, because spectacle without real content looks cheap."""
    words, wish = (trade or "").lower(), (wants or "").lower()
    if any(w in wish for w in ("rauhallinen", "yksinkertainen", "simple", "calm", "asiallinen")):
        return 1
    if any(w in wish for w in ("näyttävä", "wow", "rohkea", "bold", "expressive")):
        return 3
    if any(w in words for w in _CALM):
        return 1
    if any(w in words for w in _EXPRESSIVE):
        return 3 if own_media >= 4 or "kaurivo" in words or "studio" in words else 2
    return 2


def brief(trade: str = "", *, path: Path = PATH, own_media: int = 0, wants: str = "") -> str:
    """Prompt block: the needs level, the owner's rules and the techniques that suit this business."""
    data = load(path)
    level = intensity(trade, own_media=own_media, wants=wants)
    name, rule = LEVELS[level]
    lines = [f"NEEDS ASSESSMENT: level {level} {name}. {rule}",
             "Assess the business before choosing techniques: who its customers are, what they must find, how "
             "conservative its field is and what real material exists. Do not add spectacle the business does not "
             "need; a calm site done perfectly beats an extravagant one done for its own sake. State the level and "
             "the reason in the design notes.",
             "OWNER REFERENCE LIBRARY (standing training material; apply without being asked):",
             "Owner rules:"] + [f"- {rule}" for rule in data["owner_rules"]]
    lines.append("Techniques that suit this business (pick those its real material supports"
                 + (", and at this level only calm ones: cinematic photo, gentle reveals, clear type):" if level == 1 else "):"))
    for t in select(trade, path=path, limit=6 if level == 1 else 12):
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

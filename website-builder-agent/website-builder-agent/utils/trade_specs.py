"""What a finished job must contain, and what visible work each stage adds.

A build animation is only convincing when (1) every stage adds real physical
work (pipes, boards, tiles, fixtures appear), not just a new wall colour, and
(2) the finished result is complete and carefully done the way a professional
of that trade would hand it over. These specs drive the image prompts AND the
quality gate, for every trade the builder animates.
"""
from __future__ import annotations

SPECS = {
    "kylpyhuone": {
        # Everything a finished Finnish bathroom renovation is handed over with.
        "finished_must": [
            "a wall-mounted washbasin with a faucet",
            "a mirror (or mirror cabinet) above the washbasin with a light",
            "a wall-hung toilet with its flush plate",
            "a walk-in shower with a frameless glass wall, rain shower head and thermostatic mixer",
            "a floor drain with a stainless grate, the floor sloping towards it",
            "walls tiled from floor to ceiling and a tiled floor, straight even grout lines",
            "a heated towel rail",
            "ceiling lighting",
        ],
        # (stage label, the visible physical work this stage adds)
        "stage_work": {
            "Lähtötilanne": "old worn fixtures and dated tiles are clearly visible",
            "Pohja": "everything removed: bare concrete, new water pipes and drain stubs, electrical boxes visible",
            "Vedeneristys": "membrane covers walls and floor, corner tapes and pipe collars visible",
            "Laatoitus": "tiles laid on all walls and the floor with grout, pipe stubs coming through the tiles",
            "Valmis": "every finished element is installed and the room is clean and styled",
        },
    },
    "maalaus": {
        "finished_must": [
            "an evenly painted wall with crisp straight edges at the ceiling and corners",
            "clean skirting boards and window frames without paint marks",
            "the floor clean, protection removed, the room furnished again",
        ],
        "stage_work": {
            "Pohjatyöt": "cracks and holes filled and sanded, edges masked, floor protected",
            "Pohjamaali": "the whole wall primed evenly",
            "Maalaus": "the colour coat applied with a roller in even vertical lanes",
            "Valmis": "masking removed, furniture back, finished clean room",
        },
    },
}


def finished_text(trade: str) -> str:
    spec = SPECS.get(trade)
    return "; ".join(spec["finished_must"]) if spec else ""


def review_checklist(trade: str, labels: list[str]) -> str:
    """Extra lines for the strict visual review."""
    spec = SPECS.get(trade)
    if not spec:
        return ""
    lines = ["The FINISHED (last) image must clearly show ALL of: " + "; ".join(spec["finished_must"]) + ".",
             "Every stage must add VISIBLE physical work compared with the previous one, not only a new colour:"]
    for label in labels:
        if label in spec["stage_work"]:
            lines.append(f"- {label}: {spec['stage_work'][label]}")
    return "\n".join(lines)

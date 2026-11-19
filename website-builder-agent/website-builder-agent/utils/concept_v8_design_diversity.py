"""Independent structural diversity check for V8's three rendered design routes.

A slight grid ratio or different colour is NOT an independent creative
concept. This is a heuristic; screenshot critics still make the actual
aesthetic judgment after structural preflight, not this module.
"""
from __future__ import annotations

from difflib import SequenceMatcher
import re

from bs4 import BeautifulSoup

_STYLE_GEOMETRY = re.compile(
    r"(?:grid-template-columns|grid-template-areas|display|flex-direction|"
    r"justify-content|align-items|position|text-align)\s*:\s*([^;{}]+)",
    re.IGNORECASE,
)


def _route_structure(html: str) -> list[str]:
    soup = BeautifulSoup(html, "html.parser")
    main = soup.find("main")
    if main is None:
        return []
    items = []
    for section in main.find_all(["section", "article"], recursive=False)[:6]:
        children = section.find_all(recursive=False)
        # Only structural, not arbitrary utility class names, colors or copy.
        shape = []
        for child in children[:8]:
            tags = [tag.name for tag in child.find_all(
                ["h1", "h2", "h3", "p", "picture", "img", "video", "figure",
                 "form", "ul", "ol", "blockquote", "svg"], limit=15)]
            shape.append(child.name + ":" + ",".join(tags[:8]))
        media = section.find_all(["img", "picture", "video", "figure", "svg"])
        items.append(
            section.name + "|" + ";".join(shape)
            + "|media:" + ",".join(tag.name for tag in media[:6])
            + "|cols:" + str(len(children))
        )
    css = " ".join(style.get_text(" ", strip=True) for style in soup.find_all("style"))
    css += " " + " ".join(str(el.get("style") or "") for el in soup.select("[style]")[:40])
    geometry = []
    for match in _STYLE_GEOMETRY.finditer(css):
        name = str(match.group(0)).split(":", 1)[0].strip().lower()
        raw = match.group(1).strip().lower()
        if name == "grid-template-columns":
            # Normalize grid fraction values: 1fr 1fr and 1.3fr .7fr are
            # the SAME visual composition strategy, not separate concepts.
            raw = "grid" + str(len(re.findall(r"\d+(?:\.\d+)?fr", raw)))
        elif name == "grid-template-areas":
            raw = "areas"
        geometry.append(name + ":" + raw)
    items.append("geometry:" + ";".join(sorted(set(geometry))[:25]))
    return items


def near_duplicate_concepts(concepts: dict[str, dict[str, str]]) -> list[dict]:
    """Return deterministic pairwise near-duplicates across matching routes."""
    ids = list(concepts)
    problems = []
    for index, first in enumerate(ids):
        for second in ids[index + 1:]:
            common = sorted(set(concepts[first]) & set(concepts[second]))
            if not common:
                continue
            similarities = []
            for route in common:
                left = _route_structure(concepts[first][route])
                right = _route_structure(concepts[second][route])
                if not left or not right:
                    continue
                # Missing photography, route structure and layout fingerprints
                # are independently important; a text change has no effect.
                fraction = SequenceMatcher(None, left, right, autojunk=False).ratio()
                similarities.append(fraction)
            if similarities and min(similarities) >= .92:
                problems.append({
                    "first": first, "second": second,
                    "routes": common,
                    "similarity": round(sum(similarities) / len(similarities), 3),
                    "repair": (
                        "Change the first-fold visual composition and at least "
                        "one substantive subpage structure, not merely "
                        "colors, copy or a CSS grid ratio."
                    ),
                })
    return problems

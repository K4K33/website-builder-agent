"""Structural originality gate for unrelated Kaurivo client sites. Offline only."""
from __future__ import annotations
from difflib import SequenceMatcher
from pathlib import Path
from bs4 import BeautifulSoup

SIGNIFICANT_TAGS = {"section", "article", "figure", "div", "aside"}
THEME_CLASSES = {"auto", "food", "build", "theme-auto", "theme-food", "theme-build"}

def _layout(html: str) -> tuple[str, ...]:
    main = BeautifulSoup(html, "html.parser").find("main")
    if main is None:
        return ()
    tokens = []
    for tag in main.find_all(True):
        if tag.name not in SIGNIFICANT_TAGS:
            continue
        classes = sorted(c.lower() for c in tag.get("class", [])
                         if c.lower() not in THEME_CLASSES)
        if classes:
            tokens.append(tag.name + ":" + ".".join(classes))
    return tuple(tokens)

def _styles(html: str) -> set[str]:
    soup = BeautifulSoup(html, "html.parser")
    return {str(link["href"]).split("?", 1)[0]
            for link in soup.find_all("link", href=True)
            if "stylesheet" in link.get("rel", [])
            and not str(link["href"]).startswith(("http:", "https:"))}

def compare_site_designs(first: str, second: str) -> dict[str, object]:
    """Flags layout clones, including those with superficial color changes.

    This is a necessary screening check, not a substitute for human review.
    Shared small utilities and accessible interaction code remain allowed.
    """
    left, right = _layout(first), _layout(second)
    if min(len(left), len(right)) < 12:
        return {"too_similar": False, "layout_similarity": 0.0,
                "same_core_stylesheet": False}
    ratio = SequenceMatcher(a=left, b=right, autojunk=False).ratio()
    same_sheet = bool(_styles(first) & _styles(second))
    # Stronger threshold if distinct stylesheets; do not accept a clone
    # merely because its creator renamed or changed the stylesheet.
    return {"too_similar": (same_sheet and ratio >= 0.62) or ratio >= 0.94,
            "layout_similarity": round(ratio, 3),
            "same_core_stylesheet": same_sheet}

def assert_unique_against_output(html: str, slug: str,
                                 output_dir: str | Path) -> None:
    """Raise before saving another company's repeated layout."""
    folder = Path(output_dir)
    if not folder.is_dir():
        return
    for other in folder.glob("*/index.html"):
        if other.parent.name == slug:
            continue
        result = compare_site_designs(html, other.read_text(encoding="utf-8"))
        if result["too_similar"]:
            raise RuntimeError(
                f"Reused customer website template from {other.parent.name}: "
                f"layout similarity {result['layout_similarity']}. "
                "Create an original information architecture, composition "
                "and visual hierarchy; changing only colors is not enough."
            )

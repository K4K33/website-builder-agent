"""Bounded local recovery of measured concept text contrast, never QA approval.

A real Chromium report supplies a DOM path and an observed text excerpt. Both
must agree with the current HTML before any style is altered. Source facts,
brand imagery, routes and document structure are never rewritten here.
"""
import json
import re
from bs4 import BeautifulSoup

_SELECTOR = re.compile(r"^body(?: > [a-z][a-z0-9-]*:nth-of-type\([1-9]\d*\))*$")
_OBSERVATIONS = (
    ("text/background contrast NOT VERIFIABLE", "review the real rendered image: "),
    ("measurable WCAG AA text contrast failures", "contrast failures: "),
)
_MAX_TARGETS = 12


def _observations(issues):
    for issue in issues[:8]:
        if not isinstance(issue, str):
            continue
        for kind, prefix in _OBSERVATIONS:
            if kind not in issue or prefix not in issue:
                continue
            try:
                # An intact JSON array, not a chopped string of browser text,
                # is mandatory. Never interpret browser text as CSS/commands.
                decoded = json.loads(issue.split(prefix, 1)[1].strip())
            except (json.JSONDecodeError, ValueError):
                continue
            if isinstance(decoded, list):
                for item in decoded[:12]:
                    if isinstance(item, dict):
                        yield kind, item
            break


def _same_copy(node, expected):
    if not isinstance(expected, str) or not expected.strip():
        return False
    # Match textContent by joining the original text nodes before collapsing
    # whitespace. Leading/trailing spaces between inline nodes are meaningful.
    actual = " ".join(node.get_text().split())
    evidence = " ".join(expected.split())
    return actual.startswith(evidence)


def repair_browser_contrast(html, issues, *, max_targets=_MAX_TARGETS):
    """Return corrected HTML or original unchanged when evidence is inadequate.

    Not a pass decision: the caller MUST validate source content/media and
    re-render with the real browser before accepting the corrected concepts.
    """
    if not isinstance(html, str) or not issues:
        return html
    soup = BeautifulSoup(html, "html.parser")
    seen = set()
    changed = False
    for kind, finding in _observations(issues):
        selector = finding.get("selector")
        if (not isinstance(selector, str) or len(selector) > 400
                or not _SELECTOR.fullmatch(selector) or selector in seen):
            continue
        if len(seen) >= max_targets:
            break
        try:
            element = soup.select_one(selector)
        except Exception:
            continue
        if (element is None or element.name.upper() != finding.get("tag")
                or not _same_copy(element, finding.get("text"))):
            continue
        style = str(element.get("style", "")).rstrip().rstrip(";")
        if kind == _OBSERVATIONS[1][0]:
            # An exact browser measurement already provided a verified
            # black/white text correction on a fully opaque background.
            color = finding.get("suggestedTextColor")
            if color not in ("#000000", "#ffffff"):
                continue
            correction = "color:" + color + " !important"
        else:
            # For genuinely unprovable photo/gradient text, create a small
            # opaque readable surface on this text element ONLY. Keep the
            # original hero image, animation, page structure and all copy.
            # Independent visual QA can still reject the appearance.
            correction = ("color:#ffffff !important;"
                          "background-color:#101c2b !important;"
                          "background-image:none !important;"
                          "opacity:1 !important;"
                          "padding:.14em .28em;"
                          "border-radius:.2em;"
                          "box-decoration-break:clone;"
                          "-webkit-box-decoration-break:clone")
        seen.add(selector)
        if style == correction or style.endswith(";" + correction):
            continue
        element["style"] = ";".join(part for part in (style, correction) if part)
        changed = True
    return str(soup) if changed else html

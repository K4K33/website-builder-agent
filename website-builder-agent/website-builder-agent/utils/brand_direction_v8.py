"""V8 art-direction guard: use the client's real identity, not a benchmark's.

This is a conservative, code-based preflight BEFORE image-based criticism.
It does not infer design quality, copyright status or human approval from
similar CSS, nor does it purport to recognize the colours of famous sites.
"""
from __future__ import annotations

from colorsys import rgb_to_hsv
from pathlib import Path
import re

from bs4 import BeautifulSoup

_COLOR = re.compile(r"(?<![\w-])#(?:[0-9a-fA-F]{6}|[0-9a-fA-F]{3})(?![\w-])")
_TOKEN = re.compile(
    r"(?:--[\w-]*(?:brand|primary|accent|highlight|lime|leaf|coral|neon)[\w-]*)\s*:\s*"
    r"(#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3})(?![\w-])", re.I
)


def _hex(value: str) -> str | None:
    value = str(value or "").strip().lower()
    if not re.fullmatch(r"#[0-9a-f]{3}(?:[0-9a-f]{3})?", value):
        return None
    if len(value) == 4:
        value = "#" + "".join(char * 2 for char in value[1:])
    return value


def _vivid(value: str) -> bool:
    rgb = _hex(value)
    if not rgb:
        return False
    channels = tuple(int(rgb[pos:pos + 2], 16) / 255 for pos in (1, 3, 5))
    _, saturation, brightness = rgb_to_hsv(*channels)
    return saturation >= .36 and brightness >= .67


def derive_identity_boundaries(research: dict) -> dict:
    """Source-observed tokens only; industry and global references NEVER qualify."""
    research = research if isinstance(research, dict) else {}
    pages = (research.get("source_inventory") or {}).get("pages") or []
    colors, logos, observed = {}, set(), []
    for page in pages:
        if not isinstance(page, dict):
            continue
        identity = page.get("source_identity") or {}
        if not isinstance(identity, dict):
            continue
        url = str(page.get("url") or "")
        if not url.startswith("https://"):
            continue
        color = _hex(identity.get("theme_color"))
        if color:
            colors.setdefault(color, []).append(url)
        for candidate in identity.get("original_logo_candidates") or []:
            if isinstance(candidate, str) and candidate:
                logos.add(candidate)
        if color or identity.get("original_logo_candidates"):
            observed.append(url)
    return {
        "protocol": "company-identity-evidence-v8",
        "company": str((research.get("company_facts") or {}).get("name") or ""),
        "verified_original_colors": [
            {"hex": color, "source_urls": urls} for color, urls in sorted(colors.items())
        ],
        "verified_original_logos": sorted(logos),
        "verified_source_pages": sorted(set(observed)),
        "reference_color_copying_permitted": False,
        "new_colors_status": "provisional_until_owner_checks",
        "no_site_brand_still_may_exist": research.get("research_mode") == "verified_no_website",
        "contract_is_not_a_licence": True,
    }


def _read_styles(html: str, site_root: Path | None = None, route: str = "") -> str:
    soup = BeautifulSoup(html, "html.parser")
    pieces = [el.get_text(" ", strip=True) for el in soup.find_all("style")]
    pieces += [str(el.get("style") or "") for el in soup.select("[style]")]
    if site_root is not None:
        # All linked files stay under the actual on-disk generated site.
        root = Path(site_root).resolve()
        page = (root / route).resolve()
        if page.is_relative_to(root):
            for link in soup.select('link[rel~="stylesheet"][href]'):
                href = str(link.get("href") or "")
                if not href or href.startswith(("/", "http:", "https:", "//")):
                    continue
                path = (page.parent / href.split("?", 1)[0].split("#", 1)[0]).resolve()
                if path.is_relative_to(root) and path.is_file() and path.stat().st_size <= 400_000:
                    pieces.append(path.read_text(encoding="utf-8"))
    return "\n".join(pieces)[:1_000_000]


def audit_art_direction(
    pages: dict[str, str], research: dict | None,
    *, site_root: Path | None = None,
) -> dict:
    """Find evidenced, *specific* missing brand discipline; not a numeric score.

    For the new V8 protocol, a vivid named-brand accent unsupported by the
    source becomes a concrete repair target. Ordinary colors, accessible UI
    accents, a verified original palette and a clearly labeled no-site study
    are NOT automatically rejected.
    """
    research = research if isinstance(research, dict) else {}
    identity = derive_identity_boundaries(research)
    known = {row["hex"] for row in identity["verified_original_colors"]}
    strict = research.get("v8_visual_protocol") == "v8"
    no_site = research.get("research_mode") == "verified_no_website"
    blockers, review = [], []
    palette_observations = {}
    evidence = research.get("primary_offering_evidence") or {}
    label = str(evidence.get("label") or "").strip() if isinstance(evidence, dict) else ""
    for route, html in (pages or {}).items():
        if not isinstance(html, str):
            blockers.append({"route": route, "code": "invalid_page", "repair": "Render real HTML."})
            continue
        css = _read_styles(html, site_root, route)
        # CSS models may hide an accent in an arbitrary --custom-token
        # or emit it repeatedly as a literal, bypassing --brand/--accent.
        # Treat dominant :root colours and repeated vivid literal paints as
        # part of the proposed visual identity, not source-verified facts.
        source_tokens = {
            normalized for match in _TOKEN.finditer(css)
            if (normalized := _hex(match.group(1)))
        }
        for root_match in re.finditer(r":root\s*\{([^{}]{0,5000})\}", css, re.I):
            for color in _COLOR.findall(root_match.group(1)):
                normalized = _hex(color)
                if normalized:
                    source_tokens.add(normalized)
        explicit_paints = re.findall(
            r"(?:background(?:-color)?|border-color|color)\s*:\s*"
            r"(#[0-9a-fA-F]{6}|#[0-9a-fA-F]{3})(?![\w-])", css, re.I
        )
        for color in set(explicit_paints):
            if explicit_paints.count(color) >= 2:
                normalized = _hex(color)
                if normalized and _vivid(normalized):
                    source_tokens.add(normalized)
        uncovered = sorted(c for c in source_tokens if _vivid(c) and c not in known)
        palette_observations[route] = {
            "named_chromatic_tokens": sorted(source_tokens),
            "source_palette": sorted(known),
            "unproven_vivid_tokens": uncovered,
        }
        if uncovered:
            finding = {
                "route": route,
                "code": "unproven_brand_accent",
                "evidence": uncovered[:6],
                "repair": (
                    "Do not select a vivid brand accent from international UX "
                    "benchmarks. Use the original company's observed palette, "
                    "or a restrained provisional theme clearly pending owner "
                    "visual approval; rebuild all matching brand tokens."
                )
            }
            if strict and not no_site:
                blockers.append(finding)
            else:
                review.append(finding)
        # A huge technical road/gear schematic used only for decoration
        # cannot replace real source business imagery or service content.
        # Small ordinary SVG icons and genuinely original company media are
        # not rejected by this narrow evidence-driven rule.
        if strict and route == "index.html":
            soup = BeautifulSoup(html, "html.parser")
            for svg in soup.select("main svg"):
                box = re.findall(r"-?\d+(?:\.\d+)?", str(svg.get("viewbox") or ""))
                if len(box) != 4:
                    continue
                try:
                    oversized = float(box[2]) >= 250 and float(box[3]) >= 250
                except ValueError:
                    continue
                nearby = " ".join([
                    str(svg.get("class") or ""),
                    str(svg.parent.get("class") if svg.parent else ""),
                    str(svg.get("id") or ""),
                    " ".join(str(tag.get("class") or "")
                             for tag in svg.find_all(["path", "g", "pattern"])[:14]),
                ]).casefold()
                if oversized and re.search(
                    r"terrain|road-outline|road-center|cargo-hatch|blueprint|"
                    r"gear-outline|technical-schematic|fake-map", nearby):
                    blockers.append({
                        "route": route,
                        "code": "generic_technical_hero_illustration",
                        "repair": (
                            "Remove the unsupported decorative road/gear or "
                            "pseudo-map SVG. Use the company's evidenced images "
                            "and an actually useful, source-led first fold."
                        ),
                    })
                    break
        if strict and label and route == "index.html":
            soup = BeautifulSoup(html, "html.parser")
            main = soup.find("main")
            first = (main.find("section") if main else None) or main
            first_text = " ".join(first.get_text(" ", strip=True).casefold().split()) if first else ""
            # A supporting tagline in the actual hero is sufficient; don't
            # force every customer to put a generic keyword in its h1.
            if label.casefold() not in first_text:
                blockers.append({
                    "route": route,
                    "code": "verified_service_not_visible_in_hero",
                    "evidence": label[:100],
                    "repair": "Show the exact source-verified core service in the first real main section.",
                })
    return {
        "protocol": "company-art-direction-gate-v8",
        "pass": not blockers,
        "blocking": blockers,
        "review_required": review,
        "palette_evidence": palette_observations,
        "identity": identity,
        "does_not_certify_visual_premium_quality": True,
    }

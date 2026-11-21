"""What award-winning small-business sites actually do, as rules and code.

Measured 20.11.2026 in a real browser (computed styles, libraries, scroll
captures) on Awwwards winners close to Kaurivo's clients; details are in
docs/KAURIVO_AWARD_STUDY.md. Two outputs:

- AWARD_BRIEF: concrete rules appended to the concept and builder prompts.
- derive_photo_palette(): colour theory as code. The winners take their
  palette from their own product or place photography (Delta: one coffee
  brown over most of the page; Agrumea: cream, orange and burgundy from the
  jars), tint their text instead of using black or white, and keep one
  saturated accent for action. This derives exactly that from the company's
  own photos, with WCAG contrast checked, so a free model never has to invent
  colours.
"""
from __future__ import annotations

import colorsys
from pathlib import Path

AWARD_BRIEF = """
AWARD-LEVEL DESIGN RULES (measured on Awwwards-winning small-business sites):
1. One idea per page. The hero is one big claim plus one cinematic subject
   (the company's own video, a cut-out product, a real project photo). Never a
   generic stock-like split with a bullet list.
2. Palette from the company's own photographs: one dominant colour covers most
   of the page (60-80 %), a second surface tone, and one saturated accent used
   only for the primary action and small highlights. Text is tinted from the
   dominant hue (for example deep brown on cream, peach on espresso), never
   pure #000 on pure #fff. Use pre_build_brief q3 photo_palette when present.
   Vivid colours may come ONLY from verified original brand colours or from
   that photo_palette; never invent or borrow an accent from a reference.
3. Typography: at most two families. Display is either a characterful serif
   at a light or medium weight (300-500) or a tight grotesque at 600-700, set
   large (clamp up to 7-9vw), line-height 0.9-1.05 and negative tracking
   (-0.02 to -0.04em). Body 16-23 px, line-height 1.4-1.6. Small labels may be
   uppercase with +0.04-0.08em tracking; use them sparingly.
4. Rhythm: alternate scale. A full-bleed image section, then a quiet text
   section with generous space (12-20 vh padding), then a dense detail
   section. No row of identical cards with icons; real photos carry sections.
5. Motion is about content: an image that grows from inset to full bleed on
   scroll, a product that turns, a sequence of real process steps, a text
   line revealed by a mask. One orchestrated entrance, not a fade-up on every
   block. Every motion has a reduced-motion still.
6. Proof inside the hero: a small real detail card over the image (a verified
   service area, a project fact, opening hours) instead of a third paragraph.
7. Navigation stays small and quiet (13-15 px), with one clear action button.
""".strip()


def _luminance(rgb) -> float:
    def channel(c):
        c = c / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (channel(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b) -> float:
    la, lb = sorted((_luminance(a), _luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def _hex(rgb) -> str:
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(c))) for c in rgb)


def _hls(rgb):
    return colorsys.rgb_to_hls(*(c / 255 for c in rgb))


def _from_hls(h, l, s):
    return tuple(c * 255 for c in colorsys.hls_to_rgb(h, max(0, min(1, l)), max(0, min(1, s))))


def _clusters(paths: list[Path], weights: list | None = None, colours: int = 8):
    """Colour clusters with their share, weighted towards the subject.

    ``weights`` are optional grey maps (white = subject, e.g. a depth map with
    near = white). Without them the centre and lower part are sampled, since
    the top band is usually sky or ceiling.
    """
    import numpy as np
    from PIL import Image
    counts: dict = {}
    for index, path in enumerate(paths):
        with Image.open(path) as image:
            rgb_image = image.convert("RGB")
            w, h = rgb_image.size
            weight = None
            if weights and index < len(weights) and weights[index] and Path(weights[index]).is_file():
                with Image.open(weights[index]) as grey:
                    weight = grey.convert("L").resize((w, h))
            else:
                rgb_image = rgb_image.crop((int(w * .12), int(h * .28), int(w * .88), h))
            small = rgb_image.copy()
            small.thumbnail((160, 160))
            quantised = small.quantize(colors=colours, method=Image.Quantize.MEDIANCUT)
            palette = quantised.getpalette()[: colours * 3]
            indices = np.asarray(quantised)
            if weight is not None:
                factor = (np.asarray(weight.resize(small.size), dtype=np.float32) / 255.0) ** 3
            else:
                factor = np.ones(indices.shape, dtype=np.float32)
            for k in range(colours):
                share = float(factor[indices == k].sum())
                if share > 0:
                    rgb = tuple(palette[k * 3: k * 3 + 3])
                    counts[rgb] = counts.get(rgb, 0) + share
    total = sum(counts.values()) or 1
    return sorted(((rgb, n / total) for rgb, n in counts.items()), key=lambda x: -x[1])


def derive_photo_palette(paths: list[Path], *, mode: str = "auto",
                         weights: list | None = None) -> dict | None:
    """Return colour roles derived from real photos, or None if unusable.

    mode "light" gives a tinted paper canvas, "dark" a deep canvas from the
    dominant hue; "auto" picks dark when the photos are mostly dark.
    """
    paths = [Path(p) for p in paths if Path(p).is_file()][:6]
    if not paths:
        return None
    try:
        clusters = _clusters(paths, weights)
    except Exception:
        return None
    if not clusters:
        return None
    # Dominant hue: the largest cluster that has some colour (sky-grey and
    # concrete are skipped unless nothing else exists).
    chromatic = [(rgb, share) for rgb, share in clusters if _hls(rgb)[2] > 0.12 and 0.12 < _hls(rgb)[1] < 0.9]
    dominant = (chromatic or clusters)[0][0]
    hue, light, sat = _hls(dominant)
    avg_light = sum(_hls(rgb)[1] * share for rgb, share in clusters)
    if mode == "auto":
        mode = "dark" if avg_light < 0.38 else "light"
    tint = min(sat, 0.35)
    if mode == "dark":
        canvas = _from_hls(hue, 0.10, min(0.45, tint + 0.12))
        surface = _from_hls(hue, 0.15, min(0.40, tint + 0.08))
        ink = _from_hls(hue, 0.88, min(0.55, tint + 0.2))
        muted = _from_hls(hue, 0.70, min(0.30, tint))
    else:
        canvas = _from_hls(hue, 0.95, min(0.45, tint + 0.1))
        surface = _from_hls(hue, 0.89, min(0.35, tint + 0.05))
        ink = _from_hls(hue, 0.13, min(0.45, tint + 0.1))
        muted = _from_hls(hue, 0.38, min(0.25, tint))
    # Accent: the most saturated photo colour that reads on the canvas, pushed
    # to a usable lightness; else a complement of the dominant hue.
    def hue_gap(rgb):
        gap = abs(_hls(rgb)[0] - hue)
        return min(gap, 1 - gap)
    # Accent: the subject's own hue first (analogous within 30 degrees), then
    # other saturated photo colours; complements only as a last resort.
    candidates = [dominant] + sorted(
        (rgb for rgb, share in clusters if share > 0.01 and rgb != dominant),
        key=lambda rgb: (hue_gap(rgb) > 0.085, -_hls(rgb)[2]))
    accent = None
    for rgb in candidates:
        h, l, s = _hls(rgb)
        if s < 0.30:
            continue
        for target in ((0.55, 0.62, 0.48, 0.70) if mode == "dark" else (0.42, 0.36, 0.48, 0.30)):
            option = _from_hls(h, target, max(s, 0.55))
            if contrast(option, canvas) >= 3.0:
                accent = option
                break
        if accent:
            break
    if accent is None:
        accent = _from_hls((hue + 0.5) % 1, 0.58 if mode == "dark" else 0.40, 0.6)
    def ink_for(colour):
        return canvas if contrast(canvas, colour) >= contrast(ink, colour) else ink
    # Nudge the accent's lightness until its button text passes WCAG AA.
    h, l, sat_a = _hls(accent)
    for _ in range(12):
        if contrast(ink_for(accent), accent) >= 4.5:
            break
        l += 0.03 if contrast(ink, accent) >= contrast(canvas, accent) else -0.03
        accent = _from_hls(h, l, sat_a)
    accent_ink = ink_for(accent)
    roles = {"mode": mode, "canvas": _hex(canvas), "surface": _hex(surface), "ink": _hex(ink),
             "muted": _hex(muted), "accent": _hex(accent), "accent_ink": _hex(accent_ink),
             "photo_dominant": _hex(dominant)}
    checks = {
        "ink_on_canvas": round(contrast(ink, canvas), 2),
        "muted_on_canvas": round(contrast(muted, canvas), 2),
        "accent_on_canvas": round(contrast(accent, canvas), 2),
        "accent_ink_on_accent": round(contrast(accent_ink, accent), 2),
    }
    if checks["ink_on_canvas"] < 7 or checks["muted_on_canvas"] < 4.5 or checks["accent_ink_on_accent"] < 4.5:
        return None
    roles["contrast"] = checks
    roles["rule"] = ("Canvas covers most of the page; surface for alternate sections; ink for "
                     "text; accent only for the primary action and small highlights. "
                     "Brand colours verified from the source (v8 identity) take precedence.")
    return roles

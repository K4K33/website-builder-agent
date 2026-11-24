"""Colour theory for every built site: perceptual palettes and rendered-colour checks.

Owner feedback (24.11.2026): white text on a bright cobalt field was hard to read, and
the builder clearly did not know colour theory. This module works in OKLCH (perceptual
lightness L 0-1, chroma C, hue H in degrees) so that "make the brand colour deeper"
keeps its hue and only changes how light it is, and it checks the pairings that cause
the problem: light text on a vivid, mid-light field vibrates even when WCAG passes.
"""

import math

# ---------- conversions (sRGB <-> OKLab <-> OKLCH) ----------

def _to_linear(c):
    c = c / 255
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def _from_linear(c):
    c = 12.92 * c if c <= 0.0031308 else 1.055 * c ** (1 / 2.4) - 0.055
    return c * 255


def hex_to_rgb(value):
    value = value.strip().lstrip("#")
    if len(value) == 3:
        value = "".join(ch * 2 for ch in value)
    return tuple(int(value[i:i + 2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb):
    return "#%02x%02x%02x" % tuple(max(0, min(255, round(c))) for c in rgb)


def rgb_to_oklch(rgb):
    r, g, b = (_to_linear(c) for c in rgb)
    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    l, m, s = (math.copysign(abs(v) ** (1 / 3), v) for v in (l, m, s))
    L = 0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s
    a = 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s
    bb = 0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s
    return L, math.hypot(a, bb), math.degrees(math.atan2(bb, a)) % 360


def _oklch_to_linear(L, C, H):
    a = C * math.cos(math.radians(H))
    b = C * math.sin(math.radians(H))
    l = (L + 0.3963377774 * a + 0.2158037573 * b) ** 3
    m = (L - 0.1055613458 * a - 0.0638541728 * b) ** 3
    s = (L - 0.0894841775 * a - 1.2914855480 * b) ** 3
    return (4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
            -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
            -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s)


def oklch_to_rgb(L, C, H):
    """Map to sRGB, reducing chroma (never hue or lightness) until the colour fits."""
    for _ in range(40):
        lin = _oklch_to_linear(L, C, H)
        if all(-1e-4 <= v <= 1 + 1e-4 for v in lin):
            break
        C *= 0.92
    return tuple(_from_linear(min(1, max(0, v))) for v in _oklch_to_linear(L, C, H))


def oklch_hex(L, C, H):
    return rgb_to_hex(oklch_to_rgb(L, C, H))


# ---------- contrast ----------

def luminance(rgb):
    r, g, b = (_to_linear(c) for c in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast(a, b):
    a = hex_to_rgb(a) if isinstance(a, str) else a
    b = hex_to_rgb(b) if isinstance(b, str) else b
    hi, lo = sorted((luminance(a), luminance(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def _shift_until(L, C, H, against, target, direction):
    """Move lightness in one direction until contrast against `against` reaches target."""
    for _ in range(100):
        colour = oklch_hex(L, C, H)
        if contrast(colour, against) >= target:
            return colour
        L = min(0.99, max(0.02, L + 0.01 * direction))
    return oklch_hex(L, C, H)


# ---------- palette ----------

def brand_palette(brand_hex, *, ground="dark"):
    """Return colour roles built around one brand colour.

    - field: the brand colour as a large surface, deepened (same hue, chroma capped at .22) until
      white body text on it reaches 7.5:1, so it reads calmly instead of vibrating.
    - ink / paper: neutrals tinted with the brand hue, never flat grey or pure #000/#fff.
    - accent_on_ink / accent_on_paper: the brand colour lightened or darkened until it
      works as text or links on that ground (4.5:1).
    - muted_on_ink / muted_on_paper / muted_on_field: secondary text tinted from the hue.
    """
    L, C, H = rgb_to_oklch(hex_to_rgb(brand_hex))
    ink = oklch_hex(0.16, min(0.02, C * 0.12), H)
    paper = oklch_hex(0.975, min(0.012, C * 0.06), H)
    on_field = oklch_hex(0.995, 0.004, H)
    field = _shift_until(min(L, 0.62), min(max(C, 0.12), 0.22), H, on_field, 7.5, -1)
    roles = {
        "brand": rgb_to_hex(hex_to_rgb(brand_hex)),
        "field": field,
        "field_deep": oklch_hex(max(0.05, rgb_to_oklch(hex_to_rgb(field))[0] - 0.08), C, H),
        "on_field": on_field,
        "muted_on_field": _shift_until(0.9, 0.04, H, field, 4.5, 1),
        "ink": ink,
        "paper": paper,
        "accent_on_ink": _shift_until(max(L, 0.62), C, H, ink, 4.5, 1),
        "accent_on_paper": _shift_until(min(L, 0.5), C, H, paper, 4.5, -1),
        "muted_on_ink": _shift_until(0.72, 0.02, H, ink, 4.5, 1),
        "muted_on_paper": _shift_until(0.5, 0.02, H, paper, 4.5, -1),
        "line_on_ink": oklch_hex(0.3, 0.02, H),
        "line_on_paper": oklch_hex(0.88, 0.015, H),
        "ground": ground,
    }
    return roles


# ---------- pair checks ----------

def pair_problems(text_hex, bg_hex, *, large=False):
    """Colour-theory problems for one text/background pairing (empty list = fine)."""
    problems = []
    ratio = contrast(text_hex, bg_hex)
    need = 3.0 if large else 4.5
    if ratio < need:
        problems.append(f"contrast {ratio:.2f}:1 below {need}:1")
    tL, tC, tH = rgb_to_oklch(hex_to_rgb(text_hex))
    bL, bC, bH = rgb_to_oklch(hex_to_rgb(bg_hex))
    # A vivid mid-light field behind light body text vibrates (simultaneous contrast):
    # deepen the field so body text reaches 7:1.
    if bC >= 0.13 and 0.35 <= bL <= 0.72 and tL > bL and not large and ratio < 7.5:
        problems.append(f"light body text on a vivid field ({ratio:.2f}:1) vibrates; deepen the field to 7.5:1")
    elif bC > 0.24 and tL > bL and not large:
        problems.append("light body text on a neon field (OKLCH chroma > .24) vibrates; lower the field chroma")
    # Two saturated colours of opposing hue as text and ground flicker at their edge.
    gap = abs(tH - bH) % 360
    gap = min(gap, 360 - gap)
    if tC >= 0.12 and bC >= 0.12 and gap >= 100:
        problems.append("saturated text on a saturated complementary ground flickers")
    return problems


def audit_pairs(pairs, *, min_share=0.01):
    """Audit [{'text': hex, 'bg': hex, 'large': bool, 'weight': n}] measured on a page."""
    total = sum(p.get("weight", 1) for p in pairs) or 1
    seen, out = set(), []
    for pair in pairs:
        if pair.get("weight", 1) / total < min_share:
            continue
        key = (pair["text"], pair["bg"], bool(pair.get("large")))
        if key in seen:
            continue
        seen.add(key)
        for problem in pair_problems(pair["text"], pair["bg"], large=bool(pair.get("large"))):
            out.append(f"colour: {pair['text']} on {pair['bg']}: {problem}")
    return out


# Text colour and the first opaque background behind it, weighted by characters x size.
PAIR_SCRIPT = """() => {
  const toHex = c => { const m = c.match(/\\d+(\\.\\d+)?/g); if (!m) return null;
    if (m.length > 3 && parseFloat(m[3]) < 0.98) return null;
    return '#' + m.slice(0, 3).map(v => Math.round(+v).toString(16).padStart(2, '0')).join(''); };
  const painted = e => { const cs = getComputedStyle(e);
    if (['IMG', 'VIDEO', 'CANVAS', 'PICTURE', 'IFRAME'].includes(e.tagName) || (cs.backgroundImage && cs.backgroundImage !== 'none')) return 'media';
    return toHex(cs.backgroundColor); };
  const mediaChild = e => [...e.children].some(c => ['IMG', 'VIDEO', 'PICTURE', 'CANVAS'].includes(c.tagName) && /absolute|fixed/.test(getComputedStyle(c).position));
  const bgOf = el => {
    // what is actually painted behind the text; null when that is a photo/video (visual review
    // judges those) or when something else covers the text at this moment
    const r = el.getBoundingClientRect();
    if (r.bottom > 0 && r.top < innerHeight && r.right > 0 && r.left < innerWidth) {
      const x = Math.min(innerWidth - 1, Math.max(0, r.left + r.width / 2)), y = Math.min(innerHeight - 1, Math.max(0, r.top + r.height / 2));
      const stack = document.elementsFromPoint(x, y);
      const at = stack.findIndex(e => e === el || el.contains(e));
      if (at < 0) return null;
      for (const e of stack.slice(0, at)) if (painted(e)) return null;   // covered by another layer
      for (const e of stack.slice(at)) { const p = painted(e); if (p === 'media') return null; if (p) return p; }
      return '#ffffff';
    }
    for (let e = el; e; e = e.parentElement) {
      const p = painted(e); if (p === 'media' || mediaChild(e)) return null; if (p) return p; }
    return '#ffffff'; };
  const out = {};
  const skip = new Set(['SCRIPT','STYLE','NOSCRIPT','OPTION','SELECT','TEXTAREA','INPUT','TITLE']);
  for (const el of document.body.querySelectorAll('*')) {
    if (skip.has(el.tagName) || el.closest(':disabled') || (el.closest('details:not([open])') && !el.closest('summary'))) continue;
    let own = ''; for (const n of el.childNodes) if (n.nodeType === 3) own += n.textContent;
    own = own.trim(); if (!own || el.closest('[aria-hidden="true"]')) continue;
    const cs = getComputedStyle(el);
    if (cs.visibility === 'hidden' || cs.display === 'none' || parseFloat(cs.opacity) < 0.5 || !el.getClientRects().length) continue;
    const text = toHex(cs.color), bg = bgOf(el); if (!text || !bg) continue;
    const size = parseFloat(cs.fontSize), large = size >= 24 || (size >= 18.66 && +cs.fontWeight >= 700);
    const k = text + bg + large;
    out[k] = out[k] || {text, bg, large, weight: 0};
    out[k].weight += own.length * size;
  }
  return Object.values(out);
}"""


COLOR_BRIEF = """COLOUR THEORY (applied to every site; build the palette before any layout):
- Value before hue: decide light/dark structure first; colour only works when the lightness steps are clear.
- 60-30-10: one dominant ground, one secondary, and ONE accent (two at most). The brand colour is the accent or a
  whole field, never sprinkled as small bits on grey.
- Work in OKLCH: change lightness to deepen or lighten the brand colour and keep its hue; never pick a new hue.
- A vivid colour used as a large field behind body text is deepened (chroma at most .22) until white text reaches 7.5:1; bright, mid-light
  blues, reds and purples behind light text vibrate (simultaneous contrast) even when they pass 4.5:1.
- Neutrals are tinted with the brand hue (ink about L .16, paper about L .97); never flat grey, never pure #000/#fff
  as the main ground. Secondary text is a tint of the ground's hue, not a grey at low opacity.
- Accent text/links: lighten the brand colour on dark grounds and darken it on light grounds until 4.5:1.
- Never saturated text on a saturated complementary ground (red on green, blue on orange): edges flicker.
- Warm vs cool: a warm subject (wood, food, sauna) on a cool field gains depth; keep photographs and fields from
  fighting by sampling the field hue from the brand or the photo, not inventing a third.
- Text over photos sits on a gradient or a measured dark/light zone of the photo, never on mid-tones.
- utils.color_system.brand_palette(brand_hex) gives these roles; use them as CSS custom properties."""

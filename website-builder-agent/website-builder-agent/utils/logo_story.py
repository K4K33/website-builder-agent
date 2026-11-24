"""Logo story: any company's own logo assembled in 3D as the scroll-driven hero.

The Kaurivo home page proved the pattern (award references: THE LINE, Dropbox
Brand): the brand mark is the protagonist, frame 0 is a full-screen poster of
its pieces close to the camera, scrolling pulls back and locks them together,
one light sweep crosses the mark, then the lock-up steps aside for the copy.

This module makes that automatic for any logo file:

- ``cut_logo`` removes a flat background (or keeps real transparency) and
  splits the mark into its visual parts (letters, shapes) with OpenCV contours,
  grouped to 2-10 pieces left to right. A single-shape mark is cut into three
  bands so it can still assemble.
- ``logo_story_html`` emits a [data-story] hero (utils.scroll_story runtime,
  utils.hero_reveal copy timing) where every piece is an image of the company's
  real logo pixels: colours and shapes are never redrawn or invented.

Use it when the logo is the most authentic subject available (no own photos,
only illustrations): the business's real work beats its logo, its logo beats
stock photography.
"""
from __future__ import annotations

import html
import math
from pathlib import Path

MAX_PIECES = 10


def _load_rgba(path: Path):
    from PIL import Image
    path = Path(path)
    if path.suffix.lower() == ".svg":
        try:
            import cairosvg  # optional; rasterise SVG logos when available
        except ImportError:
            return None
        from io import BytesIO
        png = cairosvg.svg2png(url=str(path), output_width=1600)
        return Image.open(BytesIO(png)).convert("RGBA")
    with Image.open(path) as image:
        return image.convert("RGBA")


def _components(mask, max_side: int = 360):
    """Connected parts of a boolean mask (numpy + Pillow only; CI has no OpenCV).

    Labels are found on a max-pooled, slightly grown copy at most ``max_side``
    wide and mapped back to full resolution, so every logo pixel gets a part."""
    import numpy as np
    h, w = mask.shape
    step = max(1, math.ceil(max(h, w) / max_side))
    hh, ww = math.ceil(h / step), math.ceil(w / step)
    padded = np.zeros((hh * step, ww * step), bool)
    padded[:h, :w] = mask
    small = padded.reshape(hh, step, ww, step).any(axis=(1, 3))
    grown = small.copy()
    grown[1:] |= small[:-1]; grown[:-1] |= small[1:]
    grown[:, 1:] |= small[:, :-1]; grown[:, :-1] |= small[:, 1:]
    labels = np.zeros(grown.shape, np.int32)
    count = 0
    for y, x in zip(*np.nonzero(grown)):
        if labels[y, x]:
            continue
        count += 1
        stack = [(y, x)]
        labels[y, x] = count
        while stack:
            cy, cx = stack.pop()
            for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                if 0 <= ny < hh and 0 <= nx < ww and grown[ny, nx] and not labels[ny, nx]:
                    labels[ny, nx] = count
                    stack.append((ny, nx))
    full = np.repeat(np.repeat(labels, step, axis=0), step, axis=1)[:h, :w]
    return np.where(mask, full, 0), count


def cut_logo(path: Path, out_png: Path, *, max_pieces: int = MAX_PIECES) -> dict | None:
    """Write a transparent PNG of the logo plus one PNG per piece; return the pieces or None.

    Returns {"width", "height", "ratio", "luminance", "pieces": [{"file", "cx", "cy"}]};
    piece files sit next to ``out_png`` and share its canvas, so they stack exactly.
    """
    import numpy as np
    from PIL import Image, ImageFilter

    image = _load_rgba(path)
    if image is None:
        return None
    w, h = image.size
    if w < 40 or h < 16:
        return None
    if max(w, h) < 900:  # sharper poster frame
        scale = 900 / max(w, h)
        image = image.resize((round(w * scale), round(h * scale)), Image.LANCZOS)
        w, h = image.size
    rgba = np.asarray(image).astype(np.int16)
    alpha = rgba[..., 3]
    if alpha.min() < 200 and (alpha > 128).mean() < 0.9:
        mask = alpha > 60
    else:  # flat background: the border colour
        border = np.concatenate([rgba[0, :, :3], rgba[-1, :, :3], rgba[:, 0, :3], rgba[:, -1, :3]])
        bg = np.median(border, axis=0)
        mask = np.abs(rgba[..., :3] - bg).sum(axis=2) > 60
    if mask.mean() < 0.01 or mask.mean() > 0.85:
        return None
    ys, xs = np.nonzero(mask)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    pad = max(4, round(0.02 * max(x1 - x0, y1 - y0)))
    x0, y0 = max(0, x0 - pad), max(0, y0 - pad)
    x1, y1 = min(w, x1 + pad), min(h, y1 + pad)
    mask = mask[y0:y1, x0:x1]
    cut = np.asarray(image)[y0:y1, x0:x1].copy()
    soft = np.asarray(Image.fromarray(mask.astype(np.uint8) * 255).filter(ImageFilter.GaussianBlur(0.8)))
    cut[..., 3] = np.minimum(cut[..., 3], soft)
    out_png = Path(out_png)
    out_png.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(cut, "RGBA").save(out_png, optimize=True)
    h, w = mask.shape

    labels, count = _components(mask)
    total = int(mask.sum()) or 1
    parts = []
    for label in range(1, count + 1):
        sel = labels == label
        area = int(sel.sum())
        if area < total * 0.002:
            continue
        py, px = np.nonzero(sel)
        parts.append({"area": area, "cx": float(px.mean()), "cy": float(py.mean()), "labels": [label]})
    if not parts:
        return None
    # tiny parts (dots, accents) travel with their nearest big neighbour
    big = [p for p in parts if p["area"] >= total * 0.02] or parts
    for p in parts:
        if p in big:
            continue
        near = min(big, key=lambda g: math.hypot(g["cx"] - p["cx"], g["cy"] - p["cy"]))
        near["labels"] += p["labels"]
        near["area"] += p["area"]
    groups = sorted(big, key=lambda g: g["cx"])
    while len(groups) > max_pieces:  # merge the closest neighbours left to right
        gaps = [groups[i + 1]["cx"] - groups[i]["cx"] for i in range(len(groups) - 1)]
        i = gaps.index(min(gaps))
        a, b = groups[i], groups.pop(i + 1)
        total_area = a["area"] + b["area"]
        a["cx"] = (a["cx"] * a["area"] + b["cx"] * b["area"]) / total_area
        a["cy"] = (a["cy"] * a["area"] + b["cy"] * b["area"]) / total_area
        a["area"], a["labels"] = total_area, a["labels"] + b["labels"]
    if len(groups) == 1:  # one solid shape: three vertical bands still assemble
        masks = []
        for i in range(3):
            band = np.zeros_like(mask)
            band[:, round(w * i / 3):round(w * (i + 1) / 3)] = True
            masks.append((band, (w * (i + .5)) / 3, h / 2))
    else:
        masks = [(np.isin(labels, g["labels"]), g["cx"], g["cy"]) for g in groups]
    pieces = []
    for i, (sel, cx, cy) in enumerate(masks):
        piece = cut.copy()
        piece[..., 3] = np.where(sel, piece[..., 3], 0)
        name = f"{out_png.stem}-{i + 1}.png"
        Image.fromarray(piece, "RGBA").save(out_png.with_name(name), optimize=True)
        pieces.append({"file": name, "cx": cx, "cy": cy})
    rgb = cut[..., :3][mask].astype(float)
    lum = float((0.2126 * rgb[:, 0] + 0.7152 * rgb[:, 1] + 0.0722 * rgb[:, 2]).mean() / 255) if len(rgb) else .5
    return {"width": w, "height": h, "ratio": w / h, "luminance": lum, "pieces": pieces}


def _rand(seed: int) -> float:
    """Deterministic 0..1 noise so the same logo always gets the same choreography."""
    x = math.sin(seed * 12.9898 + 78.233) * 43758.5453
    return x - math.floor(x)


def logo_story_html(*, logo_rel: str, cut: dict, copy_html: str, label: str,
                    photo_rel: str = "", photo_alt: str = "", credit_html: str = "",
                    dark: bool = True) -> str:
    """Return the <section> for a logo story hero. ``copy_html`` holds h1, text and the button."""
    w, h = cut["width"], cut["height"]
    n = len(cut["pieces"])
    pieces = []
    for i, piece in enumerate(cut["pieces"]):
        side = -1 if piece["cx"] < w / 2 else 1
        vert = -1 if piece["cy"] < h / 2 else 1
        r = [_rand(i * 7 + k) for k in range(6)]
        x = side * (14 + 22 * r[0])
        y = vert * (8 + 18 * r[1]) if n > 2 else (r[1] - .5) * 30
        z = 220 + 320 * r[2]
        # everything moves from the first pixel of scroll; pieces land one after another
        start = round(0.1 * i / max(1, n - 1), 3) if n > 1 else 0.0
        end = round(0.2 + 0.14 * i / max(1, n - 1), 3)
        base = logo_rel.rsplit("/", 1)[0] + "/" if "/" in logo_rel else ""
        pieces.append(
            f'<img class="ls-piece" data-k="{start},{end}" src="{html.escape(base + piece["file"])}" alt="" '
            f'width="{w}" height="{h}" decoding="async" '
            f'style="--x:{x:.1f}vw;--y:{y:.1f}svh;--z:{z:.0f}px;--rx:{(r[3] - .5) * 70:.0f}deg;'
            f'--ry:{(r[4] - .5) * 80:.0f}deg;--rz:{(r[5] - .5) * 50:.0f}deg;--b:{4 + 4 * r[2]:.1f}px;'
            f'--ox:{100 * piece["cx"] / w:.1f}%;--oy:{100 * piece["cy"] / h:.1f}%">')
    photo = (f'<img class="ls-photo" data-k="0.28,0.74" src="{html.escape(photo_rel)}" alt="{html.escape(photo_alt)}">'
             if photo_rel else "")
    tone = "ls--dark" if dark else "ls--light"
    return f'''<section class="ls-hero {tone}" data-story data-copy-after="0.76" style="--ratio:{cut["ratio"]:.3f}" aria-labelledby="otsikko">
 <div class="ls-stage">
  {photo}
  <div class="ls-shade" data-k="0.28,0.74"></div>
  <div class="ls-lockup" data-k="0.4,0.72" role="img" aria-label="{html.escape(label)}">
   <div class="ls-mark">{"".join(pieces)}<i class="ls-sheen" data-k="0.24,0.42" style="--logo:url('{html.escape(logo_rel)}')"></i></div>
  </div>
  <div class="ls-copy" data-hero-copy>{copy_html}</div>
  {credit_html}
 </div>
</section>'''


STYLE = """
.ls-hero{position:relative;height:250svh;background:var(--ls-bg,#0b0f14);color:var(--ls-ink,#f5f7fa)}
.ls-stage{position:sticky;top:0;height:100svh;overflow:hidden;perspective:1100px;isolation:isolate}
.ls-photo{position:absolute;inset:0;width:100%;height:100%;object-fit:cover;
  transform:scale(calc(1.16 - var(--k) * .16));filter:blur(calc((1 - var(--k)) * 10px));opacity:calc(.25 + var(--k) * .75)}
.ls-shade{position:absolute;inset:0;background:var(--ls-bg,#0b0f14);opacity:calc(.92 - var(--k) * .3)}
.ls-lockup{position:absolute;left:50%;top:48%;width:min(78vw,1080px,44svh * var(--ratio));transform-style:preserve-3d;
  transform:translate(-50%,-50%) translateY(calc(var(--k) * -24svh)) scale(calc(1 - var(--k) * .5))}
.ls-mark{position:relative;aspect-ratio:var(--ratio);transform-style:preserve-3d}
.ls-piece{position:absolute;inset:0;width:100%;height:100%;max-width:none;transform-origin:var(--ox) var(--oy);will-change:transform;
  --i:calc(1 - var(--k));
  transform:translate3d(calc(var(--x) * var(--i)),calc(var(--y) * var(--i)),calc(var(--z) * var(--i)))
    rotateX(calc(var(--rx) * var(--i))) rotateY(calc(var(--ry) * var(--i))) rotateZ(calc(var(--rz) * var(--i)));
  filter:blur(calc(var(--b) * var(--i))) drop-shadow(0 18px 30px rgba(0,0,0,calc(.45 * var(--i))))}
.ls-sheen{position:absolute;inset:0;pointer-events:none;mix-blend-mode:overlay;
  -webkit-mask:var(--logo) center/100% 100% no-repeat;mask:var(--logo) center/100% 100% no-repeat;
  background:linear-gradient(105deg,transparent 30%,rgba(255,255,255,.95) 50%,transparent 70%) no-repeat;
  background-size:60% 100%;background-position:calc(-80% + var(--k) * 260%) 0}
.ls-copy{position:absolute;left:max(20px,6vw);right:max(20px,6vw);bottom:max(28px,9svh);max-width:760px}
.ls-copy h1{margin:0 0 .4em;line-height:1}
.ls-hero .hero__credit{position:absolute;right:16px;bottom:12px;margin:0;font-size:12px;opacity:.75}
@media (max-width:700px){.ls-hero{height:230svh}.ls-lockup{width:min(86vw,36svh * var(--ratio))}
  .ls-copy{bottom:max(20px,5svh)}}
@media (prefers-reduced-motion:reduce){.ls-hero{height:auto}.ls-stage{position:relative}}
"""

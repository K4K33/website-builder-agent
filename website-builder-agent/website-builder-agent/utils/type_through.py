"""Subject through type: a giant word behind the company's own subject.

Award-style heroes put one large word BEHIND the real subject of a photo (a
product, a person at work, a building), so the subject seems to stand in
front of the type and the word slides behind it on scroll. The builder makes
this from one staged photo without any AI call:

1. U2-Net-p (local, free) finds the subject; the mask is accepted only for a
   clearly separated subject (coverage 8-70 %, little contact with the top
   and side edges; touching the bottom edge is fine: people and objects stand)
2. a cut-out with a feathered alpha is written beside the photo
3. photo, word and cut-out are stacked with the same object-fit, so the
   subject stays pixel-aligned; scroll only moves the word (and scales the
   photo and cut-out together)

Without a clean mask, for reduced motion or without JavaScript, the authored
photo and word stay as written (the word is decorative, aria-hidden; the h1
carries the meaning).
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
import re

from bs4 import BeautifulSoup

TYPECUT_BRIEF = """
SUBJECT THROUGH TYPE (optional hero, only for a staged photo whose subject is
clearly separated: one product, one person at work, one building or vehicle
against a calmer background). Write:

<section data-kaurivo-typecut aria-labelledby="hero-title">
  <img src="assets/subject.webp" alt="What the photo shows">
  <p data-typecut-word aria-hidden="true">Word</p>
  <div class="hero-copy"><h1 id="hero-title">Verified headline</h1> ... primary action ...</div>
</section>

The word is ONE short verified word from the company (its name, product or
trade, 3-10 letters). The builder puts it behind the subject and slides it
on scroll. Never use it for interiors, crowds, flat textures or busy scenes;
use at most one per page.
""".strip()

COVERAGE = (0.08, 0.70)
MAX_SIDE_SHARE = 0.16
_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".avif"}

STYLE = """
[data-kaurivo-typecut]{position:relative;overflow:clip;isolation:isolate}
[data-kaurivo-typecut][data-typecut-active]{height:210svh}
.typecut__stage{position:sticky;top:0;height:100svh;overflow:hidden;isolation:isolate}
.typecut__stage > img,.typecut__stage > [data-typecut-front]{position:absolute;inset:0;width:100%;height:100%;
 object-fit:cover;object-position:var(--typecut-pos,50% 50%);transform:scale(var(--typecut-s,1));transform-origin:50% 70%;will-change:transform}
.typecut__stage > img{z-index:0}
.typecut__stage > [data-typecut-word]{position:absolute;z-index:1;left:-50vw;right:-50vw;top:var(--typecut-top,18%);margin:0;
 white-space:nowrap;text-align:center;line-height:.8;font-size:var(--typecut-size,clamp(96px,24vw,420px));
 transform:translate3d(var(--typecut-x,0),0,0);will-change:transform;pointer-events:none}
.typecut__stage > [data-typecut-front]{z-index:2;pointer-events:none}
:where(.typecut__stage > :not(img):not([data-typecut-word]):not([data-typecut-front])){position:relative}
.typecut__stage > :not(img):not([data-typecut-word]):not([data-typecut-front]){z-index:3}
"""

SCRIPT = r"""
(() => {
  const scenes = [...document.querySelectorAll('[data-kaurivo-typecut][data-typecut-active]')];
  if (!scenes.length || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  let ticking = false;
  function update() {
    ticking = false;
    for (const s of scenes) {
      const r = s.getBoundingClientRect();
      const q = Math.min(1, Math.max(0, -r.top / Math.max(1, r.height - innerHeight)));
      // The word travels behind the subject; photo and cut-out scale together.
      s.style.setProperty('--typecut-x', (-q * 28).toFixed(2) + 'vw');
      s.style.setProperty('--typecut-s', (1 + q * .08).toFixed(4));
    }
  }
  addEventListener('scroll', () => { if (!ticking) { ticking = true; requestAnimationFrame(update); } }, {passive: true});
  update();
})();
"""


def subject_mask_ok(mask_path: Path) -> bool:
    """A clearly separated subject: sensible coverage, free top and sides."""
    from PIL import Image
    from utils.depth_estimation import mask_coverage
    coverage = mask_coverage(mask_path)
    if not COVERAGE[0] <= coverage <= COVERAGE[1]:
        return False
    with Image.open(mask_path) as image:
        gray = image.convert("L")
        width, height = gray.size
        px = gray.load()
        top = [px[x, 0] for x in range(width)]
        sides = [px[0, y] for y in range(height)] + [px[width - 1, y] for y in range(height)]
        histogram = gray.histogram()
    share = lambda values: sum(1 for v in values if v > 128) / max(1, len(values))
    uncertain = sum(histogram[40:216]) / max(1, sum(histogram))
    return share(top) <= MAX_SIDE_SHARE and share(sides) <= MAX_SIDE_SHARE and uncertain <= 0.14


def subject_box(mask_path: Path) -> tuple[float, float, float, float]:
    """Subject bounding box as fractions (left, top, right, bottom)."""
    from PIL import Image
    with Image.open(mask_path) as m:
        gray = m.convert("L")
        box = gray.point(lambda v: 255 if v > 128 else 0).getbbox() or (0, 0, *gray.size)
        w, h = gray.size
    return box[0] / w, box[1] / h, box[2] / w, box[3] / h


def solid_mask(gray):
    """Fill holes inside the subject (uncertain pixels in a cup of coffee, a
    window in a car) so the word never shows through the subject."""
    from PIL import Image, ImageDraw, ImageOps
    binary = gray.point(lambda v: 255 if v > 110 else 0)
    w, h = binary.size
    background = Image.new("L", (w + 2, h + 2), 255)  # same as the (inverted) outside
    background.paste(ImageOps.invert(binary), (1, 1))
    ImageDraw.floodfill(background, (0, 0), 128)        # outside reached from the border
    holes = background.crop((1, 1, w + 1, h + 1)).point(lambda v: 255 if v == 255 else 0)
    from PIL import ImageChops, ImageFilter
    filled = ImageChops.lighter(binary, holes)
    # Fully opaque inside (a few pixels in from the outline), soft only at the edge.
    core = filled.filter(ImageFilter.MinFilter(7))
    return ImageChops.lighter(ImageChops.lighter(gray, holes), core)


def make_cutout(photo: Path, mask_path: Path, target: Path) -> Path | None:
    """The photo with the subject mask as a softly feathered alpha (same size)."""
    try:
        from PIL import Image, ImageFilter
        with Image.open(photo) as image:
            rgb = image.convert("RGB")
        with Image.open(mask_path) as m:
            alpha = solid_mask(m.convert("L").resize(rgb.size)).filter(ImageFilter.GaussianBlur(1.2))
        rgba = rgb.copy()
        rgba.putalpha(alpha)
        target.parent.mkdir(parents=True, exist_ok=True)
        rgba.save(target, "WEBP", quality=88)
        return target
    except Exception:
        return None


def _staged(route: str, src: str, allowed: dict) -> str | None:
    from utils.product_relief import _staged as staged
    return staged(route, src, allowed)


def enhance_type_through(html: str, *, route: str, media: list[dict],
                         site_root: str | Path | None) -> str:
    if "data-kaurivo-typecut" not in html or site_root is None:
        return html
    from utils import depth_estimation
    site_root = Path(site_root)
    soup = BeautifulSoup(html, "html.parser")
    allowed = {item["src"]: item["sha256"] for item in media
               if PurePosixPath(item["src"]).suffix.lower() in _IMAGE_EXT}
    prefix = "../" * (len(PurePosixPath(route).parts) - 1)
    active = 0
    for scene in soup.select("[data-kaurivo-typecut]"):
        scene.attrs.pop("data-typecut-active", None)
        for old in scene.select("[data-typecut-front]"):
            old.decompose()
        for stage in scene.find_all("div", class_="typecut__stage", recursive=False):
            stage.unwrap()
        photo = scene.find("img", recursive=False)
        word = scene.find(attrs={"data-typecut-word": True}, recursive=False)
        if (active or photo is None or word is None or not photo.get("alt", "").strip()
                or not 2 <= len(word.get_text(strip=True)) <= 14 or depth_estimation.disabled()):
            continue
        word["aria-hidden"] = "true"
        src = _staged(route, photo.get("src"), allowed)
        if not src or not (site_root / src).is_file():
            continue
        key = sha256((allowed[src] + "typecut-v1").encode()).hexdigest()[:12]
        folder = PurePosixPath("assets/typecut") / key
        mask, front = site_root / folder / "mask.webp", site_root / folder / "front.webp"
        if not mask.is_file() and depth_estimation.estimate_mask(site_root / src, mask) is None:
            continue
        if not subject_mask_ok(mask):
            continue
        if not front.is_file() and make_cutout(site_root / src, mask, front) is None:
            continue
        # Place the word across the upper part of the subject, sized to it, and
        # keep the subject in view when the photo is cropped (cover).
        left, top, right, bottom = subject_box(mask)
        cx, cy = (left + right) / 2, (top + bottom) / 2
        height = max(.15, bottom - top)
        # The word lives in the UPPER band of the hero and must end above the copy
        # (headline, text and call sit in the lower half): top 6-18 %, and its
        # height (font-size x .85) never past 44 % of the hero.
        word_top = min(18.0, max(6.0, (top + height * .08) * 100 - 6))
        word_size = max(12.0, min(height * 62, (44.0 - word_top) / .85))
        kept = re.sub(r"--typecut-(?:pos|top|size):[^;]*;?\s*", "", str(scene.get("style") or "")).strip().rstrip(";")
        scene["style"] = (kept + ("; " if kept else "")
                          + f"--typecut-pos:{cx * 100:.1f}% {cy * 100:.1f}%;"
                          + f"--typecut-top:{word_top:.1f}%;"
                          + f"--typecut-size:min(22vw,{word_size:.1f}svh)")
        word.insert_after(soup.new_tag("img", attrs={
            "data-typecut-front": "", "src": prefix + str(folder / "front.webp"), "alt": "",
            "aria-hidden": "true", "decoding": "async"}))
        scene["data-typecut-active"] = ""
        # Pin all layers in one stage so the word can slide while the hero holds.
        stage = soup.new_tag("div", attrs={"class": "typecut__stage"})
        for child in list(scene.children):
            stage.append(child.extract())
        scene.append(stage)
        active += 1
    for item in soup.select("style[data-kaurivo-typecut-runtime], script[data-kaurivo-typecut-runtime]"):
        item.decompose()
    if active and soup.head and soup.body:
        for name, code, parent in (("style", STYLE, soup.head), ("script", SCRIPT, soup.body)):
            tag = soup.new_tag(name, attrs={"data-kaurivo-typecut-runtime": ""})
            tag.string = code
            parent.append(tag)
    return re.sub(r"\A(<!DOCTYPE[^>]+>)\s*", r"\1\n", str(soup))

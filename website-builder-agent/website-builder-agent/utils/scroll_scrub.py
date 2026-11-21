"""Scroll-scrubbed signature hero: the builder's deterministic motion engine.

The model only authors ordinary, readable HTML (poster image, h1, chapter
texts, primary action) inside ``data-kaurivo-scrub``. The builder then:

1. makes a frame sequence from the company's own staged material
   (a video when one is staged, otherwise a slow camera move through 1-4 real
   photographs) as WebP, separately for desktop and phone;
2. pins the hero for several screen heights and draws the frame that matches
   the scroll position on a canvas, eased so the motion feels smooth without
   hijacking native scrolling;
3. reveals each chapter text at its own scroll point (``data-at``), in the DOM;
4. keeps the poster as the first view, shows the poster and all text without
   motion for reduced motion or without JavaScript, loads the first 20 frames
   first and the rest in the background, and caps the device pixel ratio.

No generated or stock imagery: only staged files with verified digests.
"""
from __future__ import annotations

from hashlib import sha256
import json
from pathlib import Path, PurePosixPath
from posixpath import normpath
import re
import shutil
import subprocess
import tempfile
from urllib.parse import urlsplit

from bs4 import BeautifulSoup

from utils.depth_scene_runtime import SCRIPT as DEPTH_SCRIPT

SCRUB_BRIEF = """
SIGNATURE HERO ENGINE (use when pre_build_brief q1 technique is video_scrub,
photo_sequence_scrub or cinematic_photo_scroll). Author the home page hero as
ordinary HTML; the builder adds frames, canvas, pinning and playback:

<section data-kaurivo-scrub aria-labelledby="hero-title">
  <img data-kaurivo-scrub-poster src="assets/best-photo.webp" alt="…">
  <img data-kaurivo-scrub-frame src="assets/second-photo.webp" alt="…">  (optional, up to 3 more, in story order)
  <div data-kaurivo-scrub-copy>
    <h1 id="hero-title">Verified headline</h1>
    <p data-at="0">First chapter, verified fact.</p>
    <p data-at="0.4">Second chapter.</p>
    <p data-at="0.75">Third chapter.</p>
    <a href="tel:…">Primary action from q4</a>
  </div>
</section>

For a builder, renovator, carpenter or architect add data-scrub-style="blueprint"
to the section: the first photo then starts as a line drawing of the real
building and is built up from the ground as the visitor scrolls.

Use only staged image paths. Chapters are short verified facts in story
order; data-at is the scroll point between 0 and 0.9. Write a good static
layout for the poster and copy too: it is what reduced-motion and no-script
visitors see. Do not write canvas, scripts or scroll code for this hero.
""".strip()

DESKTOP = {"width": 1280, "height": 800, "count": 96}
MOBILE = {"width": 540, "height": 960, "count": 60}
BUDGET_BYTES = {"d": 6_000_000, "m": 2_500_000}
EAGER_FRAMES = 20
_IMAGE_EXT = {".jpg", ".jpeg", ".png", ".webp", ".avif"}
_VIDEO_EXT = {".mp4", ".webm", ".mov"}


def _smooth(t: float) -> float:
    return t * t * (3 - 2 * t)


def _cover_crop(image, width, height, scale, focus_x=.5, focus_y=.5):
    """Crop ``image`` to width:height, zoomed in by ``scale`` around a focus."""
    src_w, src_h = image.size
    target = width / height
    if src_w / src_h > target:
        crop_h = src_h / scale
        crop_w = crop_h * target
    else:
        crop_w = src_w / scale
        crop_h = crop_w / target
    left = min(max(0, focus_x * src_w - crop_w / 2), src_w - crop_w)
    top = min(max(0, focus_y * src_h - crop_h / 2), src_h - crop_h)
    from PIL import Image
    return image.resize((width, height), Image.LANCZOS,
                        box=(left, top, left + crop_w, top + crop_h))


def _photo_frames(paths: list[Path], width: int, height: int, count: int):
    """A slow push-in through each photo with soft crossfades between them."""
    from PIL import Image
    photos = [Image.open(p).convert("RGB") for p in paths]
    segments = len(photos)
    for index in range(count):
        t = index / max(1, count - 1)
        position = min(segments - 1e-6, t * segments)
        current = int(position)
        local = position - current
        drift = (-1) ** current * .04

        def render(n, u):
            return _cover_crop(photos[n], width, height, 1.0 + .16 * _smooth(u),
                               .5 + drift * (u - .5), .5)
        frame = render(current, local)
        fade_start = .78
        if current + 1 < segments and local > fade_start:
            mix = _smooth((local - fade_start) / (1 - fade_start))
            frame = Image.blend(frame, render(current + 1, 0.0), mix)
        yield frame


def _video_frames(path: Path, width: int, height: int, count: int, workdir: Path):
    """Evenly sampled frames from the company's own video (needs ffmpeg)."""
    from PIL import Image
    ffmpeg = shutil.which("ffmpeg")
    ffprobe = shutil.which("ffprobe")
    if not ffmpeg or not ffprobe:
        raise RuntimeError("ffmpeg is required for a video signature")
    duration = float(subprocess.run(
        [ffprobe, "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(path)],
        check=True, capture_output=True, text=True, timeout=60).stdout.strip() or 0)
    if duration <= 0:
        raise RuntimeError("video has no duration")
    subprocess.run(
        [ffmpeg, "-v", "error", "-y", "-i", str(path), "-vf", f"fps={count / duration:.5f}",
         "-frames:v", str(count), str(workdir / "v%04d.png")],
        check=True, timeout=600)
    for frame in sorted(workdir.glob("v*.png"))[:count]:
        with Image.open(frame) as image:
            yield _cover_crop(image.convert("RGB"), width, height, 1.0)


def make_frames(sources: list[Path], out_dir: Path, *, kind: str, width: int,
                height: int, count: int) -> dict:
    """Write frames to out_dir and return the sequence manifest."""
    out_dir.mkdir(parents=True, exist_ok=True)
    budget = BUDGET_BYTES[kind]
    attempts = [(count, q) for q in (68, 56, 46)] + [(max(min(count, 24), count * 2 // 3), 46)]
    for frames_wanted, quality in attempts:
        for old in out_dir.glob("*.webp"):
            old.unlink()
        with tempfile.TemporaryDirectory() as tmp:
            if sources[0].suffix.lower() in _VIDEO_EXT:
                frames = _video_frames(sources[0], width, height, frames_wanted, Path(tmp))
            else:
                frames = _photo_frames(sources, width, height, frames_wanted)
            written = 0
            for index, frame in enumerate(frames):
                frame.save(out_dir / f"{index:03d}.webp", "WEBP", quality=quality, method=4)
                written += 1
        total = sum(p.stat().st_size for p in out_dir.glob("*.webp"))
        if total <= budget:
            return {"count": written, "bytes": total, "quality": quality,
                    "width": width, "height": height}
    for old in out_dir.glob("*.webp"):
        old.unlink()
    raise RuntimeError(f"scroll scrub frames exceed the {kind} budget ({total} bytes)")


_STYLE = """
[data-kaurivo-scrub="ready"][data-scrub-active]{position:relative;display:block!important;block-size:var(--scrub-length,420svh)!important;padding:0!important;margin-inline:0!important;max-inline-size:none!important;border-radius:0!important}
[data-scrub-active]>[data-scrub-stage]{position:sticky;inset-block-start:0;block-size:100svh;overflow:hidden;isolation:isolate}
[data-scrub-active] [data-kaurivo-scrub-poster],[data-scrub-active] canvas[data-scrub-canvas]{position:absolute;inset:0;inline-size:100%;block-size:100%;object-fit:cover;margin:0}
[data-scrub-active] [data-kaurivo-scrub-frame]{display:none}
[data-scrub-active] canvas[data-scrub-canvas]{opacity:0;transition:opacity .4s ease}
[data-scrub-active][data-scrub-drawn] canvas[data-scrub-canvas]{opacity:1}
[data-scrub-active]>[data-scrub-stage]::after{content:"";position:absolute;inset:0;z-index:1;pointer-events:none;background:linear-gradient(180deg,rgba(0,0,0,0) 30%,rgba(0,0,0,.7) 100%),radial-gradient(80% 60% at 0% 100%,rgba(0,0,0,.45),rgba(0,0,0,0) 70%)}
[data-scrub-active] [data-kaurivo-scrub-copy]{position:absolute;z-index:2;inset-inline:clamp(20px,5vw,72px);inset-block-end:clamp(28px,8svh,88px);max-inline-size:min(46rem,calc(100% - 40px));color:#fff;margin:0}
[data-scrub-active] [data-kaurivo-scrub-copy] [data-at]{opacity:0;transform:translateY(12px);transition:opacity .45s ease,transform .6s cubic-bezier(.16,1,.3,1)}
[data-scrub-active] [data-kaurivo-scrub-copy] [data-at].is-on{opacity:1;transform:none}
[data-scrub-active] [data-scrub-chapters]{display:grid}
[data-scrub-active] [data-scrub-chapters]>[data-at]{grid-area:1/1}
[data-scrub-progress]{display:none}
[data-scrub-active] [data-scrub-progress]{display:block;position:absolute;z-index:2;inset:auto 0 0;block-size:3px;background:rgba(255,255,255,.22)}
[data-scrub-progress] i{display:block;block-size:100%;background:currentColor;transform-origin:left;transform:scaleX(var(--scrub-p,0))}
"""

_SCRIPT = """
(() => {
  const reduce = matchMedia('(prefers-reduced-motion: reduce)');
  if (reduce.matches || !('IntersectionObserver' in window)) return;
  const phone = matchMedia('(max-width: 760px)').matches;
  for (const scene of document.querySelectorAll('[data-kaurivo-scrub="ready"]:not([data-scrub-mode="depth"])')) {
    const set = JSON.parse(scene.getAttribute(phone ? 'data-scrub-m' : 'data-scrub-d'));
    const stage = scene.querySelector('[data-scrub-stage]');
    const canvas = scene.querySelector('canvas[data-scrub-canvas]');
    const ctx = canvas.getContext('2d');
    const bar = scene.querySelector('[data-scrub-progress]');
    const chapters = [...scene.querySelectorAll('[data-kaurivo-scrub-copy] [data-at]')]
      .map(el => ({el, at: Math.min(.95, Math.max(0, parseFloat(el.dataset.at) || 0))}))
      .sort((a, b) => a.at - b.at);
    const frames = new Array(set.count);
    let current = 0, target = 0, running = false, drawn = -1;
    const url = i => set.base + String(i).padStart(3, '0') + '.webp';
    function load(i) {
      if (frames[i]) return frames[i].ready;
      const image = new Image(); image.decoding = 'async'; image.src = url(i);
      frames[i] = image; image.ready = image.decode().then(() => { image.ok = true; }).catch(() => {});
      return image.ready;
    }
    function size() {
      const dpr = Math.min(devicePixelRatio || 1, 2);
      canvas.width = Math.round(stage.clientWidth * dpr);
      canvas.height = Math.round(stage.clientHeight * dpr);
      drawn = -1; paint();
    }
    function paint() {
      let i = Math.round(current);
      while (i > 0 && !(frames[i] && frames[i].ok)) i--;
      const image = frames[i];
      if (!image || !image.ok || i === drawn) return;
      const s = Math.max(canvas.width / image.naturalWidth, canvas.height / image.naturalHeight);
      const w = image.naturalWidth * s, h = image.naturalHeight * s;
      ctx.drawImage(image, (canvas.width - w) / 2, (canvas.height - h) / 2, w, h);
      drawn = i; scene.setAttribute('data-scrub-drawn', '');
    }
    function progress() {
      const r = scene.getBoundingClientRect();
      return Math.min(1, Math.max(0, -r.top / Math.max(1, r.height - innerHeight)));
    }
    function tick() {
      current += (target - current) * .2;
      if (Math.abs(target - current) < .02) current = target;
      paint();
      if (current !== target) requestAnimationFrame(tick); else running = false;
    }
    function update() {
      const p = progress();
      target = p * (set.count - 1);
      if (bar) bar.style.setProperty('--scrub-p', p.toFixed(4));
      let on = 0;
      chapters.forEach((c, k) => { if (p >= c.at) on = k; });
      chapters.forEach((c, k) => c.el.classList.toggle('is-on', k === on));
      if (!running) { running = true; requestAnimationFrame(tick); }
    }
    const eager = Math.min(set.count, set.eager);
    Promise.all(Array.from({length: eager}, (_, i) => load(i))).then(() => {
      if (!(frames[0] && frames[0].ok)) return;  // keep the poster layout
      scene.style.setProperty('--scrub-length', set.length);
      scene.setAttribute('data-scrub-active', '');
      size(); update();
      addEventListener('scroll', update, {passive: true});
      addEventListener('resize', size, {passive: true});
      reduce.addEventListener('change', () => location.reload());
      let next = eager;
      const more = () => {
        const batch = [];
        for (let k = 0; k < 12 && next < set.count; k++) batch.push(load(next++));
        if (batch.length) Promise.all(batch).then(() => {
          (window.requestIdleCallback || setTimeout)(more); update();
        });
      };
      more();
    });
  }
})();
"""


def _staged(route: str, src: str, allowed: dict) -> tuple[str, str] | None:
    try:
        parts = urlsplit(src or "")
    except ValueError:
        return None
    if parts.scheme or parts.netloc or parts.path.startswith("/") or parts.query or parts.fragment:
        return None
    resolved = normpath(str(PurePosixPath(route).parent / parts.path))
    digest = allowed.get(resolved)
    return (resolved, digest) if digest else None


def _depth_layers(sources, files, site_root: Path, prefix: str, route: str,
                  blueprint: bool = False) -> list | None:
    """Depth map per staged photo (free local model), or None to use frames."""
    from utils import depth_estimation
    if depth_estimation.disabled() or any(f.suffix.lower() in _VIDEO_EXT for f in files):
        return None
    key = sha256(json.dumps([d for _, d in sources] + ["depth-v1"]).encode()).hexdigest()[:12]
    layers = []
    for index, ((src, _), file) in enumerate(zip(sources, files)):
        relative = PurePosixPath("assets/depth") / key / f"{index}.webp"
        target = site_root / relative
        if not target.is_file() and depth_estimation.estimate_depth(file, target) is None:
            return None
        layer = {"img": prefix + src, "depth": prefix + str(relative)}
        if blueprint and index == 0:
            drawing = PurePosixPath("assets/depth") / key / "0-lines.webp"
            if (site_root / drawing).is_file() or depth_estimation.line_drawing(
                    file, target, site_root / drawing):
                layer["lines"] = prefix + str(drawing)
        layers.append(layer)
    return layers


def enhance_scroll_scrub(html: str, *, route: str, media: list[dict],
                         site_root: str | Path | None) -> str:
    """Attach the scrub engine to a well-formed hero built from staged media."""
    if "data-kaurivo-scrub" not in html or site_root is None:
        return html
    site_root = Path(site_root)
    soup = BeautifulSoup(html, "html.parser")
    allowed = {item["src"]: item["sha256"] for item in media
               if PurePosixPath(item["src"]).suffix.lower() in _IMAGE_EXT | _VIDEO_EXT}
    ready = False
    for scene in soup.select("[data-kaurivo-scrub]"):
        for attr in ("data-scrub-active", "data-scrub-d", "data-scrub-m", "data-scrub-drawn",
                     "data-scrub-mode", "data-depth"):
            scene.attrs.pop(attr, None)
        scene["data-kaurivo-scrub"] = ""
        if ready or scene.find_parent("main") is None:
            continue  # one signature moment per page, inside main
        for old in scene.select("[data-scrub-stage], [data-scrub-chapters]"):
            old.unwrap()
        for old in scene.select("canvas[data-scrub-canvas], [data-scrub-progress]"):
            old.decompose()
        poster = scene.find(attrs={"data-kaurivo-scrub-poster": True}, recursive=False)
        copy = scene.find(attrs={"data-kaurivo-scrub-copy": True}, recursive=False)
        if poster is None or copy is None or poster.name != "img" or not poster.get("alt", "").strip():
            continue
        if copy.find("h1") is None:
            continue
        extra = scene.find_all(attrs={"data-kaurivo-scrub-frame": True}, recursive=False)[:3]
        sources = []
        for image in [poster, *extra]:
            staged = _staged(route, image.get("src"), allowed)
            if staged and staged not in sources:
                sources.append(staged)
        if not sources or len(sources) != 1 + len(extra):
            continue
        files = [site_root / src for src, _ in sources]
        if not all(f.is_file() for f in files):
            continue
        prefix = "../" * (len(PurePosixPath(route).parts) - 1)
        length = f"{300 + 40 * len(sources)}svh"
        blueprint = scene.get("data-scrub-style") == "blueprint"
        depth_layers = _depth_layers(sources, files, site_root, prefix, route, blueprint)
        if depth_layers:
            # A real 3D camera move through the photos: far lighter than frames.
            scene["data-scrub-mode"] = "depth"
            scene["data-depth"] = json.dumps({"layers": depth_layers, "length": length},
                                             separators=(",", ":"))
            manifests = {"d": None, "m": None}
        else:
            manifests = {}
        key = sha256(json.dumps([d for _, d in sources] + [DESKTOP, MOBILE]).encode()).hexdigest()[:12]
        base = PurePosixPath("assets/scrub") / key
        for kind, spec in (() if depth_layers else (("d", DESKTOP), ("m", MOBILE))):
            folder = site_root / base / kind
            manifest_file = folder / "manifest.json"
            if manifest_file.is_file():
                manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
            else:
                try:
                    manifest = make_frames(files, folder, kind=kind, **spec)
                except (RuntimeError, OSError, subprocess.SubprocessError):
                    manifest = None  # keep the authored static hero
                if manifest:
                    manifest_file.write_text(json.dumps(manifest), encoding="utf-8")
            if not manifest:
                break
            manifests[kind] = {"base": prefix + f"{base}/{kind}/",
                               "count": manifest["count"], "eager": EAGER_FRAMES,
                               "length": length}
        if set(manifests) != {"d", "m"}:
            continue
        if not depth_layers:
            scene["data-scrub-d"] = json.dumps(manifests["d"], separators=(",", ":"))
            scene["data-scrub-m"] = json.dumps(manifests["m"], separators=(",", ":"))
        poster["fetchpriority"] = "high"
        poster.attrs.pop("loading", None)
        stage = soup.new_tag("div", attrs={"data-scrub-stage": ""})
        for child in list(scene.contents):
            stage.append(child.extract())
        scene.append(stage)
        poster.insert_after(soup.new_tag("canvas", attrs={"data-scrub-canvas": "", "aria-hidden": "true"}))
        chapters = copy.find_all(attrs={"data-at": True}, recursive=False)
        if len(chapters) > 1:
            group = soup.new_tag("div", attrs={"data-scrub-chapters": ""})
            chapters[0].insert_before(group)
            for chapter in chapters:
                group.append(chapter.extract())
        bar = soup.new_tag("div", attrs={"data-scrub-progress": "", "aria-hidden": "true"})
        bar.append(soup.new_tag("i"))
        stage.append(bar)
        scene["data-kaurivo-scrub"] = "ready"
        ready = True

    for item in soup.select("style[data-kaurivo-scrub-runtime], script[data-kaurivo-scrub-runtime]"):
        item.decompose()
    if ready and soup.head and soup.body:
        runtime = [("style", _STYLE, soup.head)]
        if soup.select_one('[data-kaurivo-scrub="ready"]:not([data-scrub-mode="depth"])'):
            runtime.append(("script", _SCRIPT, soup.body))
        if soup.select_one('[data-kaurivo-scrub="ready"][data-scrub-mode="depth"]'):
            runtime.append(("script", DEPTH_SCRIPT, soup.body))
        for name, code, parent in runtime:
            tag = soup.new_tag(name, attrs={"data-kaurivo-scrub-runtime": ""})
            tag.string = code
            parent.append(tag)
    return re.sub(r"\A(<!DOCTYPE[^>]+>)\s*", r"\1\n", str(soup))

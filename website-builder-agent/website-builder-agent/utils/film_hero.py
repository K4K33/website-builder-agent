"""Film hero: a construction film scrubbed by scroll (the reference-site device).

The hero pins a full-bleed canvas and draws frame N of a pre-cut frame
sequence as the visitor scrolls (frames, not <video>, so scrubbing is exact
and smooth on every phone). The current work stage is named in large type
and switches when its clip starts; the film is labelled as an illustration.
Reduced motion or no JavaScript: the finished last frame is shown still.
"""
from __future__ import annotations

import html
import json
from pathlib import Path
import shutil

STYLE = """
.hero--film{position:relative;height:430svh;background:#0d0f10;color:#fff}
.film__stage{position:sticky;top:0;height:100svh;overflow:hidden}
.film__stage canvas,.film__poster{position:absolute;inset:0;width:100%;height:100%;display:block;object-fit:cover}
.hero--film.is-live .film__poster{visibility:hidden}
.film__stage::after{content:"";position:absolute;inset:0;pointer-events:none;
 background:linear-gradient(90deg,rgba(0,0,0,.62),rgba(0,0,0,.18) 48%,transparent 70%),linear-gradient(0deg,rgba(0,0,0,.5),transparent 40%)}
.film__step{position:absolute;z-index:2;left:var(--gutter,24px);top:clamp(96px,16vh,160px);margin:0;display:flex;align-items:baseline;gap:16px}
.film__num{font-variant-numeric:tabular-nums;font-weight:650;font-size:clamp(14px,1.1vw,18px);opacity:.8}
.film__name{font-family:"Display",inherit;font-size:clamp(46px,8vw,132px);line-height:.9;letter-spacing:-.02em}
.film__step.flip .film__name{animation:filmIn .8s cubic-bezier(.16,1,.3,1)}
@keyframes filmIn{from{opacity:0;transform:translateY(.25em)}to{opacity:1;transform:none}}
.film__copy{position:absolute;z-index:2;left:var(--gutter,24px);bottom:clamp(40px,9vh,96px);max-width:min(36rem,82vw)}
.film__copy h1{font-size:clamp(34px,4.4vw,72px);line-height:.98;margin:0;color:#fff}
.film__copy p{margin:12px 0 0;max-width:36ch;color:rgba(255,255,255,.86)}
.film__note{position:absolute;z-index:2;right:var(--gutter,24px);top:clamp(80px,11vh,96px);margin:0;font-size:12px;
 background:rgba(0,0,0,.45);padding:5px 10px;border-radius:999px}
.film__bar{position:absolute;z-index:2;left:var(--gutter,24px);right:var(--gutter,24px);bottom:20px;height:2px;background:rgba(255,255,255,.22)}
.film__bar i{display:block;height:100%;width:100%;background:#fff;transform-origin:0 50%;transform:scaleX(var(--film-q,0))}
@media (prefers-reduced-motion:reduce){.hero--film{height:100svh}}
"""

SCRIPT = r"""
(() => {
  const hero = document.querySelector('.hero--film');
  if (!hero) return;
  const n = +hero.dataset.count, base = hero.dataset.frames, labels = JSON.parse(hero.dataset.labels || '[]');
  const canvas = hero.querySelector('canvas'), ctx = canvas.getContext('2d');
  const step = hero.querySelector('.film__step'), name = hero.querySelector('.film__name'), num = hero.querySelector('.film__num');
  const pad = i => String(i + 1).padStart(3, '0');
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const frames = new Array(n);
  let current = -1, label = -1;
  function draw(i) {
    let k = i; while (k > 0 && !(frames[k] && frames[k].complete && frames[k].naturalWidth)) k--;
    const img = frames[k]; if (!img || !img.complete || !img.naturalWidth) return;
    const w = canvas.clientWidth, h = canvas.clientHeight, d = Math.min(2, devicePixelRatio || 1);
    if (canvas.width !== Math.round(w * d)) { canvas.width = Math.round(w * d); canvas.height = Math.round(h * d); }
    const s = Math.max(canvas.width / img.naturalWidth, canvas.height / img.naturalHeight);
    const dw = img.naturalWidth * s, dh = img.naturalHeight * s;
    ctx.drawImage(img, (canvas.width - dw) / 2, (canvas.height - dh) / 2, dw, dh);
    hero.classList.add('is-live');
  }
  function load(i) { if (frames[i]) return; const im = new Image(); im.decoding = 'async'; im.src = base + 'f' + pad(i) + '.webp';
    im.onload = () => { if (i === current) draw(i); }; frames[i] = im; }
  function update() {
    const r = hero.getBoundingClientRect();
    const q = reduce ? 1 : Math.min(1, Math.max(0, -r.top / Math.max(1, r.height - innerHeight)));
    const i = Math.round(q * (n - 1));
    hero.style.setProperty('--film-q', q.toFixed(4));
    if (i !== current) { current = i; load(i); draw(i); }
    const l = Math.min(labels.length - 1, Math.floor(q * labels.length * .999));
    if (l !== label && labels.length) { label = l; name.textContent = labels[l]; num.textContent = String(l + 1).padStart(2, '0');
      step.classList.remove('flip'); void step.offsetWidth; step.classList.add('flip'); }
  }
  // Load key frames first (every 8th), then the rest, so scrubbing never waits long.
  for (let i = 0; i < n; i += 8) load(i);
  setTimeout(() => { for (let i = 0; i < n; i++) load(i); }, 400);
  addEventListener('scroll', () => requestAnimationFrame(update), {passive: true});
  addEventListener('resize', () => { canvas.width = 0; draw(current); });
  update();
})();
"""


def stage_frames(frames: list[Path], out_dir: Path, folder: str = "assets/film") -> str:
    """Copy f001.webp.. into the site; return the relative prefix."""
    target = Path(out_dir) / folder
    target.mkdir(parents=True, exist_ok=True)
    for index, frame in enumerate(sorted(frames)):
        shutil.copyfile(frame, target / f"f{index + 1:03d}.webp")
    return folder + "/"


def hero_html(*, prefix: str, count: int, labels: list[str], headline_html: str, body_html: str,
              note: str, alt: str) -> str:
    labels_json = html.escape(json.dumps(labels, ensure_ascii=False), quote=True)
    first = html.escape(labels[0]) if labels else ""
    return f'''
<section class="hero hero--film" data-frames="{prefix}" data-count="{count}" data-labels="{labels_json}" aria-labelledby="otsikko">
 <div class="film__stage">
  <img class="film__poster" src="{prefix}f{count:03d}.webp" alt="{html.escape(alt)}">
  <canvas aria-hidden="true"></canvas>
  <p class="film__step" aria-hidden="true"><span class="film__num">01</span><span class="film__name">{first}</span></p>
  <div class="film__copy">{headline_html}{body_html}</div>
  <p class="film__note">{html.escape(note)}</p>
  <div class="film__bar" aria-hidden="true"><i></i></div>
 </div>
</section>'''

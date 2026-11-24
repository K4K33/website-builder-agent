"""Scroll stories: the hero animation as a designed sequence, for any business.

The reference sites do not animate decoration; they animate the business's own
transformation (a house is built, a room renovated, a product assembled) and
let the scroll drive it. The builder designs that sequence like a short film:

1. find the one transformation that IS the business (before -> after),
2. storyboard it in 4-5 beats that each add visible, physical change,
3. give every moving element a scroll window (data-k="start,end"),
4. hold the final frame, then reveal the copy (data-copy-after, hero_reveal).

The runtime is tiny and generic: every [data-k] element inside a [data-story]
gets --k (0..1, eased) for its window of the story's scroll progress, and CSS
turns --k into transform/opacity/clip-path. One stage caption may follow the
beats ([data-story-caption], data-stages). No canvas, no library, no layout
properties animated; reduced motion and no-JS show the finished frame.
"""
from __future__ import annotations

from bs4 import BeautifulSoup

MOTION_BRIEF = """SCROLL STORY (hero animation design, required when the hero animates):
- The protagonist is the business's own subject at production quality: its real logo/mark as a crafted
  object (studio, brand, shop), or its real transformation from real or licensed photos/video (old
  bathroom -> renovated, bare plot -> house). Abstract blobs, particles, generic parallax and CSS mock-ups
  built from grey bars, empty boxes or fake browser windows are clip-art, not a story; never animate them.
- Award-site scale and depth (THE LINE, Dropbox Brand, Lando Norris): frame 0 is already a poster -
  the subject fills or crosses the viewport, cropped, close to the camera. Scrolling pulls back, assembles
  or transforms it in 3D (perspective + translateZ/rotate, depth blur that sharpens, one light sweep when
  it locks). Small centred objects in an empty dark stage read as a template.
- Storyboard 3-5 beats; every scroll interval changes something visible (no dead stretch longer than
  ~12 % of the scroll). Big moves early, details late, then a short hold of the finished frame.
- Show, don't label: no step captions ("Step 1", "Purku") unless the change cannot be read without them;
  at most one small line. Headline, text and the call button wait ([data-hero-copy],
  data-hide-while-building) until the final frame holds, then share the frame with the subject.
- Mechanics: <section data-story data-copy-after="0.82" style="height:260-300svh"> with a position:sticky
  100svh stage. Each moving element gets data-k="a,b" (its window of scroll progress 0..1); CSS uses
  var(--k) (0..1, eased) only in transform, opacity, clip-path or filter, e.g.
  transform:translate3d(calc((1 - var(--k)) * 30vw),0,calc((1 - var(--k)) * 400px)).
  Vector or high-resolution media only: a logo is redrawn as SVG (gradients, edge highlight, thickness),
  never an upscaled bitmap.
- Mobile first: the poster frame and the final frame both work at 360px wide; reduced motion and no-JS
  show the final frame. The browser QA films the story and rejects empty first frames, dead stretches
  and placeholder blocks."""

STYLE = """
[data-story] [data-k]{--k:1}
[data-story].is-js [data-k]{--k:0}
[data-story] [data-story-caption]{transition:opacity .4s ease}
@media (prefers-reduced-motion:reduce){[data-story] [data-k]{--k:1!important}}
"""

SCRIPT = r"""
(() => {
  "use strict";
  const stories = [...document.querySelectorAll('[data-story]')];
  if (!stories.length) return;
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const ease = t => t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
  const setup = stories.map(story => {
    const items = [...story.querySelectorAll('[data-k]')].map(el => {
      const [a, b] = el.dataset.k.split(',').map(Number);
      return {el, a, b: Math.max(b, a + .001), last: -1};
    });
    let stages = [];
    try { stages = JSON.parse(story.dataset.stages || '[]'); } catch (e) { stages = []; }
    story.classList.add('is-js');
    return {story, items, stages, caption: story.querySelector('[data-story-caption]'), last: -1};
  });
  function frame() {
    for (const s of setup) {
      const r = s.story.getBoundingClientRect(), room = Math.max(1, r.height - innerHeight);
      const p = reduce ? 1 : Math.min(1, Math.max(0, -r.top / room));
      if (Math.abs(p - s.last) < .0004) continue;
      s.last = p;
      s.story.style.setProperty('--p', p.toFixed(4));
      for (const it of s.items) {
        const k = ease(Math.min(1, Math.max(0, (p - it.a) / (it.b - it.a))));
        if (Math.abs(k - it.last) > .0005) { it.last = k; it.el.style.setProperty('--k', k.toFixed(4)); }
      }
      if (s.caption && s.stages.length) {
        const en = document.documentElement.lang === 'en';
        let text = '';
        for (const st of s.stages) if (p >= st[0]) text = (en && st[2]) || st[1];
        if (s.caption.textContent !== text) s.caption.textContent = text;
      }
    }
  }
  let queued = false;
  const request = () => { if (!queued) { queued = true; requestAnimationFrame(() => { queued = false; frame(); }); } };
  addEventListener('scroll', request, {passive: true});
  addEventListener('resize', request);
  new MutationObserver(request).observe(document.documentElement, {attributes: true, attributeFilter: ['lang']});
  frame();
})();
"""


def enhance_scroll_story(html: str) -> str:
    """Add the scroll-story runtime to a page that uses [data-story] (idempotent)."""
    if "data-story" not in html:
        return html
    soup = BeautifulSoup(html, "html.parser")
    for item in soup.select("style[data-kaurivo-story-runtime], script[data-kaurivo-story-runtime]"):
        item.decompose()
    if not soup.select("[data-story] [data-k]") or not (soup.head and soup.body):
        return html
    for name, code, parent in (("style", STYLE, soup.head), ("script", SCRIPT, soup.body)):
        tag = soup.new_tag(name, attrs={"data-kaurivo-story-runtime": ""})
        tag.string = code
        parent.append(tag)
    return str(soup)


# Browser evidence for QA: film the story and reject the failure modes that
# made earlier heroes look cheap (empty poster frame, dead scroll stretches,
# wireframe placeholder blocks, copy that never arrives).
AUDIT_POSITIONS = (0.0, 0.15, 0.3, 0.45, 0.6, 0.75, 0.9, 1.0)

_STORY_STATE = r"""story => {
  const vw = innerWidth, vh = innerHeight;
  const visible = el => { const r = el.getBoundingClientRect(), s = getComputedStyle(el);
    return r.width > 1 && r.height > 1 && r.bottom > 0 && r.right > 0 && r.top < vh && r.left < vw &&
      s.visibility !== 'hidden' && +s.opacity > .05; };
  let minX = vw, minY = vh, maxX = 0, maxY = 0, any = false;
  for (const el of story.querySelectorAll('[data-k]')) {
    if (!visible(el) || el.closest('[data-hero-copy]')) continue;
    const r = el.getBoundingClientRect(); any = true;
    minX = Math.min(minX, Math.max(0, r.left)); minY = Math.min(minY, Math.max(0, r.top));
    maxX = Math.max(maxX, Math.min(vw, r.right)); maxY = Math.max(maxY, Math.min(vh, r.bottom));
  }
  const coverage = any ? (maxX - minX) * (maxY - minY) / (vw * vh) : 0;
  const media = 'img,svg,video,canvas,picture,polygon,path';
  const placeholders = [...story.querySelectorAll('*')].filter(el => {
    if (el.children.length || el.closest('svg') || el.matches(media) || el.closest('[data-hero-copy]')) return false;
    if ((el.textContent || '').trim()) return false;
    const s = getComputedStyle(el), r = el.getBoundingClientRect();
    return visible(el) && r.width * r.height > 300 && s.backgroundImage === 'none' &&
      !/rgba\(0, 0, 0, 0\)|transparent/.test(s.backgroundColor);
  }).length;
  const copy = story.querySelector('[data-hero-copy]');
  return {coverage, placeholders, copy: copy ? +getComputedStyle(copy).opacity : null};
}"""


def audit_scroll_story(page, *, output_dir, viewport):
    """Film each [data-story] at fixed progress points; return issues and a filmstrip."""
    from io import BytesIO
    from PIL import Image, ImageChops, ImageStat

    issues, observations = [], []
    page.emulate_media(reduced_motion="no-preference")
    page.reload(wait_until="load")
    stories = page.locator("[data-story]")
    for index in range(stories.count()):
        story = stories.nth(index)
        label = f"scroll story {index + 1}"
        try:
            frames, states = [], []
            for position in AUDIT_POSITIONS:
                story.evaluate("""(story, position) => {
                    const top = story.getBoundingClientRect().top + scrollY;
                    scrollTo({top: top + position * Math.max(0, story.offsetHeight - innerHeight), behavior: 'instant'});
                }""", position)
                page.wait_for_timeout(260)
                page.evaluate("new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)))")
                states.append(story.evaluate(_STORY_STATE))
                frames.append(Image.open(BytesIO(page.screenshot(animations="disabled"))).convert("RGB"))
            if states[0]["coverage"] < 0.12:
                issues.append(f"{label}: first frame is nearly empty (subject covers "
                              f"{states[0]['coverage']:.0%} of the viewport); make frame 0 a poster.")
            small = [f.convert("L").resize((160, max(1, round(160 * f.height / f.width)))) for f in frames]
            # every interval up to the final hold must visibly change something
            for a, b, pa, pb in zip(small[:-2], small[1:-1], AUDIT_POSITIONS, AUDIT_POSITIONS[1:]):
                change = ImageStat.Stat(ImageChops.difference(a, b)).mean[0]
                if change < 0.6:
                    issues.append(f"{label}: nothing visible changes between {pa:.0%} and {pb:.0%} of the scroll.")
            worst = max(state["placeholders"] for state in states)
            if worst >= 5:
                issues.append(f"{label}: {worst} empty placeholder blocks (grey bars/boxes) in the story; "
                              "animate the real subject, not a wireframe mock-up.")
            if states[-1]["copy"] is not None and states[-1]["copy"] < 0.9:
                issues.append(f"{label}: headline and call to action are not visible on the final frame.")
            thumbs = []
            for frame in frames:
                frame.thumbnail((360, 360))
                thumbs.append(frame)
            strip = Image.new("RGB", (sum(t.width for t in thumbs), max(t.height for t in thumbs)))
            offset = 0
            for thumb in thumbs:
                strip.paste(thumb, (offset, 0))
                offset += thumb.width
            output_dir.mkdir(parents=True, exist_ok=True)
            path = output_dir / f"{viewport}-scroll-story-{index + 1}.jpg"
            strip.save(path, quality=86)
            observations.append({"category": "scroll_story", "viewport": viewport, "sequence": index + 1,
                                 "filmstrip": str(path),
                                 "states": "Progress " + ", ".join(f"{p:.0%}" for p in AUDIT_POSITIONS),
                                 "note": "Browser frames of the scroll story. Judge whether frame 0 "
                                         "is a poster, the subject is the business's own, and the build reads "
                                         "as crafted motion rather than a wireframe."})
        except Exception as error:
            issues.append(f"{label}: playback inspection failed ({type(error).__name__}).")
    page.emulate_media(reduced_motion="reduce")
    page.reload(wait_until="load")
    return {"issues": issues, "observations": observations}

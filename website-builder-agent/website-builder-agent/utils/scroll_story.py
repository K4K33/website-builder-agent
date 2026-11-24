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
- Find the ONE transformation that is this business's work (old bathroom -> renovated, bare plot ->
  finished house, messy garden -> landscaped, dull hair -> styled, old website -> new website). Animate
  that, not decoration. Abstract blobs, floating particles and generic parallax are not a story.
- Storyboard 4-5 beats; every beat adds VISIBLE, physical change (parts come off, structure appears,
  material goes on, details land, the result is shown). Order follows how the work really happens.
- Mechanics: <section data-story data-copy-after="0.88" data-stages='[[0,"Lähtötilanne","Before"],...]'
  style="height:380svh"> with a position:sticky 100svh stage. Each moving element gets data-k="a,b"
  (its window of scroll progress 0..1) and CSS uses var(--k) (0..1, eased) only in transform, opacity,
  clip-path or filter, e.g. transform:translateY(calc((1 - var(--k)) * 40px));opacity:var(--k).
- Stagger windows (each element ~0.08-0.15 long, overlapping) so motion reads as one continuous build;
  big moves early, details late; nothing moves after the final beat.
- During the story only one small stage caption ([data-story-caption]); headline, text and the call
  button wait ([data-hero-copy], data-hide-while-building) until the final frame holds.
- Mobile first: the stage must read at 360px wide; reduced motion and no-JS show the final frame."""

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

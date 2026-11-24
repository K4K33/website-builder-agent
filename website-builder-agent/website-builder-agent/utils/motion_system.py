"""Page-wide scroll motion: the whole page moves with the scroll, not only the hero.

Studied on award and category-leader sites (Squarespace home 11/2026, THE LINE,
Dropbox Brand): premium feel comes from every section having ONE scroll-linked
motion idea, all driven by the same smoothed scroll value, never from timed
fade-ups. This module gives every built page that system automatically:

- smoothing: displayed progress glides toward the real scroll position
  (lerp per frame), so wheel steps never jump; native scrolling is untouched
- rise: section headings come up through a mask as they enter
- media: images open from an inset frame to full size while the photo settles
- stagger: sibling cards/rows arrive one after another
- wall: a gallery becomes a 3D wall the camera passes through ([data-depth-wall])
- tone: the page background blends between section colours ([data-tone])
- hover: cards lift and their image breathes

Elements get --v (0..1, eased) as they enter the viewport; CSS uses only the
individual `translate`/`scale` properties, clip-path, opacity and filter, so it
never fights a page's own `transform`. Reduced motion and no-JS show the final
state. ``enhance_motion_system`` annotates a built page and injects the runtime
(idempotent); the hero story ([data-story]) is left to utils.scroll_story.
"""
from __future__ import annotations

from bs4 import BeautifulSoup

STYLE = """
html.mo-js [data-reveal]{--v:0}
[data-reveal]{--v:1}
[data-reveal="rise"]{clip-path:inset(-.2em -.2em calc((1 - var(--v)) * 60%) -.2em);
  translate:0 calc((1 - var(--v)) * .55em);opacity:calc(.15 + var(--v) * .85)}
[data-reveal="fade"]{translate:0 calc((1 - var(--v)) * 26px);opacity:var(--v)}
[data-reveal="media"]{clip-path:inset(calc((1 - var(--v)) * 9%) calc((1 - var(--v)) * 7%));overflow:hidden}
[data-reveal="media"] img,[data-reveal="media"] video,img[data-reveal="media"]{scale:calc(1.14 - var(--v) * .14)}
[data-reveal="stagger"]>[data-si]{--vi:clamp(0,calc(var(--v) * 1.6 - var(--i,0) * .16),1);
  translate:0 calc((1 - var(--vi)) * 54px);opacity:calc(.1 + var(--vi) * .9)}
[data-depth-wall]{perspective:900px;perspective-origin:50% 40%;overflow:hidden}
[data-depth-wall]>*{transform-style:preserve-3d;
  transform:translateZ(calc(-380px + var(--pass,.5) * 560px)) rotateX(calc(16deg - var(--pass,.5) * 26deg))}
[data-depth-wall] [data-col]{transform:rotateY(calc(var(--col) * -13deg)) translateZ(calc(var(--col) * var(--col) * -40px))}
.mo-card{transition:translate .5s cubic-bezier(.2,.8,.2,1),box-shadow .5s}
.mo-card img{transition:scale .9s cubic-bezier(.2,.8,.2,1)}
@media (hover:hover){.mo-card:hover{translate:0 -6px;box-shadow:0 22px 50px -24px rgba(0,0,0,.45)}.mo-card:hover img{scale:1.045}}
@media (prefers-reduced-motion:reduce){
  html.mo-js [data-reveal],[data-reveal]{--v:1!important}
  [data-reveal="stagger"]>[data-si]{--vi:1!important}
  [data-depth-wall]>*{transform:none}
  .mo-card,.mo-card img{transition:none}
}
"""

SCRIPT = r"""
(() => {
  "use strict";
  const root = document.documentElement;
  if (matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  // Static sites mark their script with data-auto: the same rules as annotate()
  // run here, so the HTML (and its SEO markup) never has to be rewritten.
  const me = document.currentScript;
  if (me && me.hasAttribute('data-auto')) {
    const skip = el => el.closest('header,nav,footer,form,[data-story],[data-hero-copy],[data-no-motion],[data-reveal]');
    const main = document.querySelector('main') || document.body;
    const sections = [...main.querySelectorAll('section')].filter(s => !s.parentElement.closest('section'));
    for (const section of sections.slice(1)) {
      if (section.hasAttribute('data-story') || section.hasAttribute('data-no-motion')) continue;
      for (const h of section.querySelectorAll('h2')) if (!skip(h)) h.dataset.reveal = 'rise';
      for (const parent of section.querySelectorAll('*')) {
        if (skip(parent) || parent.closest('[data-reveal="stagger"]')) continue;
        const kids = [...parent.children];
        if (kids.length < 3) continue;
        const keys = kids.map(k => [...k.classList].sort().join(' ') || k.tagName);
        const counts = {}; keys.forEach(k => counts[k] = (counts[k] || 0) + 1);
        const common = Object.keys(counts).sort((a, b) => counts[b] - counts[a])[0];
        if (counts[common] < 3 || counts[common] < kids.length * .6) continue;
        parent.dataset.reveal = 'stagger';
        kids.filter((k, i) => keys[i] === common).forEach((k, i) => {
          k.setAttribute('data-si', ''); k.style.setProperty('--i', i);
          if (k.querySelector('img,picture,video') && (k.tagName === 'A' || k.querySelector('a'))) k.classList.add('mo-card');
        });
      }
      for (const m of section.querySelectorAll('img,picture,video')) {
        if (skip(m) || m.closest('[data-depth-wall]') || (m.width && m.width < 280)) continue;
        let frame = ['FIGURE', 'PICTURE', 'DIV'].includes(m.parentElement.tagName) ? m.parentElement : m;
        if (frame.tagName === 'PICTURE') frame = frame.parentElement;
        if (!frame.hasAttribute('data-reveal')) frame.dataset.reveal = 'media';
      }
    }
  }
  root.classList.add('mo-js');
  const ease = t => 1 - Math.pow(1 - t, 3);
  const items = [...document.querySelectorAll('[data-reveal],[data-depth-wall]')].map(el => ({el, cur: -1, wall: el.hasAttribute('data-depth-wall')}));
  const tones = [...document.querySelectorAll('[data-tone]')];
  let toneCur = null, running = false;
  const target = it => {
    const r = it.el.getBoundingClientRect(), vh = innerHeight;
    if (it.wall) return Math.min(1, Math.max(0, (vh - r.top) / (vh + r.height)));
    return ease(Math.min(1, Math.max(0, (vh - r.top) / (vh * .6))));
  };
  const hex = c => [1, 3, 5].map(i => parseInt(c.slice(i, i + 2), 16));
  function toneTarget() {
    let best = null, bestDist = 1e9;
    const mid = innerHeight * .55;
    for (const s of tones) {
      const r = s.getBoundingClientRect();
      const d = r.top <= mid && r.bottom >= mid ? 0 : Math.min(Math.abs(r.top - mid), Math.abs(r.bottom - mid));
      if (d < bestDist) { bestDist = d; best = s; }
    }
    return best && /^#[0-9a-f]{6}$/i.test(best.dataset.tone) ? hex(best.dataset.tone) : null;
  }
  function frame() {
    let moving = false;
    for (const it of items) {
      const t = target(it);
      const next = it.cur < 0 ? t : it.cur + (t - it.cur) * .16;
      if (Math.abs(next - t) > .0008) moving = true;
      const v = Math.abs(next - t) > .0008 ? next : t;
      if (Math.abs(v - it.cur) > .0004) {
        it.cur = v;
        it.el.style.setProperty(it.wall ? '--pass' : '--v', v.toFixed(4));
      }
    }
    if (tones.length) {
      const t = toneTarget();
      if (t) {
        toneCur = toneCur ? toneCur.map((c, i) => c + (t[i] - c) * .12) : t;
        if (toneCur.some((c, i) => Math.abs(c - t[i]) > .5)) moving = true;
        document.body.style.backgroundColor = `rgb(${toneCur.map(Math.round).join(',')})`;
      }
    }
    running = moving;
    if (moving) requestAnimationFrame(frame);
  }
  const kick = () => { if (!running) { running = true; requestAnimationFrame(frame); } };
  addEventListener('scroll', kick, {passive: true});
  addEventListener('resize', kick);
  frame();
})();
"""

MOTION_SYSTEM_BRIEF = """PAGE-WIDE MOTION (every section, not only the hero; utils.motion_system adds the runtime):
- Each section gets ONE scroll-linked motion idea that fits its content: headings rise through a mask
  (data-reveal="rise"), key images open from an inset frame (data-reveal="media"), rows of cards/services
  arrive one after another (data-reveal="stagger" on their parent), a gallery of work becomes a 3D wall
  the camera passes through (data-depth-wall with children marked data-col="-2..2"), and sections may set
  data-tone="#hex" so the page background blends between section colours as you scroll.
- Motion is scroll-linked and smoothed, never a timed fade-up per block; small text and buttons do not move.
- Interactive elements answer the cursor (cards lift, images breathe); nothing loops without purpose."""

_SKIP = "header, nav, footer, [data-story], [data-hero-copy], form, [data-no-motion]"
_MEDIA = ("img", "picture", "video")


def _skippable(tag) -> bool:
    return bool(tag.find_parent(["header", "nav", "footer", "form"])) or any(
        tag.find_parent(attrs={a: True}) is not None or tag.has_attr(a)
        for a in ("data-story", "data-hero-copy", "data-no-motion", "data-reveal"))


def annotate(soup: BeautifulSoup) -> int:
    """Mark headings, large media and card groups below the hero. Returns how many were marked."""
    main = soup.find("main") or soup.body
    if main is None:
        return 0
    sections = [s for s in main.find_all("section") if not s.find_parent("section")]
    below = sections[1:] if sections else []
    count = 0
    for section in below:
        if section.has_attr("data-story") or section.has_attr("data-no-motion"):
            continue
        for h in section.find_all("h2"):
            if not _skippable(h):
                h["data-reveal"] = "rise"
                count += 1
        # rows of similar siblings (cards, services, price rows) arrive in turn
        for parent in section.find_all(True):
            if _skippable(parent) or parent.name in ("ul", "ol") and parent.find_parent("nav"):
                continue
            kids = [c for c in parent.find_all(recursive=False) if c.name]
            if len(kids) < 3:
                continue
            classes = [" ".join(sorted(c.get("class") or [])) or c.name for c in kids]
            common = max(set(classes), key=classes.count)
            if classes.count(common) >= 3 and classes.count(common) >= len(kids) * .6 \
                    and not parent.find_parent(attrs={"data-reveal": "stagger"}):
                parent["data-reveal"] = "stagger"
                for i, kid in enumerate(k for k, c in zip(kids, classes) if c == common):
                    kid["data-si"] = ""
                    kid["style"] = (kid.get("style", "").rstrip(";") + f";--i:{i}").lstrip(";")
                    if kid.find(_MEDIA) and kid.find("a") or kid.name == "a" and kid.find(_MEDIA):
                        kid["class"] = (kid.get("class") or []) + ["mo-card"]
                count += 1
        for media in section.find_all(_MEDIA):
            if _skippable(media) or media.find_parent(attrs={"data-reveal": "stagger"}) \
                    or media.find_parent(attrs={"data-depth-wall": True}):
                continue
            frame = media.parent if media.parent.name in ("figure", "picture", "div") else media
            if frame.name == "picture":
                frame = frame.parent
            width = int(str(media.get("width") or "0").rstrip("px") or 0) if str(media.get("width") or "").rstrip("px").isdigit() else 0
            if width and width < 280:
                continue
            if not frame.has_attr("data-reveal"):
                frame["data-reveal"] = "media"
                count += 1
    return count


def enhance_motion_system(html: str, *, asset_href: str | None = None, asset_src: str | None = None) -> str:
    """Annotate the page and add the runtime once. With asset paths, link shared files instead of inlining."""
    soup = BeautifulSoup(html, "html.parser")
    if not (soup.head and soup.body):
        return html
    for item in soup.select("style[data-kaurivo-motion], script[data-kaurivo-motion], link[data-kaurivo-motion]"):
        item.decompose()
    if not annotate(soup) and not soup.select("[data-reveal],[data-depth-wall],[data-tone]"):
        return str(soup)
    if asset_href and asset_src:
        soup.head.append(soup.new_tag("link", attrs={"rel": "stylesheet", "href": asset_href, "data-kaurivo-motion": ""}))
        soup.body.append(soup.new_tag("script", attrs={"src": asset_src, "defer": "", "data-kaurivo-motion": ""}))
    else:
        style = soup.new_tag("style", attrs={"data-kaurivo-motion": ""})
        style.string = STYLE
        script = soup.new_tag("script", attrs={"data-kaurivo-motion": ""})
        script.string = SCRIPT
        soup.head.append(style)
        soup.body.append(script)
    return str(soup)

"""Kinetic type band: the company's own words as giant type that moves on scroll.

Award sites often pace a page with one band of huge words (a trade's
services, a product's qualities) whose lines slide in opposite directions as
the visitor scrolls. The builder makes it from verified words only: the
author writes the words once, the builder repeats them to fill the width,
alternates filled and outlined lines and drives them from scroll position.

The band is decorative (aria-hidden) and must repeat words that already
appear as real text on the page. Without JavaScript or with reduced motion
it stays still.
"""
from __future__ import annotations

import html as html_lib
import re

from bs4 import BeautifulSoup

KINETIC_BRIEF = """
KINETIC TYPE BAND (optional, at most one per page, for pacing between two
sections). Only words that ALSO appear as real text on the page (service
names, the trade, the town), 2-6 short items, 1-3 words each:

<section data-kaurivo-kinetic aria-hidden="true">
  <p data-kinetic-line>Service one|Service two|Service three</p>
  <p data-kinetic-line>Service four|Service five</p>
</section>

The builder repeats, sizes and moves the lines on scroll (opposite
directions, outlined and filled). Never put claims, prices or numbers in it.
""".strip()

MAX_ITEM = 28
STYLE = """
[data-kaurivo-kinetic]{overflow:hidden;padding:clamp(40px,9vh,110px) 0;contain:paint}
[data-kaurivo-kinetic] [data-kinetic-line]{margin:0;white-space:nowrap;line-height:.92;font-size:clamp(56px,11vw,190px);
 transform:translate3d(var(--kinetic-x,0),0,0);will-change:transform}
[data-kaurivo-kinetic] [data-kinetic-line]:nth-child(even){-webkit-text-fill-color:transparent;-webkit-text-stroke:max(1.5px,.014em) currentColor}
[data-kaurivo-kinetic] .kinetic__dot{display:inline-block;width:.16em;height:.16em;margin:0 .32em;border-radius:50%;
 vertical-align:.22em;background:var(--kinetic-dot,currentColor)}
"""
SCRIPT = r"""
(() => {
  const bands = [...document.querySelectorAll('[data-kaurivo-kinetic][data-kinetic-active]')];
  if (!bands.length || matchMedia('(prefers-reduced-motion: reduce)').matches) return;
  let ticking = false;
  function update() {
    ticking = false;
    const vh = innerHeight;
    for (const band of bands) {
      const r = band.getBoundingClientRect();
      if (r.bottom < -vh || r.top > vh * 2) continue;
      const q = (vh - r.top) / (vh + r.height);           // 0 entering .. 1 leaving
      band.querySelectorAll('[data-kinetic-line]').forEach((line, i) => {
        const span = Math.max(0, line.scrollWidth - innerWidth) * .5;
        const x = i % 2 ? -span * (1 - q) : -span * q;
        line.style.setProperty('--kinetic-x', x.toFixed(1) + 'px');
      });
    }
  }
  addEventListener('scroll', () => { if (!ticking) { ticking = true; requestAnimationFrame(update); } }, {passive: true});
  addEventListener('resize', update);
  update();
})();
"""


def items(text: str) -> list[str]:
    parts = [" ".join(p.split()) for p in str(text or "").split("|")]
    return [p for p in parts if 0 < len(p) <= MAX_ITEM and not re.search(r"\d", p)]


def band_html(words: list[str], *, lines: int = 2) -> str:
    """Author markup for a band from verified words (alternating lines)."""
    words = [w for w in (" ".join(str(x).split()) for x in words) if 0 < len(w) <= MAX_ITEM
             and not re.search(r"\d", w)]
    if len(words) < 2:
        return ""
    rows = [words[i::lines] for i in range(lines)]
    rows = [r for r in rows if r]
    body = "".join(f'<p data-kinetic-line>{html_lib.escape("|".join(r))}</p>' for r in rows)
    return f'<section data-kaurivo-kinetic aria-hidden="true">{body}</section>'


def enhance_kinetic_type(html: str) -> str:
    if "data-kaurivo-kinetic" not in html:
        return html
    soup = BeautifulSoup(html, "html.parser")
    page_text = " ".join(t for t in soup.find_all(string=True)
                         if not t.find_parent(attrs={"data-kaurivo-kinetic": True})
                         and t.parent.name not in ("script", "style")).casefold()
    active = 0
    for band in soup.select("[data-kaurivo-kinetic]"):
        band.attrs.pop("data-kinetic-active", None)
        band["aria-hidden"] = "true"
        lines = band.select("[data-kinetic-line]")
        ok_lines = 0
        for line in lines:
            raw = line.get("data-kinetic-source") or line.get_text("|")
            # Only words that also stand on the page as real text.
            words = [w for w in items(raw) if w.casefold() in page_text]
            line.clear()
            if not words:
                line.decompose()
                continue
            line["data-kinetic-source"] = "|".join(words)
            # Repeat to fill wide screens (min ~60 characters per line).
            reps = max(2, -(-60 // max(1, len(" ".join(words)))))
            for index, word in enumerate(words * reps):
                if index:
                    line.append(soup.new_tag("span", attrs={"class": "kinetic__dot"}))
                line.append(word)
            ok_lines += 1
        if active or ok_lines == 0:
            band.decompose()
            continue
        band["data-kinetic-active"] = ""
        active += 1
    for item in soup.select("style[data-kaurivo-kinetic-runtime], script[data-kaurivo-kinetic-runtime]"):
        item.decompose()
    if active and soup.head and soup.body:
        for name, code, parent in (("style", STYLE, soup.head), ("script", SCRIPT, soup.body)):
            tag = soup.new_tag(name, attrs={"data-kaurivo-kinetic-runtime": ""})
            tag.string = code
            parent.append(tag)
    return re.sub(r"\A(<!DOCTYPE[^>]+>)\s*", r"\1\n", str(soup), flags=re.I)

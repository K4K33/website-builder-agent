"""Hero choreography shared by every hero: the visual first, the words last.

Award heroes open with the image or animation alone; the headline, text and
call arrive only when the visitor has scrolled the animation through (a house
is built, a word slides behind the subject, a room is renovated). Any hero
marked data-copy-after="0.8" hides its [data-hero-copy] until that share of
its scroll has passed. Without JavaScript, with reduced motion or for a hero
with no scroll room the copy is simply shown; screen readers always get it.
"""
from __future__ import annotations

import re

from bs4 import BeautifulSoup

STYLE = """
[data-copy-after] [data-hero-copy]{transition:opacity .9s cubic-bezier(.16,1,.3,1),transform 1s cubic-bezier(.16,1,.3,1)}
[data-copy-after].is-js:not(.is-done) [data-hero-copy]{opacity:0!important;transform:translateY(28px)!important;pointer-events:none}
/* Page chrome that would compete with the animation (the call button) waits too. */
[data-hide-while-building]{transition:opacity .8s ease,transform .8s ease}
html.hero-building [data-hide-while-building]{opacity:0;transform:translateY(-8px);pointer-events:none}
"""

SCRIPT = r"""
(() => {
  const heroes = [...document.querySelectorAll('[data-copy-after]')];
  if (!heroes.length) return;
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  function update() {
    let building = false;
    for (const h of heroes) {
      const r = h.getBoundingClientRect(), room = r.height - innerHeight;
      const at = Math.min(.95, Math.max(.1, +h.dataset.copyAfter || .8));
      // A hero without scroll room (no animation to finish) shows its copy at once.
      const done = reduce || room < innerHeight * .25 || -r.top / room >= at;
      h.classList.toggle('is-done', done);
      if (r.top < innerHeight && r.bottom > 0 && !done) building = true;
    }
    document.documentElement.classList.toggle('hero-building', building);
  }
  heroes.forEach(h => h.classList.add('is-js'));
  addEventListener('scroll', () => requestAnimationFrame(update), {passive: true});
  addEventListener('resize', update);
  update();
})();
"""


def enhance_hero_reveal(html: str) -> str:
    if "data-copy-after" not in html:
        return html
    soup = BeautifulSoup(html, "html.parser")
    for item in soup.select("style[data-kaurivo-reveal-runtime], script[data-kaurivo-reveal-runtime]"):
        item.decompose()
    if not soup.select("[data-copy-after] [data-hero-copy]") or not (soup.head and soup.body):
        return html
    for name, code, parent in (("style", STYLE, soup.head), ("script", SCRIPT, soup.body)):
        tag = soup.new_tag(name, attrs={"data-kaurivo-reveal-runtime": ""})
        tag.string = code
        parent.append(tag)
    return re.sub(r"\A(<!DOCTYPE[^>]+>)\s*", r"\1\n", str(soup), flags=re.I)


REVEAL_BRIEF = """
HERO CHOREOGRAPHY (every hero with a scroll animation: scrub, film, typecut,
product): the visual plays alone first; the words come last. Put
data-copy-after="0.8" on the hero <section> and data-hero-copy on the one
element that holds the h1, text and call. The builder hides that copy until
80 % of the hero's scroll has passed. Never place text over the animation
while it is still building.
""".strip()

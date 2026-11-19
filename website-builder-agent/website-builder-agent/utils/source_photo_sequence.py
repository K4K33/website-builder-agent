"""Progressive enhancement for an optional, source-backed photo sequence."""

from pathlib import PurePosixPath
from posixpath import normpath
import re
from urllib.parse import urlsplit

from bs4 import BeautifulSoup


PHOTO_SEQUENCE_BRIEF = """
A source photo sequence is optional. Use it only for verified related images
(e.g. the same project's phases), with an intentional crop for desktop and
phone. Verify their relationship from the source; do not infer construction
stages from unrelated photos. Place this ordinary HTML inside your own layout:

<section aria-labelledby="project-heading">
  <h2 id="project-heading">Actual project heading</h2>
  <div data-kaurivo-photo-sequence>
    <div data-kaurivo-photo-stage>
      <figure><img src="assets/first.webp" alt="…"><figcaption>…</figcaption></figure>
      <figure><img src="assets/second.webp" alt="…"><figcaption>…</figcaption></figure>
    </div>
  </div>
  <!-- Normal content and links outside the moving stage -->
</section>

Use two to four distinct, staged still photographs. Use normal img tags with
actual paths, alt text and plain-text captions; no linked or interactive figures.
Set each image's object-position in your own responsive CSS where necessary.
Author a good static layout for the figures as well. The builder supplies
scroll playback automatically. Never implement a replay-only zoom as a
substitute. With insufficient material, use a well-composed still or preserve a
verified source video/gallery where appropriate.
""".strip()

_STYLE = """
[data-kaurivo-photo-sequence][data-photo-active] {
  block-size: calc(90svh + var(--photo-distance));
}
[data-photo-active] > [data-kaurivo-photo-stage] {
  position: sticky;
  inset-block-start: 10svh;
  block-size: var(--photo-hold);
  display: grid;
  grid-template: minmax(0,1fr) / minmax(0,1fr);
  gap: 0;
  overflow: hidden;
  isolation: isolate;
}
[data-photo-active] > [data-kaurivo-photo-stage] > figure {
  grid-area: 1 / 1;
  display: grid;
  grid-template-rows: minmax(0,1fr) auto;
  margin: 0;
  min-block-size: 0;
  opacity: var(--photo-opacity,0);
}
[data-photo-active] > [data-kaurivo-photo-stage] > figure > img {
  inline-size: 100%;
  block-size: 100%;
  min-block-size: 0;
  object-fit: cover;
}
[data-photo-active] > [data-kaurivo-photo-stage] > figure > figcaption {
  position: absolute;
  inset: auto 0 0;
  margin: 0;
  padding: .65em 1em;
  background: #151515;
  color: white;
}
"""

_SCRIPT = """
(() => {
  const preference = matchMedia('(prefers-reduced-motion: reduce)');
  if (!('IntersectionObserver' in window) || !CSS.supports('height', '1svh')) return;
  const scenes = [...document.querySelectorAll('[data-kaurivo-photo-sequence="ready"]')].map(scene => ({
    scene, stage: scene.firstElementChild,
    figures: [...scene.firstElementChild.children],
    ready: false
  }));
  let queued = false;

  function update() {
    queued = false;
    for (const {scene, stage, figures, ready} of scenes) {
      if (preference.matches || !ready) {
        scene.removeAttribute('data-photo-active');
        continue;
      }
      scene.style.setProperty('--photo-hold', '72svh');
      scene.style.setProperty('--photo-distance', `${(figures.length - 1) * 62}svh`);
      scene.setAttribute('data-photo-active', '');
      const start = parseFloat(getComputedStyle(stage).top);
      const distance = scene.offsetHeight - stage.offsetHeight * 1.25;
      const relative = (start - scene.getBoundingClientRect().top) / Math.max(1, distance);
      const progress = Math.max(0, Math.min(1, relative)) * (figures.length - 1);
      const current = Math.floor(progress);
      const fraction = progress - current;
      // The outgoing frame remains opaque under the incoming frame. This
      // avoids dimming both photos against the page background mid-fade.
      figures.forEach((figure, index) => {
        const fade = fraction * fraction * (3 - 2 * fraction);
        figure.style.setProperty('--photo-opacity',
          index === current ? 1 : index === current + 1 ? fade : 0);
      });
    }
  }

  function schedule() {
    if (queued) return;
    queued = true;
    requestAnimationFrame(update);
  }

  for (const record of scenes) {
    const images = record.figures.map(figure => figure.firstElementChild);
    const observer = new IntersectionObserver(entries => {
      if (!entries.some(entry => entry.isIntersecting)) return;
      observer.disconnect();
      images.forEach(image => { image.loading = 'eager'; });
      Promise.all(images.map(image => image.decode())).then(() => {
        record.ready = true;
        schedule();
      }).catch(() => {}); // Preserve the normal HTML if media cannot decode.
    }, {rootMargin: '50% 0px'});
    observer.observe(record.scene);
  }
  addEventListener('scroll', schedule, {passive: true});
  addEventListener('resize', schedule, {passive: true});
  preference.addEventListener('change', schedule);
})();
"""


def enhance_photo_sequence(html: str, *, route: str, media: list[dict]) -> str:
    """Attach playback only to well-formed sequences using staged stills."""
    if "data-kaurivo-photo-sequence" not in html:
        return html
    soup = BeautifulSoup(html, "html.parser")
    allowed = {
        item["src"]: item["sha256"] for item in media
        if PurePosixPath(item["src"]).suffix.lower() in {".jpg", ".jpeg", ".png", ".webp", ".avif"}
    }
    ready = False
    for scene in soup.select("[data-kaurivo-photo-sequence]"):
        # Revisions can contain the previously assembled page.
        scene.attrs.pop("data-photo-active", None)
        scene.attrs.pop("data-kaurivo-photo-sequence", None)
        if scene.find_parent("main") is None or len(scene.find_all(recursive=False)) != 1:
            continue
        stage = scene.find(recursive=False)
        if not stage.has_attr("data-kaurivo-photo-stage"):
            continue
        figures = stage.find_all(recursive=False)
        if not 2 <= len(figures) <= 4:
            continue
        digests = set()
        images = []
        for figure in figures:
            children = figure.find_all(recursive=False)
            if figure.name != "figure" or [child.name for child in children] != ["img", "figcaption"]:
                break
            image, caption = children
            if not image.get("alt", "").strip() or not caption.get_text(strip=True) or caption.find(True):
                break
            try:
                src = urlsplit(image.get("src") or "")
            except ValueError:
                break
            if src.scheme or src.netloc or src.path.startswith("/") or src.query or src.fragment:
                break
            digest = allowed.get(normpath(str(PurePosixPath(route).parent / src.path)))
            if not digest:
                break
            images.append(image)
            digests.add(digest)
        if len(digests) != len(figures):
            continue
        for image in images:
            # Every state must use its verified asset on phones as well.
            image.attrs.pop("srcset", None)
            image.attrs.pop("sizes", None)
        scene["data-kaurivo-photo-sequence"] = "ready"
        ready = True

    for item in soup.select("style[data-kaurivo-photo-runtime], script[data-kaurivo-photo-runtime]"):
        item.decompose()
    if ready and soup.head and soup.body:
        for name, code, parent in (("style", _STYLE, soup.head), ("script", _SCRIPT, soup.body)):
            tag = soup.new_tag(name, attrs={"data-kaurivo-photo-runtime": ""})
            tag.string = code
            parent.append(tag)
    return re.sub(r"\A(<!DOCTYPE[^>]+>)\s*", r"\1\n", str(soup))

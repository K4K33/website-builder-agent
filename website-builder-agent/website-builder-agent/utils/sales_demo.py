"""Kaurivo sales demo: one premium homepage per prospect, built in minutes.

The heavy pipeline (deep research, three concepts, independent review) is for
paying or interested customers. A sales email needs one striking page of the
company's OWN name, services and photos. Here a free model is asked once to
fill a small JSON content plan from the verified source text; everything
visual is deterministic and tested:

- palette from the company's photos (utils.award_playbook)
- one of three licensed type pairings chosen by trade
- signature hero: depth scene or blueprint build (utils.scroll_scrub)
- services as a typographic index with photo reveal, a photo that grows to
  full bleed, the phone number as the closing headline
- a visible note that this is a Kaurivo draft, not the official site

All text is escaped; only tel:, mailto: and in-page links are emitted.
"""
from __future__ import annotations

from hashlib import sha256
import html
import json
from pathlib import Path
import re
import os
import shutil

ASSETS = Path(__file__).resolve().parents[1] / "assets" / "sales_demo"

TYPE_PAIRS = {
    # trade: (display file, display css, body file, body css, palette mode)
    "rakennus": ("archivo.woff", "font-stretch:68%;font-weight:800;letter-spacing:-.025em",
                 "hanken.woff", "font-weight:400", "dark"),
    "lampin": ("fraunces.woff", "font-weight:420;letter-spacing:-.02em;font-variation-settings:'SOFT' 60,'opsz' 144",
               "familjen.woff", "font-weight:400", "light"),
    "moderni": ("bricolage.woff", "font-stretch:82%;font-weight:700;letter-spacing:-.035em",
                "schibsted.woff", "font-weight:400", "auto"),
}

CONTENT_BRIEF = """
Fill a Kaurivo sales demo content plan as JSON, using ONLY facts and wording
from the verified source text. Never invent numbers, years, awards, prices,
reviews or guarantees. Finnish unless the source is in another language.
{"trade": "rakennus" | "lampin" | "moderni",
 "hero_style": "depth" | "blueprint" (blueprint only for builders,
               renovators, carpenters, painters, architects),
 "headline": "4-8 words, the company's core offer in its own words",
 "chapters": ["three short verified facts in story order, max 12 words each"],
 "statement": "2-3 sentences about the company from the source",
 "services": [{"name": "verified service name", "text": "one sentence from the source"}],
 "photo_captions": ["short factual caption per provided photo, same order"],
 "proof": [{"title": "reference group heading from the source",
            "items": ["each listed reference exactly as written, e.g. 'As Oy Kylätie 8, 15 kph'"]}],
 "contact_lead": "one sentence inviting contact, no promises"}
""".strip()


def _e(value) -> str:
    return html.escape(str(value or "").strip(), quote=True)


def _favicon(name, background: str, ink: str) -> str:
    """URL-encoded SVG favicon: the company's initial on the accent colour."""
    from urllib.parse import quote
    letter = (re.sub(r"[^\w]", "", str(name or "K"), flags=re.UNICODE)[:1] or "K").upper()
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" '
           f'fill="{background}"/><text x="32" y="45" font-family="Arial,sans-serif" font-size="38" '
           f'font-weight="700" text-anchor="middle" fill="{ink}">{html.escape(letter)}</text></svg>')
    return quote(svg, safe="")


def _glue(text: str) -> str:
    """Escape, and bind words of 1-2 letters to the next word (no lone 'ja' line)."""
    return re.sub(r"(?<![\w-])(\w{1,2}) (?=\S)", "\\1\u00a0", _e(text))


def _tel(phone: str) -> str:
    digits = re.sub(r"\D", "", phone or "")
    if digits.startswith("358"):
        digits = digits[3:]
    digits = digits.lstrip("0")
    return "tel:+358" + digits if len(digits) >= 6 else ""


def _mail(email: str) -> str:
    email = str(email or "").strip()
    return "mailto:" + email if re.fullmatch(r"[^@\s<>\"']+@[^@\s<>\"']+\.[a-z]{2,}", email, re.I) else ""


def validate_plan(plan: dict, photos: list[Path]) -> dict:
    """Bound and normalise a model-written plan; raise on unusable input."""
    if not isinstance(plan, dict):
        raise ValueError("plan must be an object")
    out = {
        "trade": plan.get("trade") if plan.get("trade") in TYPE_PAIRS else "moderni",
        "hero_style": "blueprint" if plan.get("hero_style") == "blueprint" else "depth",
        "headline": str(plan.get("headline") or "").strip()[:90],
        "chapters": [str(c).strip()[:110] for c in (plan.get("chapters") or []) if str(c).strip()][:3],
        "statement": str(plan.get("statement") or "").strip()[:420],
        "services": [{"name": str(s.get("name") or "").strip()[:60],
                      "text": str(s.get("text") or "").strip()[:180]}
                     for s in (plan.get("services") or []) if isinstance(s, dict) and s.get("name")][:8],
        "photo_captions": [str(c).strip()[:80] for c in (plan.get("photo_captions") or [])],
        "contact_lead": str(plan.get("contact_lead") or "").strip()[:200],
        "proof": [{"title": str(g.get("title") or "").strip()[:110],
                   "items": [str(i).strip()[:90] for i in (g.get("items") or []) if str(i).strip()][:14]}
                  for g in (plan.get("proof") or []) if isinstance(g, dict) and g.get("items")][:4],
    }
    if len(out["headline"].split()) < 2:
        raise ValueError("headline missing")
    if not out["services"]:
        raise ValueError("at least one verified service is required")
    if not photos:
        raise ValueError("a sales demo needs the company's own photos")
    return out


_FIGURE = re.compile(r"(\d[\d\s]{0,6})\s*(kph|m2|m²)\b", re.I)


def _figure(item: str) -> tuple[str, str, int, str]:
    """Split a reference line into (name, figure text, number, unit) when it ends in a quantity."""
    match = None
    for match in _FIGURE.finditer(item):
        pass
    if not match:
        return item, "", 0, ""
    number = int(re.sub(r"\D", "", match.group(1)))
    unit = "m²" if match.group(2).lower() in ("m2", "m²") else "kph"
    name = (item[:match.start()] + item[match.end():]).strip(" ,–-")
    return name or item, f"{number} {unit}", number, unit


def _proof_section(groups: list[dict]) -> str:
    """References as a typographic proof list; totals only from listed figures."""
    if not groups:
        return ""
    blocks = []
    for group in groups:
        rows, totals = [], {}
        for item in group["items"]:
            name, figure, number, unit = _figure(item)
            if unit:
                totals.setdefault(unit, []).append(number)
            rows.append(f'<li><span class="ref__name">{_e(name)}</span>'
                        + (f'<span class="ref__fig">{_e(figure)}</span>' if figure else "") + "</li>")
        total = ""
        for unit, numbers in totals.items():
            if len(numbers) >= 2:
                label = "kylpyhuonetta" if unit == "kph" else "m² laatoitusta"
                total = (f'<p class="ref__total"><span data-to="{sum(numbers)}">{sum(numbers):,}'.replace(",", "\u202f")
                         + f'</span> {label} näissä {len(numbers)} kohteessa</p>')
                break
        blocks.append(f'<div class="ref"><h3>{_e(group["title"])}</h3>{total}<ul>{"".join(rows)}</ul></div>')
    return ('<section class="proof" aria-labelledby="kohteet"><h2 id="kohteet">Kohteita</h2>'
            + "".join(blocks) + "</section>")


def _logo_ratio(path: Path) -> float:
    """Width/height of a logo (SVG viewBox or raster), bounded to 1-25."""
    try:
        if path.suffix.lower() == ".svg":
            box = re.search(r'viewBox="\s*[-\d.]+[ ,]+[-\d.]+[ ,]+([\d.]+)[ ,]+([\d.]+)',
                            path.read_text(encoding="utf-8", errors="ignore")[:4000])
            ratio = float(box.group(1)) / float(box.group(2)) if box else 4.0
        else:
            from PIL import Image
            with Image.open(path) as image:
                ratio = image.width / image.height
    except Exception:
        ratio = 4.0
    return max(1.0, min(25.0, ratio))


def _font_face(name: str, file: str) -> str:
    return (f"@font-face{{font-family:'{name}';src:url(assets/fonts/{file}) format('woff');"
            "font-weight:100 900;font-stretch:50% 125%;font-display:swap}")


# Purpose-made 3D build scenes (assets/sales_demo/build3d). Illustrations of the
# work stages, labelled as such; free (Three.js, MIT), no AI call.
BUILD_SCENES = {
    "bathroom": {
        "pattern": r"kylpyhuone|laatoit|laatta|vedeneristy|märkätila",
        "steps": ((0.0, "Runko"), (0.2, "Putkivedot"), (0.36, "Vedeneristys"), (0.56, "Laatoitus"), (0.84, "Valmis")),
        "note": "3D-havainnollistus kylpyhuoneremontin työvaiheista, ei yrityksen kohde",
        "alt": "3D-havainnollistus valmiista kylpyhuoneesta",
    },
}

BUILD_RUNTIME = """<script type="module">
const hero = document.querySelector('[data-build3d]');
if (hero) {
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const steps = JSON.parse(hero.dataset.steps);
  const box = hero.querySelector('.b3d__step'), name = hero.querySelector('.b3d__name'), num = hero.querySelector('.b3d__num');
  const bar = hero.querySelector('.b3d__bar i'), chapters = [...hero.querySelectorAll('[data-at]')];
  let scene = null;
  try {
    const mod = await import('./assets/build3d/' + hero.dataset.build3d + '.min.js');
    scene = mod.mountBathroom(hero.querySelector('canvas'), {reduce});
    hero.classList.add('is-live');
  } catch (e) { hero.classList.add('no-3d'); }
  const update = () => {
    const r = hero.getBoundingClientRect();
    const p = reduce ? 1 : Math.min(1, Math.max(0, -r.top / Math.max(1, r.height - innerHeight)));
    if (scene && !reduce) scene.set(p);
    let k = 0; steps.forEach((s, i) => { if (p >= s.at) k = i; });
    if (name.textContent !== steps[k].name) {
      name.textContent = steps[k].name; num.textContent = String(k + 1).padStart(2, '0');
      box.classList.remove('flip'); void box.offsetWidth; box.classList.add('flip');
    }
    if (bar) bar.style.transform = 'scaleX(' + p.toFixed(4) + ')';
    let c = 0; chapters.forEach((el, i) => { if (p >= +el.dataset.at) c = i; });
    chapters.forEach((el, i) => el.classList.toggle('is-on', i === c));
  };
  addEventListener('scroll', update, {passive: true}); update();
}
</script>"""


def build_scene_for(text: str) -> str | None:
    text = str(text or "").casefold()
    for key, scene in BUILD_SCENES.items():
        if re.search(scene["pattern"], text):
            return key
    return None


def _echoes(name: str, text: str) -> bool:
    """True when a service text only repeats its name (e.g. 'Kylpyhuoneremontit ja ...')."""
    stem = lambda w: w[:6]
    words = lambda t: {stem(w) for w in re.findall(r"\w{3,}", str(t or "").casefold())}
    named, said = words(name), words(text)
    return not (said - named)


def render_sales_demo(*, company: dict, plan: dict, photos: list[Path], out_dir: Path,
                      logo: Path | None = None, credits: list | None = None,
                      sequence: list[Path] | None = None, sequence_labels: list[str] | None = None,
                      sequence_note: str = "", build_scene: str | None = None) -> Path:
    """credits[i] is None for the company's own photo, or a stock credit
    {"photographer", "source_url", "licence"}: such photos are shown as
    labelled illustrations, never as the company's work."""
    """Write index.html and assets for one prospect; returns the page path.

    ``sequence``: 2-4 frames of ONE illustrated scene in build order (e.g. a
    bathroom from bare concrete to finished). They form the hero, set the
    palette and are labelled with ``sequence_note``; ``photos`` then serve the
    rest of the page, each used once."""
    from utils.award_playbook import derive_photo_palette
    from utils.scroll_scrub import enhance_scroll_scrub

    sequence = [Path(f) for f in (sequence or []) if Path(f).is_file()][:4]
    if len(sequence) < 2:
        sequence = []
    build_scene = build_scene if build_scene in BUILD_SCENES else None
    if build_scene:
        sequence = []  # one signature moment: the 3D build replaces an image sequence
    plan = validate_plan(plan, photos or sequence or ([ASSETS / "build3d" / "bathroom-poster.webp"] if build_scene else []))
    out_dir = Path(out_dir)
    assets = out_dir / "assets"
    (assets / "fonts").mkdir(parents=True, exist_ok=True)
    display_file, display_css, body_file, body_css, mode = TYPE_PAIRS[plan["trade"]]
    for file in (display_file, body_file):
        shutil.copyfile(ASSETS / "fonts" / file, assets / "fonts" / file)

    staged, media = [], []
    seq_staged = []
    for index, frame in enumerate(sequence):
        target = assets / f"vaihe-{index + 1}{frame.suffix.lower()}"
        shutil.copyfile(frame, target)
        seq_staged.append(f"assets/{target.name}")
    for index, photo in enumerate(photos[:6]):
        target = assets / f"kuva-{index + 1}{photo.suffix.lower()}"
        shutil.copyfile(photo, target)
        rel = f"assets/{target.name}"
        staged.append(rel)
        media.append({"src": rel, "sha256": sha256(target.read_bytes()).hexdigest()})
    logo_rel, logo_ratio = "", 4.0
    if logo and logo.is_file():
        target = assets / ("logo" + logo.suffix.lower())
        shutil.copyfile(logo, target)
        logo_rel = f"assets/{target.name}"
        logo_ratio = _logo_ratio(target)

    # The hero photos are the signature moment, so they alone set the palette.
    palette_photos = [assets / Path(p).name for p in (seq_staged or staged[:3])]
    scene_rel = ""
    if build_scene:
        scene_dir = assets / "build3d"
        scene_dir.mkdir(parents=True, exist_ok=True)
        for file in (f"{build_scene}.min.js", f"{build_scene}-poster.webp", "LICENSE-three.txt"):
            shutil.copyfile(ASSETS / "build3d" / file, scene_dir / file)
        scene_rel = "assets/build3d/"
        # The build scene is the signature moment and sets the palette.
        palette_photos = [ASSETS / "build3d" / f"{build_scene}-palette.webp"]
    palette = derive_photo_palette(palette_photos, mode=mode) \
        or derive_photo_palette(palette_photos, mode="light")
    if not palette:
        raise ValueError("photo palette unavailable")
    if os.getenv("KAURIVO_PHOTO_GRADE", "1") != "0":
        from utils.photo_grade import grade_photo
        shadow = palette["ink"] if palette["mode"] == "light" else palette["surface"]
        highlight = palette["canvas"] if palette["mode"] == "light" else palette["ink"]

        def _graded(rels, strength):
            out = []
            for rel in rels:
                source = out_dir / rel
                target = grade_photo(source, source.with_name(source.stem + "-g.webp"),
                                     shadow=shadow, highlight=highlight, strength=strength)
                source.unlink()
                out.append(f"assets/{target.name}")
            return out
        staged = _graded(staged, 1.0)
        # Illustrated sequences are already lit as one series: a light touch only.
        seq_staged = _graded(seq_staged, .45)
    media = [{"src": rel, "sha256": sha256((out_dir / rel).read_bytes()).hexdigest()}
             for rel in seq_staged + staged]
    captions = plan["photo_captions"] + [""] * len(staged)
    credits = list(credits or []) + [None] * len(staged)
    stock = [bool(credits[i]) for i in range(len(staged))]
    for i, credit in enumerate(credits[:len(staged)]):
        if credit:  # an illustration caption replaces any project-like caption
            who = str(credit.get("photographer") or "").strip()
            provider = str(credit.get("provider") or "Pexels")
            licence = str(credit.get("licence") or "")
            captions[i] = ("Havainnekuva" + (f", kuva: {who} / {provider}" if who else f", {provider}")
                           + (f", {licence}" if licence.startswith(("CC", "Public")) else ""))

    name = _e(company.get("name"))
    phone = str(company.get("phone") or "").strip()
    tel, mail = _tel(phone), _mail(company.get("email"))
    alt = lambda i: _e(captions[i] or f"{company.get('name')}: työkuva {i + 1}")
    labels = [str(x)[:24] for x in (sequence_labels or [])][:len(seq_staged)]
    if seq_staged:
        hero_photos = seq_staged
        hero_alts = [_e(f"Havainnekuva: {labels[i]}" if i < len(labels) else "Havainnekuva")
                     for i in range(len(seq_staged))]
        rest = list(range(len(staged)))
        hero_badge = f'<p class="hero__credit">{_e(sequence_note or "Havainnekuva")}</p>'
    else:
        hero_photos = staged[:3]
        hero_alts = [alt(i) for i in range(len(hero_photos))]
        rest = list(range(len(hero_photos), len(staged)))
        hero_badge = (f'<p class="hero__credit">{_e(captions[0])}</p>' if stock and stock[0] else "")
    if build_scene:
        rest = list(range(len(staged)))
    any_illustration = any(stock) or bool(seq_staged)
    scene_note = (" Herossa on 3D-havainnollistus työvaiheista." if build_scene else "")
    kinds = [k for k, on in (("tekoälyllä luotuja", bool(seq_staged)), ("kuvapankin", any(stock))) if on]
    stock_note = (f" Kuvat ovat {' ja '.join(kinds)} havainnekuvia, eivät yrityksen omia kohteita."
                  if any_illustration else "") + scene_note
    stage_strip = ("" if not labels else '<ol class="stages" aria-hidden="true">' + "".join(
        f'<li data-stage="{i / len(labels):.3f}"><span>{i + 1}</span>{_e(t)}</li>'
        for i, t in enumerate(labels)) + "</ol>")

    chapters = "".join(
        f'<p data-at="{at}">{_e(text)}</p>'
        for at, text in zip(("0", "0.36", "0.7"), plan["chapters"]))
    if build_scene:
        steps = BUILD_SCENES[build_scene]["steps"]
        labels = [name for _, name in steps]
        stage_strip = '<ol class="stages" aria-hidden="true">' + "".join(
            f'<li data-stage="{at:.3f}"><span>{i + 1}</span>{_e(n)}</li>' for i, (at, n) in enumerate(steps)) + "</ol>"
        steps_json = _e(json.dumps([{"at": at, "name": n} for at, n in steps], ensure_ascii=False))
        hero = f'''
<section class="hero hero--3d" data-build3d="{build_scene}" data-steps="{steps_json}" aria-labelledby="otsikko">
 <div class="b3d__stage">
  <img class="b3d__poster" src="{scene_rel}{build_scene}-poster.webp" alt="{_e(BUILD_SCENES[build_scene]["alt"])}">
  <canvas class="b3d__canvas" aria-hidden="true"></canvas>
  <p class="b3d__step" aria-hidden="true"><span class="b3d__num">01</span><span class="b3d__name">{_e(steps[0][1])}</span></p>
  <div class="b3d__copy">
    <h1 id="otsikko">{_glue(plan["headline"])}</h1>
    <div class="b3d__chapters">{chapters}</div>
    {f'<a class="btn" href="{tel}">Soita {_e(phone)}</a>' if tel else ""}
  </div>
  <p class="hero__credit">{_e(BUILD_SCENES[build_scene]["note"])}</p>
  {stage_strip}
  <div class="b3d__bar" aria-hidden="true"><i></i></div>
 </div>
</section>'''
    else:
        hero = f'''
<section class="hero" data-kaurivo-scrub{' data-scrub-style="blueprint"' if plan["hero_style"] == "blueprint" else ""}{' data-scrub-warp="0"' if plan["trade"] == "rakennus" or seq_staged else ""} aria-labelledby="otsikko">
  <img data-kaurivo-scrub-poster src="{hero_photos[0]}" alt="{hero_alts[0]}">
  {"".join(f'<img data-kaurivo-scrub-frame src="{p}" alt="{hero_alts[i + 1]}">' for i, p in enumerate(hero_photos[1:]))}
  <div data-kaurivo-scrub-copy>
    <h1 id="otsikko">{_glue(plan["headline"])}</h1>
    {chapters}
    {f'<a class="btn" href="{tel}">Soita {_e(phone)}</a>' if tel else ""}
  </div>
  {hero_badge}
  {stage_strip}
</section>'''

    # Every photo appears once: the growing photo first, then services. Next to an
    # illustrated sequence, stock photos from other cameras would break the world:
    # only the company's own photos are added, and the finished frame grows.
    if seq_staged:
        rest = [i for i in rest if not stock[i]]
    grow_index = rest.pop(0) if rest else None
    grow_photo = staged[grow_index] if grow_index is not None else ""
    if seq_staged and grow_index is None:
        grow_photo = seq_staged[-1]
    grow_html = ""
    if grow_photo:
        cap_text = captions[grow_index] if grow_index is not None else (sequence_note or "Havainnekuva")
        grow_cap = f'<p class="grow__cap">{_e(cap_text)}</p>' if cap_text else ""
        grow_html = (f'<section class="grow" aria-label="Työkuva"><div class="grow__stage">'
                     f'<img src="{grow_photo}" alt="{alt(grow_index) if grow_index is not None else hero_alts[-1]}" loading="lazy">\n{grow_cap}</div></section>')
    svc_photos = {i: staged[rest[i]] for i in range(min(len(rest), len(plan["services"])))}
    service_items = "".join(
        f'''<li class="svc"{f' data-photo="{svc_photos[i]}"' if i in svc_photos else ""}>
      <h3>{_e(s["name"])}</h3>{"" if _echoes(s["name"], s["text"]) else f"<p>{_e(s['text'])}</p>"}
      {f'<img class="svc__img" src="{svc_photos[i]}" alt="" loading="lazy">' if i in svc_photos else ""}
    </li>''' for i, s in enumerate(plan["services"]))

    p = palette
    from utils.award_playbook import contrast
    hexrgb = lambda v: tuple(int(v[i:i + 2], 16) for i in (1, 3, 5))
    band = p["surface"] if p["mode"] == "dark" else p["ink"]
    band_ink = p["ink"] if p["mode"] == "dark" else p["canvas"]
    phone_colour = p["accent"] if contrast(hexrgb(p["accent"]), hexrgb(band)) >= 3 else band_ink
    page = f'''<!doctype html>
<html lang="fi">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>{name} | Kaurivon luonnos</title>
<link rel="icon" href="data:image/svg+xml,{_favicon(company.get("name"), p["accent"], p["accent_ink"])}">
<style>
{_font_face("Display", display_file)}
{_font_face("Body", body_file)}
:root{{--canvas:{p["canvas"]};--surface:{p["surface"]};--ink:{p["ink"]};--muted:{p["muted"]};
--accent:{p["accent"]};--accent-ink:{p["accent_ink"]};
--band:{band};--band-ink:{band_ink};--phone:{phone_colour};--gutter:clamp(20px,5vw,72px);--ease:cubic-bezier(.16,1,.3,1)}}
*,*::before,*::after{{box-sizing:border-box}}
html{{background:var(--canvas)}}
body{{margin:0;background:var(--canvas);color:var(--ink);font-family:"Body",system-ui,sans-serif;{body_css};
font-size:clamp(16px,.96rem + .25vw,19px);line-height:1.55;-webkit-font-smoothing:antialiased}}
img{{display:block;max-width:100%}}
a{{color:inherit}}
:focus-visible{{outline:3px solid var(--accent);outline-offset:3px}}
.draft{{position:fixed;z-index:40;right:16px;bottom:16px;margin:0;max-width:min(400px,calc(100% - 32px));background:var(--ink);color:var(--canvas);
font-size:12.5px;line-height:1.35;padding:8px 12px;border-radius:10px;box-shadow:0 8px 24px -12px rgba(0,0,0,.5)}}
.draft{{max-width:min(300px,calc(100% - 32px))}}
.draft__short{{display:none}}
@media (max-width:560px){{.draft{{left:12px;right:12px;bottom:12px;max-width:none;padding:6px 10px;font-size:11.5px;border-radius:8px}}
 .draft__long{{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}}.draft__short{{display:inline}}}}
.nav{{position:fixed;top:0;left:0;right:0;z-index:30;display:flex;align-items:center;justify-content:space-between;gap:16px;
padding:14px var(--gutter);background:linear-gradient(180deg,color-mix(in srgb,var(--canvas) 70%,transparent),transparent);transition:background-color .3s ease}}
.nav.solid{{background:color-mix(in srgb,var(--canvas) 94%,transparent);backdrop-filter:blur(10px);box-shadow:0 1px 0 color-mix(in srgb,var(--ink) 12%,transparent)}}
.nav__name{{font-family:"Display";{display_css};font-size:clamp(18px,1.6vw,24px);text-decoration:none;letter-spacing:-.01em}}
.nav__logo{{display:block;height:clamp(14px,1.5vw,20px);width:auto;max-width:min(50vw,300px);object-fit:contain;object-position:left center}}
.nav__brand{{display:inline-flex;align-items:center;min-width:0}}
.nav__brand.chip{{background:{"var(--ink)" if p["mode"] == "dark" else "transparent"};padding:{"8px 14px" if p["mode"] == "dark" else "0"};border-radius:10px}}
.nav__call .long{{display:inline}}
@media (max-width:560px){{.nav__call .long{{display:none}}}}
.nav__call{{flex:none;background:var(--accent);color:var(--accent-ink);text-decoration:none;font-weight:650;padding:10px 18px;border-radius:999px;white-space:nowrap}}
h1,h2,h3{{font-family:"Display",serif;{display_css};margin:0;text-wrap:balance}}
h1{{font-size:clamp(46px,8.2vw,132px);line-height:.92}}
.hero{{position:relative;background:var(--surface)}}
.hero [data-kaurivo-scrub-poster]{{width:100%;max-height:72svh;object-fit:cover}}
.hero [data-kaurivo-scrub-frame]{{display:none}}
.hero [data-kaurivo-scrub-copy]{{padding:clamp(24px,5vh,56px) var(--gutter)}}
.hero > [data-kaurivo-scrub-poster]{{margin-top:0}}
main{{padding-top:0}}
.hero [data-kaurivo-scrub-copy] p{{max-width:34ch;font-size:clamp(17px,1rem + .45vw,23px);margin:.6em 0 0}}
.btn{{display:inline-flex;align-items:center;min-height:52px;margin-top:22px;padding:0 26px;border-radius:999px;
background:var(--accent);color:var(--accent-ink);font-weight:650;text-decoration:none}}
.statement{{padding:clamp(96px,18vh,200px) var(--gutter)}}
.statement p{{font-family:"Display";{display_css};font-size:clamp(30px,1.3rem + 3.2vw,72px);line-height:1.04;margin:0;max-width:22ch}}
.statement .w{{opacity:.18;transition:opacity .3s linear}}
.statement .w.on{{opacity:1}}
.services{{padding:0 var(--gutter) clamp(80px,14vh,160px)}}
.services h2{{font-size:clamp(22px,1.6vw,28px);font-family:"Body";font-weight:600;letter-spacing:0;margin-bottom:12px;color:var(--muted)}}
.svc-list{{list-style:none;margin:0;padding:0;border-top:1px solid color-mix(in srgb,var(--ink) 22%,transparent)}}
.svc{{position:relative;display:grid;grid-template-columns:minmax(0,1.1fr) minmax(0,1fr);gap:8px 40px;align-items:baseline;
padding:clamp(18px,3vh,30px) 0;border-bottom:1px solid color-mix(in srgb,var(--ink) 22%,transparent)}}
.svc h3{{font-size:clamp(30px,4.6vw,76px);line-height:.95;transition:color .3s var(--ease),transform .5s var(--ease)}}
.svc p{{margin:0;max-width:40ch;color:var(--muted)}}
.svc__img{{display:none}}
@media (hover:hover) and (pointer:fine){{
 .svc:hover h3{{color:var(--accent);transform:translateX(12px)}}
 .preview{{position:fixed;left:0;top:0;width:min(28vw,380px);aspect-ratio:4/3;object-fit:cover;border-radius:14px;pointer-events:none;
 z-index:20;opacity:0;transform:translate(-50%,-60%) scale(.9);transition:opacity .25s ease,transform .45s var(--ease)}}
 .preview.on{{opacity:1;transform:translate(-50%,-60%) scale(1)}}
}}
@media (max-width:760px){{.svc{{grid-template-columns:1fr}} .svc__img{{display:block;margin-top:10px;border-radius:10px;aspect-ratio:16/10;object-fit:cover;width:100%}}}}
.grow{{position:relative;height:220vh}}
.grow__stage{{position:sticky;top:0;height:100svh;display:grid;place-items:center;overflow:hidden}}
.grow__stage img{{width:100%;height:100%;object-fit:cover;clip-path:inset(var(--inset,14%) var(--inset-x,20%) round 22px)}}
.hero__credit{{position:absolute;z-index:3;top:76px;right:var(--gutter);margin:0;font-size:12px;color:#fff;background:rgba(0,0,0,.45);padding:5px 10px;border-radius:999px}}
.hero > .hero__credit, [data-scrub-stage] > .hero__credit{{position:absolute}}
.stages{{position:absolute;z-index:3;right:var(--gutter);bottom:clamp(96px,12vh,128px);margin:0;padding:0;list-style:none;display:flex;gap:6px;
font-size:13px;color:#fff}}
.stages li{{display:flex;align-items:center;gap:8px;padding:7px 12px 7px 8px;border-radius:999px;background:rgba(0,0,0,.38);
backdrop-filter:blur(6px);opacity:.55;transition:opacity .4s var(--ease),background-color .4s var(--ease)}}
.stages li span{{display:grid;place-items:center;width:22px;height:22px;border-radius:50%;border:1px solid rgba(255,255,255,.6);font-size:11px;font-variant-numeric:tabular-nums}}
.stages li.on{{opacity:1;background:color-mix(in srgb,var(--accent) 88%,transparent);color:var(--accent-ink)}}
.stages li.on span{{border-color:currentColor}}
@media (max-width:760px){{.stages{{left:var(--gutter);right:auto;top:118px;bottom:auto;flex-direction:column;align-items:flex-start;font-size:12px}}
 .stages li:not(.on){{display:none}}}}
.hero--3d{{height:540svh;background:var(--canvas)}}
.b3d__stage{{position:sticky;top:0;height:100svh;overflow:hidden}}
.b3d__canvas,.b3d__poster{{position:absolute;top:0;bottom:0;left:28%;right:0;width:72%;height:100%;display:block}}
.b3d__poster{{object-fit:contain;object-position:60% 58%;padding:12vh 4vw 6vh}}
.hero--3d.is-live .b3d__poster{{display:none}}
.b3d__step{{position:absolute;z-index:2;left:var(--gutter);top:clamp(92px,15vh,150px);margin:0;display:flex;align-items:baseline;gap:18px}}
.b3d__num{{font-variant-numeric:tabular-nums;color:var(--accent);font-weight:650;font-size:clamp(14px,1.1vw,18px)}}
.b3d__name{{font-family:"Display";{display_css};font-size:clamp(44px,7.4vw,124px);line-height:.9;color:var(--ink)}}
.b3d__step.flip .b3d__name{{animation:b3dIn .7s var(--ease)}}
@keyframes b3dIn{{from{{opacity:0;transform:translateY(.25em)}}to{{opacity:1;transform:none}}}}
.b3d__copy{{position:absolute;z-index:2;left:var(--gutter);bottom:clamp(36px,9vh,96px);max-width:min(34rem,36vw)}}
.hero--3d h1{{font-size:clamp(34px,3.6vw,60px);line-height:.98}}
.b3d__chapters{{display:grid;margin-top:14px}}
.b3d__chapters p{{grid-area:1/1;margin:0;max-width:34ch;color:var(--muted);font-size:clamp(16px,1rem + .3vw,20px);opacity:0;transform:translateY(8px);transition:opacity .45s ease,transform .6s var(--ease)}}
.b3d__chapters p.is-on{{opacity:1;transform:none}}
.b3d__bar{{position:absolute;left:0;right:0;bottom:0;height:3px;background:color-mix(in srgb,var(--ink) 14%,transparent);z-index:2}}
.b3d__bar i{{display:block;height:100%;background:var(--accent);transform-origin:left;transform:scaleX(0)}}
.hero--3d .hero__credit{{top:auto;bottom:clamp(36px,9vh,96px);right:var(--gutter);background:color-mix(in srgb,var(--ink) 12%,transparent);color:var(--muted)}}
.hero--3d .stages{{bottom:clamp(84px,15vh,150px)}}
.hero--3d .stages li{{background:color-mix(in srgb,var(--ink) 10%,transparent);color:var(--ink)}}
@media (max-width:760px){{
 .b3d__canvas,.b3d__poster{{left:0;width:100%;top:9svh;height:48svh}}
 .b3d__poster{{padding:4vh 2vw}}
 .b3d__step{{top:84px}} .b3d__name{{font-size:clamp(34px,11vw,56px)}}
 .b3d__copy{{max-width:none;right:var(--gutter);bottom:clamp(64px,10svh,96px)}}
 .hero--3d h1{{font-size:clamp(30px,8.6vw,44px)}}
 .hero--3d .stages{{display:none}}
 .hero--3d .hero__credit{{bottom:auto;top:calc(9svh + 48svh + 6px);left:var(--gutter);right:var(--gutter);font-size:11px;line-height:1.3;border-radius:8px}}
}}
@media (prefers-reduced-motion:reduce){{.hero--3d{{height:auto}}.b3d__stage{{position:relative}}}}
.grow__cap{{position:absolute;left:var(--gutter);bottom:clamp(24px,6vh,60px);background:var(--canvas);color:var(--ink);padding:8px 14px;border-radius:999px;font-size:14px}}
.proof{{padding:clamp(72px,12vh,140px) var(--gutter);border-top:1px solid color-mix(in srgb,var(--ink) 16%,transparent)}}
.proof>h2{{font-size:clamp(22px,1.6vw,28px);font-family:"Body";font-weight:600;letter-spacing:0;color:var(--muted);margin-bottom:clamp(28px,5vh,56px)}}
.ref{{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.5fr);gap:12px clamp(24px,5vw,80px);padding:clamp(28px,5vh,52px) 0;
border-top:1px solid color-mix(in srgb,var(--ink) 22%,transparent)}}
.ref h3{{font-size:clamp(24px,2.4vw,38px);line-height:1.05;max-width:18ch}}
.ref__total{{grid-column:1;margin:0;color:var(--muted);max-width:24ch}}
.ref__total span{{display:block;font-family:"Display";{display_css};font-size:clamp(64px,9vw,150px);line-height:.9;color:var(--ink);font-variant-numeric:tabular-nums}}
.ref ul{{grid-column:2;grid-row:1 / span 2;list-style:none;margin:0;padding:0;columns:2 16rem;column-gap:clamp(20px,3vw,48px)}}
.ref li{{display:flex;justify-content:space-between;gap:12px;break-inside:avoid;padding:9px 0;border-bottom:1px solid color-mix(in srgb,var(--ink) 12%,transparent)}}
.ref__fig{{flex:none;font-variant-numeric:tabular-nums;color:var(--muted)}}
@media (max-width:760px){{.ref{{grid-template-columns:1fr}}.ref ul{{grid-column:1;grid-row:auto}}}}
.contact{{background:var(--band);color:var(--band-ink);padding:clamp(96px,16vh,180px) var(--gutter) clamp(48px,8vh,80px)}}
.contact p{{max-width:38ch;font-size:clamp(18px,1rem + .5vw,24px);margin:0 0 24px}}
.contact__phone{{display:inline-block;font-family:"Display";{display_css};font-size:clamp(54px,12vw,210px);line-height:.88;color:var(--phone);text-decoration:none;white-space:nowrap}}
.contact__row{{display:flex;flex-wrap:wrap;justify-content:space-between;gap:20px 48px;margin-top:clamp(32px,6vh,64px);padding-top:22px;
border-top:1px solid color-mix(in srgb,var(--band-ink) 25%,transparent)}}
.contact address{{font-style:normal}}
.sr{{position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap}}
footer{{background:var(--band);color:color-mix(in srgb,var(--band-ink) 72%,transparent);padding:0 var(--gutter) 28px;font-size:14px;display:flex;flex-wrap:wrap;gap:8px 28px}}
@media (prefers-reduced-motion:reduce){{*,*::before,*::after{{transition:none!important}}.statement .w{{opacity:1}}.grow{{height:auto}}.grow__stage{{position:relative;height:80svh}}.grow__stage img{{clip-path:none}}}}
</style>
</head>
<body>
<p class="draft" role="note"><span class="draft__long">Kaurivon luonnos yritykselle {name}. Ei yrityksen virallinen verkkosivu.{stock_note}</span><span class="draft__short" aria-hidden="true">Kaurivon luonnos, ei virallinen sivu.{" Kuvat ovat havainnekuvia." if any(stock) else ""}</span></p>
<header class="nav">
  {f'<a class="nav__brand chip" href="#otsikko"><img class="nav__logo" src="{logo_rel}" alt="{name}" width="{round(20 * logo_ratio)}" height="20"></a>' if logo_rel else f'<a class="nav__name" href="#otsikko">{name}</a>'}
  {f'<a class="nav__call" href="{tel}">Soita<span class="long"> {_e(phone)}</span></a>' if tel else ""}
</header>
<main>
{hero}
<section class="statement" aria-label="Yrityksestä"><p id="lausunto">{_e(plan["statement"])}</p></section>
<section class="services" aria-labelledby="palvelut"><h2 id="palvelut">Palvelut</h2><ul class="svc-list">{service_items}</ul></section>
{_proof_section(plan["proof"])}
{grow_html}
<section class="contact" aria-labelledby="yhteys">
  <h2 id="yhteys" class="sr">Yhteystiedot</h2>
  {f'<p>{_e(plan["contact_lead"])}</p>' if plan["contact_lead"] else ""}
  {f'<a class="contact__phone" href="{tel}">{_e(phone)}</a>' if tel else ""}
  <div class="contact__row">
    {f'<a href="{mail}">{_e(company.get("email"))}</a>' if mail else ""}
    <address>{name}{"<br>" + _e(company.get("address")) if company.get("address") else ""}</address>
  </div>
</section>
</main>
<footer><span>{name}</span><span>Kaurivon luonnos, ei yrityksen virallinen verkkosivu.{stock_note}</span>{"<span>Y-tunnus " + _e(company.get("business_id")) + "</span>" if company.get("business_id") else ""}</footer>
<script>
(() => {{
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const nav = document.querySelector('.nav'), hero = document.querySelector('.hero');
  const solid = () => nav.classList.toggle('solid', hero.getBoundingClientRect().bottom < innerHeight * .35 || scrollY > hero.offsetHeight);
  addEventListener('scroll', solid, {{passive: true}}); solid();
  const st = document.getElementById('lausunto');
  st.innerHTML = st.textContent.split(' ').map(w => '<span class="w">' + w.replace(/[&<>]/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;'}})[c]) + '</span>').join(' ');
  const words = st.querySelectorAll('.w');
  const grow = document.querySelector('.grow');
  const img = grow && grow.querySelector('img');
  function tick() {{
    const r = st.getBoundingClientRect(), vh = innerHeight;
    const p = Math.min(1, Math.max(0, (vh * .85 - r.top) / (r.height + vh * .4)));
    const n = Math.round(p * words.length);
    words.forEach((w, i) => w.classList.toggle('on', i < n));
    if (img) {{
      const g = grow.getBoundingClientRect();
      const q = Math.min(1, Math.max(0, -g.top / Math.max(1, g.height - vh)));
      img.style.setProperty('--inset', (14 * (1 - q)).toFixed(2) + '%');
      img.style.setProperty('--inset-x', ((innerWidth < 760 ? 5 : 20) * (1 - q)).toFixed(2) + '%');
    }}
  }}
  const stages = [...document.querySelectorAll('.stages li')];
  const counters = [...document.querySelectorAll('.ref__total span')].map(el => ({{el, to: +el.dataset.to || 0, ref: el.closest('.ref')}}));
  const fmt = n => String(n).replace(/\\B(?=(\\d{{3}})+(?!\\d))/g, '\u202f');
  function live() {{
    const vh = innerHeight;
    if (stages.length) {{
      const h = hero.getBoundingClientRect();
      const q = Math.min(.999, Math.max(0, -h.top / Math.max(1, h.height - vh)));
      let on = 0; stages.forEach((s, i) => {{ if (q >= +s.dataset.stage) on = i; }});
      stages.forEach((s, i) => s.classList.toggle('on', i === on));
    }}
    counters.forEach(c => {{
      const r = c.ref.getBoundingClientRect();
      const q = Math.min(1, Math.max(0, (vh * .9 - r.top) / Math.max(1, Math.min(r.height * .35, vh * .45))));
      c.el.textContent = fmt(Math.round(c.to * (1 - Math.pow(1 - q, 2))));
    }});
  }}
  if (reduce) {{ words.forEach(w => w.classList.add('on')); counters.forEach(c => c.el.textContent = fmt(c.to)); live(); return; }}
  addEventListener('scroll', () => requestAnimationFrame(live), {{passive: true}}); live();
  addEventListener('scroll', () => requestAnimationFrame(tick), {{passive: true}}); tick();
  if (matchMedia('(hover: hover) and (pointer: fine)').matches) {{
    const preview = document.createElement('img'); preview.className = 'preview'; preview.alt = '';
    document.body.appendChild(preview);
    document.querySelectorAll('.svc').forEach(item => {{
      item.addEventListener('pointerenter', () => {{ preview.src = item.dataset.photo; preview.classList.add('on'); }});
      item.addEventListener('pointerleave', () => preview.classList.remove('on'));
      item.addEventListener('pointermove', e => {{ preview.style.left = e.clientX + 'px'; preview.style.top = e.clientY + 'px'; }});
    }});
  }}
}})();
</script>
{BUILD_RUNTIME if build_scene else ""}
</body>
</html>
'''
    page = enhance_scroll_scrub(page, route="index.html", media=media, site_root=out_dir)
    target = out_dir / "index.html"
    target.write_text(page, encoding="utf-8")
    (out_dir / "sales-demo.json").write_text(json.dumps(
        {"palette": palette, "plan": plan, "trade": plan["trade"]}, ensure_ascii=False, indent=1),
        encoding="utf-8")
    return target

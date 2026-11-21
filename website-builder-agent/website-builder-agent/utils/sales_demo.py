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
 "contact_lead": "one sentence inviting contact, no promises"}
""".strip()


def _e(value) -> str:
    return html.escape(str(value or "").strip(), quote=True)


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
    }
    if len(out["headline"].split()) < 2:
        raise ValueError("headline missing")
    if not out["services"]:
        raise ValueError("at least one verified service is required")
    if not photos:
        raise ValueError("a sales demo needs the company's own photos")
    return out


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


def render_sales_demo(*, company: dict, plan: dict, photos: list[Path], out_dir: Path,
                      logo: Path | None = None) -> Path:
    """Write index.html and assets for one prospect; returns the page path."""
    from utils.award_playbook import derive_photo_palette
    from utils.scroll_scrub import enhance_scroll_scrub

    plan = validate_plan(plan, photos)
    out_dir = Path(out_dir)
    assets = out_dir / "assets"
    (assets / "fonts").mkdir(parents=True, exist_ok=True)
    display_file, display_css, body_file, body_css, mode = TYPE_PAIRS[plan["trade"]]
    for file in (display_file, body_file):
        shutil.copyfile(ASSETS / "fonts" / file, assets / "fonts" / file)

    staged, media = [], []
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

    palette = derive_photo_palette([assets / Path(p).name for p in staged], mode=mode) \
        or derive_photo_palette([assets / Path(p).name for p in staged], mode="light")
    if not palette:
        raise ValueError("photo palette unavailable")
    captions = plan["photo_captions"] + [""] * len(staged)

    name = _e(company.get("name"))
    phone = str(company.get("phone") or "").strip()
    tel, mail = _tel(phone), _mail(company.get("email"))
    hero_photos = staged[:3]
    alt = lambda i: _e(captions[i] or f"{company.get('name')}: työkuva {i + 1}")

    chapters = "".join(
        f'<p data-at="{at}">{_e(text)}</p>'
        for at, text in zip(("0", "0.36", "0.7"), plan["chapters"]))
    hero = f'''
<section class="hero" data-kaurivo-scrub{' data-scrub-style="blueprint"' if plan["hero_style"] == "blueprint" else ""} aria-labelledby="otsikko">
  <img data-kaurivo-scrub-poster src="{hero_photos[0]}" alt="{alt(0)}">
  {"".join(f'<img data-kaurivo-scrub-frame src="{p}" alt="{alt(i + 1)}">' for i, p in enumerate(hero_photos[1:]))}
  <div data-kaurivo-scrub-copy>
    <h1 id="otsikko">{_e(plan["headline"])}</h1>
    {chapters}
    {f'<a class="btn" href="{tel}">Soita {_e(phone)}</a>' if tel else ""}
  </div>
</section>'''

    service_items = "".join(
        f'''<li class="svc" data-photo="{staged[i % len(staged)]}">
      <h3>{_e(s["name"])}</h3><p>{_e(s["text"])}</p>
      <img class="svc__img" src="{staged[i % len(staged)]}" alt="" loading="lazy">
    </li>''' for i, s in enumerate(plan["services"]))

    grow_photo = staged[min(len(staged) - 1, 3)] if len(staged) > 3 else staged[-1]
    grow_index = staged.index(grow_photo)

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
.draft{{position:fixed;z-index:40;right:16px;bottom:16px;margin:0;max-width:calc(100% - 32px);background:var(--ink);color:var(--canvas);
font-size:12.5px;line-height:1.35;padding:8px 12px;border-radius:10px;box-shadow:0 8px 24px -12px rgba(0,0,0,.5)}}
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
.hero{{background:var(--surface)}}
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
.grow__cap{{position:absolute;left:var(--gutter);bottom:clamp(24px,6vh,60px);background:var(--canvas);color:var(--ink);padding:8px 14px;border-radius:999px;font-size:14px}}
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
<p class="draft" role="note">Kaurivon luonnos yritykselle {name}. Ei yrityksen virallinen verkkosivu.</p>
<header class="nav">
  {f'<a class="nav__brand chip" href="#otsikko"><img class="nav__logo" src="{logo_rel}" alt="{name}" width="{round(20 * logo_ratio)}" height="20"></a>' if logo_rel else f'<a class="nav__name" href="#otsikko">{name}</a>'}
  {f'<a class="nav__call" href="{tel}">Soita<span class="long"> {_e(phone)}</span></a>' if tel else ""}
</header>
<main>
{hero}
<section class="statement" aria-label="Yrityksestä"><p id="lausunto">{_e(plan["statement"])}</p></section>
<section class="services" aria-labelledby="palvelut"><h2 id="palvelut">Palvelut</h2><ul class="svc-list">{service_items}</ul></section>
<section class="grow" aria-label="Työkuva"><div class="grow__stage"><img src="{grow_photo}" alt="{alt(grow_index)}" loading="lazy">
{f'<p class="grow__cap">{_e(captions[grow_index])}</p>' if captions[grow_index] else ""}</div></section>
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
<footer><span>{name}</span>{"<span>Y-tunnus " + _e(company.get("business_id")) + "</span>" if company.get("business_id") else ""}</footer>
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
      img.style.setProperty('--inset-x', (20 * (1 - q)).toFixed(2) + '%');
    }}
  }}
  if (reduce) {{ words.forEach(w => w.classList.add('on')); return; }}
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

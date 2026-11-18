"""Three *visibly distinct*, real browser concept screenshots for Räsänen.

Research-backed first-view experiments; comparison/selection require separate
human or honestly identified model reviewer. No screenshots are manufactured.
Not an agency-wide reusable visual template, just this company's test brief.
"""
from __future__ import annotations

import base64
import hashlib
import io
import json
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]
DEMO = ROOT / "docs/kaurivo/demos/s-rasasen-autohuolto-v1"
OUT = DEMO / "_concept_evidence"
OUT.mkdir(exist_ok=True)

SHARED = """<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow"><title>S. Räsäsen Autohuolto Oy | Huolto Keravalla</title>"""
DIRECT_1 = """<!doctype html><html lang="fi"><head>""" + SHARED + """<style>
*{box-sizing:border-box}body{margin:0;color:#171b1d;font-family:Arial,sans-serif;background:#f4f1ed}
header{height:94px;padding:0 5%;display:flex;align-items:center;justify-content:space-between;background:#fff;border-bottom:5px solid #bf112a}
header strong{font-size:25px;font-weight:900;letter-spacing:-.045em}
header a{font-weight:700;font-size:17px;text-decoration:none;color:#191e1f}
main{display:grid;grid-template-columns:1.36fr .64fr;min-height:640px}
.intro{padding:88px 9% 70px 9%;display:flex;flex-direction:column;align-items:flex-start}
.eyebrow{color:#b5122b;font-weight:800;font-size:12px;letter-spacing:.13em}
h1{font-size:clamp(58px,7.2vw,108px);line-height:.94;letter-spacing:-.075em;margin:38px 0 24px}
p{font-size:18px;line-height:1.55;max-width:520px}
aside{background:#191d1f;color:#fff;padding:90px 10%;display:flex;flex-direction:column;justify-content:center;gap:18px}
aside small{font-weight:800;letter-spacing:.17em;color:#e7939e}
aside h2{font-size:39px;line-height:1.02;margin:0;letter-spacing:-.05em}
aside p{font-size:16px;color:#cfd0cb}
a.action{display:inline-block;background:#b5122b;color:white;padding:17px 24px;text-decoration:none;font-weight:800;margin-top:18px;font-size:15px}
.visual{height:330px;background:center/cover url("assets/garage-service.webp")}
@media(max-width:700px){header{height:73px;padding:0 20px}header strong{font-size:18px}header a{font-size:13px}main{grid-template-columns:1fr}.intro{padding:54px 22px}h1{font-size:62px}aside{padding:35px 22px}aside h2{font-size:30px}.visual{height:240px}}
</style></head><body><header><strong>S. RÄSÄSEN AUTOHUOLTO OY</strong><a href="#yhteys">09 302 113</a></header>
<main><section class="intro"><div class="eyebrow">AUTOHUOLTO KERAVALLA</div>
<h1>Autosi<br>huolto,<br>selkeästi.</h1><p>Huollot ja korjaukset kaikille merkeille. Öljynvaihtoon pääset myös ilman ajanvarausta.</p>
<a class="action" href="tel:+3589302113">Kysy huollosta</a></section>
<aside id="yhteys"><small>KERAVAN KORJAAMO</small><h2>Suoraan<br>huoltoon.</h2><p>Heisitie 4 · 04260 Kerava</p><p>Ma–pe klo 8–17</p><p>09 302 113</p></aside></main>
<div class="visual" aria-label="Lisensoitu työkuva autohuollosta"></div></body></html>"""

DIRECT_2 = """<!doctype html><html lang="fi"><head>""" + SHARED + """<style>
*{box-sizing:border-box}body{margin:0;font-family:Arial,sans-serif;background:#161b1e;color:#fff}
header{height:77px;background:#c40e29;color:#fff;display:flex;align-items:center;justify-content:space-between;padding:0 5%}
header strong{font-size:27px;letter-spacing:-.045em}header a{color:white;font-size:16px;font-weight:800;text-decoration:none}
main{position:relative;min-height:650px;background:linear-gradient(90deg,#11171bdf 0%,#11171ba8 43%,#11171b0a 100%),url("assets/garage-hero.webp") center/cover;display:flex;align-items:center}
.hero{padding:88px 6%;max-width:940px}
.eyebrow{font-size:13px;letter-spacing:.17em;color:#efb2b8;font-weight:800}
h1{font-size:clamp(64px,7.8vw,112px);line-height:.96;letter-spacing:-.06em;margin:34px 0}
p{font-size:20px;line-height:1.55;color:#e2e2dc;max-width:600px}
a.action{background:#c40e29;display:inline-block;padding:20px 28px;text-decoration:none;color:#fff;font-size:16px;font-weight:800;margin-top:22px}
footer{padding:35px 6%;background:#f8f5ef;color:#1b1e1f;display:grid;grid-template-columns:repeat(3,1fr);gap:25px;font-size:15px;font-weight:800}
footer span{border-left:4px solid #c40e29;padding-left:16px}
@media(max-width:700px){header{padding:0 20px;height:74px}header strong{font-size:17px}header a{font-size:13px}main{min-height:625px;background-position:60% center}.hero{padding:65px 22px}h1{font-size:61px}p{font-size:16px}footer{grid-template-columns:1fr;padding:28px 22px;gap:20px}}
</style></head><body><header><strong>S. RÄSÄSEN AUTOHUOLTO OY</strong><a href="tel:+3589302113">Soita 09 302 113</a></header>
<main><div class="hero"><div class="eyebrow">AUTOFIT-KETJUN KORJAAMO · KERAVA</div>
<h1>Huolto,<br>johon on<br>helppo tulla.</h1>
<p>Autohuoltoa henkilö- ja matkailuautoille. Kaikki merkit, myös öljynvaihto ilman ajanvarausta.</p>
<a class="action" href="tel:+3589302113">Ota yhteyttä korjaamoon</a></div></main>
<footer><span>Heisitie 4, Kerava</span><span>Ma–pe klo 8–17</span><span>Huollot ja korjaukset kaikille merkeille</span></footer></body></html>"""

OPTIONS = {
    "tietoensin": DIRECT_1,
    "kuvaensin": DIRECT_2,
}
for concept, html in OPTIONS.items():
    (DEMO / f".temporary-{concept}.html").write_text(html, encoding="utf-8")

records = []
previews = []
with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    for concept in ("tietoensin","kuvaensin","editorial"):
        rec = {"id":concept}
        for name, width, height in (("desktop",1440,900),("mobile",390,844)):
            page = browser.new_page(viewport={"width":width,"height":height}, device_scale_factor=1)
            source = DEMO / ("index.html" if concept=="editorial" else f".temporary-{concept}.html")
            page.goto(source.as_uri(), wait_until="load", timeout=20000)
            page.wait_for_timeout(300)
            problems=page.evaluate("""() => ({
                overflow:document.documentElement.scrollWidth>innerWidth+2,
                title:document.title,
                unloaded:[...document.images].filter(x=>x.complete&&!x.naturalWidth).length,
                backgroundImage:getComputedStyle(document.querySelector('main')).backgroundImage
            })""")
            if problems["overflow"] or problems["unloaded"]:
                raise RuntimeError(f"Concept {concept} {name} invalid: {problems}")
            destination = OUT / f"{concept}-{name}.png"
            page.screenshot(path=str(destination),full_page=True,timeout=25000,animations="disabled")
            rec[name] = "_concept_evidence/" + destination.name
            rec[name+"_sha256"] = hashlib.sha256(destination.read_bytes()).hexdigest()
            print("CONCEPT",concept,name,rec[name+"_sha256"],"size",destination.stat().st_size)
            if name=="desktop":
                im=Image.open(destination).convert("RGB");im.thumbnail((540,800))
                previews.append(im.copy())
            page.close()
        records.append(rec)
    browser.close()
for concept in OPTIONS:
    (DEMO / f".temporary-{concept}.html").unlink()
(OUT / "hashes.json").write_text(json.dumps(records,indent=2),encoding="utf-8")
if previews:
    target=Image.new("RGB",(max(im.width for im in previews)*len(previews), max(im.height for im in previews)),"white")
    for i,im in enumerate(previews):target.paste(im,(i*max(im.width for im in previews),0))
    b=io.BytesIO();target.save(b,"JPEG",quality=40,optimize=True)
    print("CONCEPT_COMPARISON_BASE64="+base64.b64encode(b.getvalue()).decode())
print("All six real concept screenshots captured for separate design review.")

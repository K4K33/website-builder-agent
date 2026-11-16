"""Bind and materialize a complete, searchable local product catalogue."""
from __future__ import annotations

from hashlib import sha256
import html
import json
import os
import posixpath
from pathlib import Path

from bs4 import BeautifulSoup


def bind_commerce_architecture(research: dict) -> None:
    captures = research.get("commerce_inventory") or []
    if not captures:
        return
    architecture = research.get("site_architecture") or {}
    pages = architecture.get("pages") if isinstance(architecture, dict) else None
    if not isinstance(pages, list):
        return
    candidates = [p for p in pages if isinstance(p, dict) and any(
        word in str(p.get("path") or "").casefold()
        for word in ("kauppa", "shop", "tuotte", "product", "catalog"))]
    if candidates:
        route = str(candidates[0]["path"])
        sections = candidates[0].setdefault("section_ids", [])
        if "kauppa-valikoima" not in sections:
            sections.append("kauppa-valikoima")
    else:
        if len(pages) >= 14:
            raise RuntimeError("Complete shop catalogue needs a real local route.")
        route = "verkkokauppa.html"
        pages.append({
            "path": route,
            "purpose": "Koko lähteestä tarkistettu tuotevalikoima paikallisena hakemistona",
            "user_task": "Asiakas hakee tuotteen ja jatkaa oikealle tuotesivulle ostamaan",
            "section_ids": ["kauppa-valikoima"],
        })
    for capture in captures:
        capture["target"] = route


def commerce_builder_brief(research: dict) -> list[dict]:
    return [{
        "shop_url": c.get("shop_url"), "target": c.get("target"),
        "product_count": c.get("observed_product_count"),
        "render_mode": c.get("render_mode"),
        "requirement": "Pidä reitti navigaatiossa. Hakemisto ja toimivat tuotelinkit lisätään deterministisesti.",
    } for c in (research.get("commerce_inventory") or [])]


def _catalogue_payload(capture: dict) -> tuple[str, str]:
    rows = [{k: product.get(k, "") for k in ("url", "name", "price_text")}
            for product in capture.get("products") or []]
    raw = json.dumps(rows, ensure_ascii=False, separators=(",", ":"))
    return raw, sha256(raw.encode("utf-8")).hexdigest()


def attach_commerce_catalogue(pages: dict[str, str], research: dict) -> tuple[dict[str, str], dict[str, str]]:
    artifacts: dict[str, str] = {}
    for index, capture in enumerate(research.get("commerce_inventory") or []):
        if capture.get("render_mode") != "local_paginated_catalogue":
            continue
        target = str(capture.get("target") or "")
        if target not in pages:
            raise RuntimeError("Commerce target route is absent from generated pages.")
        raw, digest = _catalogue_payload(capture)
        asset = f"assets/commerce-catalogue-{index + 1}.js"
        artifacts[asset] = "window.KAURIVO_CATALOGUE_PRODUCTS=" + raw + ";\n"
        soup = BeautifulSoup(pages[target], "html.parser")
        main = soup.find("main")
        if main is None:
            raise RuntimeError("Commerce route needs a main element.")
        old = soup.find(id="kauppa-valikoima")
        if old:
            old.decompose()
        relative_asset = posixpath.relpath(asset, posixpath.dirname(target) or ".")
        block = BeautifulSoup(f'''<section id="kauppa-valikoima" data-shop-catalogue
          data-catalog-sha256="{digest}" data-product-count="{len(capture.get('products') or [])}">
          <style>#kauppa-valikoima{{padding:clamp(3rem,7vw,7rem) clamp(1rem,5vw,5rem)}}
          #kauppa-valikoima [data-shop-controls]{{display:grid;gap:1rem;margin-bottom:2rem}}
          #kauppa-valikoima input{{font:inherit;padding:.9rem 1rem;border:1px solid currentColor;border-radius:.45rem;max-width:34rem;width:100%;background:transparent;color:inherit}}
          #kauppa-valikoima [data-catalog-grid]{{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,15rem),1fr));gap:1rem}}
          #kauppa-valikoima article{{border:1px solid color-mix(in srgb,currentColor 22%,transparent);border-radius:.7rem;padding:1.25rem;display:flex;flex-direction:column;gap:.65rem;min-height:10rem}}
          #kauppa-valikoima article h3,#kauppa-valikoima article p{{margin:0}}#kauppa-valikoima article a{{margin-top:auto;color:inherit;font-weight:700}}
          #kauppa-valikoima [data-catalog-pages]{{display:flex;gap:.75rem;margin-top:2rem}}#kauppa-valikoima button{{font:inherit;padding:.75rem 1rem}}</style>
          <div data-shop-controls><h2>Tuotevalikoima</h2>
          <label>Hae tuotteita <input type="search" data-catalog-search autocomplete="off"></label>
          <p data-catalog-status aria-live="polite"></p></div>
          <div data-catalog-grid></div><nav aria-label="Tuotevalikoiman sivutus" data-catalog-pages></nav>
          <noscript>Tuotehaku tarvitsee JavaScriptin. <a href="{html.escape(str(capture.get('shop_url') or ''))}">Avaa alkuperäinen verkkokauppa</a>.</noscript>
          <script src="{relative_asset}"></script><script>{_CONTROLLER}</script>
          </section>''', "html.parser")
        footer = main.find("footer", recursive=False)
        (footer.insert_before(block) if footer else main.append(block))
        pages[target] = str(soup)
    return pages, artifacts


def write_commerce_artifacts(root: Path, artifacts: dict[str, str]) -> None:
    for relative, content in artifacts.items():
        destination = root / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        temporary = destination.with_name("." + destination.name + ".tmp")
        temporary.write_text(content, encoding="utf-8")
        os.replace(temporary, destination)


_CONTROLLER = r'''(()=>{const all=Array.isArray(window.KAURIVO_CATALOGUE_PRODUCTS)?window.KAURIVO_CATALOGUE_PRODUCTS:[];
const root=document.currentScript.closest('[data-shop-catalogue]'),grid=root.querySelector('[data-catalog-grid]'),status=root.querySelector('[data-catalog-status]'),pages=root.querySelector('[data-catalog-pages]'),input=root.querySelector('[data-catalog-search]');let page=0;const size=24;
const esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
function draw(){const q=input.value.trim().toLocaleLowerCase('fi');const found=q?all.filter(p=>p.name.toLocaleLowerCase('fi').includes(q)):all;const max=Math.max(1,Math.ceil(found.length/size));page=Math.min(page,max-1);grid.innerHTML=found.slice(page*size,(page+1)*size).map(p=>`<article data-product-source="${esc(p.url)}"><h3>${esc(p.name)}</h3><p>${esc(p.price_text)}</p><a href="${esc(p.url)}" target="_blank" rel="noreferrer">Avaa tuote verkkokaupassa</a></article>`).join('');status.textContent=`${found.length} tuotetta, sivu ${page+1}/${max}`;pages.innerHTML=`<button type="button" data-prev ${page<1?'disabled':''}>Edellinen</button><button type="button" data-next ${page>=max-1?'disabled':''}>Seuraava</button>`;pages.querySelector('[data-prev]').onclick=()=>{page--;draw()};pages.querySelector('[data-next]').onclick=()=>{page++;draw()};window.KAURIVO_CATALOGUE_READY=true}
input.addEventListener('input',()=>{page=0;draw()});draw()})()'''

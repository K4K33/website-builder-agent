"""Sales demo pipeline: one prospect's source site -> one premium page.

Zero-AI collection, one free model call, deterministic verification, render:

1. fetch up to six public HTML pages (``kaurivo_demo_readiness.fetch_html``
   rules: safe hosts, validated redirects) and collect visible text, own photo
   URLs, phone and e-mail
2. download up to six own photos (safe public URLs, image/*, >= 900 px wide)
3. ask a free model ONCE to fill ``sales_demo.CONTENT_BRIEF`` from the text
4. verify every model field against the source text; unverifiable services,
   chapters, captions and reference lines are dropped, an unverifiable
   headline or no verified service stops the demo (``SalesDemoBlocked``)
5. with fewer than four own photos, add labelled stock illustrations
6. render with ``sales_demo.render_sales_demo``

Nothing here contacts the company or publishes anything.
"""
from __future__ import annotations

import json
import re
import socket
import unicodedata
from io import BytesIO
from pathlib import Path
from urllib.parse import urlsplit

import requests
from bs4 import BeautifulSoup

MAX_PAGES = 6
MAX_OWN_PHOTOS = 6
MIN_PHOTO_WIDTH = 900
MAX_SOURCE_CHARS = 14_000
_PHONE = re.compile(r"(?:\+358|\b0)[\s-]?\d{1,3}(?:[\s-]?\d{2,4}){2,3}\b")
_EMAIL = re.compile(r"\b[\w.+-]+\s?(?:@|\(@\)|\[at\]|\(at\))\s?[\w-]+\.[\w.-]{2,}\b", re.I)


class SalesDemoBlocked(RuntimeError):
    def __init__(self, code: str, detail: str = ""):
        super().__init__(code)
        self.code = code
        self.detail = detail


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKC", str(text or "")).casefold()
    text = text.replace("m²", "m2")
    return " ".join(re.sub(r"[^\w\s]", " ", text).split())


def _stems(text: str) -> list[str]:
    """Content words as 5-letter stems (Finnish inflection tolerant)."""
    return [w[:5] if len(w) > 5 else w for w in _norm(text).split() if len(w) >= 3 or w.isdigit()]


def supported(claim: str, source_text: str, *, share: float = 0.8) -> bool:
    """True when the claim's words (and every number) occur in the source."""
    stems = _stems(claim)
    if not stems:
        return False
    source = _norm(source_text)
    source_stems = set(_stems(source_text))
    numbers = [w for w in _norm(claim).split() if w.isdigit()]
    if any(not re.search(r"(?<!\d)" + n + r"(?!\d)", source) for n in numbers):
        return False
    hits = sum(1 for s in stems if s in source_stems)
    return hits / len(stems) >= share


def verify_plan(plan: dict, source_text: str) -> tuple[dict, list[str]]:
    """Return (plan with only source-supported fields, list of dropped items)."""
    dropped: list[str] = []
    out = dict(plan)
    if not supported(plan.get("headline", ""), source_text, share=0.75):
        raise SalesDemoBlocked("sales_headline_unverified", "Otsikkoa ei löydy lähdesivun sanoista")
    keep = []
    for service in plan.get("services") or []:
        if not isinstance(service, dict):
            continue
        if supported(service.get("name", ""), source_text):
            text = service.get("text", "")
            keep.append({"name": service.get("name", ""),
                         "text": text if supported(text, source_text, share=0.7) else ""})
        else:
            dropped.append("service:" + str(service.get("name", ""))[:40])
    if not keep:
        raise SalesDemoBlocked("sales_services_unverified", "Yhtään palvelua ei voitu todentaa lähteestä")
    out["services"] = keep
    out["chapters"] = [c for c in plan.get("chapters") or [] if supported(c, source_text, share=0.7)]
    if not supported(plan.get("statement", ""), source_text, share=0.7):
        dropped.append("statement")
        out["statement"] = ""
    if plan.get("contact_lead") and not supported(plan["contact_lead"], source_text, share=0.6):
        out["contact_lead"] = ""
    out["photo_captions"] = [c if supported(c, source_text, share=0.7) else ""
                             for c in plan.get("photo_captions") or []]
    groups = []
    for group in plan.get("proof") or []:
        if not isinstance(group, dict):
            continue
        items = [i for i in group.get("items") or [] if supported(i, source_text, share=1.0)]
        dropped += ["proof:" + str(i)[:40] for i in group.get("items") or [] if i not in items]
        if len(items) >= 2 and supported(group.get("title", ""), source_text, share=0.7):
            groups.append({"title": group["title"], "items": items})
    out["proof"] = groups
    return out, dropped


def _contacts(texts: list[str], soups: list[BeautifulSoup]) -> tuple[str, str]:
    phone = email = ""
    for soup in soups:
        for a in soup.select("a[href^='tel:']"):
            phone = phone or a.get_text(" ", strip=True) or a["href"][4:]
        for a in soup.select("a[href^='mailto:']"):
            email = email or a["href"][7:].split("?")[0]
    joined = " ".join(texts)
    if not phone and (m := _PHONE.search(joined)):
        phone = m.group(0)
    if not email and (m := _EMAIL.search(joined)):
        email = re.sub(r"\s?(?:\(@\)|\[at\]|\(at\))\s?", "@", m.group(0), flags=re.I).replace(" ", "")
    return phone.strip()[:40], email.strip()[:120]


def collect_source(url: str, *, get=requests.get, resolve=socket.getaddrinfo) -> dict:
    """Fetch public pages; returns text, own photo URLs and contacts."""
    from utils.kaurivo_demo_readiness import (_internal_links, _photo_urls, _site_key,
                                              _visible_text, fetch_html)
    final, html = fetch_html(url, get=get, resolve=resolve)
    if not html:
        raise SalesDemoBlocked("sales_source_unreachable", str(final)[:40])
    pages = [(final, html)]
    for link in _internal_links(BeautifulSoup(html, "html.parser"), final)[:MAX_PAGES * 2]:
        if len(pages) >= MAX_PAGES:
            break
        page_url, page_html = fetch_html(link, get=get, resolve=resolve)
        if page_html and _site_key(urlsplit(page_url).hostname or "") == _site_key(urlsplit(final).hostname or ""):
            pages.append((page_url, page_html))
    texts, soups, photos = [], [], []
    for page_url, page_html in pages:
        soup = BeautifulSoup(page_html, "html.parser")
        soups.append(BeautifulSoup(page_html, "html.parser"))
        for photo in sorted(_photo_urls(soup, page_url)):
            if photo not in photos:
                photos.append(photo)
        texts.append(_visible_text(soup))
    phone, email = _contacts(texts, soups)
    text = "\n\n".join(texts)
    return {"url": final, "pages": len(pages), "text": text[:MAX_SOURCE_CHARS * 2],
            "photo_urls": photos[:24], "phone": phone, "email": email}


def download_own_photos(urls: list[str], folder: Path, *, get=requests.get,
                        resolve=socket.getaddrinfo, limit: int = MAX_OWN_PHOTOS) -> list[Path]:
    from PIL import Image
    from utils.kaurivo_demo_readiness import safe_url
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    saved: list[Path] = []
    for url in urls:
        if len(saved) >= limit:
            break
        safe = safe_url(url, resolve)
        if not safe:
            continue
        try:
            reply = get(safe, timeout=(5, 20), allow_redirects=False,
                        headers={"User-Agent": "KaurivoSalesDemo/1.0"})
            if reply.status_code != 200 or not reply.headers.get("content-type", "").startswith("image/"):
                continue
            data = reply.content[:8_000_000]
            with Image.open(BytesIO(data)) as image:
                image = image.convert("RGB")
                if image.width < MIN_PHOTO_WIDTH or image.width < image.height * 0.6:
                    continue
                image.thumbnail((2400, 2400))
                target = folder / f"oma-{len(saved) + 1}.webp"
                image.save(target, "WEBP", quality=86)
                saved.append(target)
        except Exception:
            continue
    return saved


def ask_plan(company_name: str, source: dict, photo_count: int, *, ask=None) -> dict:
    from utils.sales_demo import CONTENT_BRIEF
    if ask is None:
        from utils.claude_client import ask_claude_json as ask
    prompt = (f"Company: {company_name}\nPhotos provided: {photo_count}\n"
              f"Verified source text (the ONLY allowed facts):\n<<<\n{source['text'][:MAX_SOURCE_CHARS]}\n>>>")
    plan = ask(CONTENT_BRIEF, prompt, max_tokens=4000, stage="research")
    if not isinstance(plan, dict):
        raise SalesDemoBlocked("sales_plan_invalid")
    return plan


def display_name(registry_name: str, source_text: str) -> str:
    """The company's name as written on its own site, else a readable casing
    of the registry form (PRH stores many names in capitals)."""
    name = " ".join(str(registry_name or "").split())
    match = re.search(re.escape(name), source_text or "", re.I)
    if match and not match.group(0).isupper():
        return match.group(0)
    if not name.isupper():
        return name
    small = {"ja", "och", "and", "&"}
    fixed = {"OY": "Oy", "AB": "Ab", "OYJ": "Oyj", "KY": "Ky", "TMI": "Tmi", "AY": "Ay", "RY": "ry"}
    words = []
    for i, word in enumerate(name.split()):
        if word in fixed:
            words.append(fixed[word])
        elif i and word.lower() in small:
            words.append(word.lower())
        else:
            words.append(word[:1] + word[1:].lower())
    return " ".join(words)


class _Step:
    """Tag any failure with the pipeline step (no content in the tag)."""
    def __init__(self, name):
        self.name = name

    def __enter__(self):
        return self

    def __exit__(self, kind, exc, tb):
        if exc is not None and not getattr(exc, "sales_step", None):
            try:
                exc.sales_step = self.name
            except Exception:
                pass
        return False


def build_sales_demo(company_name: str, url: str, out_dir: Path, *, work_dir: Path,
                     get=requests.get, resolve=socket.getaddrinfo, ask=None,
                     fetch_stock=None, make_sequence=None) -> dict:
    """Collect, plan, verify and render. Returns a summary without page text."""
    from utils.sales_demo import render_sales_demo, validate_plan
    from utils.stock_media import MIN_OWN_PHOTOS, fetch_stock_photos
    with _Step("collect"):
        source = collect_source(url, get=get, resolve=resolve)
    if len(_norm(source["text"]).split()) < 40:
        raise SalesDemoBlocked("sales_source_text_thin", "Lähdesivulla alle 40 sanaa")
    with _Step("photos"):
        own = download_own_photos(source["photo_urls"], Path(work_dir) / "own", get=get, resolve=resolve)
    with _Step("plan"):
        plan = ask_plan(company_name, source, len(own), ask=ask)
    with _Step("verify"):
        plan, dropped = verify_plan(plan, source["text"])
    photos, credits = list(own), [None] * len(own)
    sequence = None
    from utils.sales_demo import build_scene_for
    topic = " ".join([plan.get("headline", "")] + [s["name"] for s in plan["services"]])
    # A purpose-made 3D build scene (free, no AI) is the strongest hero; with it
    # only the company's own photos are added, never stock from other cameras.
    scene = build_scene_for(topic)
    # A reviewed construction film for the trade (made once, reused) leads the hero.
    from utils.build_film import film_for
    film = film_for(topic)
    if film:
        scene = None
        with _Step("stock"):
            stock = (fetch_stock or fetch_stock_photos)(
                topic, Path(work_dir) / "stock", count=4) if len(own) < MIN_OWN_PHOTOS else []
        photos += [Path(s["path"]) for s in stock]
        credits += stock
    if not film and not scene and len(own) < MIN_OWN_PHOTOS:
        topic = " ".join([plan.get("headline", "")] + [s["name"] for s in plan["services"]])
        # One illustrated build sequence carries the hero; stock fills the rest.
        with _Step("sequence"):
            if make_sequence is None:
                from utils.illustrated_sequence import generate_sequence as make_sequence
            sequence = make_sequence(topic, Path(work_dir) / "sequence")
        with _Step("stock"):
            stock = (fetch_stock or fetch_stock_photos)(
                topic, Path(work_dir) / "stock",
                count=max(3, MIN_OWN_PHOTOS - len(own) + 1)) if not sequence else []
        # Own photos stay first; stock only fills the gap.
        photos += [Path(s["path"]) for s in stock]
        credits += stock
    if not photos and not sequence and not scene and not film:
        raise SalesDemoBlocked("sales_no_photos", "Ei omia eikä kuvapankkikuvia aiheeseen")
    with _Step("render"):
        validate_plan(plan, photos or (sequence["paths"] if sequence else film["frames"][-1:] if film else [Path("build3d")]))
        company = {"name": display_name(company_name, source["text"]), "phone": source["phone"],
                   "email": source["email"]}
        if sequence:
            plan["hero_style"] = "depth"
        page = render_sales_demo(company=company, plan=plan, photos=photos, out_dir=Path(out_dir),
                                 credits=credits,
                                 sequence=sequence["paths"] if sequence else None,
                                 sequence_labels=sequence["labels"] if sequence else None,
                                 sequence_note=sequence["note"] if sequence else "", build_scene=scene,
                                 sequence_transitions=sequence.get("transitions") if sequence else None,
                                 film=film)
    return {"page": str(page), "own_photos": len(own), "stock_photos": sum(1 for c in credits if c),
            "sequence_frames": len(sequence["paths"]) if sequence else 0, "build_scene": scene or "", "film": (film or {}).get("trade", ""),
            "services": len(plan["services"]), "proof_groups": len(plan.get("proof") or []),
            "dropped": dropped[:20], "source_pages": source["pages"]}

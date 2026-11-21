"""Licensed stock photos for sales demos when a prospect has too few own photos.

Sales demos may use free stock photography as clearly labelled illustrations
(havainnekuvat). The final customer site uses the company's own photos, asked
for once the company is interested. Sources: Pexels (if a key exists; new
keys are paused), Pixabay (free key, KAURIVO_PIXABAY_API_KEY) and Openverse
(no key; only CC0, Public Domain Mark and CC BY). We show the photographer,
source and, for Creative Commons, the licence on every image,
avoid photos of identifiable people where possible, and never present a stock
photo as the company's own work.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re

API = "https://api.pexels.com/v1/search"
MIN_OWN_PHOTOS = 4
MAX_STOCK = 5
_KEY = re.compile(r"[A-Za-z0-9]{40,80}")
_PEOPLE = re.compile(r"\b(man|woman|men|women|person|people|girl|boy|child|portrait|face|selfie|couple)\b", re.I)

# Industry terms in the plan/services -> English stock queries (most specific first).
QUERIES = (
    (r"kylpyhuone|laatoit|laatta|vedeneristy", ("modern bathroom interior tiles", "bathroom renovation tiling", "tiled shower interior")),
    (r"maalaus|maalari|tasoitus", ("freshly painted interior wall", "house exterior painting", "paint roller wall")),
    (r"keittiö", ("modern kitchen interior", "kitchen cabinets installation")),
    (r"katto|kattoremontti|peltikatto", ("metal roof house", "roofing construction")),
    (r"sähkö|sähköasennus", ("electrical panel installation", "electrician tools wiring")),
    (r"lvi|putki|vesijohto", ("plumbing pipes installation", "modern bathroom sink")),
    (r"siivous|puhtaus|ikkunanpesu", ("clean bright living room", "cleaning supplies home")),
    (r"rakennus|rakentaminen|omakotitalo|rivitalo|saneeraus|remontti",
     ("wooden house construction frame", "house renovation interior", "modern nordic house exterior")),
    (r"kahvila|ravintola|lounas|kahvi", ("cozy cafe interior", "coffee shop counter", "restaurant table food")),
    (r"kampaamo|parturi|kauneus|hius", ("hair salon interior", "barber shop chair")),
    (r"auto|korjaamo|rengas", ("car repair garage", "mechanic workshop tools")),
)


def api_key() -> str:
    key = os.getenv("KAURIVO_PEXELS_API_KEY", "").strip()
    return key if _KEY.fullmatch(key) else ""


def queries_for(text: str) -> list[str]:
    text = str(text or "").casefold()
    for pattern, queries in QUERIES:
        if re.search(pattern, text):
            return list(queries)
    return []


def pixabay_key() -> str:
    key = os.getenv("KAURIVO_PIXABAY_API_KEY", "").strip()
    return key if re.fullmatch(r"[A-Za-z0-9-]{20,80}", key) else ""


# Openverse indexes many sources; download only from these known image hosts.
_OPENVERSE_HOSTS = ("live.staticflickr.com", "farm1.staticflickr.com", "farm2.staticflickr.com",
                    "farm3.staticflickr.com", "farm4.staticflickr.com", "farm5.staticflickr.com",
                    "farm6.staticflickr.com", "farm7.staticflickr.com", "farm8.staticflickr.com",
                    "farm9.staticflickr.com", "upload.wikimedia.org", "images.rawpixel.com")
_OPENVERSE_OK = {"cc0": "CC0", "pdm": "Public Domain Mark", "by": "CC BY"}


def _pexels(session, query):
    key = api_key()
    if not key:
        return
    reply = session.get(API, headers={"Authorization": key}, timeout=(5, 20),
                        params={"query": query, "orientation": "landscape", "per_page": 15})
    if reply.status_code != 200:
        return
    for p in reply.json().get("photos") or []:
        src = (p.get("src") or {}).get("large2x") or (p.get("src") or {}).get("large")
        yield {"id": f"pexels-{p.get('id')}", "width": p.get("width", 0), "height": p.get("height", 0),
               "text": p.get("alt"), "url": src, "hosts": ("images.pexels.com",),
               "creator": p.get("photographer"), "creator_url": p.get("photographer_url"),
               "source_url": p.get("url"), "licence": "Pexels License", "provider": "Pexels"}


def _pixabay(session, query):
    key = pixabay_key()
    if not key:
        return
    reply = session.get("https://pixabay.com/api/", timeout=(5, 20),
                        params={"key": key, "q": query, "image_type": "photo", "orientation": "horizontal",
                                "safesearch": "true", "per_page": 20})
    if reply.status_code != 200:
        return
    for h in reply.json().get("hits") or []:
        yield {"id": f"pixabay-{h.get('id')}", "width": h.get("imageWidth", 0), "height": h.get("imageHeight", 0),
               "text": h.get("tags"), "url": h.get("largeImageURL"), "hosts": ("pixabay.com", "cdn.pixabay.com"),
               "creator": h.get("user"), "creator_url": "", "source_url": h.get("pageURL"),
               "licence": "Pixabay Content License", "provider": "Pixabay"}


def _openverse(session, query):
    if os.getenv("KAURIVO_OPENVERSE", "1") == "0":
        return
    # Openverse matches all words; long queries return almost nothing, so use the
    # last two words (the subject), and filter size and orientation locally.
    short = " ".join(str(query).split()[-2:])
    reply = session.get("https://api.openverse.org/v1/images/", timeout=(5, 20),
                        params={"q": short, "license": "cc0,pdm,by", "mature": "false", "page_size": 20})
    if reply.status_code != 200:
        return
    for r in reply.json().get("results") or []:
        licence = _OPENVERSE_OK.get(str(r.get("license") or "").lower())
        if not licence:
            continue
        version = str(r.get("license_version") or "").strip()
        yield {"id": f"openverse-{r.get('id')}", "width": r.get("width") or 0, "height": r.get("height") or 0,
               "text": " ".join(str(r.get(k) or "") for k in ("title", "tags")), "url": r.get("url"),
               "hosts": _OPENVERSE_HOSTS, "min_width": 1000, "creator": r.get("creator"), "creator_url": r.get("creator_url"),
               "source_url": r.get("foreign_landing_url"),
               "licence": licence + (f" {version}" if licence == "CC BY" and version else ""),
               "provider": "Openverse"}


PROVIDERS = (_pexels, _pixabay, _openverse)


def _usable(photo: dict) -> bool:
    width, height = int(photo.get("width") or 0), int(photo.get("height") or 0)
    return width >= int(photo.get("min_width") or 1200) and width > height * 1.2 and not _PEOPLE.search(str(photo.get("text") or ""))


def _allowed_url(photo: dict) -> bool:
    from urllib.parse import urlsplit
    url = str(photo.get("url") or "")
    if not url.startswith("https://"):
        return False
    if photo.get("hosts"):
        return urlsplit(url).hostname in photo["hosts"]
    try:
        from utils.kaurivo_demo_readiness import safe_url
        return bool(safe_url(url))
    except Exception:
        return False


def fetch_stock_photos(topic_text: str, folder: Path, *, count: int = MAX_STOCK,
                       session=None) -> list[dict]:
    """Download up to ``count`` licensed photos; returns credit records.

    Providers in order: Pexels (if a key exists), Pixabay (free key), then
    Openverse (no key; only CC0, Public Domain Mark and CC BY, with credit).
    Each record: {"path", "photographer", "photographer_url", "source_url",
    "licence", "provider", "alt"}.
    """
    queries = queries_for(topic_text)
    if not queries:
        return []
    if session is None:
        import requests
        session = requests
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    chosen, seen = [], set()
    for provider in PROVIDERS:
        for query in queries:
            if len(chosen) >= count:
                break
            try:
                candidates = list(provider(session, query) or [])
            except Exception:
                continue
            for photo in candidates:
                if len(chosen) >= count:
                    break
                if photo["id"] in seen or not _usable(photo) or not _allowed_url(photo):
                    continue
                try:
                    image = session.get(photo["url"], timeout=(5, 30))
                    if image.status_code != 200 or not image.headers.get("content-type", "").startswith("image/"):
                        continue
                    safe_id = re.sub(r"[^a-z0-9-]", "", str(photo["id"]).lower())[:60]
                    target = folder / f"{safe_id}.jpg"
                    target.write_bytes(image.content[:12_000_000])
                except Exception:
                    continue
                seen.add(photo["id"])
                chosen.append({"path": str(target), "photographer": str(photo.get("creator") or "")[:80],
                               "photographer_url": str(photo.get("creator_url") or ""),
                               "source_url": str(photo.get("source_url") or ""),
                               "licence": photo["licence"], "provider": photo["provider"],
                               "alt": str(photo.get("text") or "")[:140]})
        if len(chosen) >= count:
            break
    (folder / "credits.json").write_text(json.dumps(chosen, ensure_ascii=False, indent=1), encoding="utf-8")
    return chosen

"""Licensed stock photos for sales demos when a prospect has too few own photos.

Sales demos may use free stock photography as clearly labelled illustrations
(havainnekuvat). The final customer site uses the company's own photos, asked
for once the company is interested. Source: the Pexels API (free key in the
KAURIVO_PEXELS_API_KEY secret). The Pexels licence allows free commercial use
without attribution; we still show the photographer and Pexels on every image,
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


def _usable(photo: dict) -> bool:
    alt = str(photo.get("alt") or "")
    return (photo.get("width", 0) >= 1600 and photo.get("width", 0) > photo.get("height", 1)
            and not _PEOPLE.search(alt))


def fetch_stock_photos(topic_text: str, folder: Path, *, count: int = MAX_STOCK,
                       session=None) -> list[dict]:
    """Download up to ``count`` licensed photos; returns credit records.

    Each record: {"path", "photographer", "photographer_url", "source_url",
    "licence": "Pexels License", "alt"}. Empty list without a key or match.
    """
    key = api_key()
    queries = queries_for(topic_text)
    if not key or not queries:
        return []
    if session is None:
        import requests
        session = requests
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    chosen, seen = [], set()
    for query in queries:
        if len(chosen) >= count:
            break
        try:
            reply = session.get(API, headers={"Authorization": key}, timeout=(5, 20),
                                params={"query": query, "orientation": "landscape", "per_page": 15})
            if reply.status_code != 200:
                continue
            photos = reply.json().get("photos") or []
        except Exception:
            continue
        for photo in photos:
            if len(chosen) >= count:
                break
            if photo.get("id") in seen or not _usable(photo):
                continue
            src = (photo.get("src") or {}).get("large2x") or (photo.get("src") or {}).get("large")
            if not str(src or "").startswith("https://images.pexels.com/"):
                continue
            try:
                image = session.get(src, timeout=(5, 30))
                if image.status_code != 200 or not image.headers.get("content-type", "").startswith("image/"):
                    continue
                target = folder / f"pexels-{int(photo['id'])}.jpg"
                target.write_bytes(image.content[:12_000_000])
            except Exception:
                continue
            seen.add(photo.get("id"))
            chosen.append({"path": str(target), "photographer": str(photo.get("photographer") or "")[:80],
                           "photographer_url": str(photo.get("photographer_url") or ""),
                           "source_url": str(photo.get("url") or ""),
                           "licence": "Pexels License", "alt": str(photo.get("alt") or "")[:140]})
    (folder / "credits.json").write_text(json.dumps(chosen, ensure_ascii=False, indent=1), encoding="utf-8")
    return chosen

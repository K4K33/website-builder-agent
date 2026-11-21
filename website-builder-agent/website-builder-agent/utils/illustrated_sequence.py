"""Illustrated build sequence for sales demos (free Cloudflare Workers AI).

The reference sites look premium because ONE purpose-made visual drives the
page (a house that builds itself on scroll). A prospect without own photos
gets the same device as an illustration: one scene, one camera, one seed,
four build stages; only the surface/fixture words change between prompts,
which keeps the room consistent. The page labels it "Havainnekuva,
tekoälyllä luotu" and never presents it as the company's work.

Runs only when the owner-confirmed Workers Free opt-in is enabled
(``cloudflare_free_ai.enabled``). Failure returns no sequence and the demo
falls back to stock illustrations.
"""
from __future__ import annotations

import base64
import os
import re
from io import BytesIO
from pathlib import Path

MODEL = "@cf/leonardo/lucid-origin"
_URL = "https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{model}"

# One template per trade: (pattern, seed, scene, [(label, surfaces, fixtures)], note).
TEMPLATES = (
    (r"kylpyhuone|laatoit|laatta|vedeneristy|märkätila", 9001,
     "Realistic architectural photograph, eye-level straight-on wide shot of a small Nordic apartment bathroom. "
     "The back wall faces the camera. Left side: shower corner. Right side: toilet position. Round ceiling light. "
     "24mm lens, soft daylight, high detail, no people, no text. Surfaces: {s}. Fixtures: {f}.",
     (("Pohja", "bare grey concrete walls and floor, renovation site, dust",
       "nothing installed, empty room, only capped water pipes and a capped floor drain"),
      ("Vedeneristys", "all walls and floor coated with smooth light blue waterproofing membrane, "
                       "white reinforcement tape in the corners", "nothing installed, empty room, capped pipes"),
      ("Laatoitus", "large light grey tiles installed on the lower half of the walls and the floor, light blue "
                    "waterproofing membrane still visible above, tile adhesive bucket and trowel on the floor",
       "nothing installed yet, empty room"),
      ("Valmis", "large light grey matte tiles on all walls and the floor",
       "black rain shower, frameless glass shower wall, wall-hung white toilet, black fixtures")),
     "Havainnekuva, tekoälyllä luotu: kylpyhuoneremontin vaiheet"),
    (r"maalaus|maalari|tasoitus|tapetointi", 9001,
     "Realistic interior photograph, eye-level straight-on wide shot of a bright Nordic living room wall with a "
     "window on the left and wooden floor. 24mm lens, soft daylight, high detail, no people, no text. "
     "Wall: {s}. Room: {f}.",
     (("Pohjatyöt", "old worn wall with cracks, patched with white filler spots, masking tape on the edges",
       "furniture removed, floor covered with protective paper"),
      ("Pohjamaali", "evenly primed matte white wall", "floor covered with protective paper, paint roller and tray"),
      ("Maalaus", "wall half painted in deep warm green, the rest primed white, wet paint edge",
       "floor covered with protective paper, paint roller on extension pole"),
      ("Valmis", "finished wall painted in deep warm green, crisp edges", "protective paper removed, clean wooden floor, "
                 "a simple sofa and a plant")),
     "Havainnekuva, tekoälyllä luotu: maalaustyön vaiheet"),
    (r"rakennus|rakentaminen|omakotitalo|rivitalo|runko|talopaketti", 4242,
     "Realistic architectural photograph, three-quarter view at eye level of a single-storey Nordic family house "
     "on a flat plot with pine trees behind, overcast soft light, 35mm lens, high detail, no people, no text. "
     "The house: {s}. Site: {f}.",
     (("Perustus", "only the concrete foundation slab is finished", "gravel, formwork boards, construction site"),
      ("Runko", "timber wall frame and roof trusses erected on the slab, no cladding",
       "gravel, stacked timber, construction site"),
      ("Vesikatto", "black metal roof and wind barrier installed, windows fitted, no cladding yet",
       "gravel, scaffolding, construction site"),
      ("Valmis", "finished with dark vertical wooden cladding, black metal roof and warm lit windows",
       "finished yard with lawn, dusk")),
     "Havainnekuva, tekoälyllä luotu: talon rakentumisen vaiheet"),
)


def template_for(text: str):
    text = str(text or "").casefold()
    for pattern, seed, scene, stages, note in TEMPLATES:
        if re.search(pattern, text):
            return seed, scene, stages, note
    return None


def generate_sequence(topic_text: str, folder: Path, *, post=None) -> dict | None:
    """Return {"paths", "labels", "note"} for a 4-stage sequence, or None."""
    from utils import cloudflare_free_ai
    if not cloudflare_free_ai.enabled() or os.getenv("KAURIVO_ILLUSTRATED_SEQUENCE", "1") == "0":
        return None
    chosen = template_for(topic_text)
    if not chosen:
        return None
    seed, scene, stages, note = chosen
    if post is None:
        import requests
        post = requests.post
    from PIL import Image
    account = os.getenv("CLOUDFLARE_ACCOUNT_ID", "").strip()
    token = os.getenv("CLOUDFLARE_API_TOKEN", "").strip()
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    paths, labels = [], []
    for index, (label, surfaces, fixtures) in enumerate(stages):
        try:
            reply = post(_URL.format(account=account, model=MODEL), timeout=(10, 180),
                         headers={"Authorization": "Bearer " + token},
                         json={"prompt": scene.format(s=surfaces, f=fixtures), "seed": seed,
                               "width": 1536, "height": 864, "guidance": 4.5, "num_steps": 30})
            if reply.status_code != 200:
                return None
            body = reply.json()
            data = (body.get("result") or {}).get("image") or body.get("image")
            raw = base64.b64decode(data or "", validate=True)
            with Image.open(BytesIO(raw)) as image:
                image = image.convert("RGB")
                if image.width < 1024 or image.width <= image.height:
                    return None
                target = folder / f"vaihe-{index + 1}.webp"
                image.save(target, "WEBP", quality=88)
        except Exception:
            return None
        paths.append(target)
        labels.append(label)
    return {"paths": paths, "labels": labels, "note": note}

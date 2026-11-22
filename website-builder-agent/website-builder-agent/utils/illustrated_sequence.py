"""Illustrated build sequence for sales demos (free Cloudflare Workers AI).

The reference sites look premium because ONE purpose-made visual drives the
page (a house that builds itself on scroll). A prospect without own photos
gets the same device as an illustration: one scene, one camera, one seed,
four build stages; only the surface/fixture words change between prompts,
which keeps the room consistent. The page labels it "Havainnekuva,
tekoälyllä luotu" and never presents it as the company's work.

Cost: Workers Free gives 10 000 neurons per day, shared with the free LLM
fallback. Lucid Origin costs about 4 000 neurons per 1536x864 image, so a
4-stage sequence would exhaust a day. FLUX.2 [klein] 4B costs about 26 neurons
per output 512 tile: the finished room is generated once (about 160 neurons)
and the earlier stages are EDITS of that same image (input image about 30
neurons), about 720 neurons per sequence and the same room in every frame.

Off unless KAURIVO_ILLUSTRATED_SEQUENCE=1 and the owner-confirmed Workers Free
opt-in is enabled. Any failure returns no sequence; the demo then falls back
to stock illustrations.
"""
from __future__ import annotations

import base64
import os
import re
from io import BytesIO
from pathlib import Path

MODEL = "@cf/black-forest-labs/flux-2-klein-4b"
WIDTH, HEIGHT = 1536, 864  # multiples of 16, ~5 output tiles
_URL = "https://api.cloudflare.com/client/v4/accounts/{account}/ai/run/{model}"
# Last failure, for diagnostics only (HTTP status and the provider's error
# code/message; never prompts, keys or images).
LAST_ERROR = ""

# One template per trade: (pattern, seed, scene, [(label, surfaces, fixtures)], note).
# How each stage appears on scroll (coat = roller strokes, tiles = row by row,
# rise = bottom up, build = floor by floor from the bottom, symmetric about the
# centre, depth = objects front to back); the first stage has none. Building
# trades follow the reference: one 3/4 aerial view, the work grows in order.
MOVES = {"kylpyhuone": ("depth", "depth", "build", "build", "build"),
         "maalaus": ("depth", "coat", "coat", "depth"),
         "talo": ("depth", "build", "build", "build")}
TEMPLATES = (
    (r"kylpyhuone|laatoit|laatta|vedeneristy|märkätila", 9001,
     "Premium 3D architectural visualization, symmetric three-quarter aerial cutaway view from above of one small "
     "Nordic bathroom standing alone on a dark charcoal studio floor: no ceiling, the two front walls cut away at "
     "the same height so the whole room is visible like a dollhouse. Back-left wall: shower corner; back-right wall: "
     "toilet. Soft warm studio light, gentle shadows, clean and tidy, high detail, no people, no text. "
     "Surfaces: {s}. Fixtures: {f}.",
     (("Lähtötilanne", "old worn 1990s bathroom: small beige tiles on the walls and floor, stained grout",
       "old white bathtub with a shower curtain, old pedestal sink, old toilet, old chrome fixtures"),
      ("Pohja", "bare grey concrete walls and floor, renovation site, dust",
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
     "Premium 3D architectural visualization, three-quarter aerial view from about 30 metres of a two-storey "
     "Nordic family house in the centre of a neat plot with pine trees around, golden-hour light, cinematic, "
     "high detail, no people, no text. The house: {s}. Site: {f}.",
     (("Perustus", "only the concrete foundation slab is finished", "levelled sand plot, tidy construction site"),
      ("Runko", "the walls of both floors built in light grey blocks up to the roof line, window openings, no roof",
       "tidy construction site, stacked materials"),
      ("Vesikatto", "dark roof installed on the block walls, windows fitted, no cladding yet",
       "tidy construction site"),
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
    if not cloudflare_free_ai.enabled() or os.getenv("KAURIVO_ILLUSTRATED_SEQUENCE", "0") != "1":
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
    def run(prompt, reference=None):
        """One multipart call; returns RGB image or None."""
        fields = {"prompt": (None, prompt), "width": (None, str(WIDTH)), "height": (None, str(HEIGHT)),
                  "seed": (None, str(seed))}
        if reference is not None:
            buffer = BytesIO()
            reference.save(buffer, "JPEG", quality=92)
            fields["input_image_0"] = ("reference.jpg", buffer.getvalue(), "image/jpeg")
        reply = post(_URL.format(account=account, model=MODEL), timeout=(10, 180),
                     headers={"Authorization": "Bearer " + token}, files=fields)
        if reply.status_code != 200:
            global LAST_ERROR
            try:
                errors = (reply.json() or {}).get("errors") or [{}]
                detail = "%s %s" % (errors[0].get("code", ""), str(errors[0].get("message", ""))[:160])
            except ValueError:
                detail = ""
            LAST_ERROR = "HTTP %s %s" % (reply.status_code, detail)
            return None
        body = reply.json()
        data = (body.get("result") or {}).get("image") or body.get("image")
        with Image.open(BytesIO(base64.b64decode(data or "", validate=True))) as image:
            image = image.convert("RGB")
        if image.width < 1024 or image.width <= image.height:
            return None
        return image

    # 1) the finished room from text; 2) each earlier stage as an edit of it.
    finished_label, finished_s, finished_f = stages[-1]
    images = {}
    try:
        final = run(scene.format(s=finished_s, f=finished_f))
        if final is None:
            return None
        images[len(stages) - 1] = final
        for index, (label, surfaces, fixtures) in enumerate(stages[:-1]):
            edit = ("Edit this exact photo. Keep the same room, walls, ceiling, window, camera position, lens and "
                    f"light. Change only the build stage: surfaces: {surfaces}. Contents: {fixtures}. "
                    "Photorealistic, no people, no text.")
            image = run(edit, final)
            if image is None:
                return None
            images[index] = image
    except Exception as exc:
        global LAST_ERROR
        LAST_ERROR = LAST_ERROR or type(exc).__name__
        return None
    paths, labels = [], []
    for index, (label, _surfaces, _fixtures) in enumerate(stages):
        target = folder / f"vaihe-{index + 1}.webp"
        images[index].save(target, "WEBP", quality=88)
        paths.append(target)
        labels.append(label)
    kind = "kylpyhuone" if "kylpyhuone" in note else "maalaus" if "maalaus" in note else "talo"
    return {"paths": paths, "labels": labels, "note": note, "transitions": list(MOVES[kind])}

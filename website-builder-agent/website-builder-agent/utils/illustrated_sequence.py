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
      ("Pohja", "bare grey concrete walls and floor",
       "REMOVE every fixture: no toilet, no shower, no glass wall, no taps, no sink; completely empty room, "
       "only a capped floor drain"),
      ("Vedeneristys", "all walls and floor coated with smooth light blue waterproofing membrane, "
                       "white reinforcement tape in the corners",
       "REMOVE every fixture: no toilet, no shower, no glass wall, no taps; completely empty room"),
      ("Laatoitus", "the same large light grey tiles as the finished room on the floor and the lower half of the "
                    "walls, light blue waterproofing membrane still visible on the upper half",
       "REMOVE every fixture: no toilet, no shower, no glass wall, no taps; empty room, no tools"),
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


GEMINI_IMAGE_MODELS = ("gemini-2.5-flash-image", "gemini-2.0-flash-preview-image-generation")
_GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"


def _gemini_image(prompt: str, reference=None, *, post):
    """Gemini API free tier (no-billing key) image generation/editing; RGB image or None."""
    global LAST_ERROR
    from PIL import Image
    key = os.getenv("KAURIVO_GEMINI_API_KEY", "").strip()
    parts = [{"text": prompt + " Wide 16:9 landscape image."}]
    if reference is not None:
        buffer = BytesIO()
        reference.save(buffer, "JPEG", quality=92)
        parts.append({"inline_data": {"mime_type": "image/jpeg",
                                      "data": base64.b64encode(buffer.getvalue()).decode("ascii")}})
    for model in GEMINI_IMAGE_MODELS:
        body = {"contents": [{"parts": parts}],
                "generationConfig": {"responseModalities": ["TEXT", "IMAGE"]}}
        if model.startswith("gemini-2.5"):
            body["generationConfig"]["imageConfig"] = {"aspectRatio": "16:9"}
        reply = post(_GEMINI_URL.format(model=model), timeout=(10, 180), json=body,
                     headers={"x-goog-api-key": key, "Content-Type": "application/json"})
        if reply.status_code != 200:
            try:
                LAST_ERROR = "gemini %s HTTP %s %s" % (model, reply.status_code,
                                                      str((reply.json().get("error") or {}).get("message", ""))[:160])
            except ValueError:
                LAST_ERROR = "gemini %s HTTP %s" % (model, reply.status_code)
            continue
        for candidate in reply.json().get("candidates") or []:
            for part in (candidate.get("content") or {}).get("parts") or []:
                data = (part.get("inline_data") or part.get("inlineData") or {}).get("data")
                if data:
                    with Image.open(BytesIO(base64.b64decode(data))) as image:
                        image = image.convert("RGB")
                    if image.width < image.height:
                        return None
                    # Same frame size as the Cloudflare path (cover crop to 16:9).
                    from PIL import ImageOps
                    return ImageOps.fit(image, (WIDTH, HEIGHT), Image.LANCZOS)
        LAST_ERROR = "gemini %s returned no image" % model
    return None


def generate_sequence(topic_text: str, folder: Path, *, post=None) -> dict | None:
    """Return {"paths", "labels", "note", "transitions"} for a staged sequence, or None.

    Cloudflare Workers Free (FLUX klein) first; when its daily neurons are spent,
    the Gemini API free tier (no-billing key) makes the whole sequence instead.
    """
    from utils import cloudflare_free_ai, gemini_free_ai
    if os.getenv("KAURIVO_ILLUSTRATED_SEQUENCE", "0") != "1":
        return None
    use_cf, use_gemini = cloudflare_free_ai.enabled(), gemini_free_ai.enabled()
    if not (use_cf or use_gemini):
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
    # One provider for the whole sequence keeps every frame the same room.
    finished_label, finished_s, finished_f = stages[-1]
    images = {}
    try:
        final = run(scene.format(s=finished_s, f=finished_f)) if use_cf else None
        if final is None and use_gemini:
            run = lambda prompt, reference=None: _gemini_image(prompt, reference, post=post)
            final = run(scene.format(s=finished_s, f=finished_f))
        if final is None:
            return None
        images[len(stages) - 1] = final
        for index, (label, surfaces, fixtures) in enumerate(stages[:-1]):
            edit = ("Edit this exact image. Keep exactly the same camera position, framing, scale, lens, light "
                    "and the same background colour and floor around the room; keep the room's shape and wall "
                    f"heights. Change only the build stage: surfaces: {surfaces}. Contents: {fixtures}. "
                    "Same rendering style, no people, no text.")
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

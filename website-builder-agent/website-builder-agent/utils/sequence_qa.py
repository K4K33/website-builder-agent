"""Quality gate for build sequences and films: reject what does not look right.

Two checks, both free:

1. alignment (no AI): every stage must be the SAME room from the SAME camera.
   Edges of each stage are compared with the finished frame; a moved camera,
   a different room or a re-composed image scores low.
2. visual review (free vision model): a strict art director looks at all the
   stages at once and scores realism, sense and premium feel. Anything that
   looks wrong (view from outside, objects that should not be there yet,
   melted geometry, different rooms) fails.

Only a sequence that passes both may become a hero or a film.
"""
from __future__ import annotations

from pathlib import Path

MIN_ALIGNMENT = 0.88
MIN_SCORE = 8

REVIEW_BRIEF = """You are a strict art director reviewing AI images for a premium website hero that shows
a renovation step by step. The images are the stages in order: {labels}.
Judge like a demanding client. Fail it if ANY of these is true:
- an interior job is not seen from inside the room at eye level (e.g. a dollhouse or aerial cutaway);
  a house build is seen from a drone view and may end at eye level by the front door
- the stages are not clearly the same room or building (from the same camera, except a final view
  that is described as a deliberate camera move)
- a stage shows things that do not belong to that stage (fixtures before they are installed,
  tools, debris, people, text, logos)
- any object appears twice where one is expected (two toilets, two sinks, doubled taps)
- a stage does not clearly show its own work (e.g. "tiles" must show visible tiles with grout
  lines, "waterproofing" an even membrane, "finished" a fully finished premium room)
- geometry is warped, melted, doubled or physically impossible
- it looks cheap, cartoonish, noisy or inconsistent in colour and light
Answer JSON only: {{"score": 0-10, "ok": true/false, "issues": ["short issue", ...]}}.
ok is true only when score >= 8 and nothing above applies."""


def _edges(image, size=(192, 108)):
    """Structural lines only (blurred, top 7 % gradients): walls, corners, fixtures."""
    import numpy as np
    from PIL import ImageFilter
    gray = image.convert("L").resize(size).filter(ImageFilter.GaussianBlur(1.5)).filter(ImageFilter.FIND_EDGES)
    a = np.asarray(gray, dtype=np.float32)
    return a > float(np.percentile(a, 93))


def alignment(images: list, ref: int | None = None) -> list[float]:
    """How much of the reference stage's room structure (walls, corners, ceiling
    edges) survives in every other stage. The reference is the empty shell, so
    fixtures added later never count against a stage. Calibrated: same room and
    camera 0.90-0.99; a moved camera or another room 0.62-0.84."""
    import numpy as np
    from PIL import Image, ImageFilter
    ref = len(images) - 1 if ref is None else ref
    base = _edges(images[ref])
    scores = []
    for index, image in enumerate(images):
        if index == ref:
            continue
        grown = Image.fromarray(_edges(image).astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(3))
        scores.append(round(float((base & (np.asarray(grown) > 0)).sum() / max(1, base.sum())), 3))
    return scores


def review(paths: list[Path], labels: list[str], *, ask=None, trade: str = "") -> dict:
    """Ask the free vision QA model; {'ok', 'score', 'issues'} (never raises)."""
    try:
        if ask is None:
            from utils.claude_client import ask_claude_json as ask
        from utils.trade_specs import review_checklist
        brief = REVIEW_BRIEF.format(labels=" -> ".join(labels))
        extra = review_checklist(trade, labels)
        if extra:
            brief += "\n" + extra + "\nFail it if anything in this checklist is missing."
        reply = ask(brief,
                    "Review these stage images in order.", max_tokens=600,
                    image_paths=[str(p) for p in paths], stage="qa")
        score = int(reply.get("score", 0))
        issues = [str(i)[:140] for i in reply.get("issues") or []][:8]
        return {"ok": bool(reply.get("ok")) and score >= MIN_SCORE, "score": score, "issues": issues}
    except Exception as exc:
        return {"ok": False, "score": 0, "issues": ["review unavailable: " + type(exc).__name__]}


def check(paths: list[Path], labels: list[str], *, ask=None, ref: int | None = None, trade: str = "") -> dict:
    from PIL import Image
    images = [Image.open(p).convert("RGB") for p in paths]
    from utils.trade_specs import SPECS
    same = (SPECS.get(trade) or {}).get("same_camera_until")
    # A designed camera move (drone -> front door) is not a misalignment.
    aligned = alignment(images[:same] if same else images, ref)
    result = {"alignment": aligned, "aligned": min(aligned or [1]) >= MIN_ALIGNMENT}
    result.update(review(paths, labels, ask=ask, trade=trade) if result["aligned"] else
                  {"ok": False, "score": 0, "issues": ["stages are not the same room/camera"]})
    result["ok"] = result["aligned"] and result["ok"]
    return result

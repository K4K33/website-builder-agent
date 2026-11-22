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

MIN_ALIGNMENT = 0.78
MIN_SCORE = 8

REVIEW_BRIEF = """You are a strict art director reviewing AI images for a premium website hero that shows
a renovation step by step. The images are the stages in order: {labels}.
Judge like a demanding client. Fail it if ANY of these is true:
- the view is not from inside the room at eye level (e.g. a dollhouse or aerial cutaway from outside)
- the stages are not clearly the same room from the same camera position
- a stage shows things that do not belong to that stage (fixtures before they are installed,
  tools, debris, people, text, logos)
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


def alignment(images: list) -> list[float]:
    """Structural agreement of each stage with the finished frame (calibrated:
    same room and camera 0.84-0.94, a different room or camera 0.57-0.71)."""
    import numpy as np
    from PIL import Image, ImageFilter

    def binary_dilation(mask, iterations=1):
        grown = Image.fromarray(mask.astype(np.uint8) * 255).filter(ImageFilter.MaxFilter(2 * iterations + 1))
        return np.asarray(grown) > 0
    final = _edges(images[-1])
    grown = binary_dilation(final, iterations=1)
    scores = []
    for image in images[:-1]:
        edges = _edges(image)
        forward = (edges & grown).sum() / max(1, edges.sum())
        back = (final & binary_dilation(edges, iterations=1)).sum() / max(1, final.sum())
        scores.append(round(float(min(forward, back)), 3))
    return scores


def review(paths: list[Path], labels: list[str], *, ask=None) -> dict:
    """Ask the free vision QA model; {'ok', 'score', 'issues'} (never raises)."""
    try:
        if ask is None:
            from utils.claude_client import ask_claude_json as ask
        reply = ask(REVIEW_BRIEF.format(labels=" -> ".join(labels)),
                    "Review these stage images in order.", max_tokens=600,
                    image_paths=[str(p) for p in paths], stage="qa")
        score = int(reply.get("score", 0))
        issues = [str(i)[:140] for i in reply.get("issues") or []][:8]
        return {"ok": bool(reply.get("ok")) and score >= MIN_SCORE, "score": score, "issues": issues}
    except Exception as exc:
        return {"ok": False, "score": 0, "issues": ["review unavailable: " + type(exc).__name__]}


def check(paths: list[Path], labels: list[str], *, ask=None) -> dict:
    from PIL import Image
    images = [Image.open(p).convert("RGB") for p in paths]
    aligned = alignment(images)
    result = {"alignment": aligned, "aligned": min(aligned or [1]) >= MIN_ALIGNMENT}
    result.update(review(paths, labels, ask=ask) if result["aligned"] else
                  {"ok": False, "score": 0, "issues": ["stages are not the same room/camera"]})
    result["ok"] = result["aligned"] and result["ok"]
    return result

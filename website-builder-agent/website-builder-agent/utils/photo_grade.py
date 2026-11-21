"""One cinematic grade for every photo on a sales demo.

Stock illustrations and a company's own photos come from different cameras and
light. Unedited they read as a real-estate listing: clipped white walls, mixed
colour casts, sharp digital noise. A shared grade makes them one series:

- highlights roll off below pure white and blacks lift slightly (film shoulder
  and toe), with a gentle S-curve in between
- saturation is reduced a little, more in the highlights
- shadows are toned toward the page's ink and highlights toward its canvas, so
  photos and typography share one colour world
- a fine luminance grain hides upscaling softness

The grade keeps the content truthful: no retouching, no added or removed objects.
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image


def _rgb(hex_colour: str) -> np.ndarray:
    value = str(hex_colour or "#000000").lstrip("#")
    if len(value) == 3:
        value = "".join(c * 2 for c in value)
    if len(value) != 6:
        value = "000000"
    return np.array([int(value[i:i + 2], 16) for i in (0, 2, 4)], dtype=np.float32) / 255.0


def grade_array(rgb: np.ndarray, *, shadow: str, highlight: str, strength: float = 1.0,
                seed: int = 7) -> np.ndarray:
    """rgb float32 0-1 (H, W, 3) -> graded float32 0-1."""
    x = np.clip(rgb.astype(np.float32), 0, 1)
    k = float(max(0.0, min(1.0, strength)))
    # Filmic tone curve: S-curve, then toe lift and shoulder roll-off.
    s = 0.5 + 0.5 * np.tanh(2.2 * (x - 0.5)) / np.tanh(1.1)
    curve = 0.035 + (0.93 - 0.035) * (0.55 * s + 0.45 * x)
    x = x + (curve - x) * k
    lum = (0.2126 * x[..., 0] + 0.7152 * x[..., 1] + 0.0722 * x[..., 2])[..., None]
    # Saturation: -12 %, up to -30 % in the brightest areas.
    sat = 1 - k * (0.12 + 0.18 * np.clip((lum - 0.6) / 0.4, 0, 1))
    x = lum + (x - lum) * sat
    # Split toning toward the page colours.
    shadow_tone, highlight_tone = _rgb(shadow), _rgb(highlight)
    w_shadow = (np.clip(1 - lum / 0.45, 0, 1) ** 1.5) * 0.22 * k
    w_high = (np.clip((lum - 0.55) / 0.45, 0, 1) ** 1.5) * 0.12 * k
    shadow_target = shadow_tone * 0.5 + lum * 0.5
    highlight_target = highlight_tone * (0.35 + 0.65 * lum)
    x = x * (1 - w_shadow - w_high) + shadow_target * w_shadow + highlight_target * w_high
    # Fine grain, stronger in the mid-tones.
    if k > 0:
        rng = np.random.default_rng(seed)
        grain = rng.normal(0, 1, x.shape[:2]).astype(np.float32)[..., None]
        x = x + grain * 0.012 * k * (1 - np.abs(lum - 0.5) * 1.2)
    return np.clip(x, 0, 1)


def grade_photo(source: Path, target: Path, *, shadow: str, highlight: str,
                strength: float = 1.0, max_side: int = 2400) -> Path:
    """Write a graded WebP copy of ``source`` to ``target`` (suffix forced .webp)."""
    target = Path(target).with_suffix(".webp")
    with Image.open(source) as image:
        image = image.convert("RGB")
        image.thumbnail((max_side, max_side))
        rgb = np.asarray(image, dtype=np.float32) / 255.0
    out = grade_array(rgb, shadow=shadow, highlight=highlight, strength=strength,
                      seed=sum(Path(source).name.encode()) % 997)
    Image.fromarray((out * 255 + 0.5).astype(np.uint8)).save(target, "WEBP", quality=84, method=5)
    return target

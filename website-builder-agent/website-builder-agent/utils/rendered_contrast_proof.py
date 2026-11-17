"""Conservative WCAG proof from *real* Chromium background pixels.

Used only after an opaque CSS proof was impossible. This does not infer
contrast from a blurred/photo mock, sampled corner, or model judgement.
Every captured background pixel is bounded using each RGB channel's extrema,
and every unknown/animated/failed capture is rejected.
"""
from io import BytesIO


def _luminance(rgb):
    def linear(channel):
        value = channel / 255.0
        return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4
    return sum(weight * linear(value) for weight, value in zip(
        (0.2126, 0.7152, 0.0722), rgb))


def rendered_background_contrast(png_bytes, foreground, required, *, max_pixels=2500000):
    """Return a certified contrast lower bound, or None if it cannot be proved.

    A single minimum/maximum pixel sample is not sufficient. The minimum
    luminance is bounded by the *per-channel* minima, and the maximum by
    the per-channel maxima over the full element screenshot. The bounds
    can be pessimistic for photos, but cannot hide a low-contrast pixel.
    """
    if (not isinstance(png_bytes, bytes) or
            not png_bytes.startswith(b"\x89PNG\r\n\x1a\n") or
            not isinstance(foreground, (tuple, list)) or len(foreground) != 3 or
            any(not isinstance(c, (int, float)) or c < 0 or c > 255 for c in foreground) or
            not isinstance(required, (int, float)) or required < 3 or required > 7):
        return None
    try:
        from PIL import Image, UnidentifiedImageError
    except ImportError:
        # Minimal audit environments may omit Pillow. Never turn a missing
        # verifier into a positive QA verdict.
        return None
    try:
        with Image.open(BytesIO(png_bytes)) as image:
            if image.format != "PNG" or image.width < 2 or image.height < 2:
                return None
            if image.width * image.height > max_pixels:
                return None
            if image.mode not in ("RGB", "RGBA"):
                return None
            if image.mode == "RGBA" and image.getchannel("A").getextrema() != (255, 255):
                return None
            extrema = image.convert("RGB").getextrema()
    except (UnidentifiedImageError, OSError, ValueError):
        return None

    minimum = _luminance([pair[0] for pair in extrema])
    maximum = _luminance([pair[1] for pair in extrema])
    text = _luminance(foreground)
    if text >= maximum:
        ratio = (text + 0.05) / (maximum + 0.05)
    elif text <= minimum:
        ratio = (minimum + 0.05) / (text + 0.05)
    else:
        return None
    return ratio if ratio >= required + 0.03 else None

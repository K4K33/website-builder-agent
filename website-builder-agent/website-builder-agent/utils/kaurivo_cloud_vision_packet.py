"""AI-only compressed visual evidence, never a replacement for source images.

Kaurivo keeps original screenshots unmodified for factual source capture,
desktop/mobile comparisons and public/browser QA. The Cloudflare free endpoint
gets a size-bounded JPEG overview of each real screenshot so a few full-page
PNG captures cannot overflow a single multipart-like JSON request.
"""
from __future__ import annotations

import base64
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

MAX_IMAGES = 8
MAX_BYTES_PER_IMAGE = 390000
MAX_SOURCE_PIXELS = 52000000
MAX_TOTAL_INLINE_BYTES = 4_000_000


def compact_screenshot_data_url(path: str) -> str:
    if not path or not Path(path).is_file():
        raise RuntimeError("FREE_AI_MEDIA_MISSING: observed screenshot file unavailable")
    try:
        with Image.open(path) as original:
            if original.width < 25 or original.height < 25:
                raise ValueError("invalid screenshot dimensions")
            if original.width * original.height > MAX_SOURCE_PIXELS:
                raise RuntimeError("FREE_AI_MEDIA_TOO_LARGE: screenshot pixels exceed safe decode limit")
            image = ImageOps.exif_transpose(original)
            image.load()
            image = image.convert("RGB")
        # Whole-page overview, not a crop pretending the rest of the
        # customer or competitor website does not exist.
        image.thumbnail((1300, 3200), Image.Resampling.LANCZOS)
        for quality in (78, 65, 52):
            buffer = BytesIO()
            image.save(buffer, format="JPEG", quality=quality,
                       optimize=True, progressive=True)
            data = buffer.getvalue()
            if len(data) <= MAX_BYTES_PER_IMAGE:
                return "data:image/jpeg;base64," + base64.b64encode(data).decode("ascii")
        raise RuntimeError("FREE_AI_MEDIA_TOO_LARGE: cannot compact screenshot safely")
    except (OSError, ValueError, UnidentifiedImageError) as error:
        raise RuntimeError("FREE_AI_MEDIA_INVALID: screenshot cannot be safely decoded") from error


def compact_vision_user_content(prompt: str, image_paths: list[str]) -> list[dict]:
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("AI image prompt must be nonempty")
    if not isinstance(image_paths, list) or not 1 <= len(image_paths) <= MAX_IMAGES:
        raise RuntimeError("FREE_AI_MEDIA_TOO_LARGE: unsupported visual image count")
    message = [{"type": "text", "text": prompt}]
    total_inline = 0
    for path in image_paths:
        uri = compact_screenshot_data_url(path)
        total_inline += len(uri)
        if total_inline > MAX_TOTAL_INLINE_BYTES:
            raise RuntimeError("FREE_AI_MEDIA_TOO_LARGE: free AI visual payload exceeds safe limit")
        message.append({"type": "image_url", "image_url": {"url": uri}})
    return message

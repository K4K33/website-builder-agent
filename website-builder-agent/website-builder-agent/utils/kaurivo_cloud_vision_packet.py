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



def compact_concept_review_user_content(
    prompt: str, image_paths: list[str],
) -> list[dict]:
    """Pack 12/14 real concept+source screenshots as seven paired overviews.

    The private reviewer still receives ALL twelve concept views and both
    original-company references where present. The originals remain unchanged,
    and actual full-resolution screenshots still govern source/browser QA.
    Pair labels map directly to the ordered view IDs in the review JSON; never
    silently omit a viewport to fit a provider image-count limit.
    """
    from PIL import ImageDraw, ImageFont
    if not isinstance(prompt, str) or not prompt.strip():
        raise ValueError("AI review prompt must be nonempty")
    if not isinstance(image_paths, list) or len(image_paths) not in (12, 14):
        raise RuntimeError("FREE_AI_MEDIA_TOO_LARGE: concept visual review needs all 12 or 14 views")
    sheets = len(image_paths) // 2
    header = (
        "\n\nINDEPENDENT VISUAL EVIDENCE: Each attached JPEG contains TWO "
        "separately labeled full-page screenshot overviews, side-by-side. "
        "LEFT panel VIEW 01 and RIGHT panel VIEW 02 are the first two "
        "views_in_image_order entries; subsequent sheets contain VIEW 03/04, "
        "05/06, etc. VIEW 01 through VIEW 12 map to all 12 required "
        "concept viewport IDs. When present, VIEW 13 and VIEW 14 are the "
        "unaltered source-company desktop/mobile screenshots in "
        "original_source_images_after_concept_images. Inspect every individual "
        "panel and report all required view IDs, not merely the combined images. "
        "Overview packing is not a pass or replacement for full-resolution QA."
    )
    message = [{"type": "text", "text": prompt + header}]
    total_inline = 0
    for idx in range(0, len(image_paths), 2):
        images = []
        for name in image_paths[idx:idx + 2]:
            if not name or not Path(name).is_file():
                raise RuntimeError("FREE_AI_MEDIA_MISSING: source screenshot unavailable")
            try:
                with Image.open(name) as original:
                    if original.width < 25 or original.height < 25:
                        raise ValueError("invalid screenshot dimensions")
                    if original.width * original.height > MAX_SOURCE_PIXELS:
                        raise RuntimeError(
                            "FREE_AI_MEDIA_TOO_LARGE: screenshot exceeds safe decode limit")
                    copy = ImageOps.exif_transpose(original)
                    copy.load()
                    copy = copy.convert("RGB")
                copy.thumbnail((940, 2070), Image.Resampling.LANCZOS)
                images.append(copy)
            except (OSError, ValueError, UnidentifiedImageError) as exc:
                raise RuntimeError(
                    "FREE_AI_MEDIA_INVALID: screenshot cannot be safely decoded") from exc
        sheet = Image.new("RGB", (1940, 2160), (235, 238, 240))
        draw = ImageDraw.Draw(sheet)
        try:
            font = ImageFont.load_default(size=27)
        except TypeError:
            font = ImageFont.load_default()
        for offset, photo in enumerate(images):
            left = 20 + offset * 960
            number = idx + offset + 1
            draw.text((left + 10, 16), f"VIEW {number:02d}",
                      fill=(12, 19, 30), font=font)
            sheet.paste(photo, (left, 68))
        jpeg = None
        for quality in (78, 67, 57, 46, 37):
            buffer = BytesIO()
            sheet.save(buffer, format="JPEG", quality=quality,
                       optimize=True, progressive=True)
            if buffer.tell() <= MAX_BYTES_PER_IMAGE:
                jpeg = buffer.getvalue()
                break
        if jpeg is None:
            raise RuntimeError("FREE_AI_MEDIA_TOO_LARGE: paired overview cannot fit free budget")
        uri = "data:image/jpeg;base64," + base64.b64encode(jpeg).decode("ascii")
        total_inline += len(uri)
        if total_inline > MAX_TOTAL_INLINE_BYTES:
            raise RuntimeError("FREE_AI_MEDIA_TOO_LARGE: paired vision payload exceeds safe limit")
        message.append({"type": "image_url", "image_url": {"url": uri}})
    if len(message) != sheets + 1 or sheets > MAX_IMAGES:
        raise RuntimeError("FREE_AI_MEDIA_TOO_LARGE: required visual panel count mismatch")
    return message


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

"""Credit-free visual-media preflight shared by ALL Kaurivo customers.

Source checks alone do not prove images load in a public browser. An external
image is explicitly UNVERIFIED until a real published-URL check confirms it;
a linked source website is not a stable media host or a licensing grant.

This module deliberately has no company names, network calls, API credits,
hard-coded visual layout or subjective self-generated quality rating.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path
import struct
import re
from urllib.parse import unquote, urlsplit

from bs4 import BeautifulSoup


def _bitmap_width(path: Path) -> int | None:
    """Inspect PNG/GIF header width without extra dependencies or OCR."""
    try:
        with path.open("rb") as file:
            header = file.read(26)
        if header.startswith(b"\x89PNG\r\n\x1a\n") and len(header) >= 24:
            return struct.unpack(">I", header[16:20])[0]
        if header[:6] in (b"GIF87a", b"GIF89a") and len(header) >= 10:
            return struct.unpack("<H", header[6:8])[0]
    except (OSError, ValueError, struct.error):
        pass
    return None


def _primary_brand_image(image) -> bool:
    if image.find_parent("header") is None:
        return False
    chain = [image, *list(image.parents)[:4]]
    hint = " ".join(
        str(node.get("class", "")) + " " + str(node.get("id", ""))
        for node in chain if getattr(node, "attrs", None) is not None
    ).lower()
    alt = str(image.get("alt") or "").lower()
    return any(term in hint for term in ("brand", "logo", "identity")) or "logo" in alt


def _image_source(image) -> str:
    """Use src; a srcset-only picture still needs a fallback."""
    return str(image.get("src") or "").strip()


def audit_visual_media(
    html: str,
    *,
    html_path: str | Path | None = None,
    verified_public_images: set[str] | frozenset[str] | None = None,
    min_header_bitmap_width: int = 256,
) -> dict:
    """Find objectively invalid or unverified images before an owner preview.

    A verified_public_images entry means the exact image URL was checked in
    a real browser/public HTTP probe for THIS build. This remains separate
    from licensing, source authenticity, accessibility and artistic approval.
    No caller may treat these results as a 9.5 or 10/10 visual score.
    """
    if not isinstance(html, str):
        raise TypeError("html must be a string")
    verified = set(verified_public_images or ())
    soup = BeautifulSoup(html, "html.parser")
    root = Path(html_path).resolve().parent if html_path is not None else None
    blockers, pending, warnings, inventory = [], [], [], []
    sources = []

    for index, img in enumerate(soup.find_all("img"), 1):
        source = _image_source(img)
        is_brand = _primary_brand_image(img)
        # For brand and hero imagery, even one absent picture destroys trust.
        parent_hero = img.find_parent(
            lambda tag: bool(tag.get("class") or tag.get("id"))
            and any(
                key in ("hero", "hero-image", "hero-media", "welcome-image", "masthead")
                or key.startswith("hero-")
                for key in (list(tag.get("class") or []) + [str(tag.get("id") or "")])
            )
        )
        placement = "brand" if is_brand else "hero" if parent_hero else "content"
        label = str(img.get("alt") or "").strip() or f"image #{index}"
        entry = {"placement": placement, "source": source, "label": label}
        inventory.append(entry)

        if not source:
            blockers.append(f"{placement}: missing src for {label[:70]}")
            continue
        if source.startswith(("data:", "blob:")):
            if is_brand or parent_hero:
                pending.append(f"{placement}: embedded/generated media requires quality and source verification: {label[:70]}")
            continue

        url = urlsplit(source)
        if url.scheme in ("http", "https") or source.startswith("//"):
            sources.append(source)
            if source not in verified:
                pending.append(
                    f"{placement}: remote image unverified at public preview: {source[:190]}"
                )
            continue
        if url.scheme or source.startswith(("/", "\\")):
            blockers.append(f"{placement}: unsupported or unstable image address: {source[:150]}")
            continue
        sources.append(source)
        if root is None:
            pending.append(f"{placement}: local file cannot be checked without html_path: {source[:150]}")
            continue

        local = (root / unquote(url.path)).resolve()
        if not local.is_file():
            blockers.append(f"{placement}: missing local image: {source[:150]}")
            continue
        if local.stat().st_size == 0:
            blockers.append(f"{placement}: empty local image: {source[:150]}")
            continue
        if is_brand and local.suffix.lower() in (".png", ".gif"):
            width = _bitmap_width(local)
            if width is not None and width < min_header_bitmap_width:
                blockers.append(
                    f"brand: raster logo is only {width}px wide; obtain original high-resolution/vector logo: {source[:120]}"
                )
            elif width is None:
                pending.append(
                    f"brand: actual bitmap resolution could not be determined: {source[:120]}"
                )

    # Image-like resources can be in picture/srcset and inline CSS, not only
    # in <img>. Check their exact local paths too so a decorative background
    # cannot silently become another empty hero rectangle.
    supplemental = []
    for node in soup.select("img[srcset],source[srcset]"):
        for candidate in str(node.get("srcset") or "").split(","):
            part = candidate.strip().split()
            if part:
                supplemental.append(("srcset", part[0]))
    for node in soup.find_all("style"):
        supplemental.extend(
            ("CSS image", m.strip().strip("\\\"'"))
            for m in re.findall(r"url\(\s*([^)]*)\)", node.get_text(), flags=re.I)
        )
    for node in soup.find_all(style=True):
        supplemental.extend(
            ("CSS image", m.strip().strip("\\\"'"))
            for m in re.findall(r"url\(\s*([^)]*)\)", str(node.get("style") or ""), flags=re.I)
        )
    for placement, value in supplemental:
        if not value or value.startswith(("data:", "#")):
            continue
        parsed = urlsplit(value)
        if parsed.scheme in ("https", "http") or value.startswith("//"):
            if value not in verified:
                pending.append(f"{placement}: remote asset unverified in published preview: {value[:190]}")
        elif parsed.scheme or value.startswith(("/", "\\\\")):
            blockers.append(f"{placement}: unsupported asset path: {value[:150]}")
        elif root is None:
            pending.append(f"{placement}: local asset not checked without html_path: {value[:150]}")
        else:
            local = (root / unquote(parsed.path)).resolve()
            if not local.is_file() or local.stat().st_size == 0:
                blockers.append(f"{placement}: missing or empty local asset: {value[:150]}")

    # A repeated hero photo used as another section's main image is a creative
    # warning, not a fabricated failure: multiple placements can be deliberate.
    common = Counter(source for source in sources if source)
    for src, n in common.items():
        if n > 2:
            warnings.append(
                f"Image repeated {n} times; confirm it does not make the site feel generic: {src[:130]}"
            )

    # Text-first layouts are valid; no universal 'must have hero image' rule.
    # For image-led layouts every unverified image is held for review, never
    # silently substituted with a blank rectangle.
    return {
        "static_pass": not blockers,
        "owner_preview_ready": not blockers and not pending,
        "blockers": blockers,
        "needs_public_verification": pending,
        "creative_warnings": warnings,
        "image_inventory": inventory,
        "note": (
            "Passing this static preflight does NOT verify visual excellence or media rights. "
            "Remote media needs exact published-URL checks; raster logo sharpness "
            "must also be measured at rendered desktop/mobile size."
        ),
    }

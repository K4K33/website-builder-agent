"""Safe credit-free packaging of client-supplied images for any Kaurivo build.

Only explicitly provided local source files can be staged. This does not
download images from an arbitrary third-party website, invent licenses, or
replace a brand logo. Image rights stay separate from technical integrity.
"""
from __future__ import annotations

from hashlib import sha256
from pathlib import Path
import re
import shutil
from xml.etree import ElementTree as ET

MEDIA_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".webp", ".gif", ".avif", ".svg"})
RIGHTS_STATUSES = frozenset({"client_approved", "licensed", "internal_demo_only"})
MAX_ASSET_SIZE_BYTES = 12 * 1024 * 1024
MAX_ASSET_COUNT = 24


def _safe_svg(source: Path) -> bool:
    """Reject SVG scripting, external references and embedded HTML."""
    try:
        document = ET.parse(source)
        for node in document.iter():
            name = node.tag.split("}")[-1].lower()
            if name in {"script", "foreignobject", "iframe", "image", "animate",
                        "animatemotion", "animatetransform", "set"}:
                return False
            for key, value in node.attrib.items():
                attr = key.split("}")[-1].lower()
                if attr.startswith("on"):
                    return False
                if attr in {"href", "src"} and not str(value).startswith("#"):
                    return False
        return True
    except (ET.ParseError, OSError, ValueError):
        return False


def stage_local_media(
    items: list[dict] | None,
    *,
    intake_root: str | Path,
    output_dir: str | Path,
) -> list[dict]:
    """Copy approved intake files to an output/assets folder; no network calls.

    Each item: {"file": "client/logo.svg", "purpose": "header logo",
    "alt": "Client logo", "rights_status": "client_approved",
    "source_note": "Customer email/permission evidence"}.
    Source paths are relative to intake_root and cannot escape via symlinks
    or traversal. Internal-demo-only images are never silently marked licensed.
    """
    if not items:
        return []
    if not isinstance(items, list) or len(items) > MAX_ASSET_COUNT:
        raise ValueError("Media intake requires a bounded list of approved files.")
    root = Path(intake_root).resolve()
    destination = Path(output_dir).resolve() / "assets"
    proposed = []
    for index, item in enumerate(items, 1):
        if not isinstance(item, dict):
            raise ValueError(f"Media asset #{index} is not a record.")
        rel = str(item.get("file") or "").strip()
        rights = str(item.get("rights_status") or "").strip()
        purpose = str(item.get("purpose") or "").strip()
        alt = str(item.get("alt") or "").strip()
        source_note = str(item.get("source_note") or "").strip()
        if (not rel or not purpose or not alt or not source_note
                or rights not in RIGHTS_STATUSES):
            raise ValueError(f"Media asset #{index} is missing usage/source evidence.")
        relative = Path(rel)
        if relative.is_absolute() or str(relative).startswith(("/", "\\")):
            raise ValueError("Media intake source must be relative to the approved media directory.")
        source = (root / relative).resolve()
        if not source.is_relative_to(root) or not source.is_file():
            raise ValueError(f"Media source absent or escapes approved intake root: {rel}")
        extension = source.suffix.lower()
        if extension not in MEDIA_EXTENSIONS:
            raise ValueError(f"Unsupported media extension: {rel}")
        size = source.stat().st_size
        if not 0 < size <= MAX_ASSET_SIZE_BYTES:
            raise ValueError(f"Missing, empty or oversized media asset: {rel}")
        if extension == ".svg" and not _safe_svg(source):
            raise ValueError(f"SVG contains unsafe or external elements: {rel}")
        content_digest = sha256(source.read_bytes()).hexdigest()
        filename_part = re.sub(r"[^a-z0-9]+", "-", source.stem.lower()).strip("-")[:40] or "media"
        target_name = f"{filename_part}-{content_digest[:12]}{extension}"
        proposed.append({
            "source": source,
            "target": destination / target_name,
            "media": {
                "src": f"assets/{target_name}",
                "purpose": purpose,
                "alt": alt,
                "rights_status": rights,
                "source_note": source_note,
                "sha256": content_digest,
                "production_rights_verified": rights in ("client_approved", "licensed"),
            },
        })
    # Validate all input before copying ANY file to avoid partial media builds.
    destination.mkdir(parents=True, exist_ok=True)
    for asset in proposed:
        target = asset["target"]
        if not target.is_file() or sha256(target.read_bytes()).hexdigest() != asset["media"]["sha256"]:
            shutil.copyfile(asset["source"], target)
    return [asset["media"] for asset in proposed]

"""Gate hand-authored AND automated new Kaurivo demos against V6 art-direction proof.

Source-grounded three concept plans alone are not rendered comparisons.
For a new/changed demo, require three *real binary PNG screenshots* for
desktop and mobile, current master contract SHA, chosen/rejected concept
identities, and a traceable review. A JSON path, placeholder, screenshot URL,
or an old source-capture is not evidence.
"""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import struct
import zlib

from utils.creative_directions import validate_creative_directions
from utils.service_quality import MASTER_PROMPT_SHA256

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _png_evidence(path: Path, *, viewport: str) -> str:
    raw = path.read_bytes()
    if not 256 <= len(raw) <= 15_000_000 or not raw.startswith(PNG_SIGNATURE):
        raise ValueError("Missing or invalid real PNG screenshot: " + path.name)
    cursor, image_data, size, ending = 8, bytearray(), None, False
    while cursor+12 <= len(raw):
        length = struct.unpack(">I", raw[cursor:cursor+4])[0]
        tag = raw[cursor+4:cursor+8]
        end = cursor+12+length
        if end > len(raw) or length > 15_000_000:
            raise ValueError("Corrupt PNG chunk: " + path.name)
        payload = raw[cursor+8:cursor+8+length]
        crc = struct.unpack(">I", raw[cursor+8+length:end])[0]
        if zlib.crc32(tag+payload) & 0xffffffff != crc:
            raise ValueError("PNG CRC mismatch: " + path.name)
        if tag == b"IHDR":
            if size is not None or len(payload) != 13:
                raise ValueError("Invalid PNG header")
            size = struct.unpack(">II", payload[:8])
        if tag == b"IDAT":
            image_data.extend(payload)
        cursor = end
        if tag == b"IEND":
            ending = True
            break
    if not ending or not size or not image_data or cursor != len(raw):
        raise ValueError("Missing screenshot image data or IEND: " + path.name)
    decompressor = zlib.decompressobj()
    decoded = decompressor.decompress(bytes(image_data), 60_000_000)
    if not decompressor.eof or len(decoded) < 4000:
        raise ValueError("Not a real rendered PNG pixel stream: " + path.name)
    w, h = size
    if (viewport == "desktop" and not (w >= 960 and h >= 500)
            or viewport == "mobile" and not (320 <= w <= 600 and h >= 500)):
        raise ValueError("Screenshot dimensions do not match device: " + path.name)
    return hashlib.sha256(raw).hexdigest()


def verify_demo_concept_evidence(slug: str, demo_folder: Path, manifest: dict) -> dict:
    """Hard block changed code before reviewer sees it as an approved concept."""
    if manifest.get("quality_contract_version") != 6:
        raise ValueError("New demo bypasses V6 quality contract.")
    if manifest.get("master_prompt_sha256") != MASTER_PROMPT_SHA256:
        raise ValueError("Changed demo was not researched under the current master prompt.")
    if manifest.get("visual_concepts_protocol") != "v1":
        raise ValueError("Three actual rendered concepts not required by this demo; HOLD.")
    selection = validate_creative_directions({
        "creative_directions": manifest.get("creative_directions"),
        "creative_selection": manifest.get("creative_selection")
    })
    records = manifest.get("rendered_concept_previews")
    if not isinstance(records, list) or len(records) != 3:
        raise ValueError("Exactly 3 real rendered concept previews required.")
    wanted = {c["id"] for c in selection["alternatives"]}
    found, hashes = set(), set()
    root = demo_folder.resolve()
    for record in records:
        if not isinstance(record, dict) or record.get("id") not in wanted:
            raise ValueError("Unknown rendered concept; cannot invent a fourth preview.")
        identifier = record["id"]
        if identifier in found:
            raise ValueError("Duplicate rendered concept ID.")
        found.add(identifier)
        for viewport in ("desktop", "mobile"):
            candidate = record.get(viewport)
            claimed_hash = record.get(viewport + "_sha256")
            if not isinstance(candidate, str) or not candidate.startswith("_concept_evidence/"):
                raise ValueError("Concept screenshots must be committed locally in approved evidence folder.")
            file = (root / candidate).resolve()
            if not file.is_relative_to(root) or not file.is_file() or file.is_symlink():
                raise ValueError("Untrusted, missing, or remote concept screenshot: " + candidate)
            digest = _png_evidence(file, viewport=viewport)
            if claimed_hash != digest or digest in hashes:
                raise ValueError("Concept image stale or re-used; real distinct renders required.")
            hashes.add(digest)
    if found != wanted:
        raise ValueError("Not all 3 selected/rejected concepts were actually rendered.")
    review = manifest.get("concept_comparison_review") or {}
    if (review.get("selected_id") != selection["selected"]["id"]
            or set(review.get("rejected_ids") or []) != wanted-{selection["selected"]["id"]}
            or not str(review.get("reviewer") or "").strip()
            or len(str(review.get("comparative_notes") or "").strip()) < 80
            or not str(review.get("reviewed_at") or "").strip()):
        raise ValueError("Missing real side-by-side design review and explicit rejection reasons.")
    return {"checked_concepts": 3, "screenshots": 6,
            "master_prompt_sha256": MASTER_PROMPT_SHA256,
            "status": "RENDERED_CONCEPT_EVIDENCE_PRESENT_NOT_PREMIUM_APPROVAL"}

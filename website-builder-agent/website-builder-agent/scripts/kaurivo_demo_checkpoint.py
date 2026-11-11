"""Private, bounded per-job filesystem checkpoints for the Kaurivo GitHub worker.

The sole persisted state is the verified prospect's own company JSON and its
source/visual/build assets. Never include other CRM rows, API keys, Git metadata,
logs, arbitrary host files or public GitHub artifacts. After a resume, all QA
steps still run for the exact last built version; a checkpoint is never approval.
"""
from __future__ import annotations

import hashlib
import io
import json
import re
import stat
import zipfile
from pathlib import Path, PurePosixPath

MAX_ARCHIVE_BYTES = 30 * 1024 * 1024
MAX_UNPACKED_BYTES = 105 * 1024 * 1024
MAX_FILES = 420
STAGES = ("researched", "concepts", "selected", "built", "revised_1", "revised_2")
ALLOWED_SUFFIXES = frozenset((
    ".html", ".css", ".js", ".json", ".png", ".jpg", ".jpeg", ".webp",
    ".svg", ".ico", ".woff", ".woff2", ".webmanifest", ".pdf", ".md",
    ".txt", ".avif", ".gif", ".mp4",
))
UUID_RE = re.compile(r"^[a-f0-9]{8}-(?:[a-f0-9]{4}-){3}[a-f0-9]{12}$")
SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9-]{0,119}$")


class CheckpointError(RuntimeError):
    pass


def _identity(slug: str, job_id: str, phase: str) -> None:
    if not SLUG_RE.fullmatch(slug) or not UUID_RE.fullmatch(job_id):
        raise CheckpointError("invalid checkpoint identity")
    if phase not in STAGES:
        raise CheckpointError("invalid checkpoint stage")


def _allowed(relative: PurePosixPath, slug: str, *, referenced: bool) -> bool:
    parts = relative.parts
    if (len(parts) < 3 or parts[0] != "output" or
            len(parts) > 12 or len(str(relative)) > 350 or
            any(p in (".", "..") or p.startswith(".") for p in parts)):
        return False
    if relative.suffix.lower() not in ALLOWED_SUFFIXES:
        return False
    if parts[1] == slug:
        return True
    return referenced and parts[1] in ("screenshots", "_reference_screenshot_cache")


def _referenced_paths(project: Path, company: dict, slug: str) -> set[Path]:
    """Whitelist only real output files referenced by THIS company's state."""
    output = (project / "output").resolve()
    found: set[Path] = set()

    def walk(value, depth=0):
        if depth > 25:
            return
        if isinstance(value, dict):
            for child in value.values():
                walk(child, depth + 1)
        elif isinstance(value, (list, tuple)):
            for child in value:
                walk(child, depth + 1)
        elif isinstance(value, str) and len(value) <= 900:
            if value.startswith(("https:", "http:", "data:", "javascript:")):
                return
            candidate = Path(value)
            if not candidate.is_absolute():
                candidate = project / candidate
            try:
                safe = candidate.resolve()
                if (safe.is_relative_to(output) and safe.is_file() and
                        _allowed(PurePosixPath(safe.relative_to(project).as_posix()),
                                 slug, referenced=True)):
                    found.add(safe)
            except (ValueError, OSError):
                return

    walk(company)
    return found


def _validate_phase(company: dict, slug: str, phase: str, project: Path) -> None:
    if not isinstance(company, dict) or company.get("slug") != slug:
        raise CheckpointError("company snapshot identity mismatch")
    if not isinstance(company.get("research"), dict) or not company["research"]:
        raise CheckpointError("research not complete")
    if STAGES.index(phase) >= STAGES.index("concepts"):
        if not isinstance(company.get("concept_previews"), dict) or not company["concept_previews"]:
            raise CheckpointError("concept snapshot not complete")
    if STAGES.index(phase) >= STAGES.index("selected"):
        if not isinstance(company["research"].get("creative_selection"), dict):
            raise CheckpointError("concept selection not complete")
    if STAGES.index(phase) >= STAGES.index("built"):
        build = company.get("build")
        if not isinstance(build, dict) or not build.get("page_paths"):
            raise CheckpointError("built site manifest missing")
        source = Path(str(build.get("output_path") or ""))
        path = (source if source.is_absolute() else project / source).resolve()
        if (path != (project / "output" / slug / "index.html").resolve()
                or not path.is_file()):
            raise CheckpointError("built home route missing")
        if not build.get("version"):
            raise CheckpointError("built version marker missing")
        for route in build["page_paths"]:
            if not isinstance(route, str) or not route.endswith(".html"):
                raise CheckpointError("invalid build route")
            route_path = (project / "output" / slug / route).resolve()
            if not route_path.is_relative_to(project / "output" / slug) or not route_path.is_file():
                raise CheckpointError("build route missing from snapshot")


def make_archive(project: Path, slug: str, job_id: str,
                 phase: str, company: dict) -> bytes:
    """Create content-only ZIP; no symlinks, secrets, other client state."""
    _identity(slug, job_id, phase)
    project = project.resolve()
    _validate_phase(company, slug, phase, project)
    targets: set[Path] = set()
    own = project / "output" / slug
    if own.is_dir():
        for path in own.rglob("*"):
            if path.is_symlink():
                raise CheckpointError("symlink in demo output")
            if path.is_file():
                targets.add(path.resolve())
    targets |= _referenced_paths(project, company, slug)

    # Original-company images may be created before Research finishes but
    # not yet referenced in a JSON field if a later stage was interrupted.
    screenshots = project / "output" / "screenshots"
    if screenshots.is_dir():
        for path in screenshots.glob("original-client-" + slug + "_*"):
            if path.is_symlink():
                raise CheckpointError("symlink in source images")
            if path.is_file():
                targets.add(path.resolve())

    entries: list[tuple[str, bytes]] = []
    total = 0
    for path in sorted(targets):
        try:
            relative = PurePosixPath(path.relative_to(project).as_posix())
        except ValueError as exc:
            raise CheckpointError("out-of-project asset") from exc
        if not _allowed(relative, slug, referenced=True):
            raise CheckpointError("unapproved checkpoint asset")
        if path.stat().st_size > MAX_UNPACKED_BYTES:
            raise CheckpointError("oversized checkpoint file")
        payload = path.read_bytes()
        total += len(payload)
        if total > MAX_UNPACKED_BYTES:
            raise CheckpointError("checkpoint exceeds uncompressed budget")
        entries.append((str(relative), payload))

    manifest = {"format": 1, "job_id": job_id, "slug": slug,
                "phase": phase, "project_root": str(project)}
    entries += [
        ("checkpoint.json", json.dumps(manifest, sort_keys=True).encode()),
        ("company.json", json.dumps(company, ensure_ascii=False, sort_keys=True).encode()),
    ]
    if len(entries) > MAX_FILES:
        raise CheckpointError("too many checkpoint files")
    result = io.BytesIO()
    with zipfile.ZipFile(result, "w", compression=zipfile.ZIP_DEFLATED,
                         compresslevel=6, allowZip64=False) as zf:
        for name, contents in sorted(entries):
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = (stat.S_IFREG | 0o600) << 16
            zf.writestr(info, contents)
            if result.tell() > MAX_ARCHIVE_BYTES:
                raise CheckpointError("checkpoint exceeds private storage limit")
    archive = result.getvalue()
    if len(archive) < 1 or len(archive) > MAX_ARCHIVE_BYTES:
        raise CheckpointError("checkpoint exceeds private storage limit")
    return archive


def _relocate(value, old_root: str, new_root: str):
    """Only relocate absolute paths inside the exact recorded project root."""
    if isinstance(value, dict):
        return {key: _relocate(child, old_root, new_root)
                for key, child in value.items()}
    if isinstance(value, list):
        return [_relocate(child, old_root, new_root) for child in value]
    if isinstance(value, str) and value.startswith(old_root + "/"):
        return new_root + value[len(old_root):]
    return value


def unpack_archive(project: Path, slug: str, job_id: str,
                   phase: str, archive: bytes, sha256: str,
                   *, expected_name: str, expected_source: str) -> dict:
    """Validate complete contents before writing ANY files into working tree."""
    _identity(slug, job_id, phase)
    project = project.resolve()
    if (len(archive) < 1 or len(archive) > MAX_ARCHIVE_BYTES or
            not re.fullmatch("[0-9a-f]{64}", sha256) or
            hashlib.sha256(archive).hexdigest() != sha256):
        raise CheckpointError("checkpoint digest mismatch")
    extracted: dict[str, bytes] = {}
    total = 0
    try:
        with zipfile.ZipFile(io.BytesIO(archive), "r") as zf:
            if len(zf.infolist()) > MAX_FILES:
                raise CheckpointError("checkpoint file count exceeded")
            for member in zf.infolist():
                name = member.filename
                relative = PurePosixPath(name)
                if (member.is_dir() or name in extracted or
                    name.startswith("/") or "\\" in name or
                    any(part in ("", ".", "..") for part in relative.parts) or
                    str(relative) != name):
                    raise CheckpointError("unsafe checkpoint member")
                mode = (member.external_attr >> 16) & 0xFFFF
                if stat.S_IFMT(mode) not in (0, stat.S_IFREG):
                    raise CheckpointError("checkpoint contains nonregular file")
                if name not in ("checkpoint.json", "company.json") and not _allowed(
                        relative, slug, referenced=True):
                    raise CheckpointError("checkpoint contains unrelated client file")
                total += member.file_size
                if total > MAX_UNPACKED_BYTES or member.file_size > MAX_UNPACKED_BYTES:
                    raise CheckpointError("checkpoint expansion limit")
                data = zf.read(member)
                if len(data) != member.file_size:
                    raise CheckpointError("checkpoint entry truncated")
                extracted[name] = data
    except (zipfile.BadZipFile, EOFError, OverflowError) as exc:
        raise CheckpointError("invalid checkpoint zip") from exc
    if "checkpoint.json" not in extracted or "company.json" not in extracted:
        raise CheckpointError("checkpoint metadata missing")
    try:
        meta = json.loads(extracted.pop("checkpoint.json"))
        company = json.loads(extracted.pop("company.json"))
    except (ValueError, TypeError, UnicodeError) as exc:
        raise CheckpointError("invalid checkpoint JSON") from exc
    if not isinstance(meta, dict) or (
            meta.get("format"), meta.get("job_id"), meta.get("slug"), meta.get("phase")) != (
                1, job_id, slug, phase):
        raise CheckpointError("checkpoint belongs to different job or stage")
    old_root = meta.get("project_root")
    if not isinstance(old_root, str) or not Path(old_root).is_absolute():
        raise CheckpointError("invalid old project root")
    company = _relocate(company, old_root, str(project))
    if (not isinstance(company, dict) or company.get("slug") != slug or
            company.get("name") != expected_name or
            company.get("url") != expected_source):
        raise CheckpointError("checkpoint company identity conflict")
    # Ensure all required paths exist IN THE ARCHIVE before touching the
    # workspace. A missing route cannot be excused by an old checkout file.
    if STAGES.index(phase) >= STAGES.index("built"):
        build = company.get("build")
        if not isinstance(build, dict) or not isinstance(build.get("page_paths"), list):
            raise CheckpointError("built manifest not preserved")
        expected = {"output/" + slug + "/" + route for route in build["page_paths"]
                    if isinstance(route, str) and route.endswith(".html")}
        if (not expected or len(expected) != len(build["page_paths"]) or
                "output/" + slug + "/index.html" not in expected or
                not expected.issubset(extracted)):
            raise CheckpointError("incomplete built route snapshot")
    # Atomic-ish restore: all input validated first, then write files under
    # pre-approved workspace roots; company state is published by caller LAST.
    for name, data in sorted(extracted.items()):
        target = project / name
        target.parent.mkdir(parents=True, exist_ok=True)
        if target.is_symlink() or any(p.is_symlink() for p in target.parents if p != project):
            raise CheckpointError("unsafe existing symlink")
        if not target.resolve().is_relative_to(project):
            raise CheckpointError("checkpoint target escaped project")
        target.write_bytes(data)
    _validate_phase(company, slug, phase, project)
    return company

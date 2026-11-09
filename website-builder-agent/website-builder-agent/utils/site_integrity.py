"""Exact-build hash of every route and packaged image, style and script.

An index.html digest alone cannot protect a multi-page site against
post-QA edits to pages, work photography, typography, CSS or JS interactions.
Every public image, logo, font, script and style is content-addressed even
outside assets/ (for example images/, media/, or site-root logo.png).
Remote CDN assets still require separate live verification and human rights review.
"""
from __future__ import annotations
from hashlib import sha256
from pathlib import Path
from utils.site_architecture import route_path

ALLOWED_ASSET_EXTENSIONS={".png",".jpg",".jpeg",".gif",".svg",".avif",".webp",
                          ".ico",".css",".js",".mjs",".json",".webmanifest",
                          ".woff",".woff2"}

def site_files(root: str | Path, page_paths: list[str]) -> list[tuple[str,Path]]:
    base=Path(root).resolve()
    if not base.is_dir():
        raise RuntimeError("Generated site directory missing.")
    files=[]
    seen=set()
    for item in page_paths:
        route=route_path(item)
        if route in seen: raise RuntimeError("Duplicate generated route.")
        seen.add(route)
        target=base/route
        if not target.is_file() or target.is_symlink() or not target.resolve().is_relative_to(base):
            raise RuntimeError("Unsafe or missing generated HTML route: "+route)
        files.append((route,target))
    if "index.html" not in seen:
        raise RuntimeError("Missing generated index.html.")
    # Every public asset matters, wherever the author placed it. Previously
    # only assets/ was hashed, so editing a root-level logo.png or images/
    # portfolio photo after QA silently bypassed the review/delivery hash.
    # Private captured review/concept evidence is not part of the published site.
    public_routes = set(seen)
    for target in sorted(base.rglob("*")):
        rel = target.relative_to(base)
        if any(part.startswith(("_", ".")) for part in rel.parts):
            continue
        # Private screenshots produced by the concept-review renderer are
        # created AFTER the prototype HTML hash. They are verified separately
        # by concept_previews (SHA256) and must not mutate the site's bundle
        # digest when the screenshots are captured. Limit this exemption to
        # internal prototype variant directories, never actual customer sites.
        if base.name.startswith("variant-") and "qa" in rel.parts:
            continue
        if target.is_symlink():
            raise RuntimeError("Symlink cannot be a published site asset.")
        if target.is_dir():
            continue
        rel_text = rel.as_posix()
        if rel_text in public_routes:
            continue
        if not target.is_file() or not target.resolve().is_relative_to(base):
            raise RuntimeError("Unsafe site bundle file: " + str(target))
        if target.suffix.lower() == ".html":
            raise RuntimeError("Unreviewed HTML route exists in release bundle: "+rel_text)
        if target.suffix.lower() in ALLOWED_ASSET_EXTENSIONS:
            files.append((rel_text,target))
        elif rel.parts[0] == "assets":
            raise RuntimeError("Unsupported public asset in site bundle: "+rel_text)
    return sorted(files,key=lambda pair:pair[0])

def site_sha256(root: str | Path, page_paths: list[str]) -> str:
    data=sha256()
    for rel,path in site_files(root,page_paths):
        content=path.read_bytes()
        data.update(len(rel.encode()).to_bytes(4,"big"))
        data.update(rel.encode())
        data.update(len(content).to_bytes(8,"big"))
        data.update(content)
    return data.hexdigest()

"""Exact-build hash of every route and packaged image.

An index.html digest alone cannot protect a multi-page site against
post-QA edits to service/product pages or changes to images.
"""
from __future__ import annotations
from hashlib import sha256
from pathlib import Path
from utils.site_architecture import route_path

ALLOWED_ASSET_EXTENSIONS={".png",".jpg",".jpeg",".gif",".svg",".avif",".webp"}

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
    assets=base/"assets"
    if assets.exists():
        if not assets.is_dir() or assets.is_symlink():
            raise RuntimeError("Unsafe assets directory.")
        for target in sorted(assets.rglob("*")):
            if target.is_dir(): continue
            if (not target.is_file() or target.is_symlink()
                or not target.resolve().is_relative_to(base)
                or target.suffix.lower() not in ALLOWED_ASSET_EXTENSIONS):
                raise RuntimeError("Untrusted asset in site bundle: "+str(target))
            files.append((target.relative_to(base).as_posix(),target))
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

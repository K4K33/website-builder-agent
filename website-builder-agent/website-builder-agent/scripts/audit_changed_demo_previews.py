"""Check every changed static demo through real universal QA before merge.

This catches hand-committed demos that skip Builder's preflight; passing
objective checks is NOT an independent premium quality score.
"""
from __future__ import annotations
import os
from pathlib import Path
import subprocess
import sys
ROOT=Path(__file__).resolve().parents[1]
# Executed as python scripts/..., so explicitly make the project package root importable.
sys.path.insert(0, str(ROOT))
from utils.universal_quality import audit_universal_standards
DEMOS=ROOT/"docs"/"kaurivo"/"demos"
PREFIX="website-builder-agent/website-builder-agent/docs/kaurivo/demos/"

def changed_slugs(base,head):
    changed=subprocess.check_output(["git","diff","--name-only",base,head],cwd=ROOT,text=True).splitlines()
    return sorted({p[len(PREFIX):].split("/",1)[0] for p in changed
                   if p.startswith(PREFIX) and "/" in p[len(PREFIX):]
                   and not p[len(PREFIX):].startswith("_shared/")})

def verified_source_evidence(slug):
    """Accept only explicit source-grounded affiliation inventories.

    This is observed-source evidence for internal demos, NEVER licence or client
    approval. The independent screenshots and rights gates remain pending.
    """
    import json
    from urllib.parse import urlsplit
    safe = slug.replace("-", "").replace("_", "")
    if not safe.isalnum():
        raise ValueError("Invalid demo slug")
    manifest = ROOT / "data" / "demo_provenance" / (slug + ".json")
    if not manifest.is_file():
        return {}
    data = json.loads(manifest.read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or data.get("stage") != "internal_demo":
        raise ValueError("Unexpected source evidence format/stage")
    source = data.get("source_url", "")
    host = urlsplit(source).hostname
    if not host or not source.startswith("https://"):
        raise ValueError("Source must be a verified HTTPS domain")
    entries = data.get("footer_assets") or []
    if not entries or len(entries) > 100:
        raise ValueError("Missing or unreasonably large partner inventory")
    found = set()
    for item in entries:
        url = item.get("src", "")
        page = item.get("source_url", "")
        if (not item.get("name") or not url.startswith("https://")
            or urlsplit(url).hostname != host
            or urlsplit(page).hostname != host
            or not page.startswith("https://")
            or url in found):
            raise ValueError("Source assets must be unique and first-party")
        found.add(url)
    return {"source_inventory":{"pages":[{
        "url":source,
        "footer_assets":[{"src":x["src"],"name":x["name"]} for x in entries]
    }]}}

def main():
    base,head=os.environ.get("BASE_SHA",""),os.environ.get("HEAD_SHA","")
    if not base or not head:
        print("BLOCK: missing commit range for universal demo audit")
        return 2
    failed=False
    for slug in changed_slugs(base,head):
        folder=DEMOS/slug
        if not folder.is_dir():
            continue
        pages={str(p.relative_to(folder)):p.read_text(encoding="utf-8")
               for p in folder.rglob("index.html")}
        if "index.html" not in pages:
            print("BLOCK",slug,"missing index.html")
            failed=True
            continue
        result=audit_universal_standards(pages["index.html"],research=verified_source_evidence(slug),rendered_pages=pages,stage="internal_demo")
        problems=result.get("blocking_problems") or {}
        if problems:
            failed=True
            for category,messages in sorted(problems.items()):
                print("BLOCK",slug,category,"; ".join(messages[:3])[:550])
        else:
            print("OBJECTIVE PASS",slug,len(pages),"routes; real visual/media and source review still required")
    return 1 if failed else 0

if __name__=="__main__":
    sys.exit(main())

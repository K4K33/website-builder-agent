"""Source-grounded multi-page information architecture and safe generated site bundles.

Source pages and content-rich businesses require actual new service/product
routes instead of a single brochure or redirects back to the old site.
"""
from __future__ import annotations
import json
import re
from pathlib import PurePosixPath

MAX_PAGES = 14
MAX_JSON_BYTES = 1_600_000

def route_path(value: str) -> str:
    raw = str(value or "").strip()
    if not raw or chr(92) in raw or raw.startswith(("/", ".")) or "?" in raw or "#" in raw:
        raise ValueError("Route must be a safe site-relative HTML filename.")
    p = PurePosixPath(raw)
    if (any(part in ("", ".", "..") for part in raw.split("/"))
        or p.suffix.lower() != ".html" or len(p.parts) > 4
        or any(not re.fullmatch(r"[a-z0-9][a-z0-9_-]*", part) for part in p.parts[:-1])
        or not re.fullmatch(r"[a-z0-9][a-z0-9_-]*[.]html", p.name)):
        raise ValueError("Invalid site-relative route: " + raw[:140])
    return str(p)

def _target_route(value: str) -> str:
    return route_path(str(value or "").split("#", 1)[0])

def validate_site_architecture(research: dict, *, no_site: bool = False) -> dict:
    plan = research.get("site_architecture")
    if not isinstance(plan, dict) or not isinstance(plan.get("pages"), list):
        raise RuntimeError("Missing an actual site information architecture.")
    pages = plan["pages"]
    if not 1 <= len(pages) <= MAX_PAGES:
        raise RuntimeError("Site architecture needs between 1 and 14 pages.")
    routes = set()
    for page in pages:
        if not isinstance(page, dict):
            raise RuntimeError("Invalid page plan.")
        try: route = route_path(page.get("path"))
        except ValueError as exc: raise RuntimeError(str(exc)) from exc
        if route in routes:
            raise RuntimeError("Duplicate route: " + route)
        routes.add(route)
        if not all(isinstance(page.get(key), str) and len(page[key].strip()) >= 13
                   for key in ("purpose", "user_task")):
            raise RuntimeError("Every route needs a distinct business purpose and visitor task.")
        sections = page.get("section_ids")
        if not isinstance(sections, list) or not sections or any(
            not re.fullmatch(r"[a-z][a-z0-9_-]*", str(a or "")) for a in sections
        ):
            raise RuntimeError("Every planned route needs valid section ids.")
    if "index.html" not in routes:
        raise RuntimeError("Site plan must contain index.html.")
    inventory = research.get("source_inventory") or {}
    originals = inventory.get("pages") or []
    old_words = sum(len(str(p.get("text") or "").split()) for p in originals)
    min_pages = 2 if not no_site and (len(originals) >= 3 or old_words >= 650) else 1
    if len(pages) < min_pages:
        raise RuntimeError("A content-rich source site cannot be replaced by one brochure page.")
    missing = []
    for item in (research.get("source_content_map") or {}).get("pages") or []:
        if not isinstance(item, dict): continue
        targets = [item.get("target")]
        targets.extend(s.get("target") for s in item.get("sections") or [] if isinstance(s,dict))
        for value in targets:
            try:
                if _target_route(value) not in routes: missing.append(str(value))
            except ValueError:
                missing.append(str(value))
    if missing:
        raise RuntimeError("Source topics planned outside real routes: " + ", ".join(missing[:8]))
    return {"pages": pages, "page_paths": [p["path"] for p in pages],
            "source_page_count": len(originals), "minimum_page_count": min_pages}

def parse_generated_site(raw: str, architecture: dict) -> dict[str, str]:
    required = set(architecture["page_paths"])
    text = str(raw or "").strip()
    if len(text.encode("utf-8")) > MAX_JSON_BYTES:
        raise RuntimeError("Site bundle exceeds a safe bounded size.")
    if text.lower().startswith("<!doctype html"):
        if required != {"index.html"}:
            raise RuntimeError("A multi-page design cannot be delivered as one index.html.")
        return {"index.html": text}
    if text.startswith("~~~"):
        text = "\n".join(text.splitlines()[1:-1]).strip()
    try: data = json.loads(text)
    except (TypeError, ValueError) as exc:
        raise RuntimeError("Generator must return a valid JSON website bundle.") from exc
    items = data.get("pages") if isinstance(data, dict) else None
    if not isinstance(items, dict) or len(items) != len(required):
        raise RuntimeError("Website bundle must have exactly the planned routes.")
    pages = {}
    for key, html in items.items():
        try: route = route_path(key)
        except ValueError as exc: raise RuntimeError(str(exc)) from exc
        if not isinstance(html, str) or not html.lstrip().lower().startswith("<!doctype html"):
            raise RuntimeError("Incomplete page HTML for " + route)
        pages[route] = html.strip()
    if set(pages) != required:
        raise RuntimeError("Generated pages differ from approved plan.")
    return pages

def pages_for_validation(pages: dict[str,str]) -> str:
    """Visible text across routes for parity; each route needs separate QA."""
    from bs4 import BeautifulSoup
    return "<html><body>" + "\n".join(
        BeautifulSoup(pages[key], "html.parser").get_text(" ", strip=True)
        for key in sorted(pages)
    ) + "</body></html>"

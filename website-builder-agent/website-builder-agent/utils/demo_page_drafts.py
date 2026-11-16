"""Persist complete page drafts for a single queued job, separate from the public site."""
from hashlib import sha256
import json
from pathlib import Path

from utils.site_architecture import MAX_JSON_BYTES, parse_generated_site


DRAFT_DIR = "_demo_page_drafts"


def draft_pages(*, root, job_id, phase, routes, system, prompt_for, request, image_paths=()):
    """Generate and validate one complete response per route and reuse matching drafts."""
    directory = Path(root) / DRAFT_DIR
    directory.mkdir(parents=True, exist_ok=True)
    images = [sha256(Path(path).read_bytes()).hexdigest() for path in image_paths]
    pages = {}
    for route in routes:
        prompt = prompt_for(route)
        key = sha256(json.dumps([job_id, phase, route, system, prompt, images],
                                ensure_ascii=False).encode()).hexdigest()
        cache = directory / (key + ".json")
        contract = {"page_paths": [route]}
        if cache.is_file() and cache.stat().st_size <= MAX_JSON_BYTES:
            try:
                pages.update(parse_generated_site(cache.read_text(encoding="utf-8"), contract))
                continue
            except (RuntimeError, UnicodeError):
                pass
        raw = request(system, prompt + "\nFINAL RESPONSE SCOPE: return only the complete "
                      "HTML document for " + route + " in the pages JSON object. "
                      "Other routes are context for consistent branding and working local links. "
                      "Use compact CSS and no repeated code or explanations outside the document.")
        pages.update(parse_generated_site(raw, contract))
        temporary = cache.with_suffix(".tmp")
        temporary.write_text(raw, encoding="utf-8")
        temporary.replace(cache)
    return pages

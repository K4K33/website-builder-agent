"""Persist complete page drafts for a single queued job, separate from the public site."""
from hashlib import sha256
import json
from pathlib import Path

from utils.site_architecture import MAX_JSON_BYTES, parse_generated_site
from utils.kaurivo_free_json_envelope import parse_complete_model_json


DRAFT_DIR = "_demo_page_drafts"


def _page_from_response(raw, route, concept_id):
    """Resolve only the requested document, including older model envelopes."""
    if not isinstance(raw, str) or len(raw.encode("utf-8")) > MAX_JSON_BYTES:
        raise RuntimeError("Requested page response is missing or oversized.")
    if raw.lstrip().lower().startswith("<!doctype html"):
        document = raw
    else:
        data = parse_complete_model_json(raw)
        if not isinstance(data, dict):
            raise RuntimeError("Requested page response must be an object.")
        # A route-named response is authoritative. Older instructions can
        # still cause the model to wrap one page in its exact concept ID.
        concepts = data.get("concepts")
        if concept_id and isinstance(concepts, dict):
            data = concepts.get(concept_id)
            if not isinstance(data, dict):
                raise RuntimeError("Requested concept is absent from the response.")
        pages = data.get("pages")
        document = pages.get(route) if isinstance(pages, dict) else data.get("html")
    if not isinstance(document, str) or not document.rstrip().lower().endswith("</html>"):
        raise RuntimeError("Requested route differs from the response or its HTML is incomplete.")
    canonical = json.dumps({"pages": {route: document}}, ensure_ascii=False)
    return canonical, parse_generated_site(canonical, {"page_paths": [route]})


def draft_pages(*, root, job_id, phase, routes, system, prompt_for, request, image_paths=(),
                concept_id=None):
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
        scope = ("This call only authors " + route + ". Return JSON with one key "
                 '`html` holding the complete document from <!doctype html> through </html>. '
                 "Keep all other routes as navigation targets only. Use compact CSS.")
        raw = request(scope + "\n\n" + system, scope + "\n\n" + prompt + "\n\n" + scope)
        canonical, parsed = _page_from_response(raw, route, concept_id)
        pages.update(parsed)
        temporary = cache.with_suffix(".tmp")
        temporary.write_text(canonical, encoding="utf-8")
        temporary.replace(cache)
    return pages

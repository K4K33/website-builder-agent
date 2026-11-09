"""Explicit model/import entry points for source-bound visible concept choice."""
from pathlib import Path
import json
import config
from utils.concept_previews import (preview_routes, write_concepts, load_verified_set,
                                    blind_order, record_selection)
from utils.local_media_intake import stage_local_media
from utils.state import get_company, upsert_company

CONCEPT_PROMPT = '''Create THREE ACTUAL RESPONSIVE HTML CONCEPTS, not prose alternatives.
Return JSON {"concepts": {direction_id: {"pages": {route: "<!doctype html>..."}}}}.
Each concept has exactly the supplied two routes: home and one key content page.
Use only the verified facts, original brand and explicitly supplied local media.
Do not invent logos, products, testimonials, staff or a capability. Do not use
stock/generative imagery as client work. Use exact intake src filenames; nested
routes resolve them with ../ as appropriate. All CSS is inline. No scripts,
forms, iframes, external stylesheets or network resources. Navigation connects
the two prototype pages. Include nav, main, footer, title, meta description/viewport, one h1 per page and mobile responsive CSS.
The concepts must visibly differ in composition and information hierarchy,
not just colour, font, heading wording or decoration. Each home has its first
view and one meaningful content section; the other page serves its visitor task.
These are PRIVATE PROTOTYPES, never a completed client website or checkout.
'''


def source_visual_evidence(research):
    """Require actual original-company screenshots in approved capture storage.

    Never use customer supplied arbitrary file paths, stale image-only claims,
    or competitor screenshots as a replacement for source brand experience.
    """
    if research.get("premium_visual_protocol") != "v2":
        return []
    if research.get("research_mode") == "verified_no_website":
        return []
    from utils.screenshot import OUTPUT_DIR as screenshots_root
    from hashlib import sha256
    safe_root = Path(screenshots_root).resolve()
    captured = research.get("original_screenshots") or {}
    evidence = []
    for viewport in ("desktop", "mobile"):
        original = captured.get(viewport)
        if not isinstance(original, str) or not original:
            raise RuntimeError("Premium concept selection requires real original " +
                               viewport + " screenshots before full Build.")
        file = Path(original).resolve()
        if (not file.is_relative_to(safe_root) or not file.is_file()
                or not file.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")):
            raise RuntimeError("Original source screenshot missing or outside safe capture storage.")
        evidence.append({"viewport": viewport, "path": str(file),
                         "sha256": sha256(file.read_bytes()).hexdigest(),
                         "role": "original_company_site_not_competitor"})
    return evidence


def _company(name):
    slug, company = get_company(name)
    if not company or not company.get('research'):
        raise RuntimeError('Research is required before visual concepts')
    return slug, company


def generate_concepts(name, *, response_path=None, producer=''):
    from agents.builder import _validate_generated_content
    from utils.browser_qa import inspect_site
    from utils.claude_client import ask_claude_json
    from utils.creative_directions import validate_creative_directions
    slug, company = _company(name)
    research = company['research']; validate_creative_directions(research)
    # Prepare deterministic intake filenames before asking the generator.
    root = Path(config.OUTPUT_DIR) / slug
    media = stage_local_media(company.get('media_intake'), intake_root=config.MEDIA_INTAKE_DIR,
                              output_dir=root)
    if response_path:
        if not producer.strip(): raise RuntimeError('External concept producer must be explicit')
        raw = Path(response_path).read_text(encoding='utf-8')
    else:
        authored = ask_claude_json(CONCEPT_PROMPT, json.dumps({
            'facts': research.get('company_facts'), 'directions': research['creative_directions'],
            'required_routes': preview_routes(research), 'media': media,
            'brand_plan': research.get('brand_preservation_plan'),
            'site_architecture': research.get('site_architecture')}, ensure_ascii=False),
            max_tokens=config.BUILDER_MAX_TOKENS, stage='builder')
        raw = json.dumps(authored, ensure_ascii=False)
        producer = config.backend_for_stage('builder') + ':' + config.model_for_stage('builder')
    result = write_concepts(raw, research, output_parent=root / '_concept_previews',
        producer=producer, renderer=inspect_site, media_items=company.get('media_intake'),
        intake_root=config.MEDIA_INTAKE_DIR, content_validator=_validate_generated_content)
    upsert_company(slug, {'concept_previews': result})
    return result


def choose_concept(name, *, review_path=None, reviewer=''):
    from utils.claude_client import ask_claude_json
    slug, company = _company(name); research = company['research']
    root = Path(config.OUTPUT_DIR) / slug
    reference = company.get('concept_previews') or {}
    path, manifest = load_verified_set(reference, research, allowed_root=root)
    order = blind_order(manifest)
    views = [{'alias': alias, **view} for alias, entry in order.items() for view in entry['views']]
    sources = source_visual_evidence(research)
    if review_path:
        if not reviewer.strip(): raise RuntimeError('External visual reviewer must be explicit')
        report = json.loads(Path(review_path).read_text(encoding='utf-8'))
    else:
        # Fresh context, shuffled aliases; no Builder self-praise or preferred winner.
        report = ask_claude_json(
            'Compare all twelve real concept screenshots (three concepts x two routes x '
            'desktop/mobile) with the verified client tasks and ORIGINAL company screens. '
            'Do not prefer the first choice automatically. Return selected_alias A/B/C, '
            'observations (A/B/C with concrete critical reasons), critical_issues '
            '(A/B/C arrays) and reviewed_view_ids for every concept image. '
            'For premium_visual_protocol=v2, return view_assessments for ALL twelve '
            'view ids: verdict pass/needs_revision, brand_evidence, '
            'composition_evidence and media_evidence (each >=35 concrete characters). '
            'source_reference_reviewed=true only when actual original-company '
            'screenshots were provided and inspected. Reject decorative filler, '
            'repetitive layouts, lost original logos/patterns/textures, photo misuse, '
            'weak content pages and inaccessible mobile compositions. The winning '
            'concept needs a pass on each page at both viewports and zero unresolved '
            'critical issues. An unsatisfactory candidate MUST be rejected. '
            'This is a preliminary visual choice, NOT a 9.5 score, licence or '
            'independent human client approval.',
            json.dumps({
                'facts': research.get('company_facts'),
                'visitor_tasks': (research.get('site_architecture') or {}).get('pages'),
                'views_in_image_order': [
                    {k: v for k, v in view.items() if k != 'path'} for view in views],
                'original_source_images_after_concept_images': [
                    {k: v for k, v in view.items() if k != 'path'} for view in sources],
                'premium_visual_protocol': research.get('premium_visual_protocol'),
                'brand_signature_plan': research.get('brand_signature_plan') or {},
            }, ensure_ascii=False),
            stage='qa', max_tokens=6500,
            image_paths=[str(path.parent / view['path']) for view in views]
                        + [view['path'] for view in sources])
        reviewer = config.backend_for_stage('qa') + ':' + config.model_for_stage('qa')
    reference, choice = record_selection(reference, research, report, allowed_root=root, reviewer=reviewer)
    updated = dict(research); updated['creative_selection'] = choice
    upsert_company(slug, {'research': updated, 'concept_previews': reference})
    return {'concept_previews': reference, 'choice': choice, 'premium_approval': False}

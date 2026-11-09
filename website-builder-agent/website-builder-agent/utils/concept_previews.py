"""Three real, private, source-bound responsive concept bundles before Build.

Generates no stock layout and makes no network/model calls. A caller supplies
actual authored HTML and an explicit producer. Browser rendering is injectable
for offline tests; rendered screenshots are integrity-checked on every use.
"""
from __future__ import annotations
from hashlib import sha256
from pathlib import Path
import html
import json
import random
import shutil
import re
from tempfile import mkdtemp
from bs4 import BeautifulSoup
from utils.creative_directions import validate_creative_directions
from utils.local_media_intake import stage_local_media
from utils.service_quality import service_brief
from utils.site_architecture import route_path
from utils.site_integrity import site_files, site_sha256
from utils.visual_originality import _structure

PROTOCOL = 'visual-concepts-v1'
REQUIRED_VIEWS = ('desktop', 'mobile')
MAX_RESPONSE_BYTES = 1_600_000


def digest(value):
    return sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                            separators=(',', ':')).encode()).hexdigest()


def file_hash(path):
    return sha256(Path(path).read_bytes()).hexdigest()


def context_digest(research):
    return digest({'service': service_brief({**research, 'creative_selection': None})['contract_sha256'],
                   'directions': research.get('creative_directions'),
                   'architecture': research.get('site_architecture'),
                   'brand_plan': research.get('brand_preservation_plan'),
                   'premium_visual_protocol': research.get('premium_visual_protocol'),
                   'brand_signature_plan': research.get('brand_signature_plan')})


def intake_fingerprint(items, root):
    if not items:
        return digest([])
    base = Path(root).resolve()
    records = []
    for item in items:
        file = (base / item['file']).resolve()
        if not file.is_relative_to(base) or not file.is_file():
            raise RuntimeError('Concept media input is missing or outside the approved intake')
        records.append({'metadata': item, 'sha256': file_hash(file)})
    return digest(records)


def preview_routes(research):
    planned = (research.get('site_architecture') or {}).get('pages') or []
    secondary = next((p['path'] for p in planned if p.get('path') != 'index.html'), 'preview-detail.html')
    return ['index.html', route_path(secondary)]


def _layout_signature(pages):
    result = []
    for route, raw in sorted(pages.items()):
        soup = BeautifulSoup(raw, 'html.parser')
        css = ' '.join(s.get_text() for s in soup.find_all('style'))
        geometry = re.findall(r'(?:display|grid-template[^:;{}]*|flex-direction|order|position|text-align)\s*:\s*[^;}]+', css, re.I)
        main = soup.find('main')
        result.append([_structure(raw), re.sub(r'\s+', '', ' '.join(geometry)),
                       [e.name for e in main.find_all(recursive=False)] if main else []])
    return digest(result)


def parse_concepts(raw, research):
    choices = validate_creative_directions(research)
    expected = {d['id'] for d in choices['alternatives']}
    if not isinstance(raw, str) or len(raw.encode()) > MAX_RESPONSE_BYTES:
        raise RuntimeError('Concept response missing or oversized')
    try:
        value = json.loads(raw)
    except ValueError as error:
        raise RuntimeError('Concepts require a JSON object with real HTML pages') from error
    concepts = value.get('concepts') if isinstance(value, dict) else None
    if not isinstance(concepts, dict) or set(concepts) != expected:
        raise RuntimeError('Exactly the three planned concept ids are required')
    required_routes = set(preview_routes(research))
    output = {}
    for identifier, concept in concepts.items():
        pages = concept.get('pages') if isinstance(concept, dict) else None
        if not isinstance(pages, dict) or set(pages) != required_routes:
            raise RuntimeError('Each concept requires a home and the same key content route')
        for route, body in pages.items():
            route_path(route)
            if not isinstance(body, str) or not body.lstrip().lower().startswith('<!doctype html'):
                raise RuntimeError('Every concept page must contain complete HTML')
            soup = BeautifulSoup(body, 'html.parser')
            if not soup.find('main') or len(soup.select('main h1')) != 1 or not soup.find('style'):
                raise RuntimeError('Concept pages need a real main, one h1 and responsive styles')
            # These are visual prototypes. Never run authored code or collect data.
            if soup.find(['script', 'form', 'iframe', 'object', 'embed', 'base', 'link', 'svg', 'math', 'video', 'audio', 'source']):
                raise RuntimeError('Concepts must be self-contained presentation HTML; no scripts/forms/embeds')
            if soup.select('meta[http-equiv]'):
                raise RuntimeError('Concept pages cannot redirect or load an external document')
            for element in soup.find_all(True):
                if 'srcset' in element.attrs or (element.name != 'img' and 'src' in element.attrs):
                    raise RuntimeError('Only explicitly staged img sources may load in a concept')
                if any(str(key).lower().startswith('on') for key in element.attrs):
                    raise RuntimeError('Event handlers are forbidden in concepts')
            for a in soup.select('a[href]'):
                href = a['href']
                if href.startswith(('#', 'https://', 'mailto:', 'tel:')):
                    continue
                from urllib.parse import urljoin, urlsplit
                parsed = urlsplit(href)
                if parsed.scheme or parsed.netloc:
                    raise RuntimeError('Concept navigation cannot execute code or use an unapproved external scheme')
                dest = urlsplit(urljoin('https://preview.invalid/' + route, href)).path.lstrip('/')
                if dest not in required_routes:
                    raise RuntimeError('Concept navigation leaves its two actual prototype pages')
        output[identifier] = pages
    if len({_layout_signature(pages) for pages in output.values()}) != 3:
        raise RuntimeError('Three copies with changed colour or prose are not distinct concept prototypes')
    return output


def write_concepts(raw, research, *, output_parent, producer, renderer,
                   media_items=None, intake_root=None, content_validator=None):
    """Write a new immutable review set; never overwrite a prior selection."""
    if not str(producer).strip():
        raise RuntimeError('Actual concept producer must be recorded')
    pages_by_id = parse_concepts(raw, research)
    parent = Path(output_parent).resolve(); parent.mkdir(parents=True, exist_ok=True)
    root = Path(mkdtemp(prefix='set-', dir=parent))
    manifest = {'protocol': PROTOCOL, 'context_sha256': context_digest(research),
                'producer': producer, 'status': 'blocked', 'entries': [],
                'intake_sha256': intake_fingerprint(media_items, intake_root or root),
                'premium_approval': False}
    for position, (identifier, pages) in enumerate(pages_by_id.items(), 1):
        folder = root / ('variant-' + str(position)); folder.mkdir()
        media = stage_local_media(media_items, intake_root=intake_root or folder,
                                  output_dir=folder)
        if content_validator:
            for body in pages.values(): content_validator(body, research.get('company_facts') or {})
        allowed = {item['src'] for item in media}
        for route, body in pages.items():
            soup = BeautifulSoup(body, 'html.parser')
            css = ' '.join(s.get_text() for s in soup.find_all('style')) + ' ' + ' '.join(str(s.get('style')) for s in soup.select('[style]'))
            if re.search(r'@import', css, re.I):
                raise RuntimeError('Concept CSS cannot import other stylesheets')
            sources = [image['src'] for image in soup.select('img[src]')]
            sources += [match.strip().strip('\"\'') for match in re.findall(r'url\(\s*([^)]*)\)', css, re.I)]
            for src in sources:
                from urllib.parse import urljoin, urlsplit
                # Actual intake assets only. No invented pictures or old-host dependencies.
                resolved = urlsplit(urljoin('https://preview.invalid/' + route, src)).path.lstrip('/')
                if urlsplit(src).scheme or urlsplit(src).netloc or resolved not in allowed:
                    raise RuntimeError('Concept image must refer to an explicitly staged intake asset: ' + src[:100])
            file = folder / route; file.parent.mkdir(parents=True, exist_ok=True)
            file.write_text(body, encoding='utf-8')
        entry = {'id': identifier, 'folder': folder.relative_to(root).as_posix(),
                 'routes': list(pages), 'files': [], 'views': [], 'issues': []}
        for relative, file in site_files(folder, list(pages)):
            entry['files'].append({'path': file.relative_to(root).as_posix(), 'sha256': file_hash(file)})
        entry['site_sha256'] = site_sha256(folder, list(pages))
        for route in pages:
            report = renderer(folder / route, allowed_file_root=folder)
            entry['issues'].extend(str(i) for i in report.get('issues') or [])
            if report.get('pass') is not True:
                entry['issues'].append(route + ': browser checks did not pass')
            for viewport in REQUIRED_VIEWS:
                shot = (report.get('screenshots') or {}).get(viewport)
                file = Path(shot).resolve() if isinstance(shot, str) else None
                if not file or not file.is_file() or not file.is_relative_to(root):
                    entry['issues'].append(route + ': missing actual ' + viewport + ' screenshot')
                    continue
                if not file.read_bytes().startswith(b'\x89PNG\r\n\x1a\n'):
                    entry['issues'].append(route + ': screenshot is not a real PNG file')
                    continue
                capture = folder / '_captures' / digest(route)[:16] / (viewport + '.png')
                capture.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(file, capture)
                file = capture
                entry['views'].append({'id': digest([identifier, route, viewport])[:20],
                    'route': route, 'viewport': viewport, 'path': file.relative_to(root).as_posix(),
                    'sha256': file_hash(file)})
        manifest['entries'].append(entry)
    if all(not e['issues'] and len(e['views']) == 4 for e in manifest['entries']):
        manifest['status'] = 'ready_for_comparison'
    manifest['set_sha256'] = digest(manifest)
    file = root / 'manifest.json'; file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2))
    _write_comparison(root, manifest)
    return {'manifest_path': str(file), 'set_sha256': manifest['set_sha256'],
            'comparison_path': str(root / 'comparison.html'), 'status': manifest['status']}


def load_verified_set(reference, research, *, allowed_root):
    path = Path(reference.get('manifest_path') or '').resolve()
    base = Path(allowed_root).resolve()
    if not path.is_relative_to(base) or path.is_symlink() or not path.is_file():
        raise RuntimeError('Concept manifest missing or outside the private project output')
    manifest = json.loads(path.read_text(encoding='utf-8'))
    claimed = manifest.get('set_sha256')
    payload = {k: v for k, v in manifest.items() if k != 'set_sha256'}
    if claimed != digest(payload) or claimed != reference.get('set_sha256'):
        raise RuntimeError('Concept manifest changed after capture')
    if manifest.get('protocol') != PROTOCOL or manifest.get('context_sha256') != context_digest(research):
        raise RuntimeError('Concept source, voice, task or design plan changed; render again')
    if manifest.get('status') != 'ready_for_comparison':
        raise RuntimeError('Concepts have not passed actual rendering checks')
    expected = {d['id'] for d in validate_creative_directions(research)['alternatives']}
    if {e['id'] for e in manifest.get('entries') or []} != expected:
        raise RuntimeError('Concept set does not cover all three directions')
    for entry in manifest['entries']:
        folder = (path.parent / entry['folder']).resolve()
        if not folder.is_relative_to(path.parent) or site_sha256(folder, entry['routes']) != entry['site_sha256']:
            raise RuntimeError('Rendered concept HTML or assets changed')
        for item in entry['files'] + entry['views']:
            file = (path.parent / item['path']).resolve()
            if not file.is_relative_to(path.parent) or not file.is_file() or file_hash(file) != item['sha256']:
                raise RuntimeError('Concept page, media or screenshot is missing or changed')
    return path, manifest


def blind_order(manifest):
    entries = list(manifest['entries'])
    random.Random(manifest['set_sha256']).shuffle(entries)
    return dict(zip(('A', 'B', 'C'), entries))


def _write_comparison(root, manifest):
    cards = []
    for alias, entry in blind_order(manifest).items():
        shots = ''.join('<figure><figcaption>' + html.escape(v['route'] + ' · ' + v['viewport'])
                        + '</figcaption><img src="' + html.escape(v['path'], quote=True) + '"></figure>'
                        for v in entry['views'])
        cards.append('<section><h2>' + alias + '</h2>' + shots + '</section>')
    (root / 'comparison.html').write_text('<!doctype html><html lang="fi"><meta charset="utf-8">'
        '<meta name="robots" content="noindex"><title>Kolmen luonnoksen vertailu</title>'
        '<style>body{font:16px Arial;margin:24px;background:#f6f6f4;color:#222}main{display:grid;'
        'grid-template-columns:repeat(3,minmax(0,1fr));gap:24px}img{max-width:100%;height:auto}'
        'figure{margin:12px 0}section{min-width:0}@media(max-width:800px){main{grid-template-columns:1fr}}</style>'
        '<h1>Kolme toteutettua suunnitteluvaihtoehtoa</h1><p>Sisäinen vertailu. Näyttökuvat eivät ole laatuhyväksyntä.</p>'
        '<main>' + ''.join(cards) + '</main></html>', encoding='utf-8')


def record_selection(reference, research, report, *, allowed_root, reviewer):
    path, manifest = load_verified_set(reference, research, allowed_root=allowed_root)
    order = blind_order(manifest)
    selected = report.get('selected_alias')
    observations = report.get('observations') or {}
    issues = report.get('critical_issues') or {}
    view_ids = {v['id'] for e in manifest['entries'] for v in e['views']}
    if (selected not in order or set(observations) != set(order) or set(issues) != set(order)
        or any(not isinstance(v, str) or len(v.strip()) < 30 for v in observations.values())
        or any(not isinstance(v, list) for v in issues.values()) or issues[selected]
        or set(report.get('reviewed_view_ids') or []) != view_ids or not str(reviewer).strip()):
        raise RuntimeError('Visual choice needs all twelve real views, comparison of all three, and no critical winner issue')
    if research.get("premium_visual_protocol") == "v2":
        # A screenshot list alone does not establish visual quality. Every
        # variant, route and viewport must receive concrete, critical notes
        # before the full site can consume API credits. The winning route's
        # views need an explicitly acceptable verdict without unresolved gaps.
        checks = report.get("view_assessments") or {}
        if not isinstance(checks, dict) or set(checks) != view_ids:
            raise RuntimeError("Premium concepts need individual critical reviews of all twelve actual views.")
        winner_ids = {v["id"] for v in order[selected]["views"]}
        for view_id, assessment in checks.items():
            if not isinstance(assessment, dict) or assessment.get("verdict") not in (
                "pass", "needs_revision"):
                raise RuntimeError("Each real viewport needs a pass/needs_revision verdict.")
            for dimension in ("brand_evidence", "composition_evidence", "media_evidence"):
                detail = assessment.get(dimension)
                if not isinstance(detail, str) or len(detail.strip()) < 35:
                    raise RuntimeError(
                        f"{view_id}: {dimension} needs concrete image-grounded reasoning."
                    )
            if view_id in winner_ids and assessment["verdict"] != "pass":
                raise RuntimeError("Winning concept has a deficient route/viewport: revise before full Build.")
        if (report.get("source_reference_reviewed") is not True
            and research.get("research_mode") != "verified_no_website"):
            raise RuntimeError("Premium concept choice has no verified original-site screenshot comparison.")
        if str(reviewer).strip() == str(manifest.get("producer") or "").strip():
            raise RuntimeError("The concept producer cannot be its only visual reviewer.")
    choice = {'selected_id': order[selected]['id'], 'business_reason': observations[selected],
              'rejected_ids': [e['id'] for alias, e in order.items() if alias != selected]}
    source_proofs = []
    if research.get("premium_visual_protocol") == "v2":
        from utils.concept_workflow import source_visual_evidence
        source_proofs = [
            {"viewport": item["viewport"], "sha256": item["sha256"]}
            for item in source_visual_evidence(research)
        ]
    selection = {'set_sha256': manifest['set_sha256'], 'reviewer': reviewer, 'report': report,
                 'choice': choice, 'source_image_proofs': source_proofs,
                 'premium_approval': False}
    selection['selection_sha256'] = digest(selection)
    (path.parent / 'selection.json').write_text(json.dumps(selection, ensure_ascii=False, indent=2), encoding='utf-8')
    return {**reference, 'selection_sha256': selection['selection_sha256'], 'selection_path': str(path.parent / 'selection.json')}, choice


def validate_selected_concept(company, *, allowed_root):
    research = company.get('research') or {}
    if research.get('visual_concepts_protocol') != 'v1':
        return None
    reference = company.get('concept_previews') or {}
    path, manifest = load_verified_set(reference, research, allowed_root=allowed_root)
    import config
    if manifest.get('intake_sha256') != intake_fingerprint(company.get('media_intake'), config.MEDIA_INTAKE_DIR):
        raise RuntimeError('Client media or its permitted use changed; render concepts again')
    selection_path = path.parent / 'selection.json'
    if not selection_path.is_file():
        raise RuntimeError('Render and compare three concepts before the full Builder request')
    selection = json.loads(selection_path.read_text(encoding='utf-8'))
    claimed = selection.get('selection_sha256')
    if (claimed != digest({k: v for k, v in selection.items() if k != 'selection_sha256'})
        or claimed != reference.get('selection_sha256')
        or selection.get('set_sha256') != manifest['set_sha256']
        or selection.get('choice') != research.get('creative_selection')):
        raise RuntimeError('Concept choice changed or does not match the rendered comparison')
    if research.get("premium_visual_protocol") == "v2":
        from utils.concept_workflow import source_visual_evidence
        expected_source = [
            {"viewport": item["viewport"], "sha256": item["sha256"]}
            for item in source_visual_evidence(research)
        ]
        if selection.get("source_image_proofs") != expected_source:
            raise RuntimeError(
                "Original brand screenshots changed since concept selection; "
                "render/review the three design proposals again."
            )
    return selection

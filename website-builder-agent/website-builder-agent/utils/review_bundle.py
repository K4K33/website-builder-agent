"""Collect real review bytes into one private, tamper-evident evidence bundle.

Never downloads assets, submits a form, fabricates a review or publishes files.
A recorded reference is accepted only when its bytes exist inside this bundle.
"""
from __future__ import annotations
from hashlib import sha256
from pathlib import Path
from tempfile import mkdtemp
from urllib.parse import urljoin, urlsplit, unquote
import html
import json
import shutil
from bs4 import BeautifulSoup
from utils.concept_previews import digest, file_hash, load_verified_set
from utils.service_quality import service_brief
from utils.site_integrity import site_sha256

MAX_FILE_BYTES = 30 * 1024 * 1024
ALLOWED = {'.png', '.jpg', '.jpeg', '.webp', '.json', '.webm'}


def preserve_route_captures(report, *, site_root, route):
    """Freeze each route before inspect_site reuses its same-folder QA paths."""
    root = Path(site_root).resolve()
    saved = dict(report)
    saved['screenshots'] = {}
    for viewport, value in (report.get('screenshots') or {}).items():
        source = Path(value).resolve()
        if not source.is_file() or not source.is_relative_to(root):
            continue
        target = root / 'qa' / digest(route)[:16] / (digest(viewport)[:16] + source.suffix)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, target)
        saved['screenshots'][viewport] = str(target)
    return saved


def collect_review_bundle(company, pages, qa, *, site_root, output_parent,
                          allowed_capture_roots):
    research = company.get('research') or {}
    root = Path(site_root).resolve()
    parent = Path(output_parent).resolve(); parent.mkdir(parents=True, exist_ok=True)
    destination = Path(mkdtemp(prefix='review-', dir=parent))
    roots = [Path(p).resolve() for p in allowed_capture_roots] + [root]
    manifest = {'protocol': 'review-bundle-v1', 'artifact_sha256': site_sha256(root, list(pages)),
                'contract_sha256': service_brief(research)['contract_sha256'],
                'items': [], 'missing': [], 'premium_approval': False}

    def collect(file, kind, *, route='', viewport='', task_id='', asset_ids=None):
        try:
            original = Path(file)
            source = original.resolve()
            if (original.is_symlink() or not source.is_file() or source.suffix.lower() not in ALLOWED
                or not 0 < source.stat().st_size <= MAX_FILE_BYTES
                or not any(source.is_relative_to(base) for base in roots)):
                raise ValueError('Untrusted evidence path')
            content_hash = file_hash(source)
            identifier = digest([kind, route, viewport, task_id, content_hash] +
                                ([asset_ids] if asset_ids is not None else []))[:24]
            name = 'files/' + identifier + source.suffix.lower()
            target = destination / name; target.parent.mkdir(exist_ok=True)
            shutil.copyfile(source, target)
            item = {'id': identifier, 'kind': kind, 'path': name, 'sha256': content_hash,
                    'route': route, 'viewport': viewport, 'task_id': task_id}
            if asset_ids is not None:
                item['asset_ids'] = asset_ids
            if item not in manifest['items']: manifest['items'].append(item)
            return item
        except (OSError, ValueError, TypeError):
            manifest['missing'].append({'kind': kind, 'route': route, 'viewport': viewport,
                                        'task_id': task_id, 'reason': 'Actual permitted evidence file unavailable'})
            return None

    def report(name, kind, value):
        file = destination / (name + '.json')
        file.write_text(json.dumps(value, ensure_ascii=False, indent=2, default=str), encoding='utf-8')
        # Generated reports are created by this collector, not read from an arbitrary path.
        roots.append(destination)
        item = collect(file, kind)
        file.unlink()
        return item

    report('source', 'source_inventory', {'source_inventory': research.get('source_inventory'),
                                          'fact_sources': research.get('fact_sources'),
                                          'company_facts': research.get('company_facts')})
    copy = {route: BeautifulSoup(raw, 'html.parser').get_text(' ', strip=True) for route, raw in pages.items()}
    report('copy', 'copy_inventory', copy)
    report('browser', 'browser_report', qa.get('browser') or {})
    report('media', 'media_decisions', research.get('media_purpose_plan') or [])
    report('journeys', 'journey_report', {'plan': research.get('business_task_plan') or [],
        'task_outcomes': qa.get('journey_results') or [],
        'note': 'Missing actual journey captures remain untested; DOM links do not prove completion.'})
    report('prior-comparison', 'prior_client_comparison', qa.get('originality') or {})

    browser = qa.get('browser') or {}
    page_reports = browser.get('pages') or {'index.html': browser}
    for route in pages:
        captures = (page_reports.get(route) or {}).get('screenshots') or {}
        for viewport in ('desktop', 'mobile'):
            collect(captures.get(viewport), 'new_screenshot', route=route, viewport=viewport)
    original = research.get('original_screenshots') or {}
    captures = original.get('screenshots') or original
    if (research.get('source_inventory') or {}).get('pages'):
        for viewport in ('desktop', 'mobile'):
            collect(captures.get(viewport), 'original_screenshot', viewport=viewport)

    # Per-source-page visual evidence includes unlabelled manufacturer marks.
    # Keep distinct source URLs; a homepage capture does not prove a shop logo.
    for row in research.get('source_visual_captures') or []:
        if isinstance(row, dict) and row.get('source_url') in {
                p.get('url') for p in (research.get('source_inventory') or {}).get('pages', [])}:
            collect(row.get('path'), 'source_visual_capture', route=row['source_url'],
                    viewport=str(row.get('viewport') or ''), asset_ids=row.get('asset_ids')
                    if isinstance(row.get('asset_ids'), list) else [])
    report('visual-plan', 'visual_asset_plan', research.get('visual_asset_plan') or [])

    for route, raw in pages.items():
        for image in BeautifulSoup(raw, 'html.parser').select('main img[src]'):
            parsed = urlsplit(urljoin('https://preview.invalid/' + route, image['src']))
            if parsed.netloc != 'preview.invalid':
                manifest['missing'].append({'kind': 'media_asset', 'route': route,
                    'reason': 'Remote or inline media not captured as owner-controlled image bytes'})
                continue
            collect(root / unquote(parsed.path.lstrip('/')), 'media_asset', route=route)
    for row in qa.get('journey_captures') or []:
        if isinstance(row, dict):
            collect(row.get('path'), 'journey_capture', task_id=str(row.get('task_id') or ''))
    # Actual private commerce captures, never the generated QA JSON report alone.
    commerce_record = (company.get('delivery') or {}).get('commerce_runtime') or {}
    if commerce_record.get('transaction_capture_path'):
        collect(commerce_record['transaction_capture_path'], 'commerce_backend_trace')
    for row in commerce_record.get('tests', []):
        if isinstance(row, dict):
            for file in row.get('capture_paths') or []:
                collect(file, 'commerce_capture', task_id=str(row.get('case') or ''),
                        viewport=str(row.get('viewport') or ''))
    for row in qa.get('prior_client_captures') or []:
        if isinstance(row, dict):
            collect(row.get('path'), 'prior_client_screenshot', route=str(row.get('client') or ''))
    if not any(i['kind'] == 'prior_client_screenshot' for i in manifest['items']):
        manifest['missing'].append({'kind': 'prior_client_screenshot',
                                    'reason': 'Actual comparison capture from another client is missing'})
    task_captures = {i['task_id'] for i in manifest['items'] if i['kind'] == 'journey_capture'}
    for task in research.get('business_task_plan') or []:
        if task.get('task_id') not in task_captures:
            manifest['missing'].append({'kind': 'journey_capture', 'task_id': task.get('task_id'),
                                        'reason': 'Actual visitor task execution has not been captured'})

    if company.get('concept_previews'):
        try:
            path, concepts = load_verified_set(company['concept_previews'], research, allowed_root=root)
            roots.append(path.parent)
            for entry in concepts['entries']:
                for view in entry['views']:
                    collect(path.parent / view['path'], 'concept_screenshot',
                            route=entry['id'] + ':' + view['route'], viewport=view['viewport'])
        except (OSError, RuntimeError, ValueError, KeyError):
            manifest['missing'].append({'kind': 'concept_screenshot', 'reason': 'Concept set unavailable or changed'})
    manifest['bundle_sha256'] = digest(manifest)
    file = destination / 'manifest.json'
    file.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    _write_review_index(destination, manifest)
    return {'manifest_path': str(file), 'bundle_sha256': manifest['bundle_sha256'],
            'index_path': str(destination / 'index.html'), 'missing_count': len(manifest['missing'])}


def verify_review_bundle(reference, *, allowed_root, artifact_digest, contract_digest):
    path = Path(reference.get('manifest_path') or '').resolve()
    if not path.is_relative_to(Path(allowed_root).resolve()) or not path.is_file():
        raise RuntimeError('Review bundle is outside the private project output or missing')
    manifest = json.loads(path.read_text(encoding='utf-8'))
    if (manifest.get('protocol') != 'review-bundle-v1'
        or manifest.get('bundle_sha256') != reference.get('bundle_sha256')
        or manifest.get('bundle_sha256') != digest({k: v for k, v in manifest.items() if k != 'bundle_sha256'})
        or manifest.get('artifact_sha256') != artifact_digest
        or manifest.get('contract_sha256') != contract_digest):
        raise RuntimeError('Review bundle changed or belongs to another source, plan or build')
    for item in manifest.get('items') or []:
        file = (path.parent / item['path']).resolve()
        if not file.is_relative_to(path.parent) or not file.is_file() or file_hash(file) != item['sha256']:
            raise RuntimeError('Referenced review evidence bytes are missing or changed')
    return manifest


def domain_evidence_complete(bundle, record, domain, *, routes, tasks, source_exists):
    """A URL or a checkbox is not evidence; resolve concrete bundled file ids."""
    if not isinstance(bundle, dict) or not isinstance(record.get('evidence_ids'), list):
        return False
    indexed = {item['id']: item for item in bundle.get('items') or []}
    ids = record['evidence_ids']
    if not ids or any(not isinstance(i, str) or i not in indexed for i in ids):
        return False
    selected = [indexed[i] for i in ids]
    kinds = {i['kind'] for i in selected}
    needed = {'technical': {'browser_report'}, 'content': {'source_inventory', 'copy_inventory'},
              'visual': {'new_screenshot', 'media_decisions', 'prior_client_comparison'},
              'commercial': {'journey_report'}}[domain]
    if not needed <= kinds:
        return False
    if domain == 'visual':
        views = {(i['route'], i['viewport']) for i in selected if i['kind'] == 'new_screenshot'}
        if not {(route, vp) for route in routes for vp in ('desktop', 'mobile')} <= views:
            return False
        if source_exists and 'original_screenshot' not in kinds:
            return False
        if 'prior_client_screenshot' not in kinds:
            return False
    if domain == 'commercial':
        captures = {i['task_id'] for i in selected if i['kind'] == 'journey_capture'}
        if not set(tasks) <= captures:
            return False
    return True


def _write_review_index(destination, manifest):
    cards = []
    for item in manifest['items']:
        title = html.escape(' · '.join(str(item.get(k) or '') for k in ('kind', 'route', 'viewport')))
        url = html.escape(item['path'], quote=True)
        content = '<img loading="lazy" src="' + url + '">' if item['path'].endswith(('.png', '.jpg', '.jpeg', '.webp')) else '<a href="' + url + '">Avaa aineisto</a>'
        cards.append('<article><h2>' + title + '</h2><small>' + item['id'] + '</small>' + content + '</article>')
    missing = ''.join('<li>' + html.escape(str(i)) + '</li>' for i in manifest['missing'])
    (destination / 'index.html').write_text('<!doctype html><html lang="fi"><meta charset="utf-8">'
        '<meta name="robots" content="noindex"><meta name="viewport" content="width=device-width,initial-scale=1">'
        '<title>Sivuston arviointiaineisto</title><style>body{font:16px Arial;margin:24px;background:#f5f5f2;color:#222}'
        'main{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:24px}article{min-width:0;background:white;padding:16px}'
        'img{display:block;max-width:100%;height:auto;margin-top:12px}h2{font-size:18px}small{overflow-wrap:anywhere}'
        '@media(max-width:760px){main{grid-template-columns:1fr}}</style><h1>Sivuston arviointiaineisto</h1>'
        '<p>Sisäinen tarkastelu. Kerätty aineisto ei ole riippumaton hyväksyntä.</p><h2>Avoimet puutteet</h2><ul>'
        + missing + '</ul><main>' + ''.join(cards) + '</main></html>', encoding='utf-8')


def current_review_bundle(company, pages, *, artifact_digest=None):
    reference = company.get('review_bundle') or {}
    path = (company.get('build') or {}).get('output_path')
    if not reference or not path:
        return None
    root = Path(path).resolve().parent
    # Never bind an old on-disk site's proof to newly generated in-memory HTML.
    for route, body in pages.items():
        file = (root / route).resolve()
        if not file.is_relative_to(root) or not file.is_file() or file.read_text(encoding='utf-8') != body:
            raise RuntimeError('Review bundle does not describe the current HTML pages')
    actual = site_sha256(root, list(pages))
    if artifact_digest and actual != artifact_digest:
        raise RuntimeError('Current package differs from the audited package')
    return verify_review_bundle(reference, allowed_root=root, artifact_digest=actual,
        contract_digest=service_brief(company.get('research') or {})['contract_sha256'])

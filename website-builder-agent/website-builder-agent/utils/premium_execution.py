"""Exact-build premium execution gates; no browser, provider or invented approval.

Recorded observations require real capture bytes. Integrity cannot certify their
truth: a separate reviewer must actually inspect the website and source assets.
"""
import math
import re
import struct
from datetime import datetime, timezone
from hashlib import sha256
from pathlib import Path
from bs4 import BeautifulSoup
from soupsieve import SelectorSyntaxError

PROTOCOL = 'premium-execution-v1'
CHECKS = {
    'galleries': ('first_view', 'last_row_balance', 'crop_integrity', 'keyboard_enlarge', 'focus_return'),
    'images': ('sharpness', 'crop_integrity'),
    'case_studies': ('source_context', 'work_explained', 'result_explained'),
    'motion': ('material_quality', 'label_readability', 'input_response', 'native_scroll', 'reduced_motion'),
}


def balanced_gallery_rows(count, columns):
    """A layout recipe, not evidence that its browser rendering is attractive.

    With >2 columns, borrow from the preceding full row to avoid 3+1 or
    3+3+1. With two columns and odd counts use one deliberately full-width
    opening image; do not strand a final image in the rightmost column.
    """
    if type(count) is not int or type(columns) is not int or count < 0 or not 1 <= columns <= 8:
        raise ValueError('Non-negative count and 1–8 columns required')
    sizes = [columns] * (count // columns)
    if count % columns: sizes.append(count % columns)
    if len(sizes) > 1 and sizes[-1] == 1:
        if columns == 2: sizes = [1] + [2] * (count // 2)
        elif columns > 2: sizes[-2:] = [columns - 1, 2]
    rows, offset = [], 0
    for size in sizes:
        rows.append(list(range(offset, offset + size))); offset += size
    return rows


def validate_execution_plan(research):
    plan = research.get('premium_execution_plan')
    if not isinstance(plan, dict) or plan.get('protocol') != PROTOCOL:
        raise RuntimeError('Missing premium-execution-v1 plan before Builder')
    routes = {p.get('path') for p in (research.get('site_architecture') or {}).get('pages', [])}
    for kind in CHECKS:
        rows = plan.get(kind)
        if not isinstance(rows, list) or any(not isinstance(r, dict) for r in rows):
            raise RuntimeError('Explicit premium plan list required: ' + kind)
        ids = [r.get('id') for r in rows]
        if any(not isinstance(i, str) or not i.strip() for i in ids) or len(set(ids)) != len(ids):
            raise RuntimeError('Unique premium scope IDs required: ' + kind)
        for row in rows:
            if row.get('route') not in routes or not isinstance(row.get('selector'), str) or not row['selector'].strip():
                raise RuntimeError('Premium scope needs an actual planned route and selector')
            fields = {'galleries': ('last_row_strategy', 'responsive_strategy'),
                      'images': ('source_src', 'display_strategy'),
                      'case_studies': (), 'motion': ('purpose', 'material_strategy')}[kind]
            if any(not isinstance(row.get(k), str) or not row[k].strip() for k in fields):
                raise RuntimeError('Premium scope missing implementation decisions: ' + kind)
            if kind in ('galleries', 'motion'):
                states = row.get('states')
                if (not isinstance(states, list) or not states
                        or any(not isinstance(s, dict) or not isinstance(s.get('id'), str) or not s['id'].strip() for s in states)
                        or len({s['id'] for s in states}) != len(states)):
                    raise RuntimeError('Every gallery group and motion state needs a unique explicit state')
                if kind == 'galleries' and any(type(s.get('expected_count')) is not int or s['expected_count'] <= 0 for s in states):
                    raise RuntimeError('Gallery states need verified positive image counts')
            if kind == 'case_studies' and (not isinstance(row.get('facts'), dict) or not isinstance(row.get('missing_information'), list)):
                raise RuntimeError('Case study needs sourced facts and explicit missing-information list')
    return plan


def _read(company, item, suffixes, limit=30 * 1024 * 1024):
    try:
        root = Path(company['review_bundle']['manifest_path']).resolve().parent
        rel = Path(item['path']); path = root / rel
        if (rel.is_absolute() or path.is_symlink() or not path.resolve().is_relative_to(root)
                or path.suffix.lower() not in suffixes or not path.is_file() or not 0 < path.stat().st_size <= limit): return None
        raw = path.read_bytes()
        return raw if sha256(raw).hexdigest() == item.get('sha256') else None
    except (OSError, ValueError, TypeError, KeyError): return None


def image_dimensions(raw):
    """Read dimensions from PNG/JPEG/WebP headers, without network or upscaling."""
    if not raw: return None
    if raw.startswith(b'\x89PNG\r\n\x1a\n') and len(raw) >= 24 and raw[12:16] == b'IHDR':
        return struct.unpack('>II', raw[16:24])
    if raw.startswith(b'RIFF') and raw[8:12] == b'WEBP':
        if raw[12:16] == b'VP8X' and len(raw) >= 30:
            return 1 + int.from_bytes(raw[24:27], 'little'), 1 + int.from_bytes(raw[27:30], 'little')
        if raw[12:16] == b'VP8L' and len(raw) >= 25 and raw[20] == 0x2f:
            bits = int.from_bytes(raw[21:25], 'little'); return (bits & 0x3fff) + 1, ((bits >> 14) & 0x3fff) + 1
        if raw[12:16] == b'VP8 ' and len(raw) >= 30 and raw[23:26] == b'\x9d\x01\x2a':
            w, h = struct.unpack('<HH', raw[26:30]); return w & 0x3fff, h & 0x3fff
    if raw.startswith(b'\xff\xd8'):
        pos = 2
        while pos + 3 < len(raw):
            if raw[pos] != 0xff: return None
            while pos < len(raw) and raw[pos] == 0xff: pos += 1
            if pos >= len(raw): return None
            marker = raw[pos]; pos += 1
            if marker in (0xd9, 0xda): return None
            if marker in (0x01, *range(0xd0, 0xd9)): continue
            if pos + 2 > len(raw): return None
            length = int.from_bytes(raw[pos:pos+2], 'big')
            if length < 2 or pos + length > len(raw): return None
            if marker in (0xc0, 0xc1, 0xc2, 0xc3, 0xc5, 0xc6, 0xc7, 0xc9, 0xca, 0xcb, 0xcd, 0xce, 0xcf) and length >= 7:
                h, w = struct.unpack('>HH', raw[pos+3:pos+7]); return w, h
            pos += length
    return None


def _positive(value):
    return type(value) in (int, float) and math.isfinite(value) and value > 0


def audit_execution(pages, research, company, *, artifact_digest=None, contract_digest=None, review_bundle=None, now=None):
    block, pending = [], []
    if research.get('premium_execution_protocol') != 'v1':
        return {'blocking': [], 'pending': ['Premium execution plan/evidence not collected'], 'ready': False}
    try: plan = validate_execution_plan(research)
    except RuntimeError as e: return {'blocking': [str(e)], 'pending': [], 'ready': False}
    soups = {route: BeautifulSoup(raw, 'html.parser') for route, raw in pages.items()}
    scopes = []
    observed_media = {str(i.get('src')) for p in (research.get('source_inventory') or {}).get('pages', [])
                      for i in (p.get('images') or []) + (p.get('source_identity') or {}).get('original_content_photos', [])
                      if isinstance(i, dict) and i.get('src')}
    image_nodes, gallery_nodes = set(), set()
    sources = {p.get('url'): ' '.join(str(p.get('text') or p.get('visible_text') or '').split())
               for p in (research.get('source_inventory') or {}).get('pages', [])}
    for kind in CHECKS:
        for scope in plan[kind]:
            route = scope['route']; soup = soups.get(route)
            try: nodes = soup.select(scope['selector']) if soup else []
            except (ValueError, TypeError, SelectorSyntaxError): nodes = []
            if len(nodes) != 1:
                block.append(f'{kind}:{scope["id"]}: actual rendered selector missing/ambiguous'); continue
            node = nodes[0]
            if kind == 'images':
                if node.name != 'img' or not node.get('src'):
                    block.append('Image execution scope must identify an actual img'); continue
                if scope['source_src'] not in observed_media:
                    block.append('Image execution source not observed: ' + scope['id'])
                image_nodes.add((route, id(node)))
            if kind == 'galleries': gallery_nodes.add((route, id(node)))
            if kind == 'case_studies':
                for name in ('context', 'work', 'result'):
                    fact = scope['facts'].get(name) or {}
                    if not fact:
                        pending.append(f'case_studies:{scope["id"]}: source-backed {name} needed; do not invent it'); continue
                    if (not isinstance(fact, dict) or not isinstance(fact.get('source_text'), str) or not fact['source_text'].strip()
                            or ' '.join(fact['source_text'].split()) not in sources.get(fact.get('source_url'), '')
                            or not isinstance(fact.get('rendered_text'), str) or not fact['rendered_text'].strip()
                            or ' '.join(fact['rendered_text'].split()) not in node.get_text(' ', strip=True)):
                        block.append(f'case_studies:{scope["id"]}: unsupported or missing {name}')
                if scope['missing_information']: pending.append('Case study intake gaps remain open: ' + scope['id'])
            states = scope['states'] if kind in ('galleries', 'motion') else [{'id': 'default'}]
            scopes.extend((kind, scope, state, node) for state in states)
    for route, soup in soups.items():
        for node in soup.select('main img[src]'):
            if (route, id(node)) not in image_nodes: block.append('Image display size unplanned: ' + route + ':' + node['src'])
        for node in soup.select('[data-gallery],.gallery-grid,.photo-gallery'):
            if (route, id(node)) not in gallery_nodes: block.append('Gallery group/last-row plan missing: ' + route)
    if any(g.get('purpose') == 'portfolio' for g in plan['galleries']) and not plan['case_studies']:
        pending.append('Portfolio needs a selected source-backed case study; a photo count is insufficient')
    record = (company.get('delivery') or {}).get('premium_execution') or {}
    record = record if isinstance(record, dict) else {}
    bundle = review_bundle or {}
    bound = bool(artifact_digest and contract_digest and record.get('artifact_sha256') == artifact_digest
                 and record.get('contract_sha256') == contract_digest
                 and bundle.get('artifact_sha256') == artifact_digest and bundle.get('contract_sha256') == contract_digest
                 and record.get('deployment_reference') and record['deployment_reference'] == (company.get('delivery') or {}).get('deployment_reference')
                 and record.get('independent_of_builder') is True and record.get('reviewer_id'))
    try:
        tested = datetime.fromisoformat(record['checked_at'].replace('Z', '+00:00'))
        deployed = datetime.fromisoformat(company['delivery']['deployed_at'].replace('Z', '+00:00'))
        age = (now or datetime.now(timezone.utc)) - tested
        bound = bound and bool(tested.tzinfo and deployed.tzinfo and tested >= deployed and 0 <= age.total_seconds() <= 14*86400)
    except (KeyError, ValueError, TypeError, AttributeError): bound = False
    if not bound:
        pending.append('Exact-deployment independent premium observations/capture bundle missing or stale')
        return {'blocking': block, 'pending': pending, 'ready': False}
    observations = record.get('observations') or []
    observations = observations if isinstance(observations, list) else []
    items = bundle.get('items') or []
    for kind, scope, state, node in scopes:
        for view in ('desktop', 'mobile'):
            key = f'{kind}:{scope["id"]}:{state["id"]}:{view}'
            rows = [r for r in observations if isinstance(r, dict) and
                    (r.get('kind'), r.get('scope_id'), r.get('state'), r.get('viewport')) == (kind, scope['id'], state['id'], view)]
            if len(rows) != 1:
                pending.append(key + ': observation missing/duplicated'); continue
            row = rows[0]
            captures = [i for i in items if isinstance(i, dict) and i.get('kind') == 'premium_capture'
                        and i.get('task_id') == kind + ':' + scope['id'] and i.get('route') == scope['route']
                        and i.get('viewport') == view and i.get('state') == state['id']
                        and _read(company, i, {'.png', '.jpg', '.jpeg', '.webp', '.webm'})]
            if not captures: pending.append(key + ': actual state/viewport screenshot or video missing')
            for name in CHECKS[kind]:
                checks = row.get('checks') if isinstance(row.get('checks'), dict) else {}
                check = checks.get(name) or {}
                check = check if isinstance(check, dict) else {}
                if check.get('result') == 'fail': block.append(key + ': observed ' + name + ' failure')
                elif check.get('result') != 'pass' or not isinstance(check.get('observation'), str) or not check['observation'].strip(): pending.append(key + ': ' + name + ' unverified')
            if kind == 'galleries':
                layout = row.get('layout') if isinstance(row.get('layout'), dict) else {}
                rects = layout.get('items') or []
                valid = (_positive(layout.get('container_width')) and isinstance(rects, list)
                         and len(rects) == state['expected_count'] and all(isinstance(r, dict) and
                         type(r.get('x')) in (int,float) and math.isfinite(r['x']) and
                         type(r.get('y')) in (int,float) and math.isfinite(r['y']) and
                         _positive(r.get('width')) and _positive(r.get('height')) for r in rects))
                if not valid: pending.append(key + ': complete measured gallery geometry required')
                elif len(rects) > 1:
                    bottom = max(r['y'] for r in rects); last = [r for r in rects if abs(r['y']-bottom) <= 2]
                    if len(last) == 1 and last[0]['x'] > layout['container_width']*.4 and last[0]['width'] < layout['container_width']*.6:
                        block.append(key + ': isolated final image leaves a large empty left area')
            if kind == 'images':
                assets = [i for i in items if isinstance(i, dict) and i.get('kind') == 'media_asset'
                          and i.get('route') == scope['route'] and i.get('asset_src') == node.get('src')]
                dimensions = next((d for i in assets if (d := image_dimensions(_read(company, i, {'.png','.jpg','.jpeg','.webp'})))), None)
                display = row.get('display') if isinstance(row.get('display'), dict) else {}
                if not dimensions or not all(_positive(display.get(k)) for k in ('width','height','dpr')):
                    pending.append(key + ': actual media bytes and measured display dimensions/DPR required')
                elif dimensions[0] < display['width']*display['dpr'] or dimensions[1] < display['height']*display['dpr']:
                    block.append(key + ': source pixels insufficient for measured display size')
    return {'blocking': block, 'pending': pending, 'ready': not block and not pending,
            'note': 'Integrity and recorded checks are not proof of truth, visual taste or physical-device performance.'}

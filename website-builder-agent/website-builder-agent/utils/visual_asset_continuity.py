"""Source visual inventory and all-placement acceptance, without OCR or paid calls.

Inventory every candidate, including unlabelled images, inline SVG and inline
backgrounds. Classification is an observation, never inferred from alt/filename.
DOM presence is not a visual review or a licence. Verified review-bundle bytes
and independent source/new observations remain mandatory for acceptance.
"""
from __future__ import annotations
import hashlib
import json
import re
from pathlib import Path
from urllib.parse import urljoin, urlsplit
from bs4 import BeautifulSoup
from soupsieve import SelectorSyntaxError
from utils.content_parity import source_inventory_sha256
from utils.premium_quality_gate import site_digest

PROTOCOL = 'visual-assets-v1'
ROLES = {'brand_mark', 'photo', 'information_graphic', 'decorative'}
POLICY = """
VISUAL INFORMATION CONTINUITY: inspect every source candidate, even a blank-alt
image, SVG, manufacturer mark, certificate or background. Do not use text-only
extraction to declare the brand complete. Return visual_asset_plan entries for
ALL manifest ids. Each entry: asset_id, role (brand_mark/photo/information_graphic/
decorative), observed_subject, visible_information (list), supported_uses (list),
not_depicted (list), destinations (list). Information graphics may instead use text_destinations (route, selector, information
list copying every observed fact) when that is clearer; all facts must survive.
Brand marks need a name and at least
one real image placement. A word in body copy never replaces logo artwork.
Each destination needs route, selector, src, purpose (in supported_uses and not
in not_depicted), expected_alt and crop_mode (contain/cover/natural). All real
content images, not merely the first hero image, need an observed assignment.
Brand marks require contain; keep all lettering intact. Choose photo crops per
placement and desktop/mobile, preserving faces, products and relevant details.
Do not relabel repair work as a retail assortment. If a subject is unknown,
leave it unresolved; do not invent an observation. Decorative classification
also needs actual inspection, not an empty alt attribute.
Plans are not independent visual approval. Review all source candidates and
all output placements with source/new capture evidence, including whitespace
rhythm, repeated CTAs, industry character and native/reduced-motion behavior.
No passing mean or checkbox can erase a lost visual fact or unverified use.
"""


def _hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def _text(value):
    return value.strip() if isinstance(value, str) else ''


def canonical(value, base=''):
    value = _text(value)
    if not value or value.startswith(('data:', 'blob:', 'javascript:', '#')):
        return ''
    value = urljoin(base, value)
    try:
        p = urlsplit(value)
    except ValueError:
        return ''
    if p.scheme not in ('http', 'https') or not p.hostname:
        return value if not p.scheme and value else ''
    if p.scheme == 'https' and p.hostname == 'static.wixstatic.com':
        m = re.fullmatch(r'/media/([A-Za-z0-9_~.%-]+)(?:/v1/(?:fill|fit|crop)/[^?#]+)?', p.path)
        if m:
            return 'https://static.wixstatic.com/media/' + m[1]
    return value


def extract_visual_candidates(html, source_url=''):
    """No semantic guessing or silent 70-image truncation; no network access."""
    soup = BeautifulSoup(html, 'html.parser')
    rows = {}
    def add(src, kind, node, ordinal):
        identity = canonical(src, source_url) if kind != 'inline_svg' else 'inline-svg:' + _hash(src)
        if not identity:
            return
        key = _hash([kind, identity])[:24]
        row = rows.setdefault(key, {'id': key, 'source_url': source_url,
            'src': identity, 'kind': kind, 'occurrences': [], 'classification': 'unresolved'})
        row['occurrences'].append({'element': node.name, 'index': ordinal,
            'alt_hint': str(node.get('alt') or node.get('aria-label') or ''),
            'nearby_text_hint': node.parent.get_text(' ', strip=True)[:250] if node.parent else ''})
    for index, node in enumerate(soup.find_all(['img', 'svg'])):
        if node.name == 'svg':
            add(str(node), 'inline_svg', node, index)
            continue
        for key in ('data-src', 'data-lazy-src', 'data-original', 'data-image', 'src', 'data-srcset', 'srcset'):
            src = str(node.get(key) or '')
            if key.endswith('srcset'):
                src = src.split(',')[0].strip().split(' ')[0]
            if canonical(src, source_url):
                add(src, 'image', node, index)
                break
    for index, node in enumerate(soup.select('[style]')):
        for src in re.findall(r'url\(\s*[\"\']?([^\"\')]+)', str(node.get('style') or ''), re.I):
            add(src.strip(), 'background', node, index)
    return list(rows.values())


def visual_candidates(research):
    # Classify identical artwork once; retain every page where it appeared.
    # Repeated header logos must not consume the entire planning budget.
    unique = {}
    for page in (research.get('source_inventory') or {}).get('pages', []):
        if not isinstance(page, dict):
            continue
        for asset in (page.get('source_identity') or {}).get('visual_assets', []):
            if not isinstance(asset, dict):
                continue
            key = asset.get('id')
            if not isinstance(key, str):
                return [asset]  # Validation reports malformed source data.
            row = unique.setdefault(key, {**asset, 'source_urls': []})
            if asset.get('source_url') not in row['source_urls']:
                row['source_urls'].append(asset.get('source_url'))
    return list(unique.values())



def source_visual_image_inputs(research, profile, *, allowed_root):
    """Supply actual target pixels to Research before any model/search credits.

    These captures aid planning; they do not create independent approvals.
    Missing/changed/outside-root files cannot turn into filename-only analysis.
    """
    root = Path(allowed_root).resolve()
    images, labels, covered = [], [], set()
    expected = {p.get('url') for p in (research.get('source_inventory') or {}).get('pages', [])}
    for row in profile.get('visual_captures') or []:
        if not isinstance(row, dict) or row.get('source_url') not in expected:
            continue
        try:
            original = Path(row.get('path') or '')
            file = original.resolve()
            if (original.is_symlink() or not file.is_relative_to(root) or not file.is_file()
                    or file.suffix.lower() not in ('.png', '.jpg', '.jpeg', '.webp')
                    or not 0 < file.stat().st_size <= 30 * 1024 * 1024):
                continue
            data = file.read_bytes()
            magic = data.startswith((b'\x89PNG\r\n\x1a\n', b'\xff\xd8\xff')) or (data.startswith(b'RIFF') and data[8:12] == b'WEBP')
            if not magic or hashlib.sha256(data).hexdigest() != row.get('sha256'):
                continue
        except (OSError, ValueError, TypeError):
            continue
        images.append(str(file)); covered.add(row['source_url'])
        labels.append({'source_url': row['source_url'], 'capture_sha256': row['sha256']})
    if visual_candidates(research) and (not profile.get('visual_capture_complete') or not expected <= covered):
        raise RuntimeError('Original visual candidates need actual source page captures before model/search credits; no classification from alt text alone.')
    return images, labels


def enabled(research):
    return research.get('visual_inventory_protocol') == PROTOCOL or bool(visual_candidates(research))


def visual_plan_errors(research):
    if not enabled(research):
        return []
    candidates = visual_candidates(research)
    plan = research.get('visual_asset_plan')
    if not isinstance(plan, list) or any(not isinstance(row, dict) for row in plan):
        return ['Every source visual candidate needs a classified visual_asset_plan before Builder']
    if any(not _text(r.get('id')) or not _text(r.get('src')) or not _text(r.get('source_url')) for r in candidates):
        return ['Invalid source visual candidate; re-inspect source inventory']
    expected = {r['id'] for r in candidates}
    ids = [r.get('asset_id') for r in plan]
    if any(not isinstance(i, str) for i in ids) or len(ids) != len(set(ids)) or set(ids) != expected:
        return ['Visual plan must classify every source candidate exactly once, including unlabelled artwork']
    routes = {p.get('path') for p in (research.get('site_architecture') or {}).get('pages', [])}
    errors = []
    for row in plan:
        ident = str(row.get('asset_id'))
        if not isinstance(row.get('role'), str) or row.get('role') not in ROLES or not _text(row.get('observed_subject')):
            errors.append(ident + ': visual subject/role is unresolved')
        invalid_lists = False
        for key in ('visible_information', 'supported_uses', 'not_depicted'):
            if not isinstance(row.get(key), list) or any(not _text(s) for s in row[key]):
                errors.append(ident + ': explicit ' + key + ' list required')
                invalid_lists = True
        if invalid_lists:
            continue
        uses = row.get('destinations')
        if not isinstance(uses, list) or any(not isinstance(u, dict) for u in uses):
            errors.append(ident + ': explicit destinations required'); continue
        text_uses = row.get('text_destinations', [])
        if not isinstance(text_uses, list) or any(not isinstance(u, dict) for u in text_uses):
            errors.append(ident + ': invalid text destinations'); text_uses = []
        if row.get('role') == 'brand_mark' and not uses:
            errors.append(ident + ': source artwork/information cannot silently disappear')
        if row.get('role') == 'brand_mark' and not _text(row.get('name')):
            errors.append(ident + ': original brand name required')
        if row.get('role') == 'information_graphic' and not uses and not text_uses:
            errors.append(ident + ': source visual information cannot disappear')
        if not uses and row.get('visible_information'):
            preserved = [fact for u in text_uses if isinstance(u.get('information'), list) for fact in u['information'] if isinstance(fact, str)]
            if not set(row['visible_information']) <= set(preserved):
                errors.append(ident + ': image-only source facts need explicit text destinations')
        for use in text_uses:
            if (use.get('route') not in routes or not _text(use.get('selector'))
                    or not isinstance(use.get('information'), list) or not use['information']
                    or any(not _text(v) for v in use['information'])):
                errors.append(ident + ': invalid information-to-text mapping')
        for use in uses:
            if use.get('route') not in routes or any(not _text(use.get(k)) for k in ('selector', 'src', 'purpose')):
                errors.append(ident + ': invalid visual placement')
            if not isinstance(use.get('expected_alt'), str) or (row.get('role') != 'decorative' and not use['expected_alt'].strip()):
                errors.append(ident + ': accurate alternative text required')
            supported, denied = row.get('supported_uses'), row.get('not_depicted')
            if (not isinstance(supported, list) or use.get('purpose') not in supported
                    or isinstance(denied, list) and use.get('purpose') in denied):
                errors.append(ident + ': image subject does not support the intended purpose')
            if use.get('crop_mode') not in ('contain', 'cover', 'natural'):
                errors.append(ident + ': crop strategy missing')
            if row.get('role') == 'brand_mark' and use.get('crop_mode') != 'contain':
                errors.append(ident + ': brand artwork must remain uncropped')
    return errors


def validate_visual_plan(research):
    errors = visual_plan_errors(research)
    if errors:
        raise RuntimeError('Visual source continuity: ' + '; '.join(errors[:8]))


def _source_review_valid(research, plan, candidates, bundle, build, contract):
    record = research.get('visual_source_review')
    if not isinstance(record, dict) or not isinstance(bundle, dict):
        return False
    if (record.get('source_sha256') != source_inventory_sha256(research.get('source_inventory') or {})
            or record.get('plan_sha256') != _hash(plan)
            or record.get('artifact_sha256') != build or record.get('contract_sha256') != contract
            or record.get('independent_of_builder') is not True
            or not _text(record.get('reviewer_id')) or not _text(record.get('checked_at'))
            or record.get('open_issues') != []):
        return False
    rows = record.get('assets')
    if not isinstance(rows, list) or any(not isinstance(r, dict) for r in rows):
        return False
    ids = [r.get('asset_id') for r in rows]
    if any(not isinstance(i, str) for i in ids) or len(ids) != len(set(ids)) or set(ids) != {c['id'] for c in candidates}:
        return False
    items = {i.get('id'): i for i in bundle.get('items', []) if isinstance(i, dict)}
    source_by_id = {c['id']: c for c in candidates}
    for row in rows:
        refs = row.get('evidence_ids')
        if (row.get('classification_matches_pixels') is not True
                or not _text(row.get('observation')) or not isinstance(refs, list) or not refs
                or any(not isinstance(i, str) or i not in items for i in refs)):
            return False
        if not any(items[i].get('kind') == 'source_visual_capture'
                   and items[i].get('route') in source_by_id[row['asset_id']]['source_urls']
                   and row['asset_id'] in items[i].get('asset_ids', []) for i in refs):
            return False
    refs = record.get('evidence_ids')
    if not isinstance(refs, list) or any(not isinstance(i, str) or i not in items for i in refs):
        return False
    urls = {p.get('url') for p in (research.get('source_inventory') or {}).get('pages', [])}
    if not urls <= {items[i].get('route') for i in refs if items[i].get('kind') == 'source_visual_capture'}:
        return False
    # Actual inspection of external CSS/JS-loaded content is explicit. Static
    # candidates alone can never certify that dynamic logos were absent.
    return record.get('dynamic_and_background_content_checked') is True


def _rendered_asset(node):
    if node.name == 'img':
        return canonical(node.get('src', ''))
    if node.name == 'svg':
        return 'inline-svg:' + _hash(str(node))
    urls = re.findall(r'url\(\s*[\"\']?([^\"\')]+)', str(node.get('style') or ''), re.I)
    return canonical(urls[0]) if urls else ''


def audit_visual_continuity(pages, research, *, artifact_digest=None, review_bundle=None, contract_digest=None):
    result = {'blocking': [], 'pending': [], 'placements': [], 'ready': False, 'applicable': enabled(research)}
    if not result['applicable']:
        result['ready'] = True
        return result
    block, pending = result['blocking'], result['pending']
    errors = visual_plan_errors(research)
    if errors:
        block.extend({'kind': 'visual_inventory_incomplete', 'reason': e} for e in errors)
        return result
    candidates = visual_candidates(research)
    candidate_by_id = {c['id']: c for c in candidates}
    plan = research.get('visual_asset_plan') or []
    soups = {route: BeautifulSoup(raw, 'html.parser') for route, raw in pages.items()}
    matched = set()
    for row in plan:
        for use in row['destinations']:
            route, selector = use['route'], use['selector']
            try:
                nodes = soups[route].select(selector)
            except (KeyError, ValueError, TypeError, SelectorSyntaxError):
                # soupsieve selector errors are not consistently ValueError.
                block.append({'kind': 'invalid_visual_selector', 'route': route, 'selector': selector})
                continue
            if len(nodes) != 1 or _rendered_asset(nodes[0]) != (use['src'] if use['src'].startswith('inline-svg:') else canonical(use['src'])):
                block.append({'kind': 'source_visual_placement_missing', 'asset_id': row['asset_id'], 'route': route, 'selector': selector})
                continue
            node = nodes[0]
            if any(p.has_attr('hidden') or p.get('aria-hidden') == 'true' or re.search(
                    r'(?:display\s*:\s*none|visibility\s*:\s*hidden|opacity\s*:\s*0(?:[;\s]|$))',
                    str(p.get('style') or ''), re.I) for p in [node, *node.parents] if getattr(p, 'attrs', None) is not None):
                block.append({'kind': 'hidden_visual_substitute', 'route': route, 'asset_id': row['asset_id']})
            if _text(node.get('alt') if node.name == 'img' else node.get('aria-label')) != use['expected_alt']:
                block.append({'kind': 'image_alt_mismatch', 'route': route, 'selector': selector})
            if row['role'] == 'brand_mark' and re.search(r'object-fit\s*:\s*cover', str(node.get('style') or ''), re.I):
                block.append({'kind': 'cropped_brand_mark', 'route': route, 'selector': selector})
            matched.add((route, id(node)))
            result['placements'].append({'asset_id': row['asset_id'], 'route': route, 'selector': selector,
                'src': use['src'], 'source_src': candidate_by_id[row['asset_id']]['src'],
                'purpose': use['purpose'], 'crop_mode': use['crop_mode']})
    for row in plan:
        for use in row.get('text_destinations', []):
            try:
                nodes = soups[use['route']].select(use['selector'])
            except (KeyError, ValueError, TypeError, SelectorSyntaxError):
                nodes = []
            if (len(nodes) != 1 or nodes[0].has_attr('hidden')
                    or nodes[0].get('aria-hidden') == 'true'
                    or any(fact.casefold() not in nodes[0].get_text(' ', strip=True).casefold()
                           for fact in use['information'])):
                block.append({'kind': 'image_only_information_lost', 'asset_id': row['asset_id'],
                              'route': use['route']})
    for route, soup in soups.items():
        # All content AND partner/footer images, including images after the lead.
        for image in soup.select('img,svg,[style]'):
            if not _rendered_asset(image):
                continue
            if (route, id(image)) not in matched:
                block.append({'kind': 'unplanned_visual_placement', 'route': route, 'src': image.get('src', '')})
    build = artifact_digest or site_digest(pages)
    bundle = review_bundle if isinstance(review_bundle, dict) else {}
    bound = (bundle.get('artifact_sha256') == build and bundle.get('contract_sha256') == contract_digest)
    if not bound or not _source_review_valid(research, plan, candidates, bundle, build, contract_digest):
        pending.append({'kind': 'source_visual_classification_unverified'})
    record = research.get('visual_placement_review')
    if not isinstance(record, dict):
        record = {}
    metadata = (bound and record.get('artifact_sha256') == build
        and record.get('contract_sha256') == contract_digest and record.get('plan_sha256') == _hash(plan)
        and record.get('independent_of_builder') is True and _text(record.get('reviewer_id'))
        and _text(record.get('checked_at')) and record.get('open_issues') == [])
    observations = record.get('placements')
    observations = observations if isinstance(observations, list) else []
    items = {i.get('id'): i for i in bundle.get('items', []) if isinstance(i, dict)}
    keys = []
    for use in result['placements']:
        for viewport in ('desktop', 'mobile'):
            key = (use['asset_id'], use['route'], use['selector'], viewport)
            keys.append(key)
            rows = [o for o in observations if isinstance(o, dict) and tuple(o.get(k) for k in ('asset_id', 'route', 'selector', 'viewport')) == key]
            ok = bool(metadata and len(rows) == 1)
            if ok:
                row = rows[0]; refs = row.get('evidence_ids')
                ok = all(isinstance(row.get(k), dict) and row[k].get('result') == 'pass'
                         and _text(row[k].get('observation')) for k in ('subject_match', 'alt_accuracy', 'crop_integrity', 'visual_information_preserved'))
                ok = bool(ok and isinstance(refs, list) and refs
                    and all(isinstance(i, str) and i in items for i in refs)
                    and any(items[i].get('kind') == 'new_screenshot' and items[i].get('route') == use['route']
                            and items[i].get('viewport') == viewport for i in refs))
            if not ok:
                pending.append({'kind': 'visual_placement_unverified', 'placement': key})
    if len(observations) != len(keys):
        pending.append({'kind': 'visual_placement_review_coverage_mismatch'})
    result['ready'] = not block and not pending
    return result

"""Offline integrity gate for actual PUBLISHED click-through and contact evidence.

Does not browse, call, submit forms or certify the truth of a human observation.
Local preview, goto-only checks and draft emails cannot stand in for live tests.
"""
from datetime import date, datetime
from hashlib import sha256
from pathlib import Path
import re
from urllib.parse import urljoin, urlsplit, urlunsplit


def _text(value):
    return isinstance(value, str) and bool(value.strip())


def _origin(url):
    try:
        p = urlsplit(url)
        if (p.scheme != 'https' or not p.hostname or p.username or p.password
                or p.hostname in ('localhost', '127.0.0.1', '::1')
                or p.hostname.endswith(('.local', '.invalid'))):
            return None
        return p.scheme, p.netloc.lower()
    except (TypeError, ValueError, AttributeError):
        return None


def _url(url):
    try:
        p = urlsplit(url)
        return urlunsplit((p.scheme, p.netloc.lower(), p.path or '/', p.query, p.fragment))
    except (TypeError, ValueError, AttributeError):
        return ''


def _capture(record, capture):
    if not isinstance(capture, dict) or not _text(record.get('evidence_root')):
        return False
    rel = capture.get('path')
    if not _text(rel) or Path(rel).is_absolute():
        return False
    try:
        root = Path(record['evidence_root']).resolve()
        path = (root / rel).resolve()
        return (path.is_relative_to(root) and path.suffix.lower() in ('.png', '.jpg', '.jpeg', '.webp', '.webm')
                and path.is_file() and 0 < path.stat().st_size <= 30 * 1024 * 1024
                and sha256(path.read_bytes()).hexdigest() == capture.get('sha256'))
    except (OSError, ValueError):
        return False


def audit_published_experience(company, *, research=None, expected_site_sha256=None, today=None):
    today = today or date.today()
    research = research if isinstance(research, dict) else company.get('research') or {}
    delivery = company.get('delivery') or {}
    delivery = delivery if isinstance(delivery, dict) else {}
    qa, build = company.get('qa') or {}, company.get('build') or {}
    record = delivery.get('published_experience')
    issues = []
    def issue(kind, reason):
        issues.append({'kind': kind, 'reason': reason})
    if not isinstance(record, dict):
        return {'pass': False, 'navigation_pass': False, 'contact_pass': False, 'public_demo_ready': False,
                'issues': [{'kind': 'navigation', 'reason': 'Published click-through and contact evidence missing.'}]}
    expected = expected_site_sha256 or qa.get('site_sha256')
    if (not isinstance(expected, str) or not re.fullmatch('[a-f0-9]{64}', expected)
            or record.get('site_sha256') != expected
            or record.get('build_version') != build.get('version')
            or not _text(delivery.get('deployment_reference'))
            or record.get('deployment_reference') != delivery.get('deployment_reference')
            or record.get('published_url') != delivery.get('published_url')
            or record.get('verified_by_human') is not True
            or not _text(record.get('reviewer'))):
        issue('navigation', 'Published observations do not match this build, deployment, URL and reviewer.')
    try:
        deployed = datetime.fromisoformat(delivery['deployed_at'].replace('Z', '+00:00'))
        tested = datetime.fromisoformat(record['tested_at'].replace('Z', '+00:00'))
        if (not deployed.tzinfo or not tested.tzinfo or tested < deployed
                or not 0 <= (today - tested.date()).days <= 14):
            raise ValueError('stale or pre-deployment')
    except (KeyError, TypeError, ValueError, AttributeError):
        issue('navigation', 'Tests must be recent and recorded after this deployment.')
    origin = _origin(delivery.get('published_url'))
    routes = [p.get('path') for p in (research.get('site_architecture') or {}).get('pages', []) if isinstance(p, dict)]
    urls = delivery.get('route_urls')
    if (not origin or not routes or any(not _text(r) for r in routes)
            or len(set(routes)) != len(routes) or not isinstance(urls, dict)
            or set(urls) != set(routes) or any(_origin(u) != origin for u in urls.values())
            or len({_url(u) for u in urls.values()}) != len(routes)):
        issue('navigation', 'Published HTTPS route inventory is missing, duplicated or not on the deployed origin.')
        urls = {}
    clicks = record.get('clicks')
    clicks = clicks if isinstance(clicks, list) else []
    covered = set()
    for row in clicks:
        if not isinstance(row, dict):
            issue('navigation', 'Invalid click observation.')
            continue
        route, viewport = row.get('target_route'), row.get('viewport')
        if not isinstance(route, str) or not isinstance(viewport, str):
            issue('navigation', 'Click observation lacks its route or viewport.')
            continue
        target = urls.get(route)
        valid = bool(target and viewport in ('desktop', 'mobile')
                     and row.get('method') == 'click' and row.get('result') == 'pass'
                     and _origin(row.get('source_url')) == origin
                     and _text(row.get('clicked_href'))
                     and _url(urljoin(row['source_url'], row['clicked_href'])) == _url(target)
                     and _url(row.get('observed_url')) == _url(target)
                     and _text(row.get('expected_heading'))
                     and row.get('observed_heading') == row['expected_heading']
                     and row.get('site_errors') == [] and _capture(record, row.get('capture')))
        if valid:
            covered.add((route, viewport))
        else:
            issue('navigation', 'A published click failed, changed the wrong content, or lacks valid evidence.')
    if not {(route, vp) for route in routes for vp in ('desktop', 'mobile')} <= covered:
        issue('navigation', 'Every published route needs a desktop/mobile click, correct URL AND heading, capture and no Site errors.')
    contact = record.get('contact')
    contact = contact if isinstance(contact, dict) else {}
    from utils.service_quality import source_tasks
    tasks = source_tasks(research)
    source_has_form = any(t['kind'].endswith('_form') for t in tasks)
    if source_has_form or contact.get('mode') == 'live_form':
        good = (contact.get('mode') == 'live_form' and contact.get('test_recipient_authorized') is True
                and contact.get('delivery_result') == 'received' and _text(contact.get('receipt_reference'))
                and all(contact.get(k) == 'pass' for k in ('validation_feedback', 'success_feedback', 'error_feedback'))
                and _capture(record, contact.get('capture')))
    elif contact.get('mode') == 'existing_platform':
        good = (any(t['id'] == contact.get('task_id') and t['destination'] == contact.get('destination')
                    for t in tasks) and contact.get('completion_result') == 'pass'
                and _capture(record, contact.get('capture')))
    else:
        facts = research.get('company_facts') or {}
        links = [str(link.get('href') or '') for page in (research.get('source_inventory') or {}).get('pages', [])
                 for link in page.get('links', []) if isinstance(link, dict)]
        needed = []
        if facts.get('email') or any(link.lower().startswith('mailto:') for link in links):
            needed += ['email_link', 'visible_email']
        if facts.get('phone') or any(link.lower().startswith('tel:') for link in links):
            needed += ['phone_link']
        good = (contact.get('mode') == 'source_email_phone' and bool(needed)
                and all(contact.get(k) == 'pass' for k in needed)
                and _capture(record, contact.get('capture')))
    if not good:
        issue('contact', 'Contact needs observed source-appropriate behavior; a draft or unreceived form is not lead delivery.')
    navigation_pass = not any(item['kind'] == 'navigation' for item in issues)
    disclosed_draft = (contact.get('mode') == 'draft_only'
                       and contact.get('draft_disclosure_verified') is True
                       and _capture(record, contact.get('capture')))
    return {'pass': not issues, 'navigation_pass': navigation_pass, 'contact_pass': bool(good),
            'public_demo_ready': navigation_pass and (bool(good) or disclosed_draft),
            'issues': issues, 'note': 'Recorded byte integrity and consistency only; actual live observations are required.'}

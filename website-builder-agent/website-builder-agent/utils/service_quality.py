"""Business tasks and evidence of design decisions, independent of a client demo.

Static checks cannot recognise a photograph's subject or certify good taste.
Unknown decisions stay pending until a reviewer inspects the exact bundle.
"""
from __future__ import annotations
import hashlib
import json
import re
from urllib.parse import urljoin, urlsplit
from pathlib import Path
from bs4 import BeautifulSoup
from utils.content_parity import source_inventory_sha256

DOMAINS = ('technical', 'content', 'visual', 'commercial')
TASK_PATTERNS = (
    ('shopping', r'verkkokau|webshop|webbutik|nätbutik|online.?shop|\bshop\b'),
    ('booking', r'ajanvar|varaa aika|boka tid|boka bord|tidsbokning|bokning|booking|book now|reservation'),
    ('quotation', r'tarjouspy|pyydä tarjous|begär offert|offertförfrågan|be om offert|request.{0,8}quote'),
    ('application', r'ilmoittaudu|hae mukaan|anmäl|register|apply now'),
)
POLICY = '''SERVICE QUALITY CONTRACT — ALL CLIENTS:
Plan actual visitor tasks before layout. Preserve every distinct original
booking, shopping, quotation and application destination, including external
platforms and forms. A mailto draft is not equivalent to a delivered form.
For each route, choose imagery by its observed subject and visitor task;
source ownership, filename and alt text alone do not prove subject relevance.
Keep company_voice_brief with exact source excerpts and company-specific
facts. Avoid generic transferable headlines and third-person source narration.
Compare composition, typography, image strategy and copy rhythm with previous
unrelated clients; brand colour differences alone do not make a unique design.
Keep four separate decisions: technical, content, visual and commercial.
Never turn tests passing into a visual score or an independent approval.
Reviewers inspect source/new screenshots, image-to-task decisions and an actual
visitor walkthrough; missing proof stays pending. Feedback is service-wide by
default; explicitly client-specific preferences stay local. Implementation and
unseen-company validation are separate statuses. Do not claim field validation
from synthetic tests or the same demo revised repeatedly.
'''


def _hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':')).encode()).hexdigest()


def _normal(text):
    return ' '.join(str(text or '').split())


def source_tasks(research):
    """No category deduplication: two branches can have different bookings."""
    result, seen = [], set()
    for page in (research.get('source_inventory') or {}).get('pages', []):
        source = page.get('url', '')
        for link in page.get('links') or []:
            href = urljoin(source, str(link.get('href') or ''))
            if urlsplit(href).scheme not in ('http', 'https'):
                continue
            text = _normal(link.get('text'))
            kind = next((kind for kind, pattern in TASK_PATTERNS
                         if re.search(pattern, text + ' ' + urlsplit(href).path, re.I)), None)
            if kind and (kind, href) not in seen:
                seen.add((kind, href))
                result.append({'id': _hash([kind, href])[:16], 'kind': kind,
                               'source_url': source, 'destination': href, 'label': text})
        for index, form in enumerate(page.get('forms') or []):
            fields = form.get('fields') or []
            # Search, consent and newsletter forms are not inferred to be sales forms.
            has_message = any(f.get('type') == 'textarea' for f in fields)
            has_email = any(f.get('type') == 'email' for f in fields)
            action_hint = str(form.get('action') or '')
            has_date = any(f.get('type') in ('date', 'datetime-local') for f in fields)
            form_kind = ('contact_form' if has_message and has_email else
                         'booking_form' if has_email and has_date else
                         'quotation_form' if has_email and re.search(r'quote|offert|tarjous', action_hint, re.I) else None)
            if form_kind:
                result.append({'id': _hash([source, 'form', index])[:16],
                               'kind': form_kind, 'source_url': source,
                               'destination': urljoin(source, form.get('action') or ''),
                               'label': 'Observed contact form',
                               'method': str(form.get('method') or 'get').lower()})
    return result


def service_brief(research):
    tasks = source_tasks(research)
    routes = [{'route': p.get('path'), 'visitor_task': p.get('user_task'),
               'purpose': p.get('purpose')}
              for p in (research.get('site_architecture') or {}).get('pages', [])]
    lessons_file = Path(__file__).resolve().parents[1] / 'data/service_quality_lessons.json'
    lessons = json.loads(lessons_file.read_text(encoding='utf-8')) if lessons_file.is_file() else []
    payload = {'service_lessons': lessons,
               'source_observation_sha256': _hash({'inventory': research.get('source_inventory') or {},
                                                   'fact_sources': research.get('fact_sources') or []}),
               'source_sha256': source_inventory_sha256(research.get('source_inventory') or {}),
               'tasks': tasks, 'routes': routes,
               'task_plan': research.get('business_task_plan') or [],
               'media_plan': research.get('media_purpose_plan') or [],
               'voice': research.get('company_voice_brief') or {},
               'company_facts': research.get('company_facts') or {}}
    return {**payload, 'contract_sha256': _hash(payload), 'policy': POLICY}


def reset_generated_review_claims(research):
    """A Research model can propose plans, never author independent approvals."""
    research.pop('service_quality_reviews', None)
    research['service_quality_protocol'] = 'v1'
    return research


def validate_service_plan(research):
    """Reject incomplete or invented task plans before a new Builder request.

    Legacy research is still audited on output; newly researched projects use
    v1 and must map every discovered business task before spending on a build.
    """
    tasks = source_tasks(research)
    plans = research.get('business_task_plan')
    if plans is None and research.get('service_quality_protocol') != 'v1':
        return
    if plans is not None and not isinstance(plans, list):
        raise RuntimeError('Service business task plan must be a list')
    if plans is None:
        plans = []
    task_ids = {t['id'] for t in tasks}
    ids = [p.get('task_id') for p in plans if isinstance(p, dict)]
    routes = {p.get('path') for p in (research.get('site_architecture') or {}).get('pages', [])}
    if set(ids) != task_ids or len(ids) != len(set(ids)) or len(ids) != len(plans):
        raise RuntimeError('Service plan must map every observed business task exactly once before Builder')
    for plan in plans:
        if (urlsplit(str(plan.get('destination') or '')).scheme not in ('', 'http', 'https')
            or plan.get('source_route') not in routes or not plan.get('destination')
            or plan.get('completion_mode') not in ('form_submission', 'existing_platform', 'local_flow')):
            raise RuntimeError('Service plan has an invalid route, destination or completion mode')


def _target(pages, source_route, href):
    parsed = urlsplit(urljoin('https://preview.invalid/' + source_route, href))
    route = parsed.path.lstrip('/')
    if not route or route.endswith('/'):
        route += 'index.html'
    if route not in pages and route + '/index.html' in pages:
        route += '/index.html'
    if parsed.netloc != 'preview.invalid' or route not in pages:
        return None
    soup = BeautifulSoup(pages[route], 'html.parser')
    return soup.find(id=parsed.fragment) if parsed.fragment else soup.find('main') or soup


def audit_service_quality(pages, research, *, artifact_digest=None):
    brief = service_brief(research)
    blocking, pending = [], []
    try:
        validate_service_plan(research)
    except RuntimeError as error:
        blocking.append({'kind': 'invalid_business_task_plan', 'reason': str(error)})
    soups = {route: BeautifulSoup(raw, 'html.parser') for route, raw in pages.items()}
    task_ids = {t['id'] for t in brief['tasks']}
    plans = research.get('business_task_plan') or []
    plans = plans if isinstance(plans, list) else []
    mapped = {p.get('task_id'): p for p in plans if isinstance(p, dict)}
    for task in brief['tasks']:
        record = mapped.get(task['id'])
        external = ((urlsplit(task['destination']).hostname or '').lower().removeprefix('www.')
                    != (urlsplit(task['source_url']).hostname or '').lower().removeprefix('www.'))
        if not record:
            if not task['kind'].endswith('_form') and external and task['kind'] != 'shopping':
                if not any(a.get('href') == task['destination']
                           for soup in soups.values() for a in soup.select('a[href]')):
                    blocking.append({'kind': 'lost_business_task', 'task_id': task['id'],
                                     'source': task['destination']})
            pending.append({'kind': 'task_mapping_unreviewed', 'task_id': task['id']})
            continue
        route, destination = record.get('source_route'), record.get('destination')
        if route not in soups or not destination:
            blocking.append({'kind': 'invalid_task_mapping', 'task_id': task['id']})
            continue
        if task['kind'].endswith('_form'):
            form = soups[route].find('form')
            if (record.get('completion_mode') != 'form_submission' or not form
                or (task['kind'] == 'contact_form' and not form.find('textarea'))
                or not form.select_one('input[type="email"]')):
                blocking.append({'kind': 'form_replaced_with_weaker_action', 'task_id': task['id']})
        else:
            links = [a for a in soups[route].select('a[href]') if a.get('href') == destination
                     and (a.get_text(' ', strip=True) or a.get('aria-label'))]
            if not links or (not urlsplit(destination).scheme and _target(pages, route, destination) is None):
                blocking.append({'kind': 'broken_business_task', 'task_id': task['id']})
            if external and task['kind'] != 'shopping' and destination != task['destination']:
                blocking.append({'kind': 'changed_external_task_destination', 'task_id': task['id']})
        if record.get('completion_mode') not in ('form_submission', 'existing_platform', 'local_flow'):
            blocking.append({'kind': 'unknown_completion_mode', 'task_id': task['id']})
    if any(p.get('task_id') not in task_ids for p in plans if isinstance(p, dict)):
        blocking.append({'kind': 'invented_source_task'})

    observed_images = set()
    for page in (research.get('source_inventory') or {}).get('pages', []):
        for p in (page.get('source_identity') or {}).get('original_content_photos', []):
            if isinstance(p, dict) and p.get('src'):
                observed_images.add(p['src'])
        for p in page.get('images') or []:
            if isinstance(p, dict) and p.get('src'):
                observed_images.add(p['src'])
    assignments = research.get('media_purpose_plan') or []
    reviewed_images = []
    for route, soup in soups.items():
        main = soup.find('main')
        lead = main.find('img') if main else None
        if not lead:
            continue
        matches = [p for p in assignments if isinstance(p, dict) and p.get('route') == route
                   and p.get('src') == lead.get('src')]
        if not matches:
            pending.append({'kind': 'lead_image_task_relevance_unreviewed', 'route': route,
                            'src': lead.get('src')})
            continue
        assignment = matches[0]
        source_src = assignment.get('source_src') or assignment.get('src')
        if source_src not in observed_images:
            blocking.append({'kind': 'unobserved_media_source', 'route': route})
        if not all(_normal(assignment.get(k)) for k in ('observed_subject', 'visitor_task', 'rationale')):
            pending.append({'kind': 'media_subject_not_observed', 'route': route})
        reviewed_images.append({'route': route, 'src': lead.get('src'),
                                'subject': assignment.get('observed_subject'),
                                'visitor_task': assignment.get('visitor_task')})

    voice = research.get('company_voice_brief') or {}
    if not isinstance(voice, dict):
        blocking.append({'kind': 'invalid_voice_brief'})
        voice = {}
    sources = {p.get('url'): str(p.get('text') or '')
               for p in (research.get('source_inventory') or {}).get('pages', [])}
    sources.update({p.get('url'): str(p.get('text') or '') for p in research.get('fact_sources') or []})
    excerpts = voice.get('source_excerpts') or []
    if not isinstance(excerpts, list) or any(not isinstance(e, dict) for e in excerpts):
        blocking.append({'kind': 'invalid_voice_excerpts'})
        excerpts = []
    fact_corpus = _normal(' '.join(sources.values()) + ' ' + json.dumps(research.get('company_facts') or {}, ensure_ascii=False)).casefold()
    voice_facts = voice.get('company_specific_facts') or []
    if not isinstance(voice_facts, list) or any(not isinstance(f, str) for f in voice_facts):
        blocking.append({'kind': 'invalid_voice_facts'})
        voice_facts = []
    for fact in voice_facts:
        if not _normal(fact) or _normal(fact).casefold() not in fact_corpus:
            blocking.append({'kind': 'invented_voice_fact'})
    valid_voice = bool(excerpts and voice_facts and isinstance(voice.get('tone'), str) and _normal(voice.get('tone')))
    for excerpt in excerpts:
        quote = _normal(excerpt.get('text'))
        if not quote or quote not in _normal(sources.get(excerpt.get('source_url'), '')):
            blocking.append({'kind': 'invented_voice_source'})
            valid_voice = False
    if not valid_voice:
        pending.append({'kind': 'company_voice_not_source_grounded'})

    # Evidence must inspect the complete bundle, not just unchanged HTML.
    evidence = research.get('service_quality_reviews') or {}
    evidence = evidence if isinstance(evidence, dict) else {}
    reviews = {}
    for domain in DOMAINS:
        record = evidence.get(domain) or {}
        record = record if isinstance(record, dict) else {}
        ok = bool(isinstance(artifact_digest, str) and re.fullmatch('[a-f0-9]{64}', artifact_digest)
                  and record.get('approved') is True
                  and record.get('artifact_sha256') == artifact_digest
                  and record.get('contract_sha256') == brief['contract_sha256']
                  and record.get('independent_of_builder') is True
                  and record.get('reviewer_id') and record.get('evidence_reference')
                  and record.get('checked_at') and record.get('open_issues') == []
                  and isinstance(record.get('routes_reviewed'), list)
                  and all(isinstance(x, str) for x in record['routes_reviewed'])
                  and set(record['routes_reviewed']) == set(pages))
        if domain in ('commercial', 'technical'):
            ok = ok and isinstance(record.get('task_ids_tested'), list)
            ok = ok and all(isinstance(x, str) for x in record['task_ids_tested'])
            ok = ok and set(record['task_ids_tested']) == task_ids
        if domain == 'commercial':
            results = record.get('journey_results') or []
            results = results if isinstance(results, list) else []
            checked = {r.get('task_id') for r in results if isinstance(r, dict)
                       and r.get('result') == 'pass' and r.get('completion_evidence')
                       and r.get('completion_mode') == mapped.get(r.get('task_id'), {}).get('completion_mode')}
            ok = ok and checked == task_ids
        if domain == 'visual':
            ok = ok and record.get('media_decisions_reviewed') == reviewed_images
            ok = ok and bool(record.get('source_new_comparison') and record.get('prior_client_comparison'))
        if domain == 'content':
            ok = ok and valid_voice and record.get('voice_excerpts_reviewed') == excerpts
        reviews[domain] = 'reviewed' if ok else 'pending'
        if not ok:
            pending.append({'kind': 'domain_review_pending', 'domain': domain})
    # A human claim cannot erase a missing plan or invalid source record.
    return {'blocking': blocking, 'pending': pending, 'domains': reviews,
            'client_ready': not blocking and not pending, 'brief': brief,
            'media_decisions': reviewed_images,
            'note': 'No static defect is not a visual approval. Subject relevance and taste require inspection.'}

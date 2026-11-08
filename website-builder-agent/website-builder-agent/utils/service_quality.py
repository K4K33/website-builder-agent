"""Business tasks and evidence of design decisions, independent of a client demo.

Static checks cannot recognise a photograph's subject or certify good taste.
Unknown decisions stay pending until a reviewer inspects the exact bundle.
"""
from __future__ import annotations
import hashlib
import json
import re
from urllib.parse import unquote
from urllib.parse import urljoin, urlsplit
from pathlib import Path
from bs4 import BeautifulSoup
from utils.content_parity import source_inventory_sha256
from utils.master_prompt import MASTER_PROMPT, MASTER_PROMPT_SHA256

DOMAINS = ('technical', 'content', 'visual', 'commercial')
TASK_PATTERNS = (
    ('shopping', r'verkkokau|webshop|webbutik|nätbutik|online.?shop|\bshop\b'),
    ('booking', r'ajanvar|varaa aika|boka tid|boka bord|tidsbokning|bokning|booking|book now|reservation'),
    ('quotation', r'tarjouspy|pyydä tarjous|begär offert|offertförfrågan|be om offert|request.{0,8}quote'),
    ('application', r'ilmoittaudu|hae mukaan|anmäl|register|apply now'),
)
POLICY = MASTER_PROMPT + '\n\n' + '''SERVICE QUALITY CONTRACT — ALL CLIENTS:
Plan the final editable platform before composition; build the customer preview
in that implementation where possible. A separate stripped-down CMS theme is
not delivery parity. Verify every preview route against the editable version,
including text/image edits, mobile layout, actual tasks and rollback.
Group genuine portfolio images into projects with sourced context, detail
views and accurate credits. Never infer client names, materials, results or
project scope from a filename. Unknown context is an intake gap, not copy.
Every subpage must answer a distinct visitor question and add information;
do not expand a homepage paragraph into another hero with the same portrait.
Compare three actual responsive compositions using company assets before
selection; heading, image, CTA and navigation proportions must work together.
Plan contact continuity: a source form link may preserve a demo task but does
not establish a complete redesigned contact flow. Keep genuine external
booking/payment platforms when appropriate; do not fabricate replacements.
Observe cold-cache first load AND transitions, including loading/error states.
After publication, click the actual deployed navigation and primary CTAs;
verify destination URL AND route content. Direct URL opens or local preview
checks cannot certify published client-side navigation. Keep first-pass
failures recorded even after a functional regression is repaired.
Measure before blaming blank frames on image size, fonts, network or framework.
Choose 3D to explain verified structure/details only when genuine source models
or assets support it; a tilted photo is not an interactive product model.
Before building, plan EVERY route's visitor task, composition, needed real
photo subjects, available assets and missing assets. Do not stretch two photos
across unrelated product/venue/team pages or invent replacement photographs.
Record a justified text-led choice where photos would not help the task.
Preserve brand character beyond logo/palette: source type, material, image
language and tone. Inspect readable navigation, body copy, CTA hierarchy and
image crops in actual desktop/mobile views, not only the hero.
Choose purposeful animation/3D or a justified static treatment. Preserve native
scrolling; observe wheel, trackpad, touch, keyboard and reduced-motion behavior.
Record actual device/browser and evidence; CSS inspection cannot prove smoothness.
Visible email addresses must remain selectable even without a configured mail
app. Do not call a mailto click a delivered lead. Test forms through receipt
and honest success/failure feedback, using an authorized test recipient only.
Client handover requires actual CMS text/image/contact edit, save, publish,
mobile recheck and rollback evidence; a theme ZIP is not an editable-site test.
Shared header/footer, phone, email and source hours must be editable through the
customer editor; a developer changing theme HTML does not qualify.
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
Before choosing the final composition, inspect the actual first viewport:
balance brand recognition, service choice, image subject and readable copy.
Do not impose the same oversized heading or split hero on unrelated companies.
Inspect each photo crop at desktop and mobile sizes; consistent boxes alone do
not prove consistent image quality. Missing original working/people photos stay
an intake gap, never a licence to invent a workshop or the owner's portrait.
Report the same nine owner scorecard dimensions for every company. Evidence
gaps remain unscored; fixed weights and the exact mean must not change between
projects. A 9.5 mean never overrides lost functionality or untested CMS editing.
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
    payload = {'master_prompt_sha256': MASTER_PROMPT_SHA256,
               'service_lessons': lessons,
               'route_review_requirements': ROUTE_REVIEW_CHECKS,
               'source_observation_sha256': _hash({'inventory': research.get('source_inventory') or {},
                                                   'fact_sources': research.get('fact_sources') or []}),
               'source_sha256': source_inventory_sha256(research.get('source_inventory') or {}),
               'tasks': tasks, 'routes': routes,
               'task_plan': research.get('business_task_plan') or [],
               'media_plan': research.get('media_purpose_plan') or [],
               'visual_inventory_protocol': research.get('visual_inventory_protocol'),
               'visual_asset_plan': research.get('visual_asset_plan') or [],
               'route_experience_plan': research.get('route_experience_plan') or [],
               'premium_experience_plan': research.get('premium_experience_plan') or {},
               'commerce_plan': research.get('commerce_plan') or {},
               'commerce_inventory': research.get('commerce_inventory') or [],
               'voice': research.get('company_voice_brief') or {},
               'creative_selection': research.get('creative_selection'),
               'review_evidence_protocol': research.get('review_evidence_protocol'),
               'company_facts': research.get('company_facts') or {}}
    return {**payload, 'contract_sha256': _hash(payload), 'policy': POLICY}


def reset_generated_review_claims(research):
    """A Research model can propose plans, never author independent approvals."""
    research.pop('service_quality_reviews', None)
    research.pop('quality_scorecard', None)
    research.pop('visual_source_review', None)
    research.pop('visual_placement_review', None)
    research['service_quality_protocol'] = 'v1'
    research['route_experience_protocol'] = 'v1'
    research['premium_experience_protocol'] = 'v1'
    return research


def validate_service_plan(research):
    """Reject incomplete or invented task plans before a new Builder request.

    Legacy research is still audited on output; newly researched projects use
    v1 and must map every discovered business task before spending on a build.
    """
    if research.get('premium_experience_protocol') == 'v1':
        validate_premium_experience_plan(research)
    if research.get('route_experience_protocol') == 'v1':
        validate_route_experience_plan(research)
    from utils.visual_asset_continuity import validate_visual_plan
    validate_visual_plan(research)
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


def validate_route_experience_plan(research):
    routes = [p.get('path') for p in (research.get('site_architecture') or {}).get('pages', [])]
    rows = research.get('route_experience_plan')
    if (not routes or not isinstance(rows, list) or len(rows) != len(routes)
            or any(not isinstance(row, dict) for row in rows)):
        raise RuntimeError('Every route needs an experience and media plan before Builder')
    names = [row.get('route') for row in rows]
    if (any(not isinstance(name, str) for name in names)
            or len(set(names)) != len(names) or set(names) != set(routes)):
        raise RuntimeError('Experience plan must cover each planned route exactly once')
    for row in rows:
        for key in ('visitor_task', 'composition', 'brand_character', 'type_hierarchy', 'motion_decision'):
            if not isinstance(row.get(key), str) or not row[key].strip():
                raise RuntimeError('Experience plan is missing ' + key)
        for key in ('required_photo_subjects', 'available_source_images', 'missing_assets'):
            if (not isinstance(row.get(key), list)
                    or any(not isinstance(v, str) or not v.strip() for v in row[key])):
                raise RuntimeError('Experience plan needs an explicit list for ' + key)


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


def validate_premium_experience_plan(research):
    plan = research.get('premium_experience_plan')
    if not isinstance(plan, dict):
        raise RuntimeError('Premium experience plan is missing')
    for field in ('editable_platform', 'preview_implementation', 'delivery_parity_strategy',
                  'portfolio_strategy', 'contact_continuity', 'cold_load_test_plan',
                  'composition_selection', 'motion_purpose', 'image_scale_strategy',
                  'service_composition_strategy', 'craft_evidence_strategy',
                  'motion_quality_strategy', 'enquiry_preparation'):
        if not isinstance(plan.get(field), str) or not plan[field].strip():
            raise RuntimeError('Premium experience plan is missing ' + field)
    routes = [p.get('path') for p in (research.get('site_architecture') or {}).get('pages', [])]
    additions = plan.get('route_added_value')
    if (not isinstance(additions, dict) or set(additions) != set(routes)
            or any(not isinstance(value, str) or not value.strip() for value in additions.values())):
        raise RuntimeError('Every planned route needs its own additional visitor value')


# Review observations, not scores or promises from the generator. The enclosing
# domain record binds these to the current source, plan, bytes and reviewer.
ROUTE_REVIEW_CHECKS = {
    'visual': ('media_sufficiency', 'task_composition', 'brand_character',
               'readable_hierarchy', 'motion_suitability', 'project_presentation',
               'new_information', 'composition_comparison', 'whitespace_rhythm',
               'cta_repetition', 'image_subject_match', 'crop_integrity',
               'visual_information_preserved', 'sector_specificity',
               'image_quality_at_display_size', 'image_hierarchy',
               'service_composition_rationale', 'responsive_type_detail',
               'company_work_evidence', 'motion_material_quality'),
    'technical': ('wheel_scroll', 'trackpad_scroll', 'touch_scroll',
                  'keyboard_scroll', 'reduced_motion', 'motion_input_response',
                  'cold_load', 'route_transition'),
    'commercial': ('contact_continuity', 'enquiry_preparation'),
}


def _route_observations_complete(record, domain, routes):
    if domain not in ROUTE_REVIEW_CHECKS:
        return True
    rows = record.get('route_results')
    if not isinstance(rows, list) or len(rows) != len(routes):
        return False
    if any(not isinstance(row, dict) for row in rows):
        return False
    names = [row.get('route') for row in rows]
    if any(not isinstance(name, str) for name in names) or set(names) != set(routes):
        return False
    for row in rows:
        if not isinstance(row.get('evidence_reference'), str) or not row['evidence_reference'].strip():
            return False
        if domain == 'technical' and not all(isinstance(row.get(k), str) and row[k].strip()
                                             for k in ('device', 'browser')):
            return False
        checks = row.get('checks')
        if not isinstance(checks, dict):
            return False
        for name in ROUTE_REVIEW_CHECKS[domain]:
            check = checks.get(name)
            if (not isinstance(check, dict) or check.get('result') != 'pass'
                    or not isinstance(check.get('observation'), str)
                    or not check['observation'].strip()):
                return False
    return True


def audit_service_quality(pages, research, *, artifact_digest=None, review_bundle=None):
    brief = service_brief(research)
    blocking, pending = [], []
    try:
        validate_service_plan(research)
    except RuntimeError as error:
        blocking.append({'kind': 'invalid_business_task_plan', 'reason': str(error)})
    try:
        validate_premium_experience_plan(research)
    except RuntimeError as error:
        pending.append({'kind': 'premium_experience_plan_incomplete', 'reason': str(error)})
    try:
        validate_route_experience_plan(research)
    except RuntimeError as error:
        pending.append({'kind': 'route_experience_plan_incomplete', 'reason': str(error)})
    experience_rows = research.get('route_experience_plan')
    for row in experience_rows if isinstance(experience_rows, list) else []:
        if isinstance(row, dict) and row.get('missing_assets'):
            pending.append({'kind': 'route_assets_missing', 'route': row.get('route'),
                            'assets': row['missing_assets']})
    soups = {route: BeautifulSoup(raw, 'html.parser') for route, raw in pages.items()}
    for route, soup in soups.items():
        # An icon/button alone depends on the visitor's configured mail app.
        # Hidden footer text does not provide a selectable fallback.
        visible = BeautifulSoup(str(soup), 'html.parser')
        for node in visible.select('script,style,template,[hidden],[aria-hidden="true"]'):
            node.decompose()
        text = visible.get_text(' ', strip=True).casefold()
        for link in soup.select('a[href]'):
            href = str(link.get('href') or '')
            if href.casefold().startswith('mailto:'):
                email = unquote(href[7:].split('?', 1)[0]).strip().casefold()
                if email and email not in text:
                    blocking.append({'kind': 'email_fallback_missing', 'route': route})
                    break
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
        observations_ok = _route_observations_complete(record, domain, pages)
        if not observations_ok:
            pending.append({'kind': 'route_experience_observations_missing', 'domain': domain})
        ok = bool(isinstance(artifact_digest, str) and re.fullmatch('[a-f0-9]{64}', artifact_digest)
                  and record.get('approved') is True
                  and record.get('artifact_sha256') == artifact_digest
                  and record.get('contract_sha256') == brief['contract_sha256']
                  and record.get('independent_of_builder') is True
                  and record.get('reviewer_id') and record.get('evidence_reference')
                  and record.get('checked_at') and record.get('open_issues') == []
                  and isinstance(record.get('routes_reviewed'), list)
                  and all(isinstance(x, str) for x in record['routes_reviewed'])
                  and set(record['routes_reviewed']) == set(pages)
                  and observations_ok)
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
        if research.get('review_evidence_protocol') == 'v1':
            from utils.review_bundle import domain_evidence_complete
            ok = ok and domain_evidence_complete(review_bundle, record, domain, routes=pages,
                tasks=task_ids, source_exists=bool((research.get('source_inventory') or {}).get('pages')))
        reviews[domain] = 'reviewed' if ok else 'pending'
        if not ok:
            pending.append({'kind': 'domain_review_pending', 'domain': domain})
    # A human claim cannot erase a missing plan or invalid source record.
    return {'blocking': blocking, 'pending': pending, 'domains': reviews,
            'client_ready': not blocking and not pending, 'brief': brief,
            'media_decisions': reviewed_images,
            'note': 'No static defect is not a visual approval. Subject relevance and taste require inspection.'}

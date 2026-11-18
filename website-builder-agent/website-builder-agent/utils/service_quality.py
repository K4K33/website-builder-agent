"""Business tasks and evidence of design decisions, independent of a client demo.

Static checks cannot recognise a photograph's subject or certify good taste.
Unknown decisions stay pending until a reviewer inspects the exact bundle.
"""
from __future__ import annotations
import hashlib
import json
import re
from collections import Counter
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
The first screen states the verified primary offer and the visitor's next step.
Every service route must earn its place with a distinct visitor question and
source-backed answers, examples, or practical details. Combine thin routes
when evidence is sparse. Put company register details after the contact path.
Use evidence of actual work where available. Never turn a registry's business
scope into a service list. Give the primary action a clear destination and avoid
repeating a vague link through consecutive sections on the same page.
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

# The canonical Master Prompt is an actual runtime dependency, not a file
# that only a human might read. Load only its short active block to avoid
# multiplying tokens/API costs for every Research/Builder/Revision/QA call.
MASTER_PROMPT_PATH = Path(__file__).resolve().parents[1] / "docs/KAURIVO_MESTARI_PROMPT.md"
MASTER_PROMPT_SOURCE = MASTER_PROMPT_PATH.read_text(encoding="utf-8")
from utils.quality_v7 import V7_POLICY, V7_SHA256
# Version-bound research/preview evidence now changes when either V6 archive
# or the short active V7 design contract changes.
MASTER_PROMPT_SHA256 = hashlib.sha256(MASTER_PROMPT_SOURCE.encode("utf-8")).hexdigest()
# Preserve historical V6 contract IDs used in source-bound review evidence.
# V7 has a separate immutable SHA in every new design brief.
EFFECTIVE_MASTER_PROMPT_SHA256 = hashlib.sha256(
    (MASTER_PROMPT_SOURCE + "\nV7:" + V7_SHA256).encode("utf-8")
).hexdigest()
_MASTER_START = "<!-- ACTIVE_RUNTIME_CONTRACT_START -->"
_MASTER_END = "<!-- ACTIVE_RUNTIME_CONTRACT_END -->"
if MASTER_PROMPT_SOURCE.count(_MASTER_START) != 1 or MASTER_PROMPT_SOURCE.count(_MASTER_END) != 1:
    raise RuntimeError("Canonical master prompt is missing its single active runtime contract")
_active = MASTER_PROMPT_SOURCE.split(_MASTER_START, 1)[1].split(_MASTER_END, 1)[0].strip()
if len(_active) < 500:
    raise RuntimeError("Canonical master prompt runtime contract is incomplete")
POLICY += "\n" + _active + "\n"
# A short, ordered current standard overrides contradictory historical aesthetic
# instructions. Old factual/rights/SEO gates remain mandatory.
POLICY += "\nCURRENT K4URIVO MASTER V7 (design wins over decorative novelty):\n" + V7_POLICY + "\n"




def _hash(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                    separators=(',', ':')).encode()).hexdigest()


def _normal(text):
    return ' '.join(str(text or '').split())


def is_registry_source(url):
    host = (urlsplit(url).hostname or '').lower().rstrip('.')
    return any(host == domain or host.endswith('.' + domain)
               for domain in ('prh.fi', 'ytj.fi', 'virre.fi'))


_REGISTRY_SCOPE = re.compile(
    r'kaupparekisteri|päätoimiala|yhtiön toimialana on|kaikki laillinen liiketoiminta|'
    r'handelsregistret|huvudbransch|registered business scope', re.I
)


def validate_primary_offering(evidence, pages):
    """Bind one concrete offer to an exact excerpt from the observed site."""
    if isinstance(evidence, dict):
        url = evidence.get('source_url')
        label = _normal(evidence.get('label'))
        quote = _normal(evidence.get('quote'))
        if (isinstance(url, str) and label and len(quote.split()) >= 3
                and label.casefold() in quote.casefold()
                and not _REGISTRY_SCOPE.search(quote)
                and any(p.get('url') == url and quote in _normal(p.get('text'))
                        for p in pages)
                and not is_registry_source(url)):
            return {'label': label, 'quote': quote, 'source_url': url}
    raise RuntimeError("Original-site primary offering unverified; "
                       "confirm a current product or service with a customer-facing source.")


def reconcile_primary_offering_with_source(evidence, pages):
    """Repair a formatting-only model quotation using exact adjacent source text.

    Never infer a product, change a source URL, accept a paraphrased quote, or
    treat an industry registry as a client-facing service page. This covers
    cases where a model chooses a real service heading as its label and a
    verbatim paragraph immediately beneath it as its quote. The strict original
    validator remains the authority on the repaired evidence.
    """
    try:
        return validate_primary_offering(evidence, pages)
    except RuntimeError:
        if not isinstance(evidence, dict):
            raise
        url = evidence.get("source_url")
        label = _normal(evidence.get("label"))
        quote = _normal(evidence.get("quote"))
        if (not isinstance(url, str) or is_registry_source(url)
                or len(label) < 5 or len(label) > 90
                or len(quote.split()) < 3 or len(quote) > 280
                or _REGISTRY_SCOPE.search(label) or _REGISTRY_SCOPE.search(quote)):
            raise
        for page in pages if isinstance(pages, list) else []:
            if page.get("url") != url:
                continue
            original = _normal(page.get("text"))
            folded = original.casefold()
            quote_at = folded.find(quote.casefold())
            if quote_at < 0:
                continue  # A paraphrased or hallucinated model quote is never repaired.
            near_start = max(0, quote_at - 200)
            near_end = min(len(original), quote_at + len(quote) + 200)
            label_at = folded.find(label.casefold(), near_start, near_end)
            if label_at < 0:
                continue
            first = min(quote_at, label_at)
            last = max(quote_at + len(quote), label_at + len(label))
            if last - first > 250:
                continue
            exact_span = original[max(0, first - 45):min(len(original), last + 45)]
            if _REGISTRY_SCOPE.search(exact_span):
                continue
            return validate_primary_offering(
                {"source_url": url, "label": label, "quote": exact_span}, pages
            )
        raise


_GENERIC_ACTIONS = {
    'lähetä tiedustelu', 'ota yhteyttä', 'lue lisää', 'tutustu', 'tutustu lisää',
    'skicka en förfrågan', 'kontakta oss', 'läs mer',
    'send an inquiry', 'send an enquiry', 'get in touch', 'contact us', 'learn more',
}


def repeated_generic_actions(soup):
    main = soup.find('main')
    if not main:
        return []
    counts = Counter()
    for link in main.select('a[href]'):
        if link.find_parent(['header', 'footer', 'nav']):
            continue
        label = _normal(link.get_text(' ', strip=True)).casefold()
        if label in _GENERIC_ACTIONS:
            counts[label, link['href'].strip()] += 1
    return [{'label': label, 'destination': destination, 'count': count}
            for (label, destination), count in counts.items() if count >= 3]


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
               'source_observation_sha256': _hash({'inventory': research.get('source_inventory') or {},
                                                   'fact_sources': research.get('fact_sources') or []}),
               'source_sha256': source_inventory_sha256(research.get('source_inventory') or {}),
               'tasks': tasks, 'routes': routes,
               'task_plan': research.get('business_task_plan') or [],
               'media_plan': research.get('media_purpose_plan') or [],
               'voice': research.get('company_voice_brief') or {},
               'creative_selection': research.get('creative_selection'),
               'review_evidence_protocol': research.get('review_evidence_protocol'),
               'company_facts': research.get('company_facts') or {}}
    if research.get('media_selection_protocol'):
        payload['media_selection_protocol'] = research['media_selection_protocol']
    if 'primary_offering_evidence' in research:
        payload['primary_offering_evidence'] = research['primary_offering_evidence']
    return {**payload, 'contract_sha256': _hash(payload), 'policy': POLICY}


def reset_generated_review_claims(research):
    """A Research model can propose plans, never author independent approvals."""
    research.pop('service_quality_reviews', None)
    research['service_quality_protocol'] = 'v1'
    return research


def validate_media_selection(research):
    """Check source-image choices before Builder and again during output QA.

    This verifies traceability and required reasoning. A visual reviewer must
    still assess image subjects, quality, rights and the actual composition.
    """
    if research.get('media_selection_protocol') != 'source_first_v1':
        return
    observed = set()
    for page in (research.get('source_inventory') or {}).get('pages', []):
        images = (page.get('source_identity') or {}).get('original_content_photos') or []
        images = [*images, *(page.get('images') or [])]
        observed.update(image['src'] for image in images
                        if isinstance(image, dict) and image.get('src'))
    selections = research.get('media_purpose_plan') or []
    if not isinstance(selections, list):
        raise RuntimeError('Source-first media plan must be a list before Builder')
    for choice in selections:
        if not isinstance(choice, dict):
            raise RuntimeError('Source-first media choice must be a record before Builder')
        origin = choice.get('image_origin')
        if origin not in ('original', 'client_supplied', 'licensed_stock', 'generated'):
            raise RuntimeError('Source-first media choice needs image_origin before Builder')
        if origin == 'original':
            if (choice.get('source_src') or choice.get('src')) not in observed:
                raise RuntimeError('Source-first image must match an observed source before Builder')
        if origin in ('licensed_stock', 'generated'):
            candidates = choice.get('source_candidates')
            if (not isinstance(candidates, list) or (observed and not candidates)
                    or not _normal(choice.get('gap_reason'))):
                raise RuntimeError('Source-first replacement needs rejected source candidates and gap_reason before Builder')
            for candidate in candidates:
                if (not isinstance(candidate, dict) or candidate.get('source_src') not in observed
                        or not _normal(candidate.get('reason'))):
                    raise RuntimeError('Source-first replacement candidate must cite an observed image and reason before Builder')
                if candidate.get('usable_for_task') is not False:
                    raise RuntimeError('Source-first replacement requires an assessed unusable source candidate before Builder')


def validate_service_plan(research):
    """Reject incomplete or invented task plans before a new Builder request.

    Legacy research is still audited on output; newly researched projects use
    v1 and must map every discovered business task before spending on a build.
    """
    validate_media_selection(research)
    if 'primary_offering_evidence' in research:
        validate_primary_offering(research['primary_offering_evidence'],
                                  (research.get('source_inventory') or {}).get('pages', []))
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


def audit_service_quality(pages, research, *, artifact_digest=None, review_bundle=None):
    brief = service_brief(research)
    blocking, pending = [], []
    try:
        validate_service_plan(research)
    except RuntimeError as error:
        blocking.append({'kind': 'invalid_business_task_plan', 'reason': str(error)})
    soups = {route: BeautifulSoup(raw, 'html.parser') for route, raw in pages.items()}
    for route, soup in soups.items():
        for action in repeated_generic_actions(soup):
            blocking.append({'kind': 'repeated_generic_action', 'route': route, **action})
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
    # External and handwritten Research snapshots may contain bare URLs
    # instead of source records. Never crash the all-demo QA workflow: report
    # a blocking provenance error, keep only structured and text-backed facts.
    facts = research.get('fact_sources') or []
    if not isinstance(facts, list):
        blocking.append({'kind': 'invalid_fact_sources', 'reason': 'fact_sources must be a list'})
        facts = []
    for source in facts:
        if not isinstance(source, dict) or not str(source.get('url') or '').strip() or not isinstance(source.get('text'), str):
            blocking.append({'kind': 'invalid_fact_source_entry',
                             'reason': 'Source fact must contain url and text, never a bare URL'})
            continue
        sources[str(source['url'])] = source['text']
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

"""Commerce routing and exact-build evidence. Never creates payment success.

HTML catalogue parity, backend preparation and verified commerce are separate
states. Native WooCommerce owns price, variations, stock, tax and orders.
"""
import json
import re
from pathlib import Path
from hashlib import sha256
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone
from urllib.parse import urljoin, urlsplit, parse_qs
from bs4 import BeautifulSoup

PROTOCOL = 'commerce-v1'
COMMERCE_WORDS = re.compile(
    r'verkkokaup|webshop|webbutik|\bshop\b|\bstore\b|ostoskori|varukorg|'
    r'\bcart\b|\bbasket\b|\bcheckout\b|\bkassa\b|'
    r'\bosta\b|\bbuy\b|\bköp\b|'
    r'lis[aä][aä].{0,12}kori|l[aä]gg.{0,12}varukorg|add.{0,12}(?:cart|basket)', re.I)
COMMERCE_PATH = re.compile(r'/(?:cart|basket|checkout|ostoskori|kassa|varukorg|shop|store)(?:/|$)', re.I)
PURCHASE = re.compile(r'add.{0,12}(?:cart|basket)|lis[aä][aä].{0,12}kori|l[aä]gg.{0,12}varukorg', re.I)
CASES = ('catalogue_parity', 'product_selection', 'variant_selection', 'variant_price_stock',
         'add_to_cart', 'quantity_change', 'remove_item', 'empty_cart',
         'shipping_tax_total', 'payment_success', 'payment_failure',
         'payment_cancel', 'order_confirmation', 'stock_update',
         'duplicate_callback', 'out_of_stock', 'customer_product_edit')


def _https(value):
    try:
        p = urlsplit(value)
        return bool(p.scheme == 'https' and p.hostname and not p.username and not p.password)
    except (ValueError, TypeError, AttributeError):
        return False


def _purchase_action(url, label):
    query = parse_qs(urlsplit(url).query)
    return bool(PURCHASE.search(label) or 'add-to-cart' in query
                or query.get('wc-ajax') == ['add_to_cart'])


def extract_commerce_signals(html, source_url):
    soup = BeautifulSoup(html, 'html.parser')
    rows = []
    for node in soup.select('a[href],button,input[type="submit"],form[action]'):
        label = node.get('aria-label') or node.get_text(' ', strip=True) or node.get('value', '')
        href = urljoin(source_url, node.get('href') or node.get('action') or '')
        purchase = _purchase_action(href, str(label))
        if purchase or COMMERCE_WORDS.search(str(label)) or COMMERCE_PATH.search(urlsplit(href).path):
            rows.append({'kind': 'purchase_action' if purchase else 'commerce_entry',
                         'url': source_url if purchase else href,
                         'source_url': source_url, 'label': str(label)})
    for node in soup.select('script[type="application/ld+json"]'):
        try:
            data = json.loads(node.string or node.get_text())
        except (TypeError, ValueError):
            continue
        def inspect(value):
            if isinstance(value, list):
                for child in value: inspect(child)
            elif isinstance(value, dict):
                types = value.get('@type', [])
                types = [types] if isinstance(types, str) else types
                if isinstance(types, list) and any(str(t).rsplit('/', 1)[-1] in ('Product', 'Offer', 'AggregateOffer') for t in types):
                    rows.append({'kind': 'product_schema', 'url': source_url,
                                 'source_url': source_url, 'label': 'Observed Product/Offer JSON-LD'})
                for child in value.values(): inspect(child)
        inspect(data)
    return rows


def commerce_signals(research):
    rows = []
    for page in (research.get('source_inventory') or {}).get('pages', []):
        source = str(page.get('url') or '')
        rows.extend(x for x in page.get('commerce_signals', []) if isinstance(x, dict))
        for link in page.get('links') or []:
            href = urljoin(source, str(link.get('href') or ''))
            label = str(link.get('text') or link.get('aria_label') or '')
            purchase = _purchase_action(href, label)
            if purchase or COMMERCE_WORDS.search(label) or COMMERCE_PATH.search(urlsplit(href).path):
                rows.append({'kind': 'purchase_action' if purchase else 'commerce_entry',
                             'url': source if purchase else href, 'source_url': source, 'label': label})
        for field in ('raw_html', 'rendered_html'):
            if isinstance(page.get(field), str):
                rows.extend(extract_commerce_signals(page[field], source))
    explicit = (research.get('company_facts') or {}).get('external_shop_url')
    if explicit:
        rows.append({'kind': 'commerce_entry', 'url': explicit, 'source_url': explicit, 'label': 'Verified shop'})
    if research.get('commerce_required') is True:
        rows.append({'kind': 'requested_store', 'url': '', 'source_url': '', 'label': 'Owner requested commerce'})
    # Preserve distinct inspected URLs, including empty/icon-only cart entries.
    return list({json.dumps(r, sort_keys=True): r for r in rows}.values())


def validate_commerce_plan(research):
    signals = commerce_signals(research)
    plan = research.get('commerce_plan')
    if not signals and not plan:
        return {'mode': 'presentation', 'signals': []}
    if not isinstance(plan, dict) or plan.get('protocol') != PROTOCOL:
        raise RuntimeError('Commerce signals require an inspected commerce-v1 plan; an empty cart is not proof of no shop')
    mode = plan.get('mode')
    if mode not in ('inquiry_catalogue', 'preserve_existing', 'woocommerce_native'):
        raise RuntimeError('Choose inquiry_catalogue, preserve_existing or woocommerce_native; do not silently generate a brochure')
    inspection = plan.get('inspection')
    if not isinstance(inspection, dict):
        raise RuntimeError('Commerce source inspection is missing')
    urls = inspection.get('inspected_urls')
    discovered = {s['url'].rstrip('/') for s in signals if _https(s.get('url'))}
    if (not isinstance(urls, list) or not discovered <= {str(u).rstrip('/') for u in urls}
            or not inspection.get('captured_at') or not inspection.get('reason')
            or not _https(inspection.get('catalogue_url'))
            or inspection['catalogue_url'] not in urls
            or re.search(r'/(?:cart|checkout|ostoskori|varukorg|kassa)/?$', urlsplit(inspection['catalogue_url']).path, re.I)
            or inspection.get('catalogue_inspected') is not True
            or type(inspection.get('observed_product_count')) is not int
            or inspection['observed_product_count'] < 0):
        raise RuntimeError('Inspect every commerce entry and the actual catalogue; cart inspection alone is insufficient')
    if mode == 'inquiry_catalogue':
        if (inspection.get('purchasing_enabled') is not False
                or inspection.get('checkout_observed') is not False
                or any(s['kind'] in ('purchase_action', 'requested_store') for s in signals)):
            raise RuntimeError('An actual/requested purchase flow cannot be downgraded to enquiries')
    else:
        if not _https(plan.get('backend_url')) or not plan.get('catalogue_strategy'):
            raise RuntimeError('Commerce needs a real HTTPS backend and sourced catalogue/migration strategy')
    return {**plan, 'signals': signals}


def require_static_build_allowed(research):
    plan = validate_commerce_plan(research)
    if plan['mode'] == 'woocommerce_native':
        raise RuntimeError('Native commerce requires build-commerce and a real WordPress/WooCommerce preview; static HTML is not a store')
    return plan


def _evidence_bytes(company, item, suffixes, limit):
    try:
        root = Path(company['review_bundle']['manifest_path']).resolve().parent
        relative = Path(item['path'])
        file = root / relative
        if (relative.is_absolute() or file.is_symlink() or not file.resolve().is_relative_to(root)
                or file.suffix.lower() not in suffixes or not file.is_file()
                or not 0 < file.stat().st_size <= limit):
            return None
        raw = file.read_bytes()
        return raw if sha256(raw).hexdigest() == item.get('sha256') else None
    except (OSError, ValueError, TypeError, KeyError):
        return None


def _paid_backend_trace(company, record, bundle, plan):
    """Require actual sanitized backend bytes, not a success-page screenshot.

    Native exports and independent observation are still not cryptographic
    proof of provider identity. Never claim a fabricated fixture as a real run.
    """
    item = next((i for i in bundle.get('items', []) if isinstance(i, dict)
                 and i.get('id') == record.get('transaction_evidence_id')
                 and i.get('kind') == 'commerce_backend_trace'), None)
    if not item:
        return False
    try:
        raw = _evidence_bytes(company, item, {'.json'}, 100000)
        if raw is None: return False
        trace = json.loads(raw)
        total = Decimal(str(trace.get('total')))
        paid_at = datetime.fromisoformat(trace['date_paid_utc'].replace('Z', '+00:00'))
        deployed_at = datetime.fromisoformat(company['delivery']['deployed_at'].replace('Z', '+00:00'))
        checked_at = datetime.fromisoformat(record['checked_at'].replace('Z', '+00:00'))
        return bool(trace.get('protocol') in ('kaurivo-woo-order-evidence-v1', 'kaurivo-commerce-order-evidence-v1')
            and trace.get('synthetic') is not True
            and trace.get('environment') in ('staging', 'development', 'local')
            and str(trace.get('backend_url', '')).rstrip('/') == plan['backend_url'].rstrip('/')
            and type(trace.get('order_id')) is int and trace['order_id'] > 0
            and trace.get('paid') is True and trace.get('status') in ('processing', 'completed')
            and isinstance(trace.get('transaction_id'), str) and trace['transaction_id'].strip()
            and paid_at.tzinfo and deployed_at.tzinfo and checked_at.tzinfo
            and deployed_at <= paid_at <= checked_at
            and re.fullmatch('[A-Z]{3}', str(trace.get('currency', '')))
            and total.is_finite() and total > 0 and trace.get('items')
            and all(isinstance(i, dict) and type(i.get('product_id')) is int and i['product_id'] > 0
                    and type(i.get('quantity')) is int and i['quantity'] > 0 for i in trace['items']))
    except (OSError, ValueError, TypeError, KeyError, AttributeError, InvalidOperation):
        return False


def audit_commerce(research, company, *, artifact_digest=None, contract_digest=None, review_bundle=None, now=None, pages=None):
    blocking, pending = [], []
    try:
        plan = validate_commerce_plan(research)
    except RuntimeError as error:
        return {'blocking': [str(error)], 'pending': [], 'runtime_pass': False, 'mode': 'unclassified'}
    mode = plan['mode']
    if mode == 'presentation':
        for route, raw in (pages or {}).items():
            for signal in extract_commerce_signals(raw, 'https://preview.invalid/' + route.lstrip('/')):
                if (signal['kind'] in ('purchase_action', 'product_schema') or
                        re.search(r'/(cart|checkout|ostoskori|varukorg|kassa)/?$', urlsplit(signal['url']).path, re.I)):
                    return {'blocking': ['Output introduces unplanned commerce; classify its backend and test the real flow'],
                            'pending': [], 'runtime_pass': False, 'mode': 'unclassified'}
        return {'blocking': [], 'pending': [], 'runtime_pass': True, 'mode': mode}
    record = (company.get('delivery') or {}).get('commerce_runtime') or {}
    bundle = review_bundle or {}
    bound = bool(artifact_digest and contract_digest
        and record.get('artifact_sha256') == artifact_digest
        and record.get('contract_sha256') == contract_digest
        and bundle.get('artifact_sha256') == artifact_digest
        and bundle.get('contract_sha256') == contract_digest
        and record.get('independent_of_builder') is True
        and record.get('reviewer_id') and record.get('checked_at')
        and record.get('deployment_reference')
        and record['deployment_reference'] == (company.get('delivery') or {}).get('deployment_reference'))
    if not bound:
        pending.append('Exact deployment/source/plan-bound independent commerce runtime evidence missing')
    try:
        tested = datetime.fromisoformat(record['checked_at'].replace('Z', '+00:00'))
        deployed = datetime.fromisoformat(company['delivery']['deployed_at'].replace('Z', '+00:00'))
        age = (now or datetime.now(timezone.utc)) - tested
        if not tested.tzinfo or not deployed.tzinfo or tested < deployed or not 0 <= age.total_seconds() <= 14 * 86400:
            raise ValueError('stale')
    except (KeyError, ValueError, TypeError, AttributeError):
        pending.append('Commerce tests must be recent and recorded after this exact deployment')
    items = {(x.get('task_id'), x.get('viewport')) for x in bundle.get('items', [])
             if isinstance(x, dict) and x.get('kind') == 'commerce_capture'
             and _evidence_bytes(company, x, {'.png', '.jpg', '.jpeg', '.webp', '.webm'}, 30 * 1024 * 1024)}
    cases = ('source_classification',) if mode == 'inquiry_catalogue' else CASES
    if mode != 'inquiry_catalogue':
        if record.get('environment') != 'sandbox' or record.get('payment_mode') != 'test':
            pending.append('Actual payment gateway test mode/sandbox execution not demonstrated')
        if record.get('backend_url') != plan.get('backend_url'):
            pending.append('Tested commerce backend differs from the planned backend')
        if not _paid_backend_trace(company, record, bundle, plan):
            pending.append('Paid sandbox order/transaction backend export missing, changed or invalid; success URL is insufficient')
    tests = record.get('tests') if isinstance(record.get('tests'), list) else []
    for case in cases:
        for viewport in ('desktop', 'mobile'):
            matches = [x for x in tests if isinstance(x, dict) and x.get('case') == case and x.get('viewport') == viewport]
            if len(matches) != 1:
                pending.append(f'{case}:{viewport}: actual test missing or duplicated')
                continue
            row = matches[0]
            if row.get('result') == 'fail':
                blocking.append(f'{case}:{viewport}: observed commerce failure')
            elif (row.get('result') != 'pass' or not isinstance(row.get('observation'), str)
                  or not row['observation'].strip() or (case, viewport) not in items):
                pending.append(f'{case}:{viewport}: passing observation and captured evidence required')
    return {'blocking': blocking, 'pending': pending, 'runtime_pass': not blocking and not pending,
            'mode': mode, 'note': 'File integrity and observations do not independently certify their truth. Catalogue/link tests never certify payment.'}

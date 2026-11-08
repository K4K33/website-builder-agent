"""Synthetic offline adversarial tests; not real WooCommerce/gateway acceptance."""
import copy
import json
from datetime import datetime, timezone, timedelta
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
import unittest
import zipfile
from utils.commerce_workflow import (commerce_signals, extract_commerce_signals,
    validate_commerce_plan, require_static_build_allowed, audit_commerce, CASES)
from utils.woocommerce_build import prepare_woocommerce_build, CommerceStagingRequired
from utils.fetch import extract_text_and_meta
from utils.service_quality import service_brief
from utils.industry_workflow import crawl_original_website
from tests.test_concept_previews import PNG


def fixture(mode='woocommerce_native'):
    return {'source_inventory': {'pages': [{'url': 'https://merchant.example/',
        'links': [{'text': 'Ostoskori', 'href': '/cart/'}]}]},
        'commerce_plan': {'protocol': 'commerce-v1', 'mode': mode,
            'backend_url': 'https://stage.merchant.example/',
            'catalogue_strategy': 'Actual original catalogue must be mapped, never fabricated',
            'inspection': {'inspected_urls': ['https://merchant.example/cart/', 'https://merchant.example/gallery/'],
                'catalogue_url': 'https://merchant.example/gallery/', 'captured_at': '2026-11-08',
                'observed_product_count': 0, 'catalogue_inspected': True,
                'purchasing_enabled': mode != 'inquiry_catalogue', 'checkout_observed': mode != 'inquiry_catalogue',
                'reason': 'Isolated synthetic example, not an actual merchant inspection'}}}


def evidence_fixture(root, research):
    """Only exercises evidence integrity/shape; no real test result is authored."""
    now = datetime.now(timezone.utc)
    contract = service_brief(research)['contract_sha256']
    cases = ('source_classification',) if research['commerce_plan']['mode']=='inquiry_catalogue' else CASES
    record = {'artifact_sha256': 'a'*64, 'contract_sha256': contract,
        'independent_of_builder': True, 'reviewer_id': 'synthetic-fixture',
        'checked_at': now.isoformat(), 'deployment_reference': 'fixture-deployment',
        'backend_url': research['commerce_plan']['backend_url'],
        'environment': 'sandbox', 'payment_mode': 'test',
        'transaction_evidence_id': 'transaction',
        'tests': [{'case': case, 'viewport': view, 'result': 'pass',
                   'observation': 'Synthetic observation; never a live acceptance'}
                  for case in cases for view in ('desktop', 'mobile')]}
    trace = {'protocol': 'kaurivo-woo-order-evidence-v1', 'environment': 'staging',
        'backend_url': research['commerce_plan']['backend_url'], 'order_id': 42,
        'transaction_id': 'fixture-provider-reference', 'paid': True, 'status': 'processing',
        'date_paid_utc': now.isoformat(), 'total': '20.00', 'currency': 'EUR',
        'items': [{'product_id': 3, 'quantity': 1}]}
    raw = json.dumps(trace).encode();(root/'transaction.json').write_bytes(raw)
    (root/'synthetic-capture.png').write_bytes(PNG)
    items = [{'kind':'commerce_capture', 'task_id': case, 'viewport': view,
              'path':'synthetic-capture.png', 'sha256':sha256(PNG).hexdigest()}
             for case in cases for view in ('desktop','mobile')]
    items.append({'id':'transaction','kind':'commerce_backend_trace','path':'transaction.json','sha256':sha256(raw).hexdigest()})
    bundle = {'artifact_sha256':'a'*64,'contract_sha256':contract,'items':items}
    company = {'review_bundle': {'manifest_path': str(root/'manifest.json')},
        'delivery': {'deployment_reference':'fixture-deployment',
            'deployed_at':(now-timedelta(minutes=2)).isoformat(), 'commerce_runtime':record}}
    return company, bundle, contract, trace


class CommerceDiscoveryTests(unittest.TestCase):
    def test_cart_checkout_and_swedish_labels_without_shop_word(self):
        for label, path in [('Ostoskori','/cart/'),('Varukorg','/varukorg/'),('Kassa','/checkout/')]:
            research = {'source_inventory': {'pages': [{'url':'https://merchant.example/', 'links':[{'text':label,'href':path}]}]}}
            self.assertTrue(commerce_signals(research))
            with self.assertRaises(RuntimeError): validate_commerce_plan(research)

    def test_icon_and_product_jsonld_survive_fetch_script_removal(self):
        html = '<a href="/cart/" aria-label="Ostoskori"><svg></svg></a><script type="application/ld+json">{"@graph":[{"@type":"Product","offers":{"@type":"Offer","price":"15"}}]}</script>'
        page = extract_text_and_meta(html, base_url='https://merchant.example/')
        self.assertIn('product_schema', {x['kind'] for x in page['commerce_signals']})
        self.assertTrue(commerce_signals({'source_inventory':{'pages':[page]}}))

    def test_mutating_purchase_url_is_evidence_not_a_fetch_target(self):
        rows = extract_commerce_signals('<a href="/?add-to-cart=99">+</a>', 'https://merchant.example/product/99')
        self.assertEqual(rows[0]['kind'], 'purchase_action')
        self.assertEqual(rows[0]['url'], 'https://merchant.example/product/99')
        self.assertNotIn('add-to-cart', rows[0]['url'])

    def test_cartographer_and_workshop_are_not_automatically_shops(self):
        self.assertEqual(extract_commerce_signals('<a href="/cartography">Cartography workshop</a>', 'https://artist.example/'), [])
        self.assertEqual(validate_commerce_plan({})['mode'], 'presentation')

    def test_crawler_now_inspects_cart_but_does_not_execute_purchase_query(self):
        fetched = []
        def fetch(url):
            fetched.append(url)
            return {'success':True,'final_url':url,'links':[],'commerce_signals':[{'kind':'commerce_entry','url':url,'source_url':url,'label':'cart'}]}
        first = {'success':True,'final_url':'https://merchant.example/','links':[{'href':'/cart/','text':'Ostoskori'}, {'href':'/?add-to-cart=5','text':'+'}]}
        result = crawl_original_website('https://merchant.example/', fetch, first_page=first)
        self.assertIn('https://merchant.example/cart', fetched)
        self.assertFalse(any('add-to-cart' in x for x in fetched))
        self.assertTrue(any(p.get('commerce_signals') for p in result['pages']))

    def test_empty_cart_is_not_catalogue_inspection(self):
        r = fixture('inquiry_catalogue');r['commerce_plan']['inspection']['catalogue_url']='https://merchant.example/cart/'
        with self.assertRaises(RuntimeError): validate_commerce_plan(r)

    def test_real_add_to_cart_cannot_be_reclassified_as_enquiry(self):
        r=fixture('inquiry_catalogue');r['source_inventory']['pages'][0]['links'].append({'text':'Lisää ostoskoriin','href':'/product'})
        r['commerce_plan']['inspection']['inspected_urls'].append('https://merchant.example/')
        with self.assertRaisesRegex(RuntimeError,'downgraded'):validate_commerce_plan(r)

    def test_new_owner_requested_store_also_requires_commerce_path(self):
        with self.assertRaises(RuntimeError):validate_commerce_plan({'commerce_required':True})

    def test_inquiry_is_not_forced_into_fake_payment(self):
        r=fixture('inquiry_catalogue');self.assertEqual(require_static_build_allowed(r)['mode'],'inquiry_catalogue')
        self.assertFalse(audit_commerce(r,{})['runtime_pass'])


class NativeRoutingTests(unittest.TestCase):
    def test_static_response_cannot_bypass_native_backend(self):
        from utils.site_build_pipeline import build_pages_from_response
        with self.assertRaisesRegex(RuntimeError,'build-commerce'):
            build_pages_from_response('<html>fake cart</html>',slug='sample',company={'research':fixture()},output_root='/unwritten')

    def test_automatic_build_prepares_native_artifact_before_any_paid_concept_or_html(self):
        from agents import builder
        with TemporaryDirectory() as temp:
            company={'research':fixture()}
            with patch.object(builder,'_resolve_company',return_value=('sample',company)), \
                 patch.object(builder,'_output_dir',return_value=temp), \
                 patch.object(builder,'upsert_company') as save, \
                 patch.object(builder,'set_status') as status, \
                 patch.object(builder,'ask_claude') as ai:
                with self.assertRaises(CommerceStagingRequired) as result: builder.run_build('sample')
                self.assertTrue(Path(result.exception.result['archive']).is_file())
                self.assertFalse(result.exception.result['runtime_verified'])
                ai.assert_not_called();status.assert_not_called();save.assert_called_once()

    def test_package_is_native_integration_not_standalone_checkout_or_approval(self):
        with TemporaryDirectory() as temp:
            result=prepare_woocommerce_build(fixture(),temp)
            with zipfile.ZipFile(result['archive']) as z:
                self.assertNotIn('checkout.html', z.namelist())
                self.assertIn('kaurivo-native-commerce/kaurivo-commerce.php',z.namelist())
            self.assertFalse(result['client_release_ready'])
            self.assertEqual(result['status'],'prepared_not_runtime_verified')

    def test_cli_preparation_does_not_require_paid_consent_or_call_ai(self):
        import main
        from agents import builder
        with patch.object(main,'get_company',return_value=('sample',{'research':fixture()})), \
             patch.object(main,'_require_paid_consent') as paid, \
             patch.object(builder,'run_build',side_effect=CommerceStagingRequired({'archive':'/fixture.zip','runtime_verified':False})), \
             patch('builtins.print'):
            main.cmd_build(SimpleNamespace(company='sample',confirm_paid_apis=False))
            paid.assert_not_called()
        self.assertEqual(main.build_parser().parse_args(['build-commerce','sample']).company,'sample')


class RuntimeEvidenceTests(unittest.TestCase):
    def audit(self,r,c,b,h):return audit_commerce(r,c,artifact_digest='a'*64,contract_digest=h,review_bundle=b)

    def test_missing_backend_or_any_journey_cannot_be_approved(self):
        with TemporaryDirectory() as temp:
            r=fixture();c,b,h,_=evidence_fixture(Path(temp),r)
            self.assertTrue(self.audit(r,c,b,h)['runtime_pass']) # Integrity of synthetic fixture ONLY.
            for case in CASES:
                changed=copy.deepcopy(c);changed['delivery']['commerce_runtime']['tests']=[x for x in changed['delivery']['commerce_runtime']['tests'] if x['case']!=case]
                self.assertFalse(self.audit(r,changed,b,h)['runtime_pass'],case)
            b['items']=[i for i in b['items'] if i.get('kind')!='commerce_backend_trace']
            self.assertFalse(self.audit(r,c,b,h)['runtime_pass'])

    def test_success_url_or_checkbox_without_paid_backend_export_is_insufficient(self):
        with TemporaryDirectory() as temp:
            r=fixture();c,b,h,trace=evidence_fixture(Path(temp),r)
            for key,value in [('transaction_id',''),('paid',False),('status','pending'),('synthetic',True),('total','NaN'),('environment','production'),('date_paid_utc','2020-01-01T00:00:00Z')]:
                changed={**trace,key:value};raw=json.dumps(changed).encode();(Path(temp)/'transaction.json').write_bytes(raw)
                b['items'][-1]['sha256']=sha256(raw).hexdigest()
                self.assertFalse(self.audit(r,c,b,h)['runtime_pass'],key)

    def test_tampered_missing_or_escaped_backend_bytes_stay_pending(self):
        with TemporaryDirectory() as temp:
            r=fixture();c,b,h,_=evidence_fixture(Path(temp),r)
            for path in ('missing.json','../transaction.json','/etc/passwd'):
                changed=copy.deepcopy(b);changed['items'][-1]['path']=path
                self.assertFalse(self.audit(r,c,changed,h)['runtime_pass'])
            (Path(temp)/'transaction.json').write_text('{}')
            self.assertFalse(self.audit(r,c,b,h)['runtime_pass'])

    def test_generated_json_or_missing_screenshot_does_not_count_as_journey_capture(self):
        with TemporaryDirectory() as temp:
            r=fixture();c,b,h,_=evidence_fixture(Path(temp),r)
            changed=copy.deepcopy(b)
            changed['items'][0]['path']='transaction.json'
            changed['items'][0]['sha256']=b['items'][-1]['sha256']
            self.assertFalse(self.audit(r,c,changed,h)['runtime_pass'])
            (Path(temp)/'synthetic-capture.png').unlink()
            self.assertFalse(self.audit(r,c,b,h)['runtime_pass'])

    def test_failed_stock_or_payment_test_blocks_even_with_complete_capture_list(self):
        with TemporaryDirectory() as temp:
            r=fixture();c,b,h,_=evidence_fixture(Path(temp),r)
            for case in ('stock_update','payment_failure','duplicate_callback','customer_product_edit'):
                changed=copy.deepcopy(c);next(x for x in changed['delivery']['commerce_runtime']['tests'] if x['case']==case)['result']='fail'
                self.assertTrue(self.audit(r,changed,b,h)['blocking'])

    def test_stale_self_review_wrong_backend_or_predeployment_run_stays_pending(self):
        with TemporaryDirectory() as temp:
            r=fixture();c,b,h,_=evidence_fixture(Path(temp),r)
            for key,value in [('artifact_sha256','b'*64),('independent_of_builder',False),('backend_url','https://other.example/'),('payment_mode','live'),('checked_at','2020-01-01T00:00:00+00:00')]:
                changed=copy.deepcopy(c);changed['delivery']['commerce_runtime'][key]=value
                self.assertFalse(self.audit(r,changed,b,h)['runtime_pass'],key)

    def test_enquiry_classification_needs_captures_but_not_a_fabricated_order(self):
        with TemporaryDirectory() as temp:
            r=fixture('inquiry_catalogue');c,b,h,_=evidence_fixture(Path(temp),r)
            b['items']=[i for i in b['items'] if i['kind']=='commerce_capture']
            self.assertTrue(self.audit(r,c,b,h)['runtime_pass'])

    def test_plan_or_catalogue_changes_invalidate_the_shared_contract(self):
        r=fixture();before=service_brief(r)['contract_sha256'];r['commerce_plan']['backend_url']='https://other.example/'
        self.assertNotEqual(before,service_brief(r)['contract_sha256'])
        before=service_brief(r)['contract_sha256'];r['commerce_inventory']=[{'products':[{'name':'changed'}]}]
        self.assertNotEqual(before,service_brief(r)['contract_sha256'])

    def test_whole_site_audit_exposes_missing_commerce_even_if_html_has_cart_link(self):
        from utils.master_audit import audit_site_contract
        r=fixture();r.pop('commerce_plan')
        result=audit_site_contract({'/':'<main><h1>Fine gallery</h1><a href="https://merchant.example/cart/">Ostoskori</a></main>'},r)
        self.assertIn('commerce_runtime',result['blocking']['universal'])
        self.assertFalse(result['public_demo_ready']);self.assertFalse(result['client_release_ready'])

    def test_new_fake_checkout_is_detected_even_without_a_source_store(self):
        result=audit_commerce({}, {}, pages={'/':'<main><a href="/checkout/">Kassalle</a></main>'})
        self.assertTrue(result['blocking'])


if __name__=='__main__':unittest.main()

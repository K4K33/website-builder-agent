"""Actual evidence bytes, explicit gaps and no automatic independent approval."""
import copy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from tests.test_concept_previews import PNG
from tests.test_service_quality import fixture, reviews
from utils.review_bundle import (collect_review_bundle, verify_review_bundle,
                                current_review_bundle, domain_evidence_complete, preserve_route_captures)
from utils.service_quality import audit_service_quality, service_brief
from utils.site_integrity import site_sha256


def setup(folder, *, complete=True):
    root = Path(folder) / 'site'; root.mkdir()
    research, pages = fixture()
    research['review_evidence_protocol'] = 'v1'
    (root/'assets').mkdir(); (root/'assets/photo.png').write_bytes(PNG)
    pages['index.html'] = pages['index.html'].replace('https://repair.example/workshop.jpg','assets/photo.png')
    research['media_purpose_plan'][0]['source_src'] = research['media_purpose_plan'][0]['src']
    research['media_purpose_plan'][0]['src'] = 'assets/photo.png'
    (root/'index.html').write_text(pages['index.html'], encoding='utf-8')
    captures = Path(folder) / 'captures'; captures.mkdir()
    for name in ('desktop','mobile','prior','journey'):
        (captures/(name+'.png')).write_bytes(PNG)
    shots = {vp: str(captures/(vp+'.png')) for vp in ('desktop','mobile')}
    research['original_screenshots'] = shots
    qa = {'browser': {'pass': True, 'screenshots': shots},
          'prior_client_captures': [{'client':'unrelated-fixture','path':str(captures/'prior.png')}],
          'journey_captures': [{'task_id':research['business_task_plan'][0]['task_id'],
                                'path':str(captures/'journey.png')}]}
    if not complete: qa = {'browser': {'screenshots': {}}}
    company = {'research':research, 'build': {'output_path':str(root/'index.html'),'page_paths':['index.html']}}
    reference = collect_review_bundle(company, pages, qa, site_root=root,
        output_parent=root/'_review_material', allowed_capture_roots=[captures])
    company['review_bundle'] = reference
    return root, research, pages, company, reference


class ReviewBundleTests(unittest.TestCase):
    def test_premium_collects_real_captures_with_state_and_missing_files(self):
        with TemporaryDirectory() as folder:
            root,r,pages,company,ref=setup(folder);captures=Path(folder)/'captures'
            company['delivery']={'premium_execution':{'observations':[
                {'kind':'galleries','scope_id':'work','route':'index.html','viewport':'mobile',
                 'state':'selected','capture_paths':[str(captures/'mobile.png')]},
                {'kind':'motion','scope_id':'object','route':'index.html','viewport':'desktop',
                 'state':'drag','capture_paths':[str(captures/'missing.png')]}]}}
            company['review_bundle']=collect_review_bundle(company,pages,{},site_root=root,
                output_parent=root/'_review_material',allowed_capture_roots=[captures])
            bundle=current_review_bundle(company,pages)
            self.assertTrue(any(i['kind']=='premium_capture' and i['state']=='selected'
                and i['task_id']=='galleries:work' and i['viewport']=='mobile' for i in bundle['items']))
            self.assertTrue(any(i['kind']=='premium_capture' and i['state']=='drag' for i in bundle['missing']))
            self.assertTrue(any(i['kind']=='media_asset' and i.get('asset_src')=='assets/photo.png' for i in bundle['items']))

    def test_commerce_collects_private_backend_bytes_and_viewport_captures_not_checkboxes(self):
        with TemporaryDirectory() as folder:
            root, r, pages, company, ref = setup(folder)
            captures = Path(folder)/'captures'
            (captures/'order.json').write_text('{"synthetic":true}')
            company['delivery'] = {'commerce_runtime': {
                'transaction_capture_path': str(captures/'order.json'),
                'tests': [{'case':'payment_success','viewport':'mobile','result':'pass',
                           'capture_paths':[str(captures/'mobile.png')]},
                          {'case':'stock_update','viewport':'desktop','result':'pass',
                           'capture_paths':[str(captures/'missing.png')]}]}}
            company['review_bundle'] = collect_review_bundle(company, pages, {}, site_root=root,
                output_parent=root/'_review_material', allowed_capture_roots=[captures])
            bundle = current_review_bundle(company, pages)
            backend = next(i for i in bundle['items'] if i['kind']=='commerce_backend_trace')
            self.assertEqual((Path(company['review_bundle']['manifest_path']).parent/backend['path']).read_text(), '{"synthetic":true}')
            self.assertTrue(any(i['kind']=='commerce_capture' and i['task_id']=='payment_success'
                and i['viewport']=='mobile' for i in bundle['items']))
            self.assertFalse(any(i['kind']=='commerce_capture' and i['task_id']=='stock_update'
                for i in bundle['items']))
            self.assertTrue(any(i['kind']=='commerce_capture' and i['task_id']=='stock_update'
                for i in bundle['missing']))

    def test_same_folder_page_captures_do_not_overwrite_reviewed_route(self):
        with TemporaryDirectory() as folder:
            root = Path(folder)
            shot = root/'desktop.png'; shot.write_bytes(PNG)
            first = preserve_route_captures({'screenshots': {'desktop':str(shot)}},
                                            site_root=root, route='index.html')
            shot.write_bytes(PNG + b'second-page')
            second = preserve_route_captures({'screenshots': {'desktop':str(shot)}},
                                             site_root=root, route='services.html')
            self.assertNotEqual(first['screenshots'],second['screenshots'])
            self.assertEqual(Path(first['screenshots']['desktop']).read_bytes(),PNG)
            self.assertEqual(Path(second['screenshots']['desktop']).read_bytes(),PNG+b'second-page')

    def test_actual_reports_and_images_are_copied_into_one_private_bundle(self):
        with TemporaryDirectory() as folder:
            root, r, pages, company, ref = setup(folder)
            m = current_review_bundle(company, pages)
            self.assertFalse(m['missing'])
            self.assertTrue(Path(ref['index_path']).is_file())
            self.assertFalse(m['premium_approval'])
            self.assertTrue({'source_inventory','copy_inventory','browser_report','new_screenshot','original_screenshot','media_asset'}
                            <= {i['kind'] for i in m['items']})

    def test_missing_screenshots_remain_explicit_gaps(self):
        with TemporaryDirectory() as folder:
            root, r, pages, company, ref = setup(folder, complete=False)
            m = current_review_bundle(company, pages)
            self.assertTrue(any(i['kind']=='new_screenshot' for i in m['missing']))
            self.assertTrue(any(i['kind']=='journey_capture' for i in m['missing']))
            self.assertTrue(any(i['kind']=='prior_client_screenshot' for i in m['missing']))
            self.assertGreater(ref['missing_count'],0)

    def test_edited_report_or_screenshot_bytes_invalidate_bundle(self):
        for kind in ('browser_report','new_screenshot'):
            with TemporaryDirectory() as folder:
                root, r, pages, company, ref = setup(folder)
                m = current_review_bundle(company, pages)
                item = next(i for i in m['items'] if i['kind']==kind)
                (Path(ref['manifest_path']).parent/item['path']).write_bytes(b'changed')
                with self.assertRaises(RuntimeError): current_review_bundle(company, pages)

    def test_new_html_source_or_assets_need_fresh_review_material(self):
        for change in ('html','source','asset'):
            with TemporaryDirectory() as folder:
                root, r, pages, company, ref = setup(folder)
                if change=='html': pages['index.html'] += '<p>Changed</p>'
                elif change=='source': r['company_facts']['name']='Other business'
                else: (root/'assets/photo.png').write_bytes(PNG+b'changed')
                with self.assertRaises(RuntimeError): current_review_bundle(company, pages)

    def test_outside_files_and_symlinks_are_not_collected(self):
        with TemporaryDirectory() as folder:
            root, r, pages, company, ref = setup(folder)
            outside = Path(folder)/'outside.png'; outside.write_bytes(PNG)
            symlink=root/'alias.png'; symlink.symlink_to(outside)
            qa={'browser':{'screenshots':{'desktop':str(outside),'mobile':str(symlink)}}}
            ref=collect_review_bundle(company,pages,qa,site_root=root,
                output_parent=root/'_review_material',allowed_capture_roots=[])
            m=json.loads(Path(ref['manifest_path']).read_text())
            self.assertFalse(any(i['kind']=='new_screenshot' for i in m['items']))
            self.assertTrue(m['missing'])

    def test_loose_reference_or_checkbox_is_not_accepted_by_new_protocol(self):
        with TemporaryDirectory() as folder:
            root,r,pages,company,ref=setup(folder)
            actual=site_sha256(root,list(pages)); r['service_quality_reviews']=reviews(r,pages,actual)
            self.assertFalse(audit_service_quality(pages,r,artifact_digest=actual)['client_ready'])
            bundle=current_review_bundle(company,pages)
            self.assertFalse(audit_service_quality(pages,r,artifact_digest=actual,review_bundle=bundle)['client_ready'])

    def test_each_domain_resolves_real_file_ids_and_still_needs_review(self):
        with TemporaryDirectory() as folder:
            root,r,pages,company,ref=setup(folder)
            actual=site_sha256(root,list(pages)); r['service_quality_reviews']=reviews(r,pages,actual)
            bundle=current_review_bundle(company,pages)
            for record in r['service_quality_reviews'].values(): record['evidence_ids']=[i['id'] for i in bundle['items']]
            self.assertTrue(audit_service_quality(pages,r,artifact_digest=actual,review_bundle=bundle)['client_ready'])
            r['service_quality_reviews']['visual']['approved']=False
            self.assertFalse(audit_service_quality(pages,r,artifact_digest=actual,review_bundle=bundle)['client_ready'])

    def test_wrong_file_id_or_domain_material_is_rejected(self):
        with TemporaryDirectory() as folder:
            root,r,pages,company,ref=setup(folder); bundle=current_review_bundle(company,pages)
            for ids in (['made-up'], [i['id'] for i in bundle['items'] if i['kind']=='browser_report']):
                self.assertFalse(domain_evidence_complete(bundle,{'evidence_ids':ids},'visual',
                    routes=pages,tasks=[],source_exists=True))

    def test_journey_report_without_actual_task_capture_is_not_completion(self):
        with TemporaryDirectory() as folder:
            root,r,pages,company,ref=setup(folder); bundle=current_review_bundle(company,pages)
            ids=[i['id'] for i in bundle['items'] if i['kind']!='journey_capture']
            self.assertFalse(domain_evidence_complete(bundle,{'evidence_ids':ids},'commercial',
                routes=pages,tasks=[r['business_task_plan'][0]['task_id']],source_exists=True))

    def test_live_file_reference_cannot_be_bound_to_in_memory_replacement_html(self):
        with TemporaryDirectory() as folder:
            root,r,pages,company,ref=setup(folder)
            with self.assertRaises(RuntimeError): current_review_bundle(company,{'index.html':'<main>New</main>'})

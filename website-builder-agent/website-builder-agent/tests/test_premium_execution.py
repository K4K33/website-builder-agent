"""Offline adversarial fixtures only. No real client/gateway/browser approval."""
import copy
import json
import struct
import unittest
import zlib
from datetime import datetime, timezone, timedelta
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
from utils.premium_execution import (PROTOCOL, CHECKS, audit_execution, validate_execution_plan,
                                     balanced_gallery_rows, image_dimensions)
from utils.service_quality import service_brief, audit_service_quality, source_tasks, reset_generated_review_claims
from utils.fetch import extract_text_and_meta
from tests.test_service_quality import fixture as service_fixture, reviews
from tests.test_shared_cms_editing import SharedEditingTests
from utils.client_handover import _shared_editor_evidence_complete


def png(w=32,h=16):
    def chunk(kind,content):return struct.pack('>I',len(content))+kind+content+struct.pack('>I',zlib.crc32(kind+content)&0xffffffff)
    return b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',w,h,8,2,0,0,0))+chunk(b'IDAT',zlib.compress((b'\0'+b'\x80\x80\x80'*w)*h))+chunk(b'IEND',b'')


def fixture(root):
    url='https://source.example/work';photo=url+'/photo.png'
    html='<main><h1>Boat repairs</h1><section id="gallery" class="gallery-grid">'+''.join(f'<img id="image{i}" src="assets/photo.png" alt="Repair work">' for i in range(4))+'</section><article id="story">Old hull. Replace damaged wood. Repaired hull.</article><div id="motion">Work area illustration</div></main>'
    plan={'protocol':PROTOCOL,'galleries':[{'id':'work','route':'index.html','selector':'#gallery','purpose':'portfolio','last_row_strategy':'2+2 desktop, balanced rows mobile','responsive_strategy':'Native layout, no scroll hooks','states':[{'id':'all','expected_count':4},{'id':'selected','expected_count':2}]}],
          'images':[{'id':'photo'+str(i),'route':'index.html','selector':'#image'+str(i),'source_src':photo,'display_strategy':'No enlargement beyond available source pixels'} for i in range(4)],
          'case_studies':[{'id':'repair','route':'index.html','selector':'#story','missing_information':[], 'facts':{k:{'source_url':url,'source_text':text,'rendered_text':text} for k,text in [('context','Old hull.'),('work','Replace damaged wood.'),('result','Repaired hull.')]}}],
          'motion':[{'id':'boat','route':'index.html','selector':'#motion','purpose':'Locate the selected work area','material_strategy':'Illustrative materials; not a verified construction model','states':[{'id':'initial'},{'id':'expanded'},{'id':'transition'}]}]}
    research={'premium_execution_protocol':'v1','premium_execution_plan':plan,'site_architecture':{'pages':[{'path':'index.html'}]},'source_inventory':{'pages':[{'url':url,'text':'Old hull. Replace damaged wood. Repaired hull.','images':[{'src':photo}]}]}}
    contract=service_brief(research)['contract_sha256'];now=datetime.now(timezone.utc)
    observations=[];items=[]
    raw=png();(root/'capture.png').write_bytes(raw);(root/'media.png').write_bytes(raw)
    items.append({'id':'media','kind':'media_asset','route':'index.html','asset_src':'assets/photo.png','path':'media.png','sha256':sha256(raw).hexdigest()})
    for kind in CHECKS:
        for scope in plan[kind]:
            for state in scope.get('states',[{'id':'default'}]):
                for vp in ('desktop','mobile'):
                    row={'kind':kind,'scope_id':scope['id'],'route':'index.html','state':state['id'],'viewport':vp,
                         'checks':{c:{'result':'pass','observation':'Synthetic observation for integrity test only'} for c in CHECKS[kind]}}
                    if kind=='galleries':row['layout']={'container_width':900,'items':[{'x':(i%2)*450,'y':(i//2)*220,'width':440,'height':210} for i in range(state['expected_count'])]}
                    if kind=='images':row['display']={'width':16,'height':8,'dpr':2}
                    observations.append(row)
                    items.append({'id':str(len(items)),'kind':'premium_capture','route':'index.html','task_id':kind+':'+scope['id'],'state':state['id'],'viewport':vp,'path':'capture.png','sha256':sha256(raw).hexdigest()})
    record={'artifact_sha256':'a'*64,'contract_sha256':contract,'deployment_reference':'synthetic-deploy','independent_of_builder':True,'reviewer_id':'synthetic-fixture','checked_at':now.isoformat(),'observations':observations}
    company={'review_bundle':{'manifest_path':str(root/'manifest.json')},'delivery':{'deployment_reference':'synthetic-deploy','deployed_at':(now-timedelta(minutes=5)).isoformat(),'premium_execution':record}}
    bundle={'artifact_sha256':'a'*64,'contract_sha256':contract,'items':items}
    return research,{'index.html':html},company,bundle,contract


class PremiumExecutionTests(unittest.TestCase):
    def audit(self,r,p,c,b,h):return audit_execution(p,r,c,artifact_digest='a'*64,contract_digest=h,review_bundle=b)

    def test_balanced_recipe_does_not_lose_reorder_or_leave_a_final_orphan(self):
        self.assertEqual(balanced_gallery_rows(4,3),[[0,1],[2,3]])
        self.assertEqual(balanced_gallery_rows(7,3),[[0,1,2],[3,4],[5,6]])
        for count in range(1,100):
            for cols in range(2,7):
                rows=balanced_gallery_rows(count,cols)
                self.assertEqual([n for row in rows for n in row],list(range(count)))
                self.assertTrue(all(0<len(row)<=cols for row in rows))
                if count>1:self.assertNotEqual(len(rows[-1]),1)
        self.assertEqual(balanced_gallery_rows(0,3),[])
        for args in ((-1,3),(3,0),(True,2)):
            with self.assertRaises(ValueError):balanced_gallery_rows(*args)

    def test_actual_png_jpeg_and_webp_dimensions_not_css_claim(self):
        self.assertEqual(image_dimensions(png(600,400)),(600,400))
        jpeg=b'\xff\xd8\xff\xc0\x00\x0b\x08\x01\x90\x02\x58\x01\x01\x11\x00\xff\xd9'
        self.assertEqual(image_dimensions(jpeg),(600,400))
        webp=b'RIFF'+b'\0'*4+b'WEBPVP8X'+b'\0'*8+(599).to_bytes(3,'little')+(399).to_bytes(3,'little')
        self.assertEqual(image_dimensions(webp),(600,400))
        for raw in (b'',b'not an image',b'\xff\xd8\xff\xc0\x00\x02'):
            self.assertIsNone(image_dimensions(raw))

    def test_complete_synthetic_records_only_prove_integrity(self):
        with TemporaryDirectory() as t:
            r,p,c,b,h=fixture(Path(t));self.assertTrue(self.audit(r,p,c,b,h)['ready'])

    def test_every_group_motion_state_and_viewport_needs_actual_capture(self):
        with TemporaryDirectory() as t:
            r,p,c,b,h=fixture(Path(t))
            for kind in ('galleries','motion'):
                changed=copy.deepcopy(b);changed['items']=[x for x in changed['items'] if not (x['kind']=='premium_capture' and x['task_id'].startswith(kind+':') and x['viewport']=='mobile')]
                self.assertFalse(self.audit(r,p,c,changed,h)['ready'])
            (Path(t)/'capture.png').write_bytes(b'changed');self.assertFalse(self.audit(r,p,c,b,h)['ready'])

    def test_right_column_final_image_blocks_even_when_review_says_pass(self):
        with TemporaryDirectory() as t:
            r,p,c,b,h=fixture(Path(t));row=c['delivery']['premium_execution']['observations'][0]
            row['layout']['items']=[{'x':(i%3)*300,'y':(i//3)*220,'width':290,'height':210} for i in range(4)]
            row['layout']['items'][-1]['x']=600
            report=self.audit(r,p,c,b,h);self.assertTrue(any('isolated final image' in x for x in report['blocking']))

    def test_missing_geometry_cannot_be_replaced_by_a_checkbox(self):
        with TemporaryDirectory() as t:
            r,p,c,b,h=fixture(Path(t));c['delivery']['premium_execution']['observations'][0].pop('layout')
            self.assertFalse(self.audit(r,p,c,b,h)['ready'])

    def test_image_source_bytes_and_dpr_limit_enlargement(self):
        with TemporaryDirectory() as t:
            r,p,c,b,h=fixture(Path(t));row=next(o for o in c['delivery']['premium_execution']['observations'] if o['kind']=='images')
            row['display']['width']=17
            self.assertTrue(any('source pixels' in x for x in self.audit(r,p,c,b,h)['blocking']))
            row['display']['width']=16;(Path(t)/'media.png').write_bytes(png(8,4))
            self.assertFalse(self.audit(r,p,c,b,h)['ready']) # Old capture hash no longer fits.

    def test_source_backed_case_study_does_not_allow_invented_outcomes(self):
        with TemporaryDirectory() as t:
            r,p,c,b,h=fixture(Path(t));r['premium_execution_plan']['case_studies'][0]['facts']['result']['source_text']='Guaranteed forever'
            self.assertTrue(self.audit(r,p,c,b,h)['blocking'])
            r['premium_execution_plan']['case_studies'][0]['facts']['result']={}
            r['premium_execution_plan']['case_studies'][0]['missing_information']=['Ask client about the outcome']
            result=self.audit(r,p,c,b,h);self.assertFalse(result['ready']);self.assertTrue(result['pending'])

    def test_generic_checks_missing_unplanned_images_and_bad_selectors_fail(self):
        with TemporaryDirectory() as t:
            r,p,c,b,h=fixture(Path(t));c['delivery']['premium_execution']['observations'][0]['checks']={}
            self.assertFalse(self.audit(r,p,c,b,h)['ready'])
            p['index.html']+='<main><img src="unknown.png"></main>'
            self.assertTrue(self.audit(r,p,c,b,h)['blocking'])
            r['premium_execution_plan']['galleries'][0]['selector']='['
            self.assertTrue(self.audit(r,p,c,b,h)['blocking'])

    def test_observed_failure_stale_binding_and_duplicate_record_never_pass(self):
        with TemporaryDirectory() as t:
            r,p,c,b,h=fixture(Path(t))
            for mutation in ('fail','old','wrong_build','duplicate','malformed'):
                changed=copy.deepcopy(c);rec=changed['delivery']['premium_execution']
                if mutation=='fail':next(iter(rec['observations'][0]['checks'].values()))['result']='fail'
                elif mutation=='old':rec['checked_at']='2000-01-01T00:00:00Z'
                elif mutation=='wrong_build':rec['artifact_sha256']='b'*64
                elif mutation=='duplicate':rec['observations'].append(rec['observations'][0])
                else:rec['observations'][0]['checks']=[]
                self.assertFalse(self.audit(r,p,changed,b,h)['ready'],mutation)

    def test_new_research_resets_approval_and_requires_plan_before_paid_concepts(self):
        r=reset_generated_review_claims({'premium_execution_review':{'approved':True}})
        self.assertNotIn('premium_execution_review',r)
        with self.assertRaises(RuntimeError):validate_execution_plan(r)
        from agents import builder
        with patch.object(builder,'_resolve_company',return_value=('sample',{'research':r})), patch.object(builder,'ask_claude') as paid:
            with self.assertRaisesRegex(RuntimeError,'premium-execution'):builder.run_build('sample')
            paid.assert_not_called()

    def test_plan_changes_invalidate_exact_review_contract(self):
        with TemporaryDirectory() as t:
            r,p,c,b,h=fixture(Path(t));r['premium_execution_plan']['galleries'][0]['last_row_strategy']='Another layout'
            self.assertNotEqual(service_brief(r)['contract_sha256'],h)

    def test_current_failed_route_review_blocks_not_merely_pending(self):
        r,p=service_fixture();r['service_quality_reviews']=reviews(r,p)
        r['service_quality_reviews']['visual']['route_results'][0]['checks']['gallery_final_row_balance']['result']='fail'
        report=audit_service_quality(p,r,artifact_digest='a'*64)
        self.assertTrue(any(i['kind']=='observed_quality_failure' for i in report['blocking']))
        r['service_quality_reviews']['visual']['artifact_sha256']='b'*64
        self.assertFalse(any(i['kind']=='observed_quality_failure' for i in audit_service_quality(p,r,artifact_digest='a'*64)['blocking']))

    def test_legacy_email_validator_and_phone_storage_forms_are_business_tasks(self):
        html='''<form method="post"><label for="q2">Sähköposti</label><input id="q2" type="text" onblur="validate(this,'Email')"><textarea></textarea></form>
        <form action="/talvisailytys"><label for="q3">Puhelin</label><input id="q3" type="text"><label>Veneen tiedot<select></select></label></form>
        <form><input type="email"><button>Newsletter</button></form>'''
        page=extract_text_and_meta(html,base_url='https://source.example/')
        tasks=source_tasks({'source_inventory':{'pages':[page]}})
        self.assertEqual({t['kind'] for t in tasks},{'contact_form','quotation_form'})
        self.assertEqual(page['forms'][0]['fields'][0]['type'],'text')
        self.assertEqual(page['forms'][0]['fields'][0]['semantic_type'],'email')

    def test_modern_cms_requires_real_edit_save_publish_verify_and_restore_steps(self):
        c=SharedEditingTests().fixture();c['research']['premium_execution_protocol']='v1'
        record=c['delivery']['shared_cms_edit_evidence'];record['artifact_sha256']='a'*64
        record['deployment_reference']=c['delivery']['deployment_reference'];record['checked_at']=datetime.now(timezone.utc).isoformat()
        for field in ('text','image','navigation'):
            task=copy.deepcopy(record['tasks'][0]);task['field']=field;record['tasks'].append(task)
        for task in record['tasks']:
            task.update(saved_value=task['after_value'],published_value=task['after_value'],restored_value=task['before_value'])
            task['steps']={name:{'result':'pass','observation':'Synthetic, not real CMS execution','capture_role':'after'} for name in ('login','edit','save','publish','verify_desktop','verify_mobile','restore','verify_restored')}
        # The QA full-site digest, not merely an HTML-only checksum, binds edits.
        self.assertTrue(_shared_editor_evidence_complete(c,c['delivery'],'a'*64))
        for mutation in ('missing_step','wrong_restore','missing_image','stale_deployment','changed_asset','predeployment'):
            changed=copy.deepcopy(c);rec=changed['delivery']['shared_cms_edit_evidence']
            if mutation=='missing_step':rec['tasks'][0]['steps'].pop('save')
            elif mutation=='wrong_restore':rec['tasks'][0]['restored_value']='not restored'
            elif mutation=='missing_image':rec['tasks']=[t for t in rec['tasks'] if t['field']!='image']
            elif mutation=='changed_asset':changed['qa']['site_sha256']='b'*64
            elif mutation=='stale_deployment':rec['deployment_reference']='old'
            else:rec['checked_at']='2000-01-01T00:00:00Z'
            self.assertFalse(_shared_editor_evidence_complete(changed,changed['delivery'],'a'*64),mutation)


if __name__=='__main__':unittest.main()

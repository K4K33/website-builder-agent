"""No browser/network: adversarial integrity fixtures, not real live approval."""
import copy
import unittest
from tests.test_required_client_cms import delivery_fixture
from utils.published_experience import audit_published_experience
from utils.client_handover import inspect_client_delivery

class PublishedExperienceTests(unittest.TestCase):
    def test_complete_synthetic_observations_pass_record_integrity(self):
        self.assertTrue(audit_published_experience(delivery_fixture())['pass'])

    def test_direct_address_test_does_not_prove_click_works(self):
        c=delivery_fixture();c['delivery']['published_experience']['clicks'][0]['method']='goto'
        self.assertFalse(audit_published_experience(c)['pass'])

    def test_changed_url_without_changed_page_content_fails(self):
        c=delivery_fixture();c['delivery']['published_experience']['clicks'][0]['observed_heading']='Old homepage'
        self.assertFalse(audit_published_experience(c)['pass'])

    def test_correct_content_at_wrong_url_fails(self):
        c=delivery_fixture();c['delivery']['published_experience']['clicks'][0]['observed_url']='https://customer.example.org/wrong'
        self.assertFalse(audit_published_experience(c)['pass'])

    def test_missing_mobile_or_route_coverage_fails(self):
        for mode in ('mobile','route'):
            c=delivery_fixture()
            if mode=='mobile':c['delivery']['published_experience']['clicks'].pop()
            else:c['research']['site_architecture']['pages'].append({'path':'contact.html'})
            self.assertFalse(audit_published_experience(c)['pass'])

    def test_local_origin_and_different_host_do_not_prove_live_public_site(self):
        for url in ('http://terminal.local:4173/','https://terminal.local/','https://another.example.org/'):
            c=delivery_fixture();c['delivery']['published_experience']['clicks'][0]['source_url']=url
            self.assertFalse(audit_published_experience(c)['pass'])

    def test_observed_site_error_cannot_hide_behind_a_pass_flag(self):
        c=delivery_fixture();record=c['delivery']['published_experience']
        bad=copy.deepcopy(record['clicks'][0]);bad['site_errors']=['Router TypeError'];record['clicks'].append(bad)
        self.assertFalse(audit_published_experience(c)['pass'])

    def test_new_deployment_or_changed_asset_invalidates_old_results(self):
        for field,value in [('deployment_reference','new-deployment'),('site_sha256','b'*64),('build_version',4)]:
            c=delivery_fixture();c['delivery']['published_experience'][field]=value
            self.assertFalse(audit_published_experience(c)['pass'])

    def test_predeployment_observations_and_future_dates_fail(self):
        for tested in ('2000-01-01T00:00:00+00:00','2099-01-01T00:00:00+00:00'):
            c=delivery_fixture();c['delivery']['published_experience']['tested_at']=tested
            self.assertFalse(audit_published_experience(c)['pass'])

    def test_missing_changed_or_escaped_capture_blocks(self):
        for field,value in [('path','missing.png'),('path','../escape.png'),('sha256','0'*64)]:
            c=delivery_fixture();c['delivery']['published_experience']['clicks'][0]['capture'][field]=value
            self.assertFalse(audit_published_experience(c)['pass'])

    def test_draft_cannot_replace_real_source_form_even_with_other_green_flags(self):
        c=delivery_fixture();c['research']['source_inventory']={'pages':[{'url':'https://source.example.org/',
            'forms':[{'fields':[{'type':'email'},{'type':'textarea'}],'action':'/contact'}]}]}
        self.assertFalse(audit_published_experience(c)['pass'])
        contact=c['delivery']['published_experience']['contact']
        contact.update(mode='live_form',test_recipient_authorized=True,delivery_result='received',
                       receipt_reference='fixture://receipt',validation_feedback='pass',success_feedback='pass',error_feedback='pass')
        self.assertTrue(audit_published_experience(c)['pass'])
        contact['delivery_result']='draft_created'
        self.assertFalse(audit_published_experience(c)['pass'])

    def test_live_receipt_needs_authorized_recipient_and_error_feedback(self):
        for field,value in [('test_recipient_authorized',False),('error_feedback','unverified'),('receipt_reference','')]:
            c=delivery_fixture();contact=c['delivery']['published_experience']['contact']
            contact.update(mode='live_form',test_recipient_authorized=True,delivery_result='received',receipt_reference='fixture://receipt',validation_feedback='pass',success_feedback='pass',error_feedback='pass')
            contact[field]=value
            self.assertFalse(audit_published_experience(c)['pass'])

    def test_missing_records_cannot_be_bypassed_at_handover(self):
        c=delivery_fixture();del c['delivery']['published_experience']
        self.assertFalse(inspect_client_delivery(c)['ready_to_handover'])

    def test_honest_draft_can_be_reviewed_but_never_released_as_live_contact(self):
        c=delivery_fixture();contact=c['delivery']['published_experience']['contact']
        contact.update(mode='draft_only',draft_disclosure_verified=True)
        result=audit_published_experience(c)
        self.assertTrue(result['public_demo_ready'])
        self.assertFalse(result['pass'])
        self.assertFalse(inspect_client_delivery(c)['ready_to_handover'])
        contact['draft_disclosure_verified']=False
        self.assertFalse(audit_published_experience(c)['public_demo_ready'])

    def test_disclosure_cannot_excuse_broken_navigation(self):
        c=delivery_fixture();contact=c['delivery']['published_experience']['contact']
        contact.update(mode='draft_only',draft_disclosure_verified=True)
        c['delivery']['published_experience']['clicks'][0]['method']='goto'
        self.assertFalse(audit_published_experience(c)['public_demo_ready'])

    def test_malformed_click_fields_fail_without_crashing(self):
        for field in ('observed_url','source_url','clicked_href','target_route','viewport'):
            c=delivery_fixture();c['delivery']['published_experience']['clicks'][0][field]={}
            self.assertFalse(audit_published_experience(c)['pass'])

class DeliveryReceiptTests(unittest.TestCase):
    def fixture(self):
        import json
        from pathlib import Path
        from hashlib import sha256
        c=delivery_fixture();c['research']['premium_execution_protocol']='v1'
        record=c['delivery']['published_experience'];contact=record['contact']
        contact.update(mode='live_form',test_recipient_authorized=True,delivery_result='received',
            receipt_reference='synthetic-message',test_destination='authorized@example.org',
            validation_feedback='pass',success_feedback='pass',error_feedback='pass')
        receipt={'protocol':'contact-receipt-v1','scope':'authorized_delivery_test','channel':'email',
            'destination':contact['test_destination'],'message_reference':contact['receipt_reference'],
            'deployment_reference':c['delivery']['deployment_reference'],'received_at':record['tested_at']}
        path=Path(record['evidence_root'])/'backend.json';raw=json.dumps(receipt).encode();path.write_bytes(raw)
        contact['backend_receipt']={'path':'backend.json','sha256':sha256(raw).hexdigest()}
        return c,path,receipt

    def test_actual_private_export_required_and_bound_to_authorized_test(self):
        import json
        from hashlib import sha256
        c,path,receipt=self.fixture();self.assertTrue(audit_published_experience(c)['pass'])
        for key,value in [('scope','demo_storage'),('channel','demo_storage'),('destination','wrong'),
                          ('message_reference','wrong'),('deployment_reference','old'),('received_at','2000-01-01T00:00:00Z')]:
            changed=dict(receipt);changed[key]=value;raw=json.dumps(changed).encode();path.write_bytes(raw)
            c['delivery']['published_experience']['contact']['backend_receipt']['sha256']=sha256(raw).hexdigest()
            self.assertFalse(audit_published_experience(c)['pass'],key)

    def test_missing_tampered_or_escaped_receipt_never_passes(self):
        for mode in ('missing','tamper','escape'):
            c,path,receipt=self.fixture()
            if mode=='missing':path.unlink()
            elif mode=='tamper':path.write_text('{}')
            else:c['delivery']['published_experience']['contact']['backend_receipt']['path']='../backend.json'
            self.assertFalse(audit_published_experience(c)['pass'])

    def test_disclosed_demo_storage_is_reviewable_not_delivered(self):
        c,path,receipt=self.fixture();c['delivery']['published_experience']['contact'].update(
            mode='demo_storage',draft_disclosure_verified=True)
        result=audit_published_experience(c)
        self.assertTrue(result['public_demo_ready']);self.assertFalse(result['contact_pass'])

if __name__=='__main__':unittest.main()

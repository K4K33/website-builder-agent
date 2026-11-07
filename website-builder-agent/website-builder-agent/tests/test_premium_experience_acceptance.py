"""Service-wide counterexamples learned from Woode; no remote calls."""
import copy
import unittest
from tests.test_service_quality import fixture, reviews
from tests.test_required_client_cms import delivery_fixture
from utils.service_quality import audit_service_quality, validate_service_plan
from utils.client_handover import inspect_client_delivery

class PremiumExperienceTests(unittest.TestCase):
    def test_platform_plan_required_before_new_build(self):
        for field in ('editable_platform', 'portfolio_strategy', 'contact_continuity', 'cold_load_test_plan'):
            r,p=fixture();r['premium_experience_protocol']='v1'
            validate_service_plan(r)
            del r['premium_experience_plan'][field]
            with self.assertRaises(RuntimeError):validate_service_plan(r)

    def test_every_subpage_needs_new_information(self):
        r,p=fixture();r['premium_experience_protocol']='v1'
        r['site_architecture']['pages'].append({'path':'about.html'})
        with self.assertRaisesRegex(RuntimeError,'additional visitor value'):validate_service_plan(r)

    def test_old_or_generic_review_cannot_skip_story_loading_or_contact(self):
        for domain,check in [('visual','project_presentation'),('visual','new_information'),
                             ('visual','composition_comparison'),('technical','cold_load'),
                             ('technical','route_transition'),('commercial','contact_continuity')]:
            r,p=fixture();r['service_quality_reviews']=reviews(r,p)
            del r['service_quality_reviews'][domain]['route_results'][0]['checks'][check]
            self.assertFalse(audit_service_quality(p,r,artifact_digest='a'*64)['client_ready'])

    def test_changed_editable_plan_invalidates_review(self):
        r,p=fixture();r['service_quality_reviews']=reviews(r,p)
        r['premium_experience_plan']['preview_implementation']='separate-static-demo'
        self.assertFalse(audit_service_quality(p,r,artifact_digest='a'*64)['client_ready'])

    def test_zip_and_checkbox_cannot_certify_preview_cms_parity(self):
        c=delivery_fixture();c['delivery'].pop('preview_cms_parity')
        c['delivery']['theme_zip']='theme.zip'
        self.assertFalse(inspect_client_delivery(c)['ready_to_handover'])

    def test_cms_parity_needs_all_routes_and_all_capture_roles(self):
        for mutation in ('extra_route','missing_inventory','missing_capture','changed_hash',
                         'escape_path','missing_file','invalid_role','failed_layout','stale_build'):
            c=delivery_fixture();record=c['delivery']['preview_cms_parity'];row=record['routes'][0]
            if mutation=='extra_route':c['research']={'site_architecture':{'pages':[{'path':'index.html'},{'path':'contact.html'}]}}
            elif mutation=='missing_inventory':c.pop('research')
            elif mutation=='missing_capture':row['captures'].pop()
            elif mutation=='changed_hash':row['captures'][0]['sha256']='0'*64
            elif mutation=='escape_path':row['captures'][0]['path']='../outside.png'
            elif mutation=='missing_file':row['captures'][0]['path']='missing.png'
            elif mutation=='invalid_role':row['captures'][0]['role']=[]
            elif mutation=='failed_layout':row['layout_matches']=False
            else:record['build_version']=2
            self.assertFalse(inspect_client_delivery(c)['ready_to_handover'],mutation)

    def test_current_synthetic_evidence_passes_integrity_only(self):
        self.assertTrue(inspect_client_delivery(delivery_fixture())['ready_to_handover'])

if __name__=='__main__':unittest.main()

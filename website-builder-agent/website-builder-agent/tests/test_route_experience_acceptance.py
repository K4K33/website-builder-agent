"""Counterexamples for route/media and real input evidence gates."""
import copy
import unittest
from tests.test_service_quality import fixture, reviews
from utils.service_quality import audit_service_quality, validate_service_plan, service_brief

class RouteExperienceAcceptanceTests(unittest.TestCase):
    def ready(self):
        r, p = fixture()
        r['service_quality_reviews'] = reviews(r, p)
        return r, p

    def audit(self, r, p):
        return audit_service_quality(p, r, artifact_digest='a' * 64)

    def test_new_research_requires_all_route_plans_before_build(self):
        r, p = fixture(); r['route_experience_protocol'] = 'v1'
        validate_service_plan(r)
        r['site_architecture']['pages'].append({'path': 'venue.html'})
        with self.assertRaisesRegex(RuntimeError, 'Every route'):
            validate_service_plan(r)

    def test_missing_assets_survive_positive_review(self):
        r, p = fixture()
        r['route_experience_plan'][0]['missing_assets'] = ['Actual venue photo']
        r['service_quality_reviews'] = reviews(r, p)
        out = self.audit(r, p)
        self.assertFalse(out['client_ready'])
        self.assertIn('route_assets_missing', [x['kind'] for x in out['pending']])

    def test_flags_unknown_and_failed_motion_do_not_certify_runtime(self):
        for value in (True, {'result': 'pass'}, {'result': 'unverified', 'observation': 'No touch device'},
                      {'result': 'fail', 'observation': 'Scroll stalls'}):
            r, p = self.ready()
            r['service_quality_reviews']['technical']['route_results'][0]['checks']['touch_scroll'] = value
            self.assertFalse(self.audit(r, p)['client_ready'])

    def test_image_presence_cannot_replace_sufficiency_review(self):
        r, p = self.ready()
        del r['service_quality_reviews']['visual']['route_results'][0]['checks']['media_sufficiency']
        self.assertFalse(self.audit(r, p)['client_ready'])

    def test_route_coverage_and_environment_are_required(self):
        for mutation in ('missing', 'duplicate', 'device', 'browser', 'reference'):
            r, p = self.ready()
            rows = r['service_quality_reviews']['technical']['route_results']
            if mutation == 'missing': rows.clear()
            elif mutation == 'duplicate': rows.append(copy.deepcopy(rows[0]))
            else: rows[0]['evidence_reference' if mutation == 'reference' else mutation] = ''
            self.assertFalse(self.audit(r, p)['client_ready'])

    def test_mailto_needs_visible_email_fallback(self):
        r, p = fixture()
        p['index.html'] += '<a href="mailto:office@example.org">Email</a>'
        self.assertIn('email_fallback_missing', [x['kind'] for x in self.audit(r, p)['blocking']])
        p['index.html'] += '<p hidden>office@example.org</p>'
        self.assertIn('email_fallback_missing', [x['kind'] for x in self.audit(r, p)['blocking']])
        p['index.html'] += '<p>office@example.org</p>'
        self.assertNotIn('email_fallback_missing', [x['kind'] for x in self.audit(r, p)['blocking']])

    def test_composition_change_invalidates_review(self):
        r, p = self.ready(); before = service_brief(r)['contract_sha256']
        r['route_experience_plan'][0]['composition'] = 'Different composition'
        self.assertNotEqual(before, service_brief(r)['contract_sha256'])
        self.assertFalse(self.audit(r, p)['client_ready'])

    def test_observed_justified_static_treatment_can_pass(self):
        r, p = self.ready()
        self.assertTrue(self.audit(r, p)['client_ready'])

if __name__ == '__main__':
    unittest.main()

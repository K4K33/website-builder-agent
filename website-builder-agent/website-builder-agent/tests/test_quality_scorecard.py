"""Synthetic adversarial contracts, not real-company design validation."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from utils.quality_scorecard import DIMENSIONS, RUBRIC, quality_scorecard
from utils.blind_trials import (assess_new_company, reserve_blind_trial,
                               claim_trial_build, refuse_trial_revision, first_pass_metrics,
                               record_first_pass_qa, record_trial_review)


def review_fixture(score=9.5):
    bundle = {'artifact_sha256': 'a'*64, 'contract_sha256': 'b'*64,
              'items': [{'id': 'actual-capture'}]}
    review = {'rubric': RUBRIC, 'artifact_sha256': 'a'*64, 'contract_sha256': 'b'*64,
              'reviewer_id': 'separate-reviewer', 'independent_of_builder': True,
              'checked_at': '2026-11-05', 'open_issues': [],
              'scores': {key: {'score': score, 'rationale': 'Synthetic test only',
                                'evidence_ids': ['actual-capture']} for key, _ in DIMENSIONS}}
    return review, bundle


class QualityScorecardTests(unittest.TestCase):
    def evaluate(self, review, bundle, **kwargs):
        return quality_scorecard(review, artifact_digest='a'*64,
            contract_digest='b'*64, evidence_bundle=bundle, **kwargs)

    def test_exact_nine_equal_weights_and_half_up_display(self):
        r, b = review_fixture()
        for key, value in zip(r['scores'], [9, 7.5, 7.5, 7, 6.5, 6.5, 7.5, 5.5, 3]):
            r['scores'][key]['score'] = value
        out = self.evaluate(r, b)
        self.assertEqual(out['mean'], 60 / 9)
        self.assertEqual(out['display_mean'], '6.7')
        self.assertFalse(out['release_eligible'])
        r, b = review_fixture(6.25)
        self.assertEqual(self.evaluate(r, b)['display_mean'], '6.3')

    def test_rounded_95_cannot_pass(self):
        r, b = review_fixture(9.45)
        out = self.evaluate(r, b)
        self.assertEqual(out['display_mean'], '9.5')
        self.assertFalse(out['target_met'])

    def test_high_mean_never_erases_missing_business_task_or_handover(self):
        r, b = review_fixture(10)
        for kwargs in ({'blockers': ['lost shop']}, {'pending': ['CMS runtime untested']}):
            self.assertFalse(self.evaluate(r, b, **kwargs)['release_eligible'])
        r['open_issues'] = ['contact form incomplete']
        self.assertFalse(self.evaluate(r, b)['release_eligible'])

    def test_missing_scores_no_renormalized_mean_or_invented_zero(self):
        r, b = review_fixture(); del r['scores']['photography']
        out = self.evaluate(r, b)
        self.assertIsNone(out['mean'])
        self.assertFalse(out['complete'])

    def test_unknown_or_duplicate_replacement_dimensions_are_not_accepted(self):
        r, b = review_fixture(); r['scores']['extra'] = r['scores']['photography']
        self.assertFalse(self.evaluate(r, b)['complete'])

    def test_nonfinite_boolean_out_of_range_and_fake_evidence_rejected(self):
        for value in (float('nan'), float('inf'), True, 11, -1, '9.5'):
            r, b = review_fixture(); r['scores']['photography']['score'] = value
            self.assertFalse(self.evaluate(r, b)['complete'])
        r, b = review_fixture(); r['scores']['photography']['evidence_ids'] = ['imaginary']
        self.assertFalse(self.evaluate(r, b)['complete'])

    def test_stale_source_media_or_self_review_stays_unverified(self):
        for field, value in (('artifact_sha256', 'c'*64), ('contract_sha256', 'c'*64),
                             ('independent_of_builder', False)):
            r, b = review_fixture(); r[field] = value
            self.assertFalse(self.evaluate(r, b)['complete'])

    def test_real_review_metadata_can_pass_without_automated_score_creation(self):
        r, b = review_fixture()
        self.assertTrue(self.evaluate(r, b)['release_eligible'])
        self.assertIsNone(quality_scorecard()['mean'])

    def test_universal_audit_exposes_same_rubric_and_pending_gate(self):
        from utils.universal_quality import audit_universal_standards
        out = audit_universal_standards('<main><h1>Workshop</h1></main>')
        self.assertEqual(out['quality_scorecard']['rubric'], RUBRIC)
        self.assertIn('stable_quality_scorecard', out['pending_categories'])
        self.assertFalse(out['client_release_ready'])


class NewCompanyExperimentTests(unittest.TestCase):
    def test_version_suffix_unicode_alias_and_business_id_cannot_reuse_company(self):
        history = [{'slug': 'pyorahullu-v1', 'aliases': ['Pyörähullu'], 'business_id': '1234567-8'}]
        for candidate in ({'name': 'Pyörähullu'}, {'slug': 'pyorahullu-v2'},
                          {'name': 'Renamed business', 'y_tunnus': '1234567-8'}):
            self.assertFalse(assess_new_company(candidate, history=history)['eligible'])

    def test_every_known_checked_in_demo_and_latest_site_are_excluded(self):
        root = Path(__file__).resolve().parents[1]
        history = json.loads((root/'docs/KAURIVO_HISTORICAL_DEMO_TRIALS.json').read_text())['trials']
        for folder in (root/'docs/kaurivo/demos').iterdir():
            if folder.is_dir() and not folder.name.startswith('_'):
                self.assertFalse(assess_new_company({'slug': folder.name}, history=history)['eligible'], folder.name)
        self.assertFalse(assess_new_company({'name': 'New label', 'url': 'https://soitinkorjaamo.net/'}, history=history)['eligible'])

    def test_failed_generation_cannot_be_repeated_or_revised_as_first_pass(self):
        with TemporaryDirectory() as d:
            p = Path(d)/'registry.json'
            company = {'name': 'Fresh clinic', 'url': 'https://clinic.example.fi',
                       'quality_trial': {'mode': 'first_pass_unseen'}}
            reserve_blind_trial(company, slug='fresh-clinic', registry_path=p,
                               history_path=Path(d)/'history.json')
            claim_trial_build(company, slug='fresh-clinic', registry_path=p)
            with self.assertRaisesRegex(RuntimeError, 'new company'):
                claim_trial_build(company, slug='fresh-clinic', registry_path=p)
            with self.assertRaisesRegex(RuntimeError, 'new company'):
                refuse_trial_revision(company)
            refuse_trial_revision({'name': 'Real client project'})

    def test_direct_builder_and_import_cannot_bypass_consumed_trial(self):
        from agents import builder
        company = {'quality_trial': {'mode': 'first_pass_unseen'}}
        with patch('utils.blind_trials.claim_trial_build', side_effect=RuntimeError('already attempted')):
            with self.assertRaisesRegex(RuntimeError, 'already attempted'):
                builder.build_site('fresh', company)
            with patch.object(builder, '_resolve_company', return_value=('fresh', company)):
                with self.assertRaisesRegex(RuntimeError, 'already attempted'):
                    builder.run_build_from_response('fresh', '/missing.json', 'external')

    def test_parser_defaults_to_new_company_trials_with_explicit_client_exception(self):
        import main
        self.assertTrue(main.build_parser().parse_args(['pipeline']).benchmark_mode)
        self.assertFalse(main.build_parser().parse_args(['pipeline', '--client-project']).benchmark_mode)

    def test_sector_counts_do_not_hide_unreviewed_trials(self):
        out = first_pass_metrics([{'mode': 'first_pass_unseen', 'sector': sector}
                                  for sector in ('restaurant', 'workshop', 'workshop')])
        self.assertEqual(out['unreviewed'], 3)
        self.assertEqual(out['coverage_by_sector']['workshop']['trials'], 2)
        self.assertIsNone(out['pass_rate'])

    def test_independent_review_cannot_replace_first_build_or_original_grade(self):
        with TemporaryDirectory() as tmp:
            p = Path(tmp)/'registry.json'
            reserve_blind_trial({'name': 'New restaurant'}, registry_path=p,
                               history_path=Path(tmp)/'history.json')
            record_first_pass_qa(p, slug='new-restaurant', qa_report={'site_sha256': 'a'*64})
            qa = {'site_sha256': 'b'*64, 'overall_pass': False,
                  'universal_quality': {'quality_scorecard': {
                'complete': True, 'mean': 8, 'release_eligible': True}}}
            with self.assertRaisesRegex(RuntimeError, 'original first-pass'):
                record_trial_review(p, slug='new-restaurant', qa_report=qa)
            qa['site_sha256'] = 'a'*64
            self.assertTrue(record_trial_review(p, slug='new-restaurant', qa_report=qa))
            qa['universal_quality']['quality_scorecard']['mean'] = 10
            self.assertFalse(record_trial_review(p, slug='new-restaurant', qa_report=qa))
            self.assertEqual(json.loads(p.read_text())['trials'][0]['independent_quality_score'], 8)
            self.assertFalse(json.loads(p.read_text())['trials'][0]['release_eligible'])

    def test_high_mean_with_open_release_checks_does_not_count_as_success(self):
        out = first_pass_metrics([{'mode': 'first_pass_unseen', 'quality_evidence': 'verified',
            'independent_quality_score': 9.9, 'release_eligible': False}])
        self.assertEqual(out['over_95_first_pass'], 1)
        self.assertEqual(out['pass_rate'], 0)

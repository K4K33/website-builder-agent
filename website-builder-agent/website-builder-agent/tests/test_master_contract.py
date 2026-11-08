"""Design-Kehys-shaped counterexamples, not independent visual approval."""
import copy
import unittest
from unittest.mock import patch
from pathlib import Path
from utils.master_prompt import MASTER_PROMPT, MASTER_PROMPT_SHA256
from utils.service_quality import service_brief
from utils.source_identity import extract_price_faq_evidence, audit_price_faq_preservation
from utils.source_fidelity import source_manifest
from utils.fetch import extract_text_and_meta
from utils.master_audit import audit_site_contract
from utils.quality_scorecard import quality_scorecard
from tests.test_visual_asset_continuity import fixture
from tests.test_quality_scorecard import review_fixture


class MasterContractTests(unittest.TestCase):
    def test_research_builder_revision_and_qa_share_actual_master_text(self):
        from agents.builder import BUILD_SYSTEM_PROMPT, REVISE_SYSTEM_PROMPT
        from agents.research import FINAL_RESEARCH_PROMPT
        from agents.qa import SERVICE_QUALITY_POLICY
        for prompt in (BUILD_SYSTEM_PROMPT, REVISE_SYSTEM_PROMPT,
                       FINAL_RESEARCH_PROMPT, SERVICE_QUALITY_POLICY):
            self.assertIn(MASTER_PROMPT, prompt)

    def test_master_change_invalidates_exact_review_contract(self):
        old = service_brief({})
        self.assertEqual(old['master_prompt_sha256'], MASTER_PROMPT_SHA256)
        with patch('utils.service_quality.MASTER_PROMPT_SHA256', 'f'*64):
            new = service_brief({})
        self.assertNotEqual(old['contract_sha256'], new['contract_sha256'])

    def test_wordpress_heading_and_button_questions_survive_extraction(self):
        source = ''.join(f'<h3 class="accordion-title">Milloin työ {i} kannattaa korjata?</h3>' for i in range(10))
        source += '<button aria-expanded="false">Kuinka työ toimitetaan?</button>'
        evidence = extract_price_faq_evidence(source)
        research = {'source_inventory': {'pages': [{'url': 'https://example.org/conservation', 'price_faq_evidence': evidence}]}}
        output = '<main>'+''.join(f'<details><summary>Milloin työ {i} kannattaa korjata?</summary><p>Vastaus.</p></details>' for i in range(3))+'</main>'
        report = audit_price_faq_preservation({'index.html': output}, research)
        self.assertEqual(report['faq_questions_checked'], 11)
        self.assertEqual(len(report['missing']), 8)

    def test_same_question_count_cannot_hide_different_missing_topics(self):
        research = {'source_inventory': {'pages': [{'url': 'https://example.org/',
            'price_faq_evidence': {'faq_questions': ['Miten repeämä korjataan?']}}]}}
        report = audit_price_faq_preservation({'/': '<main><h2>Mitä huolto maksaa?</h2></main>'}, research)
        self.assertFalse(report['pass'])

    def test_native_collapsed_question_counts_but_hidden_and_script_copies_do_not(self):
        question = 'Voiko vanhan teoksen korjata?'
        research = {'source_inventory': {'pages': [{'url': 'https://example.org/',
            'price_faq_evidence': {'faq_questions': [question]}}]}}
        self.assertTrue(audit_price_faq_preservation({'/': '<details><summary>'+question+'</summary><p>Vastaus</p></details>'}, research)['pass'])
        for html in ('<script>'+question+'</script>', '<div hidden>'+question+'</div>',
                     '<div aria-hidden="true">'+question+'</div>'):
            self.assertFalse(audit_price_faq_preservation({'/': html}, research)['pass'])

    def test_large_source_does_not_drop_questions_prices_or_headings_at_caps(self):
        html = '<main>'+''.join(f'<h3>Kysymys numero {i}?</h3>' for i in range(95))
        html += '<table>'+''.join(f'<tr><td>Työ {i}</td><td>{i+10} €</td></tr>' for i in range(125))+'</table></main>'
        evidence = extract_price_faq_evidence(html)
        self.assertEqual(len(evidence['faq_questions']), 95)
        self.assertEqual(len(evidence['price_rows']), 125)
        parsed = extract_text_and_meta(html, base_url='https://example.org/')
        self.assertEqual(len(parsed['headings']['h3']), 95)
        manifest = source_manifest({'source_inventory': {'pages': [{'url': 'https://example.org/', **parsed}]}})
        self.assertEqual(len(manifest['pages'][0]['headings']), 95)

    def test_visual_only_preflight_cannot_certify_site_with_source_narration(self):
        from utils.visual_asset_continuity import audit_visual_continuity
        research, pages = fixture()
        pages['index.html'] = pages['index.html'].replace('</main>', '<p>Alkuperäisen sivuston kuvasarja näyttää työn.</p></main>')
        self.assertFalse(audit_visual_continuity(pages, research)['blocking'])
        whole = audit_site_contract(pages, research)
        self.assertIn('customer_facing_copy', whole['blocking']['universal'])
        self.assertFalse(whole['preflight_pass'])
        self.assertFalse(whole['client_release_ready'])

    def test_theme_archive_and_self_scores_do_not_establish_client_acceptance(self):
        research, pages = fixture()
        company = {'research': research, 'delivery': {'wordpress_zip': '/tmp/a-theme.zip'}}
        whole = audit_site_contract(pages, research, company=company)
        self.assertFalse(whole['client_release_ready'])
        self.assertTrue(any(whole['pending'].values()))
        self.assertIsNone(whole['quality_scorecard']['mean'])

    def test_eight_dimension_historical_review_is_not_renormalized_to_nine(self):
        review, bundle = review_fixture(10)
        del review['scores']['motion_scroll']
        review['rubric'] = 'kaurivo-eight-v1'
        out = quality_scorecard(review, artifact_digest='a'*64,
            contract_digest='b'*64, evidence_bundle=bundle)
        self.assertFalse(out['complete'])
        self.assertIsNone(out['mean'])
        self.assertFalse(out['release_eligible'])

    def test_mismatched_contract_and_empty_html_map_fail_closed(self):
        with self.assertRaises(ValueError):
            audit_site_contract({}, {})
        with self.assertRaises(ValueError):
            audit_site_contract({'/': '<main>Actual HTML</main>'}, {}, company={'research': {'changed': True}})


if __name__ == '__main__':
    unittest.main()

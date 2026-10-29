import contextlib
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch, Mock

import config
from agents import scout, builder, qa, research
from utils import claude_client, state
from utils.quality import canonical_url, normalize_facts, qualify_lead
from utils.browser_qa import inspect_site

HTML = '''<!DOCTYPE html><html lang="fi"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="description" content="Testiyritys"><title>Testiyritys</title>
<style>body{margin:0;padding:20px;font-family:Arial}main{max-width:800px}button{min-height:44px}</style>
</head><body><header><nav><a href="#main">Etusivu</a></nav></header>
<main id="main"><h1>Testiyritys</h1><p>Testisisältö.</p></main><footer>Testiyritys</footer></body></html>'''


def lead(score=8, confidence=.9):
    return {"name": "Testi", "website": "https://testi.fi", "technical_analysis": {"success": True},
            "screenshots": {"desktop": "desktop.png", "mobile": "mobile.png"},
            "ai_analysis": {"overall_opportunity_score": score, "confidence": confidence,
                            "redesign_recommended": True}}


def review():
    return {"content_ok": True, "issues": [], "visual_review": dict.fromkeys(
        ("desktop", "tablet", "mobile", "small_mobile", "brand_specificity", "typography", "hierarchy"), 90
    ) | {"blockers": [], "improvements": []}}


class QualityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for key, val in {"DATA_DIR": str(self.root / 'data'),
                         "COMPANIES_FILE": str(self.root / 'data/companies.json'),
                         "OUTPUT_DIR": str(self.root / 'output')}.items():
            p = patch.object(config, key, val); p.start(); self.addCleanup(p.stop)

    def test_url_deduplication(self):
        self.assertEqual(canonical_url('http://www.testi.fi/?utm=a'), 'https://testi.fi')
        for url in ('javascript:alert(1)', 'https://facebook.com/testi', 'https://x:secret@testi.fi'):
            self.assertEqual(canonical_url(url), '')

    def test_industry_actually_changes_query(self):
        self.assertIn('"restaurant"', scout._build_overpass_query('ravintola', 'Tampere'))
        self.assertNotIn('hairdresser', scout._build_overpass_query('ravintola', 'Tampere'))

    def test_invalid_search_fails_before_network(self):
        with patch.object(scout, '_fetch_osm_companies') as fetch:
            for industry, location in (('', ''), ('nonsense', 'Tampere'), ('ravintola', '')):
                with self.assertRaises(ValueError): scout.scout(1, industry, location)
            fetch.assert_not_called()

    def test_location_escaped(self):
        self.assertIn(json.dumps('City";out;', ensure_ascii=False),
                      scout._build_overpass_query('ravintola', 'City";out;'))

    def test_persistence_preserves_builds_and_returns_pipeline_slug(self):
        state.upsert_company('old', {'name': 'Old', 'url': 'https://old.fi', 'status': 'approved', 'build': {'version': 5}})
        stored = scout._save_company(lead(), config.COMPANIES_FILE)
        self.assertEqual(stored['slug'], 'testi')
        self.assertEqual(state.load_companies()['old']['build']['version'], 5)
        self.assertEqual(state.get_company('testi')[1]['url'], 'https://testi.fi')
        self.assertIsNone(scout._save_company(lead(), config.COMPANIES_FILE))

    def test_corrupt_state_is_not_silently_overwritten(self):
        Path(config.DATA_DIR).mkdir()
        Path(config.COMPANIES_FILE).write_text("{corrupt")
        with self.assertRaises(RuntimeError): scout._save_company(lead(), config.COMPANIES_FILE)
        self.assertEqual(Path(config.COMPANIES_FILE).read_text(), "{corrupt")

    def test_http_only_prospect_keeps_original_fetch_url(self):
        self.assertEqual(scout._normalize_url("http://testi.fi"), "http://testi.fi")

    def test_same_name_different_business_not_overwritten(self):
        first = scout._save_company(lead(), config.COMPANIES_FILE)
        second = scout._save_company(lead() | {'website': 'https://another.fi'}, config.COMPANIES_FILE)
        self.assertNotEqual(first['slug'], second['slug'])

    def test_failed_or_weak_analysis_never_becomes_qualified(self):
        self.assertTrue(qualify_lead(lead())['eligible'])
        for item in (lead(3), lead(8,.2), lead(True), lead() | {'ai_analysis': {'error':'timeout'}},
                     lead() | {'screenshots': {}}, lead() | {'technical_analysis': {'success': False}}):
            self.assertFalse(qualify_lead(item)['eligible'])

    def test_scout_ranks_qualified_candidates(self):
        candidates = [lead(6), lead(9) | {'name':'Best','website':'https://best.fi'}, lead(3)]
        for item in candidates: item['qualification'] = qualify_lead(item)
        with patch.object(scout, '_fetch_osm_companies', return_value=candidates), patch.object(
                scout, '_analyze_candidates', return_value=candidates):
            result = scout.scout(1, 'ravintola', 'Tampere')
        self.assertEqual([item['name'] for item in result], ['Best'])

    def test_nested_contact_schema_reaches_builder(self):
        facts = {'contact': {'phone': '+358 40 1234567','email':'a@testi.fi'}, 'tagline_or_value_prop':'Testi'}
        self.assertIn('a@testi.fi', builder._safe_fact_summary(facts))
        builder._validate_generated_content('<a href="mailto:a@testi.fi">Ota yhteyttä</a>', facts)
        self.assertEqual(normalize_facts(facts)['tagline'], 'Testi')

    def test_invented_contact_rejected_even_with_real_contact_available(self):
        with self.assertRaises(RuntimeError):
            builder._validate_generated_content('<a href="mailto:fake@testi.fi">Ota yhteyttä</a>',
                                                {'contact': {'email':'real@testi.fi'}})

    def test_external_agent_completion_records_provenance_without_ai_call(self):
        state.upsert_company('testi', {'research':{'company_facts':{'name':'Testi'}},
                                      'qa':{'overall_pass':True}})
        response = self.root / 'response.html'; response.write_text(HTML)
        with patch.object(builder, 'ask_claude') as ask:
            path = builder.run_build_from_response('testi', str(response), 'Work agent')
            ask.assert_not_called()
        saved = state.get_company('testi')[1]
        self.assertEqual(saved['build']['generation_mode'], 'external_agent_response')
        self.assertEqual(saved['build']['producer'], 'Work agent')
        self.assertIsNone(saved['qa'])
        self.assertEqual(saved['status'], 'built')
        self.assertTrue(Path(path).exists())

    def test_external_response_needs_research_and_fact_checks(self):
        state.upsert_company('testi', {'name':'Testi'})
        response = self.root / 'response.html'; response.write_text(HTML)
        with self.assertRaises(RuntimeError):
            builder.run_build_from_response('testi', str(response), 'Work agent')
        state.upsert_company('testi', {'research':{'company_facts':{'name':'Testi'}}})
        response.write_text(HTML.replace('</main>','<a href="mailto:invented@fake.fi">Contact</a></main>'))
        with self.assertRaises(RuntimeError):
            builder.run_build_from_response('testi', str(response), 'Work agent')

    def test_invalid_revision_does_not_overwrite_work(self):
        path = builder._write_html('testi', HTML)
        with self.assertRaises(RuntimeError): builder._write_html('testi', HTML.replace('#main','#missing'))
        self.assertEqual(Path(path).read_text(), HTML)

    def test_static_checks_reject_fake_interactions_and_dependencies(self):
        self.assertTrue(qa._automated_checks(HTML)['automated_pass'])
        for invalid in ('<a href="#">Varaa aika</a>', '<form><input></form>', '<img src="//bad.fi/x" alt="">',
                        '<style>@import "remote.css";</style>', '<iframe src="https://bad.fi"></iframe>'):
            self.assertFalse(qa._automated_checks(HTML.replace('</main>', invalid+'</main>'))['automated_pass'])

    def test_visual_gate_validates_types_and_all_dimensions(self):
        self.assertTrue(qa.review_passes(review()))
        for change in ({'content_ok':'true'}, {'issues':['invented fact']}, {'visual_review':{}}):
            self.assertFalse(qa.review_passes(review() | change))
        for value in (84, True, 101, '90'):
            item = review(); item['visual_review']['mobile'] = value
            self.assertFalse(qa.review_passes(item))

    def test_model_requires_explicit_quality_selection(self):
        with patch.dict(os.environ, {'BUILDER_MODEL':'','QA_MODEL':''}), patch.object(config,'OPENROUTER_MODEL','openrouter/free'):
            with self.assertRaises(RuntimeError): config.model_for_stage('builder')
            with self.assertRaises(RuntimeError): config.model_for_stage('qa')
        with patch.dict(os.environ, {'BUILDER_MODEL':'provider/test-model'}):
            self.assertEqual(config.model_for_stage('builder'), 'provider/test-model')

    def test_truncated_nonempty_response_not_accepted(self):
        response = Mock(status_code=200)
        response.json.return_value = {'choices':[{'message':{'content':'<html>partial'},'finish_reason':'length'}]}
        with patch.object(claude_client,'_get_headers',return_value={}), patch.object(
                claude_client.resource_manager,'reserve',return_value=True), patch.object(
                claude_client.requests,'post',return_value=response):
            with self.assertRaisesRegex(RuntimeError,'truncated'):
                claude_client.ask_claude('s','u',max_retries=1)

    def test_json_mode_and_stage_forwarded(self):
        with patch.object(claude_client,'ask_claude',return_value='{"ok":true}') as call:
            self.assertEqual(claude_client.ask_claude_json('s','u',stage='qa'), {'ok':True})
            self.assertTrue(call.call_args.kwargs['json_mode'])
            self.assertEqual(call.call_args.kwargs['stage'], 'qa')

    def test_browser_failure_cannot_pass_qa(self):
        path = builder._write_html('testi', HTML)
        state.upsert_company('testi', {'build': {'output_path':path,'version':1}})
        with patch.object(qa,'inspect_site',return_value={'pass':False,'issues':['browser missing'],'screenshots':{}}), patch.object(
                qa,'ask_claude_json') as ask:
            self.assertFalse(qa.run_qa('testi')['overall_pass'])
            ask.assert_not_called()

    def test_visual_qa_receives_all_rendered_views(self):
        path = builder._write_html('testi', HTML)
        state.upsert_company('testi', {'build': {'output_path':path,'version':1},'research':{'company_facts':{}}})
        shots = {k:k+'.png' for k in ('desktop','tablet','mobile','small_mobile')}
        with patch.object(qa,'inspect_site',return_value={'pass':True,'issues':[],'screenshots':shots}), patch.object(
                qa,'ask_claude_json',return_value=review()) as ask:
            self.assertTrue(qa.run_qa('testi')['overall_pass'])
            self.assertEqual(len(ask.call_args.kwargs['image_paths']), 4)
            self.assertEqual(ask.call_args.kwargs['stage'], 'qa')

    def test_stale_qa_cannot_be_approved(self):
        state.upsert_company('testi', {'status':'qa_passed','build':{'version':2},
                                    'qa':{'overall_pass':True,'build_version':1}})
        with self.assertRaises(RuntimeError): qa.approve_company('testi')

    def test_design_pass_cannot_modify_company_facts(self):
        state.upsert_company('testi', {'name':'Testi','url':'https://testi.fi'})
        extracted = {'company_facts':{'name':'Testi','services':['Oikea palvelu']}}
        brief = {'company_facts':{'name':'Invented','services':['Fake service']}}
        with patch.object(research,'analyze_url',return_value={'success':True,'visible_text':'Oikea palvelu'}), patch.object(
                research,'_search_tavily',return_value=[]), patch.object(
                research,'ask_claude_json',side_effect=[extracted,brief]):
            research.run_research('testi')
        saved = state.get_company('testi')[1]
        self.assertEqual(saved['research']['company_facts']['services'], ['Oikea palvelu'])
        self.assertEqual(saved['name'], 'Testi')


class BrowserTests(unittest.TestCase):
    def test_render_overflow_and_menu(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'index.html'; path.write_text(HTML)
            result = inspect_site(path)
            if any('Browser QA unavailable' in issue for issue in result['issues']):
                if os.getenv('REQUIRE_BROWSER_TESTS') == '1': self.fail(str(result['issues']))
                self.skipTest('Chromium not installed')
            self.assertTrue(result['pass'], result)
            self.assertEqual(len(result['screenshots']), 4)
            path.write_text(HTML.replace('<main id="main">', '<main id="main" style="width:1800px;max-width:none">'))
            self.assertFalse(inspect_site(path)['pass'])
            broken_menu = '<button aria-controls="menu" aria-expanded="false">Valikko</button><div id="menu" hidden>Test</div>'
            path.write_text(HTML.replace('</main>', broken_menu+'</main>'))
            self.assertTrue(any('aria-expanded' in issue for issue in inspect_site(path)['issues']))


if __name__ == '__main__':
    unittest.main()

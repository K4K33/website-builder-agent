"""Pipeline/import/approval wiring without API calls or paid model configuration."""
import json
from pathlib import Path
import re
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from tests.test_concept_previews import fixture, fake_renderer, selection_report
from utils.concept_previews import write_concepts, load_verified_set
from utils.concept_workflow import generate_concepts, choose_concept


class ConceptWorkflowTests(unittest.TestCase):

    def test_unsourced_numeric_claim_is_removed_without_affecting_verified_copy(self):
        from bs4 import BeautifulSoup
        from agents.builder import _validate_generated_content
        from utils.concept_fact_recovery import prepare_verified_concept_copy

        page = ('<!doctype html><html><body><main>'
                '<h1>Yritysesittely yli <strong>88</strong> vuoden kokemuksella</h1>'
                '<p>Vahvistettu esittely säilyy.</p></main></body></html>')
        result = prepare_verified_concept_copy(
            page, {'name': 'Vahvistettu Oy'}, _validate_generated_content)
        dom = BeautifulSoup(result, 'html.parser')
        self.assertEqual(dom.select_one('h1').get_text(' ', strip=True), 'Yritysesittely')
        self.assertIn('Vahvistettu esittely säilyy.', result)
        self.assertNotIn('88', result)
        _validate_generated_content(result, {'name': 'Vahvistettu Oy'})

    def test_verified_claim_is_unchanged_and_other_false_content_still_fails(self):
        from agents.builder import _validate_generated_content
        from utils.concept_fact_recovery import prepare_verified_concept_copy

        verified = '<main><h1>Yli 35 vuoden kokemus</h1></main>'
        inventory = {'root_url': 'https://source.example', 'pages': [
            {'url': 'https://source.example/about', 'text': 'Yli 35 vuoden kokemus'}
        ]}
        def validate(page, facts):
            _validate_generated_content(page, facts, source_inventory=inventory)
        self.assertEqual(prepare_verified_concept_copy(verified, {}, validate), verified)
        with self.assertRaisesRegex(RuntimeError, 'keksineen palvelusisältöä'):
            prepare_verified_concept_copy(
                '<main><h1>Tarjoamme palveluita</h1></main>', {}, validate)

    def test_queued_concept_cleans_fake_numeric_claim_without_second_model_call(self):
        research, data = fixture()
        company = {'research': research}
        pages = [page for concept in data['concepts'].values() for page in concept['pages'].values()]
        calls = []

        def respond(system, prompt, **kwargs):
            self.assertNotIn('Required correction:', system)
            index = len(calls)
            calls.append(index)
            html = pages[index]
            if index == 0:
                html = html.replace('</main>',
                    '<p>Yli 88 vuoden kokemus</p></main>')
            return {'html': html}

        with TemporaryDirectory() as folder, \
             patch.dict('os.environ', {'KAURIVO_QUEUED_DEMO_ID': 'numeric-job'}), \
             patch('utils.concept_workflow.get_company', return_value=('studio', company)), \
             patch('utils.concept_workflow.upsert_company'), \
             patch('utils.concept_workflow.config.OUTPUT_DIR', folder), \
             patch('utils.concept_workflow.config.model_for_stage', return_value='fixture-model'), \
             patch('utils.browser_qa.inspect_site', side_effect=fake_renderer), \
             patch('utils.claude_client.ask_claude_json', side_effect=respond) as model:
            result = generate_concepts('studio')
            self.assertEqual(result['status'], 'ready_for_comparison')
            self.assertEqual(model.call_count, 6)


    def test_revises_only_browser_rejected_concept_route_and_renders_again(self):
        research, data = fixture()
        company = {'research': research}
        pages = [page for concept in data['concepts'].values()
                 for page in concept['pages'].values()]
        calls = []

        def respond(system, prompt, **kwargs):
            if 'observed_browser_failures' in prompt:
                self.assertIn('Fix measurable WCAG AA text/background contrast', prompt)
                calls.append('revision')
                return {'html': pages[0]}
            index = len(calls)
            self.assertLess(index, 6)
            calls.append('initial')
            html = pages[index]
            if index == 0:
                html = html.replace('</style>', '/* needs-browser-revision */</style>')
            return {'html': html}

        def review_browser(file, **kwargs):
            report = fake_renderer(file, **kwargs)
            if 'needs-browser-revision' in Path(file).read_text(encoding='utf-8'):
                report['issues'] = ['desktop: measurable WCAG AA text contrast failures']
                report['pass'] = False
            return report

        with TemporaryDirectory() as folder, \
             patch.dict('os.environ', {'KAURIVO_QUEUED_DEMO_ID': 'browser-job'}), \
             patch('utils.concept_workflow.get_company',
                   return_value=('studio', company)), \
             patch('utils.concept_workflow.upsert_company'), \
             patch('utils.concept_workflow.config.OUTPUT_DIR', folder), \
             patch('utils.concept_workflow.config.model_for_stage',
                   return_value='fixture-model'), \
             patch('utils.browser_qa.inspect_site', side_effect=review_browser), \
             patch('utils.claude_client.ask_claude_json', side_effect=respond):
            result = generate_concepts('studio')
            self.assertEqual(result['status'], 'ready_for_comparison')
            self.assertEqual(calls, ['initial'] * 6 + ['revision'])
            self.assertFalse(result['repair_targets'])

    def test_unrepaired_browser_issue_cannot_be_marked_ready(self):
        research, data = fixture()
        company = {'research': research}
        pages = [page for concept in data['concepts'].values()
                 for page in concept['pages'].values()]
        calls = []

        def respond(system, prompt, **kwargs):
            if 'observed_browser_failures' in prompt:
                calls.append('revision')
                return {'html': pages[0].replace('</style>',
                                                 '/* needs-browser-revision */</style>')}
            index = len(calls)
            calls.append('initial')
            html = pages[index]
            if index == 0:
                html = html.replace('</style>', '/* needs-browser-revision */</style>')
            return {'html': html}

        def browser(file, **kwargs):
            report = fake_renderer(file, **kwargs)
            if 'needs-browser-revision' in Path(file).read_text(encoding='utf-8'):
                report['issues'] = ['mobile: horizontal overflow']
                report['pass'] = False
            return report

        with TemporaryDirectory() as folder, \
             patch.dict('os.environ', {'KAURIVO_QUEUED_DEMO_ID': 'browser-bad'}), \
             patch('utils.concept_workflow.get_company',
                   return_value=('studio', company)), \
             patch('utils.concept_workflow.upsert_company'), \
             patch('utils.concept_workflow.config.OUTPUT_DIR', folder), \
             patch('utils.concept_workflow.config.model_for_stage',
                   return_value='fixture-model'), \
             patch('utils.browser_qa.inspect_site', side_effect=browser), \
             patch('utils.claude_client.ask_claude_json', side_effect=respond), \
             self.assertRaisesRegex(RuntimeError,
                 'CONCEPT_BROWSER_VALIDATION_BLOCKED'):
            generate_concepts('studio')
        self.assertEqual(calls, ['initial'] * 6 + ['revision'] * 2)

    def test_queue_repairs_unverified_contact_before_rendering(self):
        research, data = fixture()
        company = {'research': research}
        pages = [page for concept in data['concepts'].values() for page in concept['pages'].values()]
        calls = []

        def respond(system, prompt, **kwargs):
            if 'Required correction:' in system:
                self.assertIn('Unverified email link', system)
                return {'html': pages[0]}
            attempt = len(calls)
            calls.append(re.search(r'This call only authors ([^ ]+)\.', system)[1])
            draft = pages[attempt]
            if attempt == 0:
                draft = draft.replace('</main>', '<a href="mailto:unknown@example.org">Email</a></main>')
            return {'html': draft}

        with TemporaryDirectory() as folder, \
             patch.dict('os.environ', {'KAURIVO_QUEUED_DEMO_ID': 'fixture-job'}), \
             patch('utils.concept_workflow.get_company', return_value=('studio', company)), \
             patch('utils.concept_workflow.upsert_company'), \
             patch('utils.concept_workflow.config.OUTPUT_DIR', folder), \
             patch('utils.concept_workflow.config.model_for_stage', return_value='fixture-model'), \
             patch('utils.browser_qa.inspect_site', side_effect=fake_renderer), \
             patch('utils.claude_client.ask_claude_json', side_effect=respond) as model:
            result = generate_concepts('studio')
            self.assertEqual(result['status'], 'ready_for_comparison')
            self.assertEqual(model.call_count, 7)

    def test_model_workflow_uses_json_generation_and_all_twelve_real_images(self):
        research, data = fixture()
        company = {'research':research}
        with TemporaryDirectory() as folder:
            def save(slug, changes):company.update(changes);return company
            def respond(system, user, **kwargs):
                if kwargs['stage'] == 'builder':
                    requested=json.loads(user)['exact_direction_id']
                    return {'concepts':{requested:data['concepts'][requested]}}
                self.assertEqual(len(kwargs['image_paths']),12)
                self.assertTrue(all(Path(p).is_file() for p in kwargs['image_paths']))
                self.assertNotIn('creative_selection',user)
                _,manifest=load_verified_set(company['concept_previews'],company['research'],
                                              allowed_root=Path(folder)/'studio')
                return selection_report(manifest)
            with patch('utils.concept_workflow.get_company',side_effect=lambda name:('studio',company)), \
                 patch('utils.concept_workflow.upsert_company',side_effect=save), \
                 patch('utils.concept_workflow.config.OUTPUT_DIR',folder), \
                 patch('utils.concept_workflow.config.model_for_stage',return_value='fixture-model'), \
                 patch('utils.browser_qa.inspect_site',side_effect=fake_renderer), \
                 patch('agents.builder._validate_generated_content'), \
                 patch('utils.claude_client.ask_claude_json',side_effect=respond) as model:
                generate_concepts('studio')
                choose_concept('studio')
                self.assertEqual(model.call_count,4)

    def test_each_concept_is_requested_separately_to_prevent_truncation(self):
        research, data = fixture(); company={'research': research}; calls=[]
        with TemporaryDirectory() as folder:
            def respond(system,user,**kwargs):
                packet=json.loads(user); calls.append(packet['exact_direction_id'])
                identifier=packet['exact_direction_id']
                return {'concepts': {identifier: data['concepts'][identifier]}}
            with patch('utils.concept_workflow.get_company',return_value=('studio',company)), \
                 patch('utils.concept_workflow.upsert_company',side_effect=lambda s,c:company.update(c) or company), \
                 patch('utils.concept_workflow.config.OUTPUT_DIR',folder), \
                 patch('utils.concept_workflow.config.backend_for_stage',return_value='openrouter'), \
                 patch('utils.concept_workflow.config.model_for_stage',return_value='fixture-model'), \
                 patch('utils.browser_qa.inspect_site',side_effect=fake_renderer), \
                 patch('agents.builder._validate_generated_content'), \
                 patch('utils.claude_client.ask_claude_json',side_effect=respond):
                generate_concepts('studio')
        from utils.creative_directions import validate_creative_directions
        self.assertEqual(calls, [x['id'] for x in validate_creative_directions(research)['alternatives']])

    def test_external_authoring_and_selection_work_without_model_calls(self):
        research, data=fixture()
        with TemporaryDirectory() as folder:
            root=Path(folder); response=root/'response.json'; response.write_text(json.dumps(data))
            company={'research':research}
            def get(name):return 'studio',company
            def save(slug,changes):company.update(changes);return company
            with patch('utils.concept_workflow.get_company',side_effect=get), \
                 patch('utils.concept_workflow.upsert_company',side_effect=save), \
                 patch('utils.concept_workflow.config.OUTPUT_DIR',folder), \
                 patch('utils.browser_qa.inspect_site',side_effect=fake_renderer), \
                 patch('agents.builder._validate_generated_content'), \
                 patch('utils.claude_client.ask_claude') as model, \
                 patch('utils.claude_client.ask_claude_json') as judge:
                ref=generate_concepts('studio',response_path=response,producer='external-fixture')
                _,m=load_verified_set(ref,research,allowed_root=root/'studio')
                report=root/'review.json';report.write_text(json.dumps(selection_report(m)))
                result=choose_concept('studio',review_path=report,reviewer='external-fixture-review')
                self.assertEqual(company['research']['creative_selection'],result['choice'])
                self.assertFalse(result['premium_approval'])
                model.assert_not_called();judge.assert_not_called()

    def test_imported_authoring_requires_named_producer(self):
        research,data=fixture()
        with TemporaryDirectory() as folder:
            response=Path(folder)/'response.json';response.write_text(json.dumps(data))
            with patch('utils.concept_workflow.get_company',return_value=('studio',{'research':research})), \
                 patch('utils.concept_workflow.config.OUTPUT_DIR',folder), \
                 self.assertRaisesRegex(RuntimeError,'producer'):
                generate_concepts('studio',response_path=response)

    def test_cli_has_explicit_no_model_import_and_material_collection_commands(self):
        from main import build_parser
        parser=build_parser()
        self.assertEqual(parser.parse_args(['concept-previews','studio','--response','draft.json','--producer','external']).response,'draft.json')
        self.assertEqual(parser.parse_args(['choose-concept','studio','--review','review.json','--reviewer','human']).review,'review.json')
        self.assertEqual(parser.parse_args(['review-material','studio']).company,'studio')

    def test_full_build_is_not_called_before_new_protocol_concepts(self):
        from agents import builder
        company={'research':{'visual_concepts_protocol':'v1'},'concept_previews':{}}
        with patch('agents.builder._resolve_company',return_value=('studio',company)), \
             patch('utils.concept_workflow.generate_concepts',side_effect=RuntimeError('models unavailable')), \
             patch('agents.builder.build_site') as full:
            with self.assertRaisesRegex(RuntimeError,'models unavailable'):builder.run_build('studio')
            full.assert_not_called()

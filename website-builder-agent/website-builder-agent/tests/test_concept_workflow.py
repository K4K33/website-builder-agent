"""Pipeline/import/approval wiring without API calls or paid model configuration."""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch
from tests.test_concept_previews import fixture, fake_renderer, selection_report
from utils.concept_previews import write_concepts, load_verified_set
from utils.concept_workflow import generate_concepts, choose_concept


class ConceptWorkflowTests(unittest.TestCase):
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

"""Real free-LLM JSON syntax recovery; never fabricate company facts.

Prismarit cloud run 43396567058 failed at claude_client.py:554 due
to a free model returning invalid JSON despite response_format=json.
No paid calls or untrusted raw response logging may be introduced.
"""
from __future__ import annotations
from pathlib import Path
from unittest.mock import patch
import unittest

from utils.kaurivo_free_json_envelope import (
    parse_complete_model_json, InvalidModelJSON,
)
from utils.claude_client import ask_claude_json

ROOT=Path(__file__).resolve().parents[1]
SOURCE=(ROOT/"utils/claude_client.py").read_text(encoding="utf-8")


class FreeStructuredJSONTests(unittest.TestCase):
    def test_strict_valid_json_keeps_exact_source_facts(self):
        raw='{"company_facts":{"name":"Prismarit Oy","industry":"laserkeilaus"},"quotes":["Exact quoted phrase"]}'
        self.assertEqual(parse_complete_model_json(raw),{
            "company_facts":{"name":"Prismarit Oy","industry":"laserkeilaus"},
            "quotes":["Exact quoted phrase"]
        })

    def test_fenced_and_intro_wrappers_do_not_block_real_data(self):
        cases=[
            '```json\n{"selected":[{"url":"https://operator.example.org/","same_industry":true}]}\n```',
            'Here is the sourced JSON:\n{"selected":[{"url":"https://operator.example.org/","same_industry":true}]}\nDone.',
            '{"selected":[{"url":"https://operator.example.org/","same_industry":true}]}\nNote: JSON above.',
            '{"selected":[{"url":"https://operator.example.org/","same_industry":true,},]}',
        ]
        for raw in cases:
            with self.subTest(raw=raw[:30]):
                out=parse_complete_model_json(raw)
                self.assertEqual(out["selected"][0]["url"],
                                 "https://operator.example.org/")
                self.assertIs(out["selected"][0]["same_industry"], True)

    def test_embedded_commas_inside_original_quotes_are_not_changed(self):
        result=parse_complete_model_json(
            '{"evidence_quote":"Menu: coffee, cake, and tea", "other":[1,2,]}')
        self.assertEqual(result["evidence_quote"],"Menu: coffee, cake, and tea")
        self.assertEqual(result["other"],[1,2])

    def test_truncated_or_ambiguous_outputs_fail_closed(self):
        invalids=[
            '{"company_facts":{"name":"Missing"',
            '{"selected":',
            '{"fact":"first"}\n{"fact":"second"}',
            '{"fact":"first"}\n[{"fact":"second"}]',
            "",
            "only a description of a site, no JSON",
        ]
        for raw in invalids:
            with self.subTest(raw=raw[:30]):
                with self.assertRaises(InvalidModelJSON):
                    parse_complete_model_json(raw)

    def test_caller_recovers_without_any_second_model_call(self):
        raw='Answer:\n{"company_facts":{"name":"Prismarit Oy",},}\nEnd.'
        with patch("utils.claude_client.ask_claude",return_value=raw) as ask:
            result=ask_claude_json("source-bound facts","observed source",
                                   stage="research",max_tokens=3500)
        self.assertEqual(result["company_facts"]["name"],"Prismarit Oy")
        ask.assert_called_once()

    def test_invalid_model_output_never_leaks_raw_source_text(self):
        private="PRIVATE_CUSTOMER_MARKER_NOT_IN_LOGS"
        with patch("utils.claude_client.ask_claude",
                   return_value='{"broken":'+private) as ask:
            with self.assertRaises(RuntimeError) as err:
                ask_claude_json("source","original",stage="research")
        self.assertIn("AI ei palauttanut validia JSONia",str(err.exception))
        self.assertNotIn(private,str(err.exception))
        self.assertNotIn("---Raaka vastaus---",SOURCE)
        self.assertEqual(ask.call_count,1)


if __name__=="__main__":
    unittest.main()

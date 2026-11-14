"""Generic, offline new-firm Research recovery — no public APIs or real clients."""
from __future__ import annotations

from copy import deepcopy
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import Mock, patch

from tests.test_creative_multipage_originality import creative
from utils.creative_brief_recovery import ensure_creative_directions
from utils.creative_directions import validate_creative_directions
from utils.kaurivo_research_progress import get_progress, save_progress

GOOD=creative()
FACTS={"name":"Example Forest Workshop", "industry":"Carpentry",
       "services":["Locally verified furniture repairs"]}
ANCHORS=[{"source":"https://example.invalid/","evidence":"Source-confirmed repair service"}]


class BoundedCreativeRepairTests(TestCase):
    def test_already_valid_avoids_any_additional_model_call(self):
        original={**GOOD,"company_facts":deepcopy(FACTS),"unrelated_sourced_prices":["123 €"]}
        model=Mock()
        result=ensure_creative_directions(
            original,company_facts=FACTS,source_anchors=ANCHORS,repair_json=model)
        self.assertIs(result,original)
        model.assert_not_called()

    def test_only_creative_fields_change_and_full_checks_still_apply(self):
        source={"creative_directions":[],"creative_selection":{},
                "company_facts":deepcopy(FACTS),
                "source_inventory":{"pages":[{"url":"https://example.invalid/",
                                               "text":"Real company source evidence"}]},
                "original_brand_logo":"source-locked.svg",
                "pricing_conditions":["Source-confirmed extras"]}
        before=deepcopy(source)
        repair=Mock(return_value=deepcopy(GOOD))
        result=ensure_creative_directions(
            source,company_facts=FACTS,source_anchors=ANCHORS,repair_json=repair)
        validate_creative_directions(result)
        self.assertEqual(repair.call_count,1)
        kwargs=repair.call_args.kwargs
        self.assertEqual(kwargs["stage"],"research")
        self.assertEqual(kwargs["max_tokens"],4500)
        self.assertEqual({key:result[key] for key in before
                          if key not in GOOD},
                         {key:before[key] for key in before
                          if key not in GOOD})
        self.assertEqual(source,before,"Source draft cannot be mutated by repair")

    def test_model_must_not_rewrite_source_facts_or_relax_3_concepts(self):
        invalid=deepcopy(GOOD)
        invalid["creative_directions"]=[]
        model=Mock(side_effect=[
            {**GOOD,"company_facts":{"name":"Invented brand"}},
            {"creative_directions":GOOD["creative_directions"][:2],
             "creative_selection":GOOD["creative_selection"]},
        ])
        with self.assertRaisesRegex(RuntimeError,
                                    "strict validation|Creative preflight"):
            ensure_creative_directions(invalid,company_facts=FACTS,
                source_anchors=ANCHORS,repair_json=model,max_repairs=2)
        self.assertEqual(model.call_count,2)

    def test_a_poor_first_repair_uses_one_more_bounded_try(self):
        original={"creative_directions":[],"creative_selection":{}}
        model=Mock(side_effect=[
            {"creative_directions":GOOD["creative_directions"][:2],
             "creative_selection":GOOD["creative_selection"]},
            deepcopy(GOOD),
        ])
        result=ensure_creative_directions(
            original,company_facts=FACTS,source_anchors=ANCHORS,
            repair_json=model,max_repairs=2)
        validate_creative_directions(result)
        self.assertEqual(model.call_count,2)

    def test_any_company_creative_failure_classifies_as_bounded_retry(self):
        from io import StringIO
        from scripts import run_kaurivo_demo_queue as runner
        for reason in (
            "Creative preflight repair did not pass strict validation: incomplete",
            "Creative directions differ mostly by surface details.",
            "Creative direction #2 incomplete: mobile_behavior",
        ):
            with self.subTest(reason=reason):
                log=StringIO("Traceback: source safe\\nRuntimeError: "+reason+"\\n")
                category=runner.classify_stage_failure(log, "researching")
                self.assertEqual(category, "research_creative_plan_needs_repair")
                self.assertIn(category,runner.TRANSIENT_RETRY_CODES)

    def test_research_draft_remains_private_and_not_completed_after_ai_error(self):
        slug="example-woodwork"
        data={"name":"Example Forest Workshop","url":"https://example.invalid/",
              "research_progress":{"version":1,"milestone":"references",
                "source_url":"https://example.invalid/",
                "master_prompt_sha256":"a"*64,
                "site_data":{"success":True},
                "source_inventory":{"pages":[{"url":"https://example.invalid/"}]},
                "extracted":{"company_facts":FACTS},
                "references":[{"url":"https://peer.invalid/1"}],
                "selected":[{"url":"https://peer.invalid/1"},
                            {"url":"https://peer.invalid/2"},
                            {"url":"https://peer.invalid/3"}],
                "reference_evidence":[{"url":"https://peer.invalid/1"},
                                      {"url":"https://peer.invalid/2"},
                                      {"url":"https://peer.invalid/3"}]}}
        with patch("utils.kaurivo_research_progress.get_company",
                   return_value=(slug,data)), \
             patch("utils.kaurivo_research_progress.upsert_company") as store:
            draft={"creative_directions":[],"creative_selection":{}}
            partial=save_progress(slug,data,milestone="references",
                source_url=data["url"],master_prompt_sha256="a"*64,
                draft_design_brief=draft)
            self.assertEqual(partial["draft_design_brief"],draft)
            self.assertEqual(partial["milestone"],"references")
            self.assertNotIn("research",data)
            self.assertTrue(get_progress(
                {"url":data["url"],"research_progress":partial},
                source_url=data["url"],master_prompt_sha256="a"*64))
            store.assert_called_once()


if __name__=="__main__":
    import unittest
    unittest.main()

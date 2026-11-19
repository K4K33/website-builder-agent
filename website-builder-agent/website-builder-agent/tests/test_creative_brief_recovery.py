"""Generic, offline new-firm Research recovery — no public APIs or real clients."""
from __future__ import annotations

import json
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

    def test_invalid_reason_retries_only_that_field_and_saves_progress(self):
        original = deepcopy(GOOD)
        original["creative_directions"][1]["business_reason"] = "An elegant visual trend."
        model = Mock(side_effect=[
            {"business_reason": "A bold new visual style."},
            {"business_reason": "The customer needs to find the verified repair service quickly."},
        ])
        save = Mock()
        result = ensure_creative_directions(
            original, company_facts=FACTS, source_anchors=ANCHORS,
            repair_json=model, save_draft=save,
        )
        validate_creative_directions(result)
        save.assert_called_once()
        intermediate = save.call_args.args[0]
        self.assertEqual(intermediate["creative_directions"][1]["business_reason"],
                         "A bold new visual style.")
        self.assertIn("Creative direction #2", model.call_args.args[1])
        self.assertIn("fresh reason", model.call_args.args[0])
        self.assertEqual(result["creative_directions"][0], original["creative_directions"][0])
        self.assertEqual(result["creative_selection"], original["creative_selection"])

    def test_unrequested_fields_in_model_reply_cannot_rewrite_source(self):
        original = {"creative_directions": [], "company_facts": FACTS}
        model = Mock(return_value={**deepcopy(GOOD), "company_facts": {"name": "Invented"}})
        result = ensure_creative_directions(
            original, company_facts=FACTS, source_anchors=ANCHORS, repair_json=model,
        )
        self.assertEqual(result["company_facts"], FACTS)
        validate_creative_directions(result)
        self.assertEqual(model.call_count, 1)

    def test_saved_verifiable_choice_needs_no_extra_model_call(self):
        draft = deepcopy(GOOD)
        chosen = draft["creative_selection"]["selected_id"]
        draft["creative_selection"].pop("rejected_ids")
        draft["creative_directions"][0]["business_reason"] = "Asiakas löytää sopivan ajan nopeasti."
        model = Mock()
        result = ensure_creative_directions(
            draft, company_facts=FACTS, source_anchors=ANCHORS, repair_json=model,
        )
        self.assertEqual(
            set(result["creative_selection"]["rejected_ids"]),
            {direction["id"] for direction in result["creative_directions"]} - {chosen},
        )
        validate_creative_directions(result)
        model.assert_not_called()

    def test_missing_concepts_remain_rejected(self):
        model = Mock(return_value={
            **GOOD, "creative_directions": GOOD["creative_directions"][:2],
        })
        with self.assertRaisesRegex(RuntimeError, "strict validation"):
            ensure_creative_directions(
                {}, company_facts=FACTS, source_anchors=ANCHORS, repair_json=model,
            )
        self.assertEqual(model.call_count, 2)

    def test_default_repair_uses_latest_validation_feedback(self):
        original = {"creative_directions": [], "creative_selection": {}}
        malformed = {**deepcopy(GOOD), "creative_selection": ["invalid"]}
        model = Mock(side_effect=[malformed, deepcopy(GOOD)])

        result = ensure_creative_directions(
            original, company_facts=FACTS, source_anchors=ANCHORS, repair_json=model,
        )

        validate_creative_directions(result)
        self.assertEqual(model.call_count, 2)
        second_packet = json.loads(model.call_args.args[1])
        self.assertIn("Creative selection needs", second_packet["validation_error"])
        self.assertEqual(second_packet["previous_selection"], ["invalid"])

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

    def test_verified_no_website_industry_uses_source_dict_and_repairs(self):
        from agents import research as research_agent
        facts = {"name":"Example Forest Workshop", "industry":"Carpentry",
                 "services":["Verified wooden furniture repair"]}
        fact_sources = {
            "name":["https://registry.example.invalid/profile"],
            "industry":["https://registry.example.invalid/industry"],
            "services":["https://supplier.example.invalid/services"],
        }
        company={"name":facts["name"],"url":"",
                 "company_profile":{"verified_by_human":True}}
        peers=[{"url":"https://peer.example.invalid/"+str(i),
                "observations":["Original verified craft work"]} for i in range(3)]
        invalid={"creative_directions":[],"creative_selection":{}}
        responses=Mock(side_effect=[invalid, deepcopy(GOOD)])
        written=[]
        with patch.object(research_agent,"validate_verified_profile",
                          return_value={"facts":facts,
                                        "fact_sources":fact_sources,
                                        "verified_at":"2026-11-14"}), \
             patch.object(research_agent,"_search_industry_references",
                          return_value=peers), \
             patch.object(research_agent,"_select_reference_candidates",
                          return_value=peers), \
             patch.object(research_agent,"_collect_reference_evidence",
                          return_value=peers), \
             patch.object(research_agent,"reference_image_inputs",
                          return_value=([],[])), \
             patch.object(research_agent,"ask_claude_json",responses), \
             patch.object(research_agent,"_validate_research_design"), \
             patch.object(research_agent,"validate_site_architecture"), \
             patch.object(research_agent,"upsert_company",
                          side_effect=lambda slug,changes:
                          written.append(changes) or changes), \
             patch.object(research_agent,"set_status"):
            result=research_agent._research_verified_no_website_company(
                "example-forest",company)
        self.assertEqual(responses.call_count,2)
        self.assertEqual(result["research"]["fact_sources"],fact_sources)
        validate_creative_directions(result["research"])
        payload=responses.call_args.args[1]
        self.assertIn("registry.example.invalid",payload)

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

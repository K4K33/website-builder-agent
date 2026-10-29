"""Deterministic, offline tests: indicative lead priority is not solvency estimation."""
import os
import tempfile
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch, Mock

import config
import main
from agents import outreach
from utils import state
from utils.lead_intelligence import estimate_purchase_capacity, evaluate_prospect
from utils.lead_queue import rank_leads


def reviews(verified=True, count=60):
    return {
        "rating": 4.8, "review_count": count,
        "source_url": "https://example.org/sourced-reviews",
        "verified_by_human": verified, "checked_at": date.today().isoformat(),
    }


def verified_activity():
    return {
        "active": True, "verified_by_human": True,
        "source_url": "https://example.org/recent-business-operation",
        "checked_at": date.today().isoformat(),
    }


def identity():
    return {"business_id": "0116297-6", "business_id_verified": True,
            "registry_source_url": "https://avoindata.prh.fi/opendata-ytj-api/v3/companies?businessId=0116297-6",
            "legal_status": "unknown"}


def source_profile():
    return {"verified_by_human": True, "verified_at": date.today().isoformat(),
            "company_facts": {"name": "Demo Oy", "industry": "restaurant",
                              "services": ["Lounas"], "location": "Tampere"},
            "fact_sources": {
                "name": ["https://example.org/company"],
                "industry": ["https://example.org/company"],
                "services": ["https://example.org/verified-menu"]}}


def no_site():
    return {"name": "Demo Oy", "url": "", "website": "",
            "site_verification": {"confirmed_absent": True,
                "verified_by_human": True,
                "source_url": "https://example.org/reviewed-site-check"},
            "company_profile": source_profile()}


class IndicativeBuyingPotentialTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        setting = patch.object(config, "COMPANIES_FILE",
                               str(Path(self.tmp.name) / "companies.json"))
        setting.start()
        self.addCleanup(setting.stop)

    def test_missing_financials_are_unknown_not_insolvent(self):
        data = estimate_purchase_capacity({"name": "Demo", "website": "https://demo.fi"})
        self.assertEqual(data["score"], 0)
        self.assertEqual(data["status"], "insufficient_evidence")
        self.assertFalse(data["can_prioritize"])
        self.assertIn("not a probability", data["disclaimer"])

    def test_reviewed_good_reputation_counts_as_rough_purchase_indicator(self):
        lead = {"name": "Demo", "website": "https://demo.fi", "reputation": reviews()}
        report = evaluate_prospect(lead)
        self.assertEqual(report["financial"]["status"], "needs_review")
        self.assertEqual(report["purchase_capacity"]["score"], 10)
        self.assertEqual(report["purchase_capacity"]["status"], "insufficient_evidence")
        self.assertFalse(report["purchase_capacity"]["can_prioritize"])
        self.assertEqual(report["outreach_gate"], "verification_pending")

    def test_faked_ratings_or_missing_source_add_no_points(self):
        for rep in (reviews(verified=False), reviews(count=1),
                    reviews() | {"source_url": ""},
                    reviews() | {"checked_at": "2019-01-01"}):
            self.assertEqual(estimate_purchase_capacity({"reputation": rep})["score"], 0)

    def test_registry_identity_is_a_small_signal_not_cash_proof(self):
        verified = {"financials": identity()}
        report = estimate_purchase_capacity(verified)
        self.assertEqual(report["score"], 10)
        self.assertFalse(report["can_prioritize"])
        report = estimate_purchase_capacity(verified | {"reputation": reviews()})
        self.assertEqual(report["score"], 20)
        self.assertFalse(report["can_prioritize"])
        self.assertEqual(report["confidence"], "moderate")

    def test_operating_scale_must_be_source_checked_and_recent(self):
        scale = {"location_count": 3, "employee_count": 7,
                 "verified_by_human": True,
                 "source_url": "https://example.org/reviewed-company-about",
                 "checked_at": date.today().isoformat()}
        estimate = estimate_purchase_capacity({"operational_scale": scale})
        self.assertEqual(estimate["score"], 15)
        self.assertEqual(estimate["status"], "insufficient_evidence")
        single = scale | {"location_count": 1, "employee_count": 0}
        multi = scale | {"location_count": 20, "employee_count": 0}
        self.assertEqual(estimate_purchase_capacity({"operational_scale": single})["score"], 0)
        self.assertEqual(estimate_purchase_capacity({"operational_scale": multi})["score"], 0)
        for changed in (scale | {"verified_by_human": False},
                        scale | {"source_url": ""},
                        scale | {"checked_at": "2020-01-01"}):
            self.assertEqual(estimate_purchase_capacity({"operational_scale": changed})["score"], 0)

    def test_bankruptcy_or_ended_company_never_qualified_from_good_reviews(self):
        lead = {"reputation": reviews(),
                "operational_scale": {"location_count": 12, "verified_by_human": True,
                    "source_url": "https://example.org/company",
                    "checked_at": date.today().isoformat()},
                "financials": {"legal_status": "ended"}}
        report = evaluate_prospect(lead)
        self.assertEqual(report["purchase_capacity"]["status"], "excluded")
        self.assertFalse(report["purchase_capacity"]["can_prioritize"])
        self.assertEqual(report["outreach_gate"], "verification_pending")

    def test_manual_capacity_price_validation(self):
        for price in (0, -1, 99, 100001, None, "1500", True):
            with self.assertRaises(ValueError):
                estimate_purchase_capacity({}, estimated_project_eur=price)

    def test_queue_provides_transparent_priority_not_purchase_probability(self):
        rows = rank_leads({
            "high": {"name": "Strong", "website": "https://one.fi", "reputation": reviews(),
                     "financials": identity() | {
                         "legal_status": "active",
                         "financial_source_url": "https://example.org/audited",
                         "financial_verified_by_human": True, "financial_year": date.today().year - 1,
                         "revenue_eur": 240000, "operating_profit_eur": 19000,
                     }},
            "medium": {"name": "Medium", "website": "https://two.fi", "reputation": reviews()},
            "unknown": {"name": "Unknown", "website": "https://three.fi"},
        })
        self.assertEqual([x["company"] for x in rows], ["high", "medium", "unknown"])
        self.assertEqual(rows[1]["indicative_capacity"]["score"], 10)
        self.assertTrue(rows[1]["indicative_capacity"]["not_actual_solvency"])

    def test_high_reputation_no_site_with_no_turnover_can_pass_manual_pipeline(self):
        record = no_site() | {"reputation": reviews(),
                              "activity_evidence": verified_activity()}
        state.upsert_company("demo", record)
        args = SimpleNamespace(company="demo", benchmark_mode=False, confirm_live_run=True,
                               max_revisions=0, count=1, industry="ravintola", location="Tampere")
        with patch.object(config, "model_for_stage", return_value="fixture/model"), \
             patch.dict(os.environ, {"OPENROUTER_API_KEY": "fixture",
                                      "TAVILY_API_KEY": "fixture"}), \
             patch.object(main.research, "run_research") as research, \
             patch.object(main.builder, "run_build") as build, \
             patch.object(main.qa, "run_qa", return_value={"overall_pass": True}) as qa:
            main.cmd_pipeline(args)
            research.assert_called_once_with("demo")
            build.assert_called_once_with("demo")
            qa.assert_called_once_with("demo")

    def test_unknown_activity_blocks_commercial_even_when_manually_selected(self):
        record = {"name": "Demo", "website": "https://demo.fi", "url": "https://demo.fi"}
        state.upsert_company("demo", record)
        args = SimpleNamespace(company="demo", benchmark_mode=False, confirm_live_run=True,
                               max_revisions=0, count=1, industry="ravintola", location="Tampere")
        with patch.object(config, "model_for_stage", return_value="fixture/model"), \
             patch.dict(os.environ, {"OPENROUTER_API_KEY": "fixture",
                                      "TAVILY_API_KEY": "fixture"}), \
             patch.object(main.research, "run_research") as research:
            with self.assertRaisesRegex(RuntimeError, "Active business operations"):
                main.cmd_pipeline(args)
            research.assert_not_called()
            record["activity_evidence"] = verified_activity()
            state.upsert_company("demo", record)
            with patch.object(main.builder, "run_build"), \
                 patch.object(main.qa, "run_qa", return_value={"overall_pass": True}):
                main.cmd_pipeline(args)
            research.assert_called_once_with("demo")

    def test_outreach_draft_allowed_from_indicative_reviews_but_not_sent(self):
        record = {"name": "Demo", "website": "https://demo.fi", "url": "https://demo.fi",
                  "reputation": reviews(),
                  "activity_evidence": verified_activity(),
                  "build": {"version": 1},
                  "qa": {"overall_pass": True, "build_version": 1, "html_sha256": "hash"},
                  "approval": {"approved": True, "build_version": 1, "html_sha256": "hash"},
                  "research": {"company_facts": {"name": "Demo", "industry": "salon",
                                                  "services": ["Haircuts"], "location": "Tampere"}}}
        state.upsert_company("demo", record)
        with patch.object(outreach, "ask_claude_json", return_value={
            "subject": "Draft only", "body": "Reviewed draft."
        }) as model:
            draft = outreach.draft_outreach("demo", record)
            model.assert_called_once()
            self.assertFalse(draft["approved"])
        self.assertEqual(state.get_company("demo")[1]["outreach"]["subject"], "Draft only")


if __name__ == "__main__":
    unittest.main()

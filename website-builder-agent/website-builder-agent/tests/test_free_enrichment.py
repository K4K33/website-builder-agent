"""No-fee, fully mocked verification and verified no-site research tests."""
import json
import os
import tempfile
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, patch

import config
import main
from agents import research
from utils import state
from utils.free_enrichment import enrich_one, enrich_queue
from utils.prh_financials import available_financial_periods
from utils.verified_profile import validate_verified_profile


def company():
    return {"name": "Demo Oy", "city": "Tampere", "website": "", "url": "",
            "osm_type": "node", "osm_id": 1, "status": "verification_pending",
            "site_verification": {"confirmed_absent": True, "verified_by_human": True,
                                  "source_url": "https://example.org/manual-check"}}


def profile():
    return {"verified_by_human": True, "verified_at": date.today().isoformat(),
            "company_facts": {"name": "Demo Oy", "industry": "restaurant",
                              "services": ["Lounas"], "location": "Tampere"},
            "fact_sources": {
                "name": ["https://example.org/company"],
                "industry": ["https://example.org/company"],
                "services": ["https://example.org/menu"]}}


def official():
    return {"business_id": "0116297-6", "official_names": ["Demo Oy"],
            "registry_source_url": "https://avoindata.prh.fi/opendata-ytj-api/v3/companies?businessId=0116297-6",
            "registration_ended": False, "company_situations": [],
            "official_website": ""}


def prh_periods():
    return {"status": "available", "financial_dates": ["2025-12-31"],
            "latest_financial_date": "2025-12-31", "financial_figures_verified": False,
            "source_url": "https://avoindata.prh.fi/opendata-xbrl-api/v3/financials?businessId=0116297-6"}


class FreeEnrichmentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for field, path in (("DATA_DIR", self.root / "data"),
                            ("COMPANIES_FILE", self.root / "data" / "companies.json"),
                            ("OUTPUT_DIR", self.root / "output")):
            ctx = patch.object(config, field, str(path))
            ctx.start()
            self.addCleanup(ctx.stop)

    def test_financial_index_reads_only_matching_periods(self):
        response = Mock(status_code=200)
        response.raise_for_status.return_value = None
        response.json.return_value = {"totalResults": 1,
                                      "financials": [{"businessId": "0116297-6",
                                                      "financialDate": "2025-12-31"}]}
        with patch("utils.prh_financials.requests.get", return_value=response) as get:
            result = available_financial_periods("0116297-6")
        self.assertEqual(result["status"], "available")
        self.assertEqual(result["latest_financial_date"], "2025-12-31")
        self.assertFalse(result["financial_figures_verified"])
        self.assertNotIn("revenue_eur", result)
        self.assertEqual(get.call_args.kwargs["params"]["businessId"], "0116297-6")

    def test_financial_index_missing_not_assumed_bad(self):
        response = Mock(status_code=200)
        response.raise_for_status.return_value = None
        response.json.return_value = {"financials": [], "totalResults": 0}
        with patch("utils.prh_financials.requests.get", return_value=response):
            self.assertEqual(available_financial_periods("0116297-6")["status"], "not_available")
        response.status_code = 404
        with patch("utils.prh_financials.requests.get", return_value=response):
            self.assertEqual(available_financial_periods("0116297-6")["status"], "not_available")

    def test_financial_index_rejects_bad_ids_foreign_rows_and_budgets(self):
        with self.assertRaises(ValueError):
            available_financial_periods("not a business ID")
        with self.assertRaises(ValueError):
            available_financial_periods("0116297-6", max_pages=100)
        response = Mock(status_code=200)
        response.raise_for_status.return_value = None
        response.json.return_value = {"financials": [{"businessId": "bad-id",
                                                        "financialDate": "2025-12-31"}]}
        with patch("utils.prh_financials.requests.get", return_value=response):
            with self.assertRaisesRegex(RuntimeError, "identity mismatch"):
                available_financial_periods("0116297-6")

    def test_exact_name_is_required_before_auto_enrichment(self):
        wrong = official() | {"official_names": ["Different Oy"]}
        lookup = Mock(return_value=wrong)
        periods = Mock(return_value=prh_periods())
        result = enrich_one(company(), lookup_name=lookup, lookup_periods=periods)
        self.assertEqual(result["status"], "manual_identity_check")
        self.assertEqual(result["updates"], {})
        periods.assert_not_called()

    def test_free_enrichment_records_availability_not_unverified_profit(self):
        periods = Mock(return_value=prh_periods())
        result = enrich_one(company(), lookup_name=Mock(return_value=official()),
                            lookup_periods=periods)
        self.assertEqual(result["status"], "enriched")
        updates = result["updates"]
        self.assertEqual(updates["business_id"], "0116297-6")
        self.assertEqual(updates["financial_availability"]["status"], "available")
        self.assertEqual(updates["lead_intelligence"]["financial"]["status"], "needs_review")
        self.assertNotIn("operating_profit_eur", updates["financials"])
        periods.assert_called_once_with("0116297-6")

    def test_prh_website_is_candidate_not_proof_of_website(self):
        info = official() | {"official_website": "https://demo.fi"}
        result = enrich_one(company(), lookup_name=Mock(return_value=info),
                            lookup_periods=Mock(return_value=prh_periods()))
        self.assertEqual(result["updates"]["website_discovery"]["status"],
                         "official_registry_candidate")
        self.assertEqual(result["updates"]["lead_intelligence"]["site_status"],
                         "website_not_listed")
        self.assertFalse(result["updates"]["site_verification"]["confirmed_absent"])
        self.assertIn("previous_no_website_claim_needs_reverification", result["issues"])
        self.assertNotIn("website", result["updates"])

    def test_prh_lookup_failure_is_not_financial_exclusion(self):
        result = enrich_one(company(), lookup_name=Mock(return_value=official()),
                            lookup_periods=Mock(side_effect=RuntimeError("429")))
        self.assertEqual(result["updates"]["financial_availability"]["status"], "lookup_failed")
        self.assertNotEqual(result["updates"]["lead_intelligence"]["financial"]["status"], "exclude")

    def test_enrichment_queue_bounded_and_approved_work_untouched(self):
        state.upsert_company("demo", company())
        state.upsert_company("approved", company() | {"name": "Old Oy", "status": "approved",
                                                       "build": {"version": 8}})
        results = enrich_queue(max_companies=5, pause_seconds=0,
                               sleep=Mock(), lookup_name=Mock(return_value=official()),
                               lookup_periods=Mock(return_value=prh_periods()))
        self.assertEqual([x["slug"] for x in results], ["demo"])
        self.assertEqual(state.get_company("approved")[1]["build"]["version"], 8)
        self.assertEqual(state.get_company("demo")[1]["business_id"], "0116297-6")
        with self.assertRaises(ValueError):
            enrich_queue(max_companies=11)

    def test_offline_lead_queue_prioritizes_verified_finances_and_reviews(self):
        from utils.lead_queue import rank_leads
        good = company()
        good.update({
            "reputation": {"rating": 4.9, "review_count": 62, "source_url": "https://example.org/reviews",
                           "verified_by_human": True, "checked_at": date.today().isoformat()},
            "financials": {"business_id": "0116297-6", "business_id_verified": True,
                           "registry_source_url": official()["registry_source_url"],
                           "legal_status": "active", "insolvency_proceeding": False,
                           "financial_source_url": "https://example.org/verified-report",
                           "financial_verified_by_human": True, "financial_year": date.today().year - 1,
                           "revenue_eur": 240000, "operating_profit_eur": 12500}
        })
        unknown = company() | {"name": "Unknown", "site_verification": {}}
        excluded = company() | {"name": "Ended",
                                 "financials": {"legal_status": "ended"}}
        rows = rank_leads({"good": good, "unknown": unknown, "ended": excluded})
        self.assertEqual(rows[0]["company"], "good")
        self.assertEqual(rows[0]["bucket"], "high_priority_manual_review")
        self.assertEqual(rows[-1]["company"], "ended")
        self.assertTrue(all(not row["outreach_allowed"] for row in rows))

    def test_no_site_commercial_pipeline_requires_reviews_and_profile(self):
        record = company() | {"company_profile": profile()}
        record["financials"] = {
            "business_id": "0116297-6", "business_id_verified": True,
            "registry_source_url": official()["registry_source_url"],
            "legal_status": "active", "financial_source_url": "https://example.org/report",
            "financial_verified_by_human": True, "financial_year": date.today().year - 1,
            "revenue_eur": 190000, "operating_profit_eur": 7800,
        }
        state.upsert_company("demo", record)
        args = SimpleNamespace(company="demo", benchmark_mode=False, confirm_live_run=True,
                               count=1, industry="ravintola", location="Tampere", max_revisions=0)
        with patch.object(config, "model_for_stage", return_value="fixture/mock"), \
             patch.dict(os.environ, {"OPENROUTER_API_KEY": "fixture", "TAVILY_API_KEY": "fixture"}), \
             patch.object(main.research, "run_research") as researched:
            with self.assertRaisesRegex(RuntimeError, "strong independently checked reviews"):
                main.cmd_pipeline(args)
            researched.assert_not_called()
        record["reputation"] = {
            "rating": 4.8, "review_count": 60, "source_url": "https://example.org/reviews",
            "verified_by_human": True, "checked_at": date.today().isoformat(),
        }
        state.upsert_company("demo", record)
        with patch.object(config, "model_for_stage", return_value="fixture/mock"), \
             patch.dict(os.environ, {"OPENROUTER_API_KEY": "fixture", "TAVILY_API_KEY": "fixture"}), \
             patch.object(main.research, "run_research") as researched, \
             patch.object(main.builder, "run_build") as built, \
             patch.object(main.qa, "run_qa", return_value={"overall_pass": True}):
            main.cmd_pipeline(args)
            researched.assert_called_once_with("demo")
            built.assert_called_once_with("demo")

    def test_direct_paid_cli_commands_require_explicit_consent(self):
        with patch.object(main.scout, "run_scout") as paid_scout:
            args = SimpleNamespace(dry_run=False, discovery_only=False, count=1,
                                   industry="ravintola", location="Tampere",
                                   confirm_paid_apis=False)
            with self.assertRaisesRegex(RuntimeError, "confirm-paid-apis"):
                main.cmd_scout(args)
            paid_scout.assert_not_called()
        with patch.object(main.research, "run_research") as paid_research:
            with self.assertRaisesRegex(RuntimeError, "confirm-paid-apis"):
                main.cmd_research(SimpleNamespace(company="demo"))
            paid_research.assert_not_called()

    def test_enrichment_cli_fails_closed_without_permission(self):
        with patch.object(main, "enrich_queue") as run:
            with self.assertRaisesRegex(RuntimeError, "confirm-public-lookups"):
                main.cmd_enrich_free(SimpleNamespace(confirm_public_lookups=False))
            run.assert_not_called()

    def test_no_site_profile_needs_real_sources_and_manual_approval(self):
        good = company() | {"company_profile": profile()}
        self.assertEqual(validate_verified_profile(good)["facts"]["services"], ["Lounas"])
        with self.assertRaisesRegex(RuntimeError, "confirmed"):
            validate_verified_profile(good | {"site_verification": {}})
        bad = profile()
        del bad["fact_sources"]["services"]
        with self.assertRaisesRegex(RuntimeError, "source"):
            validate_verified_profile(good, bad)
        altered = profile()
        altered["company_facts"]["name"] = "Other Oy"
        with self.assertRaisesRegex(RuntimeError, "Name"):
            validate_verified_profile(good, altered)

    def test_profile_cli_saves_without_ai(self):
        record = company()
        state.upsert_company("demo", record)
        input_file = self.root / "profile.json"
        input_file.write_text(json.dumps(profile()), encoding="utf-8")
        main.cmd_attach_profile(SimpleNamespace(company="demo", profile=str(input_file)))
        saved = state.get_company("demo")[1]
        self.assertTrue(saved["company_profile"]["verified_by_human"])
        self.assertNotIn("research", saved)

    def test_research_no_site_uses_profile_and_three_references_without_fake_target_site(self):
        saved = company() | {"company_profile": profile()}
        state.upsert_company("demo", saved)
        image = self.root / "sample.png"
        image.write_bytes(b"fixture")
        urls = ["https://restaurant-a.fi", "https://restaurant-b.fi", "https://restaurant-c.fi"]
        refs = [{
            "url": u, "site_text": "Real restaurant service listing.",
            "industry_match": {"same_industry": True, "target_industry": "restaurant",
                               "reason": "Same operator industry",
                               "evidence_quote": "restaurant service"},
            "observations": ["Clear opening details"], "apply": ["Adapt to real facts"],
            "avoid": ["No copying"], "screenshots": {"desktop": str(image), "mobile": str(image)}
        } for u in urls]
        decisions = [
            {"id": section, "dimension": dim, "reference_url": urls[i % 3],
             "observation": "Clear opening details", "adaptation": "Show verified service",
             "section_id": "main", "acceptance_check": "Read main text"}
            for i, (section, dim) in enumerate([
                ("hero", "first_view"), ("services", "service_hierarchy"),
                ("contact", "contact_path"), ("mobile", "mobile")])
        ]
        brief = {
            "company_facts": {"name": "Hallucinated Oy", "industry": "consulting",
                              "services": ["Invented service"]},
            "reference_comparison": [{"url": u, "observations": ["Clear opening details"],
                                      "apply": ["Adapt to real facts"], "avoid": ["No copying"]}
                                     for u in urls],
            "design_decisions": decisions,
            "design_recommendations": {"motion_plan": {
                "purpose": "Clear layout", "implementation": "Static deliberate",
                "reduced_motion": "Visible text", "verification": "Viewport check"}}
        }
        with patch.object(research, "analyze_url") as site_read, \
             patch.object(research, "_search_tavily", return_value=[]) as tavily, \
             patch.object(research, "_select_reference_candidates", return_value=[]) as selection, \
             patch.object(research, "_collect_reference_evidence", return_value=refs) as observed, \
             patch.object(research, "ask_claude_json", return_value=brief) as model:
            research.run_research("demo")
        site_read.assert_not_called()
        self.assertEqual(tavily.call_count, 2)
        self.assertEqual(model.call_count, 1)
        saved = state.get_company("demo")[1]
        self.assertEqual(saved["research"]["company_facts"]["services"], ["Lounas"])
        self.assertEqual(saved["research"]["research_mode"], "verified_no_website")
        self.assertEqual(saved["status"], "researched")
        self.assertNotIn("current_site_raw", saved)
        self.assertEqual(saved["url"], "")


if __name__ == "__main__":
    unittest.main()

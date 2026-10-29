"""Offline regression tests for no-website discovery, reviewed leads and budget gates."""
import json
import os
import tempfile
import unittest
from pathlib import Path
from datetime import date
from unittest.mock import patch, Mock

import config
import main
from agents import scout, outreach
from utils import state
from utils.lead_intelligence import review_signal, financial_signal, evaluate_prospect, site_signal
from utils.company_registry import lookup_by_business_id


def reputation():
    return {"rating": 4.8, "review_count": 80, "source_url": "https://example.org/reviews/demo",
            "verified_by_human": True, "checked_at": date.today().isoformat()}


def finance():
    return {"business_id": "0116297-6", "business_id_verified": True,
            "registry_source_url": "https://avoindata.prh.fi/opendata-ytj-api/v3/companies?businessId=0116297-6",
            "legal_status": "active", "insolvency_proceeding": False,
            "financial_source_url": "https://example.org/verified-financial-report",
            "financial_verified_by_human": True,
            "financial_year": date.today().year - 1,
            "revenue_eur": 245000, "operating_profit_eur": 17000}


class LeadScreeningTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        for key, value in {"DATA_DIR": str(self.root / "data"),
                           "COMPANIES_FILE": str(self.root / "data" / "companies.json"),
                           "OUTPUT_DIR": str(self.root / "output")}.items():
            setting = patch.object(config, key, value)
            setting.start()
            self.addCleanup(setting.stop)

    def no_site(self, name="Demo", osm_id=100):
        return {"name": name, "website": "", "osm_type": "node", "osm_id": osm_id,
                "phone": "+358400000000", "tags": {}}

    def test_missing_website_kept_in_dry_run_without_paid_ai_or_browser(self):
        items = [self.no_site()]
        with patch.object(scout, "_fetch_osm_companies", return_value=items), \
             patch.object(scout, "_technical_analysis") as technical, \
             patch.object(scout, "_ai_analyze_company") as paid_ai, \
             patch.object(scout, "capture_website") as browser:
            found = scout.scout(count=1, dry_run=True)
            self.assertEqual(len(found), 1)
            self.assertEqual(found[0]["lead_type"], "no_website_candidate")
            self.assertEqual(found[0]["lead_intelligence"]["site_status"], "website_not_listed")
            paid_ai.assert_not_called()
            technical.assert_not_called()
            browser.assert_not_called()
        self.assertEqual(state.load_companies(), {})

    def test_missing_website_is_persisted_as_verification_pending(self):
        with patch.object(scout, "_fetch_osm_companies", return_value=[self.no_site()]), \
             patch.object(scout, "_ai_analyze_company") as ai:
            leads = scout.scout(count=1)
            ai.assert_not_called()
        self.assertEqual(len(leads), 1)
        self.assertEqual(leads[0]["status"], "verification_pending")
        self.assertFalse(leads[0]["lead_intelligence"]["outreach_allowed"])
        self.assertEqual(leads[0]["url"], "")
        # Old OSM record is deduplicated by OSM type/id even without URL.
        with patch.object(scout, "_fetch_osm_companies", return_value=[self.no_site()]):
            self.assertEqual(scout.scout(count=1), [])

    def test_discovery_only_saves_both_without_paid_ai_or_browser(self):
        leads = [self.no_site(), {"name": "Has Website", "website": "https://exists.fi",
                                 "osm_type": "node", "osm_id": 200, "tags": {}}]
        with patch.object(scout, "_fetch_osm_companies", return_value=leads), \
             patch.object(scout, "_technical_analysis") as site_check, \
             patch.object(scout, "_ai_analyze_company") as paid_ai, \
             patch.object(scout, "capture_website") as browser:
            found = scout.scout(count=2, discovery_only=True)
        self.assertEqual(len(found), 2)
        self.assertEqual({lead["name"] for lead in found}, {"Demo", "Has Website"})
        self.assertTrue(all(lead["status"] == "verification_pending" for lead in found))
        paid_ai.assert_not_called()
        site_check.assert_not_called()
        browser.assert_not_called()

    def test_paid_commercial_scan_does_not_spend_on_unknown_finances(self):
        leads = [{"name": "Unscreened", "website": "https://unscreened.fi",
                  "osm_type": "node", "osm_id": 900, "tags": {}}]
        with patch.object(scout, "_fetch_osm_companies", return_value=leads), \
             patch.object(scout, "_technical_analysis") as technical, \
             patch.object(scout, "_ai_analyze_company") as ai, \
             patch.object(scout, "capture_website") as browser:
            self.assertEqual(scout.scout(count=1, commercial_only=True), [])
            technical.assert_not_called()
            ai.assert_not_called()
            browser.assert_not_called()

    def test_missing_site_does_not_exhaust_all_website_analysis_slots(self):
        leads = [self.no_site(name=f"Without {n}", osm_id=n) for n in range(8)]
        leads.append({"name": "Actual site", "website": "https://real.fi",
                      "osm_type": "node", "osm_id": 999, "tags": {}})
        with patch.object(scout, "_fetch_osm_companies", return_value=leads), \
             patch.object(scout, "_technical_analysis") as analysis:
            found = scout.scout(count=2, discovery_only=True)
        self.assertIn("Actual site", {x["name"] for x in found})
        analysis.assert_not_called()

    def test_prh_name_and_city_rejects_ambiguous_identity(self):
        from utils.company_registry import lookup_by_name_and_location
        company = {"businessId": {"value": "0116297-6"},
                   "names": [{"name": "Demo"}],
                   "addresses": [{"postOffices": [{"city": "Tampere"}]}]}
        response = Mock()
        response.json.return_value = {"companies": [company]}
        response.raise_for_status.return_value = None
        with patch("utils.company_registry.requests.get", return_value=response):
            self.assertEqual(lookup_by_name_and_location("Demo", "Tampere")["business_id"], "0116297-6")
            response.json.return_value = {"companies": [company, company]}
            with self.assertRaisesRegex(RuntimeError, "one exact"):
                lookup_by_name_and_location("Demo", "Tampere")

    def test_unnamed_website_tag_is_not_proof_of_no_site(self):
        self.assertEqual(site_signal(self.no_site()), "website_not_listed")
        upgraded = self.no_site() | {"site_verification": {
            "confirmed_absent": True, "verified_by_human": True,
            "source_url": "https://example.org/directory/demo"}}
        self.assertEqual(site_signal(upgraded), "confirmed_no_website")
        upgraded["site_verification"]["verified_by_human"] = False
        self.assertEqual(site_signal(upgraded), "website_not_listed")

    def test_reputation_requires_source_count_recency_and_manual_verification(self):
        self.assertTrue(review_signal(reputation())["strong"])
        for change in ({"rating": 4.2}, {"review_count": 5},
                       {"source_url": ""}, {"verified_by_human": False},
                       {"checked_at": "2020-01-01"}):
            candidate = reputation() | change
            self.assertFalse(review_signal(candidate)["strong"])
        self.assertEqual(review_signal({})["status"], "unknown")

    def test_budget_fit_not_inferred_from_revenue_alone(self):
        self.assertEqual(financial_signal({})["status"], "needs_review")
        self.assertEqual(financial_signal(finance())["status"], "promising")
        for change in ({"operating_profit_eur": -1000}, {"financial_year": 2019},
                       {"financial_source_url": ""}, {"financial_verified_by_human": False},
                       {"business_id_verified": False}, {"revenue_eur": 2000}):
            self.assertNotEqual(financial_signal(finance() | change)["status"], "promising")
        self.assertEqual(financial_signal(finance() | {"insolvency_proceeding": True})["status"], "exclude")

    def test_no_website_high_reviews_and_financial_fit_is_review_priority_not_auto_outreach(self):
        candidate = self.no_site() | {"reputation": reputation(), "financials": finance(),
                                     "site_verification": {
                                         "confirmed_absent": True, "verified_by_human": True,
                                         "source_url": "https://example.org/directories/demo"}}
        result = evaluate_prospect(candidate)
        self.assertEqual(result["site_status"], "confirmed_no_website")
        self.assertEqual(result["outreach_gate"], "priority_for_human_review")
        self.assertFalse(result["outreach_allowed"])
        del candidate["site_verification"]
        self.assertEqual(evaluate_prospect(candidate)["outreach_gate"], "verification_pending")

    def test_manual_screening_requires_same_business_identity(self):
        state.upsert_company("demo", self.no_site() | {"business_id": "0116297-6"})
        evidence = self.root / "lead.json"
        evidence.write_text(json.dumps({"reputation": reputation(), "financials": finance(),
                                       "site_verification": {
                                           "confirmed_absent": True, "verified_by_human": True,
                                           "source_url": "https://example.org/directory"}}))
        main.cmd_screen_lead(type("Args", (), {"company": "demo", "evidence": str(evidence),
                                             "project_price": 1500})())
        self.assertEqual(state.get_company("demo")[1]["lead_intelligence"]["outreach_gate"],
                         "priority_for_human_review")
        bad = finance() | {"business_id": "1234567-8"}
        evidence.write_text(json.dumps({"financials": bad}))
        with self.assertRaises(ValueError):
            main.cmd_screen_lead(type("Args", (), {"company": "demo", "evidence": str(evidence),
                                                 "project_price": 1500})())

    def test_prh_free_lookup_requires_exact_id_match_and_does_not_fake_revenue(self):
        response = Mock()
        response.json.return_value = {"companies": [{
            "businessId": {"value": "0116297-6"}, "names": [{"name": "Demo Oy"}],
            "website": {"url": "https://demo.fi"}, "tradeRegisterStatus": "unknown_code",
            "status": "unknown_code", "companySituations": [], "endDate": None,
        }]}
        response.raise_for_status.return_value = None
        with patch("utils.company_registry.requests.get", return_value=response) as get:
            result = lookup_by_business_id("0116297-6")
            self.assertEqual(result["official_website"], "https://demo.fi")
            self.assertEqual(result["legal_status"], "unknown")
            self.assertNotIn("revenue_eur", result)
            get.assert_called_once()
        response.json.return_value = {"companies": [{
            "businessId": {"value": "1234567-8"}}]}
        with patch("utils.company_registry.requests.get", return_value=response):
            with self.assertRaisesRegex(RuntimeError, "No unique"):
                lookup_by_business_id("0116297-6")

    def test_registry_verification_does_not_invent_financials(self):
        state.upsert_company("demo", self.no_site())
        stub = {"business_id": "0116297-6", "official_names": ["Demo Oy"],
                "official_website": "", "registry_source_url": "https://avoindata.prh.fi/a",
                "business_id_verified": True, "registration_ended": False,
                "company_situations": [], "trade_register_status": "", "registered_status": "",
                "legal_status": "unknown"}
        with patch.object(main, "lookup_by_business_id", return_value=stub):
            main.cmd_verify_registry(type("Args", (), {
                "company": "demo", "business_id": "0116297-6",
                "confirm_name_mismatch": True})())
        record = state.get_company("demo")[1]
        self.assertEqual(record["financials"]["legal_status"] if "legal_status" in record["financials"] else "unknown", "unknown")
        self.assertEqual(record["lead_intelligence"]["financial"]["status"], "needs_review")

    def test_commercial_pipeline_fails_before_research_when_finance_missing(self):
        from types import SimpleNamespace
        record = {"name": "Demo", "url": "https://demo.fi", "website": "https://demo.fi"}
        record["lead_intelligence"] = evaluate_prospect(record)
        state.upsert_company("demo", record)
        args = SimpleNamespace(company="demo", benchmark_mode=False, confirm_live_run=True,
                               industry="ravintola", location="Tampere", count=1, max_revisions=0)
        with patch.object(config, "model_for_stage", return_value="fixture/mock"), \
             patch.dict(os.environ, {"OPENROUTER_API_KEY": "offline_fixture",
                                      "TAVILY_API_KEY": "offline_fixture"}), \
             patch.object(main.research, "run_research") as researched, \
             patch.object(main.builder, "run_build") as built:
            with self.assertRaisesRegex(RuntimeError, "Financial screening"):
                main.cmd_pipeline(args)
            researched.assert_not_called()
            built.assert_not_called()

    def test_no_site_pipeline_stops_before_any_paid_research_even_in_benchmark(self):
        from types import SimpleNamespace
        record = self.no_site()
        record["url"] = ""
        state.upsert_company("demo", record)
        args = SimpleNamespace(company="demo", benchmark_mode=True, confirm_live_run=True,
                               industry="ravintola", location="Tampere", count=1, max_revisions=0)
        with patch.object(config, "model_for_stage", return_value="fixture/mock"), \
             patch.dict(os.environ, {"OPENROUTER_API_KEY": "offline_fixture",
                                      "TAVILY_API_KEY": "offline_fixture"}), \
             patch.object(main.research, "run_research") as researched:
            with self.assertRaisesRegex(RuntimeError, "No-site lead"):
                main.cmd_pipeline(args)
            researched.assert_not_called()

    def test_outreach_blocked_before_ai_when_no_proven_budget(self):
        company = {"qa": {"overall_pass": True, "build_version": 1, "html_sha256": "hash"},
                   "approval": {"approved": True, "build_version": 1, "html_sha256": "hash"},
                   "build": {"version": 1}, "website": "https://demo.fi"}
        with patch.object(outreach, "ask_claude_json") as paid_ai:
            with self.assertRaisesRegex(RuntimeError, "budget evidence"):
                outreach.draft_outreach("demo", company)
            paid_ai.assert_not_called()


if __name__ == "__main__":
    unittest.main()

"""No-site is the primary Scout target; active trading is the production criterion.

All tests are offline and explicitly prohibit paid AI, Tavily and browser calls.
"""
import json
import os
import tempfile
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import config
import main
from agents import scout, outreach
from utils import state
from utils.lead_intelligence import business_activity_signal, estimate_purchase_capacity
from utils.lead_queue import rank_leads


def activity():
    return {
        "active": True, "verified_by_human": True,
        "source_url": "https://example.org/verified-operating-business",
        "checked_at": date.today().isoformat(),
    }


def site_absent():
    return {
        "confirmed_absent": True, "verified_by_human": True,
        "source_url": "https://example.org/independent-website-check",
    }


class NoSiteActivePriorityTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        for field, path in (("DATA_DIR", Path(self.tmp.name) / "data"),
                            ("COMPANIES_FILE", Path(self.tmp.name) / "data/companies.json")):
            setting = patch.object(config, field, str(path))
            setting.start()
            self.addCleanup(setting.stop)

    def test_verified_active_business_without_web_or_reviews_is_first(self):
        records = {
            "excellent-existing": {
                "name": "Excellent existing site", "website": "https://good.fi",
                "activity_evidence": activity(),
                "reputation": {"rating": 4.9, "review_count": 500,
                               "verified_by_human": True, "checked_at": date.today().isoformat(),
                               "source_url": "https://example.org/reviews"},
                "financials": {"legal_status": "active", "business_id_verified": True,
                               "registry_source_url": "https://example.org/prh",
                               "financial_source_url": "https://example.org/statements",
                               "financial_verified_by_human": True,
                               "financial_year": date.today().year - 1,
                               "revenue_eur": 400000, "operating_profit_eur": 25000},
            },
            "small-one-location": {
                "name": "Single location, no website",
                "website": "", "site_verification": site_absent(),
                "activity_evidence": activity(),
            },
            "no-site-unverified": {
                "name": "Unknown website listing", "website": "",
            },
        }
        rows = rank_leads(records)
        self.assertEqual([item["company"] for item in rows],
                         ["small-one-location", "no-site-unverified", "excellent-existing"])
        self.assertEqual(rows[0]["bucket"], "no_website_active_priority")
        self.assertEqual(rows[0]["business_activity"], "active")
        self.assertEqual(rows[0]["indicative_capacity"]["score"], 35)
        self.assertFalse(rows[0]["outreach_allowed"])

    def test_no_site_listing_is_first_even_for_one_result_without_api_costs(self):
        candidates = [
            {"name": "Old site", "website": "https://old.fi",
             "osm_type": "node", "osm_id": 1, "tags": {}},
            {"name": "No site listed", "website": "",
             "osm_type": "node", "osm_id": 2, "tags": {}},
        ]
        with patch.object(scout, "_fetch_osm_companies", return_value=candidates), \
             patch.object(scout, "_technical_analysis") as technical, \
             patch.object(scout, "_ai_analyze_company") as paid_model, \
             patch.object(scout, "capture_website") as browser:
            found = scout.scout(count=1, industry="kampaamo",
                                location="Tampere", discovery_only=True)
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0]["name"], "No site listed")
        self.assertEqual(found[0]["status"], "verification_pending")
        self.assertEqual(found[0]["lead_intelligence"]["site_status"], "website_not_listed")
        technical.assert_not_called()
        paid_model.assert_not_called()
        browser.assert_not_called()

    def test_multiple_locations_no_bonus_and_one_location_is_valid(self):
        base = {"activity_evidence": activity()}
        single = {**base, "operational_scale": {
            "location_count": 1, "verified_by_human": True,
            "source_url": "https://example.org/locations",
            "checked_at": date.today().isoformat()}}
        lots = {**base, "operational_scale": {
            "location_count": 50, "verified_by_human": True,
            "source_url": "https://example.org/locations",
            "checked_at": date.today().isoformat()}}
        a = estimate_purchase_capacity(single)
        b = estimate_purchase_capacity(lots)
        self.assertEqual(a["score"], b["score"])
        self.assertTrue(a["can_prioritize"])

    def test_missing_or_expired_activity_is_unknown_not_closed(self):
        self.assertEqual(business_activity_signal({})["status"], "unknown")
        bad = {"activity_evidence": activity() | {"checked_at": "2020-01-01"}}
        self.assertEqual(business_activity_signal(bad)["status"], "unknown")
        incorrect = {"activity_evidence": activity() | {"verified_by_human": False}}
        self.assertEqual(business_activity_signal(incorrect)["status"], "unknown")

    def test_inactive_business_stays_excluded_despite_review_stars(self):
        lead = {"name": "Closed", "website": "",
                "site_verification": site_absent(),
                "activity_evidence": activity(),
                "financials": {"legal_status": "ended"}}
        rows = rank_leads({"closed": lead})
        self.assertEqual(rows[0]["bucket"], "excluded_inactive_business")
        self.assertEqual(rows[0]["priority"], 0)
        self.assertEqual(rows[0]["business_activity"], "inactive")

    def test_manual_activity_evidence_can_be_attached_without_paid_ai(self):
        state.upsert_company("demo", {"name": "Demo", "website": "",
                                      "site_verification": site_absent()})
        file = Path(self.tmp.name) / "activity.json"
        file.write_text(json.dumps({"activity_evidence": activity()}), encoding="utf-8")
        with patch.object(main.research, "run_research") as paid:
            main.cmd_screen_lead(SimpleNamespace(company="demo",
                                                  evidence=str(file), project_price=1500))
            paid.assert_not_called()
        record = state.get_company("demo")[1]
        self.assertEqual(record["lead_intelligence"]["business_activity"]["status"], "active")
        self.assertEqual(record["lead_intelligence"]["site_status"], "confirmed_no_website")

    def test_unverified_operations_never_spend_commercial_ai_credits(self):
        state.upsert_company("unknown", {"name": "Unknown", "website": "https://example.org"})
        args = SimpleNamespace(company="unknown", benchmark_mode=False,
                               confirm_live_run=True, count=1, industry="kampaamo",
                               location="Tampere", max_revisions=0)
        with patch.object(config, "model_for_stage", return_value="fixture/model"), \
             patch.dict(os.environ, {"OPENROUTER_API_KEY": "offline",
                                      "TAVILY_API_KEY": "offline"}), \
             patch.object(main.research, "run_research") as paid:
            with self.assertRaisesRegex(RuntimeError, "Active business operations"):
                main.cmd_pipeline(args)
            paid.assert_not_called()

    def test_outreach_draft_requires_activity_not_stars(self):
        record = {"name": "Demo", "website": "https://example.org",
                  "activity_evidence": activity(),
                  "qa": {"overall_pass": True, "build_version": 1, "html_sha256": "hash"},
                  "approval": {"approved": True, "build_version": 1, "html_sha256": "hash"},
                  "build": {"version": 1},
                  "research": {"company_facts": {"name": "Demo", "industry": "salon", "services": ["Haircuts"]}}}
        state.upsert_company("demo", record)
        with patch.object(outreach, "ask_claude_json",
                          return_value={"subject": "Draft", "body": "No fake claims."}) as ai:
            result = outreach.draft_outreach("demo", record)
            ai.assert_called_once()
            self.assertFalse(result["approved"])


if __name__ == "__main__":
    unittest.main()

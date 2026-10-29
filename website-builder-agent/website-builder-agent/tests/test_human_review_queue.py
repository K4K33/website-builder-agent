"""All-offline tests for user approval checkpoint and shortlist flow."""
import json
import tempfile
import unittest
from datetime import date
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import config
import main
from utils import state
from utils.human_review_queue import shortlist, record_decision, format_markdown


def activity():
    return {
        "active": True, "source_url": "https://example.org/recent-working-business",
        "verified_by_human": True, "checked_at": date.today().isoformat(),
    }


def site_absent():
    return {
        "confirmed_absent": True, "source_url": "https://example.org/verified-no-web",
        "verified_by_human": True,
    }


class HumanReviewWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.dir = Path(self.temp.name)
        for key, value in (
            ("DATA_DIR", str(self.dir)),
            ("COMPANIES_FILE", str(self.dir / "companies.json")),
        ):
            patcher = patch.object(config, key, value)
            patcher.start()
            self.addCleanup(patcher.stop)

    def test_human_no_site_first_unknown_is_pending_no_fake_claims(self):
        companies = {
            "existing-strong": {"name": "Existing site", "website": "https://example.org",
                                "activity_evidence": activity()},
            "unknown-listing": {"name": "Unlisted website", "osm_type": "node",
                                "osm_id": 777, "location": "Tampere"},
            "active-no-site": {"name": "Active no site", "website": "",
                               "site_verification": site_absent(),
                               "activity_evidence": activity()},
            "closed": {"name": "Closed", "website": "",
                       "financials": {"legal_status": "ended"}},
        }
        got = shortlist(companies, limit=10)
        self.assertEqual([row["company"] for row in got],
                         ["active-no-site", "unknown-listing", "existing-strong"])
        self.assertEqual(got[0]["checks_needed"], [])
        self.assertEqual(got[1]["checks_needed"],
                         ["confirm_current_operations", "verify_website_absence"])
        self.assertEqual(got[1]["source_url"], "https://www.openstreetmap.org/node/777")
        self.assertFalse(got[0]["builder_authorized"])
        self.assertFalse(got[0]["outreach_authorized"])
        self.assertIn("ei todista sivuttomuutta", format_markdown(got))

    def test_select_is_only_a_decision_never_evidence_of_site_absence(self):
        state.upsert_company("demo", {"name": "Demo", "osm_type": "node", "osm_id": 78})
        with patch.object(main.research, "run_research") as researched, \
             patch.object(main.builder, "run_build") as built, \
             patch.object(main.outreach, "run_outreach") as mailed:
            row = record_decision("demo", "select", "Would look good as a bakery demo.")
            researched.assert_not_called()
            built.assert_not_called()
            mailed.assert_not_called()
        self.assertTrue(row["selected_for_demo"])
        self.assertFalse(row["approval_to_contact"])
        saved = state.get_company("demo")[1]
        self.assertEqual(saved["owner_review"]["decision"], "select")
        self.assertNotIn("site_verification", saved)
        self.assertNotIn("activity_evidence", saved)
        self.assertNotIn("build", saved)

    def test_skipped_companies_hidden_unless_explicitly_requested(self):
        state.upsert_company("one", {"name": "One", "osm_type": "way", "osm_id": 7})
        state.upsert_company("two", {"name": "Two", "osm_type": "node", "osm_id": 9})
        record_decision("one", "skip", "Already contacted.")
        rows = shortlist(state.load_companies())
        self.assertEqual([r["company"] for r in rows], ["two"])
        self.assertEqual(len(shortlist(state.load_companies(), include_reviewed=True)), 2)

    def test_validates_human_decision_and_source_url(self):
        state.upsert_company("one", {"name": "One", "osm_id": "invalid",
                                     "osm_type": "node",
                                     "url": "javascript:alert(1)"})
        with self.assertRaises(ValueError):
            record_decision("one", "publish")
        with self.assertRaises(ValueError):
            record_decision("one", "select", "x" * 501)
        rows = shortlist(state.load_companies())
        self.assertEqual(rows[0]["source_url"], "")
        self.assertEqual(rows[0]["website_url"], "")
        for limit in (0, 101, -5, "5"):
            with self.assertRaises(ValueError):
                shortlist(state.load_companies(), limit=limit)

    def test_cli_shortlist_and_review_preserve_state(self):
        state.upsert_company("demo", {"name": "Demo", "osm_type": "node", "osm_id": 77})
        calls = SimpleNamespace(limit=5, format="markdown", include_reviewed=False)
        with patch("builtins.print") as printed, \
             patch.object(main.research, "run_research") as ai:
            main.cmd_shortlist(calls)
            text = "\n".join(str(x) for a in printed.call_args_list for x in a.args)
            self.assertIn("Demo", text)
            ai.assert_not_called()
        main.cmd_review_lead(SimpleNamespace(company="demo", decision="select", note="Please design."))
        record = state.get_company("demo")[1]
        self.assertEqual(record["owner_review"]["decision"], "select")
        self.assertNotIn("outreach", record)


if __name__ == "__main__":
    unittest.main()

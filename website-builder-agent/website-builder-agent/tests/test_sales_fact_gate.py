"""Regression tests for the exact-build factual sales gate (offline only)."""
import copy
import unittest
from datetime import datetime, timezone, timedelta

from utils.sales_fact_gate import (
    REQUIRED_AREAS, inspect_sales_fact_review, research_fingerprint,
)


def example_record(now=None):
    now = now or datetime.now(timezone.utc)
    checked = now.isoformat()
    research = {
        "company_facts": {"name": "Verified Example Oy", "services": ["Welding"]},
        "source_inventory": {
            "pages": [{"url": "https://example.org/", "text": "Welding company"}]
        },
        "source_content_map": {"pages": []},
        "current_site_weaknesses": [],
    }
    return {
        "research": research,
        "build": {"version": 2, "page_paths": ["index.html", "palvelut/index.html"]},
        "qa": {"overall_pass": True, "build_version": 2,
               "html_sha256": "h" * 64, "site_sha256": "s" * 64},
        "approval": {"approved": True, "build_version": 2,
                     "html_sha256": "h" * 64, "site_sha256": "s" * 64},
        "sales_fact_review": {
            "status": "verified",
            "reviewer_kind": "human",
            "reviewer": "Kaurivo reviewer",
            "checked_at": checked,
            "build_version": 2,
            "html_sha256": "h" * 64,
            "site_sha256": "s" * 64,
            "research_sha256": research_fingerprint(research),
            "original_site_status": "verified_existing_website",
            "areas": {
                key: {"status": "verified",
                      "source_url": "https://example.org/company",
                      "checked_at": checked}
                for key in REQUIRED_AREAS
            },
            "reviewed_routes": ["index.html", "palvelut/index.html"],
            "missing_or_changed_facts": [],
            "unresolved_issues": [],
            "corrections": [],
        },
    }


class SalesFactGateTests(unittest.TestCase):
    def test_exact_complete_recent_record_can_be_considered_for_further_gates(self):
        company = example_record()
        self.assertTrue(inspect_sales_fact_review(company)["ready"])

    def test_owner_visual_approval_alone_never_unlocks_sales(self):
        company = example_record()
        del company["sales_fact_review"]
        result = inspect_sales_fact_review(company)
        self.assertFalse(result["ready"])
        self.assertIn("missing", result["issues"][0].lower())

    def test_changed_page_or_source_invalidates_review(self):
        for mutation in ("site", "source", "approval"):
            company = example_record()
            if mutation == "site":
                company["qa"]["site_sha256"] = "z" * 64
            elif mutation == "source":
                company["research"]["company_facts"]["services"].append("New service")
            else:
                company["approval"]["approved"] = False
            with self.subTest(mutation=mutation):
                self.assertFalse(inspect_sales_fact_review(company)["ready"])

    def test_one_unreviewed_route_or_omitted_source_fact_stops_delivery(self):
        company = example_record()
        company["sales_fact_review"]["reviewed_routes"].pop()
        self.assertFalse(inspect_sales_fact_review(company)["ready"])
        company = example_record()
        company["sales_fact_review"]["areas"].pop("public_contact_details")
        self.assertFalse(inspect_sales_fact_review(company)["ready"])

    def test_unavailable_original_is_not_proof_of_no_website(self):
        company = example_record()
        company["research"]["source_inventory"] = {"pages": []}
        company["sales_fact_review"]["research_sha256"] = research_fingerprint(company["research"])
        self.assertFalse(inspect_sales_fact_review(company)["ready"])
        company["sales_fact_review"]["original_site_status"] = "unreachable"
        self.assertFalse(inspect_sales_fact_review(company)["ready"])

    def test_every_discovered_omission_needs_fix_evidence_and_regression(self):
        company = example_record()
        company["sales_fact_review"]["missing_or_changed_facts"] = ["Phone number wrong"]
        self.assertFalse(inspect_sales_fact_review(company)["ready"])
        company = example_record()
        company["sales_fact_review"]["corrections"] = [
            {"status": "fixed", "evidence": "commit 123", "reusable_rule": True}
        ]
        self.assertFalse(inspect_sales_fact_review(company)["ready"])
        company["sales_fact_review"]["corrections"][0]["regression_test"] = "tests.test_phone_parity"
        self.assertTrue(inspect_sales_fact_review(company)["ready"])

    def test_outreach_approval_requires_completed_review(self):
        from unittest.mock import patch
        from agents import outreach
        record = example_record()
        record["outreach"] = {"subject": "Sample", "body": "Sample"}
        del record["sales_fact_review"]
        with patch.object(outreach, "get_company",
                          return_value=("verified-example", record)):
            with self.assertRaisesRegex(RuntimeError, "factual verification"):
                outreach.approve_outreach("verified-example")

    def test_stale_future_and_unverified_areas_block(self):
        now = datetime.now(timezone.utc)
        company = example_record(now)
        company["sales_fact_review"]["checked_at"] = (now-timedelta(days=8)).isoformat()
        self.assertFalse(inspect_sales_fact_review(company, now=now)["ready"])
        company = example_record(now)
        company["sales_fact_review"]["areas"]["outreach_claims"]["status"] = "unknown"
        self.assertFalse(inspect_sales_fact_review(company, now=now)["ready"])
        company = example_record(now)
        company["sales_fact_review"]["checked_at"] = (now+timedelta(hours=1)).isoformat()
        self.assertFalse(inspect_sales_fact_review(company, now=now)["ready"])


if __name__ == "__main__":
    unittest.main()

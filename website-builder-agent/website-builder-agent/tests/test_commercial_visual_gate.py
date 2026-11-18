"""A strong individual site can be marketed before agency-wide 9.5, never before real QA."""
from datetime import datetime, timedelta, timezone
from unittest.mock import patch
import unittest

from utils.commercial_visual_gate import assess_commercial_visual_review
from agents import outreach


DIGEST = "a" * 64
ROUTES = ["index.html", "palvelut/index.html", "yhteys/index.html"]


def visual_review():
    return {
        "site_sha256": DIGEST,
        "approved": True,
        "reviewer_kind": "human",
        "reviewer": "Kaurivo owner",
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "evidence_reference": "private-current-build-visual-inspection",
        "routes_reviewed": ROUTES,
        "viewports_reviewed": [390, 1440],
        "critical_issues": [],
        "source_comparison_reviewed": True,
        "brand_and_media_reviewed": True,
        "readability_and_mobile_reviewed": True,
        "commercial_journey_reviewed": True,
    }


class CommercialVisualGateTests(unittest.TestCase):
    def test_one_owner_approved_site_without_95_score_or_other_clients_can_qualify(self):
        result = assess_commercial_visual_review(
            visual_review(), site_sha256=DIGEST, routes=ROUTES)
        self.assertTrue(result["approved"], result["issues"])
        self.assertFalse(result["goal_9_5_is_required"])

    def test_scope_build_rights_and_actual_visual_quality_remain_mandatory(self):
        mutations = {
            "stale_build": lambda r: r.update(site_sha256="b"*64),
            "missing_route": lambda r: r.update(routes_reviewed=["index.html"]),
            "mobile_unchecked": lambda r: r.update(viewports_reviewed=[1440]),
            "critical_visual_defect": lambda r: r.update(critical_issues=["Unusable header"]),
            "brand_unchecked": lambda r: r.update(brand_and_media_reviewed=False),
            "unapproved": lambda r: r.update(approved=False),
            "missing_evidence": lambda r: r.update(evidence_reference=""),
        }
        for name, change in mutations.items():
            with self.subTest(name=name):
                record = visual_review()
                change(record)
                result = assess_commercial_visual_review(
                    record, site_sha256=DIGEST, routes=ROUTES)
                self.assertFalse(result["approved"])

    def test_stale_review_is_rejected(self):
        record = visual_review()
        record["checked_at"] = (datetime.now(timezone.utc) - timedelta(days=40)).isoformat()
        self.assertFalse(assess_commercial_visual_review(
            record, site_sha256=DIGEST, routes=ROUTES)["approved"])

    def test_outreach_without_three_95_projects_still_requires_facts_and_live_release(self):
        record = {
            "name": "Example Oy",
            "outreach": {"subject": "Ehdotus", "body": "Yksilöllinen hyväksytty ehdotus"},
            "agency_quality_reviews": [],
        }
        with patch.object(outreach, "get_company", return_value=("example", record)):
            with patch("utils.sales_fact_gate.inspect_sales_fact_review",
                       return_value={"ready": True, "issues": []}):
                with patch("utils.release_safety.inspect_release_safety",
                           return_value={"approved": True, "issues": [],
                                         "status": "PRESENTATION_READY"}):
                    with patch.object(outreach, "upsert_company") as saved:
                        with patch.object(outreach, "set_status"):
                            outreach.approve_outreach("example")
                            self.assertTrue(saved.call_args.args[1]["outreach"]["approved"])

    def test_factual_failure_blocks_early_sales_unchanged(self):
        record = {"name": "Example Oy",
                  "outreach": {"subject": "Ehdotus", "body": "Vahvistettu sivusto"}}
        with patch.object(outreach, "get_company", return_value=("example", record)):
            with patch("utils.sales_fact_gate.inspect_sales_fact_review",
                       return_value={"ready": False, "issues": ["Wrong company phone"]}):
                with self.assertRaisesRegex(RuntimeError, "factual verification"):
                    outreach.approve_outreach("example")


if __name__ == "__main__":
    unittest.main()

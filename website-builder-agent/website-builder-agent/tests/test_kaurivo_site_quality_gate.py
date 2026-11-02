"""Credit-free regression tests for Kaurivo portfolio-level 9.5 QA."""
from datetime import date
from pathlib import Path
import unittest

from utils.kaurivo_site_quality_gate import (
    assess_quality_consistency, lint_site_copy, lint_site_directory
)

ROOT = Path(__file__).resolve().parents[1]


def review(client: str, score: float = 9.6, **changes):
    base = {
        "client_project_id": client,
        "reviewer_kind": "external_ai",
        "reviewer_model": "IndependentExampleReviewModel",
        "independence_human_verified": True,
        "evidence_reference": "private-review-recording-ref-2026-11-02",
        "review_date": date.today().isoformat(),
        "reviewed_build": "a012345678bcdef0",
        "overall_score": score,
        "pages_reviewed": 5,
        "viewports_reviewed": [390, 1440],
        "critical_issues": [],
        "sitewide_copy_check_passed": True,
        "real_browser_checks_passed": True,
        "image_rights_checked": True,
    }
    base.update(changes)
    return base


class CopyAuditTests(unittest.TestCase):
    def test_kotifixi_v7_has_no_formulaic_opposite_pairs(self):
        check = lint_site_directory(ROOT / "docs" / "kaurivo" / "demos" / "kotifixi-v7")
        self.assertTrue(check["pass"], check["issues"])
        self.assertLessEqual(check["contrast_count"], 1)

    def test_contrast_limit_applies_across_entire_site(self):
        pages = {
            "index.html": "<h1>Vähemmän ongelmia. Enemmän iloa.</h1>",
            "palvelut/index.html": "<h2>Ei vain kotitöitä vaan myös pihatöitä.</h2>",
        }
        check = lint_site_copy(pages)
        self.assertFalse(check["pass"])
        self.assertEqual(check["contrast_count"], 2)
        self.assertIn("limit 1", check["issues"][0])
        self.assertTrue(lint_site_copy({"index.html": pages["index.html"]})["pass"])

    def test_identical_long_paragraphs_rejected_sitewide(self):
        sentence = "Kotifixi auttaa kodin ja pihan töissä ja tarjoaa yksittäisiin projekteihin apua tarpeen mukaan."
        html = f"<main><p>{sentence}</p></main>"
        check = lint_site_copy({"a/index.html": html, "b/index.html": html})
        self.assertFalse(check["pass"])
        self.assertTrue(any("Repeated paragraph" in x for x in check["issues"]))


class EvidenceGateTests(unittest.TestCase):
    def test_single_high_scoring_project_cannot_certify_agency(self):
        result = assess_quality_consistency([review("kotifixi")], current_project_id="kotifixi")
        self.assertEqual(result["status"], "HOLD")
        self.assertIn("at least 3 distinct", " ".join(result["issues"]))

    def test_all_recent_three_projects_must_score_95_or_above(self):
        reports = [review("kotifixi"), review("a"), review("b")]
        self.assertTrue(assess_quality_consistency(reports, current_project_id="kotifixi")["accepted"])
        reports[2]["overall_score"] = 9.4
        result = assess_quality_consistency(reports, current_project_id="kotifixi")
        self.assertFalse(result["accepted"])
        self.assertTrue(any("below 9.5" in x for x in result["issues"]))

    def test_mobile_only_claude_85_must_not_pass(self):
        actual_scope_example = review("kotifixi", 8.5, viewports_reviewed=[390])
        result = assess_quality_consistency([actual_scope_example], current_project_id="kotifixi")
        self.assertFalse(result["accepted"])
        self.assertTrue(any("8.5/10" in x for x in result["issues"]))
        self.assertTrue(any("Both real mobile and desktop" in x for x in result["issues"]))

    def test_independence_and_provenance_are_required(self):
        reports = [review("kotifixi", independence_human_verified=False), review("b"), review("c")]
        self.assertFalse(assess_quality_consistency(reports, current_project_id="kotifixi")["accepted"])
        reports[0]["independence_human_verified"] = True
        reports[0]["evidence_reference"] = ""
        self.assertFalse(assess_quality_consistency(reports, current_project_id="kotifixi")["accepted"])

    def test_concurrent_critical_issue_or_unchecked_licenses_holds(self):
        reports = [review("kotifixi"), review("b"), review("c", critical_issues=["Form broken"])]
        self.assertFalse(assess_quality_consistency(reports, current_project_id="kotifixi")["accepted"])
        reports[2]["critical_issues"] = []
        reports[0]["image_rights_checked"] = False
        self.assertFalse(assess_quality_consistency(reports, current_project_id="kotifixi")["accepted"])

    def test_no_self_rating_or_ai_call_in_gate_module(self):
        src = (ROOT / "utils" / "kaurivo_site_quality_gate.py").read_text(encoding="utf8")
        self.assertNotIn("ask_claude", src)
        self.assertNotIn("requests.", src)
        self.assertNotIn("openai.ChatCompletion", src)


if __name__ == "__main__":
    unittest.main()

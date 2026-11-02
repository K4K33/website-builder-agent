"""Zero-credit, business-agnostic premium QA evidence regressions."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from utils.content_parity import source_inventory_sha256
from utils.premium_quality_gate import (
    SCORE_DIMENSIONS, VIEWPORTS, site_digest, source_coverage_matrix,
    verify_independent_premium_reviews, verify_field_performance,
    audit_primary_journeys, discover_source_journeys,
)
from utils.source_content_blocks import (
    extract_source_content_blocks, audit_source_content_blocks,
)
from utils.universal_quality import audit_universal_standards


ROOT_URL = "https://local-example.org/"


class PremiumGateTests(unittest.TestCase):
    def setUp(self):
        self.html = {"index.html": (
            '<html><body><main>'
            '<h1>Real small business</h1>'
            '<p>We repair and service bicycles with verified trained technicians '
            'in our original city workshop and clearly itemized prices.</p>'
            '<a href="https://booking.example.org/repair/actual-id">Book service</a>'
            '</main></body></html>'
        )}
        self.source = (
            '<html><body><main><h1>Our workshop</h1>'
            '<p>We repair and service bicycles with verified trained technicians '
            'in our original city workshop and clearly itemized prices.</p>'
            '</main></body></html>'
        )
        blocks = extract_source_content_blocks(self.source)
        self.research = {
            "source_inventory": {"pages": [{
                "url": ROOT_URL, "text": "Content",
                "headings": {"h1": ["Our workshop"]},
                "source_content_blocks": blocks,
            }]},
            "source_content_map": {"pages": [{
                "source_url": ROOT_URL, "status": "retain", "target": "index.html",
                "sections": [{"source_heading": "Our workshop", "target": "index.html"}],
            }]},
        }

    def test_source_blocks_are_captured_with_deterministic_ids(self):
        first = extract_source_content_blocks(self.source)
        second = extract_source_content_blocks(self.source)
        self.assertEqual(first["blocks"], second["blocks"])
        self.assertEqual(len(first["blocks"]), 1)
        self.assertEqual(len(first["blocks"][0]["id"]), 16)

    def test_visible_original_text_counts_as_verbatim(self):
        audit = audit_source_content_blocks(self.html, self.research)
        self.assertTrue(audit["pass"], audit)
        self.assertEqual(audit["preserved_verbatim"], 1)

    def test_paraphrase_pending_not_falsely_accepted(self):
        rewritten = {"index.html": "<main><p>We offer repairs for local bikes.</p></main>"}
        audit = audit_source_content_blocks(rewritten, self.research)
        self.assertFalse(audit["pass"])
        self.assertEqual(len(audit["pending"]), 1)

    def test_source_bound_human_rewrite_signoff_does_not_accept_stale_build(self):
        rewritten = {"index.html": "<main><p>We offer repairs for local bikes.</p></main>"}
        missing_id = self.research["source_inventory"]["pages"][0][
            "source_content_blocks"]["blocks"][0]["id"]
        self.research["rewritten_content_review"] = {
            "reviewer_kind": "human", "reviewer": "Editorial reviewer",
            "checked_at": "2026-11-03",
            "source_sha256": source_inventory_sha256(self.research["source_inventory"]),
            "build_sha256": site_digest(rewritten),
            "verified_block_ids": [missing_id],
        }
        self.assertTrue(audit_source_content_blocks(rewritten, self.research)["pass"])
        changed = {"index.html": rewritten["index.html"].replace("local", "urban")}
        self.assertFalse(audit_source_content_blocks(changed, self.research)["pass"])

    def test_coverage_matrix_requires_exact_build_human_review(self):
        report = source_coverage_matrix(self.html, self.research)
        self.assertEqual(report["status"], "pending")
        self.assertEqual(report["source_pages"], 1)
        self.assertEqual(report["missing"], [])
        self.research["content_inventory_review"] = {
            "approved": True, "reviewer_kind": "human", "reviewer": "Reviewer",
            "checked_at": "2026-11-03",
            "snapshot_sha256": source_inventory_sha256(self.research["source_inventory"]),
            "build_sha256": site_digest(self.html), "source_urls": [ROOT_URL],
        }
        self.assertEqual(source_coverage_matrix(self.html, self.research)["status"], "verified")

    def test_unmapped_source_page_cannot_be_claimed_verified(self):
        self.research["source_content_map"]["pages"] = []
        report = source_coverage_matrix(self.html, self.research)
        self.assertEqual(report["status"], "fail")
        self.assertTrue(report["missing"])

    def test_independent_two_reviewer_evidence_and_all_dimensions(self):
        with tempfile.TemporaryDirectory() as tmp:
            files = {}
            for vp in VIEWPORTS:
                path = Path(tmp) / (vp + ".png")
                path.write_bytes(b"test-screenshot-marker")
                files[vp] = str(path)
            reviews = [
                {"reviewer_id": "independent-human-a", "independent_of_builder": True,
                 "provenance_human_verified": True,
                 "critical_issues": [], "evidence_reference": "verified-external-report-a",
                 "screenshots": files, "scores": {k: 9.7 for k in SCORE_DIMENSIONS},
                 "pages_reviewed": ["index.html"]},
                {"reviewer_id": "independent-ai-b", "independent_of_builder": True,
                 "provenance_human_verified": True,
                 "critical_issues": [], "evidence_reference": "verified-external-report-b",
                 "screenshots": files, "scores": {k: 9.5 for k in SCORE_DIMENSIONS},
                 "pages_reviewed": ["index.html"]},
            ]
            evidence = {
                "build_sha256": site_digest(self.html),
                "source_sha256": source_inventory_sha256(self.research["source_inventory"]),
                "reviewers": reviews,
            }
            self.assertTrue(verify_independent_premium_reviews(
                evidence, self.html, self.research)["pass"])
            reviews[1]["scores"]["brand_fidelity"] = 9.4
            self.assertFalse(verify_independent_premium_reviews(
                evidence, self.html, self.research)["pass"])
            reviews[1]["scores"]["brand_fidelity"] = 9.5
            reviews[1]["reviewer_id"] = reviews[0]["reviewer_id"]
            self.assertFalse(verify_independent_premium_reviews(
                evidence, self.html, self.research)["pass"])

    def test_missing_independent_review_is_never_self_certified(self):
        self.assertFalse(verify_independent_premium_reviews(
            None, self.html, self.research)["pass"])
        self.assertIn("independent_premium_consensus",
            audit_universal_standards(self.html["index.html"])["pending_evidence"])

    def test_real_field_metrics_are_provisional_without_evidence(self):
        self.assertFalse(verify_field_performance(None, self.html)["pass"])
        evidence = {"build_sha256": site_digest(self.html), "source": "rum",
                    "percentile": 75, "lcp_ms": 2450, "inp_ms": 190,
                    "cls": 0.09, "sample_size": 100,
                    "human_evidence_verified": True}
        self.assertTrue(verify_field_performance(evidence, self.html)["pass"])
        evidence["inp_ms"] = 201
        self.assertFalse(verify_field_performance(evidence, self.html)["pass"])
        evidence["inp_ms"] = 190
        evidence["source"] = "lighthouse"
        self.assertFalse(verify_field_performance(evidence, self.html)["pass"])

    def test_original_booking_url_must_be_visible_and_accessible(self):
        good = [{"label": "Book bike servicing", "source_route": "index.html",
                 "destination": "https://booking.example.org/repair/actual-id"}]
        self.assertTrue(audit_primary_journeys(self.html, good)["pass"])
        wrong = [{**good[0], "destination": "https://booking.example.org/"}]
        self.assertFalse(audit_primary_journeys(self.html, wrong)["pass"])

    def test_claimed_primary_journey_missing_blocks_universal_site(self):
        research = {"primary_user_journeys": [{
            "label": "Real booking", "source_route": "index.html",
            "destination": "https://booking.example.org/wrong"
        }]}
        result = audit_universal_standards(self.html["index.html"], research)
        self.assertIn("primary_user_journeys", result["blocking_problems"])

    def test_source_booking_cta_discovery_avoids_root_and_internal_placeholder(self):
        self.research["source_inventory"]["pages"][0]["links"] = [
            {"text": "Varaa aika", "href": "/ajanvaraus/"},
            {"text": "Varaa aika", "href": "https://appointments.example.net/book/4832"},
            {"text": "Soita meille", "href": "tel:+358401234567"},
            {"text": "Send email", "href": "mailto:info@local-example.org"},
        ]
        tasks = discover_source_journeys(self.research)
        self.assertEqual([t["kind"] for t in tasks],
                         ["booking", "phone", "email"])
        self.assertEqual(tasks[0]["destination"],
                         "https://appointments.example.net/book/4832")
        self.assertTrue(all(t["source_route"] == "index.html" for t in tasks))

    def test_unverified_booking_destination_not_invented(self):
        self.research["source_inventory"]["pages"][0]["links"] = [
            {"text": "Book", "href": "/booking"},
            {"text": "Book", "href": "javascript:alert('fake')"},
        ]
        self.assertEqual(discover_source_journeys(self.research), [])

    def test_new_premium_client_cannot_bypass_two_reviewers_at_approval(self):
        import hashlib
        from unittest.mock import patch
        from agents.qa import approve_company
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "index.html"
            path.write_text(self.html["index.html"], encoding="utf-8")
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            company = {
                "status": "qa_passed",
                "research": {"premium_protocol": "v2",
                             "research_mode": "verified_no_website",
                             "fact_sources": [{"url": "https://registry.example.org/firm"}]},
                "build": {"version": 1, "output_path": str(path)},
                "qa": {"overall_pass": True, "build_version": 1,
                       "html_sha256": digest},
            }
            with patch("agents.qa.get_company", return_value=("test", company)):
                with self.assertRaisesRegex(RuntimeError, "factual profile"):
                    approve_company("test")
                company["research"]["no_site_fact_review"] = {
                    "approved": True, "reviewer_kind": "human",
                    "build_sha256": site_digest(self.html),
                }
                with self.assertRaisesRegex(RuntimeError, "two-reviewer"):
                    approve_company("test")

    def test_verified_content_matrix_does_not_approve_stale_html(self):
        self.research["content_inventory_review"] = {
            "approved": True, "reviewer_kind": "human", "reviewer": "Reviewer",
            "checked_at": "2026-11-03",
            "snapshot_sha256": source_inventory_sha256(self.research["source_inventory"]),
            "build_sha256": site_digest(self.html), "source_urls": [ROOT_URL],
        }
        changed = {"index.html": self.html["index.html"].replace("workshop", "office")}
        self.assertNotEqual(source_coverage_matrix(changed, self.research)["status"],
                            "verified")

    def test_verified_no_website_still_needs_external_factual_review(self):
        coverage = source_coverage_matrix(self.html, {"research_mode": "verified_no_website"})
        self.assertEqual(coverage["status"], "no_original_site")
        self.assertTrue(coverage["pending"])


if __name__ == "__main__":
    unittest.main()

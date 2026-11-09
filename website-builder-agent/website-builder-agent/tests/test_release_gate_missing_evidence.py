"""Fail-closed regression matrix for client release proof.

Free offline tests. Every mutated piece of proof must independently HOLD:
passing unit tests, a Render live flag, or an owner checkbox is not a substitute.
"""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timedelta, timezone
import unittest

from utils.release_safety import check_actual_public_website, inspect_release_safety
from utils.service_quality import MASTER_PROMPT_SHA256


ROUTES = {"index.html", "services/index.html"}
SITE_DIGEST = "a" * 64
COMMIT = "b" * 40


def public_evidence():
    """A complete, well-shaped offline browser report used as the control."""
    import hashlib
    marker = "source-exact-preview-version-1234"
    return {
        "url": "https://preview.example.org/",
        "site_sha256": SITE_DIGEST,
        "commit_sha": COMMIT,
        "release_marker": marker,
        "ci_run_url": "https://github.com/owner/repo/actions/runs/123456",
        "ci_verified_by_owner": True,
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "pages": [
            {
                "route": route, "viewport": viewport, "status": 200,
                "release_marker": marker, "computed_styles_valid": True,
                "scripts_valid": True, "navigation_valid": True,
                "responsive_valid": True, "visible_brand_valid": True,
                "broken_images": 0, "page_errors": [],
                "screenshot_sha256": hashlib.sha256(
                    f"{route}:{viewport}".encode()
                ).hexdigest(),
            }
            for route in sorted(ROUTES) for viewport in ("390", "1440")
        ],
        "errors": [], "warnings": [],
    }


def check(record):
    return check_actual_public_website(
        record, site_digest=SITE_DIGEST, routes=ROUTES, build_commit=COMMIT
    )


class ExactPublicProofRegressions(unittest.TestCase):
    def test_valid_reference_fixture_is_actually_valid(self):
        self.assertTrue(check(public_evidence())["passed"])

    def test_missing_required_evidence_always_holds(self):
        for field in (
            "url", "site_sha256", "commit_sha", "release_marker",
            "ci_run_url", "ci_verified_by_owner", "checked_at",
            "pages", "errors", "warnings",
        ):
            with self.subTest(field=field):
                record = public_evidence()
                record.pop(field)
                self.assertFalse(check(record)["passed"], field)

    def test_changed_exact_release_evidence_always_holds(self):
        cases = (
            ("site_sha256", "c" * 64),
            ("commit_sha", "d" * 40),
            ("release_marker", "old-release-marker"),
            ("ci_run_url", "https://example.org/not-a-ci-run"),
            ("ci_verified_by_owner", False),
            ("checked_at", "2025-01-01T00:00:00Z"),
            ("checked_at", (datetime.now(timezone.utc) +
                             timedelta(hours=1)).isoformat()),
            ("url", "http://preview.example.org"),
            ("url", "https://preview.invalid"),
            ("warnings", ["looks broken"]),
            ("errors", ["broken CSS"]),
        )
        for field, value in cases:
            with self.subTest(field=field, value=value):
                record = public_evidence()
                record[field] = value
                self.assertFalse(check(record)["passed"])

    def test_each_route_viewport_record_is_mandatory(self):
        for index in range(4):
            with self.subTest(missing_page=index):
                record = public_evidence()
                record["pages"].pop(index)
                self.assertFalse(check(record)["passed"])

    def test_each_public_page_dimension_is_mandatory(self):
        critical = (
            "status", "release_marker", "computed_styles_valid",
            "scripts_valid", "navigation_valid", "responsive_valid",
            "visible_brand_valid", "broken_images", "page_errors",
            "screenshot_sha256",
        )
        for field in critical:
            with self.subTest(field=field):
                record = public_evidence()
                record["pages"][0].pop(field)
                self.assertFalse(check(record)["passed"])

    def test_broken_or_stale_view_is_never_approved(self):
        bad_values = (
            ("status", 404),
            ("release_marker", "outdated-build"),
            ("computed_styles_valid", False),
            ("scripts_valid", False),
            ("navigation_valid", False),
            ("responsive_valid", False),
            ("visible_brand_valid", False),
            ("broken_images", 1),
            ("page_errors", ["Uncaught TypeError"]),
            ("screenshot_sha256", "not-a-real-digest"),
            ("screenshot_sha256", "z" * 64),
            ("screenshot_sha256", "G" * 64),
        )
        for field, value in bad_values:
            with self.subTest(field=field, value=value):
                record = public_evidence()
                record["pages"][0][field] = value
                self.assertFalse(check(record)["passed"])

    def test_duplicate_extra_or_uninspected_view_is_rejected(self):
        record = public_evidence()
        record["pages"].append(deepcopy(record["pages"][0]))
        self.assertFalse(check(record)["passed"])

        record = public_evidence()
        record["pages"][0]["route"] = "invented/index.html"
        self.assertFalse(check(record)["passed"])

        record = public_evidence()
        record["pages"][0]["viewport"] = "768"
        self.assertFalse(check(record)["passed"])

    def test_all_tests_green_but_stale_master_prompt_is_hold(self):
        company = {
            "research": {
                "quality_contract_version": 6,
                "master_prompt_sha256": MASTER_PROMPT_SHA256,
                "visual_concepts_protocol": "v1",
                "premium_visual_protocol": "v2",
                "premium_protocol": "v2",
            },
            "qa": {"overall_pass": True},
            "approval": {"approved": True},
            "public_release_evidence": public_evidence(),
        }
        self.assertEqual(inspect_release_safety(company)["status"], "HOLD")
        company["research"]["master_prompt_sha256"] = "stale-contract"
        result = inspect_release_safety(company)
        self.assertEqual(result["status"], "HOLD")
        self.assertTrue(any("master prompt" in x.lower() for x in result["issues"]))
        self.assertFalse(result["approved"])

    def test_missing_current_concept_and_review_evidence_is_hold(self):
        company = {
            "research": {
                "quality_contract_version": 6,
                "master_prompt_sha256": MASTER_PROMPT_SHA256,
                "visual_concepts_protocol": "v1",
                "premium_visual_protocol": "v2",
                "premium_protocol": "v2",
                "premium_independent_reviews": [],
            },
            "concept_previews": {"selection_sha256": "a" * 64},
            "qa": {"overall_pass": True},
            "approval": {"approved": True},
            "public_release_evidence": public_evidence(),
        }
        result = inspect_release_safety(company)
        self.assertEqual(result["status"], "HOLD")
        self.assertTrue(any("concept" in x.lower() for x in result["issues"]))
        self.assertFalse(result["approved"])


if __name__ == "__main__":
    unittest.main()

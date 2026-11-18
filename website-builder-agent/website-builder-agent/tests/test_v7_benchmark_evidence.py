"""V7 blind cohort evidence cannot be simulated by five versions of one design."""
from pathlib import Path
from tempfile import TemporaryDirectory
import base64
import unittest

from utils.v7_benchmark_evidence import (
    weighted_quality_score, assess_blind_campaign, validate_blind_record
)

PNG = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO9/7n8AAAAASUVORK5CYII="
)


def record(root, company="new-company", industry="repair"):
    for source in ("original", "preview"):
        folder = root / source
        folder.mkdir(parents=True, exist_ok=True)
        for width in ("mobile", "tablet", "desktop"):
            (folder / (width + ".png")).write_bytes(PNG)
    return {
        "company_id": company, "industry": industry,
        "source_url": "https://verified-original.example/",
        "preview_url": "https://live-preview.example/",
        "build_sha256": "1" * 64, "source_sha256": "2" * 64,
        "reviewer_id": "outside-human-1",
        "reviewer_kind": "independent_human",
        "synthetic": False, "first_attempt": True,
        "critical_issues": [], "live_browser_verified": True,
        "dimensions": {
            "brand_authenticity": 8, "composition": 8, "typography": 8,
            "media_motion": 8, "mobile_usability": 8, "natural_copy": 8,
            "micro_details": 8
        },
        "ai_looking_risk": 2,
        "screenshots": {
            src: {w: f"{src}/{w}.png" for w in ("mobile", "tablet", "desktop")}
            for src in ("original", "preview")
        },
    }


class BlindCampaignTests(unittest.TestCase):
    def test_no_record_is_not_evidence_of_quality(self):
        with TemporaryDirectory() as d:
            result = assess_blind_campaign([], evidence_root=Path(d))
        self.assertEqual(result["status"], "NOT_PROVEN")
        self.assertEqual(result["valid_distinct_companies"], 0)
        self.assertFalse(result["9_5_maturity_achieved"])

    def test_unverified_self_reviews_or_revised_attempts_are_excluded(self):
        with TemporaryDirectory() as d:
            row = record(Path(d))
            row["reviewer_kind"] = "builder"
            row["first_attempt"] = False
            errs = validate_blind_record(row, evidence_root=Path(d))
            self.assertTrue(any("independent" in error for error in errs))
            self.assertTrue(any("first-attempt" in error for error in errs))

    def test_numeric_score_cannot_imply_10_or_cover_missing_metrics(self):
        self.assertIsNone(weighted_quality_score({"typography": 10}))
        score = weighted_quality_score({
            "brand_authenticity": 9.5, "composition": 9.5,
            "typography": 9.5, "media_motion": 9.5, "mobile_usability": 9.5,
            "natural_copy": 9.5, "micro_details": 9.5,
        })
        self.assertEqual(score, 9.5)

    def test_single_client_or_fake_synthetic_records_never_establish_target(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            row = record(root)
            self.assertEqual(validate_blind_record(row, evidence_root=root), [])
            row["synthetic"] = True
            report = assess_blind_campaign([row] * 5, evidence_root=root)
            self.assertEqual(report["status"], "NOT_PROVEN")
            self.assertEqual(report["valid_distinct_companies"], 0)
            self.assertFalse(report["9_5_maturity_achieved"])

    def test_missing_or_unsafe_images_do_not_count_as_real_visual_evidence(self):
        with TemporaryDirectory() as d:
            root = Path(d)
            row = record(root)
            row["screenshots"]["preview"]["desktop"] = "../unsafe.png"
            errs = validate_blind_record(row, evidence_root=root)
            self.assertTrue(any("Missing actual" in e for e in errs))


if __name__ == "__main__":
    unittest.main()

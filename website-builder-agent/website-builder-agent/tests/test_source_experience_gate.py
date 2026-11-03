"""Offline regression tests: preserve original experience without inventing effects."""
import unittest

from utils.content_parity import source_inventory_sha256
from utils.source_experience_gate import (
    KINDS, audit_experience_continuity, build_digest, inspect_markup,
)

SOURCE_URL = "https://example.org/original"
ORIGINAL = {"source_inventory": {"pages": [{
    "url": SOURCE_URL, "title": "Original", "text": "Actual original craft site"
}]}}


def research_with_features(**present):
    inv = ORIGINAL["source_inventory"]
    return {
        "source_inventory": inv,
        "original_experience_profile": {
            "source_sha256": source_inventory_sha256(inv),
            "checked_at": "2026-11-03",
            "capture_method": "browser",
            "complete": True,
            "features": {kind: {
                "present": bool(present.get(kind, False)),
                **({"source_url": SOURCE_URL, "observation": "Observed in live desktop/mobile browser"}
                   if present.get(kind, False) else {}),
            } for kind in KINDS},
        }
    }


class ExperienceContinuityTests(unittest.TestCase):
    def test_no_original_site_is_not_forced_to_have_video_or_3d(self):
        r = audit_experience_continuity({"index.html": "<main>Hello</main>"}, {})
        self.assertEqual(r["blocking"], [])
        self.assertEqual(r["pending"], [])

    def test_existing_site_missing_profile_stays_review_required(self):
        r = audit_experience_continuity({"index.html": "<main>Hello</main>"}, ORIGINAL)
        self.assertEqual(r["original_profile_status"], "missing")
        self.assertTrue(r["pending"])

    def test_partial_original_browser_capture_is_never_treated_as_complete(self):
        r = research_with_features()
        r["original_experience_profile"]["complete"] = False
        result = audit_experience_continuity({"index.html": "<main>Hi</main>"}, r)
        self.assertTrue(any("did not cover every source page" in m for m in result["pending"]))

    def test_original_video_removed_without_script_blocks(self):
        r = audit_experience_continuity(
            {"index.html": "<main><h1>Craft shop</h1></main>"},
            research_with_features(video=True),
        )
        self.assertTrue(any("video" in message for message in r["blocking"]))

    def test_video_runtime_script_remains_pending_not_false_failure(self):
        r = audit_experience_continuity(
            {"index.html": '<main></main><script src="viewer.js"></script>'},
            research_with_features(video=True),
        )
        self.assertFalse(r["blocking"])
        self.assertTrue(any("runtime" in m for m in r["pending"]))

    def test_real_html_video_counts_as_media_not_final_certification(self):
        r = audit_experience_continuity(
            {"index.html": '<video controls><source type="video/mp4" src="approved.mp4"></video>'},
            research_with_features(video=True),
        )
        self.assertFalse(r["blocking"])
        self.assertTrue(any("human" in m.lower() for m in r["pending"]))

    def test_gallery_with_actual_images_cannot_be_replaced_by_only_text(self):
        r = audit_experience_continuity(
            {"index.html": '<img src="one.jpg" alt="Work">'}, research_with_features(gallery=True)
        )
        self.assertTrue(any("gallery" in m for m in r["blocking"]))

    def test_source_with_no_3d_does_not_require_new_3d(self):
        r = audit_experience_continuity(
            {"index.html": "<main>Still editorial layout</main>"},
            research_with_features(),
        )
        self.assertFalse(r["blocking"])
        self.assertFalse(any("3-D" in m for m in r["pending"]))

    def test_added_3d_requires_company_specific_rationale(self):
        r = audit_experience_continuity(
            {"index.html": "<model-viewer></model-viewer>"},
            research_with_features(),
        )
        self.assertTrue(any("New 3-D" in m for m in r["pending"]))

    def test_background_with_external_stylesheet_not_assumed_absent(self):
        r = audit_experience_continuity(
            {"index.html": '<link rel="stylesheet" href="style.css"><main>Hi</main>'},
            research_with_features(textured_background=True),
        )
        self.assertFalse(r["blocking"])
        self.assertTrue(any("linked CSS" in m for m in r["pending"]))

    def test_client_approved_specific_exception_stops_unsupported_video_block(self):
        pages = {"index.html": "<main>Client-approved new direction</main>"}
        r = research_with_features(video=True)
        r["experience_exceptions"] = [{
            "kind": "video", "reviewer_kind": "client", "reviewer": "Site owner",
            "reason": "Customer chose still work gallery for this version",
            "source_sha256": source_inventory_sha256(r["source_inventory"]),
            "build_sha256": build_digest(pages),
        }]
        outcome = audit_experience_continuity(pages, r)
        self.assertFalse(outcome["blocking"])

    def test_invalid_source_profile_hash_never_passes(self):
        r = research_with_features(video=True)
        r["original_experience_profile"]["source_sha256"] = "old"
        result = audit_experience_continuity({"index.html": "<video></video>"}, r)
        self.assertEqual(result["original_profile_status"], "missing")
        self.assertTrue(any("stale" in m for m in result["pending"]))

    def test_deterministic_markup_probe_still_distinguishes_video_from_illustration(self):
        data = inspect_markup({
            "index.html": '<svg role="img"><path d="M0 0"/></svg><div class="shoe"></div>'
        })
        self.assertFalse(data["video"])
        self.assertFalse(data["three_d"])
        self.assertFalse(data["photography"])


if __name__ == "__main__":
    unittest.main()

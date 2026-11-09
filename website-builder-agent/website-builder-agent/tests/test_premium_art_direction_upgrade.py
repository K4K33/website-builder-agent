"""No-credit regression suite for company-wide premium redesign standards."""
import json
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

from utils.premium_art_direction import audit_premium_art_direction
from utils.premium_quality_gate import (
    PAGE_PREMIUM_DIMENSIONS, VIEWPORTS, site_digest,
    verify_independent_premium_reviews,
)
from utils.concept_previews import write_concepts, load_verified_set, blind_order, record_selection
from utils.concept_workflow import source_visual_evidence
from tests.test_concept_previews import fixture, fake_renderer, selection_report, PNG

SRC = "https://artisan.example/"
PHOTOS = [f"https://artisan.example/project-{i}.jpg" for i in range(5)]


def photographed_source(*, form=False):
    page = {"url": SRC, "source_identity": {"original_content_photos": [
        {"src": p, "role": "gallery_photo"} for p in PHOTOS
    ]}}
    if form:
        page["source_content_blocks"] = {"original_form": True}
        page["forms"] = [{"action": "/inquiry", "fields": [
            {"type": "email"}, {"type": "textarea"}]}]
    return {"premium_visual_protocol": "v2",
            "source_inventory": {"pages": [page]}}


class PremiumArtDirectionTests(unittest.TestCase):
    def test_placeholder_material_panels_cannot_replace_real_artisan_photos(self):
        research = photographed_source()
        bad = {"index.html":
            '<main><h1>Studio</h1><section class="surface-abstract">'
            '<figure aria-label="Graafinen materiaalitutkielma"></figure>'
            '</section></main>'}
        audit = audit_premium_art_direction(bad, research)
        self.assertTrue(audit["blocking"])
        self.assertIn("generic decorative", audit["blocking"][0])

    def test_authentic_photo_and_brand_texture_are_not_arbitrarily_rejected(self):
        research = photographed_source()
        html = '<main><h1>Studio</h1><section class="brand-geometric-pattern">' \
               f'<img src="{PHOTOS[0]}" alt="Actual work"></section></main>'
        audit = audit_premium_art_direction({"index.html": html}, research)
        self.assertFalse(audit["blocking"])
        self.assertTrue(audit["pending"])  # aesthetic/rights require actual proof

    def test_original_real_contact_form_cannot_be_downgraded_to_mailto(self):
        research = photographed_source(form=True)
        only_mailto = {"index.html":
                       '<main><h1>Contact</h1><a href="mailto:example@example.org">Email us</a></main>'}
        audit = audit_premium_art_direction(only_mailto, research)
        self.assertTrue(any("mailto" in s for s in audit["blocking"]))

    def test_real_form_markup_requires_live_delivery_evidence(self):
        research = photographed_source(form=True)
        real_form = {"index.html":
                     '<main><h1>Contact</h1><form method="post">'
                     '<input type="email"><textarea></textarea><button>Send</button>'
                     '</form></main>'}
        audit = audit_premium_art_direction(real_form, research)
        self.assertFalse(audit["blocking"])
        self.assertTrue(any("end-to-end POST" in s for s in audit["pending"]))

    def test_truncated_or_unreviewed_brand_signature_is_not_approved(self):
        research = photographed_source()
        report = audit_premium_art_direction({"index.html": "<main><h1>Studio</h1></main>"}, research)
        self.assertTrue(any("visual signature" in s for s in report["pending"]))


class IndependentPageReviewTests(unittest.TestCase):
    def evidence(self, root, pages, research):
        img = Path(root) / "real-image.png"
        img.write_bytes(PNG)
        reviews = []
        for i in (1, 2):
            reviews.append({
                "reviewer_id": f"independent-reviewer-{i}",
                "independent_of_builder": True,
                "provenance_human_verified": True,
                "critical_issues": [],
                "evidence_reference": f"verified-review-{i}",
                "scores": {k: 9.6 for k in (
                    "visual_design", "originality", "brand_fidelity",
                    "content_fidelity", "real_photography", "natural_copy",
                    "usability", "mobile", "accessibility", "interaction_quality")},
                "screenshots": {vp: str(img) for vp in VIEWPORTS},
                "pages_reviewed": list(pages),
                "page_scores": {
                    route: {dim: 9.6 for dim in PAGE_PREMIUM_DIMENSIONS}
                    for route in pages
                },
                "route_screenshots": {
                    route: {vp: str(img) for vp in VIEWPORTS}
                    for route in pages
                },
                "page_observations": {
                    route: "Actual source versus new rendered design, "
                           "brand-pattern, photographic roles and usability checked."
                    for route in pages
                },
            })
        return {"build_sha256": site_digest(pages), "reviewers": reviews}

    def test_full_review_of_each_page_can_pass_only_with_actual_evidence(self):
        research = {"premium_visual_protocol": "v2"}
        pages = {"index.html": "<main>Home</main>",
                 "palvelut/index.html": "<main>Services</main>"}
        with TemporaryDirectory() as folder:
            evidence = self.evidence(folder, pages, research)
            report = verify_independent_premium_reviews(evidence, pages, research)
            self.assertTrue(report["pass"], report["issues"])

    def test_a_great_home_does_not_hide_a_weak_services_page(self):
        research = {"premium_visual_protocol": "v2"}
        pages = {"index.html": "<main>Home</main>",
                 "palvelut/index.html": "<main>Services</main>"}
        with TemporaryDirectory() as folder:
            evidence = self.evidence(folder, pages, research)
            evidence["reviewers"][1]["page_scores"]["palvelut/index.html"]["premium_appeal"] = 7.4
            report = verify_independent_premium_reviews(evidence, pages, research)
            self.assertFalse(report["pass"])
            self.assertTrue(any("palvelut/index.html" in s for s in report["issues"]))

    def test_missing_phone_capture_and_per_route_reason_cannot_pass(self):
        research = {"premium_visual_protocol": "v2"}
        pages = {"index.html": "<main>Home</main>", "yhteys/index.html": "<main>Contact</main>"}
        with TemporaryDirectory() as folder:
            evidence = self.evidence(folder, pages, research)
            del evidence["reviewers"][0]["route_screenshots"]["yhteys/index.html"]["mobile"]
            evidence["reviewers"][0]["page_observations"]["yhteys/index.html"] = "Great."
            report = verify_independent_premium_reviews(evidence, pages, research)
            self.assertFalse(report["pass"])
            self.assertTrue(any("screenshot" in s for s in report["issues"]))
            self.assertTrue(any("no concrete" in s for s in report["issues"]))


class PremiumConceptChoiceTests(unittest.TestCase):
    def test_winner_requires_all_real_views_and_source_brand_reasons(self):
        research, variants = fixture()
        research["premium_visual_protocol"] = "v2"
        research["research_mode"] = "verified_no_website"
        with TemporaryDirectory() as folder:
            ref = write_concepts(json.dumps(variants), research, output_parent=folder,
                                 producer="fixture-author", renderer=fake_renderer)
            _, manifest = load_verified_set(ref, research, allowed_root=folder)
            report = selection_report(manifest)
            report["view_assessments"] = {
                v["id"]: {
                    "verdict": "pass",
                    "brand_evidence": "Original company name and sourced type treatment are preserved.",
                    "composition_evidence": "The real rendered hero and content route have balanced photo hierarchy.",
                    "media_evidence": "No invented photography or misleading product illustration appears.",
                }
                for entry in manifest["entries"] for v in entry["views"]
            }
            report["source_reference_reviewed"] = False
            ref, choice = record_selection(ref, research, report,
                                           allowed_root=folder, reviewer="fixture-critic")
            self.assertIn(choice["selected_id"], {"concept_1", "concept_2", "concept_3"})
            self.assertFalse(ref.get("premium_approval", False))

    def test_one_mediocre_winning_subpage_forces_revision(self):
        research, variants = fixture()
        research["premium_visual_protocol"] = "v2"
        research["research_mode"] = "verified_no_website"
        with TemporaryDirectory() as folder:
            ref = write_concepts(json.dumps(variants), research, output_parent=folder,
                                 producer="fixture-author", renderer=fake_renderer)
            _, manifest = load_verified_set(ref, research, allowed_root=folder)
            report = selection_report(manifest)
            report["view_assessments"] = {
                v["id"]: {
                    "verdict": "pass",
                    "brand_evidence": "Verified company identity visible on the image and header.",
                    "composition_evidence": "Responsive composition has a clear and distinctive hero.",
                    "media_evidence": "Genuine source pictures or legitimate text-only layout appear.",
                }
                for e in manifest["entries"] for v in e["views"]
            }
            winning = blind_order(manifest)["B"]["views"][-1]["id"]
            report["view_assessments"][winning]["verdict"] = "needs_revision"
            with self.assertRaisesRegex(RuntimeError, "deficient route"):
                record_selection(ref, research, report, allowed_root=folder, reviewer="fixture-critic")

    def test_existing_site_without_original_screens_is_blocked(self):
        with self.assertRaisesRegex(RuntimeError, "original desktop"):
            source_visual_evidence({"premium_visual_protocol": "v2",
                                    "original_screenshots": {}})

    def test_valid_source_screens_are_bound_to_safe_root(self):
        with TemporaryDirectory() as root:
            screenshots = Path(root) / "safe"; screenshots.mkdir()
            a, b = screenshots / "desktop.png", screenshots / "mobile.png"
            a.write_bytes(PNG); b.write_bytes(PNG)
            with patch("utils.screenshot.OUTPUT_DIR", str(screenshots)):
                evidence = source_visual_evidence({
                    "premium_visual_protocol": "v2",
                    "original_screenshots": {"desktop": str(a), "mobile": str(b)}})
            self.assertEqual(len(evidence), 2)
            self.assertTrue(all(e["sha256"] for e in evidence))


if __name__ == "__main__":
    unittest.main()

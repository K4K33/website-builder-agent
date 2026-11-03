"""V6: universal verified-brand-character gates; zero API / synthetic companies only."""
from __future__ import annotations
from copy import deepcopy
import unittest

from utils.brand_experience import audit_brand_experience, REVIEW_ITEMS, REVIEW_WIDTHS
from utils.content_parity import source_inventory_sha256
from utils.premium_quality_gate import site_digest
from utils.source_identity import extract_source_identity
from utils.brand_design_blueprint import derive_brand_site_blueprint
from utils.universal_quality import audit_universal_standards


SOURCE = "https://fictional-florist.example.invalid/"
OLD = """<html><head><meta name="theme-color" content="#f2dadf"></head>
 <body><header><a class="brand" href="/">
 <img src="/flower.svg" alt="Flower sign"><span class="site-title">Pienet Kukkaset</span>
 </a></header><main><h1>Flowers for life</h1>
 <img src="/actual-flowers.jpg" alt="Real original work"></main></body></html>"""


def pages():
    return {"index.html": (
        '<html><body><header><a href="/"><img class="brand-logo"'
        ' src="https://fictional-florist.example.invalid/flower.svg">'
        '<strong>Pienet Kukkaset</strong></a></header>'
        '<main><h1>Kimput ja kukat</h1></main></body></html>'
    )}


def research():
    return {"company_facts": {"name": "Pienet Kukkaset", "industry": "Kukkakauppa"},
            "source_inventory": {"pages": [{
                "url": SOURCE,
                "source_identity": extract_source_identity(OLD, SOURCE),
            }]}}


def review(source, rendered):
    return {
        "verified": True,
        "reviewer_kind": "independent_human",
        "reviewer_id": "Reviewer 01",
        "evidence_reference": "reviewed-real-images-dummy-test",
        "build_sha256": site_digest(rendered),
        "source_sha256": source_inventory_sha256(source["source_inventory"]),
        "routes_reviewed": list(rendered),
        "screenshots": {
            side + "_" + str(width): "evidence/side-by-side/" + side + str(width) + ".png"
            for side in ("original", "redesign") for width in REVIEW_WIDTHS
        },
        "findings": {
            name: {"ok": True,
                   "explanation": "Reviewer checked the original and new design screenshots."}
            for name in REVIEW_ITEMS
        }
    }


class BrandExperienceV6Tests(unittest.TestCase):
    def test_source_capture_real_wordmark_not_inferred_font(self):
        identity = extract_source_identity(OLD, SOURCE)
        self.assertEqual(identity["original_header_wordmark_candidates"], ["Pienet Kukkaset"])
        self.assertEqual(identity["original_logo_candidates"], [SOURCE + "flower.svg"])
        self.assertEqual(identity["original_content_photos"][0]["src"], SOURCE + "actual-flowers.jpg")
        self.assertEqual(identity["theme_color"], "#f2dadf")
        # We do not invent script/handwriting from the text alone.
        self.assertNotIn("original_font_family", identity)

    def test_unreviewed_visual_fidelity_is_pending_even_with_matching_source_logo(self):
        data, rendered = research(), pages()
        result = audit_brand_experience(rendered, data)
        self.assertFalse(result["blocking"], result)
        self.assertIn("No source-to-new first-screen visual comparison record.", result["pending"])
        universal = audit_universal_standards(rendered["index.html"], data, rendered_pages=rendered)
        self.assertIn("original_brand_experience", universal["pending_categories"])
        self.assertIn("first_view_visual_priority", universal["pending_categories"])
        self.assertFalse(universal["client_release_ready"])

    def test_approved_logo_does_not_override_no_visual_review(self):
        data, rendered = research(), pages()
        data["brand_assets"] = {"approved_original_logo_url": SOURCE + "flower.svg"}
        audit = audit_brand_experience(rendered, data)
        self.assertFalse(audit["pass"])
        self.assertTrue(audit["pending"])

    def test_declared_unapproved_rebranding_blocks_release(self):
        data, rendered = research(), pages()
        data["brand_character_plan"] = {
            "replace_wordmark": True,
            "replace_brand_character": True,
        }
        result = audit_brand_experience(rendered, data)
        self.assertEqual(result["blocking"][0]["category"], "unapproved_visual_rebrand")
        audit = audit_universal_standards(rendered["index.html"], data, rendered_pages=rendered)
        self.assertIn("original_brand_experience", audit["blocking_categories"])
        self.assertEqual(audit["quality_decision"], "blocked")

    def test_wrong_source_or_build_invalidates_comparison(self):
        data, rendered = research(), pages()
        data["brand_experience_review"] = review(data, rendered)
        result = audit_brand_experience(rendered, data)
        self.assertTrue(result["pass"], result)
        changed = {"index.html": rendered["index.html"] + " "}
        self.assertFalse(audit_brand_experience(changed, data)["pass"])
        altered = deepcopy(data)
        altered["source_inventory"]["pages"][0]["source_identity"]["theme_color"] = "#202020"
        self.assertFalse(audit_brand_experience(rendered, altered)["pass"])

    def test_missing_any_route_or_evidence_is_pending(self):
        rendered = pages()
        rendered["yhteys/index.html"] = "<html><body><main>Yhteys</main></body></html>"
        data = research()
        record = review(data, rendered)
        record["routes_reviewed"] = ["index.html"]
        record["screenshots"].pop("original_320")
        record["findings"]["palette_character"] = {
            "ok": False, "explanation": "Dark new identity conflicts with original soft palette."
        }
        data["brand_experience_review"] = record
        result = audit_brand_experience(rendered, data)
        self.assertTrue(any("every route" in item for item in result["pending"]))
        self.assertTrue(any("original_320" in item for item in result["pending"]))
        self.assertTrue(any("palette_character" in item for item in result["pending"]))

    def test_company_approval_must_match_exact_source_and_site(self):
        data, rendered = research(), pages()
        data["brand_character_plan"] = {"replace_wordmark": True}
        data["brand_experience_review"] = review(data, rendered)
        approval = {
            "approved": True, "reviewer_kind": "client",
            "reviewer": "Fictional owner", "approval_reference": "signed-example",
            "build_sha256": site_digest(rendered),
            "source_sha256": source_inventory_sha256(data["source_inventory"]),
        }
        data["brand_character_change_approval"] = approval
        self.assertTrue(audit_brand_experience(rendered, data)["pass"])
        data["brand_character_change_approval"]["source_sha256"] = "wrong-source"
        self.assertFalse(audit_brand_experience(rendered, data)["pass"])
        self.assertTrue(audit_brand_experience(rendered, data)["blocking"])

    def test_no_site_research_never_invents_a_brand_comparison(self):
        data = {"research_mode": "verified_no_website",
                "source_inventory": {"pages": []}}
        result = audit_brand_experience(pages(), data)
        self.assertTrue(result["pass"])
        self.assertFalse(result["source_sha256"])

    def test_blueprint_includes_real_observed_wordmark(self):
        data = research()
        data.update({
            "site_architecture": {"pages": [{"path": "index.html",
                                             "purpose": "Order real floral arrangements",
                                             "user_task": "Call the florist"}]},
            "creative_directions": [{"id": "actual-floral",
                                     "source_anchor": "Real original flowers"}],
            "creative_selection": {"selected_id": "actual-floral"},
        })
        bp = derive_brand_site_blueprint(data)
        system = bp["shared_brand_system"]
        self.assertEqual(system["original_header_wordmark_candidates"][0]["text"], "Pienet Kukkaset")
        self.assertTrue(system["compare_original_full_wordmark_not_just_logo"])
        self.assertTrue(system["source_vs_redesign_mobile_320_390_review_required"])
        self.assertEqual(system["first_screen_source_photo_references"][0]["url"],
                         SOURCE + "actual-flowers.jpg")


if __name__ == "__main__":
    unittest.main()

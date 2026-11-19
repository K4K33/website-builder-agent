"""Original media before improvised rotating product illustrations.

Real photo / video motion is allowed; small icons and approved client vector
assets are allowed. Tests are offline and cannot certify artistic quality.
"""
from __future__ import annotations

import copy
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from utils.authentic_media_direction import audit_hero_media, source_media_evidence


def researched():
    return {
        "v8_visual_protocol": "v8",
        "company_facts": {"name": "Korjaamo Oy", "services": ["Rengashuolto"]},
        "source_inventory": {
            "pages": [{
                "url": "https://korjaamo.example/palvelut",
                "source_identity": {
                    "original_content_photos": [
                        {"src": "https://korjaamo.example/kuvat/renkaat.jpg", "alt": "Aito rengas"}
                    ],
                    "original_logo_candidates": ["https://korjaamo.example/logo.svg"],
                },
                "images": []
            }]
        },
    }


def site(content, css=""):
    return (
        '<!doctype html><html><head><style>' + css + '</style></head>'
        '<body><header><nav>Korjaamo Oy</nav></header><main><section class="hero">'
        '<h1>Rengashuolto</h1>' + content
        + '</section><section><p>Palvelut ja yhteystiedot</p></section>'
        '</main></body></html>'
    )


class AuthenticMediaFirstV8(unittest.TestCase):
    def test_original_photo_observation_never_creates_licence_or_changes_research(self):
        research = researched()
        before = copy.deepcopy(research)
        evidence = source_media_evidence(research)
        self.assertEqual(evidence["original_photo_candidate_count"], 1)
        self.assertEqual(evidence["staged_real_photo_count"], 0)
        self.assertTrue(evidence["original_photos_are_not_licensed_by_observation"])
        self.assertEqual(before, research)

    def test_css_drawn_spinning_wheel_cannot_replace_real_tire_hero(self):
        css = """
        .hero-wheel .rim{border-radius:50%;background:radial-gradient(circle,#555,#111)}
        .hero-wheel{animation:rotate 10s linear infinite}
        @keyframes rotate{to{transform:rotate(360deg)}}
        """
        content = "<div class='hero-wheel'><i class='rim'></i><i class='spoke'></i></div>"
        result = audit_hero_media({"index.html": site(content, css)}, researched())
        self.assertFalse(result["pass"])
        self.assertIn("css_drawn_real_world_object",
                      result["blocking"][0]["evidence"])

    def test_small_wheel_icon_with_unrelated_page_fade_is_not_falsely_blocked(self):
        css = """
        .small-wheel-icon{font-size:14px;color:inherit}
        .hero p{animation:fade .4s}
        @keyframes fade{from{opacity:0}to{opacity:1}}
        """
        result = audit_hero_media(
            {"index.html": site("<span class='small-wheel-icon'>●</span>", css)}, researched())
        self.assertTrue(result["pass"])

    def test_photographic_css_background_not_mistaken_for_illustrated_tire(self):
        css = (
            ".wheel{background-image:url('assets/real-tire.jpg');"
            "border-radius:50%;height:300px;width:300px}"
        )
        result = audit_hero_media(
            {"index.html": site("<div class='wheel'></div>", css)}, researched())
        self.assertTrue(result["pass"])
        # Local file delivery and rights are checked by other media gates.

    def test_large_vector_tire_art_is_rejected_even_with_misleading_premium_label(self):
        svg = ('<svg viewBox="0 0 640 540" class="premium-product">'
               '<g class="tire" aria-label="rengas"><circle cx="200" cy="200" r="180"/>'
               '</g></svg>')
        result = audit_hero_media({"index.html": site(svg)}, researched())
        self.assertEqual(result["blocking"][0]["code"], "fake_real_world_object_hero")

    def test_giant_unlabelled_generated_svg_scene_is_not_automatically_premium(self):
        svg = ('<svg viewBox="0 0 620 500">'
               + '<path d="M0 0 L100 100"/>' * 9 + '</svg>')
        result = audit_hero_media({"index.html": site(svg)}, researched())
        self.assertFalse(result["pass"])

    def test_text_first_hero_allowed_when_image_rights_not_available(self):
        research = researched()
        result = audit_hero_media(
            {"index.html": site("<p>Huollamme ja vaihdamme renkaat</p>")}, research)
        self.assertTrue(result["pass"])
        self.assertEqual(result["blocking"], [])

    def test_genuine_photo_with_subtle_motion_allowed(self):
        css = """
        .photo{transition:transform .3s ease}
        .photo:hover{transform:scale(1.015)}
        @media(prefers-reduced-motion:reduce){.photo{transition:none}}
        """
        body = '<figure><img class="photo" src="assets/tyo.jpg" alt="Oikea huoltotyö"></figure>'
        result = audit_hero_media({"index.html": site(body, css)}, researched())
        self.assertTrue(result["pass"])
        self.assertTrue(result["real_motion_is_not_banned"])

    def test_real_approved_client_video_allowed(self):
        result = audit_hero_media(
            {"index.html": site('<video controls src="assets/oikea-korjaamo.webm"></video>')},
            researched())
        self.assertTrue(result["pass"])

    def test_tiny_functional_svg_icon_not_banned(self):
        body = ('<svg width="24" height="24" viewBox="0 0 24 24" aria-hidden="true">'
                '<path d="M0 0 L20 20"/></svg>')
        result = audit_hero_media({"index.html": site(body)}, researched())
        self.assertTrue(result["pass"])

    def test_real_original_company_vector_brand_not_banned(self):
        body = '<svg viewBox="0 0 620 300" class="original-logo">'
        body += '<path d="M0 0 L200 200"/>' * 10 + '</svg>'
        self.assertTrue(audit_hero_media({"index.html": site(body)}, researched())["pass"])

    def test_previously_approved_staged_svg_asset_is_not_misclassified_as_fabrication(self):
        image = '<img src="assets/original-wheel.svg" alt="Korjaamon dokumentoitu alkuperäinen kuva">'
        approved = [{"src": "assets/original-wheel.svg", "rights_status": "client_approved"}]
        report = audit_hero_media({"index.html": site(image)}, researched(), media_items=approved)
        self.assertTrue(report["pass"])

    def test_unknown_svg_tyre_file_is_held_for_review_as_unverified(self):
        image = '<img src="assets/fake-wheel.svg" alt="Tyre service">'
        report = audit_hero_media({"index.html": site(image)}, researched())
        self.assertFalse(report["pass"])

    def test_ordinary_non_illustration_motion_survives_without_photo(self):
        css = '.hero h1{animation:reveal .45s ease} @keyframes reveal{from{opacity:0}to{opacity:1}}'
        result = audit_hero_media({"index.html": site("<p>Rengashuolto</p>",css)}, researched())
        self.assertTrue(result["pass"])

    def test_final_qa_and_concept_engine_really_call_media_gate(self):
        from agents import qa
        from utils import concept_previews
        import inspect
        self.assertIn("authentic_media = audit_hero_media(", inspect.getsource(qa.run_qa))
        self.assertIn("authentic_media = audit_hero_media(", inspect.getsource(concept_previews.write_concepts))
        self.assertIn('and authentic_media["pass"]', inspect.getsource(qa.run_qa))

    def test_qa_repair_planner_includes_media_defects(self):
        from utils.visual_revision import decide_revision
        report = {
            "overall_pass": False,
            "authentic_media_direction": {
                "blocking": [{
                    "route": "index.html",
                    "code": "fake_real_world_object_hero",
                    "repair": "Use approved photo or a clean text-first layout."
                }]
            }
        }
        decision = decide_revision(report)
        self.assertTrue(decision["revise"])
        self.assertIn("fake_real_world_object_hero",
                      " ".join(decision["feedback"]["actionable_defects"]))


if __name__ == "__main__":
    unittest.main()

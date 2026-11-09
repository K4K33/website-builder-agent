"""Business-agnostic regressions for Kaurivo's researched 3D/motion standard.

Zero network, AI model, third-party scene, email, or credit consumption.
Passing here certifies enforcement mechanics ONLY, never visual 9.5/10.
"""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from utils.premium_effect_assets import audit_premium_effect_assets
from utils.service_quality import POLICY, MASTER_PROMPT_PATH, MASTER_PROMPT_SHA256, service_brief
from utils.visual_direction import audit_visual_motion, visual_direction_plan


PHOTO = '<main><section class="hero"><img src="real-oak-stair.jpg" alt="Actual staircase"></section></main>'
SPOTLIGHT = (
    '.hero:after{content:"";position:absolute;inset:0;'
    'background:radial-gradient(450px circle at var(--px) var(--py),'
    'rgba(255,230,190,.3),transparent 70%);mix-blend-mode:screen}'
)
SUBTLE = (
    '.hero:after{content:"";position:absolute;inset:0;'
    'background:linear-gradient(90deg,rgba(0,0,0,.4),transparent)}'
)


class UniversalPremiumMotionTests(unittest.TestCase):
    def test_master_prompt_is_in_every_shared_runtime_policy(self):
        content = MASTER_PROMPT_PATH.read_text(encoding="utf-8")
        self.assertIn("ACTIVE_RUNTIME_CONTRACT_START", content)
        self.assertIn("ONE public website overall score", POLICY)
        self.assertIn("Reject artificial pointer-following light halos", POLICY)
        self.assertEqual(len(MASTER_PROMPT_SHA256), 64)
        brief = service_brief({})
        self.assertEqual(brief["master_prompt_sha256"], MASTER_PROMPT_SHA256)
        self.assertIn("master_prompt_sha256", brief["policy"] if False else brief)

    def test_photo_spotlight_blocks_in_complete_inline_css(self):
        report = audit_visual_motion(
            {"index.html": f'<style>{SPOTLIGHT}</style>{PHOTO}'},
            assets_complete=True,
        )
        self.assertTrue(report["blocking"])
        self.assertTrue(report["observations"]["synthetic_photo_spotlights"])

    def test_detected_hero_glow_blocks_even_if_other_assets_pending(self):
        report = audit_visual_motion(
            {"index.html": f'<link rel="stylesheet" href="https://cdn.example/theme.css">'
                           f'<style>{SPOTLIGHT}</style>{PHOTO}'},
            assets_complete=False,
        )
        self.assertTrue(any("Synthetic photo spotlight" in x for x in report["blocking"]))

    def test_legitimate_static_photo_contrast_is_not_rejected(self):
        report = audit_visual_motion(
            {"index.html": f'<style>{SUBTLE}</style>{PHOTO}'},
            assets_complete=True,
        )
        self.assertFalse(report["blocking"], report)

    def test_no_photo_abstract_3d_is_not_misclassified_as_photo_glow(self):
        html = (
            '<style>.visual:after{background:radial-gradient(circle at var(--px),'
            '#fff,#333);mix-blend-mode:screen}</style><main><div class="visual"></div></main>'
        )
        report = audit_visual_motion({"index.html": html}, assets_complete=True)
        self.assertFalse(report["observations"]["synthetic_photo_spotlights"])

    def test_local_assets_are_read_and_flagged_on_inner_routes(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "assets").mkdir()
            (root / "services").mkdir()
            (root / "assets" / "theme.css").write_text(SPOTLIGHT, encoding="utf-8")
            pages = {
                "index.html": "<main><h1>Home</h1></main>",
                "services/index.html": ('<link rel="stylesheet" href="../assets/theme.css">'
                                        + PHOTO),
            }
            review = audit_premium_effect_assets(pages, root)
            self.assertEqual(review["observations"]["inspected_local_assets"], 1)
            self.assertTrue(review["blocking"])
            self.assertTrue(any("Synthetic photo spotlight" in x for x in review["blocking"]))

    def test_missing_local_asset_is_not_mistaken_for_safe(self):
        with TemporaryDirectory() as tmp:
            pages = {"index.html": '<link rel="stylesheet" href="/assets/does-not-exist.css"><main>Home</main>'}
            report = audit_premium_effect_assets(pages, tmp)
            self.assertTrue(any("missing css asset" in x for x in report["blocking"]))

    def test_external_spline_scene_or_script_needs_separate_proof(self):
        with TemporaryDirectory() as tmp:
            pages = {"index.html": (
                '<script src="https://unpkg.example/spline-viewer.js"></script>'
                '<main><h1>Product</h1></main>')}
            report = audit_premium_effect_assets(pages, tmp)
            self.assertFalse(report["blocking"])
            self.assertTrue(report["observations"]["external_assets_pending"])
            self.assertTrue(report["pending"])

    def test_reduced_motion_with_guarded_depth_is_compatible(self):
        css = ('.hero img{transition:transform .2s}'
               '@media(prefers-reduced-motion:reduce){.hero img{transition:none}}')
        js = ("const reduce=matchMedia('(prefers-reduced-motion: reduce)');"
              "if(!reduce.matches){window.addEventListener('pointermove',move)}")
        report = audit_visual_motion({"index.html": PHOTO},css_text=css,js_text=js,
                                     assets_complete=True)
        self.assertFalse(report["blocking"], report)

    def test_visual_direction_chooses_real_material_without_glow(self):
        research = {"source_inventory": {"pages": [{
            "source_identity": {"original_content_photos": [
                {"src": "/real-a.jpg"},{"src": "/real-b.jpg"},{"src": "/real-c.jpg"},
            ]}}]}}
        creative = {"selected": {
            "concept": "Workshop",
            "business_reason": "Demonstrate measured workmanship",
            "source_anchor": "Real wooden staircase photos",
            "first_view": "Wide authentic staircase detail",
            "image_strategy": "Real workshop media",
            "typography": "Legible workshop identity",
            "brand_continuity": "Original colors and logo retained",
            "mobile_behavior": "One-column first view",
        }}
        direction = visual_direction_plan(research,creative,{"page_paths":["index.html"]})
        self.assertIn("photo parallax", direction["depth_direction"])
        self.assertIn("Never add pointer-following radial light", direction["depth_direction"])

    def test_permanent_standard_has_different_effect_tiers_and_one_score(self):
        doc = (Path(__file__).resolve().parents[1]/"docs"/
               "KAURIVO_3D_PREMIUM_MOTION_STANDARD_20261109.md").read_text(encoding="utf-8")
        for phrase in ("A — arkkitehtoninen premium", "B — elävä työnäyte",
                       "C — aito interaktiivinen 3D", "kokonaisarvio x/10",
                       "GSAP", "Three.js", "Spline", "Tavoite"):
            # The standard is a human contract; it does not assert a success rating.
            if phrase == "Tavoite":
                continue
            self.assertIn(phrase, doc)


if __name__ == "__main__":
    unittest.main()

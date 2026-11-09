"""Regression tests for brand-specific depth and accessible, progressive motion."""
import unittest
from utils.visual_direction import visual_direction_plan, audit_visual_motion


def direction():
    return {"selected": {
        "concept": "Architectural glasswork editorial exhibition",
        "business_reason": "Clients must judge actual restored windows before requesting a quote.",
        "source_anchor": "Original window portfolio from photographed artisan work",
        "first_view": "Oversized authentic window detail followed by workshop context",
        "image_strategy": "Use approved original project imagery with a variable editorial grid",
        "typography": "Keep the actual business identity and readable type hierarchy",
        "brand_continuity": "Preserve the company's original visible brand and colors",
        "mobile_behavior": "Single column, focusable gallery and non-obscuring navigation",
    }}


class VisualDirectionTests(unittest.TestCase):
    def test_plan_follows_authentic_media_and_selected_concept(self):
        source = {"source_inventory": {"pages": [{
            "source_identity": {"original_content_photos": [
                {"src": "/work-a.jpg"}, {"src": "/work-b.jpg"},
                {"src": "/work-c.jpg"}]}}]}}
        result = visual_direction_plan(source, direction(), {
            "page_paths": ["index.html", "tyot/index.html", "yhteystiedot/index.html"]})
        self.assertIn("original project", result["image_strategy"])
        self.assertIn("parallax", result["depth_direction"])
        self.assertIn("reduced-motion", result["motion_safety"])
        self.assertEqual(len(result["route_tasks"]), 3)
        self.assertIn("Original window portfolio", result["source_anchor"])

    def test_sober_source_allows_deliberate_restraint_not_forced_3d(self):
        result = visual_direction_plan(
            {}, direction(), {"page_paths": ["index.html", "palvelut/index.html"]})
        self.assertIn("typography", result["depth_direction"])
        self.assertIn("restraint", result["motion_decision"])
        self.assertNotIn("3D model", result["depth_direction"])

    def test_missing_design_choice_does_not_pass_prebuild(self):
        with self.assertRaises(RuntimeError):
            visual_direction_plan({}, {"selected": {}}, {"page_paths": ["index.html"]})

    def test_keyframe_animation_without_reduced_motion_is_blocked_with_full_css(self):
        pages = {"index.html": "<main><h1>Demo</h1></main>"}
        report = audit_visual_motion(
            pages, css_text="@keyframes float {to { transform:translateY(5px) }} "
                                 ".hero{animation:float 2s infinite}",
            assets_complete=True)
        self.assertTrue(report["blocking"])
        self.assertTrue(report["observations"]["css_animation"])

    def test_js_pointer_motion_without_guard_is_blocked(self):
        report = audit_visual_motion(
            {"index.html": "<main>Example</main>"},
            js_text="document.addEventListener('pointermove', move);",
            assets_complete=True)
        self.assertTrue(report["blocking"])

    def test_guarded_motion_passes_objective_accessibility_lint(self):
        report = audit_visual_motion(
            {"index.html": "<main>Example</main>"},
            css_text=("@keyframes reveal{to{opacity:1}} "
                      ".art{animation:reveal 400ms both} "
                      "@media (prefers-reduced-motion: reduce) {"
                      ".art{animation:none}}"),
            js_text=("const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;"
                     "if (!reduce) requestAnimationFrame(tick)"),
            assets_complete=True)
        self.assertFalse(report["blocking"])
        self.assertTrue(report["observations"]["css_reduced_motion"])
        self.assertTrue(report["observations"]["js_reduced_motion"])
        # A successful static lint cannot claim good real-world aesthetics.
        self.assertTrue(report["pending"])

    def test_incomplete_external_assets_are_pending_not_falsely_safe(self):
        html = "<link rel='stylesheet' href='/remote-theme.css'><main>Example</main>"
        report = audit_visual_motion(
            {"index.html": html},
            css_text=".art{animation:fade 2s infinite}", assets_complete=False)
        self.assertFalse(report["blocking"])
        self.assertTrue(any("full asset inspection" in str(x) for x in report["pending"]))

    def test_purposefully_static_site_remains_possible(self):
        report = audit_visual_motion(
            {"index.html": "<main><h1>Architect</h1></main>"}, assets_complete=True)
        self.assertFalse(report["blocking"])
        self.assertTrue(any("deliberate restraint" in s for s in report["pending"]))


if __name__ == "__main__":
    unittest.main()

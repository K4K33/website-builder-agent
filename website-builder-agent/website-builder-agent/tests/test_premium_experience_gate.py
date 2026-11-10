"""Regressions from 2026-11-10 Verhoomo 3 Ässää owner video feedback.

These tests prove an automatic hard block is implemented. They do not
claim the current demo has been corrected, or that unseen clients passed.
"""
from unittest import TestCase
from utils.premium_experience_gate import audit_premium_experience


BAD_COMPARE = """<main><div class="comparison"><div class="comparison-canvas">
<div class="comparison-before"><img src="before.jpg"></div>
<div class="comparison-after"><img src="after.jpg"></div>
<div class="comparison-split"></div></div>
<input aria-label="Compare" type="range" value="50" min="0" max="100">
</div></main>"""
BAD_SWATCH = """<main><section class="fabric-section"><h2>Materials</h2>
<div class="fabric-rack"><div class="swatch a"></div>
<div class="swatch b"></div><div class="swatch c"></div></div></section></main>"""
CSS = """.fabric-rack{perspective:950px}.swatch{background:#8a6543;
transform:rotate(15deg)}.comparison-split:after{content:'↔'}"""


class PremiumExperienceRegressionTests(TestCase):
    def test_video_bug_detached_input_cannot_replace_dragging_image(self):
        result = audit_premium_experience(
            {"index.html":BAD_COMPARE},
            js_text="input.addEventListener('input',update);"
                    "box.style.setProperty('--split',input.value+'%')",
        )
        self.assertIn(
            "comparison_handle_not_directly_draggable",
            {x["kind"] for x in result["blocking"]},
        )
        self.assertEqual(result["status"], "HOLD")

    def test_real_pointer_capture_plus_keyboard_control_passes_static_guard(self):
        js = """
        document.querySelectorAll('.comparison-canvas').forEach(canvas=>{
          canvas.addEventListener('pointerdown',onStart)
          canvas.addEventListener('pointermove',onMove)
          canvas.setPointerCapture(event.pointerId)
          canvas.style.setProperty('--split', '72%')
        })
        """
        r = audit_premium_experience({"index.html":BAD_COMPARE},js_text=js)
        self.assertFalse(r["blocking"], r)
        self.assertEqual(r["status"],"PENDING_INDEPENDENT_VISUAL_REVIEW")
        self.assertIn(
            "before_after_visual_alignment_unproven",
            {x["kind"] for x in r["review_required"]},
        )

    def test_range_overlay_usable_without_pointer_js(self):
        html=BAD_COMPARE.replace(
            '</div>\n<input aria-label="Compare" type="range" value="50" min="0" max="100">',
            '<input aria-label="Compare" type="range" value="50" min="0" max="100"></div>',
        )
        result=audit_premium_experience({"index.html":html})
        self.assertFalse(result["blocking"],result)

    def test_css_rectangles_not_sold_as_three_dimensional_textile(self):
        r=audit_premium_experience(
            {"palvelut/index.html":BAD_SWATCH},css_text=CSS,
        )
        self.assertIn(
            "flat_css_cards_pretend_to_be_fabric_3d",
            {x["kind"] for x in r["blocking"]},
        )

    def test_actual_material_photo_can_pass_static_preflight(self):
        with_image=BAD_SWATCH.replace(
            '<div class="fabric-rack">',
            '<div class="fabric-rack"><img alt="Actual close-up of fabric" src="fabric.jpg">',
        )
        r=audit_premium_experience(
            {"palvelut/index.html":with_image},css_text=CSS,
        )
        self.assertFalse(r["blocking"],r)
        self.assertTrue(r["review_required"])

    def test_text_heavy_color_bands_never_auto_claim_aesthetic_success(self):
        html="<main>"+''.join(
            f'<section class="band"><span class="eyebrow">Meta</span>'
            f'<h2>Repeat {i}</h2><p>Long text</p></section>'
            for i in range(4)
        )+"</main>"
        r=audit_premium_experience({"index.html":html})
        self.assertEqual(r["status"],"PENDING_INDEPENDENT_VISUAL_REVIEW")
        self.assertIn(
            "repeating_full_width_text_band_rhythm",
            {x["kind"] for x in r["review_required"]},
        )

    def test_purposefully_static_and_image_poor_business_is_not_forced_into_3d(self):
        r=audit_premium_experience({
            "index.html":"<main><h1>Actual verified workshop</h1></main>"
        })
        self.assertFalse(r["blocking"])
        self.assertEqual(r["status"],"PENDING_INDEPENDENT_VISUAL_REVIEW")

import unittest

from utils.brand_consistency import external_font_notes, font_load_issues
from utils.color_system import (COLOR_BRIEF, audit_pairs, brand_palette, contrast, hex_to_rgb,
                                oklch_hex, pair_problems, rgb_to_oklch)


class ColorSystemTests(unittest.TestCase):
    def test_round_trip_keeps_colour(self):
        for colour in ("#2b3cff", "#d8b979", "#1f8a4c", "#0b0b0d"):
            L, C, H = rgb_to_oklch(hex_to_rgb(colour))
            back = hex_to_rgb(oklch_hex(L, C, H))
            for a, b in zip(back, hex_to_rgb(colour)):
                self.assertLessEqual(abs(a - b), 1)

    def test_palette_roles_meet_contrast_and_keep_hue(self):
        for brand in ("#2b3cff", "#e4572e", "#d8b979", "#1f8a4c", "#7a3cff"):
            p = brand_palette(brand)
            self.assertGreaterEqual(contrast(p["field"], p["on_field"]), 7.5)
            self.assertGreaterEqual(contrast(p["accent_on_ink"], p["ink"]), 4.5)
            self.assertGreaterEqual(contrast(p["accent_on_paper"], p["paper"]), 4.5)
            self.assertGreaterEqual(contrast(p["muted_on_ink"], p["ink"]), 4.5)
            self.assertGreaterEqual(contrast(p["muted_on_field"], p["field"]), 4.5)
            h_brand = rgb_to_oklch(hex_to_rgb(brand))[2]
            h_field = rgb_to_oklch(hex_to_rgb(p["field"]))[2]
            self.assertLess(min(abs(h_brand - h_field), 360 - abs(h_brand - h_field)), 6)

    def test_bright_cobalt_with_light_text_is_flagged_and_deep_cobalt_passes(self):
        self.assertTrue(pair_problems("#f2eee6", "#2b3cff"))
        self.assertEqual(pair_problems("#ffffff", "#1c24c4"), [])
        self.assertEqual(pair_problems("#ffffff", brand_palette("#2b3cff")["field"]), [])

    def test_complementary_flicker_and_audit(self):
        self.assertTrue(any("flickers" in p for p in pair_problems("#e5322d", "#1f9a4a", large=True)))
        out = audit_pairs([{"text": "#f2eee6", "bg": "#2b3cff", "large": False, "weight": 500},
                           {"text": "#111111", "bg": "#ffffff", "large": False, "weight": 5000}])
        self.assertEqual(len(out), 1)
        self.assertIn("#2b3cff", out[0])

    def test_brief_and_font_load(self):
        self.assertIn("OKLCH", COLOR_BRIEF)
        self.assertIn("7.5:1", COLOR_BRIEF)
        self.assertEqual(font_load_issues([]), [])
        self.assertIn("Bricolage", font_load_issues(["Bricolage Grotesque"])[0])
        linked = [{"family": "Bricolage Grotesque", "external": True}]
        self.assertEqual(font_load_issues(linked), [])
        self.assertIn("self-host", external_font_notes(linked)[0])


if __name__ == "__main__":
    unittest.main()

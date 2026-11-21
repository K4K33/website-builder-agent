from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]


class RevisionUsesSameDeterministicRepairsTests(unittest.TestCase):
    def test_revision_path_has_brand_repair_phone_pinning_and_palette(self):
        src = (ROOT / "utils/kaurivo_visual_review_recovery.py").read_text(encoding="utf-8")
        self.assertIn("repair_v8_findings(current, research)", src)
        self.assertEqual(src.count("repair_measured_contrast(repair_brand(render_current_concepts()))"), 2)
        self.assertIn("pin_phone_links(body, facts)", src)
        self.assertEqual(src.count('"allowed_colours_and_brief": research.get("pre_build_brief")'), 2)
        self.assertIn("_blocked_diagnostic(authored, research)", src)


if __name__ == "__main__":
    unittest.main()

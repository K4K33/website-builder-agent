"""Keep original brand-experience requirements wired to all website agents."""
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class BrandExperienceV5PolicyTests(unittest.TestCase):
    def test_builder_and_reviser_both_use_original_full_wordmark_policy(self):
        prompt = (ROOT / "agents" / "builder.py").read_text("utf-8")
        self.assertEqual(prompt.count("V5: ALKUPERÄISEN BRÄNDIN TUNTU"), 2)
        self.assertIn("ALKUPERÄINEN KOKO SANATUNNUS", prompt)
        self.assertIn("320/390 px", prompt)
        self.assertIn("kiv", (ROOT / "docs" / "KAURIVO_BRAND_EXPERIENCE_V5_2026-11-03.md").read_text("utf-8"))

    def test_research_and_qa_compare_emotional_brand_not_merely_logo_file(self):
        research = (ROOT / "agents" / "research.py").read_text("utf-8")
        qa = (ROOT / "agents" / "qa.py").read_text("utf-8")
        self.assertIn("V5 BRAND EXPERIENCE BEFORE DESIGN:", research)
        self.assertIn("FULL wordmark appearance", research)
        self.assertIn("V5 SOURCE-TO-NEW BRAND EXPERIENCE RED-TEAM:", qa)
        self.assertIn("pale soft rose", qa)
        self.assertIn("source URL/noindex", qa)

    def test_general_standard_rejects_fake_automatic_aesthetic_certification(self):
        policy = (ROOT / "docs" / "KAURIVO_BRAND_EXPERIENCE_V5_2026-11-03.md").read_text("utf-8")
        check = (ROOT / "docs" / "KAURIVO_GLOBAL_DESIGN_QA_CHECKLIST.md").read_text("utf-8")
        self.assertIn("Brand DNA", policy)
        self.assertIn("first mobile view", policy)
        self.assertIn("not equivalent to 9.5/10", policy)
        self.assertIn("V5: original brand character", check)
        self.assertIn("source emblem", check)


if __name__ == "__main__":
    unittest.main()

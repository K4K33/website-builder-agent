"""The distilled craft floor reaches every build; the full skills are installed for Claude (offline)."""
from pathlib import Path
import unittest

from utils.craft_brief import CRAFT_BRIEF

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT.parents[1] / ".claude" / "skills"


class CraftBriefTests(unittest.TestCase):
    def test_brief_carries_the_key_rules(self):
        for rule in ("cubic-bezier(.23,1,.32,1)", "never ease-in", "scale(.97) on :active", "(hover:hover) and (pointer:fine)",
                     "eyebrow/kicker label above headings (always refuse)", "PERSUADE"):
            self.assertIn(rule, CRAFT_BRIEF)
        self.assertIn("CRAFT_BRIEF", (ROOT / "agents/builder.py").read_text(encoding="utf-8"))

    def test_skills_are_installed_with_their_licences(self):
        if not SKILLS.exists():
            self.skipTest("repository skills not present in this checkout")
        self.assertTrue((SKILLS / "impeccable" / "SKILL.md").is_file())
        self.assertIn("Apache", (SKILLS / "impeccable" / "LICENSE").read_text(encoding="utf-8"))
        self.assertTrue((SKILLS / "emil-design-eng" / "SKILL.md").is_file())
        self.assertIn("MIT", (SKILLS / "emil-design-eng" / "LICENSE").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

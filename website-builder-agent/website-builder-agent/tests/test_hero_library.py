"""Hero library and flow rules reach the builder and QA (offline)."""
from pathlib import Path
import unittest

from utils.hero_library import FLOW_RULES, HERO_LIBRARY

ROOT = Path(__file__).resolve().parents[1]


class HeroLibraryTests(unittest.TestCase):
    def test_library_covers_the_studied_patterns(self):
        for name in ("CINEMATIC PHOTO", "GIANT WORDMARK", "BRAND MARK ASSEMBLY", "BEFORE / AFTER WIPE",
                     "TRANSITION AS SCROLL", "SPATIAL GALLERY", "SLATTED REVEAL", "VIDEO + INDEX", "TOUCHABLE SURFACE"):
            self.assertIn(name, HERO_LIBRARY)
        self.assertIn("never inside a card", HERO_LIBRARY)
        self.assertIn("Max one card grid per page", FLOW_RULES)

    def test_builder_and_qa_use_it(self):
        builder = (ROOT / "agents/builder.py").read_text(encoding="utf-8")
        self.assertIn("HERO_LIBRARY, FLOW_RULES", builder)
        self.assertIn("mostly stacked boxes", (ROOT / "agents/qa.py").read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()

"""The owner's examples are standing training material for every build (offline)."""
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from utils import reference_library as lib

ROOT = Path(__file__).resolve().parents[1]


class ReferenceLibraryTests(unittest.TestCase):
    def test_owner_rules_and_curation_reference_reach_the_brief(self):
        text = lib.brief("luova studio, agency")
        self.assertIn("never show the same logo twice".lower(), text.lower())
        self.assertIn("stacked boxes", text)
        self.assertIn("horizontal track [curation-by]", text)
        self.assertIn("utils.reference_library import brief", (ROOT / "agents/builder.py").read_text(encoding="utf-8"))

    def test_needs_decide_how_much_spectacle(self):
        self.assertEqual(lib.intensity("tilitoimisto Jyväskylä"), 1)
        self.assertEqual(lib.intensity("kylpyhuoneremontit"), 2)
        self.assertEqual(lib.intensity("ravintola", own_media=8), 3)
        self.assertEqual(lib.intensity("ravintola", own_media=0), 2)   # no real material, no spectacle
        self.assertEqual(lib.intensity("ravintola", own_media=8, wants="rauhallinen ja asiallinen"), 1)
        self.assertIn("level 1 CALM", lib.brief("tilitoimisto"))
        self.assertIn("Do not add spectacle", lib.brief("kaurivo studio"))

    def test_trade_specific_techniques_come_first(self):
        first = lib.select("kylpyhuone remontti", limit=4)
        self.assertTrue(all(t["reference"] == "steal-these-interactions-reel" for t in first))

    def test_new_reference_is_validated_and_kept(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "refs.json"
            shutil.copyfile(lib.PATH, path)
            entry = {"id": "x", "source": "owner", "fits": ["any"],
                     "techniques": [{"name": "n", "observed": "o", "recipe": "r", "needs": "m"}]}
            lib.add_reference(entry, path=path)
            self.assertEqual(json.loads(path.read_text())["references"][-1]["id"], "x")
            with self.assertRaises(ValueError):
                lib.add_reference(entry, path=path)
            with self.assertRaises(ValueError):
                lib.add_reference({"id": "y", "source": "s", "fits": [], "techniques": [{"name": "n"}]}, path=path)

    def test_motion_runtime_has_the_horizontal_track(self):
        from utils.motion_system import SCRIPT, STYLE, MOTION_SYSTEM_BRIEF
        self.assertIn("data-hscroll-track", STYLE)
        self.assertIn("data-hscroll", SCRIPT)
        self.assertIn("horizontal track", MOTION_SYSTEM_BRIEF)


if __name__ == "__main__":
    unittest.main()

import unittest

from utils.illustrated_sequence import TEMPLATES
from utils.trade_specs import SPECS, finished_text, review_checklist


class TradeSpecsTests(unittest.TestCase):
    def test_bathroom_finished_result_is_complete(self):
        text = finished_text("kylpyhuone")
        for item in ("washbasin", "mirror", "toilet", "glass wall", "floor drain", "towel rail", "lighting"):
            self.assertIn(item, text)

    def test_review_demands_checklist_and_visible_work_per_stage(self):
        lines = review_checklist("kylpyhuone", ["Lähtötilanne", "Pohja", "Vedeneristys", "Laatoitus", "Valmis"])
        self.assertIn("ALL of", lines)
        self.assertIn("not only a new colour", lines)
        self.assertIn("- Pohja:", lines)
        self.assertEqual(review_checklist("tuntematon", ["A"]), "")

    def test_every_stage_with_a_spec_adds_physical_work(self):
        bathroom = next(t for t in TEMPLATES if "kylpyhuone" in t[0])
        for label, surfaces, _fixtures in bathroom[3]:
            self.assertIn(label, SPECS["kylpyhuone"]["stage_work"])
        self.assertIn("pipe", bathroom[3][1][1])  # the stripped shell shows new pipes, not just concrete


if __name__ == "__main__":
    unittest.main()

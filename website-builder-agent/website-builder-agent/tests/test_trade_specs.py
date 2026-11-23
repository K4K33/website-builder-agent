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


class HouseBuildTests(unittest.TestCase):
    def test_house_follows_the_reference_build(self):
        from utils.illustrated_sequence import BASE_STAGE, LAST_VIEW, template_for
        seed, scene, stages, note = template_for("Omakotitalojen rakentaminen")
        self.assertIn("drone", scene)
        self.assertEqual([s[0] for s in stages], ["Perustus", "Runko", "Vesikatto", "Julkisivu", "Valmis"])
        self.assertEqual(BASE_STAGE["talo"], 0)          # built up from the foundation
        self.assertIn("front door", LAST_VIEW["talo"])   # ends at the door like the reference
        self.assertEqual(SPECS["talo"]["same_camera_until"], 4)
        self.assertIn("gutters", finished_text("talo"))

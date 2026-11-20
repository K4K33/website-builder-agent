"""Brand plan gate gets a bounded repair instead of losing the whole research."""
import unittest

from utils.source_identity import repair_brand_preservation_plan


def research(plan):
    return {
        "source_inventory": {"pages": [{
            "url": "https://ostroferia.example/",
            "source_identity": {"theme_color": "#1d3557",
                                "original_logo_candidates": ["https://ostroferia.example/logo.png"],
                                "original_content_photos": ["a.jpg", "b.jpg"]},
        }]},
        "brand_preservation_plan": plan,
    }


GOOD = "Keep the original navy logo file unchanged in the header and footer."


class BrandPlanRepairTests(unittest.TestCase):
    def test_short_fields_are_repaired_and_sources_bound(self):
        calls = []
        def repair(system, user, **kw):
            calls.append(system)
            return {"color_treatment": "Use the observed navy #1d3557 as the main brand color with warm neutrals.",
                    "photography_treatment": "Lead with the company's own interior photos; no stock people."}
        data = research({"logo_treatment": GOOD, "typography_treatment": GOOD,
                         "color_treatment": "navy", "photography_treatment": ""})
        result = repair_brand_preservation_plan(data, repair)
        self.assertTrue(result["required"])
        self.assertEqual(len(calls), 1)
        self.assertIn("color_treatment, photography_treatment", calls[0])
        plan = data["brand_preservation_plan"]
        self.assertEqual(plan["original_theme_colors"], ["#1d3557"])
        self.assertEqual(plan["original_logo_candidates"], ["https://ostroferia.example/logo.png"])

    def test_missing_plan_is_created(self):
        def repair(system, user, **kw):
            return {key: GOOD for key in ("logo_treatment", "color_treatment",
                                          "typography_treatment", "photography_treatment")}
        data = research(None)
        self.assertTrue(repair_brand_preservation_plan(data, repair)["required"])

    def test_valid_plan_makes_no_model_call(self):
        data = research({k: GOOD for k in ("logo_treatment", "color_treatment",
                                            "typography_treatment", "photography_treatment")})
        from utils.source_identity import bind_brand_plan_sources
        bind_brand_plan_sources(data)
        def repair(*a, **k):
            raise AssertionError("no repair expected")
        self.assertTrue(repair_brand_preservation_plan(data, repair)["required"])

    def test_useless_repairs_stop_after_bound(self):
        calls = []
        def repair(*a, **k):
            calls.append(1)
            return {"color_treatment": "short"}
        data = research({"logo_treatment": GOOD, "typography_treatment": GOOD,
                         "photography_treatment": GOOD, "color_treatment": ""})
        with self.assertRaises(RuntimeError) as caught:
            repair_brand_preservation_plan(data, repair)
        self.assertEqual(len(calls), 2)
        self.assertIn("repair did not pass", str(caught.exception))


if __name__ == "__main__":
    unittest.main()

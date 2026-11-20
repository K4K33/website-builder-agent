import unittest

from utils.site_architecture import ensure_site_architecture, validate_site_architecture


def research(plan=None, pages=3, words=300):
    data = {"source_inventory": {"pages": [{"url": f"https://e.fi/{i}", "text": "sana " * words}
                                           for i in range(pages)]}}
    if plan is not None:
        data["site_architecture"] = plan
    return data


class SiteArchitectureRepairTests(unittest.TestCase):
    def test_missing_plan_is_built_from_source(self):
        data = research()
        self.assertTrue(ensure_site_architecture(data))
        result = validate_site_architecture(data)
        routes = [p["path"] for p in data["site_architecture"]["pages"]]
        self.assertEqual(routes[0], "index.html")
        self.assertGreaterEqual(len(routes), 2)  # content-rich source needs real routes
        self.assertTrue(result)

    def test_small_source_gets_one_page(self):
        data = research(pages=1, words=100)
        ensure_site_architecture(data)
        validate_site_architecture(data)
        self.assertEqual([p["path"] for p in data["site_architecture"]["pages"]], ["index.html"])

    def test_list_shape_and_bad_sections_are_normalised(self):
        plan = [{"path": "index.html", "purpose": "Etusivu", "user_task": "x",
                 "section_ids": ["Hero osio", "2 palvelut"]},
                {"path": "palvelut/index.html", "purpose": "Palvelut esitellään tässä",
                 "user_task": "Asiakas valitsee palvelun", "section_ids": ["palvelut"]},
                {"path": "../evil.html"}]
        data = research(plan)
        self.assertTrue(ensure_site_architecture(data))
        validate_site_architecture(data)
        index = data["site_architecture"]["pages"][0]
        self.assertEqual(index["section_ids"], ["hero-osio", "section-2-palvelut"])
        self.assertEqual(len(data["site_architecture"]["pages"]), 2)

    def test_valid_plan_is_untouched(self):
        plan = {"pages": [{"path": "index.html", "purpose": "Etusivu esittelee palvelut",
                           "user_task": "Asiakas löytää palvelut", "section_ids": ["hero"]},
                          {"path": "yhteys.html", "purpose": "Yhteystiedot ja sijainti",
                           "user_task": "Asiakas ottaa yhteyttä", "section_ids": ["yhteys"]}]}
        data = research(plan)
        self.assertFalse(ensure_site_architecture(data))
        self.assertEqual(data["site_architecture"], plan)


if __name__ == "__main__":
    unittest.main()

"""Common SME trades have a free reference route (20.11.2026 queue audit)."""
import unittest

from agents.scout import _build_overpass_query
from utils.free_references import (
    OSM_CATEGORIES, normalize_industry, trade_from_source_text,
    verified_sector_search_hint, discover_free_references,
)

NEW = ("maalausliike", "keittiöliike", "kattoliike", "laatoitus",
       "rakennusliike", "sisustusliike", "lvi", "kirvesmies")


class TradeReferenceTests(unittest.TestCase):
    def test_every_new_trade_has_osm_tags(self):
        for category in NEW:
            with self.subTest(category=category):
                self.assertIn(category, OSM_CATEGORIES)
                self.assertIn('nwr["', _build_overpass_query(category, "Helsinki"))

    def test_registry_labels_map(self):
        self.assertEqual(normalize_industry("Keittiökalusteiden vähittäiskauppa"), "keittiöliike")
        self.assertEqual(normalize_industry("Maalaustyöt"), "maalausliike")
        self.assertEqual(normalize_industry("Kattoremontti"), "kattoliike")

    def test_source_text_needs_two_distinct_signals(self):
        self.assertEqual(trade_from_source_text(
            "Teemme ulkomaalaukset ja sisämaalaukset sekä tapetoinnit."), "maalausliike")
        self.assertEqual(trade_from_source_text("Maalaamme."), "")
        self.assertEqual(verified_sector_search_hint(
            "Muu vähittäiskauppa",
            "Suunnittelemme keittiökalusteet mittatilauksena: työtaso, välitila ja kaapit."),
            "keittiöliike")

    def test_existing_specific_rules_still_win(self):
        text = ("Parketin hionta ja lakkaus. Hiomme vanhat lattiat. "
                "Saneeraus ja peruskorjaus kohteissa.")
        self.assertEqual(verified_sector_search_hint("Rakennusten viimeistely", text), "parkettityöt")

    def test_discovery_queries_osm_for_new_trade(self):
        import tempfile, os
        calls = []
        def fetch(category, region):
            calls.append((category, region))
            return [{"name": f"Maalari {i}", "website": f"https://maalari{i}.example.fi/"} for i in range(4)]
        with tempfile.TemporaryDirectory() as tmp:
            rows = discover_free_references(
                "maalausliike", target_url="https://www.maalausvalo.fi",
                cache_path=os.path.join(tmp, "cache.json"), fetch_osm=fetch,
                historic_lookup=lambda c: [])
        self.assertGreaterEqual(len(rows), 3)
        self.assertEqual(calls[0][0], "maalausliike")


if __name__ == "__main__":
    unittest.main()

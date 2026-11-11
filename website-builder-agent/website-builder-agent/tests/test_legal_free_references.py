"""No-network legal reference discovery regressions."""
from __future__ import annotations
from datetime import datetime,timezone
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from agents.scout import _build_overpass_query
from utils.free_references import normalize_industry,discover_free_references


class LegalReferenceTests(unittest.TestCase):
    def test_finnish_english_legal_firms_map_to_real_osm_tag(self):
        for category in ("Asianajotoimisto","Asianajotoimistot",
                         "asianajopalvelut","lakitoimisto","lakipalvelut",
                         "legal services","law firm"):
            with self.subTest(category=category):
                self.assertEqual(normalize_industry(category),"asianajotoimisto")
        query=_build_overpass_query("asianajotoimisto","Tampere")
        self.assertIn('nwr["office"="lawyer"]',query)
        self.assertIn('area["name"="Tampere"]',query)

    def test_free_legal_competitors_remain_real_and_independently_unverified(self):
        hits=[]
        def fetch_osm(category,region):
            hits.append((category,region))
            return [
                {"name":"Verified-needed law A","website":"https://legal-a.example.org/"},
                {"name":"Verified-needed law B","website":"https://legal-b.example.org/"},
                {"name":"Verified-needed law C","website":"https://legal-c.example.org/"},
                {"name":"Verified-needed law D","website":"https://legal-d.example.org/"},
            ]
        with TemporaryDirectory() as tmp:
            results=discover_free_references(
                "Asianajotoimisto",target_url="https://law-client.example.org/",
                cache_path=Path(tmp)/"references.json",
                regions=("Tampere","Turku"),max_results=10,
                fetch_osm=fetch_osm,historic_lookup=lambda _:[],
                now=datetime(2026,11,11,tzinfo=timezone.utc))
            self.assertEqual(len(results),4)
            self.assertEqual(hits[0],("asianajotoimisto","Tampere"))
            self.assertTrue(all("url" in x for x in results))
            self.assertTrue(all("same_industry" not in x for x in results))


if __name__=="__main__":
    unittest.main()

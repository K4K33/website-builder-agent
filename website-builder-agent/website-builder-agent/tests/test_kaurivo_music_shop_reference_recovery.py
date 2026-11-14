"""Offline generic free music-retailer references; never a specific client exception."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from agents.scout import _build_overpass_query
from utils.free_references import (
    normalize_industry, verified_sector_search_hint, discover_free_references,
    CURATED_REFERENCE_CANDIDATES
)


class MusicShopReferencesTests(unittest.TestCase):
    def test_variants_in_finnish_and_english_map_to_musical_instruments(self):
        for label in (
            "Musiikkiliike", "soitinkauppa", "Soitinliike",
            "Soitin- ja musiikkitarvikekauppa",
            "Musical instrument store",
            "Käytettyjen soitinten vähittäiskauppa",
        ):
            with self.subTest(label=label):
                self.assertEqual(normalize_industry(label), "musiikkiliike")

    def test_only_source_proved_instrument_sales_rescue_generic_retail_industry(self):
        source = ("Kitarat, sähkökitarat, akustiset kitarat, bassot, "
                  "rumpusetit ja symbaalit. Verkkokauppa, myymälä, ostoskori.")
        self.assertEqual(verified_sector_search_hint("Muu vähittäiskauppa",source),
                         "musiikkiliike")
        # Do not substitute instrument stores for recorded music shops,
        # live-music hospitality or pure repair workshops.
        for unrelated in (
            "Lounas ja live musiikki, esiintyjiä ja keikkoja.",
            "Äänilevyjä, CD-levyjä, kasetteja ja vinyylilevyjä.",
            "Kitaran korjaus ja entisöinti, ajanvaraus.",
        ):
            with self.subTest(unrelated=unrelated):
                self.assertNotEqual(verified_sector_search_hint(
                    "Muu vähittäiskauppa", unrelated), "musiikkiliike")

    def test_real_source_citations_remain_only_unapproved_candidates(self):
        entries=CURATED_REFERENCE_CANDIDATES["musiikkiliike"]
        self.assertGreaterEqual(len(entries),5)
        with TemporaryDirectory() as td:
            calls=[]
            def osm(category, region):
                calls.append((category,region))
                return []
            candidates=discover_free_references(
                "musiikkiliike",
                target_url="https://unseen-instrument-shop.invalid/",
                cache_path=Path(td)/"references.json",
                regions=("Helsinki","Turku"),
                max_results=15,
                fetch_osm=osm,
                historic_lookup=lambda _: [],
            )
        self.assertGreaterEqual(len(candidates),5)
        self.assertEqual(len({x["url"] for x in candidates}),len(candidates))
        self.assertTrue(all(x["url"].startswith("https://") for x in candidates))
        self.assertLessEqual(len(calls),2)
        # A URL is NOT independently verified same-industry proof.
        self.assertTrue(all(set(row).issuperset({"title","url"}) for row in candidates))
        self.assertTrue(all("industry_match" not in row for row in candidates))

    def test_osm_uses_instrument_retail_not_recorded_music(self):
        query=_build_overpass_query("musiikkiliike","Helsinki")
        self.assertIn('["shop"="musical_instrument"]',query)
        self.assertNotIn('["shop"="music"]',query)
        with self.assertRaises(ValueError):
            _build_overpass_query("unverified_broad_sector","Helsinki")


if __name__=="__main__":
    unittest.main()

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from urllib.parse import urlsplit

from utils.free_references import discover_free_references, verified_sector_search_hint


class ParquetReferenceTests(unittest.TestCase):
    def test_generic_construction_label_maps_from_original_service_evidence(self):
        category = verified_sector_search_hint(
            "Lattianpäällystys", "Parketin hionnat, lakkaukset, asennukset ja korjaukset."
        )
        self.assertEqual(category, "parkettityöt")
        self.assertEqual(
            verified_sector_search_hint("Retail", "Parketti 32 euroa, lisää koriin"),
            "Retail",
        )
        with TemporaryDirectory() as directory:
            candidates = discover_free_references(
                category, target_url="https://eemelinparketti.fi/",
                cache_path=Path(directory) / "references.json",
                historic_lookup=lambda category: [],
                fetch_osm=lambda *_: self.fail("Curated pool needs no public OSM calls"),
            )
        domains = {urlsplit(row["url"]).hostname for row in candidates}
        self.assertGreaterEqual(len(domains), 4)
        self.assertNotIn("eemelinparketti.fi", domains)

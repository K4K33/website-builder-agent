from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import Mock
from urllib.parse import urlsplit

from utils.free_references import discover_free_references, verified_sector_search_hint


class SocialManagementReferenceRecoveryTests(TestCase):
    def test_observed_offering_recovers_free_operator_candidates(self):
        industry = verified_sector_search_hint(
            "Mainostoimistot", "Sosiaalisen median managerointi. Sisältöstrategia ja postaukset."
        )
        fetch_osm = Mock()
        with TemporaryDirectory() as folder:
            references = discover_free_references(
                industry, cache_path=Path(folder) / "references.json",
                fetch_osm=fetch_osm, historic_lookup=lambda _: [],
            )
        self.assertEqual(industry, "somemanagerointi")
        self.assertEqual(len({urlsplit(row["url"]).hostname for row in references}), 5)
        fetch_osm.assert_not_called()

    def test_generic_agency_and_single_incidental_feature_stay_unclassified(self):
        self.assertEqual(
            verified_sector_search_hint("Mainostoimistot", "Sisällöntuotanto ja verkkosivut"),
            "Mainostoimistot",
        )

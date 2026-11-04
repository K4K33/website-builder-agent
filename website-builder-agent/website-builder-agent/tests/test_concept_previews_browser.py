"""CI only: actual Chromium renders all six concept pages, no API/network calls."""
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from tests.test_concept_previews import fixture
from utils.concept_previews import write_concepts, load_verified_set
from utils.browser_qa import inspect_site


@unittest.skipUnless(os.getenv('REQUIRE_BROWSER_TESTS') == '1', 'Run actual rendering in the CI browser environment')
class ConceptBrowserTests(unittest.TestCase):
    def test_actual_desktop_mobile_captures_exist_for_all_six_pages(self):
        research, data = fixture()
        with TemporaryDirectory() as folder:
            reference = write_concepts(json.dumps(data), research, output_parent=folder,
                producer='synthetic-browser-fixture', renderer=inspect_site)
            path, manifest = load_verified_set(reference, research, allowed_root=folder)
            self.assertEqual(manifest['status'], 'ready_for_comparison')
            self.assertEqual(sum(len(e['views']) for e in manifest['entries']), 12)
            self.assertTrue(all((path.parent/v['path']).stat().st_size > 1000
                for e in manifest['entries'] for v in e['views']))

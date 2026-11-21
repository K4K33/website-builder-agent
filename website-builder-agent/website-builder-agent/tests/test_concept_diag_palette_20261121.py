import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from PIL import Image

import utils.pre_build_brief as pbb
from utils.concept_workflow import _blocked_diagnostic


class SourcePhotoPaletteTests(unittest.TestCase):
    def test_queued_build_without_staged_media_uses_source_photos(self):
        with TemporaryDirectory() as tmp:
            img = Path(tmp) / "x.webp"
            Image.new("RGB", (400, 300), (150, 80, 30)).save(img, "WEBP")
            with patch.object(pbb, "_fetch_source_photos", return_value=[img]) as fetch:
                palette = pbb._photo_palette([], Path(tmp) / "site", ["https://e.fi/a.jpg"])
            fetch.assert_called_once()
            self.assertEqual(palette["from"], "source_photos")
            self.assertIn("accent", palette[palette["suggested"]])
            # The analysed photos are stored outside the published site folder.
            cache = fetch.call_args[0][1]
            self.assertNotIn(str(Path(tmp) / "site"), str(cache))

    def test_fetch_is_off_outside_queued_builds(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("KAURIVO_QUEUED_DEMO_ID", None)
            with TemporaryDirectory() as tmp:
                self.assertEqual(pbb._fetch_source_photos(["https://e.fi/a.jpg"], tmp), [])

    def test_diagnostic_has_only_counters_and_colours(self):
        page = ("<!doctype html><html><head><style>:root{--accent:#22ff55}a{background:#22ff55}"
                "b{background:#22ff55}</style></head><body><main><section><h1>Salainen otsikko</h1>"
                "</section></main></body></html>")
        diag = _blocked_diagnostic({"concepts": {"a": {"pages": {"index.html": page}}}},
                                   {"v8_visual_protocol": "v8"})
        self.assertTrue(diag.startswith("diag=brand_known:0,photo_palette:0"))
        self.assertIn("#22ff55", diag)
        self.assertNotIn("Salainen", diag)


if __name__ == "__main__":
    unittest.main()

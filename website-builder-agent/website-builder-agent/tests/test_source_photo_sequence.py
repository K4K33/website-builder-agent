"""Regression coverage for actual playback and the optional production fallback."""
import os
import unittest
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory

from bs4 import BeautifulSoup
from PIL import Image

from utils.source_photo_sequence import enhance_photo_sequence


PAGE = """<!doctype html><html lang="fi">
<head><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Photo sequence fixture</title>
<style>body{margin:0}header{height:20vh}figure{margin:0}img{width:100%;display:block}
footer{height:50vh}figcaption{padding:8px}</style></head>
<body><header>Work example</header><main>
<div data-kaurivo-photo-sequence>
  <div data-kaurivo-photo-stage>
    <figure><img src="assets/original.jpg" alt="Phase one"><figcaption>Phase one</figcaption></figure>
    <figure><img src="assets/finished.jpg" alt="Phase two"><figcaption>Phase two</figcaption></figure>
  </div>
</div>
</main><footer>Contact</footer></body></html>"""


class PhotoSequenceMarkupTests(unittest.TestCase):
    media = [{"src": "assets/original.jpg", "sha256": "first"},
             {"src": "assets/finished.jpg", "sha256": "second"}]

    def test_nested_routes_resolve_staged_sources_and_reassembly_is_idempotent(self):
        result = enhance_photo_sequence(PAGE.replace('src="assets/', 'src="../assets/'),
                                        route="work/index.html", media=self.media)
        self.assertEqual(result, enhance_photo_sequence(result, route="work/index.html", media=self.media))
        self.assertIn('data-kaurivo-photo-sequence="ready"', result)
        self.assertEqual(len(BeautifulSoup(result, "html.parser").select("[data-kaurivo-photo-runtime]")), 2)

    def test_duplicate_media_and_unstaged_media_keep_static_content(self):
        for media in (self.media[:1], [dict(item, sha256="same") for item in self.media]):
            with self.subTest(media=media):
                result = enhance_photo_sequence(PAGE, route="index.html", media=media)
                soup = BeautifulSoup(result, "html.parser")
                self.assertFalse(soup.select("[data-kaurivo-photo-runtime], [data-photo-active]"))
                self.assertEqual(len(soup.select("main figure > img")), 2)

    def test_unrelated_page_is_returned_without_rewriting(self):
        page = "<!doctype html>\n<html><body>Unrelated page</body></html>"
        self.assertEqual(page, enhance_photo_sequence(page, route="index.html", media=self.media))


class PhotoSequenceBrowserTests(unittest.TestCase):
    def test_two_staged_images_play_forward_and_reverse_on_desktop_and_mobile(self):
        from utils.browser_qa import inspect_site

        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "assets").mkdir()
            media = []
            for filename, color in (("original.jpg", "#a85427"), ("finished.jpg", "#28496f")):
                file = root / "assets" / filename
                Image.new("RGB", (1500, 850), color).save(file)
                media.append({"src": f"assets/{filename}", "sha256": sha256(file.read_bytes()).hexdigest()})
            page = root / "index.html"
            page.write_text(enhance_photo_sequence(PAGE, route="index.html", media=media), encoding="utf-8")
            report = inspect_site(page, allowed_file_root=root)
            if any("Executable doesn't exist" in line for line in report["issues"]):
                if os.getenv("REQUIRE_BROWSER_TESTS") != "1":
                    self.skipTest("Chromium not installed")
            self.assertTrue(report["pass"], report["issues"])
            evidence = report["photo_sequences"]
            self.assertFalse(any(item.get("category") == "source_photo_sequence"
                                 for item in report["visual_review_flags"]))
            self.assertEqual({item["viewport"] for item in evidence}, {"desktop", "mobile"})
            self.assertTrue(all(Path(item["filmstrip"]).is_file() for item in evidence))

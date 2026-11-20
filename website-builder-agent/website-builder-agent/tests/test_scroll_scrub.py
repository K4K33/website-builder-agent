from hashlib import sha256
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from bs4 import BeautifulSoup
from PIL import Image

import utils.scroll_scrub as scrub

ROOT = Path(__file__).resolve().parents[1]

PAGE = """<!doctype html><html lang="fi"><head><title>T</title></head><body><main>
<section data-kaurivo-scrub aria-labelledby="h">
  <img data-kaurivo-scrub-poster src="assets/a.webp" alt="Työmaa">
  <img data-kaurivo-scrub-frame src="assets/b.webp" alt="Nosturi">
  <div data-kaurivo-scrub-copy>
    <h1 id="h">Otsikko</h1>
    <p data-at="0">Eka.</p><p data-at="0.5">Toka.</p>
    <a href="tel:+358401234567">Soita</a>
  </div>
</section></main></body></html>"""

SMALL = {"d": {"width": 64, "height": 40, "count": 6}, "m": {"width": 30, "height": 54, "count": 4}}


class ScrollScrubTests(unittest.TestCase):
    def setUp(self):
        # Frame-mode tests: no model download; depth mode has its own tests.
        patcher = patch.dict("os.environ", {"KAURIVO_DEPTH_DISABLED": "1"})
        patcher.start()
        self.addCleanup(patcher.stop)

    def site(self, tmp):
        root = Path(tmp)
        (root / "assets").mkdir()
        media = []
        for name, colour in (("a.webp", (200, 60, 40)), ("b.webp", (40, 90, 200))):
            Image.new("RGB", (120, 90), colour).save(root / "assets" / name, "WEBP")
            media.append({"src": "assets/" + name,
                          "sha256": sha256((root / "assets" / name).read_bytes()).hexdigest()})
        return root, media

    def enhance(self, html, root, media, route="index.html"):
        with patch.object(scrub, "DESKTOP", SMALL["d"]), patch.object(scrub, "MOBILE", SMALL["m"]):
            return scrub.enhance_scroll_scrub(html, route=route, media=media, site_root=root)

    def test_builds_frames_canvas_runtime_and_keeps_static_content(self):
        with TemporaryDirectory() as tmp:
            root, media = self.site(tmp)
            soup = BeautifulSoup(self.enhance(PAGE, root, media), "html.parser")
            scene = soup.select_one('[data-kaurivo-scrub="ready"]')
            self.assertIsNotNone(scene)
            desktop = json.loads(scene["data-scrub-d"])
            phone = json.loads(scene["data-scrub-m"])
            self.assertEqual((desktop["count"], phone["count"]), (6, 4))
            self.assertEqual(desktop["eager"], 20)
            self.assertEqual(len(list(root.glob(desktop["base"] + "*.webp"))), 6)
            self.assertEqual(len(list(root.glob(phone["base"] + "*.webp"))), 4)
            self.assertIsNotNone(scene.select_one('canvas[data-scrub-canvas][aria-hidden="true"]'))
            # Poster, headline, chapters and action remain real readable HTML.
            self.assertEqual(scene.select_one("[data-kaurivo-scrub-poster]")["fetchpriority"], "high")
            self.assertEqual([p.get_text() for p in scene.select("[data-at]")], ["Eka.", "Toka."])
            self.assertIsNotNone(scene.select_one('a[href^="tel:"]'))
            script = soup.select_one("script[data-kaurivo-scrub-runtime]").string
            self.assertIn("prefers-reduced-motion", script)
            self.assertIn("Math.min(devicePixelRatio || 1, 2)", script)
            self.assertIn("requestIdleCallback", script)

    def test_rejects_unstaged_or_remote_images(self):
        with TemporaryDirectory() as tmp:
            root, media = self.site(tmp)
            for src in ("https://example.org/a.webp", "assets/missing.webp", "/assets/a.webp"):
                html = PAGE.replace('src="assets/a.webp"', f'src="{src}"')
                self.assertNotIn('data-kaurivo-scrub="ready"', self.enhance(html, root, media))

    def test_requires_poster_alt_and_h1(self):
        with TemporaryDirectory() as tmp:
            root, media = self.site(tmp)
            for broken in (PAGE.replace('alt="Työmaa"', 'alt=""'),
                           PAGE.replace('<h1 id="h">Otsikko</h1>', "")):
                self.assertNotIn('data-kaurivo-scrub="ready"', self.enhance(broken, root, media))

    def test_nested_route_uses_relative_frame_path_and_reuses_frames(self):
        with TemporaryDirectory() as tmp:
            root, media = self.site(tmp)
            html = PAGE.replace('src="assets/', 'src="../assets/')
            first = self.enhance(html, root, media, route="palvelut/index.html")
            scene = BeautifulSoup(first, "html.parser").select_one("[data-kaurivo-scrub]")
            self.assertTrue(json.loads(scene["data-scrub-d"])["base"].startswith("../assets/scrub/"))
            with patch.object(scrub, "make_frames", side_effect=AssertionError("regenerated")):
                again = self.enhance(first, root, media, route="palvelut/index.html")
            self.assertEqual(again.count("data-kaurivo-scrub-runtime"), 2)  # one style, one script

    def test_over_budget_falls_back_to_static_hero(self):
        with TemporaryDirectory() as tmp:
            root, media = self.site(tmp)
            with patch.dict(scrub.BUDGET_BYTES, {"d": 10, "m": 10}):
                out = self.enhance(PAGE, root, media)
            self.assertNotIn('data-kaurivo-scrub="ready"', out)
            self.assertIn("Otsikko", out)

    def test_wired_into_builder(self):
        pipeline = (ROOT / "utils/site_build_pipeline.py").read_text(encoding="utf-8")
        self.assertIn("enhance_scroll_scrub(body, route=route", pipeline)
        builder = (ROOT / "agents/builder.py").read_text(encoding="utf-8")
        self.assertIn("PHOTO_SEQUENCE_BRIEF, SCRUB_BRIEF, PRODUCT_BRIEF, AWARD_BRIEF", builder)
        self.assertIn("enhance_product_relief(body, route=route", pipeline)


if __name__ == "__main__":
    unittest.main()

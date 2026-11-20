from hashlib import sha256
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from bs4 import BeautifulSoup
from PIL import Image, ImageDraw

import utils.depth_estimation as depth
import utils.scroll_scrub as scrub
from utils.product_relief import clean_cutout, enhance_product_relief

HERO = """<!doctype html><html lang="fi"><head><title>T</title></head><body><main>
<section data-kaurivo-scrub aria-labelledby="h">
  <img data-kaurivo-scrub-poster src="assets/a.webp" alt="Työmaa">
  <img data-kaurivo-scrub-frame src="assets/b.webp" alt="Nosturi">
  <div data-kaurivo-scrub-copy><h1 id="h">Otsikko</h1><p data-at="0">Eka.</p><p data-at=".5">Toka.</p></div>
</section></main></body></html>"""

PRODUCT = """<!doctype html><html lang="fi"><head><title>T</title></head><body><main>
<figure data-kaurivo-product><img src="assets/a.webp" alt="Suklaalevy"><figcaption>Suklaalevy</figcaption></figure>
</main></body></html>"""


def fake_map(_photo, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    Image.new("L", (40, 30), 128).save(destination, "WEBP", lossless=True)
    return destination


def centred_mask(_photo, destination, size=(100, 80), box=(25, 20, 75, 60)):
    destination.parent.mkdir(parents=True, exist_ok=True)
    image = Image.new("L", size, 0)
    ImageDraw.Draw(image).rectangle(box, fill=255)
    image.save(destination, "WEBP", lossless=True)
    return destination


class DepthSceneTests(unittest.TestCase):
    def site(self, tmp):
        root = Path(tmp)
        (root / "assets").mkdir()
        media = []
        for name in ("a.webp", "b.webp"):
            Image.new("RGB", (100, 80), (180, 90, 40)).save(root / "assets" / name, "WEBP")
            media.append({"src": "assets/" + name,
                          "sha256": sha256((root / "assets" / name).read_bytes()).hexdigest()})
        return root, media

    def test_depth_mode_replaces_frames_and_ships_webgl_runtime(self):
        with TemporaryDirectory() as tmp, patch.dict(os.environ, {"KAURIVO_DEPTH_DISABLED": "0"}), \
                patch.object(depth, "estimate_depth", side_effect=fake_map) as estimate, \
                patch.object(scrub, "make_frames", side_effect=AssertionError("frames not needed")):
            root, media = self.site(tmp)
            out = scrub.enhance_scroll_scrub(HERO, route="index.html", media=media, site_root=root)
            scene = BeautifulSoup(out, "html.parser").select_one("[data-kaurivo-scrub]")
            self.assertEqual(scene["data-kaurivo-scrub"], "ready")
            self.assertEqual(scene["data-scrub-mode"], "depth")
            layers = json.loads(scene["data-depth"])["layers"]
            self.assertEqual([l["img"] for l in layers], ["assets/a.webp", "assets/b.webp"])
            self.assertTrue(all((root / l["depth"]).is_file() for l in layers))
            self.assertIn("getContext('webgl'", out)
            self.assertIn("prefers-reduced-motion: reduce", out)
            self.assertEqual(estimate.call_count, 2)
            # Rebuilds reuse the cached depth maps.
            scrub.enhance_scroll_scrub(out, route="index.html", media=media, site_root=root)
            self.assertEqual(estimate.call_count, 2)

    def test_depth_failure_falls_back_to_frames(self):
        small = {"width": 32, "height": 20, "count": 3}
        with TemporaryDirectory() as tmp, patch.dict(os.environ, {"KAURIVO_DEPTH_DISABLED": "0"}), \
                patch.object(depth, "estimate_depth", return_value=None), \
                patch.object(scrub, "DESKTOP", small), patch.object(scrub, "MOBILE", small):
            root, media = self.site(tmp)
            out = scrub.enhance_scroll_scrub(HERO, route="index.html", media=media, site_root=root)
            scene = BeautifulSoup(out, "html.parser").select_one("[data-kaurivo-scrub]")
            self.assertNotIn("data-scrub-mode", scene.attrs)
            self.assertIn("data-scrub-d", scene.attrs)

    def test_product_relief_accepts_clean_cutout(self):
        with TemporaryDirectory() as tmp, patch.dict(os.environ, {"KAURIVO_DEPTH_DISABLED": "0"}), \
                patch.object(depth, "estimate_mask", side_effect=centred_mask), \
                patch.object(depth, "estimate_depth", side_effect=fake_map):
            root, media = self.site(tmp)
            out = enhance_product_relief(PRODUCT, route="index.html", media=media, site_root=root)
            figure = BeautifulSoup(out, "html.parser").select_one("[data-kaurivo-product]")
            cfg = json.loads(figure["data-product"])
            self.assertTrue((root / cfg["mask"]).is_file() and (root / cfg["depth"]).is_file())
            self.assertIsNotNone(figure.select_one('canvas[data-product-canvas][aria-hidden="true"]'))
            self.assertEqual(figure.img["alt"], "Suklaalevy")

    def test_product_relief_rejects_busy_scene(self):
        full = lambda photo, destination: centred_mask(photo, destination, box=(0, 0, 100, 80))
        with TemporaryDirectory() as tmp, patch.dict(os.environ, {"KAURIVO_DEPTH_DISABLED": "0"}), \
                patch.object(depth, "estimate_mask", side_effect=full), \
                patch.object(depth, "estimate_depth", side_effect=fake_map):
            root, media = self.site(tmp)
            out = enhance_product_relief(PRODUCT, route="index.html", media=media, site_root=root)
            self.assertNotIn("data-product=", out)
            self.assertNotIn("data-kaurivo-product-runtime", out)

    def test_clean_cutout_rules(self):
        with TemporaryDirectory() as tmp:
            path = Path(tmp) / "m.webp"
            centred_mask(None, path)
            self.assertTrue(clean_cutout(path))
            centred_mask(None, path, box=(0, 0, 3, 3))
            self.assertFalse(clean_cutout(path))  # too small to be the product

    def test_model_download_is_verified(self):
        with TemporaryDirectory() as tmp, patch.dict(os.environ, {"KAURIVO_MODEL_CACHE": tmp,
                                                                  "KAURIVO_DEPTH_DISABLED": "0"}):
            bad = lambda url, dest: dest.write_bytes(b"not the model")
            self.assertIsNone(depth.model_path("mask", download=bad))
            self.assertEqual(list(Path(tmp).iterdir()), [])
            with patch.object(depth, "MODELS", {"mask": {**depth.MODELS["mask"],
                                                         "sha256": sha256(b"ok").hexdigest()}}):
                good = lambda url, dest: dest.write_bytes(b"ok")
                path = depth.model_path("mask", download=good)
                self.assertTrue(path.is_file())
                self.assertEqual(depth.model_path("mask", download=bad), path)  # cached

    def test_disabled_never_downloads(self):
        with TemporaryDirectory() as tmp, patch.dict(os.environ, {"KAURIVO_MODEL_CACHE": tmp,
                                                                  "KAURIVO_DEPTH_DISABLED": "1"}):
            self.assertIsNone(depth.model_path("depth", download=lambda *a: self.fail("downloaded")))


if __name__ == "__main__":
    unittest.main()

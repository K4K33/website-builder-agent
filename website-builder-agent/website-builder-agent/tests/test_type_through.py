import hashlib
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from PIL import Image, ImageDraw

from utils import type_through
from utils.type_through import enhance_type_through, solid_mask, subject_mask_ok

PAGE = ('<!DOCTYPE html><html><head></head><body><main>'
        '<section data-kaurivo-typecut aria-labelledby="t"><img src="assets/k.png" alt="Kuppi">'
        '<p data-typecut-word>Kahvila</p><div><h1 id="t">Kahvia</h1></div></section></main></body></html>')


def mask_with(draw):
    image = Image.new("L", (400, 300), 0)
    draw(ImageDraw.Draw(image))
    return image


class TypeThroughTests(unittest.TestCase):
    def test_subject_must_be_separated_from_top_and_sides(self):
        with TemporaryDirectory() as tmp:
            good, wide = Path(tmp) / "g.png", Path(tmp) / "w.png"
            mask_with(lambda d: d.ellipse((120, 80, 280, 299), fill=255)).save(good)  # stands on the bottom edge
            mask_with(lambda d: d.rectangle((0, 50, 399, 250), fill=255)).save(wide)
            self.assertTrue(subject_mask_ok(good))
            self.assertFalse(subject_mask_ok(wide))

    def test_holes_inside_the_subject_are_filled(self):
        ring = mask_with(lambda d: (d.ellipse((100, 60, 300, 260), fill=255), d.ellipse((160, 120, 240, 200), fill=120)))
        solid = solid_mask(ring)
        self.assertEqual(solid.getpixel((200, 160)), 255)
        self.assertEqual(solid.getpixel((10, 10)), 0)

    def test_enhancer_adds_aligned_cutout_word_behind_and_runtime(self):
        with TemporaryDirectory() as tmp, patch.dict(os.environ, {"KAURIVO_DEPTH_DISABLED": ""}):
            root = Path(tmp)
            (root / "assets").mkdir()
            photo = Image.new("RGB", (400, 300), (120, 80, 50))
            ImageDraw.Draw(photo).ellipse((140, 90, 260, 240), fill=(240, 240, 240))
            photo.save(root / "assets/k.png")
            media = [{"src": "assets/k.png", "sha256": hashlib.sha256((root / "assets/k.png").read_bytes()).hexdigest()}]

            def fake_mask(source, destination):
                destination.parent.mkdir(parents=True, exist_ok=True)
                mask_with(lambda d: d.ellipse((140, 90, 260, 240), fill=255)).save(destination, "WEBP")
                return destination
            with patch("utils.depth_estimation.estimate_mask", side_effect=fake_mask), \
                    patch("utils.depth_estimation.disabled", return_value=False):
                html = enhance_type_through(PAGE, route="index.html", media=media, site_root=root)
            self.assertIn("data-typecut-active", html)
            self.assertRegex(html, r'<p aria-hidden="true" data-typecut-word="">Kahvila</p><img[^>]*data-typecut-front')
            self.assertIn("--typecut-top:", html)
            self.assertEqual(html.count("data-kaurivo-typecut-runtime"), 2)
            front = next((root / "assets/typecut").rglob("front.webp"))
            self.assertEqual(Image.open(front).size, (400, 300))

    def test_without_a_clean_subject_the_page_is_unchanged(self):
        with TemporaryDirectory() as tmp:
            html = enhance_type_through(PAGE, route="index.html", media=[], site_root=Path(tmp))
            self.assertNotIn("data-typecut-active", html)
            self.assertNotIn("data-typecut-front", html)


if __name__ == "__main__":
    unittest.main()

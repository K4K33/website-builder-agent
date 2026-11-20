import json
import os
from hashlib import sha256
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from PIL import Image, ImageDraw

from utils.award_playbook import AWARD_BRIEF, contrast, derive_photo_palette
import utils.depth_estimation as depth
import utils.scroll_scrub as scrub

ROOT = Path(__file__).resolve().parents[1]


def hexrgb(value):
    return tuple(int(value[i:i + 2], 16) for i in (1, 3, 5))


def photo(path, sky, subject, accent):
    image = Image.new("RGB", (300, 200), sky)
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 70, 300, 200), fill=subject)
    draw.rectangle((120, 110, 180, 170), fill=accent)
    image.save(path, "WEBP")
    return path


class AwardPlaybookTests(unittest.TestCase):
    def test_palette_roles_pass_contrast_in_both_modes(self):
        with TemporaryDirectory() as tmp:
            path = photo(Path(tmp) / "a.webp", (110, 160, 220), (40, 28, 20), (200, 120, 40))
            for mode in ("light", "dark"):
                with self.subTest(mode=mode):
                    roles = derive_photo_palette([path], mode=mode)
                    self.assertIsNotNone(roles)
                    canvas, ink, accent = (hexrgb(roles[k]) for k in ("canvas", "ink", "accent"))
                    self.assertGreaterEqual(contrast(ink, canvas), 7)
                    self.assertGreaterEqual(contrast(hexrgb(roles["accent_ink"]), accent), 4.5)
                    self.assertNotIn(roles["ink"], ("#000000", "#ffffff"))

    def test_subject_not_sky_decides_the_palette(self):
        with TemporaryDirectory() as tmp:
            path = photo(Path(tmp) / "a.webp", (90, 140, 230), (150, 60, 20), (150, 60, 20))
            roles = derive_photo_palette([path], mode="light")
            accent_hue = hexrgb(roles["accent"])
            self.assertGreater(accent_hue[0], accent_hue[2])  # warm subject, not blue sky

    def test_mask_weights_pick_the_product(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            image = Image.new("RGB", (200, 200), (10, 70, 90))       # teal backdrop
            ImageDraw.Draw(image).rectangle((60, 60, 140, 140), fill=(190, 90, 15))
            image.save(root / "p.webp", "WEBP")
            mask = Image.new("L", (200, 200), 0)
            ImageDraw.Draw(mask).rectangle((60, 60, 140, 140), fill=255)
            mask.save(root / "m.webp", "WEBP", lossless=True)
            roles = derive_photo_palette([root / "p.webp"], mode="dark", weights=[root / "m.webp"])
            r, g, b = hexrgb(roles["accent"])
            self.assertGreater(r, b)

    def test_unusable_input_returns_none(self):
        self.assertIsNone(derive_photo_palette([Path("/nonexistent.webp")]))

    def test_brief_and_palette_reach_the_builder(self):
        self.assertIn("one big claim", AWARD_BRIEF)
        builder = (ROOT / "agents/builder.py").read_text(encoding="utf-8")
        concept = (ROOT / "utils/concept_workflow.py").read_text(encoding="utf-8")
        self.assertIn("AWARD_BRIEF))", builder)
        self.assertIn("VISUAL_PLAYBOOK + \"\\n\\n\" + AWARD_BRIEF", concept)
        from utils.pre_build_brief import derive_pre_build_brief
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "assets").mkdir()
            photo(root / "assets" / "a.webp", (110, 160, 220), (40, 28, 20), (200, 120, 40))
            brief = derive_pre_build_brief({}, staged_media=[{"src": "assets/a.webp"}], media_root=root)
            palette = brief["q3_brand_feel"]["photo_palette"]
            self.assertIn(palette["suggested"], ("light", "dark"))
            self.assertIn("canvas", palette[palette["suggested"]])

    def test_blueprint_style_adds_line_drawing_to_first_layer(self):
        page = """<!doctype html><html><head><title>T</title></head><body><main>
<section data-kaurivo-scrub data-scrub-style="blueprint"><img data-kaurivo-scrub-poster src="assets/a.webp" alt="Talo">
<div data-kaurivo-scrub-copy><h1>Otsikko</h1></div></section></main></body></html>"""

        def fake_depth(_photo, destination):
            destination.parent.mkdir(parents=True, exist_ok=True)
            Image.new("L", (30, 20), 120).save(destination, "WEBP", lossless=True)
            return destination

        with TemporaryDirectory() as tmp, patch.dict(os.environ, {"KAURIVO_DEPTH_DISABLED": "0"}), \
                patch.object(depth, "estimate_depth", side_effect=fake_depth):
            root = Path(tmp)
            (root / "assets").mkdir()
            photo(root / "assets" / "a.webp", (110, 160, 220), (40, 28, 20), (200, 120, 40))
            media = [{"src": "assets/a.webp",
                      "sha256": sha256((root / "assets/a.webp").read_bytes()).hexdigest()}]
            out = scrub.enhance_scroll_scrub(page, route="index.html", media=media, site_root=root)
            cfg = json.loads(out.split("data-depth='")[1].split("'")[0]) if "data-depth='" in out else None
            if cfg is None:
                from bs4 import BeautifulSoup
                cfg = json.loads(BeautifulSoup(out, "html.parser").select_one("[data-depth]")["data-depth"])
            self.assertTrue((root / cfg["layers"][0]["lines"]).is_file())
            self.assertIn("uniform float mixv,dolly0,dolly1,bp,reveal,draw", out)


if __name__ == "__main__":
    unittest.main()

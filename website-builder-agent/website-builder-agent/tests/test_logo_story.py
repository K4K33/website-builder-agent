"""Logo story hero: any logo is cut into its own pieces and assembled on scroll (offline)."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from PIL import Image, ImageDraw

from utils.logo_story import cut_logo, logo_story_html

ROOT = Path(__file__).resolve().parents[1]


def _wordmark(path: Path) -> Path:
    image = Image.new("RGB", (620, 160), "white")
    draw = ImageDraw.Draw(image)
    draw.rectangle((14, 30, 114, 130), fill=(196, 40, 40))
    for i in range(5):  # five separate "letters"
        draw.rectangle((150 + i * 90, 40, 210 + i * 90, 130), fill=(30, 40, 60))
    image.save(path)
    return path


class LogoStoryTests(unittest.TestCase):
    def test_wordmark_is_cut_into_pieces_on_a_transparent_background(self):
        with TemporaryDirectory() as tmp:
            cut = cut_logo(_wordmark(Path(tmp) / "logo.png"), Path(tmp) / "cut.png")
            self.assertEqual(len(cut["pieces"]), 6)
            self.assertLess(cut["luminance"], 0.45)
            with Image.open(Path(tmp) / "cut.png") as png:
                self.assertEqual(png.mode, "RGBA")
                self.assertEqual(png.getpixel((1, 1))[3], 0)  # white background removed

    def test_single_shape_still_assembles_in_three_bands(self):
        with TemporaryDirectory() as tmp:
            image = Image.new("RGBA", (400, 200), (0, 0, 0, 0))
            ImageDraw.Draw(image).ellipse((40, 20, 360, 180), fill=(20, 90, 160, 255))
            image.save(Path(tmp) / "mark.png")
            cut = cut_logo(Path(tmp) / "mark.png", Path(tmp) / "cut.png")
            self.assertEqual(len(cut["pieces"]), 3)

    def test_kaurivo_mark_splits_into_its_three_shards(self):
        with TemporaryDirectory() as tmp:
            cut = cut_logo(ROOT / "docs/kaurivo/assets/kaurivo-mark.webp", Path(tmp) / "cut.png")
            self.assertEqual(len(cut["pieces"]), 3)

    def test_html_is_a_scroll_story_with_real_logo_pixels(self):
        with TemporaryDirectory() as tmp:
            cut = cut_logo(_wordmark(Path(tmp) / "logo.png"), Path(tmp) / "cut.png")
        section = logo_story_html(logo_rel="assets/logo-story.png", cut=cut, label="Testi logo",
                                  copy_html='<h1 id="otsikko">Otsikko</h1>')
        self.assertIn("data-story", section)
        self.assertIn("data-copy-after", section)
        self.assertIn("data-hero-copy", section)
        self.assertEqual(section.count('class="ls-piece"'), 6)
        self.assertEqual(section.count('src="assets/cut-'), 6)

    def test_sales_demo_uses_logo_story_when_only_stock_photos_exist(self):
        from utils.sales_demo import render_sales_demo
        plan = {"trade": "rakennus", "hero_style": "depth", "headline": "Putkityöt avaimet käteen",
                "chapters": ["Vesijohdot."], "statement": "Testi.",
                "services": [{"name": "Putkityöt", "text": "Putkityöt."}],
                "photo_captions": ["Kuva"], "contact_lead": ""}
        with TemporaryDirectory() as tmp, patch.dict(os.environ, {"KAURIVO_DEPTH_DISABLED": "1"}):
            photos = []
            for i in range(2):
                p = Path(tmp) / f"s{i}.jpg"
                Image.new("RGB", (400, 260), (120 + i * 40, 110, 100)).save(p)
                photos.append(p)
            credit = {"photographer": "Anna K", "source_url": "https://www.pexels.com/photo/1/", "licence": "Pexels License"}
            page = render_sales_demo(company={"name": "Testi Oy", "phone": "040 1234567"}, plan=plan,
                                     photos=photos, credits=[credit, credit], logo=_wordmark(Path(tmp) / "logo.png"),
                                     out_dir=Path(tmp) / "out")
            text = page.read_text(encoding="utf-8")
            self.assertIn('class="ls-hero', text)
            self.assertIn("data-kaurivo-story-runtime", text)
            self.assertTrue((page.parent / "assets/logo-story.png").is_file())
            self.assertNotIn("<img data-kaurivo-scrub-poster", text)
            self.assertIn("Havainnekuva", text)  # the stock photo behind the logo stays labelled
            try:
                from playwright.sync_api import sync_playwright
            except ImportError:
                return
            from utils.scroll_story import audit_scroll_story
            with sync_playwright() as p:
                browser = p.chromium.launch()
                try:
                    for size in ((1440, 900), (390, 844)):
                        view = browser.new_page(viewport={"width": size[0], "height": size[1]})
                        view.goto(page.as_uri())
                        issues = audit_scroll_story(view, output_dir=Path(tmp) / "a", viewport=str(size[0]))["issues"]
                        self.assertEqual(issues, [], size)
                finally:
                    browser.close()


if __name__ == "__main__":
    unittest.main()

import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from PIL import Image, ImageDraw

from utils.sales_demo import TYPE_PAIRS, render_sales_demo, validate_plan

PLAN = {"trade": "rakennus", "hero_style": "depth", "headline": "Puurakentamista avaimet käteen",
        "chapters": ["Rakennamme puusta.", "Elementit tehtaalla.", "Runko työmaalla."],
        "statement": "Testi Oy rakentaa taloja puusta.",
        "services": [{"name": "Rivitalot", "text": "Rivitalot avaimet käteen."},
                     {"name": "<script>x</script>", "text": "Erikoismerkit & testi"}],
        "photo_captions": ["Työmaa", "Elementit"], "contact_lead": "Ota yhteyttä."}
COMPANY = {"name": "Testi & Rakennus Oy", "phone": "040 123 4567", "email": "info@testi.fi",
           "address": "Katu 1, 00100 Helsinki", "business_id": "1234567-8"}


def photos(root):
    paths = []
    for i, colour in enumerate(((40, 30, 25), (150, 110, 60), (90, 120, 160))):
        image = Image.new("RGB", (400, 300), (110, 160, 220))
        ImageDraw.Draw(image).rectangle((0, 100, 400, 300), fill=colour)
        path = Path(root) / f"p{i}.webp"
        image.save(path, "WEBP")
        paths.append(path)
    return paths


class SalesDemoTests(unittest.TestCase):
    def render(self, tmp, **changes):
        with patch.dict(os.environ, {"KAURIVO_DEPTH_DISABLED": "1"}):
            return render_sales_demo(company=COMPANY, plan={**PLAN, **changes},
                                     photos=photos(tmp), out_dir=Path(tmp) / "out")

    def test_renders_one_safe_page_with_own_media_and_fonts(self):
        with TemporaryDirectory() as tmp:
            page = self.render(tmp).read_text(encoding="utf-8")
            self.assertRegex(page, r'<meta content="noindex,nofollow" name="robots"')
            self.assertIn("Kaurivon luonnos yritykselle Testi &amp; Rakennus Oy", page)
            self.assertIn('href="tel:+358401234567"', page)
            self.assertIn('href="mailto:info@testi.fi"', page)
            self.assertNotIn("<script>x</script>", page)
            self.assertIn("&lt;script&gt;x&lt;/script&gt;", page)
            self.assertNotRegex(page, r'src="https?://')
            out = Path(tmp) / "out"
            self.assertTrue((out / "assets/fonts/archivo.woff").is_file())
            self.assertTrue((out / "assets/kuva-1-g.webp").is_file())
            self.assertFalse((out / "assets/kuva-1.webp").exists())
            self.assertEqual(page.count("<h1"), 1)

    def test_references_become_proof_with_totals_from_listed_figures(self):
        proof = [{"title": "Linjasaneeraukset", "items": ["As Oy Kylätie 8, 15 kph", "Luotsikatu 9",
                                                          "As Oy Otsonmäki 62 kph"]},
                 {"title": "Liiketilat", "items": ["Alepa 350m2", "Koinonia-keskus 450m2", "<b>x</b>"]}]
        with TemporaryDirectory() as tmp:
            page = self.render(tmp, proof=proof).read_text(encoding="utf-8")
            self.assertIn('<span class="ref__name">As Oy Kylätie 8</span><span class="ref__fig">15 kph</span>', page)
            self.assertIn("<span data-to=\"77\">77</span> kylpyhuonetta näissä 2 kohteessa", page)
            self.assertIn("<span data-to=\"800\">800</span> m² laatoitusta näissä 2 kohteessa", page)
            self.assertIn("Luotsikatu 9", page)
            self.assertNotIn("<b>x</b>", page)

    def test_photos_share_one_grade_without_clipped_white(self):
        import numpy as np
        from utils.photo_grade import grade_array
        white = np.ones((8, 8, 3), dtype=np.float32)
        out = grade_array(white, shadow="#10203a", highlight="#f4efe6")
        self.assertLess(out.max(), .97)
        black = np.zeros((8, 8, 3), dtype=np.float32)
        self.assertGreater(grade_array(black, shadow="#10203a", highlight="#fff").mean(), .01)

    def test_bathroom_build_scene_hero_without_photos(self):
        from utils.sales_demo import build_scene_for
        self.assertEqual(build_scene_for("Kylpyhuoneremontit ja laatoitus"), "bathroom")
        self.assertIsNone(build_scene_for("Kampaamo"))
        with TemporaryDirectory() as tmp:
            page = render_sales_demo(company=COMPANY, plan=PLAN, photos=[], out_dir=Path(tmp) / "out",
                                     build_scene="bathroom").read_text(encoding="utf-8")
            out = Path(tmp) / "out/assets/build3d"
            self.assertTrue((out / "bathroom.min.js").is_file() and (out / "LICENSE-three.txt").is_file())
            self.assertIn('data-build3d="bathroom"', page)
            self.assertIn("Vedeneristys", page)
            self.assertIn("3D-havainnollistus kylpyhuoneremontin työvaiheista, ei yrityksen kohde", page)
            self.assertIn("import('./assets/build3d/'", page)
            self.assertNotRegex(page, r"<section[^>]*data-kaurivo-scrub")
            self.assertEqual(page.count("<h1"), 1)

    def test_each_trade_has_licensed_fonts(self):
        root = Path(__file__).resolve().parents[1] / "assets/sales_demo/fonts"
        for display, _, body, _, _ in TYPE_PAIRS.values():
            self.assertTrue((root / display).is_file() and (root / body).is_file())
        self.assertTrue(list(root.glob("OFL-*.txt")))

    def test_plan_is_bounded_and_requires_real_material(self):
        with self.assertRaises(ValueError):
            validate_plan({**PLAN, "services": []}, [Path("x.webp")])
        with self.assertRaises(ValueError):
            validate_plan(PLAN, [])
        plan = validate_plan({**PLAN, "trade": "unknown", "hero_style": "x"}, [Path("x.webp")])
        self.assertEqual((plan["trade"], plan["hero_style"]), ("moderni", "depth"))


if __name__ == "__main__":
    unittest.main()

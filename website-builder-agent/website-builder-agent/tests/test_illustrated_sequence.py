import base64
from io import BytesIO
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from PIL import Image

from utils.illustrated_sequence import generate_sequence, template_for
from utils.sales_demo import render_sales_demo

ENV = {"FREE_ONLY": "1", "KAURIVO_CLOUDFLARE_WORKERS_FREE_CONFIRMED": "1",
       "CLOUDFLARE_ACCOUNT_ID": "a" * 32, "CLOUDFLARE_API_TOKEN": "t" * 40}


def image_b64(colour, size=(1536, 864)):
    buffer = BytesIO()
    Image.new("RGB", size, colour).save(buffer, "JPEG")
    return base64.b64encode(buffer.getvalue()).decode()


class Reply:
    def __init__(self, status, body):
        self.status_code, self._body = status, body

    def json(self):
        return self._body


class IllustratedSequenceTests(unittest.TestCase):
    def test_trade_templates(self):
        self.assertEqual(template_for("Kylpyhuoneremontit ja vesieristykset")[2][1][0], "Vedeneristys")
        self.assertEqual(template_for("Maalaus ja tasoitustyöt")[2][0][0], "Pohjatyöt")
        self.assertIsNone(template_for("Kampaamo"))

    def test_four_stages_one_seed_and_disabled_without_opt_in(self):
        calls = []

        def post(url, **kwargs):
            calls.append(kwargs["json"])
            return Reply(200, {"result": {"image": image_b64((40 * len(calls), 90, 120))}})
        with TemporaryDirectory() as tmp, patch.dict(os.environ, ENV):
            got = generate_sequence("kylpyhuoneremontti", Path(tmp), post=post)
            self.assertEqual(got["labels"], ["Pohja", "Vedeneristys", "Laatoitus", "Valmis"])
            self.assertEqual(len({c["seed"] for c in calls}), 1)
            self.assertTrue(all(p.is_file() for p in got["paths"]))
            self.assertIn("tekoälyllä luotu", got["note"])
        with TemporaryDirectory() as tmp, patch.dict(os.environ, {**ENV, "KAURIVO_CLOUDFLARE_WORKERS_FREE_CONFIRMED": "0"}):
            self.assertIsNone(generate_sequence("kylpyhuoneremontti", Path(tmp), post=post))

    def test_any_failure_returns_no_sequence(self):
        with TemporaryDirectory() as tmp, patch.dict(os.environ, ENV):
            self.assertIsNone(generate_sequence("kylpyhuone", Path(tmp), post=lambda *a, **k: Reply(429, {})))
            self.assertIsNone(generate_sequence("kylpyhuone", Path(tmp), post=lambda *a, **k: Reply(
                200, {"result": {"image": image_b64((1, 2, 3), (512, 512))}})))

    def test_sequence_hero_is_labelled_and_photos_are_used_once(self):
        plan = {"trade": "rakennus", "hero_style": "blueprint", "headline": "Kylpyhuoneremontit ja vesieristykset",
                "chapters": ["Uudenmaan seudulla."], "statement": "Toteutamme remontit.",
                "services": [{"name": "Kylpyhuoneremontit", "text": "Kylpyhuoneremontit ja vesieristykset."},
                             {"name": "Kosteusmittaus", "text": "Osaavaa kosteusmittausta kokemuksella."}],
                "photo_captions": [], "contact_lead": ""}
        with TemporaryDirectory() as tmp, patch.dict(os.environ, {"KAURIVO_DEPTH_DISABLED": "1"}):
            root = Path(tmp)
            seq, photos = [], []
            for i, colour in enumerate(((60, 60, 60), (90, 140, 190), (150, 150, 150), (120, 120, 125))):
                path = root / f"s{i}.png"
                Image.new("RGB", (1536, 864), colour).save(path)
                seq.append(path)
            for i in range(2):
                path = root / f"p{i}.png"
                Image.new("RGB", (1400, 900), (100 + i * 40, 80, 60)).save(path)
                photos.append(path)
            credit = {"photographer": "x", "provider": "Pixabay"}
            page = render_sales_demo(company={"name": "Testi Oy", "phone": "040 1234567"}, plan=plan,
                                     photos=photos, out_dir=root / "out", credits=[credit, credit], sequence=seq,
                                     sequence_labels=["Pohja", "Vedeneristys", "Laatoitus", "Valmis"],
                                     sequence_note="Havainnekuva, tekoälyllä luotu").read_text(encoding="utf-8")
            self.assertIn("Havainnekuva, tekoälyllä luotu", page)
            self.assertIn('<li data-stage="0.250"><span>2</span>Vedeneristys</li>', page)
            self.assertIn('alt="Havainnekuva: Pohja"', page)
            for name in ("kuva-1-g.webp", "kuva-2-g.webp"):
                self.assertEqual(page.count(f'src="assets/{name}"'), 1, name)
            self.assertNotIn("<p>Kylpyhuoneremontit ja vesieristykset.</p>", page)
            self.assertIn("<p>Osaavaa kosteusmittausta kokemuksella.</p>", page)


if __name__ == "__main__":
    unittest.main()

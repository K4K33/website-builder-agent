import os
from io import BytesIO
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import MagicMock, patch

from PIL import Image, ImageDraw

from utils.sales_demo_pipeline import (SalesDemoBlocked, build_sales_demo, collect_source,
                                       supported, verify_plan)

SOURCE = """Osaavaa remontointia. Toteutamme kokemuksella ja ammattitaidolla tarpeidesi mukaiset
kylpyhuone- ja huoneistoremontit Uudenmaan seudulla. Kylpyhuoneremontit ja vesieristykset.
Osaavaa kosteusmittausta kokemuksella. Vesivahinkojen kuivaustyöt. Julkisivujen rappaustyöt
kokemuksella. Referenssit: As Oy Kylätie 8, 15 kph. As Oy Otsonmäki 62 kph. Alepa 350m2.
Puh : 040 5119 287 hannun(@)saneerausjalaatoitus.com Ota yhteyttä ja pyydä tarjous palveluistamme."""

PLAN = {"trade": "rakennus", "hero_style": "blueprint", "headline": "Kylpyhuoneremontit ja vesieristykset",
        "chapters": ["Kylpyhuone- ja huoneistoremontit Uudenmaan seudulla.", "Yli 30 vuoden kokemus."],
        "statement": "Toteutamme kokemuksella ja ammattitaidolla kylpyhuone- ja huoneistoremontit.",
        "services": [{"name": "Kosteusmittaus", "text": "Osaavaa kosteusmittausta kokemuksella."},
                     {"name": "Lattialämmitys", "text": "Asennamme lattialämmityksen."}],
        "photo_captions": [], "contact_lead": "Ota yhteyttä ja pyydä tarjous.",
        "proof": [{"title": "Referenssit", "items": ["As Oy Kylätie 8, 15 kph", "As Oy Otsonmäki 62 kph",
                                                     "As Oy Keksitty 9, 99 kph"]}]}


def jpeg(width=1400, height=900):
    image = Image.new("RGB", (width, height), (200, 205, 215))
    ImageDraw.Draw(image).rectangle((0, height // 2, width, height), fill=(90, 70, 60))
    buffer = BytesIO()
    image.save(buffer, "JPEG")
    return buffer.getvalue()


class Response:
    def __init__(self, status=200, body=b"", kind="text/html; charset=utf-8", headers=None):
        self.status_code = status
        self.content = body
        self.headers = {"content-type": kind, **(headers or {})}
        self.encoding = "utf-8"

    def iter_content(self, size):
        yield self.content

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


HOME = ("<html><head><title>x</title></head><body><h1>Osaavaa remontointia</h1>"
        f"<p>{SOURCE}</p><a href='/referenssit.html'>Referenssit</a>"
        "<img src='/kuvat/kph1.jpg' width='1400' height='900'><img src='/logo.png'></body></html>")


def fake_get(url, **kwargs):
    if url.endswith("/kuvat/kph1.jpg"):
        return Response(body=jpeg(), kind="image/jpeg")
    if url.endswith("/referenssit.html"):
        return Response(body=b"<html><body><p>As Oy Kylatie</p></body></html>")
    return Response(body=HOME.encode())


def resolve(host, *args, **kwargs):
    return [(2, 1, 6, "", ("93.184.216.34", 443))]


class SalesDemoPipelineTests(unittest.TestCase):
    def test_supported_requires_source_words_and_exact_numbers(self):
        self.assertTrue(supported("Kylpyhuoneremontit ja vesieristykset", SOURCE))
        self.assertTrue(supported("As Oy Kylätie 8, 15 kph", SOURCE, share=1.0))
        self.assertFalse(supported("As Oy Kylätie 8, 16 kph", SOURCE, share=1.0))
        self.assertFalse(supported("Yli 30 vuoden kokemus", SOURCE))

    def test_unverified_fields_are_dropped_and_headline_is_required(self):
        plan, dropped = verify_plan(PLAN, SOURCE)
        self.assertEqual([s["name"] for s in plan["services"]], ["Kosteusmittaus"])
        self.assertEqual(plan["chapters"], ["Kylpyhuone- ja huoneistoremontit Uudenmaan seudulla."])
        self.assertEqual(plan["proof"][0]["items"], ["As Oy Kylätie 8, 15 kph", "As Oy Otsonmäki 62 kph"])
        self.assertIn("service:Lattialämmitys", dropped)
        with self.assertRaises(SalesDemoBlocked) as blocked:
            verify_plan({**PLAN, "headline": "Suomen paras rakennusliike"}, SOURCE)
        self.assertEqual(blocked.exception.code, "sales_headline_unverified")
        with self.assertRaises(SalesDemoBlocked):
            verify_plan({**PLAN, "services": [{"name": "Lattialämmitys"}]}, SOURCE)

    def test_collects_text_contacts_and_own_photos_only(self):
        source = collect_source("https://example.fi/", get=fake_get, resolve=resolve)
        self.assertEqual(source["pages"], 2)
        self.assertEqual(source["phone"], "040 5119 287")
        self.assertEqual(source["email"], "hannun@saneerausjalaatoitus.com")
        self.assertEqual(source["photo_urls"], ["https://example.fi/kuvat/kph1.jpg"])

    def test_end_to_end_render_with_stock_fill_and_one_model_call(self):
        ask = MagicMock(return_value=PLAN)
        with TemporaryDirectory() as tmp:
            stock_paths = []
            for i in range(3):
                path = Path(tmp) / f"s{i}.jpg"
                path.write_bytes(jpeg())
                stock_paths.append({"path": str(path), "photographer": "Ville", "provider": "Pixabay",
                                    "licence": "Pixabay Content License", "source_url": "https://pixabay.com/x"})
            with patch.dict(os.environ, {"KAURIVO_DEPTH_DISABLED": "1"}):
                summary = build_sales_demo("Hannun Saneeraus Oy", "https://example.fi/", Path(tmp) / "out",
                                           work_dir=Path(tmp) / "work", get=fake_get, resolve=resolve, ask=ask,
                                           fetch_stock=lambda *a, **k: stock_paths)
            self.assertEqual(ask.call_count, 1)
            self.assertEqual((summary["own_photos"], summary["stock_photos"]), (1, 3))
            page = Path(summary["page"]).read_text(encoding="utf-8")
            self.assertIn('href="tel:+358405119287"', page)
            self.assertIn("Havainnekuva, kuva: Ville / Pixabay", page)
            self.assertNotIn("Lattialämmitys", page)
            self.assertNotIn("Keksitty", page)
            self.assertIn('rel="icon"', page)


if __name__ == "__main__":
    unittest.main()

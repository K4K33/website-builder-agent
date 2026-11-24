import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import MagicMock, patch

from PIL import Image

import utils.stock_media as stock
from utils.sales_demo import render_sales_demo

KEY = "a" * 56


def reply(status=200, payload=None, content=b"", kind="application/json"):
    r = MagicMock(status_code=status, content=content, headers={"content-type": kind})
    r.json.return_value = payload or {}
    return r


def photo(pid, alt="Modern bathroom with grey tiles", width=4000, height=2600, host="images.pexels.com"):
    return {"id": pid, "width": width, "height": height, "alt": alt, "photographer": "Anna K",
            "photographer_url": "https://www.pexels.com/@anna", "url": f"https://www.pexels.com/photo/{pid}/",
            "src": {"large2x": f"https://{host}/photos/{pid}/x.jpeg"}}


class StockMediaTests(unittest.TestCase):
    def test_queries_follow_the_trade(self):
        self.assertIn("bathroom tiles", stock.queries_for("Kylpyhuoneremontit ja vesieristykset"))
        self.assertEqual(stock.queries_for("Tilitoimisto"), [])

    def test_tags_must_match_the_query_subject(self):
        self.assertFalse(stock._relevant({"text": "solar panels, roof, tiles"}, "bathroom tile installation"))
        self.assertTrue(stock._relevant({"text": "bathroom, tiling, renovation"}, "bathroom tile installation"))
        self.assertTrue(stock._relevant({"text": "Modern bathroom with grey tiles"}, "modern bathroom interior tiles"))

    def test_textures_are_not_heroes(self):
        base = {"width": 3000, "height": 2000}
        self.assertFalse(stock._usable({**base, "text": "tiles, background, green, wallpaper"}))
        self.assertTrue(stock._usable({**base, "text": "bathroom, interior, bathtub"}))

    def test_no_key_means_no_request(self):
        session = MagicMock()
        with patch.dict(os.environ, {"KAURIVO_PEXELS_API_KEY": "", "KAURIVO_PIXABAY_API_KEY": "",
                                     "KAURIVO_OPENVERSE": "0"}), TemporaryDirectory() as tmp:
            self.assertEqual(stock.fetch_stock_photos("laatoitus", Path(tmp), session=session), [])
        session.get.assert_not_called()

    def test_downloads_licensed_landscape_photos_without_people(self):
        listing = {"photos": [photo(1), photo(2, alt="Smiling woman in bathroom"), photo(3, width=900),
                              photo(4, host="evil.example"), photo(5)]}

        def get(url, **kwargs):
            if url == stock.API:
                return reply(payload=listing)
            return reply(content=b"jpegdata", kind="image/jpeg")

        session = MagicMock()
        session.get.side_effect = get
        with patch.dict(os.environ, {"KAURIVO_PEXELS_API_KEY": KEY}), TemporaryDirectory() as tmp:
            credits = stock.fetch_stock_photos("laatoitus", Path(tmp), count=3, session=session)
            self.assertEqual([Path(c["path"]).name for c in credits], ["pexels-1.jpg", "pexels-5.jpg"])
            self.assertTrue(all(c["licence"] == "Pexels License" and c["photographer"] for c in credits))
            self.assertTrue((Path(tmp) / "credits.json").is_file())

    def test_pixabay_and_openverse_licences(self):
        pix = {"hits": [{"id": 7, "imageWidth": 4000, "imageHeight": 2600, "tags": "bathroom, tiles",
                         "largeImageURL": "https://pixabay.com/get/abc.jpg", "user": "Ville",
                         "pageURL": "https://pixabay.com/photos/x-7/"}]}
        ov = {"results": [
            {"id": "u1", "url": "https://live.staticflickr.com/1.jpg", "width": 3000, "height": 2000,
             "title": "Tiled bathroom", "creator": "Liisa", "license": "by", "license_version": "4.0",
             "foreign_landing_url": "https://flickr.com/p/1"},
            {"id": "u2", "url": "https://live.staticflickr.com/2.jpg", "width": 3000, "height": 2000,
             "title": "Bathroom", "creator": "X", "license": "by-nc", "foreign_landing_url": "https://f/2"}]}

        def get(url, **kwargs):
            if url == "https://pixabay.com/api/":
                return reply(payload=pix)
            if url.startswith("https://api.openverse.org/"):
                return reply(payload=ov)
            return reply(content=b"img", kind="image/jpeg")

        session = MagicMock()
        session.get.side_effect = get
        env = {"KAURIVO_PEXELS_API_KEY": "", "KAURIVO_PIXABAY_API_KEY": "b" * 30, "KAURIVO_OPENVERSE": "1"}
        with patch.dict(os.environ, env), TemporaryDirectory() as tmp, \
                patch("utils.kaurivo_demo_readiness.safe_url", return_value=True):
            credits = stock.fetch_stock_photos("kylpyhuone", Path(tmp), count=3, session=session)
        self.assertEqual([c["provider"] for c in credits], ["Pixabay", "Openverse"])
        self.assertEqual(credits[1]["licence"], "CC BY 4.0")  # non-commercial was rejected

    def test_stock_photos_are_labelled_as_illustrations_in_the_demo(self):
        plan = {"trade": "rakennus", "hero_style": "depth", "headline": "Kylpyhuoneremontit avaimet käteen",
                "chapters": ["Vedeneristykset."], "statement": "Testi.",
                "services": [{"name": "Laatoitus", "text": "Laatoitustyöt."}],
                "photo_captions": ["Valmis kylpyhuone"], "contact_lead": ""}
        with TemporaryDirectory() as tmp, patch.dict(os.environ, {"KAURIVO_DEPTH_DISABLED": "1"}):
            paths = []
            for i in range(2):
                p = Path(tmp) / f"s{i}.jpg"
                Image.new("RGB", (400, 260), (120 + i * 40, 110, 100)).save(p)
                paths.append(p)
            credit = {"photographer": "Anna K", "source_url": "https://www.pexels.com/photo/1/", "licence": "Pexels License"}
            page = render_sales_demo(company={"name": "Testi Oy", "phone": "040 1234567"}, plan=plan,
                                     photos=paths, credits=[credit, credit],
                                     out_dir=Path(tmp) / "out").read_text(encoding="utf-8")
            self.assertIn("Kuvat ovat kuvapankin havainnekuvia, eivät yrityksen omia kohteita.", page)
            self.assertIn("Havainnekuva, kuva: Anna K / Pexels", page)
            self.assertNotIn("Valmis kylpyhuone", page)


if __name__ == "__main__":
    unittest.main()


class UnsplashProviderTests(__import__("unittest").TestCase):
    def test_unsplash_results_are_full_size_credited_and_tracked(self):
        import os
        from unittest import mock
        from utils import stock_media

        class Reply:
            def __init__(self, status, data=None, content=b"", ctype="image/jpeg"):
                self.status_code, self._data, self.content, self.headers = status, data, content, {"content-type": ctype}

            def json(self):
                return self._data

        calls = []

        class Session:
            def get(self, url, **kw):
                calls.append(url)
                if "api.unsplash.com/search" in url:
                    return Reply(200, {"results": [{"id": "abc", "width": 6000, "height": 4000,
                                                    "alt_description": "hair salon interior with chairs",
                                                    "urls": {"raw": "https://images.unsplash.com/photo-1?ixid=x"},
                                                    "user": {"name": "Ann Example", "links": {"html": "https://unsplash.com/@ann"}},
                                                    "links": {"html": "https://unsplash.com/photos/abc",
                                                              "download_location": "https://api.unsplash.com/photos/abc/download?ixid=x"}}]})
                if "images.unsplash.com" in url:
                    return Reply(200, content=b"img")
                return Reply(200, {})

        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp, mock.patch.dict(os.environ, {"KAURIVO_UNSPLASH_ACCESS_KEY": "a" * 43, "KAURIVO_STOCK_PROVIDERS": "unsplash"}):
            got = stock_media.fetch_stock_photos("kampaamo", Path(tmp), count=1, session=Session(), queries=["hair salon interior"])
        self.assertEqual(len(got), 1)
        self.assertEqual(got[0]["provider"], "Unsplash")
        self.assertEqual(got[0]["photographer"], "Ann Example")
        self.assertTrue(any("w=3000" in c for c in calls))
        self.assertTrue(any("/download" in c for c in calls))

"""Record evidence of photo priority in a real phone viewport; no design-score fiction."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from utils.browser_qa import inspect_site


PHOTO = '<img src="work.svg" alt="Real company work sample" width="640" height="480">'


def html(body: str) -> str:
    return (
        '<!doctype html><html lang="fi"><head><meta charset="utf-8">'
        '<meta name="viewport" content="width=device-width,initial-scale=1">'
        '<style>body{margin:0;background:#fff;color:#111;font:16px Arial,sans-serif}'
        'main{padding:16px}img{width:100%;height:auto}h1{font-size:32px}'
        '.intro{margin:0;padding:0}</style></head><body>'
        '<header><nav><a href="#main">Company</a></nav></header>'
        '<main id="main"><h1>Authentic work</h1>' + body + '</main>'
        '<footer>Contact</footer></body></html>'
    )


class RealFirstFoldBrowserTests(unittest.TestCase):
    def run_page(self, body):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "work.svg").write_text(
                '<svg xmlns="http://www.w3.org/2000/svg" width="640" height="480">'
                '<rect width="640" height="480" fill="#8b273f"/></svg>',
                encoding="utf-8")
            file = root / "index.html"
            file.write_text(html(body), encoding="utf-8")
            result = inspect_site(file)
        if any("Browser QA unavailable" in issue for issue in result["issues"]):
            self.skipTest("Chromium not available")
        return result

    def test_large_text_first_screen_with_media_below_fold_gets_human_review(self):
        result = self.run_page(
            '<section class="intro" style="min-height:1050px">'
            '<p>Company facts are visible, media will come later.</p></section>'
            '<section>' + PHOTO + '</section>'
        )
        self.assertIn("small_mobile", result["first_fold_observations"])
        first = result["first_fold_observations"]["small_mobile"]
        self.assertEqual(first["visibleMainMedia"], 0)
        self.assertGreater(first["mainMediaBelowFold"], 0)
        self.assertTrue(any(
            flag.get("kind") == "first_view_business_media_below_fold"
            and flag.get("viewport") == "small_mobile"
            for flag in result["visual_review_flags"]
        ), result["visual_review_flags"])
        # This should not be an indiscriminate hard failure: some companies
        # are intentionally text-first and still have excellent design.
        self.assertTrue(result["pass"], result["issues"])

    def test_decorative_gradient_cannot_hide_below_fold_photo_flag(self):
        result = self.run_page(
            '<section class="intro" style="min-height:1050px;'
            'background:linear-gradient(145deg,#eee,#fff)">'
            '<p>Gradient is not a photo of company work.</p></section>'
            '<section>' + PHOTO + '</section>'
        )
        observed = result["first_fold_observations"]["small_mobile"]
        self.assertFalse(observed["heroHasCssBackground"])
        self.assertTrue(any(flag.get("kind") == "first_view_business_media_below_fold"
                            for flag in result["visual_review_flags"]),
                        result["visual_review_flags"])

    def test_authentic_photo_visible_above_fold_has_observed_media(self):
        result = self.run_page('<section class="intro">' + PHOTO + '</section>')
        first = result["first_fold_observations"]["small_mobile"]
        self.assertEqual(first["visibleMainMedia"], 1)
        self.assertGreater(first["firstFoldVisibleMediaArea"], 5000)
        self.assertFalse(any(
            flag.get("kind") == "first_view_business_media_below_fold"
            for flag in result["visual_review_flags"]
        ), result["visual_review_flags"])
        self.assertTrue(result["pass"], result["issues"])


if __name__ == "__main__":
    unittest.main()

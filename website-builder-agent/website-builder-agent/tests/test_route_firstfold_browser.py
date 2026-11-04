"""Real-Chromium proof: placing IMG in hero source does not guarantee visibility.

No external requests, source assets or paid credits. Tested at four widths.
"""
from pathlib import Path
from tempfile import TemporaryDirectory
import os
import unittest

from utils.browser_qa import inspect_site

SVG = ("data:image/svg+xml,%3Csvg%20xmlns%3D'http://www.w3.org/2000/svg'"
       "%20width%3D'800'%20height%3D'600'%3E%3Crect%20width%3D'800'"
       "%20height%3D'600'%20fill%3D'%23996666'/%3E%3C/svg%3E")
REQUIRED={"role":"collection","product_media_required":True}

def html(*, hidden_below_fold: bool) -> str:
    offset="padding-top:115vh;" if hidden_below_fold else "padding-top:8px;"
    return (f'<!doctype html><html lang="fi"><head>'
            f'<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">'
            f'<style>body{{margin:0;font:18px Arial;background:#faf7f3;color:#333}}'
            f'section{{{offset}padding-bottom:30px}}h1{{font-size:36px}}'
            f'img{{width:100%;max-width:500px;height:320px;object-fit:cover}}'
            f'</style></head><body><header>Business</header><main>'
            f'<section><h1>Real products</h1><img src="{SVG}" '
            f'alt="Genuine image fixture"></section></main></body></html>')


class FirstFoldBrowserGateTests(unittest.TestCase):
    def run_page(self, content):
        with TemporaryDirectory() as temp:
            path=Path(temp)/"index.html"
            path.write_text(content,encoding="utf-8")
            result=inspect_site(path,first_view_requirement=REQUIRED)
            if any("Browser QA unavailable" in str(x) for x in result["issues"]):
                if os.getenv("REQUIRE_BROWSER_TESTS")=="1":
                    self.fail(str(result["issues"]))
                self.skipTest("Chromium unavailable outside browser QA CI")
            return result

    def test_image_beneath_full_screen_empty_hero_fails_even_when_same_section(self):
        result=self.run_page(html(hidden_below_fold=True))
        issues=[x for x in result["issues"] if "lacks meaningful merchandise" in x]
        self.assertGreaterEqual(len(issues),2,issues)
        self.assertFalse(result["pass"])

    def test_product_actually_visible_at_first_fold_passes_specific_gate(self):
        result=self.run_page(html(hidden_below_fold=False))
        issues=[x for x in result["issues"] if "lacks meaningful merchandise" in x]
        self.assertFalse(issues,issues)
        self.assertGreater(result["first_fold_observations"]["mobile"]["firstFoldVisibleMediaArea"],10000)


if __name__ == "__main__":
    unittest.main()

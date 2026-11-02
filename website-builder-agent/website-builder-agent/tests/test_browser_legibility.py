"""WCAG risk checks for business text on complex backgrounds; no network."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from utils.browser_qa import inspect_site

def doc(css: str, body: str) -> str:
    return (
      '<!doctype html><html lang="fi"><head><meta charset="utf-8">'
      '<meta name="viewport" content="width=device-width"><title>Test</title>'
      '<style>body{margin:0;font:16px Arial,sans-serif}'
      +css+'</style></head><body><header><nav><a href="#main">Home</a></nav></header>'
      +'<main id="main"><h1>Business service</h1>'+body+
      '</main><footer>Contact info</footer></body></html>'
    )

class ReadabilityBrowserTests(unittest.TestCase):
    def test_text_over_gradient_cannot_silently_pass(self):
        html=doc('.photo{background:linear-gradient(90deg,#fff,#ddd);padding:60px}',
                 '<section class="photo"><p style="color:#ddd">Low contrast against picture</p></section>')
        with TemporaryDirectory() as tmp:
            p=Path(tmp)/"index.html"
            p.write_text(html,encoding="utf-8")
            result=inspect_site(p)
            self.assertFalse(result["pass"])
            self.assertTrue(any("NOT VERIFIABLE" in x for x in result["issues"]),result["issues"])

    def test_text_on_opaque_panel_is_allowed_if_contrast_passes(self):
        html=doc('.photo{background:linear-gradient(90deg,#fff,#ddd);padding:60px}'
                 '.panel{background:#111;color:#fff;padding:18px}',
                 '<section class="photo"><div class="panel"><p>Legible, opaque panel</p></div></section>')
        with TemporaryDirectory() as tmp:
            p=Path(tmp)/"index.html"
            p.write_text(html,encoding="utf-8")
            result=inspect_site(p)
            self.assertTrue(result["pass"],result["issues"])

    def test_tiny_primary_business_text_is_rejected(self):
        html=doc('p{font-size:10px;color:#222}',
                 '<p>Small important pricing and terms are not acceptable</p>')
        with TemporaryDirectory() as tmp:
            p=Path(tmp)/"index.html"
            p.write_text(html,encoding="utf-8")
            result=inspect_site(p)
            self.assertFalse(result["pass"])
            self.assertTrue(any("12px" in x for x in result["issues"]),result["issues"])

if __name__=="__main__":
    unittest.main()

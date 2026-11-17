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


    def test_opaque_dark_gradient_can_pass_proven_wcag_contrast_without_text_boxes(self):
        html=doc('.premium-hero{background:linear-gradient(90deg,#081820,#243a44);'
                 'padding:60px;color:#fff}', '<section class="premium-hero">'
                 '<p style="color:#fff">Readable source-backed premium hero</p></section>')
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/"index.html"
            path.write_text(html,encoding="utf-8")
            result=inspect_site(path)
            self.assertTrue(result["pass"], result["issues"])
            self.assertFalse(any("NOT VERIFIABLE" in issue
                                 for issue in result["issues"]))

    def test_translucent_gradient_is_still_unverified_even_with_white_text(self):
        html=doc('.premium-hero{background:linear-gradient(90deg,'
                 'rgba(8,24,32,.7),rgba(36,58,68,.7));'
                 'padding:60px}', '<section class="premium-hero">'
                 '<p style="color:#fff">Photo-layer contrast unknown</p></section>')
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/"index.html"
            path.write_text(html,encoding="utf-8")
            result=inspect_site(path)
            self.assertFalse(result["pass"])
            self.assertTrue(any("NOT VERIFIABLE" in issue
                                for issue in result["issues"]),result["issues"])

    def test_layered_gradients_remain_unverified_without_real_visual_proof(self):
        html=doc('.premium-hero{background-image:'
                 'linear-gradient(#081820,#243a44),'
                 'linear-gradient(#091720,#182b39);padding:60px}',
                 '<section class="premium-hero">'
                 '<p style="color:#fff">Layered brand hero</p></section>')
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/"index.html"
            path.write_text(html,encoding="utf-8")
            result=inspect_site(path)
            self.assertFalse(result["pass"])
            self.assertTrue(any("NOT VERIFIABLE" in issue
                                for issue in result["issues"]),result["issues"])

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

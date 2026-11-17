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

    def test_weak_translucent_gradient_still_requires_visual_proof(self):
        html=doc('.premium-hero{background:linear-gradient(90deg,'
                 'rgba(8,24,32,.2),rgba(36,58,68,.2));'
                 'padding:60px}', '<section class="premium-hero">'
                 '<p style="color:#fff">Photo-layer contrast unknown</p></section>')
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/"index.html"
            path.write_text(html,encoding="utf-8")
            result=inspect_site(path)
            self.assertFalse(result["pass"])
            self.assertTrue(any("NOT VERIFIABLE" in issue
                                for issue in result["issues"]),result["issues"])

    def test_weak_overlay_over_bright_gradient_remains_unverified(self):
        html=doc('.premium-hero{background-image:'
                 'linear-gradient(rgba(8,24,32,.12),rgba(36,58,68,.12)),'
                 'linear-gradient(#eeeeee,#ffffff);padding:60px}',
                 '<section class="premium-hero">'
                 '<p style="color:#fff">Layered brand hero</p></section>')
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/"index.html"
            path.write_text(html,encoding="utf-8")
            result=inspect_site(path)
            self.assertFalse(result["pass"])
            self.assertTrue(any("NOT VERIFIABLE" in issue
                                for issue in result["issues"]),result["issues"])

    def test_strong_translucent_overlay_proves_contrast_over_any_background(self):
        html=doc('.premium-hero{background-image:'
                 'linear-gradient(90deg,rgba(0,0,0,.82),rgba(15,20,25,.82)),'
                 'linear-gradient(90deg,#fff,#ddd);padding:60px}',
                 '<section class="premium-hero">'
                 '<p style="color:#fff">Source-backed text over layered photo</p></section>')
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/"index.html"
            path.write_text(html,encoding="utf-8")
            result=inspect_site(path)
            self.assertTrue(result["pass"],result["issues"])

    def test_non_srgb_interpolated_gradient_needs_independent_visual_proof(self):
        html=doc('.premium-hero{background-image:'
                 'linear-gradient(in oklab,#080808,#111111);padding:60px}',
                 '<section class="premium-hero">'
                 '<p style="color:#fff">Complex interpolation</p></section>')
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/"index.html"
            path.write_text(html,encoding="utf-8")
            result=inspect_site(path)
            self.assertFalse(result["pass"])
            self.assertTrue(any("NOT VERIFIABLE" in issue
                                for issue in result["issues"]), result["issues"])


    def test_radial_photo_like_dark_background_is_proved_from_actual_browser_pixels(self):
        html=doc('.hero{background:radial-gradient(circle,#071421,#182b31);'
                 'padding:60px}', '<section class="hero">'
                 '<p style="color:#fff">Genuinely readable photographed hero</p></section>')
        with TemporaryDirectory() as tmp:
            page=Path(tmp)/"index.html"
            page.write_text(html, encoding="utf-8")
            result=inspect_site(page)
            self.assertTrue(result["pass"], result["issues"])
            self.assertFalse(any("NOT VERIFIABLE" in issue for issue in result["issues"]))

    def test_actual_background_photo_dark_pixels_pass_but_bright_photo_fails(self):
        from PIL import Image
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            original=doc('.hero{background:url(hero.png);padding:60px}',
                         '<section class="hero"><p style="color:#fff">'
                         'Text over original photo</p></section>')
            page=root/"index.html"
            page.write_text(original,encoding="utf-8")
            image=root/"hero.png"
            Image.new("RGB",(80,80),(9,25,32)).save(image)
            positive=inspect_site(page)
            self.assertTrue(positive["pass"], positive["issues"])
            Image.new("RGB",(80,80),(243,245,246)).save(image)
            negative=inspect_site(page)
            self.assertFalse(negative["pass"])
            self.assertTrue(any("NOT VERIFIABLE" in issue
                                for issue in negative["issues"]),negative["issues"])

    def test_gradient_with_bright_and_dark_pixels_cannot_pass_visual_proof(self):
        html=doc('.hero{background:radial-gradient(circle,#fff,#101010);'
                 'padding:60px}', '<section class="hero">'
                 '<p style="color:#fff">Inconsistent actual contrast</p></section>')
        with TemporaryDirectory() as tmp:
            path=Path(tmp)/"index.html"
            path.write_text(html,encoding="utf-8")
            result=inspect_site(path)
            self.assertFalse(result["pass"])
            self.assertTrue(any("NOT VERIFIABLE" in issue for issue in result["issues"]))

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

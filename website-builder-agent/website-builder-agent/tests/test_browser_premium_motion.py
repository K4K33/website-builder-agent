"""Render proof, not a CSS/JS-token count, of purposeful premium effects."""
import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory

from utils.browser_motion_proof import audit_declared_interactions


class BrowserPremiumMotionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            from playwright.sync_api import sync_playwright
            cls.runner = sync_playwright().start()
            cls.browser = cls.runner.chromium.launch(headless=True)
        except Exception as error:
            if os.getenv("REQUIRE_BROWSER_TESTS") == "1":
                raise
            raise unittest.SkipTest("Chromium not installed: " + str(error))

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.runner.stop()

    def render(self, html):
        root = TemporaryDirectory()
        file = Path(root.name) / "index.html"
        file.write_text(html, encoding="utf-8")
        context = self.browser.new_context(
            viewport={"width": 1000, "height": 700}, reduced_motion="reduce"
        )
        page = context.new_page()
        page.goto(file.as_uri(), wait_until="load")
        return root, context, page

    def test_real_material_light_has_visible_change_and_reduced_fallback(self):
        html = """<!doctype html><html><head><style>
        body{margin:0;background:#eee}.art{
        width:620px;height:420px;
        background:radial-gradient(450px circle at var(--mx,15%) 50%,
                                  #f5dabb,#513f40 68%);}
        @media(prefers-reduced-motion:reduce){.art{transition:none}}
        </style></head><body><main><div class="art"
        data-premium-interaction="pointer-depth"></div></main>
        <script>
        const reduced=matchMedia('(prefers-reduced-motion: reduce)');
        const art=document.querySelector('.art');
        if(!reduced.matches)art.addEventListener('pointermove',event=>{
          const rect=art.getBoundingClientRect();
          art.style.setProperty('--mx',
             ((event.clientX-rect.left)/rect.width*100).toFixed(1)+'%');
        });
        </script></body></html>"""
        root, context, page = self.render(html)
        try:
            result = audit_declared_interactions(page)
            self.assertFalse(result["blocking"], result["blocking"])
            self.assertTrue(result["observations"][0]["screenshot_changed"])
            self.assertTrue(result["pending"])
        finally:
            context.close();root.cleanup()

    def test_claimed_3d_effect_without_actual_rendered_response_is_rejected(self):
        html = """<!doctype html><html><head><style>
        .art{width:620px;height:420px;background:#eee}
        </style></head><body><main>
        <div class="art" data-premium-interaction="pointer-depth">Artwork</div>
        </main></body></html>"""
        root, context, page = self.render(html)
        try:
            result = audit_declared_interactions(page)
            self.assertTrue(result["blocking"])
            self.assertIn("no detectable rendered difference", result["blocking"][0])
        finally:
            context.close();root.cleanup()


if __name__ == "__main__":
    unittest.main()

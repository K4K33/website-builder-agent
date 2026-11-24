"""Scroll-story capability: generic runtime + Kaurivo hero contract (offline)."""
from pathlib import Path
import unittest

from utils.scroll_story import MOTION_BRIEF, enhance_scroll_story

ROOT = Path(__file__).resolve().parents[1]
HOME = ROOT / "docs" / "kaurivo" / "index.html"

PAGE = """<html><head></head><body><section data-story data-stages='[[0,"A","A"]]'>
<div data-k="0,0.2"></div><p data-story-caption></p></section></body></html>"""


class ScrollStoryTests(unittest.TestCase):
    def test_runtime_injected_once(self):
        once = enhance_scroll_story(PAGE)
        twice = enhance_scroll_story(once)
        self.assertEqual(once.count("data-kaurivo-story-runtime"), 2)
        self.assertEqual(twice.count("data-kaurivo-story-runtime"), 2)
        self.assertIn("--k", once)
        self.assertIn("prefers-reduced-motion", once)

    def test_pages_without_story_untouched(self):
        html = "<html><head></head><body><p>x</p></body></html>"
        self.assertEqual(enhance_scroll_story(html), html)

    def test_builder_is_told_how_to_design_motion(self):
        builder = (ROOT / "agents" / "builder.py").read_text(encoding="utf-8")
        self.assertIn("MOTION_BRIEF", builder)
        for rule in ("frame 0 is already a poster", "placeholder blocks", "dead stretch", "data-k", "reduced motion"):
            self.assertIn(rule, MOTION_BRIEF)
        for path in ("utils/site_build_pipeline.py", "utils/sales_demo.py"):
            self.assertIn("enhance_scroll_story", (ROOT / path).read_text(encoding="utf-8"))

    def test_kaurivo_hero_is_a_scroll_story(self):
        html = HOME.read_text(encoding="utf-8")
        self.assertIn("data-story", html)
        self.assertGreaterEqual(html.count("data-k="), 10)
        self.assertIn("data-copy-after", html)
        self.assertIn("data-hero-copy", html)
        self.assertIn("data-hide-while-building", html)
        self.assertEqual(html.count('class="kv-piece '), 3)
        self.assertNotIn("kv-browser", html)
        js = (ROOT / "docs" / "kaurivo" / "assets" / "kv-story.js").read_text(encoding="utf-8")
        self.assertIn("data-story", js)


    def test_browser_audit_passes_kaurivo_and_rejects_wireframes(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            self.skipTest("Playwright unavailable locally")
        import tempfile
        from utils.scroll_story import audit_scroll_story
        wire = ('<html><head></head><body><section data-story data-copy-after="0.9" style="height:300vh">'
                '<div style="position:sticky;top:0;height:100vh">'
                + "".join(f'<i data-k="{i/20},{i/20+.1}" style="display:block;width:120px;height:14px;background:#888;margin:8px auto"></i>' for i in range(6))
                + '<div data-hero-copy><h1>x</h1></div></div></section></body></html>')
        with tempfile.TemporaryDirectory() as tmp, sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                bad = Path(tmp) / "wire.html"
                bad.write_text(enhance_scroll_story(wire), encoding="utf-8")
                page = browser.new_page(viewport={"width": 1440, "height": 900})
                page.goto(bad.as_uri())
                issues = audit_scroll_story(page, output_dir=Path(tmp), viewport="desktop")["issues"]
                self.assertTrue(any("first frame" in i for i in issues), issues)
                self.assertTrue(any("placeholder" in i for i in issues), issues)
                for size in ((1440, 900), (390, 844)):
                    page = browser.new_page(viewport={"width": size[0], "height": size[1]})
                    page.goto(HOME.as_uri())
                    result = audit_scroll_story(page, output_dir=Path(tmp), viewport=str(size[0]))
                    self.assertEqual(result["issues"], [], size)
                    self.assertEqual(len(result["observations"]), 1)
            finally:
                browser.close()


if __name__ == "__main__":
    unittest.main()

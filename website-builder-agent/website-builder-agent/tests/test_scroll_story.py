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
        for rule in ("ONE transformation", "4-5 beats", "data-k", "reduced motion"):
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
        self.assertIn("kuvitteellinen esimerkki", html)
        js = (ROOT / "docs" / "kaurivo" / "assets" / "kv-story.js").read_text(encoding="utf-8")
        self.assertIn("data-story", js)


if __name__ == "__main__":
    unittest.main()

import unittest

from utils.hero_reveal import REVEAL_BRIEF, enhance_hero_reveal

PAGE = """<!doctype html><html><head></head><body>
<section class="hero" data-copy-after="0.8"><img src="a.webp" alt="x">
<div data-hero-copy><h1>Otsikko</h1><a href="tel:1">Soita</a></div></section></body></html>"""


class HeroRevealTests(unittest.TestCase):
    def test_runtime_added_once_and_copy_stays_in_the_page(self):
        out = enhance_hero_reveal(PAGE)
        self.assertEqual(out.count("data-kaurivo-reveal-runtime"), 2)
        self.assertEqual(enhance_hero_reveal(out).count("data-kaurivo-reveal-runtime"), 2)
        self.assertIn("<h1>Otsikko</h1>", out)  # hidden visually only while animating
        self.assertIn(".is-js:not(.is-done) [data-hero-copy]", out)

    def test_untouched_without_marked_copy(self):
        html = PAGE.replace(" data-hero-copy", "")
        self.assertEqual(enhance_hero_reveal(html), html)
        self.assertIn("data-copy-after", REVEAL_BRIEF)


if __name__ == "__main__":
    unittest.main()

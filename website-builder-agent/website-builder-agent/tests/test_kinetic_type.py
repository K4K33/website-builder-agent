import unittest

from utils.kinetic_type import band_html, enhance_kinetic_type, items


PAGE = """<!doctype html><html><head></head><body>
{band}
<ul><li>Kylpyhuoneremontit</li><li>Laatoitus</li><li>Vedeneristys</li></ul></body></html>"""


class KineticTypeTests(unittest.TestCase):
    def test_band_uses_only_short_words_without_numbers(self):
        html = band_html(["Kylpyhuoneremontit", "Laatoitus", "Vedeneristys", "Takuu 10 vuotta"])
        self.assertIn("data-kaurivo-kinetic", html)
        self.assertNotIn("10", html)
        self.assertEqual(band_html(["Yksi"]), "")
        self.assertEqual(items("A|  B  |" + "x" * 40), ["A", "B"])

    def test_enhance_keeps_only_words_that_stand_on_the_page(self):
        band = band_html(["Kylpyhuoneremontit", "Laatoitus", "Saunaremontit"])
        out = enhance_kinetic_type(PAGE.format(band=band))
        self.assertIn("data-kinetic-active", out)
        self.assertIn('aria-hidden="true"', out)
        self.assertIn("kinetic__dot", out)
        self.assertNotIn(">Saunaremontit", out)  # not on the page as real text
        self.assertGreaterEqual(out.count("Laatoitus"), 3)  # repeated to fill the width
        self.assertIn("data-kaurivo-kinetic-runtime", out)
        self.assertEqual(out, enhance_kinetic_type(out))  # idempotent

    def test_band_without_verified_words_is_removed(self):
        out = enhance_kinetic_type(PAGE.format(band=band_html(["Pihatyöt", "Kattotyöt"])))
        self.assertNotIn("data-kaurivo-kinetic", out.replace("data-kaurivo-kinetic-runtime", ""))
        self.assertNotIn("data-kaurivo-kinetic-runtime", out)


if __name__ == "__main__":
    unittest.main()

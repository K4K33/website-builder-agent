"""Regression guard: design V4 anti-template instructions must reach both agents."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class DesignV4PromptTests(unittest.TestCase):
    def test_generation_and_revision_both_have_rules(self):
        text = (ROOT / 'agents' / 'builder.py').read_text(encoding='utf-8')
        marker = 'PREMIUM-ESTETIIKAN V4-PAKOLLINEN LAATURAJA'
        self.assertEqual(text.count(marker), 2)
        for phrase in ('Älä numeroi tavallisia palvelukortteja',
                       'Älä keksi asiakkaalle uutta kuvaketta',
                       'Brändin säilyttäminen tarkoittaa',
                       'sivun avaus, navigaation tilat',
                       'Tämän nykyisen builderin toimitusmuoto on SILTI vain yksi HTML-tiedosto'):
            self.assertEqual(text.count(phrase), 2, phrase)

    def test_doc_exposes_real_output_constraint(self):
        text = (ROOT / 'docs' / 'KAURIVO_DESIGN_STANDARD_V4.md').read_text(encoding='utf-8')
        self.assertIn('still only generates', text)
        self.assertIn('noindex', text)
        self.assertIn('actual browser-rendered', text)

if __name__ == '__main__':
    unittest.main()

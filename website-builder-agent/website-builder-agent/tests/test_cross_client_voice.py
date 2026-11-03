import unittest
from utils.design_distinctness import repeated_company_copy

class CopyTests(unittest.TestCase):
    def test_common_heading(self):
        page = '<main><h1>Palvelut</h1></main>'
        self.assertFalse(repeated_company_copy(page,page)['too_similar'])

    def test_same_long_claim_is_blocked(self):
        title = "Luotettavaa palvelua kaikkien tilanteiden ratkaisemiseen yhdessä"
        first = '<main><h1>' + title + '</h1></main>'
        second = '<main><article><h1>' + title + '</h1></article></main>'
        self.assertTrue(repeated_company_copy(first,second)['too_similar'])

    def test_original_copy_is_allowed(self):
        first = '<main><h1>Pyörän rengas vaihdetaan paikan päällä</h1></main>'
        second = '<main><h1>Kenkien pohjat saavat uuden elämän</h1></main>'
        self.assertFalse(repeated_company_copy(first,second)['too_similar'])

    def test_repeated_long_paragraph(self):
        text = "Tarjoamme yksilöllisiä ja laadukkaita palveluita asiakkaidemme kaikkiin tarpeisiin joka päivä arjessa."
        page = '<main><p>' + text + '</p></main>'
        self.assertTrue(repeated_company_copy(page,page)['too_similar'])

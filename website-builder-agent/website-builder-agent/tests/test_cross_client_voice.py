import unittest
from utils.design_distinctness import repeated_company_copy

class CopyTests(unittest.TestCase):
    def test_common_heading(self):
        page = '<main><h1>Palvelut</h1></main>'
        self.assertFalse(repeated_company_copy(page,page)['too_similar'])

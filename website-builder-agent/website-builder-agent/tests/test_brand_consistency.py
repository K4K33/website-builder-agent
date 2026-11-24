import unittest

from utils.brand_consistency import typeface_issues


class TypefaceConsistencyTests(unittest.TestCase):
    def test_one_or_two_families_pass(self):
        self.assertEqual(typeface_issues({"manrope": 4000}), [])
        self.assertEqual(typeface_issues({"manrope": 4000, "dm sans": 900, "sans-serif": 30}), [])

    def test_section_by_section_typefaces_fail(self):
        problems = typeface_issues({"bricolage grotesque": 3000, "inter": 2500, "fraunces": 300,
                                    "sora": 200, "space grotesk": 150})
        self.assertTrue(problems)
        self.assertIn("5 typefaces", problems[0])

    def test_trace_amounts_ignored(self):
        self.assertEqual(typeface_issues({"manrope": 10000, "inter": 2000, "times new roman": 20}), [])


if __name__ == "__main__":
    unittest.main()

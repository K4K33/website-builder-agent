import unittest

from agents.builder import _phone_key, _validate_generated_content

PAGE = '<html><body><main><h1>T</h1><a href="{}">Soita</a></main></body></html>'


class PhoneLinkEquivalenceTests(unittest.TestCase):
    def test_international_and_local_forms_match(self):
        for href in ("tel:+358401234567", "tel:00358401234567", "tel:040-123 4567", "tel:0401234567"):
            self.assertEqual(_phone_key(href[4:]), _phone_key("040 123 4567"))

    def test_international_link_passes_validation(self):
        _validate_generated_content(PAGE.format("tel:+358401234567"),
                                    {"name": "Testi Oy", "contact_phone": "040 123 4567"})

    def test_a_different_number_is_still_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "Unverified telephone link"):
            _validate_generated_content(PAGE.format("tel:+358401234999"),
                                        {"name": "Testi Oy", "contact_phone": "040 123 4567"})


if __name__ == "__main__":
    unittest.main()


class PinPhoneLinksTests(unittest.TestCase):
    def test_concept_tel_links_point_to_verified_number(self):
        from utils.concept_workflow import pin_phone_links
        html = '<a href="tel:+358 50 999 0000">Soita</a><a href=\'tel:0401234567\'>x</a>'
        out = pin_phone_links(html, {"contact_phone": "040 123 4567"})
        self.assertEqual(out.count('tel:+358401234567'), 2)
        self.assertNotIn("999", out)

    def test_no_verified_phone_leaves_page_for_the_validator(self):
        from utils.concept_workflow import pin_phone_links
        html = '<a href="tel:+358509990000">Soita</a>'
        self.assertEqual(pin_phone_links(html, {}), html)

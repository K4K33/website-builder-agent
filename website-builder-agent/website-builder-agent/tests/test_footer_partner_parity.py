"""No-credit tests for preserving footer sponsor, chain and partner logos."""
import unittest

from utils.footer_partner_parity import audit_footer_affiliations


class FooterPartnerParityTests(unittest.TestCase):
    def test_originals_must_remain_without_invented_logos(self):
        old = [{"name": "Example sponsor", "role": "sponsor",
                "logo": "/images/example.svg", "href": "https://example.org/"}]
        self.assertTrue(any("Missing original footer" in e
                            for e in audit_footer_affiliations(old, [])))
        self.assertEqual(
            audit_footer_affiliations(old, list(old)), []
        )
        self.assertTrue(any("role changed" in e
                            for e in audit_footer_affiliations(
                                old, [{**old[0], "role": "certificate"}])))
        self.assertTrue(any("logo changed" in e
                            for e in audit_footer_affiliations(
                                old, [{**old[0], "logo": "fake-text-logo"}])))
        self.assertTrue(any("href changed" in e
                            for e in audit_footer_affiliations(
                                old, [{**old[0], "href": "https://other.example.org"}])))

    def test_production_requires_current_relation_and_rights(self):
        source = [{"name": "Example partner", "role": "partner",
                   "logo": "/logo.png", "href": "https://example.org"}]
        self.assertGreater(len(audit_footer_affiliations(
            source, source, production=True)), 0)
        verified = [{**source[0], "active_verified": True,
                     "rights_verified": True}]
        self.assertEqual(audit_footer_affiliations(
            source, verified, production=True), [])

    def test_no_sponsors_requires_no_section(self):
        self.assertEqual(audit_footer_affiliations([], []), [])

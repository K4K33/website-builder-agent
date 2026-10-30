"""Offline legal pre-send guard tests; NO outbound email or API usage."""
import unittest

from utils.marketing_compliance import (
    assert_marketing_ready,
    company_is_suppressed,
    make_optout_footer,
    marketing_issues,
    normalize_address,
    SENDER,
)


def generic():
    return {
        "address": "info@example.fi",
        "classification": "legal_entity_generic",
        "verified_legal_entity": True,
        "source_url": "https://example.fi/contact",
        "suppression_registry_checked": True,
        "reviewed_by_human": True,
        "privacy_information_ready": True,
        "optout_handling_ready": True,
    }


class MarketingComplianceTests(unittest.TestCase):
    def test_verified_company_generic_address_can_pass(self):
        self.assertEqual(marketing_issues(generic()), [])
        assert_marketing_ready(generic())

    def test_unknown_unverified_and_missing_evidence_fail_closed(self):
        self.assertTrue(marketing_issues(None))
        record = generic()
        record.pop("classification")
        record["suppression_registry_checked"] = False
        self.assertGreaterEqual(len(marketing_issues(record)), 2)

    def test_personal_employee_requires_job_relevance_or_prior_consent(self):
        record = generic()
        record["address"] = "sara@example.fi"
        record["classification"] = "legal_entity_named_employee"
        self.assertTrue(marketing_issues(record))
        record["role_relevance_documented"] = True
        record["role_relevance_reason"] = "Verified person decides website procurement"
        self.assertEqual(marketing_issues(record), [])

    def test_sole_trader_requires_consent_not_generic_company_exception(self):
        record = generic()
        record["classification"] = "natural_person"
        self.assertTrue(marketing_issues(record))
        record["consent_evidence"] = "Recorded consent with purpose, date and source"
        self.assertEqual(marketing_issues(record), [])

    def test_suppressed_or_objected_contact_never_passes(self):
        record = generic()
        self.assertTrue(marketing_issues(record, suppressed_addresses=["INFO@EXAMPLE.FI"]))
        record["opted_out"] = True
        with self.assertRaises(RuntimeError):
            assert_marketing_ready(record)

    def test_missing_sender_privacy_transparency_or_optout_blocks(self):
        record = generic()
        self.assertTrue(marketing_issues(record, sender="personal@gmail.com"))
        record["privacy_information_ready"] = False
        self.assertTrue(marketing_issues(record))
        record["privacy_information_ready"] = True
        record["optout_handling_ready"] = False
        self.assertTrue(marketing_issues(record))

    def test_footer_is_clear_free_reply_route_and_real_sender(self):
        plain, html = make_optout_footer()
        self.assertIn("Kieltäydy jatkoviesteistä", plain)
        self.assertIn(SENDER, plain)
        self.assertIn("mailto:" + SENDER, html)
        self.assertIn("Kieltäydy jatkoviesteistä", html)

    def test_email_header_injection_and_company_suppression(self):
        self.assertFalse(normalize_address("person@example.fi\nBcc:evil@example.org"))
        self.assertFalse(normalize_address("Friend <person@example.fi>"))
        self.assertTrue(company_is_suppressed({"marketing_opt_out": True}))
        self.assertTrue(company_is_suppressed({"do_not_contact": True}))
        self.assertFalse(company_is_suppressed({}))


if __name__ == "__main__":
    unittest.main()

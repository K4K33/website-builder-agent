"""Source-grounded date claims: generic unseen-company regression tests."""
import unittest
from utils.temporal_claims import audit_temporal_claims


class TemporalClaimTests(unittest.TestCase):
    def test_operations_start_must_not_be_relabelled_registration(self):
        research = {"source_inventory": {"pages": [
            {"url": "https://example.org/about",
             "text": "Yrityksen toiminta käynnistynyt 2008. Kone- ja prosessisuunnittelua."}
        ]}}
        page = {"index.html": "<main><p>Yritys rekisteröity 2008</p></main>"}
        result = audit_temporal_claims(page, research)
        self.assertFalse(result["pass"])
        self.assertIn("not as incorporation", result["issues"][0])

    def test_correctly_labeled_operations_start_passes(self):
        research = {"fact_sources": [
            {"kind": "operations_started_year", "value": "2008",
             "source_url": "https://example.org/about"}
        ]}
        result = audit_temporal_claims(
            {"index.html": "<p>Toiminta käynnistynyt 2008</p>"}, research)
        self.assertTrue(result["pass"])

    def test_separately_evidenced_registration_is_allowed(self):
        research = {"fact_sources": [
            {"kind": "operations_started_year", "value": "2008"},
            {"kind": "registration_year", "value": "2008"},
        ]}
        result = audit_temporal_claims(
            {"index.html": "<p>Yritys rekisteröity 2008</p>"}, research)
        self.assertTrue(result["pass"])

    def test_missing_source_does_not_generate_a_fake_date(self):
        result = audit_temporal_claims(
            {"index.html": "<p>Yritys rekisteröity 2008</p>"}, {})
        self.assertTrue(result["pass"])
        # No-source case must still fail the separate source-fidelity gate.


if __name__ == "__main__":
    unittest.main()

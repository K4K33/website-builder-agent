"""No-API tests for the Kaurivo automatic general feedback loop."""
from tempfile import TemporaryDirectory
from pathlib import Path
import unittest

from utils.global_feedback import (
    load_ledger, save_ledger, record_qa_findings, record_owner_feedback,
    global_instructions, universal_rules_pending_implementation,
)


class GeneralLearningTests(unittest.TestCase):
    def test_repeated_problem_becomes_global_candidate_after_two_companies(self):
        ledger = load_ledger("/no/such/kaurivo-ledger")
        record_qa_findings(ledger, "company-a", ["decorative card numbering: 01"])
        self.assertEqual(ledger["issues"]["no_decorative_numbering"]["status"],
                         "observed")
        record_qa_findings(ledger, "company-a", ["decorative card numbering: 02"])
        self.assertEqual(ledger["issues"]["no_decorative_numbering"]["status"],
                         "observed")
        record_qa_findings(ledger, "company-b", ["decorative card numbering: 03"])
        self.assertEqual(ledger["issues"]["no_decorative_numbering"]["status"],
                         "universal_candidate")
        self.assertEqual(len(
            ledger["issues"]["no_decorative_numbering"]["project_slugs"]), 2)

    def test_all_owner_feedback_is_recorded_but_not_fake_implemented(self):
        ledger = {"schema_version": 1, "issues": {}, "user_rules": []}
        rule = record_owner_feedback(
            ledger, text="New universal idea for footers",
            applies_to_all=True)
        self.assertEqual(rule["status"], "needs_implementation")
        self.assertIn("New universal idea", global_instructions(ledger))
        self.assertTrue(universal_rules_pending_implementation(ledger))
        fixed = record_owner_feedback(
            ledger, text="Avoid decorative card numbering",
            applies_to_all=True,
            checker="no_decorative_numbering",
            regression_test="tests/test_design_distinctness.py")
        self.assertEqual(fixed["status"], "active")

    def test_company_specific_preference_not_spread(self):
        ledger = {"schema_version": 1, "issues": {}, "user_rules": []}
        rule = record_owner_feedback(ledger, text="Use purple for this client",
                                     company_slug="test-client", applies_to_all=False)
        self.assertEqual(rule["status"], "local_only")
        self.assertEqual(ledger["user_rules"], [])

    def test_persists_and_loads_without_network(self):
        with TemporaryDirectory() as temp:
            path = Path(temp) / "quality_ledger.json"
            original = {"schema_version": 1, "issues": {}, "user_rules": []}
            record_qa_findings(original, "firm", ["mobile overflow on 320px"])
            save_ledger(path, original)
            self.assertEqual(load_ledger(path), original)


if __name__ == "__main__":
    unittest.main()

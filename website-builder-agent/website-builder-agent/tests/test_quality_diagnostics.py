"""Offline self-tests for truthful, full-suite error attribution."""
import unittest

from scripts.quality_diagnostics import classify_issue, render_markdown


class DiagnosticTests(unittest.TestCase):
    def test_classifies_source_failure_with_code_location(self):
        trace = ('Traceback (most recent call last):\n'
                 '  File "/tmp/project/tests/test_quality.py", line 99, in test_builder\n'
                 '  File "/tmp/project/utils/industry_workflow.py", line 197, in validate_inventory\n'
                 'RuntimeError: Company has neither source website nor verified no-site profile.')
        diagnosis = classify_issue(trace)
        self.assertEqual(diagnosis["category"], "source_evidence")
        self.assertEqual(diagnosis["likely_source"]["line"], 197)
        self.assertIn("industry_workflow.py", diagnosis["likely_source"]["file"])

    def test_classifies_trial_collision_without_claiming_certainty(self):
        result = classify_issue("RuntimeError: Scout returned no company with a saved record.")
        self.assertEqual(result["category"], "trial_identity")
        self.assertIn("heuristic", result["confidence"])

    def test_unknown_failure_is_visible(self):
        self.assertEqual(classify_issue("ValueError: unexpected new problem")["category"], "unclassified")

    def test_failures_never_render_as_success(self):
        summary = {"tests_run": 432, "failures": 1, "errors": 0,
                   "skipped": 0, "passed": False,
                   "groups": {"navigation": [{"test": "test_link", "likely_source": None,
                                              "exception": "Broken route"}]}}
        output = render_markdown(summary)
        self.assertIn("**FAIL**", output)
        self.assertIn("blocked", output)
        self.assertIn("navigation", output)


if __name__ == "__main__":
    unittest.main()

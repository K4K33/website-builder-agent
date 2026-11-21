import io
from pathlib import Path
import unittest

from scripts.run_kaurivo_demo_queue import classify_stage_failure

ROOT = Path(__file__).resolve().parents[1]


class VisualQaRejectionTests(unittest.TestCase):
    def test_final_rejection_has_its_own_code(self):
        log = io.StringIO("Traceback\nRuntimeError: VISUAL_QA_REJECTED_AFTER_REVISION: "
                          "diag=passing_views:7,critical_issues:5\n")
        self.assertEqual(classify_stage_failure(log, "building"), "visual_qa_rejected")

    def test_two_bounded_revisions_before_rejection(self):
        src = (ROOT / "utils/concept_workflow.py").read_text(encoding="utf-8")
        self.assertIn("for revision in range(3):", src)
        self.assertIn("if revision == 2:", src)


if __name__ == "__main__":
    unittest.main()

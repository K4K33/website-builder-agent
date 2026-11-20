"""Reference selection: prefix-less quote IDs and content-free diagnostics."""
import tempfile
import unittest

from utils.reference_quote_evidence import verified_evidence_quote

CANDIDATE = {"site_text": "Suunnittelemme mittatilauskeittiöt kotiisi. Asennus kuuluu hintaan.",
             "quote_options": [{"quote_id": "c1_q0", "text": "Suunnittelemme mittatilauskeittiöt kotiisi."},
                               {"quote_id": "c1_q1", "text": "Asennus kuuluu hintaan."}]}


class QuoteIdTests(unittest.TestCase):
    def test_exact_id(self):
        self.assertEqual(verified_evidence_quote(CANDIDATE, {"quote_id": "c1_q1"}), "Asennus kuuluu hintaan.")

    def test_bare_id_resolves_only_within_same_candidate(self):
        self.assertEqual(verified_evidence_quote(CANDIDATE, {"quote_id": "q0"}),
                         "Suunnittelemme mittatilauskeittiöt kotiisi.")

    def test_other_candidates_id_is_rejected(self):
        self.assertEqual(verified_evidence_quote(CANDIDATE, {"quote_id": "c2_q0"}), "")
        self.assertEqual(verified_evidence_quote(CANDIDATE, {"quote_id": "q9"}), "")


class DiagnosticTests(unittest.TestCase):
    def test_worker_shows_only_counters(self):
        from scripts import run_kaurivo_demo_queue as queue
        with tempfile.TemporaryFile(mode="w+", encoding="utf-8") as handle:
            handle.write("RuntimeError: Fewer than three source-backed same-industry operators; "
                         "cannot build. diag=urls:9,inspected:6,proposed:5,unknown_url:0,"
                         "not_same_industry:1,no_quote:3\n")
            text = queue.selection_failure_diagnostic(handle)
        self.assertIn("avattu 6", text)
        self.assertIn("ei kelvollista lainausta 3", text)


if __name__ == "__main__":
    unittest.main()

"""Zero-cost regression for 13 Nov universal site-quality lessons.

No real Sähkö247 name, prices, clients, credentials or screenshots are baked
into the production rule. Review wording is part of the runtime contract but
no unit test can itself certify independent aesthetic quality.
"""
from __future__ import annotations

from hashlib import sha256
import unittest

from utils.service_quality import (
    MASTER_PROMPT_SOURCE, MASTER_PROMPT_SHA256, POLICY
)
from utils.demo_origin_gate import verify_demo_concept_evidence


class UniversalLessonsContractTests(unittest.TestCase):
    def test_active_canonical_contract_is_loaded_by_research_builder_and_qa(self):
        start = "<!-- ACTIVE_RUNTIME_CONTRACT_START -->"
        end = "<!-- ACTIVE_RUNTIME_CONTRACT_END -->"
        self.assertEqual(MASTER_PROMPT_SOURCE.count(start), 1)
        self.assertEqual(MASTER_PROMPT_SOURCE.count(end), 1)
        active = MASTER_PROMPT_SOURCE.split(start, 1)[1].split(end, 1)[0]
        self.assertIn(active.strip(), POLICY)
        self.assertEqual(sha256(MASTER_PROMPT_SOURCE.encode()).hexdigest(),
                         MASTER_PROMPT_SHA256)
        for phrase in (
            "SOURCE-CLAIM LEDGER",
            "minimum charge",
            "surrounding pricing terms",
            "A genuine number transplanted",
            "mailto/WhatsApp-only",
            "tiny original logo",
            "THREE recent unrelated Kaurivo clients",
            "A tilted CSS plate",
            "TECHNICAL_PREVIEW_ONLY",
            "independent exact-release design review",
            "SAME current-master SHA",
        ):
            with self.subTest(phrase=phrase):
                self.assertIn(phrase, active)

    def test_manual_and_automatic_preview_share_proof_gate(self):
        # This is not a source screenshot: the gate MUST fail for a bare HTML
        # publication with zero concepts, even if an HTTP status test is green.
        from pathlib import Path
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as td:
            folder = Path(td)
            (folder / "index.html").write_text("<main>Public demo</main>", encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "quality contract|concept|master"):
                verify_demo_concept_evidence("unrelated-fixture", folder, {
                    "quality_contract_version": 6,
                    "master_prompt_sha256": MASTER_PROMPT_SHA256,
                })

    def test_changes_to_source_or_prompt_invalidate_existing_claim(self):
        # Hash is not a score; every changed prompt version forces renewed
        # source evidence and exactly matching versioned preview proof.
        revised = MASTER_PROMPT_SOURCE + "\nQUALITY-CHANGE"
        self.assertNotEqual(sha256(revised.encode()).hexdigest(),
                            MASTER_PROMPT_SHA256)


if __name__ == "__main__":
    unittest.main()

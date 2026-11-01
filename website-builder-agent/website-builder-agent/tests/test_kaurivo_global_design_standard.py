"""Zero-API regression tests for universal Kaurivo customer-quality guidance."""
import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class UniversalDesignStandardTests(unittest.TestCase):
    def test_every_client_has_one_checklist_and_evidence_requirements(self):
        checklist = (ROOT / "docs" / "KAURIVO_GLOBAL_DESIGN_QA_CHECKLIST.md").read_text(encoding="utf-8")
        for required in (
            "ALL clients", "Five-second comprehension", "customer work",
            "verified services", "genuine ordered sequence", "external URL",
            "pricing", "cold-start", "320, 390, 768 and 1440",
            "CMS", "independently reviewed", "NOT TESTED",
        ):
            self.assertIn(required.lower(), checklist.lower(), required)
        self.assertGreaterEqual(checklist.count("- [ ]"), 19)
        # The standard must be independent of any example client company.
        self.assertNotIn("Kotifixi", checklist)

    def test_master_playbook_and_design_standard_link_global_checklist(self):
        for path in ("docs/KAURIVO_PREMIUM_PLAYBOOK.md", "docs/KAURIVO_DESIGN_STANDARD_V4.md"):
            content = (ROOT / path).read_text(encoding="utf-8")
            self.assertIn("KAURIVO_GLOBAL_DESIGN_QA_CHECKLIST.md", content, path)

    def test_builder_and_reviser_receive_new_brand_and_clarity_rules(self):
        content = (ROOT / "agents/builder.py").read_text(encoding="utf-8")
        ast.parse(content, filename="agents/builder.py")
        self.assertEqual(content.count("KAIKKIEN ASIAKKAIDEN YLEIN PREMIUM-LAATUPORTTI"), 2)
        for rule in ("Viiden sekunnin mobiilitesti",
                     "mihin se ja muut navigointi-, yhteys- ja hinnastolinkit",
                     "Poista toisteinen markkinointitäyte",
                     "hidas hosting-kylmäkäynnistys"):
            self.assertEqual(content.count(rule), 2, rule)

    def test_content_and_visual_qa_must_review_every_client(self):
        content = (ROOT / "agents/qa.py").read_text(encoding="utf-8")
        ast.parse(content, filename="agents/qa.py")
        self.assertIn("YLEINEN ASIAKASSIVUJEN SISÄLLÖN JA POLKUJEN QA", content)
        self.assertIn("PAKOLLINEN YLEINEN KAIKKIEN ASIAKKAIDEN VISUAALINEN TARKISTUS", content)
        for rule in ("Ensimmäinen mobiilinäkymä",
                     "logon alkuperäisyys",
                     "todelliset hinnasto-/yhteyslinkkien kohteet",
                     "kuva-aihe johtaa harhaan",
                     "merkitse se todentamattomaksi"):
            self.assertIn(rule, content)

    def test_human_verification_not_replaced_by_qa_model(self):
        content = (ROOT / "docs/KAURIVO_GLOBAL_DESIGN_QA_CHECKLIST.md").read_text(encoding="utf-8")
        self.assertIn("reviewed", content.lower())
        self.assertIn("Customer permission to share preview", content)
        self.assertIn("Owner approval for publication (separate)", content)


if __name__ == "__main__":
    unittest.main()

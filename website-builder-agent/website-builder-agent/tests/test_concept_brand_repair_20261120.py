"""Deterministic last-resort repair for two measured V8 concept defects."""
import unittest
from pathlib import Path

from utils.brand_direction_v8 import audit_art_direction, repair_v8_findings

RESEARCH = {
    "v8_visual_protocol": "v8",
    "source_inventory": {"pages": [{
        "url": "https://ostroferia.example/",
        "source_identity": {"theme_color": "#8a1c2b",
                            "original_logo_candidates": ["https://ostroferia.example/logo.png"]},
    }]},
    "primary_offering_evidence": {"label": "Osterit ja meren antimet",
                                  "quote": "Tarjoilemme osterit ja meren antimet",
                                  "source_url": "https://ostroferia.example/"},
}
PAGE = """<html><head><style>:root{--brand:#ff3b30}.cta{background:#ff3b30;color:#fff}
.x{border-color:#ff3b30}</style></head><body><main><section><h1>Tervetuloa</h1>
<p>Ravintola Helsingissä.</p></section></main></body></html>"""


class ConceptBrandRepairTests(unittest.TestCase):
    def test_defects_are_detected_then_repaired(self):
        before = audit_art_direction({"index.html": PAGE}, RESEARCH)
        codes = {f["code"] for f in before["blocking"]}
        self.assertEqual(codes, {"unproven_brand_accent", "verified_service_not_visible_in_hero"})
        fixed = repair_v8_findings({"index.html": PAGE}, RESEARCH)
        html = fixed["index.html"]
        self.assertNotIn("#ff3b30", html.lower())
        self.assertIn("#8a1c2b", html)
        self.assertIn("Osterit ja meren antimet", html)
        self.assertTrue(audit_art_direction(fixed, RESEARCH)["pass"])

    def test_no_observed_palette_means_no_invented_colour(self):
        research = {**RESEARCH, "source_inventory": {"pages": [{
            "url": "https://ostroferia.example/",
            "source_identity": {"original_logo_candidates": ["https://ostroferia.example/logo.png"]}}]}}
        fixed = repair_v8_findings({"index.html": PAGE}, research)
        self.assertIn("#ff3b30", fixed["index.html"].lower())

    def test_clean_page_is_unchanged(self):
        clean = PAGE.replace("#ff3b30", "#8a1c2b").replace(
            "<p>Ravintola", "<p>Osterit ja meren antimet. Ravintola")
        self.assertEqual(repair_v8_findings({"index.html": clean}, RESEARCH)["index.html"], clean)

    def test_workflow_runs_brand_repair_before_contrast_repair(self):
        source = (Path(__file__).resolve().parents[1] / "utils/concept_workflow.py").read_text(encoding="utf-8")
        self.assertLess(source.index("repair_v8_findings(pages_now, research)"),
                        source.index("repair_browser_contrast(previous, findings)"))


if __name__ == "__main__":
    unittest.main()

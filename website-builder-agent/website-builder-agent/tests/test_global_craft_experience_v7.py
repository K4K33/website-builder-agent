"""Live UX comparator regressions; no third-party browsing or AI charges."""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from utils.global_craft_experience import (
    GLOBAL_CRAFT_NAMES, required_global_craft_sites,
    collect_global_craft_evidence, compare_experiences,
)
from scripts.audit_v7_reference_scroll import audit


class GlobalCraftExperiences(TestCase):
    def test_awarded_qa_trio_is_exact_and_distinct_from_sector_library(self):
        rows=required_global_craft_sites()
        self.assertEqual(tuple(x["name"] for x in rows), GLOBAL_CRAFT_NAMES)
        self.assertEqual(len({x["url"] for x in rows}),3)
        self.assertNotIn("Singer Vehicle Design",GLOBAL_CRAFT_NAMES)
        self.assertEqual([x["url"] for x in rows],[
            "https://landonorris.com/",
            "https://brand.dropbox.com/",
            "https://www.igloo.inc/"])
        self.assertTrue(all(x["discipline"] for x in rows))

    def test_no_single_screenshot_can_certify_global_craft_experience(self):
        rows=collect_global_craft_evidence(
            capture=lambda url,name: {"desktop":"screenshot.png",
                                      "mobile":"screenshot.png"})
        self.assertFalse(rows["all_three_scrolled"])
        self.assertEqual(rows["calibration_status"],"INCOMPLETE_REFERENCE_EVIDENCE")
        self.assertTrue(all(x["status"]=="EXPERIENCE_PENDING" for x in rows["benchmarks"]))
        self.assertIsNone(rows["independent_9_5_score"])

    def test_experience_comparison_cannot_self_certify_visual_quality(self):
        rows=collect_global_craft_evidence(capture=lambda url,name: None)
        comparison=compare_experiences(rows,{"desktop":{"status":"observed","frames":[]},
                                             "mobile":{"status":"observed","frames":[]}})
        self.assertFalse(comparison["reference_all_three_scrolled"])
        self.assertTrue(comparison["generated_home_scrolled"])
        self.assertFalse(comparison["comparison_assessed_by_expert"])
        self.assertIsNone(comparison["quality_score"])
        self.assertIn("timing of reveals",comparison["review_instructions"])

    def test_global_live_audit_targets_only_three_awarded_sites(self):
        with TemporaryDirectory() as folder:
            with patch("scripts.audit_v7_reference_scroll.capture_website",return_value=None) as capture:
                result=audit(global_craft=True,output_dir=folder)
            self.assertEqual(result["mode"],"three_global_awarded_craft_benchmarks")
            self.assertEqual(result["attempted"],3)
            self.assertEqual(result["actually_scrolled_and_evidenced"],0)
            self.assertEqual([x["url"] for x in result["entries"]],
                             [x["url"] for x in required_global_craft_sites()])
            self.assertEqual(capture.call_count,3)
            self.assertTrue(Path(folder,"report.json").is_file())
            self.assertFalse(result["quality_9_5_certified"])

    def test_production_qa_includes_experience_gate_and_browser_motion_evidence(self):
        base=Path(__file__).resolve().parents[1]
        qa=(base/"agents/qa.py").read_text("utf-8")
        workflow=(base.parents[1]/".github/workflows/kaurivo-demo-worker.yml").read_text("utf-8")
        self.assertIn('KAURIVO_LIVE_CRAFT_QA: "1"',workflow)
        self.assertIn("collect_global_craft_evidence(",qa)
        self.assertIn("capture_generated_site_journey(",qa)
        self.assertIn("critical_experience_gaps",qa)
        self.assertIn("GLOBAL AWARD-WINNING UX COMPARISON",qa)
        self.assertIn("reference_all_three_scrolled",qa)
        self.assertIn("generated_home_scrolled",qa)


if __name__=="__main__":
    import unittest
    unittest.main()

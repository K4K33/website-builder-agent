"""Different business every first-pass trial, never overfit repeat demos."""
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest
from utils.blind_trials import (
    assess_new_company, reserve_blind_trial, trial_history, first_pass_metrics, record_first_pass_qa
)

class BlindTrialTests(unittest.TestCase):
    def test_history_rejects_same_domain_even_with_a_new_display_name(self):
        history=[{"slug":"old-garden-v1","url":"https://www.garden.example.fi/"}]
        candidate={"name":"Another demo brand","url":"http://garden.example.fi/services"}
        self.assertFalse(assess_new_company(candidate,history=history)["eligible"])
        self.assertTrue(assess_new_company(
            {"name":"A genuinely new furniture studio","url":"https://new-studio.example.fi"},
            history=history)["eligible"])

    def test_reservation_is_persistent_and_prevents_repeat_building(self):
        with TemporaryDirectory() as d:
            root=Path(d)
            known=root/"history.json"
            known.write_text(json.dumps({"trials":[{"slug":"previous-clinic","url":"https://clinic.test.fi"}]}))
            registry=root/"trial-registry.json"
            first={"name":"Garage service","url":"https://garage.test.fi"}
            reserve_blind_trial(first,slug="garage-service",registry_path=registry,
                                history_path=known,now="2026-11-02T00:00:00Z")
            with self.assertRaisesRegex(RuntimeError,"previously tested"):
                reserve_blind_trial(first,slug="garage-service",
                                    registry_path=registry,history_path=known)
            with self.assertRaisesRegex(RuntimeError,"previously tested"):
                reserve_blind_trial({"name":"Garage 2","url":"https://garage.test.fi"},
                                    slug="garage-2",registry_path=registry,history_path=known)
            with self.assertRaisesRegex(RuntimeError,"previously tested"):
                reserve_blind_trial({"name":"Clinic","url":"https://clinic.test.fi"},
                                    slug="any",registry_path=registry,history_path=known)
            self.assertEqual(len(trial_history(known,registry)),2)
            self.assertEqual(first_pass_metrics(trial_history(known,registry))["first_pass_trials"],1)

    def test_first_pass_is_recorded_once_without_fabricating_independent_score(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            history=root/"history.json"
            history.write_text(json.dumps({"trials":[]}))
            registry=root/"trials.json"
            reserve_blind_trial(
                {"name":"Brand new maker","url":"https://brand-new-maker.example.fi"},
                slug="brand-new-maker",registry_path=registry,history_path=history,
                now="2026-11-02T00:00:00Z"
            )
            qa={"overall_pass":False,
                "site_pages":["index.html","palvelut/index.html"],
                "source_fidelity":{"missing":[{"kind":"missing_original_affiliation_image"}],
                    "manifest":{"source_page_count":5}},
                "content_parity":{"missing":[]},
                "browser":{"issues":["mobile overflow"]},
                "originality":{"warnings":["Generic hero"],"blocking_problems":[]},
                "content_review":{"ai_style_review":{"risk_score":4.5},
                    "visual_review":{"desktop":85}}}
            metrics=record_first_pass_qa(registry,slug="brand-new-maker",qa_report=qa)
            self.assertEqual(metrics["generated_page_count"],2)
            self.assertEqual(metrics["source_page_count"],5)
            self.assertEqual(metrics["missing_original_content"],1)
            self.assertEqual(metrics["ai_style_risk"],4.5)
            self.assertIsNone(metrics["independent_quality_score"])
            with self.assertRaisesRegex(RuntimeError,"overwrite"):
                record_first_pass_qa(registry,slug="brand-new-maker",
                                     qa_report={"overall_pass":True})

    def test_absent_independent_review_does_not_fake_a_good_score(self):
        results=first_pass_metrics([
            {"slug":"a","mode":"first_pass_unseen","quality_evidence":"not_verified"},
            {"slug":"b","mode":"first_pass_unseen","quality_evidence":"verified",
             "independent_quality_score":8.5},
            {"slug":"c","mode":"first_pass_unseen","quality_evidence":"verified",
             "independent_quality_score":9.7},
        ])
        self.assertEqual(results["independently_reviewed"],2)
        self.assertEqual(results["over_95_first_pass"],1)
        self.assertEqual(results["pass_rate"],0.5)

if __name__=="__main__":
    unittest.main()

"""Bounded independent vision QA: all real views and no fabricated approvals."""
import json
import unittest
from utils.kaurivo_staged_visual_review import staged_concept_review


def sample_reviews():
    views = []
    for alias in ("A", "B", "C"):
        for index in range(4):
            views.append({"id": f"{alias.lower()}-{index}", "alias": alias,
                          "path": f"{alias}/{index}.png"})
    sources = [{"path": "original/desktop.png", "viewport": "desktop",
                "sha256": "a"*64},
               {"path": "original/mobile.png", "viewport": "mobile",
                "sha256": "b"*64}]
    return views, sources


class StagedVisualReviewTests(unittest.TestCase):
    def test_every_real_view_is_reviewed_with_source_and_independent_ranking(self):
        views, sources = sample_reviews()
        calls = []

        def ask(system, prompt, *, image_paths, max_tokens):
            calls.append((system, prompt, image_paths, max_tokens))
            if image_paths is None:
                self.assertEqual(len(calls), 4)
                supplied = json.loads(prompt)["visual_evidence_review"]
                self.assertEqual(set(supplied), {"A", "B", "C"})
                return {"selected_alias": "B", "cross_comparison":
                        "B is the strongest on all four viewports; A and C still "
                        "have greater content-density and hierarchy weaknesses."}
            index = len(calls)-1
            self.assertEqual(len(image_paths), 6)
            self.assertEqual(image_paths[-2:], ["original/desktop.png", "original/mobile.png"])
            alias = "ABC"[index]
            return {
                "observation": f"{alias} clearly preserves source branding across "
                               "all reviewed routes and both responsive viewports.",
                "critical_issues": [],
                "source_reference_reviewed": True,
                "view_assessments": {
                    f"{alias.lower()}-{j}": {
                        "verdict": "pass",
                        "brand_evidence": "Verified source color and logo evidence "
                                          "preserved with the intended business identity.",
                        "composition_evidence": "Distinct responsive hierarchy "
                                           "and balanced spacing in the shown viewport.",
                        "media_evidence": "Actual provided brand and product "
                                          "assets are visually present and legible.",
                    } for j in range(4)
                },
            }

        report = staged_concept_review(
            research={"company_facts": {}, "site_architecture": {}},
            order={"A": {}, "B": {}, "C": {}},
            views=views, sources=sources,
            root=__import__("pathlib").Path("/private"), ask=ask)
        self.assertEqual(report["selected_alias"], "B")
        self.assertEqual(set(report["view_assessments"]),
                         {v["id"] for v in views})
        self.assertEqual(report["review_batches"], 3)
        self.assertEqual(len(calls), 4)
        self.assertTrue(report["source_reference_reviewed"])
        self.assertEqual(calls[-1][2], None)

    def test_missing_or_unverified_single_view_cannot_be_ranked_or_published(self):
        views, sources = sample_reviews()
        calls = []

        def ask(system, prompt, *, image_paths, max_tokens):
            calls.append(image_paths)
            return {"observation": "A brief review without proven individual views "
                                   "cannot establish brand fidelity on its own.",
                    "critical_issues": [], "source_reference_reviewed": True,
                    "view_assessments": {}}
        with self.assertRaisesRegex(RuntimeError, "variant report invalid"):
            staged_concept_review(research={}, order={"A":{},"B":{},"C":{}},
                                  views=views, sources=sources,
                                  root=__import__("pathlib").Path("/private"), ask=ask)
        self.assertEqual(len(calls), 1)

    def test_no_source_images_block_premium_review_but_allow_proved_no_website(self):
        views, _ = sample_reviews()
        with self.assertRaisesRegex(RuntimeError, "original-site"):
            staged_concept_review(research={}, order={"A":{},"B":{},"C":{}},
                                  views=views, sources=[],
                                  root=__import__("pathlib").Path("/private"),
                                  ask=lambda *_a, **_k: None)
        recorded = []
        def call(system, prompt, *, image_paths, max_tokens):
            recorded.append(image_paths)
            raise RuntimeError("Stop after first call")
        with self.assertRaisesRegex(RuntimeError, "Stop after first call"):
            staged_concept_review(
                research={"research_mode":"verified_no_website"},
                order={"A":{},"B":{},"C":{}}, views=views, sources=[],
                root=__import__("pathlib").Path("/private"), ask=call)
        self.assertEqual(len(recorded[0]), 4)


if __name__ == "__main__":
    unittest.main()

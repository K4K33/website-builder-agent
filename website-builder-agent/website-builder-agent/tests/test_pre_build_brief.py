import io
from pathlib import Path
import unittest

from utils.pre_build_brief import (
    PROTOCOL, derive_pre_build_brief, ensure_pre_build_brief, validate_pre_build_brief,
)

ROOT = Path(__file__).resolve().parents[1]


def research(images=(), links=(), refs=2, journeys=True, contact=True, name="Esimerkki Oy"):
    return {
        "company_facts": {"name": name, "services": ["Rivitalot"],
                          "contact": {"phone": "010 123 4567" if contact else "",
                                      "email": "", "address": ""}},
        "primary_offering_evidence": {"quote": "Rakennamme rivitaloja puusta."},
        "source_inventory": {"pages": [{
            "url": "https://example.fi/",
            "images": [{"src": s, "alt": ""} for s in images],
            "links": [{"href": h, "text": ""} for h in links],
        }]},
        "creative_directions": [{"id": "a", "concept": "Rauhallinen puu",
                                 "first_view": "Elementti nousee paikalleen",
                                 "business_reason": "Asiakas näkee rakentamistavan",
                                 "typography": "Kapea groteski"}],
        "creative_selection": {"selected_id": "a"},
        "reference_comparison": [{"url": f"https://ref{i}.fi/"} for i in range(refs)],
        "primary_user_journeys": ([{"kind": "phone", "destination": "tel:+3581012345",
                                    "label": "Soita", "source_url": "https://example.fi/"}]
                                  if journeys else []),
    }


class PreBuildBriefTests(unittest.TestCase):
    def test_all_six_questions_answered(self):
        brief = derive_pre_build_brief(research(images=["/a.jpg", "/b.jpg", "/c.jpg"]))
        self.assertEqual(brief["protocol"], PROTOCOL)
        self.assertEqual(brief["gaps"], [])
        for key in ("q1_signature_moment", "q2_assets", "q3_brand_feel",
                    "q4_primary_action", "q5_performance", "q6_verified_facts"):
            self.assertTrue(brief[key])
        self.assertEqual(brief["q1_signature_moment"]["moment"], "Elementti nousee paikalleen")
        self.assertEqual(brief["q4_primary_action"]["href"], "tel:+3581012345")
        self.assertTrue(brief["q6_verified_facts"]["primary_offering_quote"])
        self.assertIs(brief["q2_assets"]["generation_allowed"], False)

    def test_technique_follows_real_material(self):
        cases = (
            ((), (), "typographic_statement"),
            (("/hero.jpg",), (), "cinematic_photo_scroll"),
            (("/1.jpg", "/2.webp", "/3.png"), (), "photo_sequence_scrub"),
            (("/1.jpg",), ("/esittely.mp4",), "video_scrub"),
            (("/1.jpg",), ("/tuote.glb",), "product_3d"),
            (("/logo.png", "/icon-phone.png", "/facebook.jpg"), (), "typographic_statement"),
        )
        for images, links, technique in cases:
            with self.subTest(technique=technique, images=images):
                brief = derive_pre_build_brief(research(images=images, links=links))
                self.assertEqual(brief["q1_signature_moment"]["technique"], technique)

    def test_procedural_3d_is_forbidden_in_every_brief(self):
        brief = derive_pre_build_brief(research())
        self.assertTrue(any("procedural" in rule for rule in brief["q1_signature_moment"]["forbidden"]))

    def test_staged_media_decides_usable_technique(self):
        data = research(images=["/1.jpg", "/2.jpg", "/3.jpg"])
        self.assertEqual(derive_pre_build_brief(data, staged_media=[])["q1_signature_moment"]["technique"],
                         "typographic_statement")
        staged = [{"src": "assets/a.jpg"}]
        self.assertEqual(derive_pre_build_brief(data, staged_media=staged)["q1_signature_moment"]["technique"],
                         "cinematic_photo_scroll")

    def test_gaps_block_before_any_page_is_authored(self):
        for kwargs, gap in (({"refs": 1}, "q3_brand_feel"),
                            ({"journeys": False, "contact": False}, "q4_primary_action"),
                            ({"name": ""}, "q6_verified_facts")):
            with self.subTest(gap=gap):
                data = research(**kwargs)
                with self.assertRaisesRegex(RuntimeError, "PRE_BUILD_BRIEF_INCOMPLETE: .*" + gap):
                    ensure_pre_build_brief(data)
                self.assertIn(gap, data["pre_build_brief"]["gaps"])

    def test_benchmark_records_count_as_references(self):
        data = research(refs=0)
        data["design_benchmark"] = [{"url": "https://a.fi/"}, {"url": "https://b.fi/"}]
        self.assertEqual(derive_pre_build_brief(data)["gaps"], [])

    def test_phone_from_facts_when_no_journey(self):
        brief = derive_pre_build_brief(research(journeys=False))
        self.assertEqual(brief["q4_primary_action"]["href"], "tel:0101234567")

    def test_missing_brief_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, "missing"):
            validate_pre_build_brief({})

    def test_pipeline_wiring(self):
        research_src = (ROOT / "agents/research.py").read_text(encoding="utf-8")
        self.assertEqual(research_src.count('research_data["pre_build_brief"] = derive_pre_build_brief'), 2)
        concept_src = (ROOT / "utils/concept_workflow.py").read_text(encoding="utf-8")
        self.assertIn("ensure_pre_build_brief(research, media)", concept_src)
        builder_src = (ROOT / "agents/builder.py").read_text(encoding="utf-8")
        self.assertEqual(builder_src.count("ensure_pre_build_brief(research, media_manifest)"), 2)

    def test_queue_classifies_gap(self):
        from scripts.run_kaurivo_demo_queue import classify_stage_failure
        log = io.StringIO("Traceback\nRuntimeError: PRE_BUILD_BRIEF_INCOMPLETE: q4_primary_action\n")
        self.assertEqual(classify_stage_failure(log, "concepting"), "pre_build_brief_incomplete")


if __name__ == "__main__":
    unittest.main()

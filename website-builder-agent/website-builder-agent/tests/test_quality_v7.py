"""V7 general-purpose design guards, not an invented aesthetic scoring tool."""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from utils.quality_v7 import (
    V7_POLICY, V7_SHA256, source_passport,
    design_brief, visual_risks, reference_candidates,
)
from utils.visual_revision import decide_revision


def html(body: str, styles: str = "") -> str:
    return (f'<!doctype html><html lang="fi"><head>'
            f'<meta name="viewport" content="width=device-width">'
            f'<title>Actual Business | Verified Service</title>'
            f'<style>body{{margin:0;font:16px Arial;background:#fff;color:#111}}'
            f'{styles}</style></head><body><header><nav><a href="#main">Home</a>'
            f'</nav></header><main id="main">{body}</main>'
            f'<footer>Verified contact</footer></body></html>')


class V7QualityContractTests(unittest.TestCase):
    def test_canonical_runtime_policy_is_loaded_in_all_relevant_stages(self):
        from utils.service_quality import POLICY, MASTER_PROMPT_SHA256
        self.assertIn("KAURIVO MASTER V7", V7_POLICY)
        self.assertIn(V7_POLICY, POLICY)
        self.assertEqual(len(V7_SHA256), 64)
        self.assertEqual(len(MASTER_PROMPT_SHA256), 64)
        # A V7 change invalidates prior research / review hashes.
        self.assertNotEqual(V7_SHA256, MASTER_PROMPT_SHA256)

    def test_reference_candidates_are_real_international_ideas_never_approved(self):
        for sector in ("autohuolto", "hammasklinikka", "asianajotoimisto",
                       "ravintola", "siivouspalvelu"):
            with self.subTest(sector=sector):
                result = reference_candidates(sector)
                self.assertTrue(result)
                self.assertTrue(all(x["status"] == "CANDIDATE_REQUIRES_REAL_BROWSER_CAPTURE"
                                    and x["copy_assets_or_layout"] is False for x in result))
                self.assertTrue(all(x["url"].startswith("https://") for x in result))
        self.assertEqual(reference_candidates("completely unclassified industry"), [])

    def test_media_passport_retains_actual_sources_but_never_forges_rights(self):
        research = {
            "company_facts": {"name": "Real Repair Oy", "industry": "autohuolto"},
            "source_inventory": {"pages": [{
                "url": "https://repair.example/",
                "source_identity": {"original_content_photos": [
                    {"src": "https://repair.example/mechanic.jpg",
                     "alt": "Actual technician at work"}
                ]}
            }]},
        }
        passport = source_passport(research, {"url": "https://repair.example/"})
        self.assertEqual(passport["available_source_photo_count"], 1)
        self.assertEqual(passport["photos"][0]["rights_status"], "PENDING_EXPLICIT_PERMISSION")
        self.assertEqual(passport["photos"][0]["observed_subject"], "Actual technician at work")
        brief = design_brief(research, {"url": "https://repair.example/"})
        self.assertEqual(brief["business"], "Real Repair Oy")
        self.assertTrue(brief["reference_discovery_candidates_only"])
        self.assertTrue(brief["quality_not_self_certified"])

    def test_no_site_does_not_mean_no_existing_brand(self):
        p = source_passport({"research_mode": "verified_no_website",
                             "company_facts": {"name": "Painter Oy"}},
                            {"name": "Painter Oy"})
        self.assertTrue(p["no_site_does_not_mean_no_brand"])
        self.assertTrue(any("social" in issue for issue in p["missing_evidence"]))
        self.assertTrue(p["rights_are_not_auto_granted"])

    def test_decorative_fake_map_is_blocked_when_presented_as_location(self):
        page = html(
            '<section class="location-card"><div class="location-grid"></div>'
            '<div class="location-pin"></div>'
            '<p>Keskitie 12, Helsinki</p></section>'
        )
        result = visual_risks({"index.html": page})
        self.assertEqual(result["status"], "HOLD")
        self.assertEqual(result["blocking"][0]["code"], "faux_geographic_map")

    def test_illustrative_engine_and_oversized_numbers_are_not_assumed_premium(self):
        page = html(
            '<section><img src="assets/engine-technical.svg" alt="schematic">'
            '<span class="story-number">20+</span>'
            '<span class="service-number">01</span></section>',
            'h1{letter-spacing:-.11em}'
        )
        result = visual_risks({"index.html": page})
        self.assertFalse(result["blocking"])
        codes = [x["code"] for x in result["review_required"]]
        self.assertIn("decorative_number_rhythm", codes)
        self.assertIn("schematic_over_real_photo", codes)
        self.assertIn("extreme_negative_letterspacing", codes)
        self.assertTrue(result["human_visual_review_still_required"])

    def test_staged_repair_receives_exact_v7_hard_failure(self):
        qa = {
            "overall_pass": False,
            "content_review": {},
            "visual_comparison": {"status": "paired_for_human_review"},
            "v7_visual_risks": {
                "blocking": [{"code": "faux_geographic_map",
                              "repair": "Replace synthetic street with verified directions."}]
            },
        }
        verdict = decide_revision(qa)
        self.assertTrue(verdict["revise"], verdict)
        self.assertIn("faux_geographic_map", str(verdict["feedback"]["actionable_defects"]))

    def test_browser_catches_rasanen_style_70px_long_paragraph(self):
        from utils.browser_qa import inspect_site
        prose = "Aitoon huoltoon kuuluva tarkastus ja huoltotyö. " * 8
        page = html(
            '<section class="service-row"><div><h2>Huolto</h2><p>' + prose +
            '</p></div><aside>Pyydä aika</aside></section>',
            '.service-row{display:grid;grid-template-columns:70px 1fr 180px;gap:40px}'
            '@media(max-width:760px){.service-row{grid-template-columns:1fr}}'
        )
        with TemporaryDirectory() as d:
            p = Path(d) / "index.html"
            p.write_text(page, encoding="utf-8")
            result = inspect_site(p)
        self.assertFalse(result["pass"])
        self.assertTrue(any("unreadable substantial text column" in s
                            for s in result["issues"]), result["issues"])

    def test_normal_wide_readable_paragraph_does_not_fail_column_gate(self):
        from utils.browser_qa import inspect_site
        prose = "Aitoon huoltoon kuuluva tarkastus ja huoltotyö. " * 8
        page = html(
            '<section class="service-row"><div><h2>Huolto</h2><p>' + prose +
            '</p></div><aside>Pyydä aika</aside></section>',
            '.service-row{display:grid;grid-template-columns:minmax(0,1fr) 180px;gap:30px}'
            '@media(max-width:760px){.service-row{grid-template-columns:1fr}}'
        )
        with TemporaryDirectory() as d:
            p = Path(d) / "index.html"
            p.write_text(page, encoding="utf-8")
            result = inspect_site(p)
        self.assertFalse(any("unreadable substantial text column" in s
                             for s in result["issues"]), result["issues"])


if __name__ == "__main__":
    unittest.main()

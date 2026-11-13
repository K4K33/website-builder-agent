"""Prismarit and RE MY SOUL fallbacks must not block reliable cloud research.

Real websites in source pools are candidate URLs only; live crawling, exact
quotes and visual checks still decide whether they qualify as references.
No external web/AI calls from this regression suite.
"""
from __future__ import annotations
from pathlib import Path
from tempfile import TemporaryDirectory
import json
import unittest
from unittest.mock import patch
from utils.free_references import (
    normalize_industry, CURATED_REFERENCE_CANDIDATES,
    discover_free_references, verified_sector_search_hint,
)
from utils.kaurivo_ai_source_packet import (
    observed_source_excerpts, pack_research_source_excerpts,
)

ROOT=Path(__file__).resolve().parents[1]
SOURCE=(ROOT/"agents/research.py").read_text(encoding="utf-8")


class SectorReferenceTests(unittest.TestCase):
    def test_niche_surveys_resolve_to_one_shared_sector(self):
        for industry in (
            "Laserkeilaus", "Rakennusmittaukset", "Maanmittaus",
            "Teollisuusmittaus", "Mittauspalvelut",
            "Teollisuuden mittaukset ja 3D-laserkeilaus",
            "Industrial surveying", "Construction surveying",
            "teollisuuden rakennusmittaus ja 3d-mittaukset",
        ):
            with self.subTest(industry=industry):
                self.assertEqual(normalize_industry(industry),"mittauspalvelut")

    def test_unknown_registration_sector_needs_two_original_service_signals(self):
        self.assertEqual(verified_sector_search_hint(
            "Muu rakennustekninen palvelu",
            "Teemme laserkeilausta ja rakennusmittauksia. Mittauspalvelut "
            "teollisuuteen ja infrakohteisiin."), "mittauspalvelut")
        self.assertEqual(verified_sector_search_hint(
            "Rakennustekninen suunnittelu",
            "We design architecture and also mention laserkeilaus once."),
            "Rakennustekninen suunnittelu")
        self.assertEqual(verified_sector_search_hint(
            "Asianajotoimisto", "Rakennusmittaus laserkeilaus mittauspalvelut"),
            "asianajotoimisto")
        self.assertEqual(verified_sector_search_hint(
            "Muu rakennustekninen palvelu", ""),
            "Muu rakennustekninen palvelu")

    def test_seven_real_sector_candidate_urls_never_count_as_proved_sources(self):
        pool=CURATED_REFERENCE_CANDIDATES["mittauspalvelut"]
        self.assertGreaterEqual(len(pool),7)
        hosts={p.split("/")[2] for _,p in pool}
        self.assertEqual(len(hosts),len(pool))
        self.assertNotIn("www.prismarit.fi",hosts)
        with TemporaryDirectory() as tmp:
            with patch("utils.free_references.historical_verified_references",return_value=[]):
                rows=discover_free_references(
                    "Laserkeilaus",target_url="https://www.prismarit.fi/",
                    cache_path=Path(tmp)/"cache.json",
                    max_results=20,
                    fetch_osm=lambda *args:[],
                    historic_lookup=lambda _:[],
                )
        self.assertGreaterEqual(len(rows),7)
        self.assertTrue(all("url" in row and "same_industry" not in row
                            for row in rows))

    def test_research_does_not_skip_final_exact_source_gates(self):
        self.assertIn('if len(candidates) < 3:',SOURCE)
        self.assertIn('verified_evidence_quote(source, match)',SOURCE)
        self.assertIn('if len(selected) < 3:',SOURCE)
        self.assertIn('len(reference_evidence) == 3',SOURCE)
        self.assertIn('validate_design_plan(research_data, url)',SOURCE)
        self.assertIn('validate_source_plan(research_data, source_url=url)',SOURCE)
        self.assertIn('validate_brand_preservation_plan(research_data)',SOURCE)


class SourcePacketTests(unittest.TestCase):
    def test_none_list_and_dict_block_shapes_normalize_without_type_error(self):
        cases=[
            {"url":"https://source.example.org/","title":None,
             "headings":{"h1":["Home"],"h2":["Menu"]},
             "text":None,"source_content_blocks":["Item A","Item B"],
             "header_assets":None,"footer_assets":None},
            {"url":"https://source.example.org/services","title":"Services",
             "headings":["Original",4,None],
             "text":"Observed source text of services.",
             "source_content_blocks":{"blocks":[{"text":"Observed block"}]}},
            {"url":"https://source.example.org/contact","title":"Contact",
             "headings":None,
             "text":{"not":"a string"},
             "source_content_blocks":"unexpected"},
        ]
        old=json.loads(json.dumps(cases))
        excerpts=observed_source_excerpts(cases)
        self.assertEqual(cases,old,"source observations must not be mutated")
        self.assertEqual(len(excerpts),3)
        self.assertEqual(excerpts[0]["source_block_samples"],["Item A","Item B"])
        self.assertEqual(excerpts[1]["source_block_samples"],[{"text":"Observed block"}])
        self.assertEqual(excerpts[0]["text"],"")
        self.assertEqual(excerpts[2]["text"],"")
        packed=pack_research_source_excerpts(excerpts)
        self.assertEqual(len(packed),3)
        self.assertEqual(packed[0]["headings"][:2],["Home","Menu"])
        self.assertTrue(all(row["url"] in [e["url"] for e in cases] for row in packed))
        json.dumps(packed)

    def test_missing_original_url_is_fail_closed(self):
        with self.assertRaisesRegex(ValueError,"missing URL"):
            observed_source_excerpts([{"title":"No evidence"}])
        with self.assertRaisesRegex(ValueError,"pages missing"):
            observed_source_excerpts([])
        with self.assertRaisesRegex(ValueError,"page without source URL"):
            pack_research_source_excerpts([{"not":"a page"}])

    def test_full_site_evidence_is_not_replaced_by_compact_packet(self):
        self.assertIn('observed_source_excerpts(source_inventory["pages"])',SOURCE)
        self.assertIn("source_inventory=source_inventory",SOURCE)
        self.assertIn('original_experience_profile=original_experience_profile',SOURCE)
        self.assertIn('source_excerpts = pack_research_source_excerpts(source_excerpts)',SOURCE)


if __name__=="__main__":
    unittest.main()

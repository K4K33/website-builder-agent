"""Free benchmark discovery: source-backed, no invented competitors or quotes.

Synthetic sites and mocked AI only. Does not fetch a live customer, consume
free model credits, scrape a search engine or weaken the three-operator QA.
"""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import Mock, patch
import unittest

from agents import research
from utils.free_references import (
    BENCHMARK_REGIONS, CURATED_REFERENCE_CANDIDATES, DEFAULT_REGIONS,
    normalize_industry, preferred_benchmark_regions, discover_free_references,
)
from utils.reference_quote_evidence import observed_quote_options, verified_evidence_quote

CLIENT="https://client-verified.example.org"
OPERATORS=[
    "https://cafe-alpha.example.org/",
    "https://cafe-beta.example.org/",
    "https://cafe-gamma.example.org/",
    "https://cafe-delta.example.org/",
]
SOURCES=[
    "Cafe Alpha welcomes guests in our cafe. We serve espresso, cakes and sandwiches in Helsinki. "
    "We have a kitchen serving weekday lunches and coffee all afternoon.",
    "Cafe Beta operates a neighbourhood coffee shop. Our menu includes breakfast, deli salads and "
    "freshly baked bread, served every day at our cafe.",
    "Cafe Gamma is a cafe with hot drinks and fresh pastries. We offer savoury ciabatta sandwiches "
    "and seasonal salads for customers visiting for lunch.",
    "Cafe Delta has a specialty coffee counter. The cafe serves breakfast plates and light lunches "
    "including sandwiches, cakes and tea.",
]


class SourceAndMunicipalityTests(unittest.TestCase):
    def test_original_helsinki_appears_first_but_no_city_is_fabricated(self):
        self.assertEqual(DEFAULT_REGIONS[0], "Helsinki")
        self.assertEqual(preferred_benchmark_regions(
            {"industry":"kahvila"},
            "Cafe Java, Mannerheimintie 22-24, 00100 Helsinki."), 
            ("Helsinki", "Tampere", "Turku", "Oulu"))
        self.assertEqual(preferred_benchmark_regions(
            {"city":"Jyväskylä","industry":"kahvila"},
            "Unrelated body mentions Helsinki." )[0], "Jyväskylä")
        self.assertEqual(preferred_benchmark_regions({}, "no city known"), DEFAULT_REGIONS)
        self.assertNotIn("Utopia", BENCHMARK_REGIONS)

    def test_cafe_industry_has_real_candidate_sources_not_automatic_proof(self):
        self.assertEqual(normalize_industry("kahvilapalvelut"),"kahvila")
        self.assertEqual(normalize_industry("Helsingin coffee shop"),"kahvila")
        sources=CURATED_REFERENCE_CANDIDATES["kahvila"]
        self.assertGreaterEqual(len(sources),5)
        self.assertEqual(len({url.split("/")[2] for _,url in sources}),len(sources))
        self.assertNotIn("https://www.cafejava.fi/",{url for _,url in sources})
        with TemporaryDirectory() as tmp:
            def no_public_queries(*_): return []
            found=discover_free_references(
                "kahvila", target_url="https://www.cafejava.fi",
                cache_path=Path(tmp)/"refs.json",regions=("Helsinki","Turku"),
                max_results=20,fetch_osm=no_public_queries,
                historic_lookup=lambda _:[])
        self.assertGreaterEqual(len(found),5)
        self.assertTrue(all(not x.get("same_industry") for x in found))

    def test_quote_ids_refer_only_to_exact_original_text(self):
        for source in SOURCES:
            options=observed_quote_options(source)
            self.assertTrue(options)
            self.assertTrue(all(item["text"] in source for item in options))
            self.assertEqual(len({q["quote_id"] for q in options}),len(options))
        candidate={"site_text":SOURCES[0],
                   "quote_options":observed_quote_options(SOURCES[0])}
        quoted=verified_evidence_quote(candidate,{"quote_id":"q0"})
        self.assertTrue(quoted and quoted in SOURCES[0])
        self.assertEqual(verified_evidence_quote(candidate,{"quote_id":"q77"}),"")
        self.assertEqual(verified_evidence_quote(candidate,{"evidence_quote":"Made up quote"}),"")
        self.assertEqual(verified_evidence_quote(candidate,{"evidence_quote":SOURCES[0][5:58]}),
                         SOURCES[0][5:58])


class VerifiedSelectionTests(unittest.TestCase):
    def _candidate(self,url):
        from utils.quality import canonical_url
        index=[canonical_url(value) for value in OPERATORS].index(canonical_url(url))
        return {"success":True,"title":"Operator "+str(index),
                "visible_text":SOURCES[index]}

    def test_three_distinct_operators_with_real_source_quote_ids(self):
        def model(system,user_prompt,**kw):
            import json
            # JSON payload can contain free model content, but only source
            # bound quote ids returned here pass the actual source validator.
            obj=json.loads(user_prompt.split("INSPECTED PRIMARY-SOURCE CANDIDATES:\n",1)[1])
            return {"selected":[
                {"url":site["url"],"same_industry":True,"reason":"Observed cafe food and service",
                 "quote_id":site["source_exact_quote_ids"][0]["quote_id"]}
                for site in obj[:3]
            ]}
        with patch("agents.research.cached_analyze",side_effect=lambda url, fn:self._candidate(url)), \
             patch("agents.research.ask_claude_json",side_effect=model) as ai, \
             patch("agents.research.config.free_only",return_value=True):
            chosen=research._select_reference_candidates(
                [{"url":x} for x in OPERATORS],
                {"industry":"kahvila","services":["coffee","salads"]},CLIENT)
        self.assertEqual(len(chosen),3)
        ai.assert_called_once()
        self.assertTrue(all(c["industry_match"]["evidence_quote"] in c["site_text"]
                            for c in chosen))
        self.assertEqual(len({c["url"] for c in chosen}),3)
        self.assertTrue(all("quote_options" not in c for c in chosen))

    def test_first_under_selection_gets_only_one_evidence_checked_repair(self):
        counts=[]
        def model(system,prompt,**kw):
            import json
            options=json.loads(prompt.split("INSPECTED PRIMARY-SOURCE CANDIDATES:\n",1)[1])
            counts.append(len(options))
            amount=1 if len(counts)==1 else 3
            return {"selected":[
                {"url":s["url"],"same_industry":True,
                 "reason":"Real cafe tasks, evidenced by original site",
                 "quote_id":s["source_exact_quote_ids"][0]["quote_id"]}
                for s in options[:amount]]}
        with patch("agents.research.cached_analyze",side_effect=lambda url,fn:self._candidate(url)), \
             patch("agents.research.ask_claude_json",side_effect=model) as ai, \
             patch("agents.research.config.free_only",return_value=True):
            result=research._select_reference_candidates(
                [{"url":x} for x in OPERATORS],{"industry":"kahvila"},CLIENT)
        self.assertEqual(len(result),4)
        self.assertEqual(ai.call_count,2)
        self.assertEqual(counts,[4,3])
        self.assertTrue(all(x["industry_match"]["evidence_quote"] in x["site_text"]
                            for x in result))

    def test_fake_or_cross_site_quote_id_can_never_fill_required_three(self):
        def fake(system,prompt,**kw):
            import json
            options=json.loads(prompt.split("INSPECTED PRIMARY-SOURCE CANDIDATES:\n",1)[1])
            return {"selected":[
                {"url":site["url"],"same_industry":True,"reason":"Alleged same sector",
                 "quote_id":"unknown-quote","evidence_quote":"AI fabricated coffee menu"}
                for site in options]}
        with patch("agents.research.cached_analyze",side_effect=lambda url,fn:self._candidate(url)), \
             patch("agents.research.ask_claude_json",side_effect=fake) as ai, \
             patch("agents.research.config.free_only",return_value=True):
            with self.assertRaisesRegex(RuntimeError,"Fewer than three source-backed"):
                research._select_reference_candidates(
                    [{"url":x} for x in OPERATORS],{"industry":"kahvila"},CLIENT)
        self.assertEqual(ai.call_count,2)

    def test_no_extra_ai_when_fewer_than_three_inspectable_sites(self):
        with patch("agents.research.cached_analyze",side_effect=lambda url,fn:
                   self._candidate(url) if url in OPERATORS[:2] else {"success":False}), \
             patch("agents.research.ask_claude_json") as ai, \
             patch("agents.research.config.free_only",return_value=True):
            with self.assertRaisesRegex(RuntimeError,"Fewer than three inspectable"):
                research._select_reference_candidates(
                    [{"url":x} for x in OPERATORS],{"industry":"kahvila"},CLIENT)
        ai.assert_not_called()


if __name__=="__main__":
    unittest.main()

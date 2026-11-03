"""Kaurivo optional website intelligence: zero-external-call regression tests."""
from datetime import date
import os
from unittest.mock import patch
import json
from pathlib import Path
import tempfile
import unittest

from utils.kaurivo_website_research import (
    enrich, plausible_url, rank_search_candidate, search_once, MAX_QUERIES_PER_RUN,
)

ROOT=Path(__file__).resolve().parents[1]

def candidate(i=12,name="Espoon Lukkohuolto Oy"):
    return {"name":name,"business_id":f"{i:07d}-{i%10}",
            "website_listed_url":"","industry_code_hint":"47529",
            "city_hint":"Espoo"}

class FakeResponse:
    def __init__(self, results, code=200):
        self.status_code=code
        self.results=results
    def raise_for_status(self):
        if self.status_code>=400:
            raise RuntimeError("HTTP not OK")
    def json(self):return {"results":self.results}

class WebsiteResearchTests(unittest.TestCase):
    def test_verified_free_plan_uses_atomic_server_budget_before_search(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"packet.json"
            path.write_text(json.dumps({
                "schema":"kaurivo_prh_shortlist_v1", "mode":"pilot-live",
                "candidates":[candidate()]}), encoding="utf-8")
            from unittest.mock import patch
            import os
            with patch.dict(os.environ, {
                    "FREE_ONLY":"1", "KAURIVO_TAVILY_FREE_PLAN_CONFIRMED":"1"}), \
                 patch("utils.kaurivo_website_research.search_once",
                       return_value=({"url":"https://espoonlukkohuolto.fi/"}, False)) as called:
                result=enrich(path,key="free-account-fixture",
                              claim=lambda: False)
                self.assertEqual(result["searched"],0)
                called.assert_not_called()
                result=enrich(path,key="free-account-fixture",
                              claim=lambda: True)
                self.assertEqual(result["searched"],1)
                called.assert_called_once()

    def test_free_only_blocks_even_a_configured_paid_search_key(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"packet.json"
            path.write_text(json.dumps({
                "schema":"kaurivo_prh_shortlist_v1","mode":"pilot-live",
                "candidates":[candidate()]}),encoding="utf-8")
            before=path.read_bytes()
            with patch.dict(os.environ, {"FREE_ONLY": "1", "AI_BACKEND": "ollama"}):
                result=enrich(path,key="a-real-key-would-go-here",
                              post=lambda *args,**kwargs: self.fail("No paid search"),
                              claim=lambda: self.fail("No credit reservation"))
                self.assertEqual(result["credits_budgeted"],0)
                self.assertEqual(result["searched"],0)
                self.assertFalse(result["enabled"])
                with self.assertRaisesRegex(RuntimeError,"FREE_ONLY"):
                    search_once(candidate(),key="mock",
                                post=lambda *args,**kwargs: self.fail("No paid search"))
            self.assertEqual(path.read_bytes(),before)

    def test_provider_is_off_without_key_and_spends_nothing(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"packet.json"
            path.write_text(json.dumps({
               "schema":"kaurivo_prh_shortlist_v1","mode":"pilot-live",
               "candidates":[candidate()]}),encoding="utf-8")
            original=path.read_bytes()
            result=enrich(path,key="",post=lambda *args,**kwargs:
                self.fail("No-key mode must never call a provider"))
            self.assertEqual(result["searched"],0)
            self.assertEqual(path.read_bytes(),original)

    def test_only_high_confidence_business_websites_appear_as_suggestions(self):
        company=candidate()
        search_results=[
          {"url":"https://finder.fi/123","title":"Espoon Lukkohuolto Oy"},
          {"url":"https://www.espoonlukkohuolto.fi/","title":"Espoon Lukkohuolto Oy | Lukkopalvelut",
           "content":"Espoon Lukkohuolto Oy"},
          {"url":"https://example.fi/","title":"Joku eri yritys"}
        ]
        result=rank_search_candidate(company,search_results)
        self.assertEqual(result["url"],"https://www.espoonlukkohuolto.fi/")
        self.assertEqual(result["source"],"tavily_search")
        self.assertGreaterEqual(result["confidence"],80)
        self.assertIsNone(rank_search_candidate(company,[{"url":"https://other.fi/",
            "title":"Espoon kilpailijat","content":"lukkohuoltopalveluita"}]))
        self.assertIsNone(rank_search_candidate(company,[{
            "url":"https://facebook.com/espoonlukkohuolto","title":"Espoon Lukkohuolto Oy"}]))
        self.assertIsNone(rank_search_candidate(company,[{
            "url":"https://paikallisuutiset.fi/yritykset/espoon-lukkohuolto",
            "title":"Espoon Lukkohuolto Oy uudisti liiketilansa",
            "content":"Espoon Lukkohuolto Oy on esimerkki paikallisesta yrityksestä"}]))

    def test_url_safety_and_no_ssrf_verification_fetch(self):
        for url in ("javascript:alert(1)","file:///etc/passwd","https://localhost/","http://127.0.0.1/x",
                    "https://finance.google.com/foo","https://www.ytj.fi/y",
                    "https://user:pw@firm.fi/", "https://123.45.67.8/private"):
            self.assertFalse(plausible_url(url),url)
        self.assertEqual(plausible_url("https://hyvayritys.fi/#home"),"https://hyvayritys.fi/")

    @patch.dict(os.environ, {"FREE_ONLY": "0", "AI_BACKEND": "openrouter"})
    def test_provider_call_is_one_basic_api_request(self):
        called=[]
        def post(url,**kwargs):
            called.append((url,kwargs))
            return FakeResponse([{"url":"https://espoonlukkohuolto.fi/",
                "title":"Espoon Lukkohuolto Oy","content":"Lukkopalvelu Espoo"}])
        suggestion,stop=search_once(candidate(),key="fake-token",post=post)
        self.assertFalse(stop)
        self.assertTrue(suggestion)
        self.assertEqual(len(called),1)
        self.assertEqual(called[0][1]["json"]["search_depth"],"basic")
        self.assertEqual(called[0][1]["json"]["include_images"],False)
        self.assertEqual(called[0][1]["headers"]["Authorization"],"Bearer fake-token")

    @patch.dict(os.environ, {"FREE_ONLY": "0", "AI_BACKEND": "openrouter"})
    def test_quota_cap_and_stop_on_429(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"packet.json"
            packet={"schema":"kaurivo_prh_shortlist_v1","mode":"pilot-live",
                    "candidates":[candidate(i, f"Lukkohuolto Espoo {i} Oy") for i in range(1,51)]}
            path.write_text(json.dumps(packet),encoding="utf-8")
            calls=[]
            def provider(url,**kw):
                calls.append(kw)
                return FakeResponse([],200)
            result=enrich(path,key="mock",max_queries=500,post=provider,claim=lambda:True)
            self.assertEqual(result["searched"],MAX_QUERIES_PER_RUN)
            self.assertEqual(len(calls),MAX_QUERIES_PER_RUN)
            packet2=json.loads(path.read_text())
            self.assertFalse(any("website_search_candidate" in c for c in packet2["candidates"]))
            calls.clear()
            def blocked(url,**kw):
                calls.append(kw)
                return FakeResponse([],429)
            result=enrich(path,key="mock",post=blocked,claim=lambda:True)
            self.assertEqual(result["searched"],1)
            self.assertEqual(len(calls),1)


    @patch.dict(os.environ, {"FREE_ONLY": "0", "AI_BACKEND": "openrouter"})
    def test_optional_search_requires_real_server_quota_reservation(self):
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/"packet.json"
            path.write_text(json.dumps({
                "schema":"kaurivo_prh_shortlist_v1","mode":"pilot-live",
                "candidates":[candidate()]}),encoding="utf-8")
            def no_provider(*args,**kwargs):
                self.fail("External search must not run without a quota claim.")
            result=enrich(path,key="mock",post=no_provider)
            self.assertEqual(result["searched"],0)
            self.assertFalse(result["enabled"])
            result=enrich(path,key="mock",post=no_provider,claim=lambda:False)
            self.assertEqual(result["searched"],0)
            self.assertEqual(result["credits_budgeted"],0)

    def test_pipeline_and_frontend_are_consistent(self):
        workflow=(ROOT.parents[1]/".github/workflows/kaurivo-national-prh.yml").read_text()
        ingest=(ROOT/"docs/kaurivo/backend/prh_ingest_edge.ts").read_text()
        admin=(ROOT/"docs/kaurivo/assets/crm.js").read_text()
        self.assertIn("secrets.KAURIVO_TAVILY_API_KEY", workflow)
        self.assertIn("vars.KAURIVO_TAVILY_FREE_PLAN_CONFIRMED", workflow)
        self.assertIn("FREE_ONLY: \"1\"", workflow)
        self.assertIn("--max-queries 12",workflow)
        self.assertIn("website_candidate_url:candidate",ingest)
        self.assertIn("website_verified:false",ingest)
        self.assertIn("Hakukoneen ehdotus",admin)
        self.assertIn("data.website_verified=false",admin)

if __name__=="__main__":
    unittest.main()

"""Strict, reproducible independent-reputation sourcing tests (no network)."""
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
from unittest.mock import patch
import unittest

from utils.kaurivo_reputation_research import (
    _aggregate_candidates, _company_identity_matches, _find_source,
    _platform, _source_snapshot, enrich_reputation
)

COMPANY={"name":"Premium Firma Oy","city_hint":"Joensuu",
    "website_listed_url":"https://premiumfirma.fi/",
    "site_technical_audit":{"status":"html_checked","url":"https://premiumfirma.fi/"},
    "website_audit_checked_at":"2026-11-18T09:00:00Z"}
SOURCE="https://fi.trustpilot.com/review/premiumfirma.fi"

def sample_html(stars="4.3", reviews="34"):
    data={"@context":"https://schema.org","@type":"Organization",
        "name":"Premium Firma Oy","aggregateRating":{
            "@type":"AggregateRating","ratingValue":stars,
            "reviewCount":reviews,"bestRating":"5"}}
    return ('<html><head><title>Premium Firma Oy - Trustpilot</title></head>'
            '<body><script type="application/ld+json">'
            +json.dumps(data)+'</script></body></html>').encode()

class FakeReviewPage:
    status_code=200
    headers={"Content-Type":"text/html;charset=utf-8"}
    encoding="utf-8"
    def __init__(self,html=None,status=200):
        self.data=html or sample_html()
        self.status_code=status
    def __enter__(self):return self
    def __exit__(self,*args):pass
    def iter_content(self,chunk_size=None):yield self.data

class FakeSearchResponse:
    status_code=200
    def raise_for_status(self):pass
    def json(self):
        return {"results":[{"url":SOURCE,"title":"Premium Firma Oy arvostelut",
                            "content":"4.3/5, 34 reviews"}]}

class ReputationScreeningTests(unittest.TestCase):
    def test_direct_4star_aggregate_and_10_review_minimum(self):
        for stars,count,accepted in [
            ("4.0","10",True),("4.8","210",True),
            ("3.99","100",False),("5.0","9",False)
        ]:
            with self.subTest(stars=stars,count=count):
                got=_source_snapshot(COMPANY,SOURCE,get=lambda *a,**k:
                    FakeReviewPage(sample_html(stars,count)))
                self.assertEqual(bool(got),accepted)
                if got:
                    self.assertEqual(got["method"],
                                     "direct_public_review_page_structured_rating")
                    self.assertGreaterEqual(got["review_count"],10)

    def test_results_snippet_never_proves_rating(self):
        result=_find_source(COMPANY,[
            {"url":SOURCE,"title":"Premium Firma Oy arvostelut",
             "content":"5 / 5 -- 999 reviews"}],
            get=lambda *a,**k: FakeReviewPage(
                b"<html><title>Test</title><body>5/5 and 999 reviews</body></html>"))
        self.assertIsNone(result)

    def test_no_google_or_wrong_company_review_attribution(self):
        self.assertEqual(_platform("https://www.google.com/maps/place/Firma"),"")
        self.assertEqual(_platform("https://trustpilot.com.evil.example/review/premiumfirma.fi"),"")
        self.assertFalse(_company_identity_matches(COMPANY,
              "https://fi.trustpilot.com/review/other.fi"))
        called=[]
        result=_find_source(COMPANY,[
            {"url":"https://www.google.com/maps/place/Premium+Firma","title":"5 stars"},
            {"url":"https://fi.trustpilot.com/review/other.fi","title":"Premium Firma Oy"},
        ],get=lambda *a,**k:called.append(1))
        self.assertIsNone(result)
        self.assertEqual(called,[])

    def test_login_or_nonpublic_review_page_not_qualified(self):
        self.assertIsNone(_source_snapshot(COMPANY,SOURCE,
              get=lambda *a,**k:FakeReviewPage(status=403)))

    def test_live_packet_one_free_credit_and_no_personal_reviews(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"crm-shortlist.json"
            path.write_text(json.dumps({"schema":"kaurivo_prh_shortlist_v1",
                "mode":"pilot-live","date":"2026-11-18",
                "candidates":[dict(COMPANY)]}),encoding="utf-8")
            claimed=[]
            with patch("utils.kaurivo_reputation_research.config.tavily_free_plan_confirmed",
                       return_value=True):
                result=enrich_reputation(
                    path,key="test_free_key",claim=lambda:claimed.append(1) or True,
                    post=lambda *a,**k: FakeSearchResponse(),
                    get=lambda *a,**k: FakeReviewPage(),
                    max_queries=8)
            self.assertEqual(result["searched"],1)
            self.assertEqual(result["qualified"],1)
            self.assertEqual(len(claimed),1)
            stored=json.loads(path.read_text())["candidates"][0]["reputation_evidence"]
            self.assertEqual(stored["rating"],4.3)
            self.assertNotIn("review_text",stored)
            self.assertNotIn("reviewer",stored)

    def test_no_approved_free_plan_means_zero_external_requests(self):
        with tempfile.TemporaryDirectory() as folder:
            path=Path(folder)/"crm-shortlist.json"
            path.write_text(json.dumps({"schema":"kaurivo_prh_shortlist_v1",
                "mode":"pilot-live","candidates":[dict(COMPANY)]}))
            with patch("utils.kaurivo_reputation_research.config.tavily_free_plan_confirmed",
                       return_value=False):
                result=enrich_reputation(path,key="available_but_not_approved",
                    claim=lambda:self.fail("No credit may be claimed"),
                    post=lambda *a,**k:self.fail("No search may be made"))
            self.assertFalse(result["enabled"])
            self.assertEqual(result["searched"],0)

if __name__=="__main__":
    unittest.main()

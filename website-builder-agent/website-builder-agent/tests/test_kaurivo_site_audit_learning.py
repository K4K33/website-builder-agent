"""Offline Kaurivo prospect audit, language, cache and cautious feedback tests."""
from datetime import datetime, timezone, timedelta, date
import json
from pathlib import Path
import tempfile
import unittest

from utils.kaurivo_site_audit import (
    safe_homepage, inspect_site, extract_html_signals, audit_packet,
)
from utils.kaurivo_lead_quality import choose_shortlist
from utils.kaurivo_feedback_priors import get_weights

ROOT=Path(__file__).resolve().parents[1]
WORKFLOW=ROOT.parents[1]/".github/workflows/kaurivo-national-prh.yml"

def public_dns(host,port,type=None):
    return [(2,1,6,"",("93.184.215.14",port))]

def private_dns(host,port,type=None):
    return [(2,1,6,"",("10.0.0.1",port))]

class FakeSite:
    encoding="utf-8"
    headers={"Content-Type":"text/html; charset=utf-8"}
    status_code=200
    def __enter__(self):return self
    def __exit__(self,*args):return None
    def iter_content(self,chunk_size=None):
        yield b'<html lang="sv"><head><title>Riktig webbsida</title><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="description" content="Vi erbjuder professionella transporttjanster till alla."></head><body><h1>Vi hjalper dig</h1><a href="/kontakt/">Kontakt</a></body></html>'

class SiteLearningTests(unittest.TestCase):
    def test_ssrf_protections_no_fetch_private_addresses(self):
        self.assertFalse(safe_homepage("http://company.fi/",resolve=public_dns))
        self.assertFalse(safe_homepage("https://private.fi:8443/",resolve=public_dns))
        self.assertFalse(safe_homepage("https://admin:pass@firm.fi/",resolve=public_dns))
        self.assertFalse(safe_homepage("https://firm.fi/",resolve=private_dns))
        self.assertEqual(safe_homepage("https://firm.fi/listing?q=secret#anchor",
            resolve=public_dns),"https://firm.fi/")
        def never_get(*args,**kwargs):self.fail("SSRF candidate reached network")
        self.assertEqual(inspect_site("https://firm.fi/",get=never_get,
            resolve=private_dns)["status"],"unsafe_or_unresolvable_url")

    def test_html_checks_annotate_not_declare_broken_design(self):
        result=inspect_site("https://firm.fi/",get=lambda *a,**k:FakeSite(),
            resolve=public_dns)
        self.assertEqual(result["status"],"html_checked")
        self.assertEqual(result["html_language_hint"],"sv")
        self.assertEqual(result["issues"],[])
        html='<html><head></head><body><p>Example</p></body></html>'
        result=extract_html_signals(html,"https://firm.fi/")
        self.assertIn("viewport_missing",result["issues"])
        self.assertIn("contact_link_missing",result["issues"])
        self.assertEqual(result["html_language_hint"],"undetermined")

    def test_packet_cache_reuses_results_without_http(self):
        with tempfile.TemporaryDirectory() as temp:
            packet=Path(temp)/"shortlist.json";cache=Path(temp)/"cache.json"
            packet.write_text(json.dumps({"schema":"kaurivo_prh_shortlist_v1",
                 "mode":"pilot-live","candidates":[{"name":"Test Oy",
                 "business_id":"1234567-8",
                 "website_listed_url":"https://firm.fi/"}]}),encoding="utf-8")
            calls=[]
            def get(*args,**kwargs):
                calls.append(args);return FakeSite()
            now=datetime(2026,11,1,tzinfo=timezone.utc)
            r=audit_packet(packet,cache,get=get,resolve=public_dns,now=now)
            self.assertEqual(r["checked"],1)
            self.assertEqual(len(calls),1)
            r=audit_packet(packet,cache,get=lambda *a,**k:self.fail("Reused site must be cached"),
              resolve=public_dns,now=now+timedelta(days=7))
            self.assertEqual(r["checked"],0)
            self.assertEqual(r["cache_hits"],1)
            r=audit_packet(packet,cache,get=get,resolve=public_dns,
               now=now+timedelta(days=31))
            self.assertEqual(r["checked"],1)
            self.assertEqual(len(calls),2)

    def test_human_feedback_prior_requires_eight_reviews(self):
        leads=[{"name":f"Palveluyritys {i} Oy",
                "business_id":f"{i:07d}-{i%10}",
                "industry_code_hint":("43220" if i%2 else "47529"),
                "website_listed_url":"https://firm.fi/" if i%3 else ""}
               for i in range(1,28)]
        neutral=choose_shortlist(leads,size=15,day="2026-11-01")
        ignored=choose_shortlist(leads,size=15,day="2026-11-01",
          weights={"43":{"boost":4,"count":2}})
        self.assertEqual([x["business_id"] for x in neutral],
                         [x["business_id"] for x in ignored])
        weighed=choose_shortlist(leads,size=15,day="2026-11-01",
          weights={"43":{"boost":4,"count":9}})
        self.assertEqual(len(weighed),15)
        self.assertTrue(any(x["industry_code_hint"].startswith("43") for x in weighed))

    def test_no_oidc_is_zero_credit_no_network(self):
        result=get_weights(env={},get=lambda *_a,**_k:self.fail("unexpected call"),
          post=lambda *_a,**_k:self.fail("unexpected call"))
        self.assertEqual(result,{})

    def test_flow_integrates_and_does_not_auto_email(self):
        yaml=WORKFLOW.read_text()
        js=(ROOT/"docs/kaurivo/assets/crm.js").read_text()
        ingest=(ROOT/"docs/kaurivo/backend/prh_ingest_edge.ts").read_text()
        self.assertIn("--max-candidates 9000",yaml)
        self.assertIn("--max-checks 12",yaml)
        self.assertIn("kaurivo_site_audit_cache.json",yaml)
        self.assertIn("kaurivo_feedback_priors",yaml)
        self.assertIn("website_technical_audit:technicalAudit",ingest)
        self.assertIn('id="lead-view"',(ROOT/"docs/kaurivo/admin/index.html").read_text())
        self.assertIn("Alustava tutkimusjärjestys",js)
        self.assertIn('screening_feedback',js)
        self.assertIn("client_won",js)

if __name__=="__main__":
    unittest.main()

"""Kaurivo operational reliability and legal review gates.

Only offline fixtures and local browser mocks; no PRH, AI, email or
Supabase network consumption.
"""
from pathlib import Path
import os
import unittest

ROOT=Path(__file__).resolve().parents[1]
HTML=ROOT/"docs/kaurivo/admin/index.html"
JS=ROOT/"docs/kaurivo/assets/crm.js"
INGEST=ROOT/"docs/kaurivo/backend/prh_ingest_edge.ts"
PUSH=ROOT/"docs/kaurivo/backend/daily_push_edge.ts"
MANUAL=ROOT/"docs/kaurivo/backend/manual_scan_edge.ts"
YAML=ROOT.parents[1]/".github/workflows/kaurivo-national-prh.yml"


class OperationsTests(unittest.TestCase):
    def test_daily_status_from_actual_telemetry_not_invented(self):
        html=HTML.read_text()
        js=JS.read_text()
        self.assertIn('id="ops-health"',html)
        self.assertIn('id="ops-brief"',html)
        self.assertIn('id="lead-pulse"',html)
        self.assertIn("kaurivo_pipeline_events",js)
        self.assertIn('event_day",selectedDay',js)
        self.assertIn("Ei vielä vahvistettua yöajoa",js)
        self.assertIn("Ei vahvistettua tapahtumaa",js)
        for code in (INGEST,PUSH,MANUAL):
            self.assertIn("kaurivo_pipeline_events",code.read_text())
        self.assertIn("utils.kaurivo_report_failure",YAML.read_text())

    def test_quality_requires_real_evidence_and_never_sends_outreach(self):
        js=JS.read_text()
        for flag in ("website_assessment","business_activity_assessment",
                     "customer_need","payment_signal","evidence_url","demo_brief",
                     "outreach_review","marketing_opt_out","leadEvidenceScore",
                     "draftDemoBrief"):
            self.assertIn(flag,js)
        self.assertIn("data.outreach_review=\"blocked\"",js)
        self.assertIn("data.outreach_stage=\"opted_out\"",js)
        self.assertIn("data.website_verified=false",js)
        self.assertIn("outreach_review===\"human_approved\"",js)
        self.assertIn("EI JULKAISTU",js)
        self.assertNotIn("sendMarketingEmail(",js)

    def test_mobile_admin_renders_true_status_and_review_fields_offline(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            if os.getenv("REQUIRE_BROWSER_TESTS")=="1":self.fail("Playwright unavailable")
            self.skipTest("Playwright unavailable")
        mock=r"""
const account={id:"admin",email:"hello.kaurivo@gmail.com",
 email_confirmed_at:"2026-10-31T00:00:00Z"};
const company={id:"p1",business_id:"1234567-8",company_name:"Korjauspalvelu Oy",
 city_hint:"Espoo",industry_code_hint:"43320",website_listed_url:"",
 website_found_url:"",website_candidate_url:"",research_notes:"",
 discovery_date:"2026-10-31",review_status:"unverified",
 website_assessment:"unreviewed",business_activity_assessment:"unreviewed",
 payment_signal:"unknown",customer_need:"unknown",evidence_url:"",
 demo_stage:"not_started",demo_brief:"",outreach_review:"not_reviewed",
 outreach_stage:"not_contacted",marketing_opt_out:false};
window.__updates=[];
const dayRecords={
 "kaurivo_crm_prospects":[company],
 "kaurivo_pipeline_events":[{
  id:5,event_day:"2026-10-31",component:"national_search",
  outcome:"success",details:"PRH valmis",records:1,notifications:0,
  created_at:"2026-10-31T06:11:00Z"}]
};
function dbTable(name){
 let pending={};
 return {
  select(){return this;},eq(field,val){pending[field]=val;return this;},
  order(){return this;},
  limit:async()=>({data:dayRecords[name]||[],error:null}),
  update(data){window.__updates.push(data);return this;}
 };
}
window.supabase={createClient:()=>({
 auth:{
  getUser:async()=>({data:{user:account},error:null}),
  onAuthStateChange:()=>({data:{subscription:{unsubscribe(){}}}}),
  getSession:async()=>({data:{session:null}})
 },
 from:dbTable
})};
window.__fakeCompany=company;
"""
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True,args=["--disable-gpu"])
            try:
                page=browser.new_page(viewport={"width":375,"height":844})
                errors=[]
                page.on("pageerror",lambda err:errors.append(str(err)))
                page.add_init_script(mock)
                page.route("https://cdn.jsdelivr.net/**",lambda route:route.abort())
                page.route("https://fonts.googleapis.com/**",lambda route:route.abort())
                page.goto(HTML.as_uri(),wait_until="domcontentloaded")
                page.locator("#prospect-day").fill("2026-10-31")
                page.locator("#prospect-day").dispatch_event("change")
                page.wait_for_function("document.querySelector('#ops-brief').textContent.includes('Yöhaku vahvistettu')")
                self.assertTrue(page.locator("#lead-pulse").is_visible())
                self.assertIn("Tutkimusprioriteetti: tiedot tarkistamatta",
                              page.locator("#prospect-list").inner_text())
                page.locator("#prospect-list button").last.click()
                self.assertTrue(page.locator("#editor").is_visible())
                self.assertTrue(page.locator("#field-marketing_opt_out").is_visible())
                self.assertEqual(page.locator("#field-website_assessment").input_value(),"unreviewed")
                self.assertFalse(errors,errors)
                page.close()
            finally:browser.close()


if __name__=="__main__":
    unittest.main()

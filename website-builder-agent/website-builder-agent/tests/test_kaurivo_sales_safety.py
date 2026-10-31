"""Kaurivo cross-day KPI & opt-out UI: mock-only tests, no PRH/AI/email credits."""
import os
from pathlib import Path
import unittest

SITE=Path(__file__).resolve().parents[1]/"docs/kaurivo"
HTML=SITE/"admin/index.html"
JS=SITE/"assets/crm.js"

class KaurivoSalesSafetyTests(unittest.TestCase):
    def test_source_exposes_lawful_business_pipeline_controls(self):
        html=HTML.read_text(encoding="utf-8")
        js=JS.read_text(encoding="utf-8")
        for phrase in ('id="sales-dashboard"','id="sales-overview-kpis"',
                       'id="sales-overview-bars"','id="suppression-form"',
                       'id="suppress-business-id"','id="add-suppression"'):
            self.assertIn(phrase,html)
        for code in ('db.rpc("kaurivo_get_sales_dashboard")',
                     'db.from("kaurivo_marketing_suppressions").insert',
                     '"direct_marketing_objection"',
                     'confirm("Vahvista yrityksen "', 'await refreshSalesMetrics()'):
            self.assertIn(code,js)
        self.assertNotIn('service_role',html)
        self.assertNotIn('sb_secret_',js)

    def test_verified_global_metrics_and_business_id_suppression(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            if os.getenv("REQUIRE_BROWSER_TESTS")=="1":
                self.fail("Playwright unavailable")
            self.skipTest("Playwright unavailable")
        fake=r"""
window.__suppressed=[];
const user={id:'test-admin',email:'hello.kaurivo@gmail.com',
 email_confirmed_at:'2026-10-31T00:00:00Z'};
window.supabase={createClient:()=>({
 auth:{
  getUser:async()=>({data:{user},error:null}),
  onAuthStateChange:()=>({data:{subscription:{unsubscribe:()=>{}}}})
 },
 rpc:async(name)=> name==='kaurivo_get_sales_dashboard'
  ? {data:{discovered:50,reviewed:5,excluded:17,site_links:4,
      suggested_sites:1,demo_briefs:2,demo_reviewed:1,legal_approved:0,
      contacted:0,responses:0,wins:0,won_eur:0,opted_out:0,
      daily:[{day:'2026-10-31',new_leads:50}]},error:null}
  : {data:null,error:{message:'unsupported test RPC'}},
 from:(name)=>({
  select(){return this;},
  eq(){return this;},
  order(){return this;},
  limit:async()=>({data:[],error:null}),
  insert:async(data)=>{window.__suppressed.push({name,data});return {error:null}}
 })
})};
window.confirm=()=>true;
"""
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True,args=['--disable-gpu'])
            try:
                for width in (375,1280):
                    page=browser.new_page(viewport={'width':width,'height':840})
                    errs=[]
                    page.on('pageerror',lambda err:errs.append(str(err)))
                    page.add_init_script(fake)
                    page.route('https://cdn.jsdelivr.net/**',lambda r:r.abort())
                    page.route('https://fonts.googleapis.com/**',lambda r:r.abort())
                    page.goto(HTML.as_uri(),wait_until='domcontentloaded')
                    page.wait_for_function("document.querySelector('#m-clients').textContent==='0'")
                    page.locator('#sales-dashboard summary').click()
                    page.wait_for_function("document.querySelector('#sales-overview-kpis').textContent.includes('50')")
                    self.assertIn('50',page.locator('#sales-overview-kpis').inner_text())
                    self.assertIn('Vahvistettu kauppa',page.locator('#sales-overview-kpis').inner_text())
                    self.assertTrue(page.locator('#sales-overview-bars').is_visible())
                    page.locator('.morning-details summary').click()
                    page.locator('#suppress-business-id').fill('1234567-8')
                    page.locator('#add-suppression').click()
                    page.wait_for_function('window.__suppressed.length===1')
                    self.assertEqual(page.evaluate('window.__suppressed[0].data.business_id'),'1234567-8')
                    self.assertIn('markkinointikielto',page.locator('#suppression-note').inner_text())
                    self.assertFalse(errs,errs)
                    overflow=page.evaluate(
                      'Math.max(document.body.scrollWidth,document.documentElement.scrollWidth)-innerWidth')
                    self.assertLessEqual(overflow,2,(width,overflow))
                    page.close()
            finally:
                browser.close()

if __name__=="__main__":
    unittest.main()

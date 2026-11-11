"""Real Chromium checks for the private admin's old/new comparison links.

No CRM credentials, Supabase calls or customer traffic. All jobs are synthetic.
"""
from __future__ import annotations
from pathlib import Path
import unittest
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
SCRIPT=(ROOT/"docs/kaurivo/assets/demo-jobs.js").read_text(encoding="utf-8")
CSS=(ROOT/"docs/kaurivo/assets/crm.css").read_text(encoding="utf-8")
PREVIEW="https://kaurivo-auto-demos-2026.onrender.com/example-123/index.html"
OLD="https://www.example.org/yritys/"
LOG="https://github.com/K4K33/website-builder-agent/actions/runs/43026585059"
SHA="a"*40


class ComparisonLinksBrowserTests(unittest.TestCase):
    def setUp(self):
        self.playwright=sync_playwright().start()
        self.browser=self.playwright.chromium.launch(headless=True)

    def tearDown(self):
        self.browser.close()
        self.playwright.stop()

    def page(self,width=1440):
        page=self.browser.new_page(viewport={"width":width,"height":900})
        page.set_content("""<!doctype html><html lang="fi"><head><meta name="viewport"
            content="width=device-width,initial-scale=1"></head><body>
            <div id="demo-health"></div><div id="demo-summary"></div>
            <div id="demo-ready-list"></div>
            <div id="demo-running-list"></div>
            <div id="demo-hold-list"></div>
            </body></html>""")
        page.add_style_tag(content=CSS)
        page.add_script_tag(content=SCRIPT)
        return page

    def render(self,page,jobs):
        page.evaluate("items => window.KaurivoDemoJobs.render(items, null, {})", jobs)

    def job(self,status="internal_preview", old=OLD, preview=PREVIEW):
        return {
            "id":"demo-test-1", "status":status,"company_name":"Esimerkki Oy",
            "business_id":"1111111-1","created_at":"2026-11-11T12:00:00Z",
            "original_url":old,"preview_url":preview,"qa_url":LOG,
            "release_sha":SHA,
            "progress":"Valmis", "prospect_id":"aabbccdd-aaaa-4aaa-8aaa-123456789abc",
        }

    def test_ready_demo_has_two_distinct_real_clickable_urls_and_copy_action(self):
        page=self.page()
        try:
            self.render(page,[self.job()])
            links=page.locator("#demo-ready-list .demo-comparison-link")
            self.assertEqual(links.count(),2)
            self.assertEqual(page.locator("#demo-ready-list .demo-handover").count(),1)
            page.locator("#demo-ready-list .demo-handover summary").click()
            self.assertIn("Testaa asiakkaan omilla oikeuksilla",page.locator("#demo-ready-list .demo-handover").inner_text())
            self.assertEqual(links.nth(0).inner_text(),"Vanha sivu")
            self.assertEqual(links.nth(0).get_attribute("href"),OLD)
            self.assertEqual(links.nth(1).inner_text(),"Uusi sivu")
            self.assertEqual(links.nth(1).get_attribute("href"),PREVIEW)
            self.assertEqual(links.nth(0).get_attribute("target"),"_blank")
            self.assertIn("noopener",links.nth(1).get_attribute("rel"))
            self.assertIn("example.org",page.locator(".demo-comparison-address").nth(0).inner_text())
            self.assertIn("onrender.com",page.locator(".demo-comparison-address").nth(1).inner_text())
            page.evaluate("""() => {
                Object.defineProperty(navigator, "clipboard", {configurable: true,
                value: {writeText: async text => {window.__copied=text}}});
            }""")
            page.get_by_role("button",name="Kopioi molemmat linkit").click()
            page.wait_for_function("Boolean(window.__copied)")
            self.assertEqual(page.evaluate("window.__copied"),
                             "Esimerkki Oy\nVanha sivu: "+OLD+"\nUusi sivu: "+PREVIEW)
        finally:
            page.close()

    def test_pending_qa_and_failed_jobs_never_receive_fabricated_new_link(self):
        page=self.page()
        try:
            jobs=[self.job(status="queued"),self.job(status="qa"),
                  self.job(status="hold")]
            for index, job in enumerate(jobs):
                job["id"]="demo-"+str(index)
                job["company_name"]="Esimerkki "+str(index)
            self.render(page,jobs)
            self.assertEqual(page.locator(".demo-comparison-link").count(),3)
            self.assertEqual(page.locator(".demo-comparison-empty").count(),3)
            self.assertEqual(page.get_by_role("button",name="Kopioi molemmat linkit").count(),0)
            self.assertEqual(page.locator("#demo-ready-list .demo-record").count(),0)
            self.assertEqual(page.locator("#demo-running-list .demo-record").count(),2)
            self.assertEqual(page.locator("#demo-hold-list .demo-record").count(),1)
        finally:
            page.close()

    def test_queued_dispatch_failure_is_not_mislabelled_as_running(self):
        page=self.page(width=390)
        try:
            job=self.job(status="queued")
            job["dispatch_error_code"]="github_token_not_configured"
            job["dispatch_checked_at"]="2026-11-11T19:45:13Z"
            self.render(page,[job])
            self.assertIn("Käynnistys estynyt",
                          page.locator("#demo-running-list").inner_text())
            self.assertIn("KAURIVO_GITHUB_DISPATCH_TOKEN",
                          page.locator("#demo-running-list").inner_text())
            self.assertEqual(page.locator(".demo-comparison-link").count(),1)
            self.assertEqual(page.locator(".demo-comparison-empty").count(),1)
        finally:
            page.close()

    def test_sent_to_github_is_not_labelled_as_started(self):
        page=self.page()
        try:
            job=self.job(status="queued")
            job["dispatch_accepted_at"]="2026-11-11T19:45:13Z"
            self.render(page,[job])
            self.assertIn("Käynnistys lähetetty",
                          page.locator("#demo-running-list").inner_text())
            self.assertNotIn("Rakenteilla",
                             page.locator("#demo-running-list .tag").inner_text())
        finally:
            page.close()

    def test_no_previous_website_has_explicit_empty_state_not_fake_url(self):
        page=self.page()
        try:
            self.render(page,[self.job(old="")])
            self.assertEqual(page.locator(".demo-comparison-link").count(),1)
            self.assertEqual(page.locator(".demo-comparison-link").first.inner_text(),"Uusi sivu")
            self.assertIn("Ei aiempaa verkkosivua",
                          page.locator(".demo-comparison-empty").first.inner_text())
        finally:
            page.close()

    def test_bad_preview_url_or_missing_qa_proof_cannot_appear_as_new(self):
        page=self.page()
        try:
            for url,qa in [
                ("https://malicious.example/demo",LOG),
                (PREVIEW,"https://not-github.example/log"),
                ("http://kaurivo-auto-demos-2026.onrender.com/demo",LOG),
            ]:
                job=self.job(preview=url)
                job["qa_url"]=qa
                self.render(page,[job])
                self.assertEqual(page.locator(".demo-comparison-link").count(),1)
                self.assertEqual(page.locator(".demo-comparison-empty").count(),1)
        finally:
            page.close()

    def test_mobile_cards_stack_link_pair_without_horizontal_overflow(self):
        for width in (320,390,768,1440):
            with self.subTest(width=width):
                page=self.page(width)
                try:
                    self.render(page,[self.job()])
                    links=page.locator(".demo-comparison-link")
                    self.assertEqual(links.count(),2)
                    self.assertFalse(page.evaluate(
                        "document.documentElement.scrollWidth > window.innerWidth + 2"))
                    rects=links.evaluate_all("""els => els.map(el=>{
                        const r=el.getBoundingClientRect();
                        return {w:r.width,h:r.height,x:r.x,right:r.right};
                    })""")
                    self.assertTrue(all(r["h"]>=40 and r["w"]>0
                                        and r["right"]<=width+2 for r in rects))
                finally:
                    page.close()


if __name__=="__main__":
    unittest.main()

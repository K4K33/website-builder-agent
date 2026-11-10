"""Regression tests: Kaurivo admin one-click demo queue.

No real customers, Supabase RPCs, GitHub Actions dispatch, Render calls or AI
requests occur during these tests. Synthetic browser mocks are isolated.
"""
from __future__ import annotations
from pathlib import Path
import os
import unittest

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/"docs/kaurivo"
HTML=SITE/"admin/index.html"
CRM=SITE/"assets/crm.js"
DASHBOARD=SITE/"assets/demo-jobs.js"
CSS=SITE/"assets/crm.css"
MIGRATION=SITE/"backend/demo_jobs_migration.sql"
EDGE=SITE/"backend/demo_worker_edge.ts"
WORKER=ROOT/"scripts/run_kaurivo_demo_queue.py"
FLOW=ROOT.parents[1]/".github/workflows/kaurivo-demo-worker.yml"


class DemoQueueSourceSafetyTests(unittest.TestCase):
    def test_admin_ui_has_real_build_button_and_separate_demo_panel(self):
        html=HTML.read_text(encoding="utf-8")
        js=CRM.read_text(encoding="utf-8")
        panel=DASHBOARD.read_text(encoding="utf-8")
        self.assertIn('id="tab-demos"',html)
        self.assertIn('id="demo-ready-list"',html)
        self.assertIn('id="demo-running-list"',html)
        self.assertIn('id="demo-hold-list"',html)
        self.assertIn('data-tab="demos"',html)
        self.assertIn('data-mobile-tab="demos"',html)
        self.assertIn('demo-jobs.js?v=',html)
        self.assertLess(html.index("demo-jobs.js"),html.index("crm.js"))
        self.assertIn('Rakenna demo',js)
        self.assertIn('window.KaurivoDemoJobs.start',js)
        self.assertIn('kaurivo_demo_build_jobs',js)
        self.assertIn('kaurivo_request_demo_build',panel)
        self.assertIn('internal_preview',panel)
        self.assertIn('Avaa uusi demo',panel)
        self.assertIn('Vanha sivu',panel)
        self.assertIn('qa_url',panel)
        self.assertIn('release_sha',panel)
        self.assertIn('onrender',panel)
        self.assertIn('noindex,nofollow,noarchive',html)
        self.assertNotIn('service_role',js.lower())
        self.assertNotIn('sb_secret_',panel)
        self.assertNotIn('innerHTML',panel)
        self.assertNotIn('eval(',panel)
        self.assertIn('.demo-build-trigger',CSS.read_text(encoding="utf-8"))

    def test_prospect_selection_not_able_to_forge_completed_preview(self):
        sql=MIGRATION.read_text(encoding="utf-8")
        self.assertIn('enable row level security',sql)
        self.assertIn('revoke all on public.kaurivo_demo_build_jobs from anon, authenticated',sql)
        self.assertIn('grant select on public.kaurivo_demo_build_jobs to authenticated',sql)
        self.assertIn('kaurivo_internal.is_kaurivo_admin()',sql)
        self.assertIn('grant execute on function public.kaurivo_request_demo_build(uuid) to authenticated',sql)
        self.assertIn('for update skip locked limit 1',sql.lower())
        self.assertIn('github_run_id=p_run_id',sql)
        self.assertIn("p_status='internal_preview'",sql)
        self.assertIn("status <> 'internal_preview'",sql)
        self.assertIn('release_sha ~',sql)
        self.assertIn('daily free-build request cap reached',sql)
        self.assertNotIn('grant insert on public.kaurivo_demo_build_jobs to authenticated',sql.lower())
        self.assertNotIn('grant update on public.kaurivo_demo_build_jobs to authenticated',sql.lower())

    def test_edge_verifies_exact_repository_workflow_and_oidc(self):
        edge=EDGE.read_text(encoding="utf-8")
        flow=FLOW.read_text(encoding="utf-8")
        self.assertIn('jwtVerify(',edge)
        self.assertIn('RS256',edge)
        self.assertIn('repository_owner_id',edge)
        self.assertIn('repository_id',edge)
        self.assertIn('WORKFLOW_REF',edge)
        self.assertIn("payload.ref_type",edge)
        self.assertIn("payload.ref",edge)
        self.assertIn('kaurivo-demo-worker.yml@refs/heads/main',edge)
        self.assertIn('"schedule","workflow_dispatch","push"',edge)
        self.assertIn('push:',flow)
        self.assertIn('branches: [main]',flow)
        self.assertIn('".github/workflows/kaurivo-demo-worker.yml"',flow)
        self.assertIn('kaurivo_worker_claim_demo',edge)
        self.assertIn('kaurivo_worker_update_demo',edge)
        self.assertIn('id-token: write',flow)
        self.assertIn('run: python -m scripts.run_kaurivo_demo_queue',flow)
        self.assertNotIn('run: python scripts/run_kaurivo_demo_queue.py',flow)
        self.assertIn('contents: write',flow)
        self.assertIn('FREE_ONLY: "1"',flow)
        self.assertIn("google/gemma-4-31b-it:free",flow)
        self.assertIn("qwen/qwen3.8-27b:free",flow)
        self.assertIn("google/gemma-4-26b-a4b-it:free",flow)
        self.assertIn("Independent Builder and QA models:",flow)
        self.assertIn('cron: "*/5 * * * *"',flow)
        self.assertIn('KAURIVO_CLAIMED_JOB_FILE',flow)
        self.assertNotIn('SUPABASE_SERVICE_ROLE_KEY:',flow)
        self.assertNotIn('sb_secret_',edge)

    def test_worker_never_marks_unverified_site_ready_or_spends_paid_credits(self):
        worker=WORKER.read_text(encoding="utf-8")
        for key in ('research','concept-previews','choose-concept','build','qa',
                    'FREE_ONLY','BUILDER_MODEL','QA_MODEL',
                    'verify_public(', 'snapshot_for_preview(', 'local_browser_smoke(',
                    'exact_free_model_required','noindex,nofollow','internal_preview',
                    'remote_image_rights_not_proven'):
            self.assertIn(key,worker)
        self.assertIn('if qa.get("overall_pass") is True:',worker)
        self.assertIn('quality_gate_build_version_mismatch',worker)
        self.assertIn('data-kaurivo-release',worker)
        self.assertIn('auto/kaurivo-demos',worker)
        self.assertIn('kaurivo-auto-demos-2026.onrender.com',worker)
        self.assertNotIn('confirm-paid-apis',worker)
        self.assertIn('Kaurivo worker redacted error:',worker)
        self.assertIn('sys.path.insert(0,str(PROJECT))',worker)
        self.assertIn('traceback.extract_tb',worker)
        self.assertIn('worker_line',worker)
        self.assertNotIn('print(str(exc))',worker)

    def test_job_is_not_suddenly_approved_by_static_site_smoke(self):
        from scripts.run_kaurivo_demo_queue import (
            HoldError, free_model_configured
        )
        from unittest.mock import patch
        with patch.dict(os.environ,{"FREE_ONLY":"1","AI_BACKEND":"openrouter",
                    "OPENROUTER_API_KEY":"","BUILDER_MODEL":"","QA_MODEL":""}):
            with self.assertRaisesRegex(HoldError, 'free_ai_key_missing'):
                free_model_configured()
        with patch.dict(os.environ,{"FREE_ONLY":"0","AI_BACKEND":"openrouter"}):
            with self.assertRaisesRegex(HoldError,'paid_ai_disabled'):
                free_model_configured()

    def test_static_preview_copies_real_html_and_not_private_json_or_txt(self):
        from tempfile import TemporaryDirectory
        from scripts.run_kaurivo_demo_queue import (
            snapshot_for_preview, verify_static_site
        )
        site='<!doctype html><html lang="fi"><head><title>Yritys</title></head><body><main><h1>Palvelut</h1><p>Esimerkki</p></main></body></html>'
        with TemporaryDirectory() as td:
            root=Path(td)
            original=root/"source"
            (original/"palvelut").mkdir(parents=True)
            (original/"index.html").write_text(site,encoding="utf-8")
            (original/"palvelut/index.html").write_text(site,encoding="utf-8")
            (original/"research-notes.json").write_text('{"private":"never publish"}')
            (original/"client-contact.txt").write_text("Private contact data")
            (original/"assets").mkdir()
            (original/"assets/main.css").write_text("body{margin:0}")
            target=root/"preview"
            snapshot_for_preview(original,target,"kaurivo-test-unique")
            self.assertEqual(
                verify_static_site(target,["index.html","palvelut/index.html"]),
                ["index.html","palvelut/index.html"]
            )
            self.assertFalse((target/"research-notes.json").exists())
            self.assertFalse((target/"client-contact.txt").exists())
            self.assertTrue((target/"assets/main.css").is_file())
            rendered=(target/"index.html").read_text()
            self.assertIn('data-kaurivo-release="kaurivo-test-unique"',rendered)
            self.assertIn('content="noindex,nofollow"',rendered)
            self.assertIn('ei yrityksen virallinen sivu',rendered)

    def test_route_manifest_is_exact_including_flat_html_pages(self):
        from tempfile import TemporaryDirectory
        from scripts.run_kaurivo_demo_queue import (
            verify_static_site, HoldError
        )
        site='<!doctype html><html><head><meta name="robots" content="noindex"></head><body><main><h1>Hei</h1></main></body></html>'
        with TemporaryDirectory() as td:
            root=Path(td)
            (root/"index.html").write_text(site)
            (root/"palvelut.html").write_text(site)
            self.assertEqual(verify_static_site(root,["index.html","palvelut.html"]),
                             ["index.html","palvelut.html"])
            with self.assertRaisesRegex(HoldError,"site_route_manifest_mismatch"):
                verify_static_site(root,["index.html","puuttuu.html"])
            with self.assertRaisesRegex(HoldError,"site_route_manifest_mismatch"):
                verify_static_site(root,["index.html"])
            (root/"yhteystiedot.html").write_text(site)
            with self.assertRaisesRegex(HoldError,"site_route_manifest_mismatch"):
                verify_static_site(root,["index.html","palvelut.html"])

    def test_research_stage_error_classification_never_reveals_private_output(self):
        from tempfile import TemporaryFile
        from scripts.run_kaurivo_demo_queue import classify_stage_failure
        fixtures=[
            ("OpenRouter rejected request: HTTP 429","free_ai_rate_limit"),
            ("OpenRouter rejected request: HTTP 402","free_ai_account_blocked"),
            ("OpenRouter rejected request: HTTP 400","free_model_request_rejected"),
            ("ModuleNotFoundError: No module named 'missing'","missing_runtime_dependency"),
            ("source inventory missing required services","source_research_incomplete"),
            ("RuntimeError: website business details insufficient","researching_failed"),
        ]
        with TemporaryFile(mode="w+",encoding="utf-8") as log:
            log.write("Previous stage: OpenRouter rejected request: HTTP 429\n")
            for trace,reason in fixtures:
                log.seek(0,2)
                start=log.tell()
                log.write("Company contact example@example.fi\n"+trace+"\n")
                self.assertEqual(classify_stage_failure(log,"researching",start),reason)
            log.seek(0,2)
            start=log.tell()
            log.write("Unfamiliar runtime failure for private company\n")
            outcome=classify_stage_failure(log,"researching",start)
            self.assertEqual(outcome,"researching_failed")
            self.assertNotIn("company",outcome.lower())
            self.assertNotIn("@",outcome)

    def test_qa_feedback_is_specific_and_autorepair_stays_bounded(self):
        from scripts.run_kaurivo_demo_queue import (
            qa_repair_feedback, MAX_AUTO_REVISIONS, AI_STAGE_BUDGET_SECONDS
        )
        packet=qa_repair_feedback({
            "browser":{"issues":["Mobiilivalikko on rikki"]},
            "content_parity":{"missing":[{"label":"Alkuperäinen hinnasto"}]},
            "content_review":{"issues":["Pääkuvasta puuttuu logon oikea versio"]},
        })
        self.assertIn("Mobiilivalikko on rikki",packet)
        self.assertIn("Alkuperäinen hinnasto",packet)
        self.assertIn("logon oikea versio",packet)
        self.assertIn("UNTRUSTED",packet)
        self.assertIn("Never invent business details",packet)
        self.assertEqual(MAX_AUTO_REVISIONS,2)
        self.assertLessEqual(AI_STAGE_BUDGET_SECONDS,2400)
        worker=WORKER.read_text(encoding="utf-8")
        self.assertIn('run_cli(["revise",agent_slug,qa_repair_feedback(qa)]',worker)
        self.assertIn('for revision in range(MAX_AUTO_REVISIONS+1)',worker)
        self.assertIn('quality_gate_build_version_mismatch',worker)
        self.assertNotIn('while True:',worker)

    def test_demo_navigation_does_not_leave_company_preview(self):
        from scripts.run_kaurivo_demo_queue import checked_preview_link, HoldError
        base="https://kaurivo-auto-demos-2026.onrender.com/yritys-1234/"
        current=base+"index.html"
        self.assertEqual(checked_preview_link(
            "palvelut/index.html",current,base),base+"palvelut/index.html")
        self.assertEqual(checked_preview_link("#palvelut",current,base),current)
        self.assertIsNone(checked_preview_link("https://example.com/",current,base))
        self.assertIsNone(checked_preview_link("mailto:info@example.com",current,base))
        with self.assertRaisesRegex(HoldError,"dead_navigation_link"):
            checked_preview_link("#",current,base)
        with self.assertRaisesRegex(HoldError,"dead_navigation_link"):
            checked_preview_link("javascript:void(0)",current,base)
        with self.assertRaisesRegex(HoldError,"internal_link_escapes_preview"):
            checked_preview_link("/toinen-yritys/",current,base)
        with self.assertRaisesRegex(HoldError,"internal_link_escapes_preview"):
            checked_preview_link("//kaurivo-auto-demos-2026.onrender.com/admin",current,base)

    def test_duplicate_builder_and_qa_model_not_certified_as_independent(self):
        from scripts.run_kaurivo_demo_queue import free_model_configured,HoldError
        from unittest.mock import patch
        same="google/gemma-4-31b-it:free"
        with patch.dict(os.environ,{
           "FREE_ONLY":"1","AI_BACKEND":"openrouter",
           "OPENROUTER_API_KEY":"fake-for-local-testing-only",
           "BUILDER_MODEL":same,"QA_MODEL":same
        }):
           with self.assertRaisesRegex(HoldError,"independent_qa_model_required"):
               free_model_configured()
        with patch.dict(os.environ,{
           "FREE_ONLY":"1","AI_BACKEND":"openrouter",
           "OPENROUTER_API_KEY":"fake-for-local-testing-only",
           "BUILDER_MODEL":"google/gemma-4-31b-it:free",
           "QA_MODEL":"qwen/qwen3.8-27b:free"
        }):
           free_model_configured()

    def test_authenticated_browser_only_mock_job_is_real_rpc(self):
        if os.getenv("SKIP_BROWSER_TESTS")=="1":
            self.skipTest("Browser intentionally disabled")
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            if os.getenv("REQUIRE_BROWSER_TESTS")=="1":self.fail("Playwright unavailable")
            self.skipTest("Playwright unavailable")
        mock=r"""
        const lead={id:'e3a0f29a-4fa7-46e3-bc55-644792ac7460',
          business_id:'1234567-8',company_name:'Esimerkki Verhoomo',
          city_hint:'Helsinki',industry_code_hint:'95240',
          website_listed_url:'https://example.com/',website_found_url:'',
          website_candidate_url:'',research_notes:'',
          discovery_date:new Date().toISOString().slice(0,10),
          review_status:'needs_demo',website_assessment:'weak_evidence',
          business_activity_assessment:'active_evidence',
          payment_signal:'unknown',customer_need:'strong',
          evidence_url:'https://example.com/',demo_stage:'not_started',
          demo_brief:'',outreach_review:'not_reviewed',
          outreach_stage:'not_contacted',marketing_opt_out:false,
          website_languages:'fi',contact_language:'fi'};
        window.__rpcCalls=[];window.__demoRows=[];
        window.__insertQueue=()=>window.__demoRows=[{
           id:'4fab441f-b8a1-4b7e-af94-d813b8a232c0',
           prospect_id:lead.id,
           company_name:lead.company_name,business_id:lead.business_id,
           original_url:'https://example.com/',created_at:new Date().toISOString(),
           status:'queued',progress:'Jonossa' }];
        window.supabase={createClient:()=>({
          auth:{
            getUser:async()=>({data:{user:{
              id:'test',email:'hello.kaurivo@gmail.com',
              email_confirmed_at:'2026-11-10T00:00:00Z'}},error:null}),
            onAuthStateChange:()=>({data:{subscription:{unsubscribe:()=>{}}}}),
            signOut:async()=>({error:null})},
          from:(table)=>({
             select(){return this;},eq(){return this;},
             order(){return this;},limit:async()=>({
               data:table==='kaurivo_crm_prospects'?[lead]:
                    table==='kaurivo_demo_build_jobs'?window.__demoRows:[],
               error:null})
          }),
          rpc:async(name,args)=>{
             window.__rpcCalls.push({name,args});
             if(name==='kaurivo_request_demo_build'){
               window.__insertQueue();
               return {data:'4fab441f-b8a1-4b7e-af94-d813b8a232c0',error:null};
             }
             return {data:[],error:null};
          }
        })};
        """
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True,args=['--disable-gpu'])
            try:
                for width in (390,1440):
                    page=browser.new_page(viewport={"width":width,"height":900})
                    page.add_init_script(mock)
                    page.route("https://cdn.jsdelivr.net/**",lambda r:r.abort())
                    page.route("https://fonts.googleapis.com/**",lambda r:r.abort())
                    page.route("https://fonts.gstatic.com/**",lambda r:r.abort())
                    exceptions=[]
                    page.on("pageerror",lambda err:exceptions.append(str(err)))
                    page.goto(HTML.as_uri(),wait_until="domcontentloaded")
                    page.wait_for_function(
                        "document.querySelector('#prospect-list .record-title')?.textContent === 'Esimerkki Verhoomo'"
                    )
                    page.locator("#prospect-list .demo-build-trigger").click()
                    page.wait_for_function(
                        "document.querySelector('#demo-running-list').textContent.includes('Esimerkki Verhoomo')"
                    )
                    self.assertEqual(page.locator("#tab-demos").is_visible(),True)
                    self.assertEqual(page.locator("#demo-ready-list .demo-external").count(),0)
                    self.assertEqual(page.evaluate(
                        "window.__rpcCalls.filter(x=>x.name==='kaurivo_request_demo_build').length"
                    ),1)
                    page.evaluate("""()=>{
                      window.__demoRows[0].status='internal_preview';
                      window.__demoRows[0].preview_url='https://kaurivo-auto-demos-2026.onrender.com/test/index.html';
                      window.__demoRows[0].qa_url='https://github.com/K4K33/website-builder-agent/actions/runs/12345';
                      window.__demoRows[0].release_sha='a'.repeat(40);
                    }""")
                    page.locator("#refresh-demos").click()
                    page.wait_for_function(
                       "document.querySelector('#demo-ready-list').textContent.includes('Esimerkki Verhoomo')"
                    )
                    link=page.locator("#demo-ready-list a.demo-external[href*='onrender.com']")
                    self.assertEqual(link.count(),1)
                    self.assertEqual(link.get_attribute('target'),'_blank')
                    self.assertTrue(link.get_attribute('href').endswith('/test/index.html'))
                    self.assertEqual(exceptions,[],exceptions)
                    page.close()
            finally:
                browser.close()


if __name__=="__main__":
    unittest.main()

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
        self.assertIn('Uusi sivu',panel)
        self.assertIn('Vanha sivu',panel)
        self.assertIn('demo-handover',panel)
        self.assertIn('Asiakasluovutus',panel)
        self.assertIn('Luovutus tehdään vasta sopimuksen',panel)
        self.assertIn('Kopioi molemmat linkit',panel)
        self.assertIn('comparisonLinks(main,job,options)',panel)
        self.assertIn('Uusi sivu valmistuu laatutarkistuksen jälkeen',panel)
        self.assertIn('Ei aiempaa verkkosivua',panel)
        self.assertIn('demo-comparison',CSS.read_text(encoding="utf-8"))
        self.assertIn('crm.css?v=20261112-local1',html)
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
        self.assertNotIn('daily free-build request cap reached',sql)
        self.assertNotIn("company is skipped",sql)
        self.assertNotIn("company has opted out",sql)
        self.assertIn("kaurivo_request_demo_build",sql)
        self.assertIn("chosen_url := '';",sql)
        self.assertNotIn('grant insert on public.kaurivo_demo_build_jobs to authenticated',sql.lower())
        self.assertNotIn('grant update on public.kaurivo_demo_build_jobs to authenticated',sql.lower())

    def test_builder_health_pauses_execution_not_admin_queue(self):
        health=(SITE/"backend/demo_builder_health_migration.sql").read_text(encoding="utf-8")
        edge=EDGE.read_text(encoding="utf-8")
        flow=FLOW.read_text(encoding="utf-8")
        crm=CRM.read_text(encoding="utf-8")
        dashboard=DASHBOARD.read_text(encoding="utf-8")
        html=HTML.read_text(encoding="utf-8")
        for term in ("enable row level security",
                     "kaurivo_internal.is_kaurivo_admin()",
                     "grant select on public.kaurivo_demo_builder_health to authenticated",
                     "grant execute on function public.kaurivo_worker_record_health(bigint,integer)",
                     "create trigger kaurivo_demo_health_before_insert",
                     "when 401 then 'blocked'",
                     "when 200 then 'ok'",
                     "return new;"):
            self.assertIn(term,health)
        self.assertNotIn("grant insert on public.kaurivo_demo_builder_health to authenticated",health)
        self.assertIn('if(data.action==="health")',edge)
        self.assertIn("kaurivo_worker_record_health",edge)
        self.assertIn('key_http_status',edge)
        self.assertIn('key_http_status=',flow)
        self.assertIn("health-demo.json",flow)
        self.assertIn("key_http_status",flow)
        self.assertIn('if [[ "$KEY_STATUS" != "200" ]]',flow)
        self.assertIn("echo \"has_job=false\"",flow)
        self.assertIn("demoHealth",crm)
        self.assertIn("kaurivo_demo_builder_health",crm)
        self.assertIn('id="demo-health"',html)
        self.assertIn("healthBlocked",dashboard)
        self.assertIn("healthStale",dashboard)
        self.assertIn("demo-health-stale",dashboard)
        self.assertIn("demo_queue_stale_health_20261111.sql",(SITE/"backend/demo_queue_stale_health_20261111.sql").as_posix())
        self.assertIn("voit lisätä työn jonoon",dashboard)
        self.assertIn('return !item||item.status!=="ok";',dashboard)
        self.assertIn("demo-health-blocked",dashboard)
        self.assertIn("Rakentaja tauolla",dashboard)
        self.assertIn("Voit silti lisätä uuden demon jonoon",dashboard)
        self.assertNotIn('build.disabled=true;',crm)
        self.assertIn("Rakenna uudelleen",dashboard)
        self.assertIn("marketing_opt_out",crm)
        migration=(SITE/"backend/demo_owner_request_independent_20261111.sql").read_text(encoding="utf-8")
        self.assertIn("kaurivo_request_demo_build",migration)
        self.assertIn("kaurivo_demo_require_healthy_worker",migration)
        self.assertNotIn("company has opted out",migration)
        self.assertNotIn("daily free-build request cap reached",migration)

    def test_immediate_dispatch_is_admin_authenticated_and_not_public(self):
        js=DASHBOARD.read_text(encoding="utf-8")
        edge=(SITE/"backend/demo_immediate_dispatch_edge.ts").read_text(encoding="utf-8")
        sql=(SITE/"backend/demo_immediate_dispatch_20261111.sql").read_text(encoding="utf-8")
        html=HTML.read_text(encoding="utf-8")
        self.assertIn('functions.invoke("kaurivo-demo-dispatch"',js)
        self.assertIn('Rakenna uudelleen',js)
        self.assertIn('Käynnistä nyt',js)
        self.assertIn('GitHubin käynnistys',js)
        self.assertIn('getUser(auth.slice(7))',edge)
        self.assertIn('.from("kaurivo_demo_build_jobs")',edge)
        self.assertIn('select("id,status,runner_kind")',edge)
        self.assertIn('kaurivo_local_worker_wakeup',edge)
        self.assertIn('kaurivo_claim_demo_dispatch',edge)
        self.assertIn('KAURIVO_GITHUB_DISPATCH_TOKEN',edge)
        self.assertIn('x-client-info, x-region',edge)
        self.assertIn('github.com/repos/K4K33/website-builder-agent/actions/workflows/',edge)
        self.assertIn('github_token_not_configured',edge)
        self.assertIn('kaurivo_internal.is_kaurivo_admin()',sql)
        self.assertIn("90 seconds",sql)
        self.assertIn("revoke all on function public.kaurivo_claim_demo_dispatch(uuid) from public,anon",sql)
        self.assertNotIn('sb_secret_',js)
        self.assertNotIn('ghp_',js)
        self.assertIn('demo-jobs.js?v=20261112-verified-start3',html)

    def test_dispatch_failures_have_private_persistent_reason_and_real_response_body(self):
        panel=DASHBOARD.read_text(encoding="utf-8")
        edge=(SITE/"backend/demo_immediate_dispatch_edge.ts").read_text(encoding="utf-8")
        sql=(SITE/"backend/demo_dispatch_status_20261111.sql").read_text(encoding="utf-8")
        self.assertIn('error.context.json()',panel)
        self.assertIn('dispatch_error_code',panel)
        self.assertIn('dispatch_accepted_at',panel)
        self.assertIn('Käynnistys estynyt',panel)
        self.assertIn('KAURIVO_GITHUB_DISPATCH_TOKEN',panel)
        self.assertIn('reportDispatch("github_token_not_configured")',edge)
        self.assertIn('reportDispatch("",true)',edge)
        self.assertIn('reportDispatch("github_token_permissions")',edge)
        self.assertIn('kaurivo_report_demo_dispatch',edge)
        self.assertIn('kaurivo_internal.is_kaurivo_admin()',sql)
        self.assertIn('status=\'queued\'',sql)
        self.assertIn('dispatch_error_code',sql)
        self.assertIn('dispatch_accepted_at',sql)
        self.assertNotIn('service_role',panel.lower())
        self.assertNotIn('sb_secret_',panel)

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
        self.assertIn('cron: "4-59/5 * * * *"',flow)
        self.assertIn('KAURIVO_CLAIMED_JOB_FILE',flow)
        self.assertNotIn('SUPABASE_SERVICE_ROLE_KEY:',flow)
        self.assertNotIn('sb_secret_',edge)

    def test_source_diagnostics_identify_paths_without_exposing_queries_or_content(self):
        from io import StringIO
        from scripts.run_kaurivo_demo_queue import source_failure_diagnostic
        log=StringIO(
          "Some unrelated HTML text should not appear here.\n"
          "RuntimeError: Original-site content research incomplete; review these pages: "
          "https://business.example/palvelut?token=private, "
          "https://business.example/ihmiset?email=private\n"
        )
        detail=source_failure_diagnostic(log)
        self.assertIn("/palvelut",detail)
        self.assertIn("/ihmiset",detail)
        self.assertNotIn("private",detail)
        self.assertNotIn("token=",detail)
        self.assertNotIn("business.example",detail)
        self.assertEqual(source_failure_diagnostic(StringIO("generic network error")),"")

    def test_stage_failure_reports_safe_exception_location_and_specific_code(self):
        from io import StringIO
        from scripts.run_kaurivo_demo_queue import (
            classify_stage_failure, private_stage_error_location)
        log=StringIO(
          'Traceback (most recent call last):\n'
          '  File "/home/runner/work/website-builder-agent/agents/research.py", line 619, in research\n'
          '    raise RuntimeError("hidden private customer information")\n'
          'RuntimeError: Fewer than three source-backed same-industry operators; cannot build.\n'
        )
        self.assertEqual(classify_stage_failure(log,"researching"),
                         "comparison_sources_insufficient")
        safe=private_stage_error_location(log)
        self.assertIn("RuntimeError",safe)
        self.assertIn("research.py:619",safe)
        self.assertNotIn("hidden private",safe)
        self.assertNotIn("/home/runner",safe)
        other=StringIO("RuntimeError: AI ei palauttanut lopullista Research-briefiä JSON-objektina.\n")
        self.assertEqual(classify_stage_failure(other,"researching"),
                         "research_ai_invalid_json")

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

    def test_free_key_preflight_is_zero_token_and_rejects_unauthorized_keys(self):
        from unittest.mock import patch, Mock
        from scripts.run_kaurivo_demo_queue import validate_free_api_key, HoldError
        def mock_response(status,data=None):
            r=Mock()
            r.status_code=status
            r.json.return_value={"data":data if data is not None else {}}
            return r
        with patch.dict(os.environ,{"OPENROUTER_API_KEY":"test-only-key"}):
            for http,reason in [(401,"free_ai_key_invalid"),(403,"free_ai_key_forbidden"),
                                (500,"free_ai_key_validation_unavailable")]:
                with self.subTest(http=http):
                    with patch("scripts.run_kaurivo_demo_queue.requests.get",
                               return_value=mock_response(http)) as get:
                        with self.assertRaisesRegex(HoldError,reason):
                            validate_free_api_key()
                        self.assertIn("/api/v1/key",get.call_args.args[0])
            with patch("scripts.run_kaurivo_demo_queue.requests.get",
                       return_value=mock_response(200,{"is_management_key":True})):
                with self.assertRaisesRegex(HoldError,"free_ai_wrong_key_type"):
                    validate_free_api_key()
            with patch("scripts.run_kaurivo_demo_queue.requests.get",
                       return_value=mock_response(200,{"is_provisioning_key":True})):
                with self.assertRaisesRegex(HoldError,"free_ai_wrong_key_type"):
                    validate_free_api_key()
            with patch("scripts.run_kaurivo_demo_queue.requests.get",
                       return_value=mock_response(200,{"is_management_key":False})) as get:
                self.assertTrue(validate_free_api_key())
                self.assertEqual(get.call_count,1)
            with patch("scripts.run_kaurivo_demo_queue.requests.get",
                       return_value=mock_response(200,{"free_model_daily_requests":{
                           "used":50,"limit":50,"remaining":0}})) as get:
                with self.assertRaisesRegex(HoldError,"free_ai_capacity_unavailable"):
                    validate_free_api_key()
                self.assertIn("/api/v1/key",get.call_args.args[0])
            with patch("scripts.run_kaurivo_demo_queue.requests.get",
                       return_value=mock_response(200,{"free_model_daily_requests":{
                           "used":1,"limit":50,"remaining":49}})):
                self.assertTrue(validate_free_api_key())
        with patch.dict(os.environ,{"OPENROUTER_API_KEY":""}):
            with self.assertRaisesRegex(HoldError,"free_ai_key_missing"):
                validate_free_api_key()

    def test_free_provider_capacity_defers_instead_of_marking_false_qa_pass(self):
        from utils import claude_client, resource_manager
        from unittest.mock import patch
        migration=(SITE/"backend/kaurivo_targeted_durable_worker_20261111.sql").read_text(
            encoding="utf-8")
        worker=WORKER.read_text(encoding="utf-8")
        bridge=EDGE.read_text(encoding="utf-8")
        self.assertIn("next_eligible_at",migration)
        self.assertIn("retry_claims_today<3",migration)
        self.assertIn("interval '1 day 10 minutes'",migration)
        self.assertIn("p_error_code='free_ai_capacity_unavailable'",migration)
        self.assertIn("kaurivo_worker_update_demo",migration)
        self.assertIn("p_run_id",migration)
        self.assertIn("internal_preview",migration)
        self.assertIn('update("queued"',worker)
        self.assertIn('TRANSIENT FAILURE DEFERRED',worker)
        self.assertIn('data.status==="queued"&&![' ,bridge)
        with patch.dict(os.environ,{"FREE_ONLY":"1",
                   "FREE_CLOUD_LOCAL_FALLBACK":"1","OLLAMA_MODEL":"",
                   "OLLAMA_RESEARCH_MODEL":""}):
            with patch.object(resource_manager,"reserve",return_value=False), \
                 patch.object(resource_manager,"openrouter_reservation_block_reason", \
                              return_value="daily"), \
                 patch.object(claude_client,"_get_headers",return_value={}), \
                 patch.object(claude_client.config,"model_for_stage",
                    return_value="google/gemma-4-26b-a4b-it:free"), \
                 patch.object(claude_client.config,"backend_for_stage",
                    return_value="openrouter"), \
                 patch.object(claude_client.requests,"post") as request:
                with self.assertRaisesRegex(RuntimeError,"FREE_AI_CAPACITY_UNAVAILABLE"):
                    claude_client.ask_claude("system","content",stage="research")
                request.assert_not_called()

    def test_minute_cap_waits_once_then_uses_free_endpoint_without_daily_defer(self):
        from utils import claude_client, resource_manager
        from unittest.mock import patch, Mock
        response=Mock(status_code=200)
        response.json.return_value={
          "choices":[{"message":{"content":"Public verified summary"},
                      "finish_reason":"stop"}]
        }
        with patch.dict(os.environ,{"FREE_ONLY":"1","OLLAMA_MODEL":""}), \
             patch.object(resource_manager,"reserve",side_effect=[False,True]) as reserve, \
             patch.object(resource_manager,"openrouter_reservation_block_reason",
                          return_value="minute"), \
             patch.object(claude_client,"_get_headers",return_value={}), \
             patch.object(claude_client.config,"model_for_stage",
                          return_value="google/gemma-4-26b-a4b-it:free"), \
             patch.object(claude_client.config,"backend_for_stage",
                          return_value="openrouter"), \
             patch.object(claude_client.time,"sleep") as pause, \
             patch.object(claude_client.requests,"post",return_value=response) as post:
            self.assertEqual(claude_client.ask_claude(
                "system","prompt",stage="research"),"Public verified summary")
            self.assertEqual(reserve.call_count,2)
            pause.assert_called_once()
            post.assert_called_once()
            self.assertTrue(post.call_args.kwargs["json"]["model"].endswith(":free"))

    def test_daily_cap_does_not_retry_or_use_paid_provider(self):
        from utils import claude_client, resource_manager
        from unittest.mock import patch
        with patch.dict(os.environ,{"FREE_ONLY":"1","OLLAMA_MODEL":"",
                         "OLLAMA_RESEARCH_MODEL":""}), \
             patch.object(resource_manager,"reserve",return_value=False), \
             patch.object(resource_manager,"openrouter_reservation_block_reason",
                          return_value="daily"), \
             patch.object(claude_client,"_get_headers",return_value={}), \
             patch.object(claude_client.config,"model_for_stage",
                          return_value="google/gemma-4-26b-a4b-it:free"), \
             patch.object(claude_client.config,"backend_for_stage",
                          return_value="openrouter"), \
             patch.object(claude_client.time,"sleep") as pause, \
             patch.object(claude_client.requests,"post") as post:
            with self.assertRaisesRegex(RuntimeError,"FREE_AI_CAPACITY_UNAVAILABLE"):
                claude_client.ask_claude("system","prompt",stage="research")
            pause.assert_not_called()
            post.assert_not_called()

    def test_research_stage_error_classification_never_reveals_private_output(self):
        from tempfile import TemporaryFile
        from scripts.run_kaurivo_demo_queue import classify_stage_failure
        fixtures=[
            ("OpenRouter rejected request: HTTP 429","free_ai_rate_limit"),
            ("OpenRouter rejected request: HTTP 402","free_ai_account_blocked"),
            ("OpenRouter rejected request: HTTP 400","free_model_request_rejected"),
            ("OpenRouter rejected request: HTTP 401","free_ai_key_invalid"),
            ("OpenRouter rejected request: HTTP 403","free_ai_key_forbidden"),
            ("RuntimeError: Yrityksen sivun analyysi epäonnistui: HTTP 403","source_http_access_blocked"),
            ("RuntimeError: Yrityksen sivun analyysi epäonnistui: HTTP 429","source_http_rate_limited"),
            ("RuntimeError: Yrityksen sivun analyysi epäonnistui: HTTP 404","source_website_unreachable"),
            ("ModuleNotFoundError: No module named 'missing'","missing_runtime_dependency"),
            ("source inventory missing required services","source_research_incomplete"),
            ("RuntimeError: FREE_AI_CAPACITY_UNAVAILABLE: no paid fallback",
             "free_ai_capacity_unavailable"),
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
        # Resume at the last saved revision, while retaining the strict
        # MAX_AUTO_REVISIONS bound rather than restarting a paid/free QA loop.
        self.assertIn('for revision in range(next_qa_revision,MAX_AUTO_REVISIONS+1)',worker)
        self.assertIn('resume.startswith("revised_")',worker)
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
           with patch("scripts.run_kaurivo_demo_queue.validate_free_api_key",
                      return_value=True) as validate:
               free_model_configured()
               validate.assert_called_once_with()

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
          review_status:'unverified',website_assessment:'unreviewed',
          business_activity_assessment:'unreviewed',
          payment_signal:'unknown',customer_need:'unknown',
          evidence_url:'https://example.com/',demo_stage:'not_started',
          demo_brief:'',outreach_review:'not_reviewed',
          outreach_stage:'not_contacted',marketing_opt_out:true,
          website_languages:'fi',contact_language:'fi'};
        window.__rpcCalls=[];window.__demoRows=[];window.__dispatchCalls=[];
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
                    table==='kaurivo_demo_build_jobs'?window.__demoRows:
                    table==='kaurivo_demo_builder_health'?[{
                      singleton:true,status:'blocked',error_code:'free_ai_key_invalid',
                      checked_at:'2026-01-01T00:00:00.000Z',github_run_url:''
                    }]:[],
               error:null})
          }),
          functions:{invoke:async(name,params)=>{
             window.__dispatchCalls.push({name,job:params?.body?.job_id});
             return {data:{ok:true,dispatch:'accepted'},error:null};
          }},
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
                    # Owner may choose All companies even if outreach is
                    # prohibited: private demo building and sales eligibility
                    # are independent. 'Research next 20' intentionally hides
                    # opt-outs to preserve its sales-focused semantics.
                    page.locator("#lead-view").select_option("all")
                    page.wait_for_function(
                        "document.querySelector('#prospect-list .record-title')?.textContent === 'Esimerkki Verhoomo'"
                    )
                    self.assertTrue(page.locator("#prospect-list .demo-build-trigger").is_enabled())
                    self.assertIn("Rakentaja tauolla",page.locator("#demo-health").inner_text())
                    page.locator("#prospect-list .demo-build-trigger").click()
                    page.wait_for_function(
                        "document.querySelector('#demo-running-list').textContent.includes('Esimerkki Verhoomo')"
                    )
                    self.assertEqual(page.locator("#tab-demos").is_visible(),True)
                    self.assertEqual(page.locator("#demo-ready-list .demo-external").count(),0)
                    self.assertEqual(page.evaluate(
                        "window.__rpcCalls.filter(x=>x.name==='kaurivo_request_demo_build').length"
                    ),1)
                    page.wait_for_function("window.__dispatchCalls.length===1")
                    self.assertEqual(page.evaluate(
                        "window.__dispatchCalls[0].name"),"kaurivo-demo-dispatch")
                    self.assertEqual(page.locator("#demo-running-list .demo-gh-manual").count(),1)
                    self.assertTrue(page.locator("#demo-running-list .demo-build-dispatch").is_enabled())
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
                    old_link=page.locator("#demo-ready-list a.demo-comparison-link")
                    self.assertEqual(old_link.count(),2)
                    self.assertEqual(old_link.nth(0).inner_text(),"Vanha sivu")
                    self.assertEqual(old_link.nth(0).get_attribute("href"),"https://example.com/")
                    self.assertEqual(old_link.nth(1).inner_text(),"Uusi sivu")
                    self.assertEqual(old_link.nth(1).get_attribute("target"),"_blank")
                    self.assertTrue(old_link.nth(1).get_attribute("href").endswith("/test/index.html"))
                    self.assertEqual(page.locator("#demo-ready-list .demo-copy-comparison").count(),1)
                    # The operator must be able to request a fresh build
                    # from the failure card when verified business facts arrive.
                    page.evaluate("""()=>{
                       window.__demoRows[0].status='hold';
                       window.__demoRows[0].error_code='source_research_incomplete';
                       window.__demoRows[0].preview_url='';
                    }""")
                    page.locator("#refresh-demos").click()
                    self.assertTrue(page.locator("#demo-hold-list .demo-build-retry").is_enabled())
                    page.locator("#demo-hold-list .demo-build-retry").click()
                    page.wait_for_function(
                      "window.__rpcCalls.filter(x=>x.name==='kaurivo_request_demo_build').length===2"
                    )
                    page.wait_for_function("window.__dispatchCalls.length===2")
                    self.assertEqual(exceptions,[],exceptions)
                    page.close()
            finally:
                browser.close()


if __name__=="__main__":
    unittest.main()

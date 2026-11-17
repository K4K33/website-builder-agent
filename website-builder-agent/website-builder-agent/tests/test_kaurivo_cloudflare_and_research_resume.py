"""Regression tests for optional free Cloudflare failover and partial research."""
import hashlib
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch
import requests
from utils import cloudflare_free_ai as cf
from utils.kaurivo_research_progress import get_progress, save_progress
from scripts.kaurivo_demo_checkpoint import make_archive, unpack_archive, STAGES, CheckpointError

ROOT=Path(__file__).resolve().parents[1]
FLOW=(ROOT.parents[1]/".github/workflows/kaurivo-demo-worker.yml").read_text(encoding="utf-8")
EDGE=(ROOT/"docs/kaurivo/backend/demo_worker_edge.ts").read_text(encoding="utf-8")
RUNNER=(ROOT/"scripts/run_kaurivo_demo_queue.py").read_text(encoding="utf-8")
SOURCE=(ROOT/"agents/research.py").read_text(encoding="utf-8")
ACCOUNT="a"*32
CONFIRMED={"FREE_ONLY":"1","KAURIVO_CLOUDFLARE_WORKERS_FREE_CONFIRMED":"1",
           "CLOUDFLARE_ACCOUNT_ID":ACCOUNT,"CLOUDFLARE_API_TOKEN":"K"*40}
JOB="020cebce-a511-4eca-8cf0-a1e55e35a82b"


def snapshot():
    return {"slug":"sample","name":"Sample","url":"https://sample.fi",
      "research_progress":{"version":1,"milestone":"source",
        "source_url":"https://sample.fi","master_prompt_sha256":"f"*64,
        "site_data":{"title":"Sample","success":True},
        "source_inventory":{"pages":[{"url":"https://sample.fi","title":"Sample"}]}}}


class CloudflareFreeTests(unittest.TestCase):
    def test_disabled_until_owner_confirms_actual_free_plan(self):
        with patch.dict(os.environ,{**CONFIRMED,
             "KAURIVO_CLOUDFLARE_WORKERS_FREE_CONFIRMED":"0"},clear=True), \
             patch.object(cf.requests,"post") as post:
            self.assertFalse(cf.enabled())
            with self.assertRaisesRegex(RuntimeError,"not confirmed"):
                cf.chat_cloudflare_free("sys","prompt",stage="research",max_tokens=100)
            post.assert_not_called()

    def test_one_allowlisted_request_with_separate_visual_qa(self):
        self.assertNotEqual(cf.FREE_MODELS["builder"],cf.FREE_MODELS["qa"])
        self.assertEqual(cf.FREE_MODELS["qa"],"@cf/mistralai/mistral-small-3.1-24b-instruct")
        resp=Mock(status_code=200)
        resp.json.return_value={"model":cf.FREE_MODELS["research"],
          "choices":[{"finish_reason":"stop","message":{"content":"Verified facts"}}]}
        with patch.dict(os.environ,CONFIRMED,clear=True), \
             patch.object(cf,"_ATTEMPTS",0), \
             patch.object(cf.requests,"post",return_value=resp) as post:
            self.assertEqual(cf.chat_cloudflare_free(
                "sys","prompt",stage="research",max_tokens=300),"Verified facts")
            self.assertEqual(post.call_count,1)
            self.assertFalse(post.call_args.kwargs["allow_redirects"])
            self.assertEqual(post.call_args.kwargs["json"]["model"],cf.FREE_MODELS["research"])
            self.assertIn("/"+ACCOUNT+"/ai/v1/chat/completions",post.call_args.args[0])


    def test_independent_qa_uses_only_documented_free_model_with_exact_allowlist(self):
        expected = "@cf/mistralai/mistral-small-3.1-24b-instruct"
        reply = Mock(status_code=200)
        reply.json.return_value = {
            "model": expected, "choices": [{
                "finish_reason": "stop",
                "message": {"content": '{"source_reference_reviewed":true}'}
            }]}
        with patch.dict(os.environ, CONFIRMED, clear=True), \
             patch.object(cf, "_ATTEMPTS", 0), \
             patch.object(cf.requests, "post", return_value=reply) as post:
            result = cf.chat_cloudflare_free(
                "Independently compare source designs", "verified assets",
                stage="qa", max_tokens=500, json_mode=True)
            self.assertIn("source_reference_reviewed", result)
            self.assertEqual(post.call_args.kwargs["json"]["model"], expected)
            self.assertEqual(post.call_count, 1)

    def test_no_paid_model_or_incomplete_content_accepted(self):
        for status,body in [(429,{}),(403,{}),(200,{"model":"@cf/moonshotai/kimi-k2.7-code",
            "choices":[{"finish_reason":"stop","message":{"content":"no"}}]}),
            (200,{"model":cf.FREE_MODELS["research"],"choices":[
             {"finish_reason":"length","message":{"content":"partial"}}]})]:
            with self.subTest(status=status):
                reply=Mock(status_code=status)
                reply.json.return_value=body
                with patch.dict(os.environ,CONFIRMED,clear=True), \
                     patch.object(cf,"_ATTEMPTS",0), \
                     patch.object(cf.requests,"post",return_value=reply) as post:
                    with self.assertRaises(RuntimeError):
                        cf.chat_cloudflare_free("sys","source",stage="research",max_tokens=200)
                    # Only a truncated, otherwise valid response receives
                    # ONE larger-budget request; no endless retries.
                    self.assertEqual(post.call_count,2 if status==200 and
                                     body.get("model")==cf.FREE_MODELS["research"] else 1)



    def test_fourteen_concept_and_original_views_are_never_dropped_by_free_qa(self):
        from utils.cloudflare_free_ai import chat_cloudflare_free
        message = [
            {"type": "text", "text": "All 14 original view panels"},
            *[{"type": "image_url",
               "image_url": {"url": "data:image/jpeg;base64,AA=="}} for _ in range(7)]
        ]
        response = Mock(status_code=200)
        response.json.return_value = {
            "model": cf.FREE_MODELS["qa"],
            "choices": [{"finish_reason": "stop",
                         "message": {"content": '{"selected_alias":"A"}'}}],
        }
        paths = ["private-verified-view-" + str(i) for i in range(14)]
        with patch.dict(os.environ, CONFIRMED, clear=True), \
             patch.object(cf, "_ATTEMPTS", 0), \
             patch("utils.kaurivo_cloud_vision_packet.compact_concept_review_user_content",
                   return_value=message) as paired, \
             patch("utils.kaurivo_cloud_vision_packet.compact_vision_user_content") as old, \
             patch.object(cf.requests, "post", return_value=response) as post:
            self.assertEqual(chat_cloudflare_free(
                "independent review", "must inspect fourteen views", stage="qa",
                max_tokens=1200, json_mode=True, image_paths=paths),
                '{"selected_alias":"A"}')
            paired.assert_called_once_with("must inspect fourteen views", paths)
            old.assert_not_called()
            self.assertEqual(len(post.call_args.kwargs["json"]["messages"][1]["content"]), 8)
            self.assertEqual(post.call_count, 1)

    def test_qa_router_404_retries_once_at_documented_same_vision_model_rest_endpoint(self):
        router = Mock(status_code=404)
        official = Mock(status_code=200)
        official.json.return_value = {
            "success": True,
            "result": {"model": cf.FREE_MODELS["qa"], "choices": [
                {"finish_reason": "stop",
                 "message": {"content": '{"selected_alias":"A"}'}}
            ]},
        }
        with patch.dict(os.environ, CONFIRMED, clear=True), \
             patch.object(cf, "_ATTEMPTS", 0), \
             patch("utils.kaurivo_cloud_vision_packet.compact_vision_user_content",
                   return_value=[
                       {"type": "text", "text": "source-backed screenshots"},
                       {"type": "image_url", "image_url": {"url": "data:image/png;base64,AA=="}}
                   ]), \
             patch.object(cf.requests, "post",
                          side_effect=[router, official]) as post:
            result = cf.chat_cloudflare_free(
                "independent reviewer", "private image review", stage="qa",
                max_tokens=1400, image_paths=["private screenshot"], json_mode=True)
            self.assertEqual(result, '{"selected_alias":"A"}')
            self.assertEqual(post.call_count, 2)
            self.assertEqual(cf._ATTEMPTS, 2)
            second = post.call_args_list[1]
            self.assertIn(
                "/ai/run/" + cf.FREE_MODELS["qa"], second.args[0])
            self.assertNotIn("model", second.kwargs["json"])
            self.assertEqual(second.kwargs["json"]["messages"][1]["content"][1]["type"],
                             "image_url")
            self.assertFalse(second.kwargs["allow_redirects"])
            self.assertNotIn("gemma", second.args[0])

    def test_cloudflare_qa_404_then_rest_404_stays_blocked_without_other_models(self):
        with patch.dict(os.environ, CONFIRMED, clear=True), \
             patch.object(cf, "_ATTEMPTS", 0), \
             patch.object(cf.requests, "post",
                          side_effect=[Mock(status_code=404),
                                       Mock(status_code=404)]) as post:
            with self.assertRaisesRegex(RuntimeError, "FREE_MODEL_UNAVAILABLE"):
                cf.chat_cloudflare_free(
                    "independent", "review", stage="qa", max_tokens=180,
                    json_mode=True)
            self.assertEqual(post.call_count, 2)
            self.assertEqual(cf._ATTEMPTS, 2)

    def test_qa_free_rate_limit_never_triggers_unverified_rest_fallback(self):
        with patch.dict(os.environ, CONFIRMED, clear=True), \
             patch.object(cf, "_ATTEMPTS", 0), \
             patch.object(cf.requests, "post",
                          return_value=Mock(status_code=429, headers={})) as post:
            with self.assertRaisesRegex(RuntimeError, "FREE_AI_RATE_LIMIT"):
                cf.chat_cloudflare_free("sys", "review", stage="qa",
                                        max_tokens=160, json_mode=True)
            post.assert_called_once()

    def test_rest_unexpected_model_and_incomplete_result_are_never_approved(self):
        cases = [
            {"success": True, "result": {
                "model": cf.FREE_MODELS["builder"],
                "choices": [{"finish_reason":"stop",
                             "message":{"content":'{"selected_alias":"B"}'}}]}},
            {"success": True, "result": {"model": cf.FREE_MODELS["qa"],
                                        "choices":[{"finish_reason":"length",
                                                    "message":{"content":'{"selected_alias":"A"}'}}]}},
            {"success": True, "result": {"response": '{"selected_alias"'}},
        ]
        for result in cases:
            with self.subTest(case=result), \
                 patch.dict(os.environ, CONFIRMED, clear=True), \
                 patch.object(cf, "_ATTEMPTS", 0), \
                 patch.object(cf.requests, "post",
                              side_effect=[Mock(status_code=404),
                                           Mock(status_code=200, json=Mock(
                                               return_value=result))]) as post:
                with self.assertRaisesRegex(RuntimeError, "FREE_MODEL_REQUEST_REJECTED"):
                    cf.chat_cloudflare_free("sys", "review", stage="qa",
                                            max_tokens=160, json_mode=True)
                self.assertEqual(post.call_count, 2)

    def test_real_openrouter_429_handler_invokes_free_cloud_not_ollama(self):
        from utils.claude_client import _local_free_quota_fallback
        with patch.dict(os.environ,CONFIRMED,clear=True), \
             patch("utils.cloudflare_free_ai.chat_cloudflare_free",return_value="pass") as cloud, \
             patch("utils.local_ai.chat_local") as local:
            answer=_local_free_quota_fallback("sys","src",stage="qa",
                           max_tokens=1000,image_paths=["example.png"],json_mode=True)
            self.assertEqual(answer,"pass")
            cloud.assert_called_once()
            local.assert_not_called()

    def test_known_empty_openrouter_free_daily_budget_uses_verified_cloud(self):
        from scripts import run_kaurivo_demo_queue as runner
        response=Mock(status_code=200)
        response.json.return_value={"data":{"free_model_daily_requests":{"remaining":0}}}
        with patch.dict(os.environ,{"OPENROUTER_API_KEY":"dummy",
                                 "KAURIVO_OPENROUTER_FREE_EXHAUSTED":""}), \
             patch("scripts.run_kaurivo_demo_queue.requests.get",
                   return_value=response), \
             patch("utils.cloudflare_free_ai.enabled",return_value=True):
            runner.validate_free_api_key()
            self.assertEqual(os.environ["KAURIVO_OPENROUTER_FREE_EXHAUSTED"],"1")
        with patch.dict(os.environ,{"OPENROUTER_API_KEY":"dummy",
                                 "KAURIVO_OPENROUTER_FREE_EXHAUSTED":""}), \
             patch("scripts.run_kaurivo_demo_queue.requests.get",
                   return_value=response), \
             patch("utils.cloudflare_free_ai.enabled",return_value=False):
            with self.assertRaisesRegex(runner.HoldError,"free_ai_capacity_unavailable"):
                runner.validate_free_api_key()

    def test_github_claim_uses_only_confirmed_free_cloud_when_openrouter_empty(self):
        self.assertIn("cloudflare_ready=",FLOW)
        self.assertIn("steps.keycheck.outputs.cloudflare_ready",FLOW)
        self.assertIn("OpenRouter free quota known empty",FLOW)
        self.assertIn('KAURIVO_CLOUDFLARE_WORKERS_FREE_CONFIRMED:',FLOW)
        from utils.claude_client import ask_claude
        with patch.dict(os.environ,{**CONFIRMED,"AI_BACKEND":"openrouter",
                     "RESEARCH_MODEL":"google/gemma-4-26b-a4b-it:free",
                     "KAURIVO_OPENROUTER_FREE_EXHAUSTED":"1"},clear=True), \
             patch("utils.cloudflare_free_ai.chat_cloudflare_free",
                   return_value="verified") as cloud, \
             patch("utils.claude_client._get_headers") as openrouter:
            self.assertEqual(ask_claude("system","source",stage="research"),"verified")
            cloud.assert_called_once()
            openrouter.assert_not_called()

    def test_worker_vars_no_paid_automatic_fallback(self):
        self.assertIn("vars.KAURIVO_CLOUDFLARE_WORKERS_FREE_CONFIRMED || '0'",FLOW)
        self.assertIn("secrets.KAURIVO_CLOUDFLARE_API_TOKEN",FLOW)
        self.assertIn('FREE_ONLY: "1"',FLOW)

    def test_openrouter_transport_failure_uses_confirmed_free_cloud(self):
        from utils.claude_client import ask_claude
        with patch.dict(os.environ,{**CONFIRMED,"AI_BACKEND":"openrouter",
                     "RESEARCH_MODEL":"google/gemma-4-26b-a4b-it:free"},clear=True), \
             patch("utils.claude_client._get_headers",return_value={}), \
             patch("utils.claude_client.resource_manager.reserve",return_value=True), \
             patch("utils.claude_client.requests.post",side_effect=requests.ReadTimeout) as post, \
             patch("utils.cloudflare_free_ai.chat_cloudflare_free",return_value="verified") as cloud:
            self.assertEqual(ask_claude("system","source",stage="research",json_mode=True),"verified")
            post.assert_called_once()
            cloud.assert_called_once_with(
                "system","source",stage="research",max_tokens=4000,image_paths=None,json_mode=True)


    def test_two_transient_free_transport_failures_retry_primary_within_bounded_cap(self):
        from utils.claude_client import ask_claude
        response = Mock(status_code=200)
        response.json.return_value = {
            "choices": [{"message": {"content": "verified"}, "finish_reason": "stop"}],
            "model": "google/gemma-4-26b-a4b-it:free",
        }
        with patch.dict(os.environ, {**CONFIRMED, "AI_BACKEND": "openrouter",
                     "RESEARCH_MODEL": "google/gemma-4-26b-a4b-it:free"}, clear=True), \
             patch("utils.claude_client._get_headers", return_value={}), \
             patch("utils.claude_client.resource_manager.reserve", return_value=True), \
             patch("utils.claude_client.requests.post",
                   side_effect=[requests.ReadTimeout(), response]) as primary, \
             patch("utils.cloudflare_free_ai.chat_cloudflare_free",
                   side_effect=RuntimeError("NETWORK_UNAVAILABLE: backup transport")) as alternate, \
             patch("utils.claude_client.time.sleep") as pause:
            self.assertEqual(ask_claude("system", "source", stage="research",
                                        json_mode=True, max_retries=2), "verified")
            self.assertEqual(primary.call_count, 2)
            alternate.assert_called_once()
            self.assertEqual(pause.call_count, 1)

    def test_nontransport_cloudflare_rejection_never_retries_free_provider(self):
        from utils.claude_client import ask_claude
        with patch.dict(os.environ, {**CONFIRMED, "AI_BACKEND": "openrouter",
                     "RESEARCH_MODEL": "google/gemma-4-26b-a4b-it:free"}, clear=True), \
             patch("utils.claude_client._get_headers", return_value={}), \
             patch("utils.claude_client.resource_manager.reserve", return_value=True), \
             patch("utils.claude_client.requests.post",
                   side_effect=requests.ReadTimeout()) as primary, \
             patch("utils.cloudflare_free_ai.chat_cloudflare_free",
                   side_effect=RuntimeError("FREE_AI_RATE_LIMIT: reached")):
            with self.assertRaisesRegex(RuntimeError, "FREE_AI_RATE_LIMIT"):
                ask_claude("system", "source", stage="research", max_retries=3)
            primary.assert_called_once()


class PartialResearchTests(unittest.TestCase):
    def test_private_partial_archive_cannot_count_as_researched(self):
        self.assertEqual(STAGES[0],"research_partial")
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            data=snapshot()
            raw=make_archive(root,"sample",JOB,"research_partial",data)
            restored=unpack_archive(root,"sample",JOB,"research_partial",raw,
                      hashlib.sha256(raw).hexdigest(),expected_name="Sample",
                      expected_source="https://sample.fi")
            self.assertEqual(restored["research_progress"]["milestone"],"source")
            with self.assertRaisesRegex(CheckpointError,"research not complete"):
                make_archive(root,"sample",JOB,"researched",data)

    def test_identity_and_master_prompt_are_not_stale(self):
        data=snapshot()
        self.assertTrue(get_progress(data,source_url="https://sample.fi",
                       master_prompt_sha256="f"*64))
        self.assertFalse(get_progress(data,source_url="https://other.fi",
                       master_prompt_sha256="f"*64))
        self.assertFalse(get_progress(data,source_url="https://sample.fi",
                       master_prompt_sha256="0"*64))

    def test_incremental_facts_keep_sourced_original_content(self):
        data=snapshot()
        with patch("utils.kaurivo_research_progress.get_company",
                   return_value=("sample",data)), \
             patch("utils.kaurivo_research_progress.upsert_company") as update:
            next_state=save_progress("sample",data, milestone="facts",
                source_url="https://sample.fi",
                master_prompt_sha256="f"*64,
                extracted={"company_facts":{"name":"Sample"}})
        self.assertEqual(next_state["milestone"],"facts")
        self.assertEqual(next_state["source_inventory"],
                         data["research_progress"]["source_inventory"])
        update.assert_called_once()

    def test_validated_design_survives_partial_archive_without_becoming_researched(self):
        data = snapshot()
        references = [{"url": f"https://peer{i}.fi"} for i in range(3)]
        data["research_progress"].update(
            milestone="references", extracted={}, selected=references,
            references=references, reference_evidence=references,
            validated_design_brief={"design_decisions": [{"id": "home"}]},
        )
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            raw = make_archive(root, "sample", JOB, "research_partial", data)
            restored = unpack_archive(
                root, "sample", JOB, "research_partial", raw,
                hashlib.sha256(raw).hexdigest(), expected_name="Sample",
                expected_source="https://sample.fi",
            )
            progress = get_progress(restored, source_url="https://sample.fi",
                                    master_prompt_sha256="f"*64)
            self.assertEqual(progress["validated_design_brief"],
                             data["research_progress"]["validated_design_brief"])
            self.assertNotIn("research", restored)

    def test_exhausted_worker_deadline_requeues_before_starting_next_stage(self):
        from scripts import run_kaurivo_demo_queue as worker
        with TemporaryDirectory() as tmp, (Path(tmp) / "worker.log").open("w+") as log:
            with patch.object(worker.time, "monotonic", return_value=100), \
                 patch.object(worker.subprocess, "run") as launch:
                with self.assertRaises(worker.HoldError) as exc:
                    worker.run_cli(["build", "sample"], log, deadline=120)
                self.assertIn(exc.exception.code, worker.TRANSIENT_RETRY_CODES)
                launch.assert_not_called()

    def test_runner_saves_partial_only_for_private_research(self):
        self.assertIn('save_private_checkpoint("research_partial", agent_slug)',RUNNER)
        self.assertIn('done = completed_stage_index(', RUNNER)
        self.assertIn('resume, load_company(agent_slug) if resume == "concepts" else None', RUNNER)
        from utils.kaurivo_checkpoint_stage_recovery import completed_stage_index
        self.assertEqual(completed_stage_index("research_partial"), -1)
        self.assertEqual(completed_stage_index("researched"), 0)
        self.assertEqual(completed_stage_index(
            "concepts", {"concept_previews": {"status": "blocked"}}), 0)
        self.assertEqual(completed_stage_index(
            "concepts", {"concept_previews": {"status": "ready_for_comparison"}}), 1)
        self.assertIn("verify_design_handoff(load_company(agent_slug),selected=False)",RUNNER)
        self.assertIn("quality_gate_not_approved",RUNNER)
        self.assertIn("verify_public(url,marker,routes)",RUNNER)
        self.assertIn("research_partial",EDGE)
        self.assertIn('milestone="source"',SOURCE)
        self.assertIn('milestone="facts"',SOURCE)
        self.assertIn('milestone="references"',SOURCE)

    def test_browser_failure_progress_does_not_leak_raw_browser_text(self):
        # A bounded diagnostic must not copy private HTML or URLs to job progress.
        self.assertIn('safe_hints = (', RUNNER)
        self.assertIn('browser_tail.rsplit(marker, 1)', RUNNER)
        self.assertIn('categories[:4]', RUNNER)
        self.assertNotIn('detail = browser_hints', RUNNER)

if __name__=="__main__":
    unittest.main()

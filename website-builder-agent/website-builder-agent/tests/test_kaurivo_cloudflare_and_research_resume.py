"""Regression tests for optional free Cloudflare failover and partial research."""
import hashlib
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch
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
        self.assertEqual(cf.FREE_MODELS["qa"],"@cf/qwen/qwen3.8-27b")
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
                    post.assert_called_once()

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

    def test_runner_saves_partial_only_for_private_research(self):
        self.assertIn('save_private_checkpoint("research_partial", agent_slug)',RUNNER)
        self.assertIn('done=(-1 if resume in (None, "research_partial")',RUNNER)
        self.assertIn("verify_design_handoff(load_company(agent_slug),selected=False)",RUNNER)
        self.assertIn("quality_gate_not_approved",RUNNER)
        self.assertIn("verify_public(url,marker,routes)",RUNNER)
        self.assertIn("research_partial",EDGE)
        self.assertIn('milestone="source"',SOURCE)
        self.assertIn('milestone="facts"',SOURCE)
        self.assertIn('milestone="references"',SOURCE)

if __name__=="__main__":
    unittest.main()

"""Private Windows-local builder: independent, offline QA and security checks.

Tests do NOT enroll a device, use an AI quota, claim any company, or mutate CRM.
"""
import os
from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock,patch

from scripts.kaurivo_local_worker import (
    FALLBACK_POLL_SECONDS,LocalWorkerError,models,ollama_ready,TOKEN_RE
)

ROOT=Path(__file__).resolve().parents[1]
SITE=ROOT/"docs/kaurivo"
SQL=(SITE/"backend/kaurivo_local_worker_20261112.sql").read_text(encoding="utf-8")
BRIDGE=(SITE/"backend/demo_worker_edge.ts").read_text(encoding="utf-8")
ENROLL=(SITE/"backend/kaurivo_local_enroll_edge.ts").read_text(encoding="utf-8")
DISPATCH=(SITE/"backend/demo_immediate_dispatch_edge.ts").read_text(encoding="utf-8")
PANEL=(SITE/"assets/demo-jobs.js").read_text(encoding="utf-8")
RUNNER=(ROOT/"scripts/run_kaurivo_demo_queue.py").read_text(encoding="utf-8")
DAEMON=(ROOT/"scripts/kaurivo_local_worker.py").read_text(encoding="utf-8")
SETUP=(ROOT/"scripts/setup_kaurivo_windows.ps1").read_text(encoding="utf-8")
START=(ROOT/"scripts/start_kaurivo_worker.ps1").read_text(encoding="utf-8")


class LocalWindowsTests(TestCase):
    def test_only_owner_enrolls_token_hash_and_device_can_heartbeat(self):
        self.assertIn("kaurivo_internal.is_kaurivo_admin()",SQL)
        self.assertIn("token_hash text not null unique",SQL)
        self.assertIn("expires_at>now()",SQL)
        self.assertIn("grant execute on function public.kaurivo_local_worker_validate",SQL)
        self.assertIn("to service_role",SQL)
        self.assertIn("from public,anon,authenticated",SQL)
        self.assertIn("return response(200,{ok:true,token",ENROLL)
        self.assertIn("crypto.getRandomValues(new Uint8Array(32))",ENROLL)
        self.assertIn('"SHA-256"',ENROLL)
        self.assertIn('db.auth.getUser(',ENROLL)
        self.assertNotIn("SUPABASE_SERVICE_ROLE_KEY",ENROLL)
        self.assertNotIn("localStorage",ENROLL)
        self.assertNotIn("sessionStorage",ENROLL)
        self.assertIn("kaurivo_local_worker_validate",BRIDGE)
        self.assertIn("jwtVerify(",BRIDGE)
        self.assertIn("repository_owner_id",BRIDGE)
        self.assertIn("repository_id",BRIDGE)
        self.assertIn("local_worker_not_enrolled",BRIDGE)

    def test_exact_local_job_is_claimed_and_not_falsely_marked_ready(self):
        self.assertIn('FALLBACK_POLL_SECONDS=90.0',DAEMON)
        self.assertEqual(FALLBACK_POLL_SECONDS,90.0)
        self.assertIn('def realtime_wakeup(',DAEMON)
        self.assertIn('wake.wait(timeout=FALLBACK_POLL_SECONDS)',DAEMON)
        self.assertIn('"claim"',DAEMON)
        self.assertIn('status=\'researching\'',SQL)
        self.assertIn("kaurivo_local_worker_claim",SQL)
        self.assertIn("for update skip locked limit 1",SQL)
        self.assertIn("j.status='queued'",SQL)
        self.assertIn("runner_kind='local'",SQL)
        self.assertIn("kaurivo_local_worker_online",DISPATCH)
        self.assertIn('dispatch:"local_ready"',DISPATCH)
        self.assertIn("Windows-rakentaja on valmiina",PANEL)
        self.assertIn("status!==\"queued\"",PANEL)
        self.assertIn("Käynnistys lähetetty",PANEL)
        self.assertIn("local_qa_public_proof_missing",RUNNER)
        self.assertIn("quality_gate_not_approved",RUNNER)
        self.assertIn("verify_public(url,marker,routes)",RUNNER)
        self.assertIn("p_release_sha !~",SQL)
        self.assertIn("p_status='internal_preview'",SQL)

    def test_local_models_require_distinct_visual_reviewer(self):
        with patch.dict(os.environ,{"OLLAMA_RESEARCH_MODEL":"qwen2.5-coder:7b",
          "OLLAMA_BUILDER_MODEL":"qwen2.5-coder:7b",
          "OLLAMA_QA_MODEL":"llava:7b"}):
            selected=models()
        self.assertNotEqual(selected["qa"],selected["builder"])
        with patch.dict(os.environ,{"OLLAMA_BUILDER_MODEL":"same:7b",
                                    "OLLAMA_QA_MODEL":"same:7b"}):
            with self.assertRaises(LocalWorkerError):models()
        session=Mock()
        session.get.return_value.json.return_value={"models":[
          {"name":"qwen2.5-coder:7b"},{"name":"llava:7b"}]}
        session.post.return_value.json.return_value={"capabilities":["completion","vision"]}
        self.assertTrue(ollama_ready(session,selected))
        session.post.return_value.json.return_value={"capabilities":["completion"]}
        self.assertFalse(ollama_ready(session,selected))
        self.assertEqual(session.get.call_args.args[0],"http://127.0.0.1:11434/api/tags")
        self.assertEqual(session.post.call_args.args[0],"http://127.0.0.1:11434/api/show")

    def test_tokens_never_enter_git_or_public_browser_code(self):
        self.assertIn("ConvertFrom-SecureString",SETUP)
        self.assertIn("ConvertTo-SecureString",START)
        self.assertIn("ZeroFreeBSTR",START)
        self.assertIn("Read-Host",SETUP)
        self.assertIn("New-ScheduledTaskTrigger",SETUP)
        self.assertIn("KAURIVO_LOCAL_WORKER_TOKEN",DAEMON)
        self.assertIn("TOKEN_RE",DAEMON)
        self.assertTrue(TOKEN_RE.fullmatch("kvl_"+"a"*64))
        self.assertFalse(TOKEN_RE.fullmatch("kvl_"+"x"*64))
        self.assertNotIn("SUPABASE_SERVICE_ROLE_KEY",START)
        self.assertNotIn("SUPABASE_SERVICE_ROLE_KEY",DAEMON)
        self.assertNotIn("ghp_",PANEL)
        self.assertIn("KAURIVO_LOCAL_WORKER",RUNNER)
        self.assertIn('AI_BACKEND":"ollama"',DAEMON)

    def test_real_qa_proof_and_immutable_preview_are_required(self):
        self.assertIn('qa_details=(company.get("qa") or {}) if LOCAL_WORKER else None',RUNNER)
        self.assertIn('verdict.get("overall_pass") is not True',RUNNER)
        self.assertIn('qa_url=proof_url,release_sha=sha',RUNNER)
        self.assertIn("qa[.]html",SQL)
        self.assertIn("replace(p_qa_url,'/qa.html','/index.html')<>p_preview_url",SQL)
        self.assertIn("k4k33[.]github[.]io",SQL)
        self.assertIn("kaurivo-auto-demos-2026.onrender.com",PANEL)
        self.assertIn("qa[.]html",PANEL)
        self.assertIn("noindex,nofollow,noarchive",RUNNER)

    def test_windows_works_even_with_cloud_quota_exhausted(self):
        self.assertIn("j.error_code='free_ai_capacity_unavailable'",SQL)
        self.assertIn('RESEARCH_AI_BACKEND":"ollama"',DAEMON)
        self.assertIn('QA_AI_BACKEND":"ollama"',DAEMON)
        self.assertIn('FREE_ONLY":"1"',DAEMON)
        self.assertIn('http://127.0.0.1:11434',DAEMON)
        self.assertIn("restore_private_checkpoint(",RUNNER)
        self.assertIn("save_private_checkpoint(",RUNNER)
        self.assertIn("stage_timeout",RUNNER)
        self.assertIn("preview_publication_failed",RUNNER)

"""Prevent confusing GitHub/OpenRouter free-model rate limits with Codex.

Synthetic source checks: no network, API key, AI inference or customer data.
"""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
JS=(ROOT/"docs/kaurivo/assets/demo-jobs.js").read_text(encoding="utf-8")
HTML=(ROOT/"docs/kaurivo/admin/index.html").read_text(encoding="utf-8")
RUNNER=(ROOT/"scripts/run_kaurivo_demo_queue.py").read_text(encoding="utf-8")
FLOW=(ROOT.parents[1]/".github/workflows/kaurivo-demo-worker.yml").read_text(encoding="utf-8")


class ExplicitCloudQuotaTests(unittest.TestCase):
    def test_status_explicitly_names_openrouter_not_codex(self):
        self.assertIn('free_ai_rate_limit:"Pilvessä toimiva OpenRouter',JS)
        self.assertIn('Tämä ei ole Codexin käyttöraja',JS)
        self.assertIn('OpenRouter-avain toimii (mallikapasiteettia ei vahvistettu)',JS)
        self.assertIn('Tämä ei varmista, että maksuton malli hyväksyy uuden pyynnön',JS)
        self.assertIn('"Odottaa pilvi-AI:ta"',JS)
        self.assertIn('job.runner_kind==="github"',JS)
        self.assertIn('GitHub Actions + OpenRouter',JS)
        self.assertNotIn('Rakennuspalvelu käytettävissä',JS)
        self.assertIn('demo-jobs.js?v=20261112-cloudflare-codes6',HTML)

    def test_deferral_progress_is_truthful_without_bypassing_qa(self):
        self.assertIn("cloud_limit=(not LOCAL_WORKER",RUNNER)
        self.assertIn('Codexia ei käytetä. Työ on tallessa;',RUNNER)
        self.assertIn("jatko riippuu ilmaisesta AI-kapasiteetista.",RUNNER)
        self.assertIn('update("queued",message,error_code=error.code)',RUNNER)
        self.assertIn('if error.code in TRANSIENT_RETRY_CODES:',RUNNER)
        self.assertIn('quality_gate_build_version_mismatch',RUNNER)
        self.assertIn('verify_public(url,marker,routes)',RUNNER)

    def test_cloud_uses_only_free_models(self):
        self.assertIn("AI_BACKEND: openrouter",FLOW)
        self.assertIn('FREE_ONLY: "1"',FLOW)
        self.assertIn("RESEARCH_MODEL:",FLOW)
        self.assertIn("QA_MODEL:",FLOW)
        self.assertNotIn("AI_BACKEND: codex",FLOW)

if __name__=="__main__":
    unittest.main()

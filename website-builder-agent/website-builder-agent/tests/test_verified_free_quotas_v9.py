"""V9: use documented provider free quotas without accidental paid usage.

All tests use mocked provider traffic: no real keys, model downloads or credits.
"""
import json
import os
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import Mock, patch

import config
from agents import research
from utils import claude_client, resource_manager
from utils import kaurivo_website_research as website


class FreeQuotaTests(TestCase):
    def test_hybrid_routes_free_research_and_local_premium_builder_and_vision_qa(self):
        env = {"FREE_ONLY": "1", "AI_BACKEND": "ollama",
               "RESEARCH_AI_BACKEND": "openrouter",
               "RESEARCH_MODEL": "provider/free-research:free",
               "OLLAMA_BUILDER_MODEL": "local-code",
               "OLLAMA_QA_MODEL": "local-vision"}
        with patch.dict(os.environ, env):
            self.assertEqual(config.backend_for_stage("research"), "openrouter")
            self.assertEqual(config.model_for_stage("research"), "provider/free-research:free")
            self.assertEqual(config.backend_for_stage("builder"), "ollama")
            self.assertEqual(config.model_for_stage("builder"), "local-code")
            self.assertEqual(config.backend_for_stage("qa"), "ollama")

    def test_explicit_free_builder_and_qa_models_are_allowed_but_router_not_allowed(self):
        with patch.dict(os.environ, {"FREE_ONLY": "1", "AI_BACKEND": "openrouter",
                                     "BUILDER_MODEL": "provider/coder:free",
                                     "QA_MODEL": "provider/vision:free"}):
            self.assertEqual(config.model_for_stage("builder"), "provider/coder:free")
            self.assertEqual(config.model_for_stage("qa"), "provider/vision:free")
        with patch.dict(os.environ, {"FREE_ONLY": "1", "AI_BACKEND": "openrouter",
                                     "QA_MODEL": "openrouter/free"}):
            with self.assertRaisesRegex(RuntimeError, "exact"):
                config.model_for_stage("qa")
        with patch.dict(os.environ, {"FREE_ONLY": "1", "AI_BACKEND": "openrouter",
                                     "BUILDER_MODEL": "provider/paid"}):
            with self.assertRaisesRegex(RuntimeError, "FREE_ONLY"):
                config.model_for_stage("builder")

    def test_free_cloud_model_makes_only_free_model_http_request(self):
        response = Mock(status_code=200)
        response.json.return_value = {
            "choices": [{"message": {"content": "Source-backed description"},
                         "finish_reason": "stop"}]}
        env = {"FREE_ONLY": "1", "AI_BACKEND": "ollama",
               "RESEARCH_AI_BACKEND": "openrouter",
               "RESEARCH_MODEL": "provider/research:free"}
        with patch.dict(os.environ, env), \
             patch.object(claude_client, "_get_headers", return_value={"Authorization": "mock"}), \
             patch.object(resource_manager, "reserve", return_value=True) as reserve, \
             patch.object(claude_client.requests, "post", return_value=response) as post:
            answer = claude_client.ask_claude("system", "prompt", stage="research")
        self.assertEqual(answer, "Source-backed description")
        reserve.assert_called_once_with("openrouter")
        self.assertEqual(post.call_args.kwargs["json"]["model"],
                         "provider/research:free")

    def test_exhausted_free_cloud_quota_uses_installed_local_model_without_paid_calls(self):
        env = {"FREE_ONLY": "1", "AI_BACKEND": "openrouter",
               "RESEARCH_MODEL": "provider/research:free",
               "OLLAMA_RESEARCH_MODEL": "local-research"}
        with patch.dict(os.environ, env), \
             patch.object(claude_client, "_get_headers", return_value={"Authorization":"mock"}), \
             patch.object(resource_manager, "reserve", return_value=False), \
             patch("utils.local_ai.chat_local", return_value="Done locally") as local, \
             patch.object(claude_client.requests, "post") as provider:
            self.assertEqual(
                claude_client.ask_claude("system", "prompt", stage="research"),
                "Done locally")
            provider.assert_not_called()
            self.assertEqual(local.call_args.kwargs["model"], "local-research")

    def test_free_cloud_429_stops_cloud_retries_and_keeps_model_local(self):
        reply = Mock(status_code=429, text="Free account rate limited")
        env = {"FREE_ONLY": "1", "AI_BACKEND": "openrouter",
               "RESEARCH_MODEL": "provider/research:free",
               "OLLAMA_RESEARCH_MODEL": "local-research"}
        with patch.dict(os.environ, env), \
             patch.object(claude_client, "_get_headers", return_value={"Authorization":"mock"}), \
             patch.object(resource_manager, "reserve", return_value=True), \
             patch("utils.local_ai.chat_local", return_value="Local reply"), \
             patch.object(claude_client.requests, "post", return_value=reply) as send:
            self.assertEqual(claude_client.ask_claude("sys", "prompt", stage="research"),
                             "Local reply")
            send.assert_called_once()

    def test_missing_local_fallback_fails_closed_at_free_quota(self):
        env = {"FREE_ONLY": "1", "AI_BACKEND": "openrouter",
               "RESEARCH_MODEL": "provider/research:free",
               "OLLAMA_MODEL": "", "OLLAMA_RESEARCH_MODEL": ""}
        with patch.dict(os.environ, env), \
             patch.object(claude_client, "_get_headers", return_value={"Authorization":"mock"}), \
             patch.object(resource_manager, "reserve", return_value=False), \
             patch.object(claude_client.requests, "post") as provider:
            with self.assertRaisesRegex(RuntimeError, "no paid fallback"):
                claude_client.ask_claude("sys", "prompt", stage="research")
            provider.assert_not_called()

    def test_paid_stage_override_cannot_bypass_explicit_paid_consent(self):
        import main
        from types import SimpleNamespace
        env = {"FREE_ONLY": "0", "AI_BACKEND": "ollama",
               "RESEARCH_AI_BACKEND": "openrouter",
               "RESEARCH_MODEL": "provider/paid"}
        with patch.dict(os.environ, env):
            with self.assertRaisesRegex(RuntimeError, "confirm-paid-apis"):
                main._require_paid_consent(
                    SimpleNamespace(confirm_paid_apis=False)
                )
            main._require_paid_consent(
                SimpleNamespace(confirm_paid_apis=True)
            )

    def test_tavily_basic_free_search_requires_account_confirmation(self):
        env = {"FREE_ONLY": "1", "TAVILY_API_KEY": "free-plan-fixture"}
        response = Mock(status_code=200)
        response.json.return_value = {"results": [
            {"title": "Real shop", "url": "https://example.org/", "content": "Observed page"}]}
        with patch.dict(os.environ, env), \
             patch.object(research.resource_manager, "reserve", return_value=True) as reserve, \
             patch.object(research.requests, "post", return_value=response) as post:
            with self.assertRaisesRegex(RuntimeError, "TAVILY_FREE_PLAN_CONFIRMED"):
                research._search_tavily("flowers")
            post.assert_not_called()
            reserve.assert_not_called()
        with patch.dict(os.environ, {**env, "TAVILY_FREE_PLAN_CONFIRMED": "1"}), \
             patch.object(research.resource_manager, "reserve", return_value=True) as reserve, \
             patch.object(research.requests, "post", return_value=response) as post:
            results = research._search_tavily("flowers", max_results=5)
            self.assertEqual(len(results), 1)
            reserve.assert_called_once_with("tavily")
            payload = post.call_args.kwargs["json"]
            self.assertEqual(payload["search_depth"], "basic")
            self.assertEqual(payload["include_raw_content"], False)
            self.assertEqual(payload["include_images"], False)

    def test_local_tavily_free_limit_never_exceeds_750_even_if_env_sets_larger(self):
        with patch.dict(os.environ, {"FREE_ONLY": "1"}), \
             patch.object(resource_manager, "TAVILY_MONTHLY_LIMIT", 100000), \
             patch.object(resource_manager, "TAVILY_SAFETY_MARGIN", 0):
            self.assertEqual(resource_manager._tavily_safe_limit(), 750)

    def test_scheduled_free_tavily_requires_own_confirmed_account_and_atomic_claim(self):
        packet = {"schema": "kaurivo_prh_shortlist_v1", "mode": "pilot-live",
                  "candidates": [{"name": "Example Oy", "business_id": "1234-5",
                                  "city_hint": "Tampere", "website_listed_url": ""}]}
        import tempfile
        from pathlib import Path
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / "leads.json"
            file.write_text(json.dumps(packet), encoding="utf-8")
            with patch.dict(os.environ, {"FREE_ONLY": "1"}), \
                 patch.object(website, "search_once") as provider:
                no = website.enrich(file, key="secret", claim=lambda: True)
                self.assertEqual(no["searched"], 0)
                provider.assert_not_called()
            with patch.dict(os.environ, {
                    "FREE_ONLY": "1", "KAURIVO_TAVILY_FREE_PLAN_CONFIRMED": "1"}), \
                 patch.object(website, "search_once",
                              return_value=({"url":"https://example.org/"}, False)) as provider:
                no_credit = website.enrich(file, key="secret", claim=lambda: False)
                self.assertEqual(no_credit["searched"], 0)
                provider.assert_not_called()
                allowed = website.enrich(file, key="secret", claim=lambda: True)
                self.assertEqual(allowed["searched"], 1)
                provider.assert_called_once()

    def test_tavily_basic_free_search_results_reused_across_companies(self):
        from utils.free_tavily_cache import cached_free_search
        from datetime import datetime, timedelta, timezone
        from pathlib import Path
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            called = Mock(return_value=[{
                "url": "https://actual-operator.example.org/",
                "title": "Real operator", "content": "Observed link"}])
            t = datetime(2026, 11, 3, tzinfo=timezone.utc)
            first = cached_free_search("real florists in Finland", called,
                                       cache_root=Path(tmp), now=t)
            second = cached_free_search("real florists in Finland", called,
                                        cache_root=Path(tmp), now=t+timedelta(days=1))
            self.assertEqual(first, second)
            called.assert_called_once()
            cached_free_search("real florists in Finland", called,
                               cache_root=Path(tmp), now=t+timedelta(days=15))
            self.assertEqual(called.call_count, 2)

    def test_no_implicit_tavily_spend_when_osm_pool_ample(self):
        with patch.dict(os.environ, {
                "FREE_ONLY": "1", "TAVILY_API_KEY": "fixture",
                "TAVILY_FREE_PLAN_CONFIRMED": "1"}), \
             patch.object(research, "discover_free_references",
                          return_value=[{"url": f"https://real{i}.example.org/"} for i in range(12)]), \
             patch.object(research, "_search_tavily") as paid:
            sites = research._search_industry_references(
                "kukkakauppa", "https://target.example/", "kukkakauppa")
            self.assertEqual(len(sites), 12)
            paid.assert_not_called()

    def test_tavily_free_is_fallback_when_osm_pool_missing(self):
        # Isolate the persistent cache: another test/run may have cached this query.
        with TemporaryDirectory() as cache_root, \
             patch.object(research.config, "OUTPUT_DIR", cache_root), \
             patch.dict(os.environ, {
                "FREE_ONLY": "1", "TAVILY_API_KEY": "fixture",
                "TAVILY_FREE_PLAN_CONFIRMED": "1"}), \
             patch.object(research, "discover_free_references", side_effect=RuntimeError("empty")), \
             patch.object(research, "_search_tavily",
                 return_value=[{"url": f"https://real{i}.example.org/"} for i in range(5)]) as tavily:
            candidates = research._search_industry_references(
                "florist", "https://target.example/", "kukkia")
            self.assertEqual(len(candidates), 5)
            tavily.assert_called_once()


if __name__ == "__main__":
    import unittest
    unittest.main()

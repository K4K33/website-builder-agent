"""V8 no-charge local builder, genuine public-source caches and unbounded queue."""
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import Mock, patch

import config
import main
from agents import research
from utils.free_batch import process_free_batch
from utils.free_references import discover_free_references, normalize_industry
from utils.reference_site_cache import cached_analyze
from utils.reference_screenshot_cache import capture_cached

NOW = datetime(2026, 11, 3, tzinfo=timezone.utc)
SITES = [{"name": f"Shop {i}", "website": f"https://shop{i}.example.org/"} for i in range(4)]


class FreePipelineTests(unittest.TestCase):
    def test_free_local_default_and_explicit_cloud_override(self):
        with patch.dict(os.environ, {}, clear=True):
            self.assertTrue(config.free_only())
            self.assertEqual(config.ai_backend(), "ollama")
        with patch.dict(os.environ, {"AI_BACKEND": "openrouter"}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "FREE_ONLY"):
                config.ai_backend()
        with patch.dict(os.environ, {"AI_BACKEND": "openrouter", "FREE_ONLY": "0"},
                        clear=True):
            self.assertEqual(config.ai_backend(), "openrouter")

    def test_tavily_never_called_in_free_mode(self):
        with patch.dict(os.environ, {"FREE_ONLY": "1", "AI_BACKEND": "ollama"}), \
             patch.object(research, "_get_tavily_key") as key, \
             patch.object(research.resource_manager, "reserve") as reserve:
            with self.assertRaisesRegex(RuntimeError, "FREE_ONLY blocks Tavily"):
                research._search_tavily("flowers")
            key.assert_not_called()
            reserve.assert_not_called()

    def test_pipeline_preflight_needs_no_tavily_key(self):
        env = {"AI_BACKEND": "ollama", "FREE_ONLY": "1",
               "OLLAMA_MODEL": "local-text", "OLLAMA_BUILDER_MODEL": "local-code",
               "OLLAMA_QA_MODEL": "local-vision", "TAVILY_API_KEY": ""}
        with patch.dict(os.environ, env), \
             patch.object(main.scout, "run_scout", return_value=[]) as scout:
            args = SimpleNamespace(confirm_live_run=True, company="", count=1,
                                   industry="kampaamo", location="Tampere",
                                   benchmark_mode=False)
            with self.assertRaisesRegex(RuntimeError, "No prequalified lead"):
                main.cmd_pipeline(args)
            scout.assert_called_once()

    def test_free_batch_refuses_paid_mode(self):
        with patch.dict(os.environ, {"FREE_ONLY": "0", "AI_BACKEND": "openrouter"}):
            with self.assertRaisesRegex(RuntimeError, "free-batch forbids"):
                main.cmd_free_batch(SimpleNamespace(allow_public_lookups=True))


class FreeReferencesTests(unittest.TestCase):
    def test_source_operator_urls_reused_with_no_repeated_public_calls(self):
        with tempfile.TemporaryDirectory() as tmp:
            fetch = Mock(return_value=SITES)
            cache = Path(tmp) / "cache.json"
            first = discover_free_references(
                "kukkakauppa", cache_path=cache, now=NOW, fetch_osm=fetch,
                historic_lookup=lambda category: [])
            second = discover_free_references(
                "florist", cache_path=cache, now=NOW + timedelta(hours=2),
                fetch_osm=fetch, historic_lookup=lambda category: [])
            self.assertEqual(first, second)
            self.assertEqual(len(first), 4)
            fetch.assert_called_once()

    def test_target_domain_excluded(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = discover_free_references(
                "kampaamo", target_url="https://shop0.example.org/",
                cache_path=Path(tmp)/"r.json", now=NOW,
                fetch_osm=lambda *args: SITES,
                historic_lookup=lambda category: [])
            self.assertEqual(len(result), 3)
            self.assertTrue(all("shop0." not in row["url"] for row in result))

    def test_missing_evidence_is_not_fabricated_or_queried_repeatedly(self):
        with tempfile.TemporaryDirectory() as tmp:
            fetch = Mock(return_value=[])
            path = Path(tmp)/"r.json"
            with self.assertRaisesRegex(RuntimeError, "Fewer than three"):
                discover_free_references("kukkakauppa", cache_path=path,
                                         now=NOW, fetch_osm=fetch,
                historic_lookup=lambda category: [])
            self.assertEqual(fetch.call_count, 2)
            with self.assertRaisesRegex(RuntimeError, "cached"):
                discover_free_references("kukkakauppa", cache_path=path,
                                         now=NOW+timedelta(hours=1), fetch_osm=fetch, historic_lookup=lambda category: [])
            self.assertEqual(fetch.call_count, 2)
            with self.assertRaisesRegex(RuntimeError, "No trustworthy free"):
                discover_free_references("unmapped-sector", cache_path=path,
                                         historic_lookup=lambda category: [])
        self.assertEqual(normalize_industry("kukkakaupan kukkakauppa"),
                         "kukkakauppa")

    def test_rare_industry_uses_prior_verified_company_references(self):
        with tempfile.TemporaryDirectory() as tmp:
            results = discover_free_references(
                "mattokutomo", cache_path=Path(tmp)/"r.json",
                historic_lookup=lambda category: [
                    {"url": f"https://rug{i}.example.org/",
                     "title": f"Real handloom operator {i}"}
                    for i in range(4)],
                fetch_osm=Mock(side_effect=AssertionError("No OSM tag mapping")),
            )
            self.assertEqual(len(results), 4)

    def test_public_osm_candidates_never_include_private_addresses(self):
        with tempfile.TemporaryDirectory() as tmp:
            unsafe = [
                {"website": "http://127.0.0.5/private"},
                {"website": "http://10.0.0.4/"},
                {"website": "http://192.168.1.1/"},
                {"website": "http://169.254.169.254/latest/"},
            ]
            results = discover_free_references(
                "kukkakauppa", cache_path=Path(tmp)/"r.json",
                historic_lookup=lambda category: [],
                fetch_osm=lambda *args: unsafe + SITES,
            )
            self.assertEqual(len(results), 4)
            self.assertTrue(all("example.org" in x["url"] for x in results))

    def test_real_source_text_cache_refreshes_after_one_week(self):
        with tempfile.TemporaryDirectory() as tmp:
            fn = Mock(return_value={"success": True, "visible_text": "Observed real product",
                                    "title": "Real company"})
            a = cached_analyze("https://real.example/", fn, root=tmp, now=NOW)
            b = cached_analyze("https://real.example/", fn, root=tmp,
                               now=NOW+timedelta(days=1))
            self.assertEqual(a, b)
            self.assertEqual(fn.call_count, 1)
            cached_analyze("https://real.example/", fn, root=tmp,
                           now=NOW+timedelta(days=8))
            self.assertEqual(fn.call_count, 2)

    def test_screenshot_cache_checks_real_file_bytes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            def capture(url, name):
                a, b = root / (name + "-desktop.png"), root / (name+"-mobile.png")
                a.write_bytes(b"real image bytes fixture A")
                b.write_bytes(b"real image bytes fixture B")
                return {"desktop": str(a), "mobile": str(b)}
            fn = Mock(side_effect=capture)
            first = capture_cached("https://site.example/", fn,
                                   cache_root=root, now=NOW)
            again = capture_cached("https://site.example/", fn,
                                   cache_root=root, now=NOW+timedelta(days=1))
            self.assertEqual(first, again)
            self.assertEqual(fn.call_count, 1)
            Path(first["mobile"]).write_bytes(b"changed")
            capture_cached("https://site.example/", fn,
                           cache_root=root, now=NOW+timedelta(days=2))
            self.assertEqual(fn.call_count, 2)


class LocalBatchTests(unittest.TestCase):
    def test_no_artificial_limit_processes_every_unapproved_company(self):
        with tempfile.TemporaryDirectory() as tmp:
            queue = {f"c{i}": {"status": "found"} for i in range(8)}
            queue["approved"] = {"status": "approved"}
            called = []
            def one(slug):
                called.append(slug)
                if slug == "c2":
                    raise RuntimeError("missing screenshot")
            checkpoint = Path(tmp)/"batch.json"
            result = process_free_batch(queue, one, status_path=checkpoint,
                                        limit=0, now=NOW)
            self.assertEqual(len(called), 8)
            self.assertEqual(result["remaining"], 0)
            self.assertEqual(result["blocked_or_failed"], 1)
            next_result = process_free_batch(queue, one, status_path=checkpoint,
                                             limit=0, now=NOW)
            self.assertEqual(next_result["attempted"], [])
            self.assertEqual(len(called), 8)
            retry = process_free_batch(queue, one, status_path=checkpoint,
                                       limit=1, retry_failed=True, now=NOW)
            self.assertEqual(len(retry["attempted"]), 1)
            self.assertEqual(len(called), 9)

    def test_limited_batch_keeps_rest_of_queue(self):
        with tempfile.TemporaryDirectory() as tmp:
            queue = {f"c{i}": {"status": "found"} for i in range(6)}
            r = process_free_batch(queue, Mock(), limit=2,
                                   status_path=Path(tmp)/"batch.json", now=NOW)
            self.assertEqual(len(r["attempted"]), 2)
            self.assertEqual(r["remaining"], 4)


if __name__ == "__main__":
    unittest.main()

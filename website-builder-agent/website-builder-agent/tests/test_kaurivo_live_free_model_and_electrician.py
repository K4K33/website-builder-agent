"""New-company regression: live free model and source-backed electrician peers.

All observations synthetic; no tokens, public lookups, paid API, or CRM reads.
"""
from __future__ import annotations

import os
from tempfile import TemporaryDirectory
from pathlib import Path
from unittest import TestCase
from unittest.mock import Mock, patch

import config
from utils.free_references import (
    normalize_industry, verified_sector_search_hint, discover_free_references
)
from utils.claude_client import ask_claude

CONF = {
    "FREE_ONLY": "1",
    "AI_BACKEND": "openrouter",
    "KAURIVO_PREFER_VERIFIED_FREE_ALTERNATE": "1",
    "OPENROUTER_API_KEY": "dummy-not-a-real-key",
    "RESEARCH_MODEL": "google/gemma-4-26b-a4b-it:free",
    "RESEARCH_FALLBACK_MODELS": "google/gemma-4-31b-it:free",
    "BUILDER_MODEL": "google/gemma-4-31b-it:free",
    "BUILDER_FALLBACK_MODELS": "google/gemma-4-26b-a4b-it:free",
    "QA_MODEL": "qwen/qwen3.8-27b:free",
    "QA_FALLBACK_MODELS": "",
}


class NewCompanyReferences(TestCase):
    def test_electrical_service_labels_keep_same_industry(self):
        for term in (
            "sähköasennukset", "Sähköurakointi ja sähkösuunnittelu",
            "sähkötyöt", "Sähköasennustyöt", "Electrical installation",
        ):
            with self.subTest(term=term):
                self.assertEqual(normalize_industry(term), "sähköasentaja")
        self.assertEqual(
            verified_sector_search_hint("Sähköurakointi", "asennukset ja huolto"),
            "sähköasentaja",
        )
        # Real observed target wording; its registered industry can be broader.
        self.assertEqual(
            verified_sector_search_hint(
                "Sähkö- ja automaatiopalvelut",
                "Tarjoamme sähköasennus- ja automaatiopalveluita Kouvolassa "
                "20 vuoden kokemuksella. Pienet sähkötyöt ja latausasemien asennus.",
            ),
            "sähköasentaja",
        )
        # Industrial-only PLC provider cannot become a household electrician.
        self.assertNotEqual(
            verified_sector_search_hint(
                "Teollisuuden tekniset palvelut",
                "Teollisuuden PLC-automaation ohjelmointia.",
            ),
            "sähköasentaja",
        )

    def test_operator_urls_are_unverified_candidates_only(self):
        with TemporaryDirectory() as tmp:
            refs = discover_free_references(
                "Sähköasennukset",
                target_url="https://www.sahko247.fi",
                cache_path=Path(tmp) / "references.json",
                fetch_osm=lambda *_: [],
                historic_lookup=lambda *_: [],
                max_results=5,
            )
            self.assertGreaterEqual(len(refs), 3)
            self.assertEqual(len({r["url"] for r in refs}), len(refs))
            self.assertTrue(all(r["url"].startswith("https://") for r in refs))
            self.assertFalse(any(r["url"].startswith("https://www.sahko247.fi") for r in refs))
            self.assertFalse(any(r.get("verified") is True for r in refs))


class AuditedFreeModelRouting(TestCase):
    def test_new_vision_json_model_preferred_only_with_explicit_opt_in(self):
        with patch.dict(os.environ, CONF, clear=True):
            research = config.stage_model_candidates("research")
            builder = config.stage_model_candidates("builder")
            qa = config.stage_model_candidates("qa")
            self.assertEqual(research[0], "dots-studio/dots-3-note-preview:free")
            self.assertEqual(builder[0], "dots-studio/dots-3-note-preview:free")
            self.assertTrue(set(builder).isdisjoint(qa))
            self.assertTrue(all(name.endswith(":free") for name in research + builder + qa))
        with patch.dict(os.environ, {**CONF,
                                     "KAURIVO_PREFER_VERIFIED_FREE_ALTERNATE": "0"},
                        clear=True):
            self.assertEqual(
                config.stage_model_candidates("research")[0],
                CONF["RESEARCH_MODEL"],
            )

    def test_actual_api_payload_uses_audited_free_primary(self):
        response = Mock(status_code=200)
        response.json.return_value = {
            "model": "dots-studio/dots-3-note-preview:free",
            "choices": [{"finish_reason": "stop",
                         "message": {"content": '{"answer":"ok"}'}}],
        }
        with patch.dict(os.environ, CONF, clear=True), \
             patch("utils.claude_client._get_headers", return_value={}), \
             patch("utils.claude_client.resource_manager.reserve", return_value=True), \
             patch("utils.claude_client.requests.post", return_value=response) as post:
            result = ask_claude(
                "validate facts", "synthetic business",
                stage="research", max_retries=1, json_mode=True,
            )
            self.assertEqual(result, '{"answer":"ok"}')
            payload = post.call_args.kwargs["json"]
            self.assertEqual(payload["model"], "dots-studio/dots-3-note-preview:free")
            self.assertEqual(payload["models"][0], payload["model"])
            self.assertEqual(len(payload["models"]), 3)

    def test_client_keeps_independent_model_gate(self):
        with patch.dict(os.environ, {
            **CONF,
            "QA_MODEL": "dots-studio/dots-3-note-preview:free",
        }, clear=True):
            with self.assertRaisesRegex(RuntimeError, "Independent QA"):
                config.stage_model_candidates("builder")


if __name__ == "__main__":
    import unittest
    unittest.main()

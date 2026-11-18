"""Regression guards for no-cost sector research and global UX QA schema.

No network calls, no API billing and no unverified source approvals.
"""
from __future__ import annotations

import ast
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase

from utils.free_references import (
    CURATED_REFERENCE_CANDIDATES,
    discover_free_references,
    normalize_industry,
)


class SectorDiscoveryUnblock(TestCase):
    def test_freight_labels_resolve_to_source_verifiable_candidates(self):
        for industry in (
            "Tieliikenteen tavarankuljetus",
            "Kuljetusliike",
            "Road freight",
            "Rahtikuljetukset",
        ):
            self.assertEqual(normalize_industry(industry), "maantiekuljetus")
        with TemporaryDirectory() as folder:
            rows = discover_free_references(
                "Kuljetusliike",
                target_url="https://kuljetusliike.com/",
                cache_path=Path(folder) / "sources.json",
                historic_lookup=lambda category: [],
                fetch_osm=lambda *args: self.fail("Freight should use official candidate pages"),
                max_results=10,
            )
        self.assertGreaterEqual(len(rows), 3)
        self.assertEqual(len(rows), len({row["url"].split("/")[2] for row in rows}))
        self.assertTrue(all(row["url"].startswith("https://") for row in rows))
        self.assertNotIn("https://kuljetusliike.com/", [row["url"] for row in rows])
        # Candidate discovery must never present proof that a live crawl has not established.
        self.assertTrue(all("industry_match" not in row and "screenshots" not in row for row in rows))

    def test_locksmith_labels_have_distinct_real_operator_candidates(self):
        for industry in ("Lukitustekniikka", "Lukkoliike", "Lukkoseppä", "Locksmith"):
            self.assertEqual(normalize_industry(industry), "lukituspalvelut")
        with TemporaryDirectory() as folder:
            rows = discover_free_references(
                "Lukitustekniikka",
                target_url="https://www.lukkokeskus.fi/",
                cache_path=Path(folder) / "sources.json",
                historic_lookup=lambda category: [],
                fetch_osm=lambda *args: self.fail("Locksmith should use official candidate pages"),
                max_results=10,
            )
        self.assertGreaterEqual(len(rows), 3)
        self.assertEqual(len(rows), len({row["url"].split("/")[2] for row in rows}))
        self.assertTrue(all("industry_match" not in row for row in rows))

    def test_no_claim_that_candidates_are_proven_references(self):
        for category in ("maantiekuljetus", "lukituspalvelut"):
            urls = [url for _, url in CURATED_REFERENCE_CANDIDATES[category]]
            self.assertGreaterEqual(len(urls), 5)
            self.assertEqual(len({url.split("/")[2] for url in urls}), len(urls))




class SourceQuoteReconciliation(TestCase):
    def test_exact_nearby_service_heading_can_repair_model_fragment(self):
        from utils.service_quality import reconcile_primary_offering_with_source
        page = {
            "url": "https://client.example/palvelut",
            "text": (
                "Sähköinen lukitus yrityksiin. "
                "Asennamme ja huollamme ovien sähköisiä lukkoja ja kulunvalvontaa. "
                "Toimimme asiakkaan tarpeiden mukaan."
            ),
        }
        result = reconcile_primary_offering_with_source({
            "source_url": page["url"],
            "label": "Sähköinen lukitus",
            "quote": "Asennamme ja huollamme ovien sähköisiä lukkoja ja kulunvalvontaa.",
        }, [page])
        self.assertEqual(result["source_url"], page["url"])
        self.assertIn("Sähköinen lukitus", result["quote"])
        self.assertIn("Asennamme ja huollamme", result["quote"])

    def test_hallucinated_quote_or_unverified_site_still_fails(self):
        from utils.service_quality import reconcile_primary_offering_with_source
        for sample in (
            {"source_url": "https://client.example/palvelut", "label": "Sähköinen lukitus",
             "quote": "Tarjoamme 24 tunnin maksutonta lukituspalvelua kaikille."},
            {"source_url": "https://other.example/palvelut", "label": "Sähköinen lukitus",
             "quote": "Asennamme ja huollamme sähköisiä lukkoja."},
            {"source_url": "https://client.example/palvelut", "label": "Sähköinen lukitus",
             "quote": "Asennamme ja huollamme ovien sähköisiä lukkoja."},
        ):
            with self.assertRaises(RuntimeError):
                reconcile_primary_offering_with_source(sample, [{
                    "url": "https://client.example/palvelut",
                    "text": "Sähköinen lukitus yrityksiin. Asennamme ja huollamme ovien mekaanisia lukkoja.",
                }])


class GlobalCraftReviewerSchema(TestCase):
    def test_json_example_in_visual_review_prompt_is_parseable_and_complete(self):
        source = (Path(__file__).resolve().parents[1] / "agents" / "qa.py").read_text("utf-8")
        module = ast.parse(source)
        prompt = None
        for node in module.body:
            if isinstance(node, ast.Assign) and any(
                isinstance(target, ast.Name) and target.id == "VISUAL_REVIEW_PROMPT"
                for target in node.targets
            ):
                prompt = ast.literal_eval(node.value)
                break
        self.assertIsNotNone(prompt)
        schema = prompt.split("Tämä palautusskeema korvaa aiemman esimerkkiskeeman:\n", 1)[1]
        schema = schema.split("\nTekoälymäisyyden riski", 1)[0]
        payload = json.loads(schema)
        self.assertIn("global_craft_experience_comparison", payload)
        craft = payload["global_craft_experience_comparison"]
        self.assertEqual(craft["references_observed"], [])
        self.assertEqual(craft["critical_experience_gaps"], [])
        self.assertFalse(craft["independently_9_5_certified"])
        self.assertIn("Älä täytä tyhjiä listoja", prompt)

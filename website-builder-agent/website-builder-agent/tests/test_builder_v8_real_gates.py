"""Production regressions for the V8 Builder engine, no external AI required.

These tests protect the source readiness and source-bound art-direction GATES,
not an AI-granted 9.5 visual score or automated client approval.
"""
from __future__ import annotations

import inspect
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from utils.brand_direction_v8 import audit_art_direction, derive_identity_boundaries
from utils.builder_readiness_v8 import assess_build_readiness, require_build_readiness


def existing(*, theme=None, mode="v8", verified=True):
    url = "https://example-business.fi/palvelut/"
    quote = "Rengashuolto ja renkaiden vaihto ammattitaitoisesti palvelupisteessämme."
    page = {"url": url, "text": "Tarjoamme " + quote,
            "source_identity": {"theme_color": theme or "", "original_logo_candidates": []}}
    return {
        "company_facts": {"name": "Todellinen Auto Oy", "industry": "autohuolto"},
        "source_inventory": {"pages": [page]},
        "primary_offering_evidence": (
            {"label": "Rengashuolto", "quote": quote, "source_url": url}
            if verified else None),
        "v8_visual_protocol": mode,
        "research_mode": "existing_site",
    }


def html(*, intro="Rengashuolto ja renkaiden vaihto", accent="#c9e87f", add_css=True):
    css = f":root{{--accent:{accent};--ink:#14251f}}.hero{{background:var(--ink);color:var(--accent)}}"
    return f"""<!doctype html><html><head>{'<style>'+css+'</style>' if add_css else ''}</head>
    <body><main><section class="hero"><h1>Todellinen Auto Oy</h1>
    <p>{intro}</p></section></main></body></html>"""


class SourceReadinessV8(unittest.TestCase):
    def test_current_service_quote_on_original_site_is_ready(self):
        good = existing()
        self.assertEqual(assess_build_readiness(good)["code"], "ready_source_verified")
        self.assertTrue(require_build_readiness(good)["ready"])

    def test_missing_or_registry_only_current_service_blocks_before_build(self):
        missing = existing(verified=False)
        self.assertEqual(assess_build_readiness(missing)["code"], "source_current_service_missing")
        with self.assertRaisesRegex(RuntimeError, "BUILD_READINESS_BLOCKED"):
            require_build_readiness(missing)
        for quote in ("Yhtiön päätoimiala on tavarankuljetus", "Nautimme yli 4 tähden arviosta"):
            invalid = existing()
            invalid["primary_offering_evidence"]["quote"] = quote
            self.assertFalse(assess_build_readiness(invalid)["ready"])
        unobserved = existing()
        unobserved["source_inventory"]["pages"] = []
        self.assertEqual(assess_build_readiness(unobserved)["code"], "source_original_site_unobserved")

    def test_conflicting_current_service_does_not_turn_into_a_verified_offer(self):
        raw=existing()
        raw["current_service_conflict"]={"status":"unresolved",
                                       "historical":"bus","registry":"freight"}
        self.assertEqual(assess_build_readiness(raw)["code"],"source_current_service_conflict")

    def test_verified_no_site_requires_source_for_a_current_service(self):
        research={"research_mode":"verified_no_website",
                  "company_facts":{"name":"Esimerkki Oy", "services":["Kotisiivous"]},
                  "fact_sources":{"services":["https://local-business-directory.fi/esimerkki"]}}
        self.assertEqual(assess_build_readiness(research)["code"],"ready_verified_no_website")
        research["fact_sources"]["services"]=[]
        self.assertFalse(assess_build_readiness(research)["ready"])

    def test_worker_rechecks_resumed_jobs_before_model_credits(self):
        from scripts import run_kaurivo_demo_queue as worker
        source=inspect.getsource(worker.main)
        self.assertLess(source.index("assess_build_readiness("), source.index('run_cli(["concept-previews"'))
        self.assertIn("source_current_service_unverified", inspect.getsource(assess_build_readiness))

    def test_research_resumed_extraction_cannot_skip_original_service_validation(self):
        from agents import research
        source = inspect.getsource(research.run_research)
        self.assertIn('primary_offering = reconcile_primary_offering_with_source(',source)
        self.assertNotIn('if not isinstance(saved_extraction, dict) or "primary_offering_evidence" in extracted:',source)


class IdentityAndHeroV8(unittest.TestCase):
    def test_unproven_lime_neon_accent_blocks_source_based_client_brand(self):
        research=existing(theme="#14251f")
        report=audit_art_direction({"index.html":html()},research)
        self.assertFalse(report["pass"])
        self.assertEqual(report["blocking"][0]["code"],"unproven_brand_accent")
        self.assertEqual(report["blocking"][0]["evidence"],["#c9e87f"])

    def test_company_verified_brand_color_is_permitted(self):
        research=existing(theme="#c9e87f")
        report=audit_art_direction({"index.html":html()},research)
        self.assertTrue(report["pass"])
        self.assertEqual(report["blocking"],[])
        self.assertEqual(derive_identity_boundaries(research)["verified_original_colors"][0]["hex"],"#c9e87f")

    def test_missing_service_in_first_fold_is_a_specific_repair(self):
        report=audit_art_direction({"index.html":html(intro="Tervetuloa meille!",accent="#14251f")},
                                   existing(theme="#14251f"))
        self.assertEqual([x["code"] for x in report["blocking"]],
                         ["verified_service_not_visible_in_hero"])

    def test_no_site_concept_never_claims_palette_is_verified(self):
        research={"research_mode":"verified_no_website",
                  "v8_visual_protocol":"v8",
                  "company_facts":{"name":"Uusi Esimerkki Oy"},
                  "source_inventory":{"pages":[]}}
        report=audit_art_direction({"index.html":html(intro="Välkommen till oss!")},
                                   research)
        self.assertTrue(report["pass"])
        self.assertTrue(report["review_required"])
        self.assertTrue(report["identity"]["no_site_brand_still_may_exist"])
        self.assertEqual(report["identity"]["new_colors_status"],
                         "provisional_until_owner_checks")

    def test_v7_route_visual_rating_cannot_pass_at_zero_or_poor_scores(self):
        from agents.qa import route_visual_review_passes
        import config
        dimensions=("desktop","mobile","premium_appeal","brand_fidelity",
                    "image_authenticity","art_direction","interaction_quality")
        site={"index.html":"<main><h1>Todellinen Auto Oy</h1></main>"}
        research={"premium_visual_protocol":"v2","v7_visual_protocol":"v7"}
        item={"critical_issues":[],"evidence":"Specific observable screenshot evidence. " * 3}
        item.update({key:0 for key in dimensions})
        report={"route_visual_review":{"index.html":item},
                "reviewed_route_view_ids":["screenshot-1"]}
        self.assertFalse(route_visual_review_passes(report,site,research,["screenshot-1"]))
        item.update({key:config.QA_MIN_VISUAL_SCORE for key in dimensions})
        self.assertTrue(route_visual_review_passes(report,site,research,["screenshot-1"]))
        item["art_direction"]=config.QA_MIN_VISUAL_SCORE-1
        self.assertFalse(route_visual_review_passes(report,site,research,["screenshot-1"]))

    def test_legacy_exercises_keep_original_qa_contract(self):
        report=audit_art_direction({"index.html":html()},existing(theme="#14251f",mode="legacy"))
        self.assertTrue(report["pass"])
        self.assertTrue(report["review_required"])

    def test_actual_linked_local_css_is_audited_and_remote_css_is_not_trusted(self):
        with TemporaryDirectory() as folder:
            root=Path(folder)
            (root/"assets").mkdir()
            (root/"assets"/"main.css").write_text(":root{--brand-accent:#c9e87f}",encoding="utf-8")
            source='<!doctype html><html><head><link rel="stylesheet" href="assets/main.css"></head><body><main><section><h1>Test</h1><p>Rengashuolto</p></section></main></body></html>'
            report=audit_art_direction({"index.html":source},existing(theme="#14251f"),site_root=root)
            self.assertFalse(report["pass"])
            self.assertEqual(report["blocking"][0]["code"],"unproven_brand_accent")


if __name__ == "__main__":
    unittest.main()

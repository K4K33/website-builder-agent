"""Company-agnostic, no-credit benchmark-derived planning regressions."""
from __future__ import annotations
import unittest

from utils.brand_design_blueprint import (
    derive_brand_site_blueprint, audit_sitewide_brand_consistency
)
from utils.universal_quality import audit_universal_standards


class BrandBlueprintTests(unittest.TestCase):
    def case(self):
        return {
            "company_facts": {"name": "Invented local repair cooperative"},
            "creative_selection": {"selected_id": "evidence-led"},
            "creative_directions": [{
                "id": "evidence-led",
                "concept": "Documented service-detail editorial visual language",
                "source_anchor": "Original service photographs",
                "first_view": "Real repair bench with factual service list",
                "information_architecture": "Services, repairs and contact",
                "navigation": "Simple direct task oriented links",
            }],
            "design_recommendations": {
                "typography_scale": "Use original typography features with legible hierarchy",
                "spacing_and_layout": "Distinct composition for a real repair company",
                "mobile_plan": "Narrow layout with direct actionable phone and address",
            },
            "site_architecture": {
                "pages": [{
                    "path": "index.html",
                    "purpose": "Explain repairs and show how to contact this shop",
                    "user_task": "Phone the workshop with a specific part",
                    "section_ids": ["services", "prices", "contact"]
                }, {
                    "path": "services/index.html",
                    "purpose": "Compare repair categories and actual pricing",
                    "user_task": "Select repair and read included work",
                    "section_ids": ["services", "price-list"]
                }]
            },
            "source_inventory": {
                "pages": [{
                    "url": "https://example.org/",
                    "source_identity": {
                        "theme_color": "#305343",
                        "original_logo_candidates": ["https://example.org/brand.svg"],
                        "original_content_photos": [{
                            "src": "https://example.org/service.jpg", "alt": "Workshop"
                        }],
                    },
                }]
            },
            "source_content_map": {"pages": [
                {"source_url": "https://example.org/",
                 "target": "index.html", "sections": []},
            ]}
        }

    def test_creates_source_cited_style_guide_and_multi_page_wireframes(self):
        brief = derive_brand_site_blueprint(self.case())
        self.assertEqual([p["route"] for p in brief["sitemap_and_wireframes"]],
                         ["index.html", "services/index.html"])
        system = brief["shared_brand_system"]
        self.assertEqual(system["sourced_original_theme_colors"][0]["color"], "#305343")
        self.assertEqual(system["sourced_original_theme_colors"][0]["source_urls"],
                         ["https://example.org/"])
        self.assertEqual(system["original_logo_candidates"][0]["url"],
                         "https://example.org/brand.svg")
        self.assertEqual(brief["selected_direction"]["id"], "evidence-led")
        self.assertTrue(system["not_a_rights_license"])
        self.assertTrue(brief["source_sha256"])

    def test_missing_original_brand_does_not_invent_color_or_logo(self):
        case = self.case()
        case["source_inventory"]["pages"][0]["source_identity"] = {}
        result = derive_brand_site_blueprint(case)
        self.assertEqual(result["shared_brand_system"]["original_logo_candidates"], [])
        self.assertEqual(result["shared_brand_system"]["sourced_original_theme_colors"], [])

    def test_no_original_website_still_has_brief_without_fake_provenance(self):
        case = self.case()
        case["source_inventory"] = {"pages": []}
        case["research_mode"] = "verified_no_website"
        result = derive_brand_site_blueprint(case)
        self.assertTrue(result["source_diligence"]["no_website"])
        self.assertEqual(result["source_sha256"], "")
        self.assertEqual(result["shared_brand_system"]["original_logo_candidates"], [])

    def test_missing_selected_creative_direction_is_not_assumed(self):
        case = self.case()
        case["creative_selection"]["selected_id"] = "not-in-choices"
        with self.assertRaisesRegex(RuntimeError, "chosen creative"):
            derive_brand_site_blueprint(case)

    def test_shared_brand_color_mismatch_is_a_full_site_failure(self):
        one = '<html><head><meta name="theme-color" content="#102030"></head><body><main><h1>Home</h1></main></body></html>'
        two = '<html><head><meta name="theme-color" content="#abcdef"></head><body><main><h1>Repairs</h1></main></body></html>'
        pages = {"index.html": one, "repairs/index.html": two}
        report = audit_sitewide_brand_consistency(pages)
        self.assertFalse(report["pass"])
        universal = audit_universal_standards(one, rendered_pages=pages)
        self.assertIn("coherent_sitewide_brand_kit", universal["blocking_problems"])

    def test_same_color_or_missing_theme_tags_do_not_trigger_false_failures(self):
        first = '<html><head><meta name="theme-color" content="#102030"></head><body><main>Home</main></body></html>'
        other = '<html><head><meta name="theme-color" content="#102030"></head><body><main>Other</main></body></html>'
        self.assertTrue(audit_sitewide_brand_consistency({
            "index.html": first, "other.html": other})["pass"])
        self.assertTrue(audit_sitewide_brand_consistency({
            "index.html": first, "other.html": "<main>Other</main>"})["pass"])


    def test_global_brand_tokens_must_agree_across_pages(self):
        """A copied unrelated client's CSS kit cannot slip into a subpage."""
        pages = {
            "index.html": ('<html><head><style>:root{--brand-primary:#153f32;'
                           '--font-heading:Georgia}</style></head><main>Home</main></html>'),
            "palvelut/index.html": ('<html><head><style>:root{--brand-primary:#a71c20;'
                                    '--font-heading:Arial}</style></head><main>Services</main></html>'),
        }
        report = audit_sitewide_brand_consistency(pages)
        self.assertFalse(report["pass"], report)
        self.assertEqual(len(report["issues"]), 2)
        universal = audit_universal_standards(pages["index.html"], rendered_pages=pages)
        self.assertIn("coherent_sitewide_brand_kit", universal["blocking_problems"])

    def test_shared_brand_tokens_allow_distinct_section_colors_and_layouts(self):
        pages = {
            "index.html": ('<style>:root{--brand-primary: #153f32;'
                           '--font-heading: Georgia;} .hero{background:#fff}</style>'),
            "palvelut/index.html": ('<style>:root{--brand-primary:#153F32;'
                                    '--font-heading:Georgia} .hero{background:#eee}</style>'),
        }
        self.assertTrue(audit_sitewide_brand_consistency(pages)["pass"])

    def test_missing_inline_brand_token_is_not_fabricated_as_comparison(self):
        pages = {
            "index.html": '<style>:root{--brand-primary:#153f32}</style>',
            "hinnasto/index.html": '<link rel="stylesheet" href="/style.css">',
        }
        report = audit_sitewide_brand_consistency(pages)
        self.assertTrue(report["pass"])
        self.assertNotIn("hinnasto/index.html",
                         {route for route, data in report["identity_tokens_by_page"].items()
                          if data})


if __name__ == "__main__":
    unittest.main()

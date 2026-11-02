"""Offline and credit-free industry-first research/build preflight regressions."""
from __future__ import annotations

import unittest

from utils.fetch import extract_text_and_meta
from utils.industry_workflow import (
    crawl_original_website, create_industry_brief, sector_guidance,
    validate_inventory,
)


class IndustryWorkflowTests(unittest.TestCase):
    def test_sector_tasks_are_not_reusable_html_templates(self):
        examples = (
            ("Autokorjaamo", "automotive", "booking"),
            ("lounasravintola", "restaurant", "menu"),
            ("rakennusurakointi", "construction", "projects"),
            ("furniture store", "retail", "products"),
            ("hieronta", "wellness", "booking"),
        )
        for label, sector, expected in examples:
            with self.subTest(label=label):
                guidance = sector_guidance(label)
                self.assertEqual(guidance["sector"], sector)
                self.assertIn(expected, " ".join(guidance["visitor_tasks"]))
                self.assertNotIn("<section", str(guidance))
        self.assertEqual(sector_guidance("unknown domain")["sector"], "other")

    def test_bounded_source_crawl_reuses_homepage_and_keeps_important_pages(self):
        root = "https://shop.example.org/"
        records = {
            root: {"success": True, "final_url": root, "title": "Home",
                   "visible_text": "Homepage contents",
                   "links": [
                       {"href": "/contact", "text": "Contact"},
                       {"href": "/services", "text": "Services"},
                       {"href": "/prices", "text": "Prices"},
                       {"href": "/terms", "text": "Terms"},
                       {"href": "https://evil.example.net/services", "text": "Outside"},
                       {"href": "javascript:alert(1)", "text": "Script"},
                       {"href": "/assets/logo.png", "text": "Photo"}]},
            "https://shop.example.org/contact": {"success": True,
                "final_url": "https://shop.example.org/contact",
                "visible_text": "Contact details", "links": []},
            "https://shop.example.org/services": {"success": True,
                "final_url": "https://shop.example.org/services",
                "visible_text": "Important services", "links": []},
            "https://shop.example.org/prices": {"success": True,
                "final_url": "https://shop.example.org/prices",
                "visible_text": "Prices and terms", "links": []},
            "https://shop.example.org/terms": {"success": True,
                "final_url": "https://shop.example.org/terms",
                "visible_text": "Terms", "links": []},
        }
        calls = []
        def fake_fetch(url):
            calls.append(url)
            return records[url]
        result = crawl_original_website(
            root, fake_fetch, first_page=records[root], max_pages=4
        )
        self.assertEqual(len(result["pages"]), 4)
        self.assertEqual(len(calls), 3)  # No duplicate homepage request.
        self.assertNotIn(root, calls)
        self.assertFalse(any("evil" in item["url"] for item in result["pages"]))
        self.assertFalse(result["priority_unvisited_urls"])
        inventory = {"source_inventory": result}
        brief = create_industry_brief(
            {"url": root, "name": "Workshop"},
            {**inventory, "company_facts": {"industry": "autokorjaamo"}},
        )
        self.assertEqual(brief["sector"], "automotive")
        self.assertEqual(brief["inventory_status"]["pages"], 4)

    def test_crawl_blocks_missing_important_pages_before_paid_builder(self):
        root = "https://test.example.org/"
        first = {"success": True, "final_url": root,
                 "visible_text": "Home",
                 "links": [{"href": "/palvelut/", "text": "Palvelut"},
                           {"href": "/yhteys/", "text": "Yhteystiedot"}]}
        result = crawl_original_website(root, lambda u: {
            "success": True, "final_url": u, "visible_text": "Some page",
            "links": []
        }, first_page=first, max_pages=1)
        self.assertEqual(len(result["priority_unvisited_urls"]), 2)
        with self.assertRaisesRegex(RuntimeError, "Important source pages"):
            validate_inventory({"url": root}, {"source_inventory": result})
        with self.assertRaisesRegex(RuntimeError, "Source inventory missing"):
            create_industry_brief({"url": root}, {"company_facts": {
                "industry": "construction"}})

    def test_preflight_prevents_private_ip_or_localhost(self):
        for url in ("http://127.0.0.1/", "http://localhost/",
                    "http://192.168.1.5/admin", "file:///tmp/test.html"):
            with self.subTest(url=url):
                with self.assertRaises(ValueError):
                    crawl_original_website(url, lambda _: {}, max_pages=1)

    def test_no_site_verified_profile_avoids_fake_old_website(self):
        company = {"name": "Test business"}
        research = {"research_mode": "verified_no_website",
                    "fact_sources": [{"url": "https://source.example.org"}],
                    "company_facts": {"industry": "ravintola"}}
        brief = create_industry_brief(company, research)
        self.assertEqual(brief["inventory_status"]["mode"], "verified_no_website")
        self.assertEqual(brief["source_pages"], [])
        self.assertEqual(brief["sector"], "restaurant")

    def test_header_footer_logo_evidence_without_inventing_relationship(self):
        doc = """<!doctype html><html><head><title>Source</title></head><body>
        <header><a href="/"><img src="/brand.svg" alt="Actual brand logo"></a></header>
        <main>Body content</main>
        <footer><a href="https://example.org/"><img src="/affiliation.png"
            alt="Example partner"></a></footer></body></html>"""
        result = extract_text_and_meta(doc, base_url="https://firm.example.org")
        self.assertEqual(result["header_assets"][0]["src"], "/brand.svg")
        self.assertEqual(result["footer_assets"][0]["href"], "https://example.org/")
        self.assertIn("unverified", result["footer_assets"][0]["role"])

if __name__ == "__main__":
    unittest.main()

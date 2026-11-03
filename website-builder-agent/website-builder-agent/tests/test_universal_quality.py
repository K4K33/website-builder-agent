"""Zero-credit tests for agency-wide checks, distinct from visual scoring."""
import unittest
from pathlib import Path
from utils.universal_quality import audit_universal_standards, UNIVERSAL_STANDARDS

class UniversalStandardsTest(unittest.TestCase):
    def setUp(self):
        self.html = ("<!doctype html><html><body><header>Brand</header>"
                     "<main><h1>Services</h1><p>Help at home</p></main>"
                     "<footer>Contact</footer></body></html>")

    def test_all_critical_categories_reported_without_fabricated_pass(self):
        required = {"source_coverage", "same_industry_inspiration",
                    "unique_art_direction", "original_brand", "sponsor_and_partner_marks",
                    "content_parity", "natural_copy", "no_decorative_numbering",
                    "real_testimonials", "accurate_media", "dietary_accuracy",
                    "navigation_and_links", "contact_and_forms", "contrast_and_accessibility",
                    "responsive_performance", "editable_cms", "approved_domain_and_rights",
                    "verified_independent_review"}
        self.assertTrue(required.issubset({x[0] for x in UNIVERSAL_STANDARDS}))
        result = audit_universal_standards(self.html)
        self.assertTrue(result["automated_pass"])
        self.assertEqual(result["quality_decision"], "review_required")
        self.assertFalse(result["blocking_categories"])
        self.assertIn("editable_cms", result["pending_categories"])
        self.assertFalse(result["client_release_ready"])
        self.assertIn("editable_cms", result["pending_evidence"])
        self.assertIn("verified_independent_review", result["pending_evidence"])

    def test_decorative_numbers_and_research_narration_fail(self):
        page = self.html.replace("<main>",
            "<main><article><span class='card-number'>01</span>"
            "<p>Yrityksen verkkosivuilla kerrotaan palveluista.</p></article>")
        result = audit_universal_standards(page)
        self.assertIn("no_decorative_numbering", result["blocking_problems"])
        self.assertIn("natural_copy", result["blocking_problems"])
        self.assertEqual(result["quality_decision"], "blocked")
        self.assertIn("natural_copy", result["blocking_categories"])

    def test_repeated_decorative_cta_arrows_are_blocked_across_pages(self):
        repeated = {
            "index.html": '<html><body><main><a href="/booking">Varaa aika ↗</a>'
                          '<a href="/prices">Hinnasto ↗</a></main></body></html>',
            "services.html": '<html><body><main><a href="/booking">Varaa aika ↗</a>'
                             '<a href="/contact">Yhteys ↗</a></main></body></html>',
        }
        result = audit_universal_standards(repeated["index.html"], rendered_pages=repeated)
        self.assertFalse(result["automated_pass"])
        self.assertIn("non_repetitive_cta_icons", result["blocking_problems"])
        self.assertIn("4 links", result["blocking_problems"]["non_repetitive_cta_icons"][0])

    def test_single_meaningful_directional_link_is_not_automatically_rejected(self):
        html = self.html.replace("</main>", '<a href="/next">Seuraava →</a></main>')
        result = audit_universal_standards(html)
        self.assertNotIn("non_repetitive_cta_icons", result["blocking_problems"])

    def test_duplicate_directional_link_is_detected_even_with_only_two_occurrences(self):
        html = self.html.replace("</main>", '<a href="/next">Seuraava →</a>'
                                 '<a href="/next">Seuraava →</a></main>')
        result = audit_universal_standards(html)
        self.assertIn("non_repetitive_cta_icons", result["blocking_problems"])

    def test_dog_salon_demo_has_zero_decorative_arrows_in_html_and_css(self):
        """Prevent the exact user-reported regression on every salon demo page."""
        root = Path(__file__).resolve().parents[1]
        demo = root / "docs" / "kaurivo" / "demos" / "helsingin-koiratrimmaamo-v1"
        pages = list(demo.rglob("index.html"))
        self.assertEqual(len(pages), 7)
        for page in pages:
            html = page.read_text(encoding="utf-8")
            self.assertNotIn("↗", html, str(page))
            self.assertNotIn('class="round-arrow"', html, str(page))
            self.assertNotIn('class="button light arrow"', html, str(page))
        css = (demo / "assets" / "style.css").read_text(encoding="utf-8")
        self.assertNotIn("↗", css)
        self.assertNotIn(".button.arrow::after", css)
        self.assertNotIn(".round-arrow", css)

    def test_salon_pricing_preserves_exact_breed_name_from_source(self):
        """The source says labradoodle mini/medium, not lagotto mini."""
        demo = (Path(__file__).resolve().parents[1] / "docs" / "kaurivo" /
                "demos" / "helsingin-koiratrimmaamo-v1" / "hinnasto" / "index.html")
        html = demo.read_text(encoding="utf-8")
        self.assertIn("labradoodle mini/medium", html)
        self.assertNotIn("lagotto mini / medium", html)

    def test_approved_logo_missing_is_real_error(self):
        research = {"brand_assets": {"approved_original_logo_url": "/brand.svg"}}
        result = audit_universal_standards(self.html, research)
        self.assertIn("original_brand", result["blocking_problems"])
        new = self.html.replace("<header>Brand</header>",
                                "<header><img src='/brand.svg' alt='Brand'></header>")
        self.assertNotIn("original_brand",
                         audit_universal_standards(new, research)["blocking_problems"])

    def test_partner_logo_requires_real_relationship_and_rights_check(self):
        research = {"source_inventory": {"pages": [{
            "url": "https://business.example.org/", "text": "Info",
            "header_assets": [{"src": "/brand.svg"}],
            "footer_assets": [{"src": "/partner.svg"}],
        }]}}
        report = audit_universal_standards(
            self.html, research, company={"url": "https://business.example.org"})
        self.assertIn("sponsor_and_partner_marks", report["pending_evidence"])
        self.assertIn("original_brand", report["pending_evidence"])

    def test_before_after_needs_same_project_pair(self):
        page = self.html.replace("<main>", "<main><div class='before-after'></div>")
        self.assertIn("accurate_media", audit_universal_standards(page)["blocking_problems"])
        verified = audit_universal_standards(page, {
            "verified_before_after_pairs": [{"before": "/before.jpg", "after": "/after.jpg"}]})
        self.assertNotIn("accurate_media", verified["blocking_problems"])

    def test_restaurant_dietary_info_remains_open_without_verification(self):
        page = self.html.replace("Services", "Lounasruokalista")
        report = audit_universal_standards(
            page, {"company_facts": {"industry": "ravintola"}})
        self.assertIn("dietary_accuracy", report["pending_evidence"])

    def test_browser_and_cms_not_self_certified(self):
        report = audit_universal_standards(self.html)
        self.assertIn("contrast_and_accessibility", report["pending_evidence"])
        self.assertIn("responsive_performance", report["pending_evidence"])
        self.assertIn("contact_and_forms", report["pending_evidence"])

    def test_all_builder_paths_and_qa_have_common_gate(self):
        root = Path(__file__).resolve().parents[1]
        b = (root/"agents"/"builder.py").read_text("utf-8")
        q = (root/"agents"/"qa.py").read_text("utf-8")
        # Every Builder path now routes through ONE shared multi-page
        # validation function instead of copying a separate checker.
        pipeline = (root/"utils"/"site_build_pipeline.py").read_text("utf-8")
        self.assertEqual(b.count("build_pages_from_response("), 3)
        self.assertIn("audit_universal_standards(", pipeline)
        self.assertIn("audit_source_fidelity(", pipeline)
        self.assertIn("validate_locked_copy(", pipeline)
        self.assertIn("audit_universal_standards(", q)
        self.assertIn("record_qa_findings(ledger, slug", q)


    def test_release_approval_is_stale_after_even_one_html_change(self):
        """Passing tick-box flags cannot stand in for fresh client approval."""
        from utils.premium_quality_gate import site_digest
        flags = {
            "cms_edit_verified": True,
            "real_lead_delivery_verified": True,
            "branded_https_verified": True,
            "media_rights_verified": True,
            "legal_and_outreach_reviewed": True,
            "client_approved": True,
            "approved": True,
            "reviewer_kind": "client",
            "reviewer": "Synthetic owner",
            "approved_at": "2026-11-03T09:00:00Z",
            "client_approval_reference": "fixture-only:approval-record",
        }
        company = {"release_evidence": flags}
        before = audit_universal_standards(self.html, company=company,
                                           stage="client_release")
        messages = before["pending_evidence"]["approved_domain_and_rights"]
        self.assertTrue(any("exact site build" in msg for msg in messages), messages)
        flags["build_sha256"] = site_digest({"index.html": self.html})
        signed = audit_universal_standards(self.html, company=company,
                                           stage="client_release")
        self.assertFalse(any("Final client signoff" in msg for msg in
                             signed["pending_evidence"].get("approved_domain_and_rights", [])))
        changed = self.html.replace("Help at home", "Repair in your neighbourhood")
        stale = audit_universal_standards(changed, company=company,
                                          stage="client_release")
        self.assertTrue(any("Final client signoff" in msg for msg in
                            stale["pending_evidence"]["approved_domain_and_rights"]))
        self.assertFalse(stale["client_release_ready"])

    def test_release_approval_cannot_reuse_an_old_source_snapshot(self):
        from utils.premium_quality_gate import site_digest
        from utils.content_parity import source_inventory_sha256
        inventory = {"pages": [{
            "url": "https://synthetic-business.example/",
            "text": "A documented synthetic workshop and service."
        }]}
        release = {
            "approved": True,
            "reviewer_kind": "client",
            "reviewer": "Synthetic owner",
            "approved_at": "2026-11-03T09:00:00Z",
            "client_approval_reference": "fixture-only:approval-record",
            "build_sha256": site_digest({"index.html": self.html}),
            "source_sha256": "stale-source",
        }
        research = {"source_inventory": inventory}
        report = audit_universal_standards(self.html, research, company={
            "release_evidence": release
        })
        self.assertTrue(any("original source snapshot" in msg for msg in
                            report["pending_evidence"]["approved_domain_and_rights"]))
        release["source_sha256"] = source_inventory_sha256(inventory)
        report = audit_universal_standards(self.html, research, company={
            "release_evidence": release
        })
        self.assertFalse(any("Final client signoff" in msg for msg in
                             report["pending_evidence"].get("approved_domain_and_rights", [])))


if __name__ == "__main__":
    unittest.main()

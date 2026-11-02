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
        self.assertEqual(b.count("_validate_all_universal_rules(cleaned, research, company)"), 3)
        self.assertIn("audit_universal_standards(", q)
        self.assertIn("record_qa_findings(ledger, slug", q)

if __name__ == "__main__":
    unittest.main()

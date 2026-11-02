"""Kaurivo: deterministic, credit-free content-preservation checks."""
from __future__ import annotations
from datetime import datetime, timezone
import unittest

from utils.content_parity import audit_content_parity, source_inventory_sha256


class ContentParityTests(unittest.TestCase):
    def setUp(self):
        self.inventory = {"pages": [{
            "url": "https://sample.example.org/",
            "text": "Autohuolto, pikahuolto, korjaus. Contact.",
            "headings": {"h1": ["Sample"]},
            "images": [],
            "header_assets": [{"src": "/brand.svg", "alt": "Brand"}],
            "footer_assets": [{"src": "/partner.svg", "alt": "Partner"}],
            "links": [{"href": "/services", "text": "Services"}],
        }]}
        self.research = {
            "company_facts": {
                "services": ["Määräaikaishuolto", "Pikahuolto"],
                "contact": {"phone": "040 123 4567", "email": "info@example.org",
                            "address": "Työpajatie 12, Kotka"},
            },
            "source_inventory": self.inventory,
        }
        self.html = """<!doctype html><html><body><header>Brand</header><main>
            <h1>Auton huolto</h1>
            <p>Määräaikaishuolto ja Pikahuolto.</p>
            <p>Työpajatie 12, Kotka</p>
            <a href="tel:+358401234567">Soita</a>
            <a href="mailto:info@example.org">Sähköposti</a>
            </main></body></html>"""

    def test_detects_missing_critical_details_before_build_is_saved(self):
        result = audit_content_parity("<main>Määräaikaishuolto</main>",
                                      self.research, require_source_review=False)
        missing = {x["field"] for x in result["missing"]}
        self.assertIn("service", missing)
        self.assertIn("contact_phone", missing)
        self.assertIn("contact_email", missing)
        self.assertIn("contact_address", missing)
        self.assertFalse(result["pass"])

    def test_valid_details_pass_factual_checks_but_need_old_site_approval(self):
        result = audit_content_parity(self.html, self.research)
        self.assertFalse(result["missing"])
        self.assertFalse(result["pass"])
        self.assertTrue(result["review_required"])
        self.assertEqual(result["automated_fields_checked"], 5)

    def test_review_is_tied_to_exact_source_snapshot_and_every_page(self):
        review = {
            "approved": True, "reviewer_kind": "human", "reviewer": "Owner",
            "checked_at": "2026-11-02T14:00:00+02:00",
            "source_urls": ["https://sample.example.org/"],
            "snapshot_sha256": source_inventory_sha256(self.inventory),
        }
        approved = dict(self.research, content_inventory_review=review)
        result = audit_content_parity(self.html, approved)
        self.assertTrue(result["pass"], result)
        self.inventory["pages"][0]["text"] += "New service was added"
        self.assertFalse(audit_content_parity(self.html, approved)["pass"])

    def test_source_specific_requirement_and_partner_image(self):
        reqs = [{
            "label": "Fixus logo", "kind": "image", "value": "/partner.svg",
            "source_url": "https://sample.example.org/",
        }, {
            "label": "Guarantee terms", "kind": "text",
            "value": "Takuu 12 kuukautta", "source_url": "https://sample.example.org/",
        }]
        data = dict(self.research, content_requirements=reqs)
        result = audit_content_parity(self.html, data, require_source_review=False)
        self.assertEqual(len(result["missing"]), 2)
        self.assertFalse(result["pass"])

    def test_unknown_source_requirement_cannot_be_accepted_as_verified(self):
        data = dict(self.research, content_requirements=[{
            "label": "Unverified", "value": "Invented", "kind": "text",
            "source_url": "https://other.example.net/"
        }])
        result = audit_content_parity(self.html, data, require_source_review=False)
        self.assertTrue(result["review_required"])
        self.assertFalse(result["pass"])

    def test_no_site_verified_data_is_not_forced_to_invent_a_history(self):
        data = {"company_facts": {"services": []}, "research_mode": "verified_no_website"}
        result = audit_content_parity("<html><body><main>Welcome</main></body></html>", data)
        self.assertTrue(result["pass"])
        self.assertEqual(result["automated_fields_checked"], 0)

    def test_tag_and_html_hidden_text_cannot_fake_visible_services(self):
        html = "<html><body><style>.x:before{content:'Pikahuolto'}</style><main>Hi</main></body></html>"
        result = audit_content_parity(html, self.research, require_source_review=False)
        self.assertTrue(any(x["label"] == "Pikahuolto" for x in result["missing"]))

    def test_company_facts_not_required_when_never_verified(self):
        html = "<main>No prices or opening hours shown.</main>"
        data = {"company_facts": {"services": []}}
        self.assertTrue(audit_content_parity(html, data)["pass"])


if __name__ == "__main__":
    unittest.main()

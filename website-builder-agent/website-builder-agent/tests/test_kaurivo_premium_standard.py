"""Premium standard regression tests; 0 web, AI, cookies, emails or credits."""
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from utils.kaurivo_premium_site import inspect_site_file
from utils.kaurivo_premium_sales import (
    agreement_gate, demo_improvement_packet, delivery_gate, funnel_metrics,
)


GOOD = """<!doctype html><html lang="fi"><head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width">
<title>Testiyrityksen kotisivut</title>
<meta name="description" content="Testiyrityksen varmistettuihin palveluihin tutustuminen.">
<style>@media (max-width:600px){main{padding:1rem}} @media (prefers-reduced-motion:reduce){*{animation:none}}</style>
</head><body><nav><a href="#main">Sisältö</a></nav><main id="main">
<h1>Testiyritys</h1><p>Esimerkkisivu.</p>
<a href="mailto:verified@example.org">Yhteystiedot</a>
<form id="contact" action="https://example.org/submit"><label for="name">Nimi</label>
<input id="name" name="name"></form></main></body></html>"""


class StaticPreflightTests(unittest.TestCase):
    def run_html(self, html, production=False):
        with TemporaryDirectory() as d:
            p = Path(d) / "index.html"
            p.write_text(html, encoding="utf-8")
            return inspect_site_file(p, production=production)

    def test_clean_preview_passes_structural_checks_not_live_verification(self):
        result = self.run_html(GOOD)
        self.assertTrue(result["pass"], result["errors"])
        self.assertIn("No Lighthouse", result["limitations"][0])

    def test_missing_links_and_anchors_block(self):
        html = GOOD.replace('href="#main"', 'href="#does-not-exist"').replace(
            "</main>", '<img src="not-found.png" alt="Kuva"></main>')
        result = self.run_html(html)
        self.assertFalse(result["pass"])
        self.assertTrue(any("Missing local reference" in x for x in result["errors"]))
        self.assertTrue(any("Broken same-page anchor" in x for x in result["errors"]))

    def test_publication_rejects_noindex(self):
        html = GOOD.replace("</head>", '<meta name="robots" content="noindex,nofollow"></head>')
        self.assertTrue(self.run_html(html)["pass"])
        self.assertFalse(self.run_html(html, production=True)["pass"])

    def test_missing_accessibility_and_semantics_block(self):
        html = GOOD.replace('<label for="name">Nimi</label>', '').replace('<h1>Testiyritys</h1>', '')
        result = self.run_html(html)
        self.assertFalse(result["pass"])
        self.assertTrue(any("Unlabelled" in x for x in result["errors"]))

    def test_kaurivo_public_home_and_demo_review_static_preflight(self):
        root = Path(__file__).resolve().parents[1] / "docs" / "kaurivo"
        for page in (root / "index.html", root / "demo-review" / "index.html"):
            with self.subTest(page=page.name):
                result = inspect_site_file(page, site_root=root)
                self.assertTrue(result["pass"], result["errors"])

    def test_no_files_outside_root(self):
        with TemporaryDirectory() as d:
            root = Path(d) / "site"
            root.mkdir()
            page = root / "index.html"
            page.write_text(GOOD.replace("</main>", '<a href="../secret.txt">bad</a></main>'))
            self.assertFalse(inspect_site_file(page, site_root=root)["pass"])


class EvidenceAndDeliveryTests(unittest.TestCase):
    def _record(self):
        return {
            "url": "https://client.example.org",
            "research": {
                "company_facts": {"name": "Client Oy", "industry": "kampaamo"},
                "design_benchmark": [
                    {"url": f"https://peer{i}.example.org", "industry_match": {
                        "same_industry": True, "target_industry": "kampaamo"},
                     "observations": ["a"], "apply": ["b"], "avoid": ["c"]}
                    for i in range(3)
                ],
                "verified_improvements": [
                    {"source_url": f"https://client.example.org/page{i}", "human_verified": True,
                     "before": "Yhteystiedot ovat vaikeasti löydettävissä.",
                     "after_proposal": "Ehdotetaan selkeää yhteystietonappia."}
                    for i in range(3)
                ],
            },
        }

    def test_demo_pack_uses_verified_evidence(self):
        packet = demo_improvement_packet(self._record())
        self.assertTrue(packet["ready_for_human_sales_review"], packet["issues"])
        self.assertFalse(packet["send_authorized"])
        self.assertEqual(packet["design"]["brand_policy"], "keep_existing_identity")

    def test_unverified_or_wrong_site_evidence_blocked(self):
        record = self._record()
        record["research"]["verified_improvements"][0]["human_verified"] = False
        record["research"]["verified_improvements"][1]["source_url"] = "https://other.example.org"
        self.assertFalse(demo_improvement_packet(record)["ready_for_human_sales_review"])
        record["research"]["design_benchmark"] = []
        self.assertFalse(demo_improvement_packet(record)["ready_for_human_sales_review"])

    def test_no_site_needs_independent_absence_evidence(self):
        record = self._record()
        record["url"] = ""
        self.assertFalse(demo_improvement_packet(record)["ready_for_human_sales_review"])
        record["site_verification"] = {
            "confirmed_absent": True, "verified_by_human": True,
            "source_url": "https://registry.example.org/verified-check",
        }
        for improvement in record["research"]["verified_improvements"]:
            improvement["source_url"] = "https://registry.example.org/verified-check"
        self.assertTrue(demo_improvement_packet(record)["ready_for_human_sales_review"])

    def test_demo_review_form_exposes_goal_editing_and_brand_choices(self):
        page = (Path(__file__).resolve().parents[1] / "docs" / "kaurivo"
                / "demo-review" / "index.html").read_text(encoding="utf-8")
        translation = (Path(__file__).resolve().parents[1] / "docs" / "kaurivo"
                       / "assets" / "i18n.js").read_text(encoding="utf-8")
        for name in ("main_goal", "editing_priority", "brand_preference"):
            self.assertIn('name="' + name + '"', page)
        self.assertIn("These are planning preferences", page)
        self.assertIn("Verkkosivun tärkein tavoite", translation)

    def test_agreement_requires_all_terms_and_scope_version(self):
        self.assertFalse(agreement_gate({})["ready_to_start_work"])
        terms = {
            "signed_or_explicit_written_acceptance": True,
            "fixed_scope_and_page_count": True,
            "total_price_and_vat_treatment": True,
            "deposit_and_final_payment_terms": True,
            "revision_rounds_and_change_requests": True,
            "approved_brand_and_content_rights": True,
            "hosting_domain_and_renewal_owner": True,
            "cms_platform_and_editing_scope": True,
            "privacy_cookie_and_form_responsibilities": True,
            "delivery_support_and_acceptance_terms": True,
            "scope_version": "offer-2026-01"
        }
        self.assertTrue(agreement_gate(terms)["ready_to_start_work"])
        terms["privacy_cookie_and_form_responsibilities"] = False
        self.assertFalse(agreement_gate(terms)["ready_to_start_work"])

    def test_static_demo_never_passes_delivery(self):
        r = delivery_gate({"build": {"version": 1}}, {"pass": True, "warnings": []})
        self.assertFalse(r["ready_to_deliver"])
        self.assertTrue(any("CMS" in x or "editor" in x.lower() for x in r["issues"]))

    def test_metrics_only_recorded_states(self):
        result = funnel_metrics({
            "a": {"status": "found", "owner_review": {"decision": "select"},
                  "approval": {"approved": True}},
            "b": {"status": "contacted", "sale": {"status": "won", "source_verified": True},
                  "delivery": {"customer_acceptance": True}},
            "c": {"status": "found", "outreach": {"draft": "looks good"}},
        })
        self.assertEqual(result["counts"]["discovered"], 3)
        self.assertEqual(result["counts"]["contacted"], 1)
        self.assertEqual(result["counts"]["won"], 1)
        self.assertEqual(result["conversion_rates"]["won_per_contacted_pct"], 100.0)
        self.assertIsNone(funnel_metrics({})["conversion_rates"]["won_per_contacted_pct"])


if __name__ == "__main__":
    unittest.main()

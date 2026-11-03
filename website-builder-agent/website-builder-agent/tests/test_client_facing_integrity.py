"""Company-agnostic regressions from repeated Kaurivo source/branding UX failures.

No source copying, real company identifiers, API usage or fake aesthetic scores.
"""
from __future__ import annotations

import unittest

from utils.client_facing_integrity import audit_client_facing_integrity
from utils.content_parity import source_inventory_sha256
from utils.premium_quality_gate import site_digest
from utils.universal_quality import audit_universal_standards


def site(main: str, *, header: str = "<header><b>Real business name</b></header>",
         footer: str = "<footer>Street and contact</footer>") -> str:
    return (f'<!doctype html><html lang="fi"><body>{header}'
            f'<main><h1>Real service business</h1>{main}</main>{footer}</body></html>')


class ClientFacingIntegrityTests(unittest.TestCase):
    def audit(self, pages, research=None, stage="internal_demo"):
        return audit_client_facing_integrity(pages, research or {}, stage=stage)

    def test_customer_site_rejects_research_notes_in_both_languages(self):
        sentences = [
            "Puhelinnumero on yrityksen omilta yhteystietosivuilta.",
            "Kuusi työtä alkuperäiseltä hinnastosivulta.",
            "6 työtä alkuperäiseltä hinnastosivulta.",
            "Kuvat on siirretty alkuperäiseltä sivulta.",
            "Alkuperäisen verkkosivuston palvelut julkaistiin.",
            "Sivulla on päiväämätön lomailmoitus.",
            "Prices taken from the original website.",
            "As described in our source inventory.",
        ]
        for sentence in sentences:
            with self.subTest(sentence=sentence):
                report = self.audit({"index.html": site("<p>" + sentence + "</p>")})
                self.assertFalse(report["pass"], report)
                self.assertIn("research_leak", [i["category"] for i in report["blocking"]])

    def test_hidden_research_script_is_not_customer_copy(self):
        html = site('<p>Voit huollattaa pyörän ja jalkineet täällä.</p>'
                    '<script>const info = "6 työtä alkuperäiseltä hinnastosivulta";</script>')
        self.assertTrue(self.audit({"index.html": html})["pass"])

    def test_explicit_internal_research_component_cannot_be_homepage(self):
        html = site('<aside class="source-note">Tiedot ovat tutkimusmuistiinpanoista.</aside>')
        report = self.audit({"index.html": html})
        self.assertFalse(report["pass"])
        self.assertIn("visible_internal_note", [i["category"] for i in report["blocking"]])

    def test_discreet_demo_disclaimer_outside_main_is_allowed_in_demo_only(self):
        note = '<footer data-demo-disclosure="true">Itsenäinen suunnitteludemo.</footer>'
        html = site("<p>Oikea palvelukuvaus.</p>", footer=note)
        self.assertTrue(self.audit({"index.html": html})["pass"])
        release = self.audit({"index.html": html}, stage="client_release")
        self.assertFalse(release["pass"])
        self.assertIn("demo_note_in_release", [i["category"] for i in release["blocking"]])

    def test_unsourced_automatic_initial_mark_is_not_brand_logo(self):
        header = ('<header><a href="/"><span class="wordmark-seal">R.</span>'
                  '<strong>Repair workshop</strong></a></header>')
        report = self.audit({"index.html": site("Real service", header=header)})
        self.assertFalse(report["pass"])
        self.assertEqual(report["blocking"][0]["category"], "unsourced_brand_mark")
        universal = audit_universal_standards(site("Real service", header=header))
        self.assertIn("verified_brand_marks", universal["blocking_problems"])

    def test_plain_company_name_wordmark_is_not_a_fake_initial(self):
        header = "<header><a href='/'>Real Repair Workshop</a></header>"
        self.assertTrue(self.audit({"index.html": site("Real service", header=header)})["pass"])

    def test_client_source_build_approved_monogram_is_accepted_not_auto_inferred(self):
        header = ('<header><a href="/"><span class="brand-monogram">R</span>'
                  '<strong>Repair workshop</strong></a></header>')
        pages = {"index.html": site("<p>Service</p>", header=header)}
        research = {"source_inventory": {"pages": [{
            "url": "https://example.org/", "text": "Real workshop"
        }]}}
        research["approved_new_brand_mark"] = {
            "approved": True, "reviewer_kind": "client", "reviewer": "Owner",
            "checked_at": "2026-11-03",
            "source_sha256": source_inventory_sha256(research["source_inventory"]),
            "build_sha256": site_digest(pages),
        }
        self.assertTrue(self.audit(pages, research)["pass"])
        pages["index.html"] += " "
        self.assertFalse(self.audit(pages, research)["pass"])

    def test_decorative_street_map_does_not_become_real_map_by_link(self):
        faux_map = ('<section class="map-panel"><svg class="map-drawing">'
                    '<path d="M0 0L10 10"/></svg>'
                    '<div class="map-pin">R.</div>'
                    '<a href="https://www.google.com/maps/search/?api=1&amp;query=Street">Map</a>'
                    '</section>')
        report = self.audit({"index.html": site(faux_map)})
        self.assertFalse(report["pass"], report)
        self.assertIn("misleading_map", [i["category"] for i in report["blocking"]])
        universal = audit_universal_standards(site(faux_map))
        self.assertIn("real_location_aids", universal["blocking_problems"])

    def test_real_map_embed_and_source_address_do_not_trigger_faux_map_rule(self):
        real = ('<section><address>Street 1, Helsinki</address>'
                '<iframe title="Map to the shop" '
                'src="https://www.google.com/maps/embed?pb=sourcevalue"></iframe>'
                '</section>')
        self.assertTrue(self.audit({"index.html": site(real)})["pass"])

    def test_fake_map_without_svg_requires_verified_geospatial_evidence(self):
        faux = '<div class="map-panel"><span class="map-pin">R</span><div class="location-label">Street 1</div></div>'
        report = self.audit({"index.html": site(faux)})
        self.assertFalse(report["pass"])

    def test_repeated_generic_headlines_require_editorial_check_not_fake_score(self):
        pages = {
            "index.html": site("<h2>Laadukasta palvelua</h2>"),
            "palvelut.html": site("<h2>Tule käymään</h2>"),
        }
        result = self.audit(pages)
        self.assertTrue(result["pass"])
        self.assertIn("template_headlines", [i["category"] for i in result["pending"]])
        self.assertIn("editorial_visual_balance",
                      audit_universal_standards(pages["index.html"],
                                                rendered_pages=pages)["pending_evidence"])

    def test_real_source_note_is_not_whitelisted_in_body_by_demo_status(self):
        pages = {"index.html": site('<p>Yrityksen omilta verkkosivuilta.</p>')}
        self.assertFalse(self.audit(pages, stage="internal_demo")["pass"])


if __name__ == "__main__":
    unittest.main()

"""Universal sector recognition regressions on fictitious businesses."""
import unittest

from utils.industry_workflow import sector_guidance
from utils.sector_presence import audit_sector_presence, repeated_text_strips, check_blind_sector_reviews
from utils.universal_quality import audit_universal_standards
from utils.premium_quality_gate import site_digest
from utils.content_parity import source_inventory_sha256


def html(inner):
    return "<html><body><header>Workshop</header><main>" + inner + "</main></body></html>"


def research():
    return {"company_facts": {"industry": "polkupyörähuolto"},
            "source_inventory": {"pages": [{
                "url": "https://synthetic.example.org/",
                "text": "Pyörän huolto ja rengastyöt",
            }]}}


def review(pages, data, person):
    return {"reviewer_id": person, "reviewer_kind": "independent_human",
            "independence_human_verified": True, "logo_masked": True,
            "recognized_service": True, "recognized_sector": "bicycle",
            "wrong_industry_impression": False,
            "brand_cues_recognized": True, "company_specific_layout": True,
            "evidence_reference": "synthetic-reference", "routes_reviewed": list(pages),
            "viewport_widths": [320, 390, 768, 1440],
            "build_sha256": site_digest(pages),
            "source_sha256": source_inventory_sha256(data["source_inventory"])}


class SectorRecognitionTests(unittest.TestCase):
    def test_bicycle_specialism_is_identified(self):
        self.assertEqual(sector_guidance("pyörähuolto")["sector"], "bicycle")
        self.assertEqual(sector_guidance("bike repair")["sector"], "bicycle")
        self.assertEqual(sector_guidance("ravintola")["sector"], "restaurant")

    def test_generic_institutional_copy_fails_first_view_task(self):
        page = html("<section><h1>Osaamista tulevaisuuteen</h1>"
                    "<p>Löydä paikkasi uudistuvassa yhteisössä.</p></section>")
        report = audit_sector_presence({"index.html": page}, research())
        self.assertEqual(report["blocking"][0]["category"],
                         "missing_bicycle_first_view")
        self.assertIn("sector_recognition",
                      audit_universal_standards(page,research())["blocking_problems"])

    def test_real_bike_service_is_not_rejected(self):
        page = html("<section><h1>Polkupyörien huollot</h1>"
                    "<p>Rengastyöt ja hinnasto</p></section>")
        report = audit_sector_presence({"index.html": page}, research())
        self.assertFalse(report["blocking"])
        self.assertTrue(report["pending"])

    def test_generic_text_strips_require_review_not_hard_failure(self):
        section = "<section><h2>Palvelut</h2><p>Teksti</p></section>"
        page = html(section * 4)
        report = audit_sector_presence({"index.html": page}, {})
        self.assertEqual(report["repeated_text_strips"]["index.html"][0]["count"], 4)
        self.assertFalse(report["blocking"])
        self.assertTrue(any("strips" in x for x in report["pending"]))

    def test_product_images_do_not_trigger_strips(self):
        s = "<section><h2>Tuote</h2><img src='a.jpg'></section>"
        self.assertFalse(repeated_text_strips(html(s * 4)))

    def test_blind_reviews_require_two_independent_people(self):
        pages = {"index.html":html("<section><h1>Pyörähuolto</h1></section>")}
        data = research()
        a,b = review(pages,data,"one"), review(pages,data,"two")
        self.assertFalse(check_blind_sector_reviews([a],pages,data,"bicycle")["pass"])
        self.assertTrue(check_blind_sector_reviews([a,b],pages,data,"bicycle")["pass"])
        b["wrong_industry_impression"] = True
        self.assertFalse(check_blind_sector_reviews([a,b],pages,data,"bicycle")["pass"])

    def test_stale_build_or_source_invalidates_review(self):
        pages = {"index.html":html("<section><h1>Pyörähuolto</h1></section>")}
        data = research()
        records = [review(pages,data,n) for n in ("one","two")]
        changed = {"index.html":pages["index.html"]+" "}
        self.assertFalse(check_blind_sector_reviews(records,changed,data,"bicycle")["pass"])
        data["source_inventory"]["pages"][0]["text"] += " nyt"
        self.assertFalse(check_blind_sector_reviews(records,pages,data,"bicycle")["pass"])


if __name__ == "__main__":
    unittest.main()

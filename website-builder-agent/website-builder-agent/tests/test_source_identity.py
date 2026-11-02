"""No-credit cross-client regression: preserve verified brand + review evidence."""
import unittest
from utils.fetch import extract_text_and_meta
from utils.industry_workflow import crawl_original_website, create_industry_brief
from utils.source_identity import (
    extract_source_identity, audit_source_reviews, validate_brand_preservation_plan
)
from utils.universal_quality import audit_universal_standards
from utils.content_parity import source_inventory_sha256


SOURCE_URL = "https://local-business.example.org/"
SOURCE_HTML = """<!doctype html><html lang="fi"><head>
<meta name="theme-color" content="#173f34"><title>Real identity</title>
</head><body>
<header><a href="/"><img src="/assets/real-logo.svg" alt="Company original logo"></a></header>
<main><h1>Authentic service business</h1>
<section class="reviews"><article class="review-card">
<blockquote>Palvelu oli todella sujuvaa ja koira viihtyi hyvin.</blockquote>
<div class="stars" aria-label="5/5 tähteä">★★★★★</div>
<cite>Oikea asiakas</cite></article></section></main></body></html>"""
QUOTE = "Palvelu oli todella sujuvaa ja koira viihtyi hyvin."


class SourceIdentityTests(unittest.TestCase):
    def source_research(self):
        source = extract_text_and_meta(SOURCE_HTML, base_url=SOURCE_URL)
        inventory = crawl_original_website(
            SOURCE_URL, lambda _: self.fail("must reuse initial source"), first_page=source
        )
        return {"source_inventory": inventory}

    def test_original_logo_color_quote_and_five_stars_captured(self):
        profile = extract_source_identity(SOURCE_HTML, SOURCE_URL)
        self.assertEqual(profile["theme_color"], "#173f34")
        self.assertEqual(profile["original_logo_candidates"],
                         [SOURCE_URL + "assets/real-logo.svg"])
        self.assertEqual(profile["reviews"][0]["quote"], QUOTE)
        self.assertEqual(profile["reviews"][0]["stars"], 5)
        self.assertEqual(profile["reviews"][0]["author"], "Oikea asiakas")

    def test_crawler_and_industry_brief_keep_source_evidence(self):
        research = self.source_research()
        self.assertEqual(research["source_inventory"]["pages"][0]["source_identity"]
                         ["reviews"][0]["stars"], 5)
        brief = create_industry_brief({"url": SOURCE_URL}, research)
        self.assertEqual(brief["source_pages"][0]["source_identity"]
                         ["theme_color"], "#173f34")
        self.assertTrue(brief["source_pages"][0]["source_identity"]
                        ["original_logo_candidates"])

    def test_missing_star_fails_even_if_review_quote_survives(self):
        research = self.source_research()
        html = f'<html><body><main><blockquote>{QUOTE}</blockquote></main></body></html>'
        report = audit_source_reviews({"index.html": html}, research)
        self.assertIn("lost_verified_review_stars",
                      [item["kind"] for item in report["missing"]])
        global_report = audit_universal_standards(html, research)
        self.assertIn("real_testimonials", global_report["blocking_problems"])

    def test_missing_original_review_fails(self):
        research = self.source_research()
        report = audit_source_reviews({"index.html": "<main>No reviews</main>"}, research)
        self.assertIn("lost_source_testimonial", [x["kind"] for x in report["missing"]])

    def test_exact_quote_and_exact_stars_pass_on_any_generated_page(self):
        research = self.source_research()
        page = ('<html><body><article class="testimonial"><blockquote>'
                + QUOTE + '</blockquote><span aria-label="5/5 tähteä">★★★★★</span>'
                '</article></body></html>')
        report = audit_source_reviews({"index.html": "<main>Home</main>",
                                       "reviews.html": page}, research)
        self.assertTrue(report["pass"], report)
        self.assertEqual(report["original_review_count"], 1)

    def test_no_rating_on_original_does_not_create_fake_stars(self):
        html = SOURCE_HTML.replace('<div class="stars" aria-label="5/5 tähteä">★★★★★</div>', "")
        profile = extract_source_identity(html, SOURCE_URL)
        self.assertIsNone(profile["reviews"][0]["stars"])
        research = {"source_inventory": {"pages": [{
            "url": SOURCE_URL, "source_identity": profile}]}}
        output = "<main><blockquote>" + QUOTE + "</blockquote></main>"
        self.assertTrue(audit_source_reviews({"index.html": output}, research)["pass"])

    def test_dynamic_external_review_widget_is_pending_not_fabricated(self):
        html = SOURCE_HTML + '<iframe src="https://widgets.example.net/reviews"></iframe>'
        profile = extract_source_identity(html, SOURCE_URL)
        self.assertTrue(profile["dynamic_review_widget"])
        research = {"source_inventory": {"pages": [{
            "url": SOURCE_URL, "source_identity": profile}]}}
        report = audit_source_reviews({"index.html": f"<main>{QUOTE} ★★★★★</main>"}, research)
        self.assertFalse(report["pass"])
        self.assertTrue(report["pending"])

    def test_brand_plan_cannot_ignore_logo_or_color(self):
        research = self.source_research()
        with self.assertRaisesRegex(RuntimeError, "brand preservation plan"):
            validate_brand_preservation_plan(research)
        identity = research["source_inventory"]["pages"][0]["source_identity"]
        plan = {
            "logo_treatment": "Preserve the exact original sourced mark with licensed reuse.",
            "color_treatment": "Retain the original green in the navigation and accents.",
            "typography_treatment": "Verify and preserve recognizable letterform proportions.",
            "photography_treatment": "Use only approved real business photographs.",
            "source_urls": [SOURCE_URL],
            "original_logo_candidates": identity["original_logo_candidates"],
            "original_theme_colors": [identity["theme_color"]],
        }
        research["brand_preservation_plan"] = plan
        self.assertTrue(validate_brand_preservation_plan(research)["required"])
        research["brand_preservation_plan"]["original_logo_candidates"] = []
        with self.assertRaisesRegex(RuntimeError, "logo"):
            validate_brand_preservation_plan(research)

    def test_original_price_row_and_faq_are_structured(self):
        from utils.source_identity import extract_price_faq_evidence
        source = """<html><body><table>
        <tr><td>Labradoodle mini/medium</td><td>93–120 €</td></tr>
        </table><details><summary>Voinko varata ajan?</summary>
        <p>Varaa puhelimitse.</p></details></body></html>"""
        data = extract_price_faq_evidence(source)
        self.assertEqual(data["price_rows"][0]["label"], "Labradoodle mini/medium")
        self.assertEqual(data["price_rows"][0]["price"], "93–120 €")
        self.assertEqual(data["faq_questions"], ["Voinko varata ajan?"])

    def test_lost_price_breed_and_faq_fail(self):
        from utils.source_identity import extract_price_faq_evidence, audit_price_faq_preservation
        source = """<table><tr><td>Labradoodle mini/medium</td>
                    <td>93–120 €</td></tr></table>
                    <details><summary>Mitä mukaan käynnille?</summary><p>Turkki</p></details>"""
        research = {"source_inventory": {"pages": [{
            "url": SOURCE_URL, "price_faq_evidence": extract_price_faq_evidence(source)}]}}
        new = "<main><article>Lagotto mini/medium: 93–120 €</article></main>"
        report = audit_price_faq_preservation({"index.html": new}, research)
        self.assertFalse(report["pass"])
        self.assertEqual(len(report["missing"]), 2)
        universal = audit_universal_standards(new, research)
        self.assertIn("content_parity", universal["blocking_problems"])

    def test_source_price_row_passes_when_label_and_price_stay_together(self):
        from utils.source_identity import extract_price_faq_evidence, audit_price_faq_preservation
        source = "<table><tr><td>Labradoodle mini/medium</td><td>93–120 €</td></tr></table>"
        research = {"source_inventory": {"pages": [{
            "url": SOURCE_URL, "price_faq_evidence": extract_price_faq_evidence(source)}]}}
        new = "<main><article>Labradoodle mini/medium — 93–120 €</article></main>"
        self.assertTrue(audit_price_faq_preservation({"index.html": new}, research)["pass"])

    def test_review_evidence_alters_source_approval_hash(self):
        research = self.source_research()
        inventory = research["source_inventory"]
        before = source_inventory_sha256(inventory)
        inventory["pages"][0]["source_identity"]["reviews"][0]["stars"] = 4
        self.assertNotEqual(before, source_inventory_sha256(inventory))


if __name__ == "__main__":
    unittest.main()

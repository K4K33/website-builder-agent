"""Cross-industry social-proof regressions; all companies here are synthetic."""
from __future__ import annotations

import unittest

from utils.content_parity import source_inventory_sha256
from utils.premium_quality_gate import site_digest
from utils.trust_claims import audit_trust_claims
from utils.universal_quality import audit_universal_standards


QUOTE = "My actual appointment was easy to book and the service was careful."


def site(stuff: str) -> str:
    return ('<!doctype html><html><body><header>Synthetic Workshop</header>'
            f'<main><h1>Repairs</h1>{stuff}</main><footer>Contact</footer>'
            '</body></html>')


def card(quote: str = QUOTE, stars: int | None = 5) -> str:
    rating = (f'<span class="rating" aria-label="{stars} / 5 stars">'
              '★★★★★</span>' if stars is not None else "")
    return (f'<article class="testimonial"><p class="testimonial-text">{quote}</p>'
            f'{rating}</article>')


def source_research(stars: int | None) -> dict:
    return {"source_inventory": {"pages": [{
        "url": "https://fictional.example.org/",
        "source_identity": {"reviews": [{
            "quote": QUOTE, "stars": stars,
            "source_url": "https://fictional.example.org/",
        }]},
    }]}}


def signoff(pages: dict[str, str], research: dict) -> dict:
    return {
        "approved": True, "reviewer_kind": "client",
        "reviewer": "Synthetic owner",
        "approved_at": "2026-11-03",
        "evidence_reference": "fixture-only-approval-id",
        "build_sha256": site_digest(pages),
        "source_sha256": source_inventory_sha256(research["source_inventory"])
        if (research.get("source_inventory") or {}).get("pages") else "",
    }


class TrustClaimsTests(unittest.TestCase):
    def test_fabricated_five_star_review_is_blocked_even_on_a_no_site_company(self):
        pages = {"index.html": site(card())}
        report = audit_trust_claims(pages, {"research_mode": "verified_no_website"})
        self.assertFalse(report["pass"])
        self.assertEqual(report["blocking"][0]["category"], "unsourced_customer_review")
        universal = audit_universal_standards(pages["index.html"],
                                              {"research_mode": "verified_no_website"})
        self.assertIn("source_bound_social_proof", universal["blocking_problems"])
        self.assertFalse(universal["automated_pass"])

    def test_original_quote_with_true_stars_is_allowed(self):
        pages = {"index.html": site(card(stars=4))}
        report = audit_trust_claims(pages, source_research(4))
        self.assertTrue(report["pass"], report)
        universal = audit_universal_standards(pages["index.html"], source_research(4))
        self.assertNotIn("source_bound_social_proof", universal["blocking_problems"])

    def test_original_unrated_review_cannot_receive_fabricated_five_stars(self):
        pages = {"index.html": site(card(stars=5))}
        report = audit_trust_claims(pages, source_research(None))
        self.assertFalse(report["pass"])
        self.assertEqual(report["blocking"][0]["original_stars"], [None])

    def test_original_four_star_review_cannot_be_upgraded_to_five(self):
        pages = {"index.html": site(card(stars=5))}
        report = audit_trust_claims(pages, source_research(4))
        self.assertEqual(report["blocking"][0]["category"], "changed_source_review_rating")

    def test_client_verified_new_quote_is_bound_to_current_build_and_source(self):
        pages = {"index.html": site(card())}
        research = source_research(4)
        research["verified_additional_reviews"] = [{
            "quote": QUOTE, "stars": 5,
            "source_url": "https://reviews.example.org/verified-entry",
            "rights_verified": True,
        }]
        # Quote with existing source evidence must keep its original rating.
        research["source_inventory"]["pages"][0]["source_identity"]["reviews"] = []
        research["additional_reviews_approval"] = signoff(pages, research)
        self.assertTrue(audit_trust_claims(pages, research)["pass"])
        changed = {"index.html": pages["index.html"] + " "}
        self.assertFalse(audit_trust_claims(changed, research)["pass"])
        research["additional_reviews_approval"] = signoff(pages, research)
        research["source_inventory"]["pages"][0]["url"] = "https://other.example.org/"
        self.assertFalse(audit_trust_claims(pages, research)["pass"])

    def test_new_client_review_requires_rights_and_a_real_evidence_url(self):
        pages = {"index.html": site(card())}
        research = {"verified_additional_reviews": [{
            "quote": QUOTE, "stars": 5,
            "source_url": "guess", "rights_verified": True,
        }]}
        research["additional_reviews_approval"] = signoff(pages, research)
        self.assertFalse(audit_trust_claims(pages, research)["pass"])
        research["verified_additional_reviews"][0]["source_url"] = "https://example.org/reviews/1"
        self.assertTrue(audit_trust_claims(pages, research)["pass"])
        research["verified_additional_reviews"][0]["rights_verified"] = False
        self.assertFalse(audit_trust_claims(pages, research)["pass"])

    def test_unverified_google_rating_summary_is_blocked(self):
        pages = {"index.html": site('<aside class="rating-summary">Google 4.9/5</aside>')}
        report = audit_trust_claims(pages)
        self.assertEqual(report["blocking"][0]["category"], "unverified_aggregate_rating")
        universal = audit_universal_standards(pages["index.html"])
        self.assertIn("source_bound_social_proof", universal["blocking_problems"])

    def test_verified_aggregate_rating_badge_requires_exact_build_approval(self):
        pages = {"index.html": site('<aside class="rating-summary">Google 4.9/5</aside>')}
        research = {
            "verified_aggregate_ratings": [{
                "visible_text": "Google 4.9/5",
                "source_url": "https://ratings.example.org/synthetic-company",
                "source_verified": True,
            }],
        }
        research["aggregate_ratings_approval"] = signoff(pages, research)
        self.assertTrue(audit_trust_claims(pages, research)["pass"])
        changed = {"index.html": pages["index.html"].replace("4.9/5", "5/5")}
        self.assertFalse(audit_trust_claims(changed, research)["pass"])

    def test_per_quote_star_icon_is_not_misclassified_as_global_rating(self):
        pages = {"index.html": site(
            '<article class="testimonial"><p class="testimonial-text">' + QUOTE + '</p>'
            '<span class="rating-badge" aria-label="4 / 5">★★★★</span></article>'
        )}
        report = audit_trust_claims(pages, source_research(4))
        self.assertTrue(report["pass"], report)
        self.assertEqual(report["aggregate_badges_checked"], 0)

    def test_decorative_star_and_generic_blockquote_are_not_customer_reviews(self):
        pages = {"index.html": site(
            '<blockquote>Repair is an art, but it starts with knowing the material.</blockquote>'
            '<p>★ Selected project</p>'
        )}
        self.assertTrue(audit_trust_claims(pages)["pass"])

    def test_uninspectable_review_widget_needs_browser_review(self):
        pages = {"index.html": site('<div class="review-card" data-review="dynamic"></div>')}
        report = audit_trust_claims(pages)
        self.assertFalse(report["pass"])
        self.assertFalse(report["blocking"])
        self.assertTrue(report["pending"])


if __name__ == "__main__":
    unittest.main()

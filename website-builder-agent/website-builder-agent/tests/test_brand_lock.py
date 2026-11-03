"""Cross-sector zero-credit tests for source-first immutable Brand Lock."""
import unittest

from utils.brand_lock import audit_brand_lock
from utils.universal_quality import audit_universal_standards
from utils.premium_quality_gate import site_digest
from utils.content_parity import source_inventory_sha256
from utils.source_identity import extract_source_identity


SOURCE = "https://synthetic.example.org/"


def page(header, favicon=""):
    return ('<!doctype html><html lang="fi"><head>'
            + favicon + '</head><body><header>' + header + '</header>'
            + '<main><h1>Real services</h1></main></body></html>')


def evidence():
    return {"source_inventory": {"pages": [{
        "url": SOURCE,
        "source_identity": {
            "original_logo_candidates": [SOURCE + "assets/logo.svg"],
            "original_favicon_candidates": [SOURCE + "favicon.ico"],
        },
    }]}}


def client_record(pages, research):
    return {
        "approved": True, "reviewer_kind": "client",
        "reviewer": "Synthetic owner", "checked_at": "2026-11-03",
        "source_sha256": source_inventory_sha256(research["source_inventory"]),
        "build_sha256": site_digest(pages),
    }


class BrandLockTests(unittest.TestCase):
    def test_source_logo_in_header_is_identified_not_silently_recreated(self):
        pages = {"index.html": page('<a class="brand" href="/">'
                                    '<img class="logo" alt="Company logo" '
                                    'src="https://synthetic.example.org/assets/logo.svg">'
                                    '</a>')}
        result = audit_brand_lock(pages, evidence())
        self.assertFalse(result["blocking"], result)
        self.assertTrue(result["routes"]["index.html"]["original_logo_in_header"])
        self.assertTrue(result["pending"], "Source identity is not a licence")

    def test_unknown_header_logo_is_hard_blocked_even_if_it_looks_plausible(self):
        pages = {"index.html": page('<a href="/"><img class="brand-logo" '
                                    'src="/invented-company-logo.svg"></a>')}
        result = audit_brand_lock(pages)
        self.assertFalse(result["pass"])
        self.assertEqual(result["blocking"][0]["category"], "unsourced_header_logo")
        universal = audit_universal_standards(pages["index.html"])
        self.assertIn("brand_identity_lock", universal["blocking_problems"])

    def test_fabricated_logo_named_final_or_original_is_still_blocked(self):
        pages = {"index.html": page('<img class="logo" '
                                    'src="/assets/official-original-logo-final.svg">')}
        self.assertTrue(audit_brand_lock(pages)["blocking"])

    def test_company_name_is_safe_fallback_when_original_mark_is_unavailable(self):
        pages = {"index.html": page('<a href="/">Synthetic Example Workshop</a>')}
        result = audit_brand_lock(pages, evidence())
        self.assertFalse(result["blocking"])
        self.assertEqual(result["pending"][0]["category"], "original_brand_fallback_review")

    def test_approved_original_logo_required_on_every_route(self):
        research = evidence()
        research["brand_assets"] = {
            "approved_original_logo_url": SOURCE + "assets/logo.svg"
        }
        pages = {
            "index.html": page('<img class="site-logo" src="' + SOURCE + 'assets/logo.svg">'),
            "contact/index.html": page('<a href="/">Synthetic Example Workshop</a>')
        }
        result = audit_brand_lock(pages, research)
        self.assertEqual(
            [x["route"] for x in result["blocking"]
             if x["category"] == "approved_original_logo_missing_from_header"],
            ["contact/index.html"],
        )

    def test_replacing_a_known_logo_with_made_up_svg_is_blocked(self):
        research = evidence()
        pages = {
            "index.html": page('<a class="brand" href="/">'
                               '<svg class="site-logo" viewBox="0 0 20 20">'
                               '<circle cx="10" cy="10" r="10"/></svg>'
                               '</a>')
        }
        result = audit_brand_lock(pages, research)
        self.assertTrue(any(x["category"] == "invented_graphic_brand_mark"
                            for x in result["blocking"]), result)

    def test_new_svg_brand_mark_requires_current_client_approval(self):
        research = evidence()
        pages = {"index.html": page('<svg class="site-logo"></svg>')}
        research["approved_new_brand_mark"] = client_record(pages, research)
        self.assertFalse(audit_brand_lock(pages, research)["blocking"])
        old_build = {"index.html": pages["index.html"] + " "}
        self.assertTrue(audit_brand_lock(old_build, research)["blocking"])

    def test_brand_colored_one_letter_monogram_without_approval_is_blocked(self):
        pages = {"index.html": page('<div class="identity-badge"><span>K</span></div>')}
        # Unknown CSS should not be used as proof that "K" is the brand mark.
        pages = {"index.html": page('<span class="brand-logo">K</span>')}
        self.assertTrue(any(x["category"] == "invented_graphic_brand_mark"
                            for x in audit_brand_lock(pages)["blocking"]))

    def test_normal_navigation_svg_not_mistaken_for_a_logo(self):
        pages = {"index.html": page('<button aria-label="Menu">'
                                    '<svg class="menu-icon"><path d="M0 0L1 1"/></svg>'
                                    '</button><strong>Example Workshop</strong>')}
        self.assertFalse(audit_brand_lock(pages)["blocking"])

    def test_source_favicon_is_inventoried(self):
        source_html = ('<html><head><link rel="icon" href="/favicon.ico">'
                       '<link rel="apple-touch-icon" href="/icon.png"></head>'
                       '<body><header><img src="/logo.svg" alt="Logo"></header></body></html>')
        data = extract_source_identity(source_html, SOURCE)
        self.assertEqual(data["original_favicon_candidates"],
                         [SOURCE + "favicon.ico", SOURCE + "icon.png"])

    def test_approved_favicon_change_is_a_blocker(self):
        research = evidence()
        research["brand_assets"] = {"approved_favicon_url": SOURCE + "favicon.ico"}
        pages = {"index.html": page('<a href="/">Example Workshop</a>',
                                    '<link rel="icon" href="/invented.ico">')}
        result = audit_brand_lock(pages, research)
        self.assertIn("approved_favicon_replaced",
                      [x["category"] for x in result["blocking"]])

    def test_new_favicon_when_original_exists_needs_client_review(self):
        pages = {"index.html": page('<a href="/">Example Workshop</a>',
                                    '<link rel="icon" href="/generated.svg">')}
        report = audit_brand_lock(pages, evidence())
        self.assertTrue(any(x["category"] == "favicon_identity_review"
                            for x in report["pending"]))
        self.assertFalse(report["blocking"])

    def test_signed_visual_equivalent_replacement_can_be_used(self):
        research = evidence()
        research["brand_assets"] = {
            "approved_original_logo_url": SOURCE + "assets/logo.svg"
        }
        pages = {"index.html": page('<img class="logo" src="/assets/optimized-logo.svg">')}
        sign = client_record(pages, research)
        research["approved_asset_replacements"] = [{
            **sign,
            "original_src": SOURCE + "assets/logo.svg",
            "replacement_src": "/assets/optimized-logo.svg",
            "rights_verified": True,
            "visual_match_verified": True,
        }]
        result = audit_brand_lock(pages, research)
        self.assertFalse(result["blocking"], result)
        research["approved_asset_replacements"][0]["visual_match_verified"] = False
        self.assertTrue(result["routes"]["index.html"]["original_logo_in_header"])
        self.assertTrue(audit_brand_lock(pages, research)["blocking"])

    def test_stale_source_snapshot_invalidates_brand_replacement(self):
        research = evidence()
        pages = {"index.html": page('<img class="logo" src="/assets/optimized-logo.svg">')}
        research["approved_asset_replacements"] = [{
            **client_record(pages, research),
            "original_src": SOURCE + "assets/logo.svg",
            "replacement_src": "/assets/optimized-logo.svg",
            "rights_verified": True, "visual_match_verified": True,
        }]
        self.assertFalse(audit_brand_lock(pages, research)["blocking"])
        research["source_inventory"]["pages"][0]["url"] = "https://changed.example.org/"
        self.assertTrue(audit_brand_lock(pages, research)["blocking"])


if __name__ == "__main__":
    unittest.main()

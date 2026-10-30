"""Offline client brand and CMS delivery contract tests. Never spends API credits."""
import unittest
from unittest.mock import patch
from utils.client_handover import client_design_brief, validate_locked_copy
from agents import builder


class ClientOwnershipTests(unittest.TestCase):
    def test_existing_site_preserves_brand_by_default(self):
        plan = client_design_brief({"website": "https://example.org"})
        self.assertEqual(plan["brand_policy"], "keep_existing_identity")
        self.assertEqual(plan["design_scope"], "major_visual_and_structural_redesign_keep_brand")
        self.assertEqual(plan["redesign_intensity"], "substantial_visible_change")
        self.assertIn("rethink_navigation_hero_layout", plan["layout_policy"])
        self.assertEqual(plan["photo_policy"], "retain_authorized_originals_or_request_rights")
        self.assertTrue(plan["keep_client_logo_by_default"])
        self.assertTrue(plan["keep_original_claims_and_taglines_by_default"])
        self.assertEqual(plan["cms_status"], "not_implemented_in_static_html")

    def test_unconfirmed_rebranding_does_not_override_default(self):
        plan = client_design_brief({
            "url": "https://example.org",
            "client_preferences": {
                "permission_to_rebrand": True, "permission_to_replace_photos": True,
                "existing_colors": ["#ffffff"], "locked_copy": ["Special claim"],
            },
        })
        self.assertEqual(plan["brand_policy"], "keep_existing_identity")
        self.assertEqual(plan["photo_policy"], "retain_authorized_originals_or_request_rights")
        self.assertEqual(plan["locked_copy"], [])
        self.assertEqual(plan["existing_colors_verified_by_client"], [])

    def test_explicit_client_approval_and_strict_copy(self):
        plan = client_design_brief({
            "website": "https://example.org",
            "client_preferences": {
                "verified_with_client": True,
                "permission_to_rebrand": False,
                "permission_to_replace_photos": False,
                "existing_colors": ["#123abc", "blue", "url(data:bad)", "#FFFFFF"],
                "locked_copy": ["Hyvää palvelua vuodesta 1986", "Ainutlaatuinen iskulause"],
                "content_editing": "client_self_service",
            }
        })
        self.assertEqual(plan["brand_policy"], "keep_existing_identity")
        self.assertEqual(plan["existing_colors_verified_by_client"], ["#123abc", "#FFFFFF"])
        self.assertEqual(plan["content_editing_goal"], "client_self_service_required")
        good = "<!doctype html><main><h1>Hyvää palvelua vuodesta 1986</h1><p>Ainutlaatuinen iskulause</p></main>"
        validate_locked_copy(good, plan)
        with self.assertRaisesRegex(RuntimeError, "protected copy"):
            validate_locked_copy(good.replace("Ainutlaatuinen iskulause", "Täysin uusi slogan"), plan)

    def test_no_website_original_design_is_not_a_redesign(self):
        plan = client_design_brief({})
        self.assertEqual(plan["site_type"], "new_site")
        self.assertEqual(plan["brand_policy"], "new_brand_design_requires_review")
        self.assertEqual(plan["design_scope"], "original_full_site_design")
        self.assertEqual(plan["redesign_intensity"], "substantial_visible_change")

    def test_explicit_permission_to_rebrand(self):
        plan = client_design_brief({
            "website": "https://example.org",
            "client_preferences": {"verified_with_client": True, "permission_to_rebrand": True}
        })
        self.assertEqual(plan["brand_policy"], "client_explicitly_permits_brand_change")

    def test_build_and_revision_prompts_include_client_brand_requirements(self):
        self.assertIn("Ulkopuolisten referenssien värit", builder.BUILD_SYSTEM_PROMPT)
        self.assertIn("Säilytä asiakkaan aiempi logo", builder.REVISE_SYSTEM_PROMPT)
        self.assertIn("Brändin säilyttäminen ei tarkoita vanhan sivun", builder.BUILD_SYSTEM_PROMPT)
        self.assertIn("SEN SIJAAN UUDISTA ISOSTI", builder.REVISE_SYSTEM_PROMPT)
        self.assertIn("client_design_brief(company)", __import__("inspect").getsource(builder.build_site))
        self.assertIn("validate_locked_copy(cleaned, brand_brief)", __import__("inspect").getsource(builder.revise_site))
        self.assertIn("validate_locked_copy(cleaned, client_design_brief(company))",
                      __import__("inspect").getsource(builder.run_build_from_response))

    def test_locked_copy_excludes_script_and_style_faking(self):
        brief = {"locked_copy": ["Asiakkaan tärkeä lause"]}
        with self.assertRaisesRegex(RuntimeError, "protected copy"):
            validate_locked_copy("<style>Asiakkaan tärkeä lause</style><main>Uusi lause</main>", brief)

    def test_no_unapproved_admin_claim(self):
        prompt = builder.BUILD_SYSTEM_PROMPT
        self.assertIn("Älä väitä yksittäistä HTML-tiedostoa sisällönhallintajärjestelmäksi", prompt)
        plan = client_design_brief({"website": "https://example.org"})
        self.assertIn("Static HTML is not itself a CMS", plan["cms_delivery"])


if __name__ == "__main__":
    unittest.main()

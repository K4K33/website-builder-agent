"""Every client delivery must have a tested customer-editable CMS.
All tests are offline and free; no external CMS or AI calls.
"""
import unittest
from datetime import date, timedelta
from utils.client_handover import client_design_brief, inspect_client_delivery
import main


def delivery_fixture():
    checked = date.today().isoformat()
    return {
        "website": "https://example.org",
        "build": {"version": 3},
        "qa": {"overall_pass": True, "build_version": 3, "html_sha256": "demo-hash"},
        "approval": {"approved": True, "build_version": 3, "html_sha256": "demo-hash"},
        "delivery": {
            "cms_platform": "wordpress",
            "admin_url": "https://customer.example.org/wp-admin/",
            "published_url": "https://customer.example.org/",
            "verified_at": checked,
            "verified_by_human": True,
            "client_editor_login_tested": True,
            "text_edit_published_tested": True,
            "image_edit_published_tested": True,
            "contact_edit_published_tested": True,
            "mobile_layout_after_edit_tested": True,
            "backup_and_rollback_tested": True,
            "client_owns_editor_access": True,
            "owner_guide_delivered": True,
            "customer_acceptance": True,
            "build_version": 3,
            "html_sha256": "demo-hash",
        }
    }


class RequiredSelfEditingTests(unittest.TestCase):
    def test_all_existing_and_new_sites_have_mandatory_self_editing(self):
        for company in ({}, {"url": "https://example.org"},
                        {"client_preferences": {
                            "verified_with_client": True,
                            "content_editing": "agency_managed"}}):
            brief = client_design_brief(company)
            self.assertEqual(brief["content_editing_goal"], "client_self_service_required")
            self.assertTrue(brief["final_delivery_requires_live_cms"])
            self.assertIn("photos", brief["content_editing_fields"])
            self.assertEqual(brief["cms_status"], "not_implemented_in_static_html")

    def test_unedited_static_demo_not_ready(self):
        result = inspect_client_delivery({"build": {"version": 1}})
        self.assertFalse(result["ready_to_handover"])
        self.assertTrue(result["client_editable"])
        self.assertIn("CMS", " ".join(result["issues"]))

    def test_handover_with_complete_reviewed_evidence(self):
        checked = inspect_client_delivery(delivery_fixture())
        self.assertTrue(checked["ready_to_handover"])
        self.assertEqual(checked["cms_platform"], "wordpress")

    def test_missing_each_critical_requirement_blocks_delivery(self):
        fields = ["verified_by_human", "client_editor_login_tested",
                  "text_edit_published_tested", "image_edit_published_tested",
                  "contact_edit_published_tested", "mobile_layout_after_edit_tested",
                  "backup_and_rollback_tested", "client_owns_editor_access",
                  "owner_guide_delivered", "customer_acceptance"]
        for field in fields:
            with self.subTest(field=field):
                site = delivery_fixture()
                site["delivery"][field] = False
                self.assertFalse(inspect_client_delivery(site)["ready_to_handover"])

    def test_stale_review_and_unapproved_build_block(self):
        site = delivery_fixture()
        site["delivery"]["verified_at"] = (date.today() - timedelta(days=65)).isoformat()
        self.assertFalse(inspect_client_delivery(site)["ready_to_handover"])
        site = delivery_fixture()
        site["build"]["version"] = 4
        self.assertFalse(inspect_client_delivery(site)["ready_to_handover"])
        site = delivery_fixture()
        site["approval"]["approved"] = False
        self.assertFalse(inspect_client_delivery(site)["ready_to_handover"])

    def test_non_https_urls_and_unknown_platform_block(self):
        for field, bad in [("admin_url", "http://localhost:8000"),
                           ("published_url", "https://user:secret@example.org/"),
                           ("cms_platform", "index_html")]:
            with self.subTest(field=field):
                site = delivery_fixture()
                site["delivery"][field] = bad
                self.assertFalse(inspect_client_delivery(site)["ready_to_handover"])

    def test_offline_cli_command_is_registered(self):
        parser = main.build_parser()
        args = parser.parse_args(["handover-check", "example-company"])
        self.assertEqual(args.command, "handover-check")
        self.assertEqual(args.company, "example-company")


if __name__ == "__main__":
    unittest.main()

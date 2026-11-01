"""Offline regression gates: customer photos only after explicit interest.

No email, hosting, API, AI or credit use.
"""
from copy import deepcopy
from pathlib import Path
import ast
import unittest

from utils.client_handover import client_photo_intake_plan, client_design_brief

ROOT = Path(__file__).resolve().parents[1]


def company(*, interested=False, planned=4, media=None):
    return {"url": "https://company.example.org",
            "client_preferences": {
                "interest_confirmed": interested,
                "planned_photo_slots": planned,
                "media_assets": media if media is not None else [],
            }}


class ClientMediaIntakeTests(unittest.TestCase):
    def test_no_photo_request_sent_to_uninterested_prospect(self):
        self.assertFalse(client_photo_intake_plan(company())["request_owner_photos"])
        self.assertIsNone(client_photo_intake_plan(company())["draft_request_fi"])

    def test_explicit_interest_and_a_photo_gap_triggers_draft_only(self):
        result = client_photo_intake_plan(company(interested=True))
        self.assertTrue(result["request_owner_photos"])
        self.assertEqual(result["missing_photos"], 4)
        self.assertIn("no_automatic_contact", result["request_policy"])
        self.assertIn("Jos kuvia ei ole", result["draft_request_fi"])

    def test_no_photo_request_if_not_planned(self):
        self.assertFalse(client_photo_intake_plan(company(interested=True, planned=0))["request_owner_photos"])

    def test_rights_and_owner_approval_are_both_required(self):
        good = dict(kind="photo", rights_verified_by_human=True,
                    client_approved=True, identifiable_people=False)
        bad_rights = dict(good, rights_verified_by_human=False)
        bad_approval = dict(good, client_approved=False)
        another = dict(good)
        plan = client_photo_intake_plan(
            company(interested=True, planned=2,
                    media=[bad_rights, bad_approval, good, another]))
        self.assertEqual(plan["approved_usable_photos"], 2)
        self.assertFalse(plan["request_owner_photos"])

    def test_identifiable_people_need_subject_permission(self):
        asset = dict(kind="photo", rights_verified_by_human=True,
                     client_approved=True, identifiable_people=True)
        self.assertEqual(client_photo_intake_plan(
            company(interested=True, planned=1, media=[asset]))["missing_photos"], 1)
        asset["subject_consent_verified"] = True
        self.assertEqual(client_photo_intake_plan(
            company(interested=True, planned=1, media=[asset]))["missing_photos"], 0)

    def test_invalid_media_fields_do_not_trigger_contact_without_interest(self):
        c = company(planned=-100, media="raw")
        self.assertEqual(client_photo_intake_plan(c)["needed_photo_slots"], 0)
        self.assertFalse(client_photo_intake_plan(c)["request_owner_photos"])
        c["client_preferences"]["planned_photo_slots"] = True
        self.assertEqual(client_photo_intake_plan(c)["needed_photo_slots"], 0)

    def test_does_not_change_customer_state_and_is_in_brief(self):
        c = company(interested=True, planned=1)
        before = deepcopy(c)
        plan = client_design_brief(c)["photo_intake"]
        self.assertEqual(c, before)
        self.assertTrue(plan["request_owner_photos"])
        self.assertEqual(client_design_brief(company())["brand_policy"], "keep_existing_identity")

    def test_general_standards_reach_both_builder_and_qa(self):
        builder = (ROOT / "agents/builder.py").read_text(encoding="utf-8")
        qa = (ROOT / "agents/qa.py").read_text(encoding="utf-8")
        ast.parse(builder)
        ast.parse(qa)
        self.assertEqual(builder.count("YLEINEN V7-SUUNNITTELUSTANDARDI"), 2)
        self.assertEqual(qa.count("YLEINEN V7-LAATURIMA"), 1)
        for doc in ("docs/KAURIVO_PREMIUM_PLAYBOOK.md",
                    "docs/KAURIVO_GLOBAL_DESIGN_QA_CHECKLIST.md",
                    "docs/CLIENT_HANDOVER.md"):
            s = (ROOT / doc).read_text(encoding="utf-8")
            self.assertIn("KAURIVO_CLIENT_PHOTOGRAPHY_INTAKE.md", s, doc)

    def test_client_photo_request_is_not_an_automated_outreach_system(self):
        source = (ROOT / "utils/client_handover.py").read_text(encoding="utf-8")
        self.assertNotIn("smtplib", source)
        self.assertNotIn("requests.post", source)
        guidelines = (ROOT / "docs/KAURIVO_CLIENT_PHOTOGRAPHY_INTAKE.md").read_text(encoding="utf-8")
        self.assertIn("DO NOT ask every cold prospect", guidelines)
        self.assertIn("not automatically sent", guidelines)


if __name__ == "__main__":
    unittest.main()

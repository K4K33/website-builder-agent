"""Offline customer-photo-first and outreach-image-caption regressions.

No external API, email, image retrieval or usage credit consumption.
"""
import unittest
from datetime import date
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import config
from agents import outreach
from utils.client_handover import demo_photo_source_policy, demo_image_caption


ROOT = Path(__file__).resolve().parents[1]


def client():
    return {
        "url": "https://example.org",
        "client_preferences": {
            "planned_photo_slots": 3,
            "media_assets": [
                {"kind": "photo", "rights_verified_by_human": True,
                 "client_approved": True, "identifiable_people": False}
            ]
        },
    }


class PhotoPriorityTests(unittest.TestCase):
    def test_company_photos_are_preferred_before_examples(self):
        c = client()
        selected = demo_photo_source_policy(c)
        self.assertEqual(selected["usable_company_photo_count"], 1)
        self.assertIn("approved_company_photos_first", selected["priority"])
        c["client_preferences"]["media_assets"] = []
        selected = demo_photo_source_policy(c)
        self.assertEqual(selected["usable_company_photo_count"], 0)
        self.assertEqual(selected["priority"], "coherent_licensed_example_photos_if_needed")

    def test_image_notice_is_true_to_reviewed_demo_not_original_site(self):
        c = client()
        c["demo_media"] = {"reviewed_by_human": True, "source": "examples_only"}
        notice = demo_image_caption(c)
        self.assertTrue(notice.startswith("Demon kuvat ovat esimerkkikuvia."))
        self.assertIn("Halutessanne", notice)
        self.assertIn("lopullisilla verkkosivuilla", notice)
        c["demo_media"]["source"] = "mixed"
        self.assertTrue(demo_image_caption(c).startswith("Osa demon kuvista"))
        c["demo_media"] = {"reviewed_by_human": True, "source": "company_only",
                           "rights_verified": True}
        self.assertEqual(demo_image_caption(c), "")
        c["demo_media"] = {"reviewed_by_human": False, "source": "company_only"}
        self.assertTrue(demo_image_caption(c).startswith("Demon kuvitus on alustava."))
        c["demo_media"] = {"reviewed_by_human": True, "source": "no_photos"}
        self.assertEqual(demo_image_caption(c), "")

    def test_caption_inserted_immediately_below_demo_url(self):
        url = "https://example.org/kauppa-demo/"
        note = "Demon kuvat ovat esimerkkikuvia."
        body = "Hei, tässä demo:\n" + url + "\n\nPidättekö sivusta?"
        added = outreach.place_demo_caption(body, note, url)
        self.assertIn(url + "\n" + note + "\n\n", added)
        self.assertEqual(outreach.place_demo_caption(added, note, url), added)
        self.assertEqual(outreach.place_demo_caption(body, "", url), body)

    def test_caption_attached_below_demo_paragraph_when_card_is_external(self):
        body = "Tässä juuri yrityksellenne tekemäni demosivusto.\n\nHaluaisitteko tällaiset?"
        added = outreach.place_demo_caption(body, "Kuvat ovat esimerkkejä.")
        self.assertEqual(added.split("\n\n")[1], "Kuvat ovat esimerkkejä.")

    def test_integrated_outreach_draft_keeps_caption_for_html_card(self):
        c = {
            "name": "Example Hair",
            "url": "https://company.example.org",
            "activity_evidence": {
                "active": True, "verified_by_human": True,
                "checked_at": date.today().isoformat(),
                "source_url": "https://registry.example.org/check",
            },
            "qa": {"overall_pass": True, "build_version": 1, "html_sha256": "x"},
            "approval": {"approved": True, "build_version": 1, "html_sha256": "x"},
            "build": {"version": 1},
            "research": {"company_facts": {
                "name": "Example Hair", "industry": "Hairdresser",
                "services": ["Cuts"], "location": "Helsinki"}},
            "outreach_research": {"verified_by_human": True},
            "demo_url": "https://example.org/demo",
            "demo_media": {"reviewed_by_human": True, "source": "examples_only"},
        }
        with TemporaryDirectory() as folder:
            with patch.object(config, "DATA_DIR", folder), patch.object(
                    config, "COMPANIES_FILE", str(Path(folder) / "companies.json")):
                with patch.object(outreach, "ask_claude_json", return_value={
                    "subject": "Verkkosivuidea Example Hairille",
                    "body": "Hei! Tein teille uuden esikatselun: "
                            "https://example.org/demo\n\nHaluaisitteko tällaisen?",
                }) as ask:
                    saved = outreach.draft_outreach("example-hair", c)
        self.assertFalse(saved["approved"])
        self.assertEqual(saved["body"].count("Demon kuvat ovat esimerkkikuvia."), 1)
        self.assertIn("https://example.org/demo\nDemon kuvat", saved["body"])
        self.assertEqual(saved["demo_card_caption"], demo_image_caption(c))
        self.assertIn("examples_only", ask.call_args.args[1])

    def test_quality_docs_require_caption_below_demo(self):
        outreach_rules = (ROOT / "docs/OUTREACH.md").read_text(encoding="utf-8")
        global_rules = (ROOT / "docs/KAURIVO_GLOBAL_DESIGN_QA_CHECKLIST.md").read_text(encoding="utf-8")
        self.assertIn("demo_card_caption", outreach_rules)
        self.assertIn("directly beneath", global_rules)
        self.assertIn("Demon kuvat ovat esimerkkikuvia.", outreach_rules)


if __name__ == "__main__":
    unittest.main()

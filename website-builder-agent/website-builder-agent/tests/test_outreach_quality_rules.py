"""No paid AI calls: personalized customer-value outreach tests."""
import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

import config
from agents import outreach


def company_record():
    return {
        "name": "Example Salon",
        "url": "https://salon.example.org",
        "website": "https://salon.example.org",
        "activity_evidence": {
            "active": True, "verified_by_human": True,
            "checked_at": date.today().isoformat(),
            "source_url": "https://example.org/active"
        },
        "qa": {"overall_pass": True, "build_version": 1, "html_sha256": "hash"},
        "approval": {"approved": True, "build_version": 1, "html_sha256": "hash"},
        "build": {"version": 1},
        "research": {
            "company_facts": {"name": "Example Salon", "industry": "Hair salon",
                              "services": ["Haircuts"], "location": "Tampere"},
            "current_site_weaknesses": ["Booking link is hard to find in mobile first view."],
            "design_recommendations": {"customer_tasks": ["Find the booking link quickly"]},
            "design_decisions": [{"id": "booking", "adaptation": "Visible booking button"}],
        },
        "outreach_research": {
            "verified_by_human": True,
            "positive_observation": "Visible specialist work",
            "customer_benefit": "Faster booking"
        },
    }


class OutreachQualityTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.dir = Path(tmp.name)
        for field, value in (("DATA_DIR", str(self.dir)),
                             ("COMPANIES_FILE", str(self.dir / "companies.json"))):
            cm = patch.object(config, field, value)
            cm.start()
            self.addCleanup(cm.stop)

    def test_prompt_focuses_on_customer_actions_not_generic_modern_sites(self):
        prompt = outreach.OUTREACH_SYSTEM_PROMPT
        self.assertIn("Olen Kaarlo, Kaurivon perustaja", prompt)
        self.assertIn("Suunnittelen ja toteutan", prompt)
        self.assertIn("voin toteuttaa uuden sivuston teille kokonaan", prompt)
        self.assertIn("Olisiko teillä kiinnostusta uudistaa", prompt)
        self.assertIn("Olisiko oman verkkosivun", prompt)
        self.assertIn("hello.kaurivo@gmail.com", prompt)
        self.assertIn("ihmisen erillisellä hyväksynnällä", prompt)

    def test_draft_includes_company_specific_evidence_and_customer_task(self):
        record = company_record()
        with patch.object(outreach, "ask_claude_json",
                          return_value={"subject": "Idea Example Salonille",
                                        "body": "Hei, huomasin, että ajanvaraus löytyy usean klikkauksen takaa. Uudessa etusivussa asiakas pääsee varaamaan heti. Miltä se kuulostaa?"}) as ask:
            result = outreach.draft_outreach("example-salon", record)
        self.assertFalse(result["approved"])
        instructions = ask.call_args.args[1]
        self.assertIn("Faster booking", instructions)
        self.assertIn("Visible booking button", instructions)
        self.assertIn("Booking link is hard to find", instructions)

    def test_prompt_passes_existing_demo_link_without_inventing_one(self):
        record = company_record()
        record["demo_url"] = "https://example.org/demo-for-salon"
        with patch.object(outreach, "ask_claude_json",
                          return_value={"subject": "Site example",
                                        "body": "Hei, olen Kaarlo. Tein ehdotuksen. Olisiko kiinnostusta?"}) as ask:
            outreach.draft_outreach("example-salon", record)
        context = ask.call_args.args[1]
        self.assertIn("https://example.org/demo-for-salon", context)
        self.assertIn("Älä koskaan keksi URL", outreach.OUTREACH_SYSTEM_PROMPT)

    def test_dashes_and_old_boilerplate_are_not_stored(self):
        record = company_record()
        for bad in (
            "Hei — tässä tarjous!",
            "Hei – tässä tarjous!",
            'Jos et toivo Kaurivolta muita yhteydenottoja, voit vastata tähän viestiin ”ei kiitos”.',
        ):
            with self.subTest(bad=bad), patch.object(outreach, "ask_claude_json",
                                                  return_value={"subject": "Hello", "body": bad}):
                with self.assertRaises(RuntimeError):
                    outreach.draft_outreach("example-salon", record)


if __name__ == "__main__":
    unittest.main()

"""Offline checks: Kaurivo must clearly explain itself in every first contact.

No web, PRH, Tavily, email or paid credits.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "docs" / "kaurivo" / "assets"
HOME = ROOT / "docs" / "kaurivo" / "index.html"


class KaurivoPositioningTests(unittest.TestCase):
    def test_first_contact_identifies_studio_in_all_languages(self):
        js = (ASSET / "crm.js").read_text(encoding="utf-8")
        first_contact = js.split("function personalizedOutreachDraft(company){", 1)[1].split(
            "function draftDemoBrief(c){", 1
        )[0]
        self.assertIn("Kaurivo on uuden sukupolven verkkosivustudio", first_contact)
        self.assertIn("Kaurivo är en modern webbstudio", first_contact)
        self.assertIn("Kaurivo is a modern web design studio", first_contact)
        self.assertIn("uusia verkkosivuja ja uudistaa nykyisiä", first_contact)
        self.assertIn("nya webbplatser och förnyar befintliga", first_contact)
        self.assertIn("new websites and redesigning existing ones", first_contact)
        self.assertIn("Kaarlo Kaurivolta", first_contact)
        self.assertIn("Kaarlo från Kaurivo", first_contact)
        self.assertIn("Kaarlo from Kaurivo", first_contact)
        self.assertIn("ei yhteydenottoja.", first_contact)
        self.assertIn("ingen mer kontakt.", first_contact)
        self.assertIn("no further contact.", first_contact)
        self.assertNotIn("och er webbplats", first_contact)
        self.assertIn('company.outreach_review!=="human_approved"', first_contact)

    def test_sender_introduction_precedes_observation(self):
        js = (ASSET / "crm.js").read_text(encoding="utf-8")
        first_contact = js.split("function personalizedOutreachDraft(company){", 1)[1].split(
            "function draftDemoBrief(c){", 1
        )[0]
        for intro, observation in [
            ("Jag heter Kaarlo", "Jag tittade på hur"),
            ("I'm Kaarlo", "I looked at"),
            ("Olen Kaarlo", "Tutustuin "),
        ]:
            self.assertLess(first_contact.index(intro), first_contact.index(observation))

    def test_prospect_can_open_company_site_without_searching(self):
        js = (ASSET / "crm.js").read_text(encoding="utf-8")
        translations = (ASSET / "i18n.js").read_text(encoding="utf-8")
        site = "https://k4k33.github.io/website-builder-agent/kaurivo/"
        self.assertIn(site + "?lang=fi", js)
        self.assertGreaterEqual(js.count(site), 3)
        self.assertIn('new URLSearchParams(location.search).get("lang")==="fi"', translations)

    def test_website_clarifies_new_sites_and_redesigns_in_two_languages(self):
        html = HOME.read_text(encoding="utf-8")
        translations = (ASSET / "i18n.js").read_text(encoding="utf-8")
        self.assertIn("Kaurivo is an independent web design studio creating new websites", html)
        self.assertIn("redesigning existing ones", html)
        self.assertIn("Kaurivo on uuden sukupolven verkkosivustudio", translations)
        self.assertIn("uudistaa nykyisiä", translations)
        self.assertIn('data-lang-set="fi"', html)


if __name__ == "__main__":
    unittest.main()

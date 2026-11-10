"""Offline checks: Kaurivo must clearly explain itself in every first contact.

No web, PRH, Tavily, email or paid credits.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / "docs" / "kaurivo" / "assets"
HOME = ROOT / "docs" / "kaurivo" / "index.html"


class KaurivoPositioningTests(unittest.TestCase):
    def test_first_contact_identifies_sender_in_all_languages(self):
        """New email composer is the source of truth, not removed CRM prose."""
        composer = (ASSET / "outreach-mail.js").read_text(encoding="utf-8")
        crm = (ASSET / "crm.js").read_text(encoding="utf-8")
        for term in ("Olen Kaarlo Kaurivolta", "Jag heter Kaarlo",
                     "I'm Kaarlo from Kaurivo", "Kaarlo Kaurivolta",
                     "Kaarlo från Kaurivo", "Kaarlo from Kaurivo",
                     "ei yhteydenottoja", "ingen mer kontakt",
                     "no further contact", 'company.outreach_review!=="human_approved"'):
            self.assertIn(term, composer)
        self.assertIn("KaurivoOutreach.firstContact(company)", crm)
        self.assertNotIn("https://k4k33.github.io/", composer)

    def test_sender_introduction_precedes_observation(self):
        composer = (ASSET / "outreach-mail.js").read_text(encoding="utf-8")
        # Verify the actual assembled one-paragraph content puts sender first.
        for intro, observation in [
            ("Jag heter Kaarlo", "och noterade följande"),
            ("I'm Kaarlo from Kaurivo", "and noticed this"),
            ("Olen Kaarlo Kaurivolta", "ja huomasin seuraavaa"),
        ]:
            self.assertLess(composer.index(intro), composer.index(observation))

    def test_public_website_is_available_without_email_tracking(self):
        translations = (ASSET / "i18n.js").read_text(encoding="utf-8")
        html = HOME.read_text(encoding="utf-8")
        composer = (ASSET / "outreach-mail.js").read_text(encoding="utf-8")
        self.assertIn('new URLSearchParams(location.search).get("lang")==="fi"', translations)
        self.assertIn("Kaurivo", html)
        self.assertNotIn("https://", composer)
        self.assertNotIn("http://", composer)

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

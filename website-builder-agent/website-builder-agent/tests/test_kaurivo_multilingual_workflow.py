"""Kaurivo Finnish/Swedish/English workflows are evidence-gated, never guessed."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
JS=(ROOT/"docs/kaurivo/assets/crm.js")
NATIONAL=ROOT.parents[1]/".github/workflows/kaurivo-national-prh.yml"
LEGACY=ROOT.parents[1]/".github/workflows/kaurivo-nightly.yml"

class LanguageSafetyTests(unittest.TestCase):
    def test_language_review_gates_and_sweden_ready_copy(self):
        js=JS.read_text(encoding="utf-8")
        for expected in (
           'contact_language',
           'website_languages',
           'language_evidence_url',
           'outreach_observation_sv',
           'outreach_observation_en',
           'company.contact_language||"undetermined"',
           'if(language==="sv")',
           'if(language==="en")',
           'Om ni inte vill få fler marknadsföringsmeddelanden',
           'KIELIOHJE: toteuta erilliset ruotsin- ja suomenkieliset sivut',
           'swedishLanguageHint(c)',
           'data.website_languages==="undetermined"'
        ):
            self.assertIn(expected.lower(),js.lower(),expected)
        self.assertIn("Viestin kieli, oma havainto",js)
        self.assertNotIn('navigator.sendMail(',js)

    def test_no_wrong_language_without_review(self):
        script=JS.read_text(encoding="utf-8")
        self.assertIn('companyHasMatchingObservation(candidate)',script)
        self.assertIn('observations[language].length<20',script)
        self.assertIn('company.contact_language',script)
        self.assertIn('data.contact_language==="undetermined"',script)

    def test_successful_late_night_search_triggers_push(self):
        main=NATIONAL.read_text(encoding="utf-8")
        legacy=LEGACY.read_text(encoding="utf-8")
        self.assertIn('Notify iPhones when delayed national lead batch is ready',main)
        self.assertIn('utils.kaurivo_morning_push',main)
        self.assertIn('KAURIVO_PRH_MODE == \'pilot-live\'',main)
        self.assertNotIn('schedule:',legacy)
        self.assertIn('workflow_dispatch:',legacy)

if __name__=="__main__":
    unittest.main()

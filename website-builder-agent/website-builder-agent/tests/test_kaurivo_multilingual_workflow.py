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
        composer=(ROOT/"docs/kaurivo/assets/outreach-mail.js").read_text(encoding="utf-8")
        for expected in (
           'contact_language', 'website_languages', 'language_evidence_url',
           'outreach_observation_sv', 'outreach_observation_en',
           'KIELIOHJE: toteuta erilliset ruotsin- ja suomenkieliset sivut',
           'swedishLanguageHint(c)', 'data.website_languages==="undetermined"'
        ):
            self.assertIn(expected.lower(),(js+"\\n"+composer).lower(),expected)
        for expected in (
           'company.contact_language', 'if(language==="sv")',
           'if(language==="en")', 'ingen mer kontakt',
           'Tarkista kieli', 'human_approved'):
            self.assertIn(expected.lower(),composer.lower(),expected)
        self.assertNotIn('navigator.sendMail(',js)

    def test_no_wrong_language_without_review(self):
        script=JS.read_text(encoding="utf-8")
        composer=(ROOT/"docs/kaurivo/assets/outreach-mail.js").read_text(encoding="utf-8")
        self.assertIn('companyHasMatchingObservation(candidate)',script)
        self.assertIn('observation.length<20',composer)
        self.assertIn('company.contact_language',composer)
        self.assertIn('data.contact_language==="undetermined"',script)
        self.assertIn('language_evidence_url',composer)

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

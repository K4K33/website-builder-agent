"""Regression checks for Kaurivo's current private CRM UI.

The previous, obsolete admin UI was replaced; keep security checks and a
guest-browser baseline instead of asserting outdated element names.
"""
import unittest
from pathlib import Path

SITE=Path(__file__).resolve().parents[1]/"docs"/"kaurivo"

class AdminSurfaceTests(unittest.TestCase):
    def test_admin_is_not_public_navigation(self):
        home=(SITE/"index.html").read_text(encoding="utf-8")
        admin=(SITE/"admin"/"index.html").read_text(encoding="utf-8")
        script=(SITE/"assets"/"crm.js").read_text(encoding="utf-8")
        self.assertNotIn('href="admin/"',home)
        self.assertNotIn('href="./admin/"',home)
        self.assertIn('noindex,nofollow,noarchive',admin)
        self.assertIn('id="login"',admin)
        self.assertIn('id="dashboard" hidden',admin)
        self.assertIn('id="tab-reviews"',admin)
        self.assertIn('id="queue-list"',admin)
        self.assertIn('getUser()',script)
        self.assertIn('email_confirmed_at',script)
        self.assertIn('source_verified:true',script)
        self.assertIn('kaurivo_prepare_feedback_invitation',script)
        self.assertNotIn('sb_secret_',script)
        self.assertNotIn('innerHTML',script)

if __name__=="__main__":
    unittest.main()

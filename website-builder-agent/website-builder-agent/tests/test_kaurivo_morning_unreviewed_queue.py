"""Verify unreviewed PRH research cannot contaminate the 4-star shortlist.

Static regression contract for the actual CRM renderer + admin selector.
A separate real authenticated admin smoke test is still required for full
end-to-end Supabase user-session UI behavior.
"""
from __future__ import annotations
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]/"docs"/"kaurivo"
SCRIPT=(ROOT/"assets"/"crm.js").read_text(encoding="utf-8")
HTML=(ROOT/"admin"/"index.html").read_text(encoding="utf-8")


class MorningUnreviewedResearchQueue(unittest.TestCase):
    def test_default_remains_strict_good_reputation(self):
        from bs4 import BeautifulSoup
        soup=BeautifulSoup(HTML,"html.parser")
        selector=soup.select_one("#lead-view")
        self.assertIsNotNone(selector)
        self.assertEqual(selector.select_one("option[selected]")["value"],"all")
        self.assertIn("vähintään 4/5",selector.select_one('option[value="all"]').get_text())
        self.assertIn("Esitutkimus",selector.select_one('option[value="unreviewed"]').get_text())
        self.assertIn("Ne eivät ole myyntisuosituksia",HTML)
        self.assertIn("websitePubliclyAccessible(x)&&fourStarIndependentReputation(x)",SCRIPT)
        self.assertIn('const unreviewedQueue=mode==="unreviewed"',SCRIPT)
        self.assertIn("(unreviewedQueue||",SCRIPT)
        self.assertIn("!websitePubliclyAccessible(x)||!fourStarIndependentReputation(x)",SCRIPT)

    def test_unreviewed_view_is_always_labeled_not_qualified_or_contact_ready(self):
        self.assertIn("ESITUTKIMUS · ei myyntisuosituksia",SCRIPT)
        self.assertIn("ESITUTKIMUS – ei myyntilistan hyväksyntää",SCRIPT)
        self.assertIn("Tämä ei tarkoita huonoa mainetta",SCRIPT)
        self.assertIn("Vain yksityinen rakennustesti",SCRIPT)
        self.assertIn("Tarkista sivun julkisuus, yrityksen maine ja kieli",SCRIPT)
        self.assertIn('if(!unreviewedQueue && candidate.outreach_review==="human_approved"',SCRIPT)
        self.assertIn('new Date(rep.checked_at).toLocaleDateString("fi-FI")',SCRIPT)
        self.assertIn("if(fourStarIndependentReputation(candidate)){",SCRIPT)
        self.assertIn('else if(mode==="research")visible=visible.filter(x=>!x.marketing_opt_out).slice(0,20)',SCRIPT)

    def test_no_fake_reputation_defaults_enter_published_sales_cards(self):
        # A missing rating must display an absence of *verified* evidence,
        # never "0.0/5" or an invalid checked date. Guard source structure
        # so the only numeric rating renderer is inside qualified branch.
        start=SCRIPT.index("const rep=candidate.reputation_evidence||{}")
        end=SCRIPT.index("append(row.main,\"div\",\"record-sub\",leadReviewBand(candidate))",start)
        fragment=SCRIPT[start:end]
        self.assertLess(fragment.index("if(fourStarIndependentReputation(candidate)){"),
                        fragment.index("Number(rep.rating).toFixed(1)"))
        self.assertIn("}else{",fragment)
        self.assertIn("Asiakasmainetta ei vielä vahvistettu",fragment)
        self.assertIn("source.protocol===\"https:\"",fragment)


if __name__=="__main__":
    unittest.main()

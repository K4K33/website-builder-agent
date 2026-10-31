"""Kaurivo PRH relevance selection tests: fixtures only, zero network cost."""
from datetime import date
from pathlib import Path
import unittest

from utils.kaurivo_lead_quality import lead_score,choose_shortlist
from utils.prh_bulk_discovery import rank_bulk

def record(idx,name,industry,site=""):
    return {
        "businessId":{"value":f"{idx:07d}-{idx%10}"},
        "names":[{"version":1,"name":name}],
        "mainBusinessLine":{"type":industry},
        "website":{"url":site},
        "addresses":[{"postOffices":[{"city":"HELSINKI"}]}],
    }

class LeadQualityTests(unittest.TestCase):
    def test_excludes_housing_and_asset_holding(self):
        self.assertIsNone(lead_score("Asunto Oy Hietaniemenkatu","68201"))
        self.assertIsNone(lead_score("Kiinteistöosakeyhtiö Kauppala","68201"))
        self.assertIsNone(lead_score("Bostadsaktiebolag Eklund","68203"))
        self.assertIsNone(lead_score("Tulevaisuus Holding Oy","64200"))
        self.assertIsNone(lead_score("Kiinteistö Oy Kallio","68201"))
        self.assertIsNone(lead_score("Sijoitusyhtiö Omega Oy","64990"))
        self.assertEqual(lead_score("Espoon Kiinteistöhuolto Oy","81100"),4)
        self.assertEqual(lead_score("Kiinteistöketju välityspalvelut Oy","68310"),4)
        self.assertEqual(lead_score("Espoon Lukkohuolto Oy","47529"),4)
        self.assertEqual(lead_score("Suomen Tilitoimisto Oy","69200"),4)

    def test_quality_not_absence_before_urls(self):
        rows=[]
        for i in range(1,21):
            rows.append(record(i,f"Asunto Oy Testi {i}","68201"))
        for i in range(21,71):
            rows.append(record(i,f"Korjausliike {i} Oy","43320",
                               ("https://firma"+str(i)+".fi") if i%2 else ""))
        selected=rank_bulk(rows,day=date(2026,10,31),max_candidates=50,shortlist_size=30)
        self.assertEqual(len(selected["shortlist"]),30)
        self.assertTrue(all("Asunto Oy" not in x["name"] for x in selected["shortlist"]))
        self.assertGreater(sum(bool(x["website_listed_url"]) for x in selected["shortlist"]),0)
        self.assertGreater(sum(not x["website_listed_url"] for x in selected["shortlist"]),0)

    def test_missing_url_never_asserts_website_absence(self):
        candidates=[
         {"business_id":f"{i:07d}-{i%10}","name":f"LVI {i} Oy",
          "industry_code_hint":"43220","website_listed_url":""}
         for i in range(1,12)
        ]
        result=choose_shortlist(candidates,size=10,day="2026-10-31")
        self.assertEqual(len(result),10)
        self.assertTrue(all(not c["website_listed_url"] for c in result))

    def test_ui_supports_manual_verification_and_search_without_credits(self):
        root=Path(__file__).resolve().parents[1]
        html=(root/"docs/kaurivo/admin/index.html").read_text()
        script=(root/"docs/kaurivo/assets/crm.js").read_text()
        service=(root/"docs/kaurivo/backend/manual_scan_edge.ts").read_text()
        self.assertIn('id="show-skipped-prospects"',html)
        self.assertIn("www.google.com/search",script)
        self.assertIn("website_found_url",script)
        self.assertIn("ei todista sivuttomuutta",script)
        self.assertIn("PROPERTY_NAME",service)
        self.assertIn("businessScore",service)
        self.assertIn("const withUrl=",service)
        self.assertIn("const withoutUrl=",service)
        self.assertNotIn("Authorization: Bearer ",html)

if __name__=="__main__":
    unittest.main()

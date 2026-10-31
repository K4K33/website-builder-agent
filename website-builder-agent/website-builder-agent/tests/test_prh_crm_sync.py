"""Zero-credit tests for authenticated PRH nightly lead sync."""
from datetime import date
import json
from pathlib import Path
import tempfile
import unittest

from utils.prh_crm_sync import AUDIENCE, FUNCTION_URL, push_packet


def sample(mode="pilot-live"):
    return {
        "schema": "kaurivo_prh_shortlist_v1",
        "date": date.today().isoformat(), "mode": mode,
        "not_verified_for_outreach": True, "review_required": True,
        "candidates": [{
            "identity": "prh:1234567-8", "business_id": "1234567-8",
            "name": "Test company Oy",
            "business_activity": "unverified",
            "website_absence_verified": False,
            "outreach_authorized": False, "demo_authorized": False,
            "website_listed_url": "", "city_hint": "Helsinki"
        }]
    }


class FakeResponse:
    def __init__(self, data, status=200):
        self.data = data
        self.ok = status == 200
        self.status_code = status

    def json(self):
        return self.data

    def raise_for_status(self):
        if not self.ok:
            raise RuntimeError("not ok")


class NightlySyncTests(unittest.TestCase):
    def test_real_packet_uses_two_calls_no_static_secrets(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"crm-shortlist.json"
            p.write_text(json.dumps(sample()),encoding="utf-8")
            events=[]
            def mock_get(url,headers,timeout):
                events.append(("get",url,headers))
                return FakeResponse({"value": "a"*150})
            def mock_post(url,headers,data,timeout):
                events.append(("post",url,headers,json.loads(data)))
                return FakeResponse({"ok":True,"processed":1,"ai_credits_used":0,"emails_sent":0})
            res=push_packet(p,env={
                "ACTIONS_ID_TOKEN_REQUEST_URL": "https://example.com/idtoken?ref=one",
                "ACTIONS_ID_TOKEN_REQUEST_TOKEN": "private_token",
            },get=mock_get,post=mock_post)
            self.assertEqual(res["processed"],1)
            self.assertEqual(res["emails_sent"],0)
            self.assertEqual(len(events),2)
            self.assertEqual(events[0][0],"get")
            self.assertIn("audience="+AUDIENCE,events[0][1])
            self.assertEqual(events[1][1],FUNCTION_URL)
            self.assertEqual(events[1][2]["Authorization"],"Bearer "+"a"*150)
            self.assertEqual(events[1][3]["candidates"][0]["business_activity"],"unverified")

    def test_offline_or_missing_oidc_cannot_sync(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/"shortlist.json"
            p.write_text(json.dumps(sample(mode="offline")))
            with self.assertRaisesRegex(RuntimeError,"real PRH"):
                push_packet(p,env={})
            p.write_text(json.dumps(sample()))
            with self.assertRaisesRegex(RuntimeError,"OIDC"):
                push_packet(p,env={})

    def test_workflow_grants_only_oidc_and_not_mailing(self):
        root=Path(__file__).resolve().parents[3]
        workflow=(root/".github"/"workflows"/"kaurivo-national-prh.yml").read_text()
        self.assertIn("id-token: write",workflow)
        self.assertIn("utils.prh_crm_sync",workflow)
        self.assertIn("pilot-live",workflow)
        self.assertNotIn("SUPABASE_SERVICE_ROLE_KEY",workflow)
        self.assertNotIn("send_email",workflow)

if __name__=="__main__":
    unittest.main()

"""Zero-network test of GitHub OIDC failure telemetry and lawful outreach draft gates."""
import json
from pathlib import Path
import unittest

from utils.kaurivo_failure_report import report_failure,AUDIENCE,ENDPOINT

ROOT=Path(__file__).resolve().parents[1]
class FakeResponse:
    def __init__(self,body):self.body=body
    def __enter__(self):return self
    def __exit__(self,*args):return None
    def read(self):return json.dumps(self.body).encode()

class FailureReportTests(unittest.TestCase):
    def test_reports_only_real_failed_live_runs_with_oidc(self):
        calls=[]
        def fake_fetch(request,timeout):
            calls.append((request,timeout))
            if len(calls)==1:return FakeResponse({"value":"x"*180})
            return FakeResponse({"ok":True,"status_recorded":True})
        env={"KAURIVO_PRH_MODE":"pilot-live",
             "ACTIONS_ID_TOKEN_REQUEST_URL":"https://actions.example/token",
             "ACTIONS_ID_TOKEN_REQUEST_TOKEN":"fake-run-token"}
        result=report_failure(env=env,send=fake_fetch)
        self.assertTrue(result["sent"])
        self.assertEqual(len(calls),2)
        self.assertIn("audience="+AUDIENCE,calls[0][0].full_url)
        self.assertEqual(calls[1][0].full_url,ENDPOINT)
        packet=json.loads(calls[1][0].data)
        self.assertEqual(packet["schema"],"kaurivo_prh_run_status_v1")
        self.assertEqual(packet["outcome"],"failure")
        self.assertRegex(packet["date"],r"^\d{4}-\d{2}-\d{2}$")

    def test_offline_and_missing_oidc_never_send(self):
        forbidden=lambda *a,**k:self.fail("offline/no-oidc must make zero HTTP requests")
        self.assertFalse(report_failure(env={"KAURIVO_PRH_MODE":"offline"},send=forbidden)["sent"])
        self.assertFalse(report_failure(env={"KAURIVO_PRH_MODE":"pilot-live"},send=forbidden)["sent"])

    def test_pipeline_failure_step_and_personalized_optout_are_present(self):
        workflow=(ROOT.parents[1]/".github/workflows/kaurivo-national-prh.yml").read_text()
        js=(ROOT/"docs/kaurivo/assets/crm.js").read_text()
        self.assertIn("python -m utils.kaurivo_failure_report",workflow)
        self.assertIn("continue-on-error: true",workflow)
        self.assertIn("personalizedOutreachDraft(",js)
        self.assertIn("outreach_observation",js)
        self.assertIn("ei yhteydenottoja.",js)
        self.assertNotIn('fetch("https://gmail',js)

if __name__=="__main__":
    unittest.main()

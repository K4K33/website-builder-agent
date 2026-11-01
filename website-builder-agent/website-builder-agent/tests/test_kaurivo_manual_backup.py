"""Kaurivo manual-search fallback + nightly recovery, offline-only tests."""
from datetime import date
from io import BytesIO
import json
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
WORKFLOW=ROOT.parents[1]/".github"/"workflows"/"kaurivo-national-prh.yml"
# This repository's Python root is nested; the workflow is stored at repository top level.
if not WORKFLOW.exists():
    WORKFLOW=ROOT.parents[2]/".github"/"workflows"/"kaurivo-national-prh.yml"
HTML=ROOT/"docs"/"kaurivo"/"admin"/"index.html"
JS=ROOT/"docs"/"kaurivo"/"assets"/"crm.js"
EDGE=ROOT/"docs"/"kaurivo"/"backend"/"manual_scan_edge.ts"

class FakeHTTP:
    def __init__(self, obj):
        self.obj=obj
    def __enter__(self): return self
    def __exit__(self,*args): return None
    def read(self): return json.dumps(self.obj).encode()
    def __iter__(self): return iter([])


class BackupTests(unittest.TestCase):
    def test_offline_recovery_gate(self):
        from utils.kaurivo_backup_gate import BACKUP_CRON,should_scan
        day=date(2026,11,1)
        ok={"id":31,"created_at":"2026-11-01T02:13:00Z",
            "event":"schedule","conclusion":"success"}
        fail={**ok,"conclusion":"failure"}
        def remote(obj):
            def fn(_request,timeout):
                self.assertEqual(timeout,15)
                return FakeHTTP({"workflow_runs":obj})
            return fn
        self.assertFalse(should_scan(event="schedule",cron=BACKUP_CRON,
            token="mock",run_id="32",local_day=day,fetch=remote([ok])))
        self.assertTrue(should_scan(event="schedule",cron=BACKUP_CRON,
            token="mock",run_id="32",local_day=day,fetch=remote([fail])))
        self.assertTrue(should_scan(event="schedule",cron=BACKUP_CRON,
            token="mock",run_id="32",local_day=day,fetch=remote([])))
        self.assertTrue(should_scan(event="schedule",cron=BACKUP_CRON,
            token="mock",run_id="32",local_day=day,fetch=lambda *_: (_ for _ in ()).throw(OSError())))
        # GitHub delayed the 04:13 local run until 11:12 on 2026-11-01.
        late_success={**ok,"created_at":"2026-11-01T09:12:11Z"}
        self.assertFalse(should_scan(event="schedule",cron=BACKUP_CRON,
            token="mock",run_id="33",local_day=day,fetch=remote([late_success])))
        self.assertFalse(should_scan(event="schedule",cron="13 4 * * *",
            token="mock",run_id="33",local_day=day,fetch=remote([late_success])))
        self.assertTrue(should_scan(event="schedule",cron="13 4 * * *",
            token="mock",run_id="33",local_day=day,fetch=remote([])))
        self.assertTrue(should_scan(event="workflow_dispatch",cron="",token="mock"))

    def test_workflow_has_two_local_scans_and_recovery_gate(self):
        text=WORKFLOW.read_text(encoding="utf-8")
        self.assertIn('cron: "13 4 * * *"',text)
        self.assertIn('cron: "17 6 * * *"',text)
        self.assertIn('timezone: "Europe/Helsinki"',text)
        self.assertIn('python -m utils.kaurivo_backup_gate',text)
        self.assertIn("should_scan == 'true'",text)
        self.assertIn("python -m utils.prh_crm_sync",text)
        self.assertIn('OPENROUTER_API_KEY: ""',text)

    def test_manual_scan_is_admin_only_limited_and_truthful(self):
        text=EDGE.read_text(encoding="utf-8")
        for needed in ('checkAdmin(req)','kaurivo_claim_manual_scan',
                       'kaurivo_manual_scan_runs','MAX_REQUESTS=6',
                       'AbortSignal.timeout(12000)','response.status===429',
                       'kaurivo_crm_prospects?on_conflict=business_id',
                       'resolution=ignore-duplicates',
                       'activity_verified:false',
                       'website_verified:false','financial_verified:false',
                       'marketing_emails_sent:0','ai_credits_used:0'):
            self.assertIn(needed,text)
        self.assertNotIn('service_role_key =',text.lower())
        self.assertNotIn('console.log(',text)

    def test_admin_has_working_manual_button(self):
        html=HTML.read_text(encoding="utf-8")
        js=JS.read_text(encoding="utf-8")
        self.assertIn('id="start-manual-scan"',html)
        self.assertIn('id="manual-scan-status"',html)
        self.assertIn('startManualScan()',js)
        self.assertIn('start-manual-scan").addEventListener("click",startManualScan)',js)
        self.assertIn('Authorization":"Bearer "+session.access_token',js)
        self.assertIn('selectedDay=helsinkiToday()',js)
        self.assertIn('await reload()',js)

if __name__=="__main__":
    unittest.main()

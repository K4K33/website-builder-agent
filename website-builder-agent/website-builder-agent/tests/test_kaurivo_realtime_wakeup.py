"""Realtime-driven free-only local Kaurivo wakeups; offline tests.

No cloud inference, Supabase tokens, customer records or billable API calls.
"""
import hashlib
import json
from pathlib import Path
import threading
import unittest
from unittest.mock import patch

from scripts.kaurivo_local_worker import realtime_wakeup,FALLBACK_POLL_SECONDS,PING_SECONDS

ROOT=Path(__file__).resolve().parents[1]
DAEMON=(ROOT/"scripts/kaurivo_local_worker.py").read_text(encoding="utf-8")
SQL=(ROOT/"docs/kaurivo/backend/kaurivo_local_realtime_wakeup_20261112.sql").read_text(encoding="utf-8")
EDGE=(ROOT/"docs/kaurivo/backend/demo_immediate_dispatch_edge.ts").read_text(encoding="utf-8")
PANEL=(ROOT/"docs/kaurivo/assets/demo-jobs.js").read_text(encoding="utf-8")


class FakeWebSocket:
    def __init__(self, topic, shutdown):
        self.topic=topic
        self.shutdown=shutdown
        self.sent=[]
        self.read=0
        self.closed=False

    def settimeout(self,seconds):
        assert seconds>=1

    def send(self,value):
        self.sent.append(json.loads(value))

    def recv(self):
        self.read+=1
        if self.read==1:
            return json.dumps({"topic":self.topic,"event":"phx_reply","ref":"1",
                               "payload":{"status":"ok","response":{}}})
        if self.read==2:
            self.shutdown.clear()
            return json.dumps({"topic":self.topic,"event":"broadcast",
                               "payload":{"event":"wake","payload":{"ready":True}}})
        return ""

    def close(self):
        self.closed=True


class RealtimeWakeupTests(unittest.TestCase):
    def test_opaque_device_topic_receives_wake_without_prospect_data(self):
        token="kvl_"+"a"*64
        digest=hashlib.sha256(token.encode("ascii")).hexdigest()[:48]
        topic="realtime:kaurivo-demo-local-"+digest
        event=threading.Event()
        active=threading.Event()
        active.set()
        ws=FakeWebSocket(topic,active)
        with patch("websocket.create_connection",return_value=ws) as connect:
            realtime_wakeup(token,event,active)
        self.assertTrue(event.is_set())
        self.assertTrue(ws.closed)
        self.assertIn("wss://xhsfbcwpwbgdbatrcyuk.supabase.co/",connect.call_args.args[0])
        self.assertNotIn(token,connect.call_args.args[0])
        self.assertEqual(ws.sent[0]["topic"],topic)
        self.assertEqual(ws.sent[0]["event"],"phx_join")
        self.assertIs(ws.sent[0]["payload"]["config"]["private"],False)
        self.assertNotIn("company_name",json.dumps(ws.sent))
        self.assertNotIn("job_id",json.dumps(ws.sent))

    def test_db_triggers_only_constant_wakeup_without_creating_worker_job(self):
        trigger=SQL.split("create or replace function kaurivo_internal.notify_local_demo_worker()")[1]
        trigger=trigger.split("$$;")[0]
        self.assertIn("perform realtime.send(jsonb_build_object('ready',true)",trigger)
        self.assertIn("'kaurivo-demo-local-'||left(d.token_hash,48),false",trigger)
        self.assertIn("after insert on public.kaurivo_demo_build_jobs",SQL)
        self.assertNotIn("company_name",trigger)
        self.assertNotIn("original_url",trigger)
        self.assertNotIn("business_id",trigger)
        self.assertIn("kaurivo_internal.is_kaurivo_admin()",SQL)
        self.assertIn("requested_by=auth.uid()",SQL)
        self.assertIn("kaurivo_local_worker_wakeup",EDGE)

    def test_wakeup_reduces_edge_invocations_and_preserves_fallback(self):
        self.assertEqual(FALLBACK_POLL_SECONDS,90.0)
        self.assertEqual(PING_SECONDS,20.0)
        self.assertIn("wake.wait(timeout=FALLBACK_POLL_SECONDS)",DAEMON)
        self.assertIn("wake.set()  # Always check pending durable jobs on first startup.",DAEMON)
        self.assertIn("listener=threading.Thread(target=realtime_wakeup",DAEMON)
        self.assertNotIn("time.sleep(POLL_SECONDS)",DAEMON)
        # 30-day baseline: 20-second heartbeats plus rare 90-second queue
        # fallback = 158400 calls, below free 500k total for this feature.
        monthly=30*24*60*60/PING_SECONDS+30*24*60*60/FALLBACK_POLL_SECONDS
        self.assertLess(monthly,160000)

    def test_owner_sees_true_fast_claim_not_already_queued_error(self):
        self.assertIn('dispatch:"local_running"',EDGE)
        self.assertIn('dispatch:"local_waiting"',EDGE)
        self.assertIn("kaurivo_local_worker_wakeup",EDGE)
        self.assertIn("job.runner_kind",EDGE)
        self.assertIn('data.dispatch==="local_running"',PANEL)
        self.assertIn('data.dispatch==="local_waiting"',PANEL)
        self.assertIn('data.dispatch==="local_ready"',PANEL)
        self.assertIn("Windows-rakentaja on jo aloittanut demon tutkimisen",PANEL)


if __name__=="__main__":
    unittest.main()

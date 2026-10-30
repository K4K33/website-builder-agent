"""Nightly Kaurivo pipeline offline tests: no real network, paid model or mail."""
from datetime import date
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

import requests
from utils.nightly_pipeline import (
    MAX_RETURNED_ELEMENTS, choose_rotation, make_report,
    normalize_candidate, parse_elements, query_once, run,
)
from utils.pitch_quality import assess_pitch_packet, CHECKS


class FakeResponse:
    def __init__(self, elements=None, error=False):
        self.elements = elements or []
        self.error = error
    def raise_for_status(self):
        if self.error:
            raise requests.HTTPError("429: rate-limited")
    def json(self):
        return {"elements": self.elements}


ELEMENTS = [
    {"type":"node","id":101,"tags":{"name":"Esimerkki yritys A"}},
    {"type":"way","id":102,"tags":{"name":"Esimerkki yritys B","website":"https://example.org"}},
    {"type":"node","id":101,"tags":{"name":"Esimerkki yritys A"}},
    {"type":"relation","id":103,"tags":{"name":"Esimerkki yritys C"}},
]


class NightlyDiscoveryTests(unittest.TestCase):
    def test_rotates_sectors_and_places_deterministically(self):
        a = choose_rotation(date(2026,10,30))
        self.assertEqual(a, choose_rotation(date(2026,10,30)))
        self.assertNotEqual(a, choose_rotation(date(2026,10,31)))

    def test_missing_tag_is_unverified_not_definitely_no_website(self):
        c = normalize_candidate(ELEMENTS[0], "Turku", "kampaamo")
        self.assertEqual(c["site_discovery_status"], "not_listed_needs_review")
        self.assertIs(c["website_absence_verified"], False)
        self.assertIs(c["outreach_authorized"], False)
        self.assertIs(c["demo_authorized"], False)
        self.assertIn("www.openstreetmap.org/node/101", c["source_url"])

    def test_limit_priority_and_seen_dedupe(self):
        rows = parse_elements(ELEMENTS, "Turku", "kampaamo", limit=10)
        self.assertEqual(len(rows), 3)
        self.assertFalse(rows[0]["website_listed_url"])
        rows2 = parse_elements(ELEMENTS, "Turku", "kampaamo",
                               seen={"osm:node:101"}, limit=10)
        self.assertEqual(len(rows2), 2)
        self.assertNotIn("osm:node:101", [v["identity"] for v in rows2])

    def test_one_request_total_and_finite_overpass_output(self):
        calls = []
        def post(url, *, data, headers, timeout):
            calls.append({"url": url, "data": data, "timeout": timeout})
            return FakeResponse(ELEMENTS)
        city, sector, els = query_once(date(2026,10,30), post=post)
        self.assertEqual(len(calls), 1)
        self.assertIn(f"out center tags {MAX_RETURNED_ELEMENTS};".encode(), calls[0]["data"])
        self.assertEqual(els, ELEMENTS)
        self.assertEqual(timeout:=calls[0]["timeout"], 35)

    def test_rate_limit_stops_without_retry(self):
        calls = []
        def post(url, *, data, headers, timeout):
            calls.append(1)
            return FakeResponse(error=True)
        with self.assertRaises(requests.HTTPError):
            query_once(date(2026,10,30), post=post)
        self.assertEqual(len(calls), 1)

    def test_fixture_mode_no_network_and_produces_artifact(self):
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            fixture = root / "source.json"
            fixture.write_text(json.dumps({"elements": ELEMENTS}), encoding="utf-8")
            def never_post(*args, **kwargs):
                raise AssertionError("Network must never be called.")
            args = {"output_dir": str(root / "output"),
                    "seen_path": str(root / "seen.json"),
                    "day": date(2026,10,30), "post": never_post}
            result = run(mode="fixture", fixture=str(fixture), **args)
            self.assertEqual(result["count"], 3)
            summary = (root/"output"/"shortlist.md").read_text(encoding="utf-8")
            self.assertIn("NOT confirmed firms", summary)
            self.assertIn("Kaurivo nightly", summary)
            status = json.loads((root/"output"/"status.json").read_text())
            self.assertEqual(status["emails_sent"], 0)
            self.assertEqual(status["openrouter_requests"], 0)
            second = run(mode="fixture", fixture=str(fixture), **args)
            self.assertEqual(second["count"], 0)

    def test_offline_mode_makes_no_calls(self):
        with TemporaryDirectory() as tmp:
            def never(*args, **kwargs):
                raise AssertionError("Network attempted")
            result = run(mode="offline", output_dir=tmp+"/out",
                         seen_path=tmp+"/seen.json", post=never)
            self.assertEqual(result["count"], 0)
            self.assertEqual(result["requests"], 0)

    def test_pilot_live_no_ai_email_or_demo(self):
        with TemporaryDirectory() as tmp:
            calls = []
            def post(*args, **kwargs):
                calls.append(1)
                return FakeResponse(ELEMENTS)
            result = run(mode="pilot-live", output_dir=tmp+"/out",
                         seen_path=tmp+"/seen.json",
                         day=date(2026,10,30), post=post)
            self.assertEqual(result["requests"], 1)
            self.assertEqual(len(calls), 1)
            s = json.loads(Path(tmp+"/out/status.json").read_text())
            self.assertEqual(s["demo_built"], 0)
            self.assertEqual(s["emails_sent"], 0)
            self.assertEqual(s["tavily_requests"], 0)

    def test_schedule_and_credentials_are_separated(self):
        path = Path(__file__).resolve().parents[3] / ".github/workflows/kaurivo-nightly.yml"
        workflow = path.read_text(encoding="utf-8")
        self.assertIn('timezone: "Europe/Helsinki"', workflow)
        self.assertIn('cron: "17 3 * * *"', workflow)
        self.assertIn("contents: read", workflow)
        self.assertIn('OPENROUTER_API_KEY: ""', workflow)
        self.assertNotIn("mcp__Gmail__", workflow)
        self.assertNotIn("send_email", workflow)


class PremiumSalesGateTests(unittest.TestCase):
    def complete(self, tmp):
        paths = {}
        for size in ("desktop", "tablet", "mobile", "small_mobile"):
            file = Path(tmp) / (size + ".png")
            file.write_bytes(b"real-file-fixture-not-visual-proof")
            paths[size] = str(file)
        digest = "htmlhash"
        q = dict((key, True) for key, _ in CHECKS)
        q["build_version"] = 2
        q["html_sha256"] = digest
        q["reviewed_at"] = date.today().isoformat()
        return {
            "build": {"version": 2},
            "qa": {"overall_pass": True, "build_version": 2,
                   "html_sha256": digest, "browser": {"screenshots": paths}},
            "approval": {"approved": True, "build_version": 2, "html_sha256": digest},
            "research": {"company_facts": {"name":"Example"},
                         "design_benchmark":[
                             {"url":f"https://peer-{i}.example.org"} for i in range(3)
                         ]},
            "demo": {"published": True, "url": "https://demo.example.org"},
            "demo_quality_review": q,
        }

    def test_incomplete_demo_cannot_be_used_in_sales(self):
        r = assess_pitch_packet({})
        self.assertFalse(r["premium_demo_ready_for_outreach_review"])
        self.assertGreater(len(r["issues"]), 10)

    def test_reviewed_demo_requires_all_checks(self):
        with TemporaryDirectory() as tmp:
            c = self.complete(tmp)
            self.assertTrue(assess_pitch_packet(c)["premium_demo_ready_for_outreach_review"])
            for field, _ in CHECKS:
                c["demo_quality_review"][field] = False
                self.assertFalse(assess_pitch_packet(c)["premium_demo_ready_for_outreach_review"])
                c["demo_quality_review"][field] = True

    def test_stale_version_and_missing_mobile_proof_block(self):
        with TemporaryDirectory() as tmp:
            c = self.complete(tmp)
            c["demo_quality_review"]["build_version"] = 1
            self.assertFalse(assess_pitch_packet(c)["premium_demo_ready_for_outreach_review"])
            c["demo_quality_review"]["build_version"] = 2
            Path(c["qa"]["browser"]["screenshots"]["mobile"]).unlink()
            self.assertFalse(assess_pitch_packet(c)["premium_demo_ready_for_outreach_review"])


if __name__ == "__main__":
    unittest.main()

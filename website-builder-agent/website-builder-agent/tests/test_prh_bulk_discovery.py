"""PRH bulk discovery: stream one ZIP, avoid API spend, verify source safety."""
from datetime import date
import io
import json
from pathlib import Path
import tempfile
import unittest
import zipfile

import requests

from utils.prh_bulk_discovery import (
    MAX_ZIP_BYTES, download_once, iter_bulk_records, normalize_company,
    rank_bulk, run,
)


def record(i, has_url=False, *, closed=False):
    return {
        "businessId": {"value": f"{i:07d}-{i % 10}"},
        "names": [{"name": f"Yritys {i} Oy", "type": "1", "version": 1}],
        "mainBusinessLine": {"type": "43320"},
        "addresses": [{"postOffices": [{"city": "HELSINKI", "languageCode": "1"}]}],
        "website": {"url": f"https://firma{i}.fi" if has_url else ""},
        "endDate": "2022-12-31" if closed else None,
    }


def zip_bytes(objects, *, root_array=True):
    raw = objects if root_array else {"companies": objects, "totalResults": len(objects)}
    with io.BytesIO() as buffer:
        with zipfile.ZipFile(buffer, mode="w", compression=zipfile.ZIP_DEFLATED) as z:
            z.writestr("companies.json", json.dumps(raw).encode("utf-8"))
        return buffer.getvalue()


class Response:
    def __init__(self, body, *, fail=False):
        self.body = body
        self.fail = fail
        self.calls = 0
    def __enter__(self):
        return self
    def __exit__(self, *a):
        pass
    def raise_for_status(self):
        if self.fail:
            raise requests.HTTPError("429")
    def iter_content(self, chunk_size=1024*1024):
        self.calls += 1
        yield self.body


class BulkPrhTests(unittest.TestCase):
    def test_normalizes_business_without_claiming_website_absence(self):
        r = normalize_company(record(123))
        self.assertEqual(r["business_id"], "0000123-3")
        self.assertEqual(r["city_hint"], "HELSINKI")
        self.assertEqual(r["site_discovery_status"], "not_listed_needs_review")
        self.assertFalse(r["website_absence_verified"])
        self.assertFalse(r["demo_authorized"])
        self.assertFalse(r["outreach_authorized"])
        self.assertIsNone(normalize_company(record(124, closed=True)))

    def test_uses_current_registered_name_over_old_first_name(self):
        c = record(127)
        c["names"] = [
            {"name": "Vanha toiminimi", "version": 2, "endDate": "2018-01-01"},
            {"name": "Nykyinen yritysnimi Oy", "version": 1},
        ]
        normalized = normalize_company(c)
        self.assertEqual(normalized["name"], "Nykyinen yritysnimi Oy")

    def test_local_array_and_object_zips_are_streamed(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / "registry.zip"
            for root in (True, False):
                file.write_bytes(zip_bytes([record(1), record(2)], root_array=root))
                rows = list(iter_bulk_records(file))
                self.assertEqual(len(rows), 2)
                self.assertEqual(rows[0]["businessId"]["value"], "0000001-1")

    def test_zip_with_multiple_members_fails_closed(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / "registry.zip"
            with zipfile.ZipFile(file, mode="w") as z:
                z.writestr("1.json", "[]")
                z.writestr("2.json", "[]")
            with self.assertRaises(RuntimeError):
                list(iter_bulk_records(file))

    def test_one_download_call_only_and_rate_limit_stop(self):
        with tempfile.TemporaryDirectory() as tmp:
            zipped = zip_bytes([record(1)])
            called = []
            def get(*args, **kwargs):
                called.append((args, kwargs))
                return Response(zipped)
            downloaded = download_once(Path(tmp) / "fetch.zip", get=get)
            self.assertEqual(downloaded, len(zipped))
            self.assertEqual(len(called), 1)
            def bad_get(*args, **kwargs):
                called.append((args, kwargs))
                return Response(b"", fail=True)
            with self.assertRaises(requests.HTTPError):
                download_once(Path(tmp)/"bad.zip", get=bad_get)
            self.assertEqual(len(called), 2)

    def test_limits_download_size_even_if_server_sends_huge_chunk(self):
        with tempfile.TemporaryDirectory() as tmp:
            def get(*args, **kwargs):
                return Response(b"z" * (MAX_ZIP_BYTES + 1))
            # Avoid actually allocating 650MB: mock module's cap temporarily.
            from unittest.mock import patch
            with patch("utils.prh_bulk_discovery.MAX_ZIP_BYTES", 12):
                with self.assertRaisesRegex(RuntimeError, "safety limit"):
                    download_once(Path(tmp) / "f.zip", get=lambda *a, **k: Response(b"x"*13))

    def test_nationwide_batch_does_not_bias_all_to_first_letter(self):
        rows = [record(i, has_url=(i % 3 == 0)) for i in range(1, 201)]
        result = rank_bulk(rows, day=date(2026,10,30), max_candidates=60, shortlist_size=20)
        self.assertEqual(result["scanned_registry_records"], 200)
        self.assertEqual(len(result["new_candidates"]), 60)
        self.assertEqual(len(result["shortlist"]), 20)
        self.assertGreater(sum(x["website_listed_url"] != "" for x in result["shortlist"]), 0)
        self.assertGreater(sum(not x["website_listed_url"] for x in result["shortlist"]), 0)

    def test_previous_seen_ids_are_skipped_and_not_lost(self):
        rows = [record(i) for i in range(1, 8)]
        result = rank_bulk(rows, day=date(2026,10,30),
                           seen=("prh:0000001-1",), max_candidates=5,
                           shortlist_size=2)
        self.assertEqual(result["previously_seen_skipped"], 1)
        self.assertTrue(all(x["identity"] != "prh:0000001-1"
                            for x in result["new_candidates"]))

    def test_fixture_creates_reports_without_network_and_dedupes(self):
        with tempfile.TemporaryDirectory() as tmp:
            file = Path(tmp) / "registry.zip"
            file.write_bytes(zip_bytes([record(i, has_url=i%2==0) for i in range(1, 21)]))
            calls = []
            def get(*a, **k):
                calls.append(1)
                raise AssertionError("fixture mode made network call")
            kwargs = {"mode":"fixture", "archive":str(file),
                      "day":date(2026,10,30),
                      "output_dir":str(Path(tmp)/"output"),
                      "seen_path":str(Path(tmp)/"seen.json"),
                      "max_candidates":15, "shortlist_size":10, "get":get}
            first = run(**kwargs)
            self.assertEqual(first["scanned"], 20)
            self.assertEqual(first["new"], 15)
            self.assertEqual(calls, [])
            self.assertIn("NOT prove a missing website",
                          (Path(tmp)/"output"/"shortlist.md").read_text())
            self.assertEqual(json.loads((Path(tmp)/"output"/"status.json").read_text())
                             ["emails_sent"], 0)
            second = run(**kwargs)
            self.assertEqual(second["new"], 5)

    def test_offline_mode_zero_requests_and_no_lead_claims(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run(mode="offline", output_dir=tmp+"/out",
                         seen_path=tmp+"/seen.json",
                         get=lambda **k: (_ for _ in ()).throw(AssertionError("network")))
            self.assertEqual(result["requests"], 0)
            self.assertEqual(result["new"], 0)

    def test_national_workflow_contains_no_marketing_or_paid_secrets(self):
        workflow = (Path(__file__).resolve().parents[3] /
                    ".github/workflows/kaurivo-national-prh.yml").read_text()
        self.assertIn("Europe/Helsinki", workflow)
        self.assertIn('OPENROUTER_API_KEY: ""', workflow)
        self.assertIn("max-candidates 5000", workflow)
        self.assertIn("shortlist-size 50", workflow)
        self.assertNotIn("send_email", workflow)


if __name__ == "__main__":
    unittest.main()

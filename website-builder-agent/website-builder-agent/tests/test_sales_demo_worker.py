import os
from pathlib import Path
import unittest
from unittest.mock import patch

os.environ.setdefault("GITHUB_RUN_ID", "1")
import scripts.run_kaurivo_demo_queue as worker
from utils.sales_demo_pipeline import SalesDemoBlocked


class SalesDemoWorkerTests(unittest.TestCase):
    def setUp(self):
        worker.working_job = {"id": "12345678-aaaa-4bbb-8ccc-1234567890ab"}
        self.updates = []
        patcher = patch.object(worker, "update", side_effect=lambda status, progress, **d:
                               self.updates.append((status, d)))
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_publishes_one_verified_page_as_internal_preview(self):
        summary = {"page": "x", "own_photos": 1, "stock_photos": 3, "services": 2,
                   "proof_groups": 1, "dropped": []}
        with patch("utils.sales_demo_pipeline.build_sales_demo", return_value=summary) as build, \
                patch.object(worker, "publish", return_value=("https://p/x/index.html", "abc", ["index.html"])) as pub, \
                patch.object(worker, "verify_public") as verify:
            self.assertEqual(worker.run_sales_demo("https://example.fi/", "Testi Oy", "testi-oy", "m"), 0)
        build.assert_called_once()
        self.assertTrue(pub.call_args.kwargs["sales"])
        verify.assert_called_once_with("https://p/x/index.html", "m", ["index.html"])
        status, details = self.updates[-1]
        self.assertEqual(status, "internal_preview")
        self.assertEqual(details["preview_url"], "https://p/x/index.html")

    def test_blocked_source_becomes_hold_and_rate_limit_is_transient(self):
        with patch("utils.sales_demo_pipeline.build_sales_demo",
                   side_effect=SalesDemoBlocked("sales_headline_unverified", "x")):
            with self.assertRaises(worker.HoldError) as hold:
                worker.run_sales_demo("https://example.fi/", "Testi Oy", "testi-oy", "m")
        self.assertEqual(hold.exception.code, "sales_headline_unverified")
        with patch("utils.sales_demo_pipeline.build_sales_demo",
                   side_effect=RuntimeError("OpenRouter 429 rate limit")):
            with self.assertRaises(worker.HoldError) as hold:
                worker.run_sales_demo("https://example.fi/", "Testi Oy", "testi-oy", "m")
        self.assertIn(hold.exception.code, worker.TRANSIENT_RETRY_CODES)
        with self.assertRaises(worker.HoldError):
            worker.run_sales_demo("", "Testi Oy", "testi-oy", "m")

    def test_sales_page_check_requires_one_noindex_page_with_draft_note(self):
        from tempfile import TemporaryDirectory
        with TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "index.html").write_text('<html><head><meta name="robots" content="noindex,nofollow"></head>'
                                             '<body><p class="draft">Luonnos</p><main><h1>X</h1>'
                                             '<img src="assets/a.webp"></main></body></html>', encoding="utf-8")
            self.assertEqual(worker.verify_sales_page(root), ["index.html"])
            (root / "index.html").write_text('<html><head><meta name="robots" content="noindex"></head><body>'
                                             '<p class="draft">L</p><main><h1>X</h1><img src="https://x/a.jpg">'
                                             '</main></body></html>', encoding="utf-8")
            with self.assertRaises(worker.HoldError):
                worker.verify_sales_page(root)


if __name__ == "__main__":
    unittest.main()

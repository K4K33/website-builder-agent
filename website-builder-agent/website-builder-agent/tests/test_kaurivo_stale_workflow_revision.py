"""Prevent GitHub Actions reruns with old SHA from consuming real build attempts."""
from pathlib import Path
import unittest

ROOT=Path(__file__).resolve().parents[1]
FLOW=(ROOT.parents[1]/".github/workflows/kaurivo-demo-worker.yml").read_text(encoding="utf-8")


class LatestMainWorkerTests(unittest.TestCase):
    def test_latest_commit_check_occurs_before_private_claim(self):
        preflight=FLOW.index("Reject stale source code before consuming private job claims")
        compare=FLOW.index('if [[ "$GITHUB_SHA" != "$CURRENT_MAIN_SHA" ]]')
        checkout=FLOW.index("actions/checkout@v4")
        claim=FLOW.index("Securely claim one queued job")
        self.assertLess(checkout,preflight)
        self.assertLess(preflight,compare)
        self.assertLess(compare,claim)
        self.assertIn("git fetch --quiet origin refs/heads/main",FLOW)
        self.assertIn("git rev-parse FETCH_HEAD",FLOW)
        self.assertIn('exit 1\n          fi\n          echo "Kaurivo builder exact latest-main',FLOW)

    def test_all_research_and_cloud_fixes_wake_fresh_main_worker(self):
        for file in (
            "agents/research.py",
            "utils/cloudflare_free_ai.py",
            "utils/kaurivo_ai_source_packet.py",
            "utils/kaurivo_cloud_vision_packet.py",
            "utils/free_references.py",
            "utils/reference_quote_evidence.py",
        ):
            with self.subTest(file=file):
                self.assertIn('"website-builder-agent/website-builder-agent/'+file+'"',FLOW)
        self.assertIn("schedule:",FLOW)
        self.assertIn("workflow_dispatch:",FLOW)
        self.assertIn('FREE_ONLY: "1"',FLOW)
        self.assertIn("KAURIVO_CLOUDFLARE_WORKERS_FREE_CONFIRMED:",FLOW)

if __name__ == "__main__":
    unittest.main()

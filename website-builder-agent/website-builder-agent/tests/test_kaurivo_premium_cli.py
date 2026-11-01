"""Offline smoke coverage for the actual Kaurivo premium CLI route.

No SMTP, API, AI, cookies, database writes or public deployments.
"""
from contextlib import redirect_stdout
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import json
import unittest

import main


class KaurivoPremiumCommandTests(unittest.TestCase):
    def _run(self, argv):
        args = main.build_parser().parse_args(argv)
        out = StringIO()
        with redirect_stdout(out):
            args.func(args)
        return json.loads(out.getvalue())

    def test_real_public_site_audit_route(self):
        root = Path(__file__).resolve().parents[1] / "docs" / "kaurivo"
        report = self._run(["premium-audit", "--html", str(root / "index.html"),
                            "--root", str(root)])
        self.assertTrue(report["pass"], report["errors"])
        self.assertTrue(report["limitations"])
        self.assertIn("html_bytes", report["measured"])

    def test_production_noindex_fail_closed_through_cli(self):
        source = """<!doctype html><html lang="fi"><head>
        <meta name="viewport" content="width=device-width">
        <meta name="robots" content="noindex">
        <meta name="description" content="Esimerkki tietoja palveluista ja yrityksestä.">
        <title>Yksinkertainen verkkosivu</title>
        <style>@media(max-width:500px){body{width:auto}}
        @media(prefers-reduced-motion:reduce){*{animation:none}}</style>
        </head><body><nav><a href="#main">Etusivu</a></nav>
        <main id="main"><h1>Etusivu</h1><a href="mailto:example@example.org">Email</a>
        </main></body></html>"""
        with TemporaryDirectory() as d:
            path = Path(d) / "index.html"
            path.write_text(source, encoding="utf-8")
            preview = self._run(["premium-audit", "--html", str(path)])
            self.assertTrue(preview["pass"])
            args = main.build_parser().parse_args(
                ["premium-audit", "--html", str(path), "--production"])
            with self.assertRaisesRegex(RuntimeError, "BLOCKED"):
                with redirect_stdout(StringIO()):
                    args.func(args)

    def test_terms_gate_blocks_unconfirmed_scope(self):
        with TemporaryDirectory() as d:
            path = Path(d) / "terms.json"
            path.write_text('{"scope_version":"example-only"}', encoding="utf-8")
            args = main.build_parser().parse_args(["project-terms", "--file", str(path)])
            with self.assertRaisesRegex(RuntimeError, "incomplete"):
                with redirect_stdout(StringIO()):
                    args.func(args)

    def test_demo_evidence_never_implies_outreach_authorization(self):
        with patch.object(main, "get_company", return_value=("candidate", {
            "research": {"company_facts": {"name": "Example Oy", "industry": "kampaamo"}},
            "url": "https://example.org",
        })):
            args = main.build_parser().parse_args(["demo-evidence", "candidate"])
            output = StringIO()
            with self.assertRaisesRegex(RuntimeError, "incomplete"):
                with redirect_stdout(output):
                    args.func(args)
            report = json.loads(output.getvalue())
            self.assertFalse(report["send_authorized"])

    def test_funnel_command_uses_local_state_only(self):
        with patch.object(main, "load_companies", return_value={
            "abc": {"owner_review": {"decision": "select"}, "status": "found"},
        }):
            report = self._run(["sales-funnel"])
            self.assertEqual(report["counts"]["discovered"], 1)
            self.assertEqual(report["counts"]["won"], 0)
            self.assertEqual(report["counts"]["delivered"], 0)


if __name__ == "__main__":
    unittest.main()

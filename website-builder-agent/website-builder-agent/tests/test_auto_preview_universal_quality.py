"""Offline regression: hand-authored auto-preview cannot bypass Master Prompt.

Rendered/published HTML is not automatically a client-ready quality-approved
demo. These tests do not download sites, spend AI credits or claim 9.5/10.
"""
from __future__ import annotations

import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from scripts import audit_changed_demo_previews as audit


class AutoPreviewUniversalQualityTests(TestCase):
    def test_all_auto_preview_folders_are_audited_not_only_changed_slugs(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            (root / "demo-company").mkdir()
            (root / "other-company").mkdir()
            (root / "index.html").write_text("Navigation", encoding="utf-8")
            with patch.object(audit, "DEMOS", root), patch.dict(
                os.environ, {"KAURIVO_DEMO_QA_AUDIT_ALL": "1"}
            ):
                self.assertEqual(
                    audit.changed_slugs("", ""),
                    ["demo-company", "other-company"],
                )

    def test_separate_html_routes_must_be_included_not_homepage_only(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        text = (root / "scripts" / "audit_changed_demo_previews.py").read_text(
            encoding="utf-8"
        )
        self.assertIn('folder.rglob("*.html") if SCOPE == "auto-previews"', text)
        self.assertIn("brand=audit_brand_lock(pages, evidence, css_text=css)", text)
        self.assertIn("verify_demo_concept_evidence(slug, folder, manifest)", text)
        self.assertIn("audit_universal_standards(", text)

    def test_no_source_provenance_is_hard_stop_even_if_public_html_works(self):
        with TemporaryDirectory() as td:
            root = Path(td)
            (root / "docs" / "kaurivo" / "auto-previews" / "demo-company").mkdir(
                parents=True
            )
            (root / "docs" / "kaurivo" / "auto-previews" /
             "demo-company" / "index.html").write_text(
                 "<html><body>Published!</body></html>", encoding="utf-8"
             )
            with patch.object(audit, "ROOT", root):
                with self.assertRaisesRegex(ValueError, "Missing source-bound"):
                    audit.verified_source_evidence("demo-company")


if __name__ == "__main__":
    import unittest
    unittest.main()

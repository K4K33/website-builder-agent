"""Offline contract tests: no real PRH calls, no model credits."""
import hashlib
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import Mock, MagicMock, patch

import config
import main
from utils import state
from utils.prh_statement_inspector import (
    inspect_xml_document, inspect_latest_statement, _download_statement,
)


XML = b'''<?xml version="1.0" encoding="utf-8"?>
<html xmlns="http://www.w3.org/1999/xhtml"
      xmlns:ix="http://www.xbrl.org/2013/inlineXBRL">
 <body>
  <div><ix:nonFraction name="fi_met:mi53" contextRef="ctx-current"
      unitRef="EUR" decimals="0" sign="-" scale="3">981.45</ix:nonFraction></div>
  <div><ix:nonFraction name="fi_met:mi99" contextRef="ctx-previous"
      unitRef="EUR" decimals="0">500</ix:nonFraction></div>
 </body>
</html>'''


def company():
    return {
        "name": "Example Oy",
        "financials": {"business_id": "0116297-6", "business_id_verified": True},
        "registry_evidence": {"business_id": "0116297-6"},
        "financial_availability": {
            "status": "available", "financial_dates": ["2025-12-31"],
            "latest_financial_date": "2025-12-31"
        },
    }


class StatementInspectorTests(unittest.TestCase):
    def test_collects_inline_xbrl_facts_but_never_claims_revenue(self):
        result = inspect_xml_document(XML, "0116297-6", "2025-12-31")
        self.assertEqual(result["sha256"], hashlib.sha256(XML).hexdigest())
        self.assertEqual(result["status"], "taxonomy_review_required")
        self.assertEqual(result["fact_candidates"][0]["taxonomy_concept"], "fi_met:mi53")
        self.assertEqual(result["fact_candidates"][0]["sign"], "-")
        self.assertEqual(result["fact_candidates"][0]["scale"], "3")
        self.assertEqual(result["fact_candidates"][0]["display_value"], "981.45")
        self.assertFalse(result["financial_figures_verified"])
        self.assertIsNone(result["revenue_eur"])
        self.assertIsNone(result["operating_profit_eur"])

    def test_xbrl_instance_fact_is_retained_unverified(self):
        xml = b'''<xbrl xmlns="http://www.xbrl.org/2003/instance"
        xmlns:f="http://example.org/taxonomy">
         <f:Revenue contextRef="C1" unitRef="eur" decimals="-3">120000</f:Revenue>
        </xbrl>'''
        result = inspect_xml_document(xml, "0116297-6", "2025-12-31")
        self.assertEqual(len(result["fact_candidates"]), 1)
        self.assertTrue(result["fact_candidates"][0]["taxonomy_concept"].endswith("Revenue"))
        self.assertFalse(result["fact_candidates"][0]["human_verified"])

    def test_external_entity_and_oversized_document_rejected(self):
        payload = b'<!DOCTYPE a [<!ENTITY xxe SYSTEM "file:///etc/passwd">]><a>&xxe;</a>'
        with self.assertRaises(ValueError):
            inspect_xml_document(payload, "0116297-6", "2025-12-31")
        with self.assertRaises(ValueError):
            inspect_xml_document(b"x" * 2_000_001, "0116297-6", "2025-12-31")
        with self.assertRaises(RuntimeError):
            inspect_xml_document(b"<xml", "0116297-6", "2025-12-31")

    def test_statement_download_stream_bounded_with_exact_request(self):
        response = MagicMock()
        response.headers = {"Content-Type": "text/xml; charset=utf-8"}
        response.iter_content.return_value = [XML[:70], XML[70:]]
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        with patch("utils.prh_statement_inspector.requests.get", return_value=response) as get:
            self.assertEqual(_download_statement("0116297-6", "2025-12-31"), XML)
        self.assertEqual(get.call_args.kwargs["params"],
                         {"businessId": "0116297-6", "financialDate": "2025-12-31"})
        self.assertTrue(get.call_args.kwargs["stream"])
        self.assertFalse(get.call_args.kwargs.get("allow_redirects", False))

    def test_invalid_content_type_and_response_limit_fail_closed(self):
        response = MagicMock()
        response.headers = {"Content-Type": "application/json"}
        response.__enter__ = Mock(return_value=response)
        response.__exit__ = Mock(return_value=False)
        with patch("utils.prh_statement_inspector.requests.get", return_value=response):
            with self.assertRaisesRegex(RuntimeError, "did not return XML"):
                _download_statement("0116297-6", "2025-12-31")
        response.headers = {"Content-Type": "text/xml"}
        response.iter_content.return_value = [b"x" * 2_000_001]
        with patch("utils.prh_statement_inspector.requests.get", return_value=response):
            with self.assertRaisesRegex(RuntimeError, "too large"):
                _download_statement("0116297-6", "2025-12-31")

    def test_unknown_or_unsafe_id_and_period_rejected_before_network(self):
        with patch("utils.prh_statement_inspector.requests.get") as get:
            for bad_id, bad_date in (("nonsense", "2025-12-31"),
                                     ("0116297-6", "2055-01-01"),
                                     ("0116297-6", "not-date")):
                with self.assertRaises(ValueError):
                    _download_statement(bad_id, bad_date)
            get.assert_not_called()

    def test_needs_verified_identity_and_official_period(self):
        with self.assertRaisesRegex(RuntimeError, "independently verified"):
            inspect_latest_statement(company() | {"registry_evidence": {}})
        with self.assertRaisesRegex(RuntimeError, "No official digital"):
            inspect_latest_statement(company() | {"financial_availability": {"status": "not_available"}})
        result = inspect_latest_statement(company(), downloader=lambda id, period: XML)
        self.assertEqual(result["business_id"], "0116297-6")

    def test_lead_queue_uses_prh_review_and_reputation_evidence_safely(self):
        from datetime import date
        from utils.lead_queue import rank_leads
        reput = {"rating": 4.9, "review_count": 55,
                 "source_url": "https://example.org/verified-reviews",
                 "verified_by_human": True, "checked_at": date.today().isoformat()}
        no_site = {"name": "Popular venue", "website": "",
                   "site_verification": {"confirmed_absent": True,
                       "verified_by_human": True, "source_url": "https://example.org/verification"},
                   "reputation": reput}
        periods = {"name": "XBRL", "website": "https://xbrl.example",
                   "financial_availability": {"status": "available"}}
        catalog = {"name": "Needs source review", "website": "https://catalog.example",
                   "financial_statement_review": {"status": "taxonomy_review_required"}}
        unknown = {"name": "Unknown", "website": ""}
        results = rank_leads({"strong": no_site, "periods": periods, "catalog": catalog, "unknown": unknown})
        by_slug = {row["company"]: row for row in results}
        self.assertEqual(by_slug["strong"]["bucket"], "verify_business_activity")
        # For an existing-site business with unknown activity, checking
        # whether it still trades now comes before inspecting old accounts.
        self.assertEqual(by_slug["periods"]["bucket"], "existing_website_verify_activity")
        self.assertEqual(by_slug["catalog"]["bucket"], "existing_website_verify_activity")
        self.assertTrue(all(row["outreach_allowed"] is False for row in results))
        self.assertLess(results.index(by_slug["strong"]), results.index(by_slug["unknown"]))

    def test_cli_requires_explicit_permission_and_keeps_financials_unchanged(self):
        with tempfile.TemporaryDirectory() as tmp:
            cfg = patch.object(config, "COMPANIES_FILE", str(Path(tmp) / "companies.json"))
            cfg.start()
            try:
                state.upsert_company("example", company())
                with patch.object(main, "inspect_latest_statement") as lookup:
                    with self.assertRaisesRegex(RuntimeError, "confirm-public-lookups"):
                        main.cmd_inspect_financial(SimpleNamespace(
                            company="example", limit=3, confirm_public_lookups=False))
                    lookup.assert_not_called()
                    lookup.return_value = inspect_xml_document(XML, "0116297-6", "2025-12-31")
                    main.cmd_inspect_financial(SimpleNamespace(
                        company="example", limit=3, confirm_public_lookups=True))
                    lookup.assert_called_once()
                saved = state.get_company("example")[1]
                self.assertNotIn("revenue_eur", saved["financials"])
                self.assertFalse(saved["financial_statement_review"]["financial_figures_verified"])
            finally:
                cfg.stop()


if __name__ == "__main__":
    unittest.main()

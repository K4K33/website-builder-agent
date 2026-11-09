"""Regression for the 9 Nov failure: 797 green tests cannot approve a broken site.

All tests are free and offline; no LLM, Gmail, customer messages or deploy.
"""
from __future__ import annotations
import copy
from datetime import datetime, timezone
import hashlib
from pathlib import Path
import struct
from tempfile import TemporaryDirectory
from unittest.mock import patch
import unittest
import zlib

from utils.demo_origin_gate import verify_demo_concept_evidence
from utils.release_safety import check_actual_public_website, inspect_release_safety
from utils.service_quality import MASTER_PROMPT_SHA256
from utils.kaurivo_premium_sales import delivery_gate


def public_evidence():
    checked = datetime.now(timezone.utc).isoformat()
    routes = ("index.html", "services/index.html")
    return {
        "url": "https://preview.example.org/",
        "site_sha256": "a" * 64,
        "commit_sha": "b" * 40,
        "release_marker": "source-exact-preview-version-1234",
        "ci_run_url": "https://github.com/owner/repo/actions/runs/123456",
        "ci_verified_by_owner": True,
        "checked_at": checked,
        "pages": [
            dict(route=route, viewport=vp, status=200,
                 release_marker="source-exact-preview-version-1234",
                 computed_styles_valid=True, scripts_valid=True,
                 navigation_valid=True, responsive_valid=True,
                 visible_brand_valid=True, broken_images=0, page_errors=[],
                 screenshot_sha256=hashlib.sha256(f"{route}-{vp}".encode()).hexdigest())
            for route in routes for vp in ("390", "1440")
        ],
        "errors": [], "warnings": [],
    }


def png(width, height, rgb):
    def chunk(kind, value):
        return (struct.pack(">I", len(value)) + kind + value
                + struct.pack(">I", zlib.crc32(kind+value) & 0xffffffff))
    pixels = (b"\0"+bytes(rgb)*width)*height
    ihdr = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
    return (b"\x89PNG\r\n\x1a\n"+chunk(b"IHDR", ihdr)
            + chunk(b"IDAT", zlib.compress(pixels))
            + chunk(b"IEND", b""))


def direction(ident, index):
    prefixes = [
        ("Large historic workshop portrait and authentic upholstery materials",
         "Company background followed by maker bios and repair consultation",
         "Vertical side navigation and anchored craft-story categories",
         "Close-up materials beside portrait-oriented owned craft photography"),
        ("One full-width service request followed by a fabric chooser",
         "Service cards first followed by quote form and filtered work gallery",
         "Horizontal process tabs and service-first quick access controls",
         "Wide process images and explanatory original workshop diagrams"),
        ("Split-screen archive with documentary timeline and case study",
         "Interactive archival story followed by independent team biographies",
         "Editorial chapter index and persistent timeline progress indicator",
         "Alternating genuine historic photography and material comparisons"),
    ]
    first, structure, nav, images = prefixes[index]
    return {
        "id": ident,
        "concept": f"Verified client-specific direction {ident}",
        "business_reason": f"This company serves upholstery customers with direction {ident} and authentic material detail.",
        "source_anchor": f"Actual observed historic upholstery business content for {ident}.",
        "first_view": first,
        "information_architecture": structure,
        "navigation": nav,
        "image_strategy": images,
        "typography": "Accessible editorial serif and native contrast, with no invented marks.",
        "brand_continuity": "Retain the company's source name, source colors and licensed photos.",
        "non_goals": "No generic fictitious staff pictures, ratings or animation spinners.",
        "mobile_behavior": "Natural vertical scroll, menu tap access, no horizontal clipping."
    }


class LivePublicAcceptanceTests(unittest.TestCase):
    def assert_public_pass(self, record):
        return check_actual_public_website(
            record, site_digest="a"*64,
            routes={"index.html", "services/index.html"},
            build_commit="b"*40)

    def test_full_actual_live_report_can_pass_only_with_all_24h_fresh_views(self):
        self.assertTrue(self.assert_public_pass(public_evidence())["passed"])

    def test_live_fail_closed_when_any_route_or_mobile_missing(self):
        record=public_evidence()
        record["pages"].pop()
        result=self.assert_public_pass(record)
        self.assertFalse(result["passed"])
        self.assertTrue(any("never inspected" in issue for issue in result["issues"]))

    def test_live_fails_on_stale_assets_screenshot_and_release_marker(self):
        record=public_evidence()
        record["pages"][0]["broken_images"]=1
        record["pages"][1]["release_marker"]="old-version"
        record["pages"][2]["screenshot_sha256"]="missing"
        result=self.assert_public_pass(record)
        self.assertFalse(result["passed"])
        self.assertTrue(any("BROKEN" in issue for issue in result["issues"]))
        self.assertTrue(any("screenshot" in issue for issue in result["issues"]))

    def test_render_saying_live_or_true_boolean_does_not_approve(self):
        record=public_evidence()
        record["pages"]=[]
        record["success"]=True
        record["render_status"]="live"
        record["ci_verified_by_owner"]=False
        self.assertFalse(self.assert_public_pass(record)["passed"])

    def test_old_browser_report_different_commit_and_digest_rejected(self):
        record=public_evidence()
        record["commit_sha"]="0"*40
        record["site_sha256"]="0"*64
        record["checked_at"]="2025-01-01T00:00:00Z"
        self.assertFalse(self.assert_public_pass(record)["passed"])

    def test_technical_green_does_not_make_client_ready_or_demo_approved(self):
        company={
            "research":{"quality_contract_version":6,"master_prompt_sha256":MASTER_PROMPT_SHA256},
            "qa":{"overall_pass":True,"build_version":1,"html_sha256":"a"*64},
            "build":{"version":1},
            "approval":{"approved":True,"build_version":1},
            "public_release_evidence":{"success":True,"render_status":"live"}
        }
        result=inspect_release_safety(company,customer_delivery=False)
        self.assertEqual(result["status"],"HOLD")
        self.assertFalse(result["approved"])
        with patch("utils.kaurivo_premium_sales.inspect_client_delivery",return_value={
            "issues":[],"ready_to_handover":True,"cms_platform":"WordPress"}):
            gate=delivery_gate(company,{"pass":True,"warnings":[]})
            self.assertFalse(gate["ready_to_deliver"])
            self.assertEqual(gate["release_status"],"HOLD")


class NoBypassMasterPromptAndRenderedConceptTests(unittest.TestCase):
    def _fixture(self, root):
        directions=[direction(f"concept-{i}",i) for i in range(3)]
        selected=directions[0]["id"]
        manifest={
            "quality_contract_version":6,
            "master_prompt_sha256":MASTER_PROMPT_SHA256,
            "visual_concepts_protocol":"v1",
            "creative_directions":directions,
            "creative_selection":{
                "selected_id":selected,
                "rejected_ids":[directions[1]["id"],directions[2]["id"]],
                "business_reason":"Selected documentary approach is grounded in the actual original upholstery workshop, while the other concepts reduce the client's visual craft signature."
            },
            "concept_comparison_review":{
                "selected_id":selected,
                "rejected_ids":[directions[1]["id"],directions[2]["id"]],
                "reviewer":"editorial reviewer",
                "reviewed_at":datetime.now(timezone.utc).isoformat(),
                "comparative_notes":"The documentary hero exposes actual workshop process, while a product-first shop would misrepresent the repair workflow. The competing timeline is weaker on phone layouts and appointment access."
            },
            "rendered_concept_previews":[]
        }
        media=root/"_concept_evidence"
        media.mkdir()
        for i,d in enumerate(directions):
            record={"id":d["id"]}
            for j,(vp,w,h) in enumerate((("desktop",1100,650),("mobile",390,690))):
                file=media/f"{d['id']}-{vp}.png"
                payload=png(w,h,((i*50+40)%255,(j*80+80)%255,(i*20+20)%255))
                file.write_bytes(payload)
                record[vp]="_concept_evidence/"+file.name
                record[vp+"_sha256"]=hashlib.sha256(payload).hexdigest()
            manifest["rendered_concept_previews"].append(record)
        return manifest

    def test_real_three_distinct_rendered_concepts_allow_only_concept_preflight(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp)
            manifest=self._fixture(root)
            result=verify_demo_concept_evidence("unused-real-client",root,manifest)
            self.assertEqual(result["screenshots"],6)
            self.assertIn("NOT_PREMIUM_APPROVAL",result["status"])

    def test_old_prompt_or_missing_actual_render_cannot_be_passed_by_promises(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp);manifest=self._fixture(root)
            manifest["master_prompt_sha256"]="old-prompt"
            with self.assertRaisesRegex(ValueError,"current master prompt"):
                verify_demo_concept_evidence("client",root,manifest)
            manifest["master_prompt_sha256"]=MASTER_PROMPT_SHA256
            manifest["rendered_concept_previews"][0]["mobile"] = "https://imaginary.example.org/mobile.png"
            with self.assertRaises(ValueError):
                verify_demo_concept_evidence("client",root,manifest)

    def test_same_render_reused_as_three_variants_is_blocked(self):
        with TemporaryDirectory() as tmp:
            root=Path(tmp);manifest=self._fixture(root)
            one=manifest["rendered_concept_previews"][0]
            for record in manifest["rendered_concept_previews"][1:]:
                record["mobile"],record["mobile_sha256"]=one["mobile"],one["mobile_sha256"]
            with self.assertRaisesRegex(ValueError,"re-used"):
                verify_demo_concept_evidence("client",root,manifest)


if __name__ == "__main__":
    unittest.main()

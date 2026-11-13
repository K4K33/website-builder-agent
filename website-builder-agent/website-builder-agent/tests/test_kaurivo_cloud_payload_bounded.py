"""Production Goodcaf regression: full source QA, bounded cloud payloads.

No real customers, external APIs, AI fees, or file mutation in this test.
"""
from __future__ import annotations

import base64
import io
import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import Mock, patch

from PIL import Image
from utils.kaurivo_ai_source_packet import (
    pack_research_source_excerpts, compact_reference_for_prompt,
    MAX_RESEARCH_PACKET_CHARS,
)
from utils.kaurivo_cloud_vision_packet import (
    compact_vision_user_content, MAX_BYTES_PER_IMAGE, MAX_IMAGES,
)
from utils import cloudflare_free_ai as cf
from utils.source_fidelity import source_manifest

ROOT=Path(__file__).resolve().parents[1]
RESEARCH=(ROOT/"agents/research.py").read_text(encoding="utf-8")
FLOW=(ROOT.parents[1]/".github/workflows/kaurivo-demo-worker.yml").read_text(encoding="utf-8")


class ResearchPayloadTests(unittest.TestCase):
    def test_24_long_real_routes_preserved_in_budgeted_ai_packet(self):
        full = []
        for i in range(24):
            text=("Original brand and opening hours menu allergen information. "*450
                  + "Open daily 10-16; cafe menu; G / L / M verified by source.\n"
                  + "Call 040 123 4567. Address Original Street 2.\n"
                  + "Footer legal info and actual original 3D gallery. "*200)
            full.append({
                "url":f"https://source.example.org/original-{i}/",
                "title":f"Actual original source page {i}",
                "headings":[f"Heading {i}", f"Allergen and menu {i}"],
                "text":text,
                "source_identity":{"logo":"https://source.example.org/logo.png",
                    "original_content_photos":[{"src":"https://source.example.org/a.jpg"}]*30},
                "price_faq_evidence":{"price_sources":list(range(20))},
                "header_assets":[{"src":"https://source.example.org/logo.png"}]*30,
                "footer_assets":[{"src":"https://source.example.org/partner.png"}]*30,
                "source_block_samples":[{"text":"Menu and real dish details."}]*20,
            })
        original=json.dumps(full,ensure_ascii=False)
        compact=pack_research_source_excerpts(full)
        self.assertLessEqual(len(json.dumps(compact,ensure_ascii=False)),
                             MAX_RESEARCH_PACKET_CHARS)
        self.assertEqual(len(compact),24)
        for i,item in enumerate(compact):
            self.assertEqual(item["url"],full[i]["url"])
            self.assertEqual(item["headings"],full[i]["headings"])
            self.assertIn("EXCERPTS ONLY",item["evidence_scope"])
        self.assertIn("allergen",compact[0]["text_excerpts"].lower())
        self.assertEqual(original,json.dumps(full,ensure_ascii=False))
        self.assertGreater(len(original),len(json.dumps(compact,ensure_ascii=False))*2)

    def test_reference_view_evidence_still_has_exact_three_live_operators(self):
        full=[{"url":f"https://real-operator-{i}.example.org","title":f"Cafe {i}",
               "site_text":"coffee and espresso service "*700,
               "industry_match":{"same_industry":True,"evidence_quote":"coffee"},
               "screenshots":{"desktop":f"/private/{i}-desktop.png",
                              "mobile":f"/private/{i}-mobile.png"},
               "unrelated_secret_field":"not necessary for AI"}
              for i in range(3)]
        compact=compact_reference_for_prompt(full)
        self.assertEqual(len(compact),3)
        self.assertEqual([r["screenshot_views"] for r in compact],
                         [["desktop","mobile"]]*3)
        self.assertTrue(all(len(r["source_text_excerpt"])<=1400 for r in compact))
        self.assertNotIn("unrelated_secret_field",json.dumps(compact))
        self.assertIn("unrelated_secret_field",full[0])

    def test_original_source_manifest_and_qa_are_not_replaced_by_packet(self):
        self.assertIn('source_excerpts = pack_research_source_excerpts(source_excerpts)',RESEARCH)
        self.assertIn('source_manifest({"source_inventory":source_inventory})',RESEARCH)
        self.assertIn('source_inventory=source_inventory',RESEARCH)
        self.assertIn('reference_images, image_labels = reference_image_inputs(reference_evidence)',RESEARCH)
        self.assertIn('validate_verified_profile(',RESEARCH)
        self.assertIn("quality_gate_not_approved",(
            ROOT/"scripts/run_kaurivo_demo_queue.py").read_text(encoding="utf-8"))


class CloudflareVisionBudgetTests(unittest.TestCase):
    def test_original_fullpage_png_untouched_cloud_has_bounded_jpeg(self):
        with TemporaryDirectory() as tmp:
            p=Path(tmp)/"real-original.png"
            Image.new("RGB",(1400,6000),(230,230,210)).save(p)
            unchanged=p.read_bytes()
            content=compact_vision_user_content("Compare actual layout",[str(p)])
            self.assertEqual(p.read_bytes(),unchanged)
            self.assertEqual(len(content),2)
            uri=content[1]["image_url"]["url"]
            self.assertTrue(uri.startswith("data:image/jpeg;base64,"))
            data=base64.b64decode(uri.split(",",1)[1])
            self.assertLessEqual(len(data),MAX_BYTES_PER_IMAGE)
            with Image.open(io.BytesIO(data)) as sample:
                self.assertEqual(sample.format,"JPEG")
                self.assertLessEqual(sample.width,1300)
                self.assertLessEqual(sample.height,3200)

    def test_missing_screenshot_and_too_many_images_fail_closed(self):
        with self.assertRaisesRegex(RuntimeError,"FREE_AI_MEDIA_MISSING"):
            compact_vision_user_content("real",["/definitely/missing.png"])
        with self.assertRaisesRegex(RuntimeError,"FREE_AI_MEDIA_TOO_LARGE"):
            compact_vision_user_content("real",["/fake.png"]*(MAX_IMAGES+1))


class RejectionDiagnosticsTests(unittest.TestCase):
    def test_http_400_logs_numeric_provider_code_not_customer_source_or_key(self):
        reply=Mock(status_code=400)
        reply.json.return_value={"errors":[{
            "code":12345,
            "message":"This model's maximum context length is smaller than customer-private-source-XYZ."}]}
        settings={
            "FREE_ONLY":"1",
            "KAURIVO_CLOUDFLARE_WORKERS_FREE_CONFIRMED":"1",
            "CLOUDFLARE_ACCOUNT_ID":"a"*32,
            "CLOUDFLARE_API_TOKEN":"secret"*9,
        }
        from contextlib import redirect_stdout
        out=io.StringIO()
        with patch.dict(os.environ,settings,clear=True), \
             patch.object(cf,"_ATTEMPTS",0), \
             patch.object(cf.requests,"post",return_value=reply), \
             redirect_stdout(out):
            with self.assertRaisesRegex(RuntimeError,"FREE_MODEL_REQUEST_REJECTED"):
                cf.chat_cloudflare_free("source","private-inventory-marker-A1",
                                       stage="research",max_tokens=3500)
        safe=out.getvalue()
        self.assertIn("provider_code=12345",safe)
        self.assertIn("reason_class=context",safe)
        self.assertNotIn("customer-private-source-XYZ",safe)
        self.assertNotIn("private-inventory-marker-A1",safe)
        self.assertNotIn("secret"*9,safe)

    def test_never_turn_free_only_off_or_unblock_paid_model(self):
        self.assertIn('FREE_ONLY: "1"',FLOW)
        self.assertIn("vars.KAURIVO_CLOUDFLARE_WORKERS_FREE_CONFIRMED || '0'",FLOW)
        self.assertIn("secrets.KAURIVO_CLOUDFLARE_API_TOKEN",FLOW)


if __name__=="__main__":
    unittest.main()

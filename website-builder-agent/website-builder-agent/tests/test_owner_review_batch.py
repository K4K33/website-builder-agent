"""Enforce truthful technical-preview HOLD without bypassing agency quality gates."""
from __future__ import annotations
import base64, io, json, lzma, tarfile, tempfile, unittest
from pathlib import Path
from scripts.install_unapproved_owner_review_batch import validate_and_install, SITES

ROOT=Path(__file__).resolve().parents[1]
BATCH=ROOT/"data"/"manual_owner_reviews"/"20261117_three_local_concepts.tar.xz.b64"
class OwnerReviewBatchTests(unittest.TestCase):
    def test_exact_batch_has_twelve_pages_and_no_quality_pass(self):
        with tempfile.TemporaryDirectory() as td:
            dest=Path(td)/"review"
            report=validate_and_install(BATCH,dest)
            self.assertEqual(report["count_sites"],3)
            self.assertEqual(report["count_html"],12)
            self.assertEqual(report["status"],"TECHNICAL_PREVIEW_ONLY / QUALITY_PENDING / HOLD")
            self.assertFalse(report["client_outreach_allowed"])
            self.assertEqual(report["independent_visual_95"],"NOT_PERFORMED")
            self.assertEqual(report["original_image_rights"],"UNVERIFIED")
            for slug,routes in SITES.items():
                for route in routes:
                    page=(dest/slug/route).read_text()
                    self.assertIn("noindex",page)
                    self.assertIn("QUALITY_PENDING",page)
                    self.assertIn("EI JULKAISUUN",page)
            self.assertTrue((dest/"QUALITY_PENDING.json").is_file())
    def test_unsafe_tar_path_is_rejected_before_creating_public_file(self):
        with tempfile.TemporaryDirectory() as td:
            tarbytes=io.BytesIO()
            with tarfile.open(fileobj=tarbytes,mode="w") as tf:
                data=b"<html>oops</html>"
                info=tarfile.TarInfo("../outside/index.html")
                info.size=len(data);tf.addfile(info,io.BytesIO(data))
            archive=Path(td)/"bad.b64"
            archive.write_text(base64.b64encode(lzma.compress(tarbytes.getvalue())).decode())
            dest=Path(td)/"public"
            with self.assertRaisesRegex(ValueError,"Unsafe|Unexpected"):
                validate_and_install(archive,dest)
            self.assertFalse(dest.exists())
    def test_missing_one_website_page_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            raw=lzma.decompress(base64.b64decode(BATCH.read_text().strip()))
            output=io.BytesIO()
            with tarfile.open(fileobj=io.BytesIO(raw),mode="r:") as source,tarfile.open(fileobj=output,mode="w") as target:
                for member in source:
                    if member.name=="talousfocus/palvelut/index.html": continue
                    target.addfile(member,source.extractfile(member) if member.isfile() else None)
            archive=Path(td)/"partial.b64"
            archive.write_text(base64.b64encode(lzma.compress(output.getvalue())).decode())
            dest=Path(td)/"public"
            with self.assertRaisesRegex(ValueError,"incomplete pages"):
                validate_and_install(archive,dest)
            self.assertFalse(dest.exists())
    def test_static_publish_does_not_skip_staging_audit(self):
        workflow=(ROOT.parents[1]/".github/workflows/static.yml").read_text()
        self.assertIn("audit_changed_demo_previews.py",workflow)
        self.assertIn("install_unapproved_owner_review_batch.py",workflow)
        self.assertLess(workflow.index("install_unapproved_owner_review_batch.py"),workflow.index("actions/upload-pages-artifact"))
if __name__=="__main__":unittest.main()

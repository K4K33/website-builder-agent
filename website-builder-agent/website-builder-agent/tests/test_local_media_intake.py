"""No-network media packaging tests for the universal website Builder."""
import base64
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from utils.local_media_intake import stage_local_media
from utils.visual_media_gate import audit_visual_media


PNG_1PX = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/Fe0AAAAASUVORK5CYII="
)


class LocalMediaIntakeTests(unittest.TestCase):
    def item(self, **changes):
        base = {
            "file": "company/photos/work.png",
            "purpose": "service example",
            "alt": "Service work",
            "rights_status": "client_approved",
            "source_note": "Customer-approved original media",
        }
        return base | changes

    def test_stages_exact_hashed_local_asset_into_site(self):
        with TemporaryDirectory() as folder:
            root = Path(folder) / "media_intake"
            photo = root / "company/photos/work.png"
            photo.parent.mkdir(parents=True)
            photo.write_bytes(PNG_1PX)
            site = Path(folder) / "output" / "new-customer"
            assets = stage_local_media([self.item()], intake_root=root, output_dir=site)
            self.assertEqual(len(assets), 1)
            self.assertTrue(assets[0]["src"].startswith("assets/work-"))
            self.assertEqual((site / assets[0]["src"]).read_bytes(), PNG_1PX)
            self.assertTrue(assets[0]["production_rights_verified"])
            html = f'<main><section class="hero"><img src="{assets[0]["src"]}" alt="Service work"></section></main>'
            self.assertTrue(audit_visual_media(
                html, html_path=site / "index.html"
            )["owner_preview_ready"])
            self.assertEqual(
                assets, stage_local_media([self.item()], intake_root=root, output_dir=site)
            )

    def test_demo_only_media_is_not_silently_licensed(self):
        with TemporaryDirectory() as folder:
            root = Path(folder) / "intake"
            source = root / "company/photos/work.png"
            source.parent.mkdir(parents=True)
            source.write_bytes(PNG_1PX)
            asset = stage_local_media(
                [self.item(rights_status="internal_demo_only")],
                intake_root=root, output_dir=Path(folder) / "output"
            )[0]
            self.assertFalse(asset["production_rights_verified"])
            self.assertEqual(asset["rights_status"], "internal_demo_only")

    def test_broken_files_unsafe_svg_and_path_escapes_are_rejected(self):
        with TemporaryDirectory() as folder:
            root = Path(folder) / "intake"
            root.mkdir()
            (root / "bad.svg").write_text(
                '<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'
            )
            (root / "pretend.jpg").write_text("not a jpeg")
            output = Path(folder) / "output"
            for item in (
                self.item(file="../hidden.png"),
                self.item(file="bad.svg"),
                self.item(file="pretend.jpg"),
                self.item(rights_status="unknown"),
            ):
                with self.subTest(item=item):
                    with self.assertRaises(ValueError):
                        stage_local_media([item], intake_root=root, output_dir=output)
            self.assertFalse((output / "assets").exists())

    def test_html_builder_accepts_only_prepackaged_local_images(self):
        from agents.builder import _write_html
        import config

        with TemporaryDirectory() as folder:
            root = Path(folder) / "intake"
            photo = root / "company/photos/work.png"
            photo.parent.mkdir(parents=True)
            photo.write_bytes(PNG_1PX)
            with patch.object(config, "OUTPUT_DIR", str(Path(folder) / "output")):
                output = Path(config.OUTPUT_DIR) / "new-customer"
                asset = stage_local_media(
                    [self.item()], intake_root=root, output_dir=output
                )[0]
                body = ('<!doctype html><html lang="fi"><head><title>New client</title>'
                        '<meta name="description" content="Real business">'
                        '<meta name="viewport" content="width=device-width"></head>'
                        '<body><header><nav><a href="#main">Home</a></nav></header>'
                        f'<main id="main"><h1>Client service</h1><img src="{asset["src"]}" alt="Work"></main>'
                        '<footer>Verified contact pending</footer></body></html>')
                result = _write_html("new-customer", body)
                self.assertTrue(Path(result).is_file())
                with self.assertRaisesRegex(RuntimeError, "Local media integrity failure"):
                    _write_html("another-customer", body)


if __name__ == "__main__":
    unittest.main()

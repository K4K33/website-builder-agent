"""Multi-page QA approval protects EACH route and the visible images."""
import hashlib
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

import config
from utils import publisher
from utils.site_integrity import site_files,site_sha256

class CompleteSiteIntegrityTests(unittest.TestCase):
    def make_site(self,base):
        root=Path(base)/"output"/"studio"
        (root/"palvelut").mkdir(parents=True)
        (root/"assets").mkdir()
        (root/"index.html").write_text("<!doctype html><h1>Homepage</h1>",encoding="utf-8")
        (root/"palvelut"/"index.html").write_text("<!doctype html><h1>Real services</h1>",encoding="utf-8")
        (root/"assets"/"photo.png").write_bytes(b"approved test asset")
        return root

    def test_subpage_or_photo_change_invalidates_the_complete_build(self):
        with TemporaryDirectory() as temp:
            root=self.make_site(temp)
            paths=["index.html","palvelut/index.html"]
            digest=site_sha256(root,paths)
            self.assertEqual(len(site_files(root,paths)),3)
            (root/"palvelut"/"index.html").write_text("<h1>Changed without QA</h1>")
            self.assertNotEqual(site_sha256(root,paths),digest)
            (root/"palvelut"/"index.html").write_text("<!doctype html><h1>Real services</h1>")
            self.assertEqual(site_sha256(root,paths),digest)
            (root/"assets"/"photo.png").write_bytes(b"tampered")
            self.assertNotEqual(site_sha256(root,paths),digest)

    def test_full_bundle_hash_changes_when_css_or_js_or_font_changes(self):
        with TemporaryDirectory() as temp:
            root = self.make_site(temp)
            routes = ["index.html", "palvelut/index.html"]
            (root / "assets" / "site.css").write_text(
                ":root{--brand-primary:#efdae2}body{font:16px Arial}",
                encoding="utf-8"
            )
            (root / "assets" / "site.js").write_text(
                "document.documentElement.dataset.ready='yes'", encoding="utf-8"
            )
            (root / "assets" / "identity.woff2").write_bytes(b"test font")
            baseline = site_sha256(root, routes)
            self.assertEqual(len(site_files(root, routes)), 6)
            (root / "assets" / "site.css").write_text(
                ":root{--brand-primary:#25121f}body{font:16px Arial}",
                encoding="utf-8"
            )
            self.assertNotEqual(site_sha256(root, routes), baseline)
            (root / "assets" / "site.css").write_text(
                ":root{--brand-primary:#efdae2}body{font:16px Arial}",
                encoding="utf-8"
            )
            self.assertEqual(site_sha256(root, routes), baseline)
            (root / "assets" / "site.js").write_text(
                "document.documentElement.dataset.ready='no'", encoding="utf-8"
            )
            self.assertNotEqual(site_sha256(root, routes), baseline)
            (root / "assets" / "site.js").write_text(
                "document.documentElement.dataset.ready='yes'", encoding="utf-8"
            )
            (root / "assets" / "identity.woff2").write_bytes(b"different font")
            self.assertNotEqual(site_sha256(root, routes), baseline)

    def test_root_level_logo_and_custom_media_folder_are_hash_protected(self):
        with TemporaryDirectory() as temp:
            root=self.make_site(temp)
            (root/"images").mkdir()
            (root/"images"/"portrait.webp").write_bytes(b"actual-client-photo")
            (root/"logo.svg").write_text("<svg>approved mark</svg>",encoding="utf-8")
            routes=["index.html","palvelut/index.html"]
            baseline=site_sha256(root,routes)
            bundled={rel for rel,_ in site_files(root,routes)}
            self.assertIn("images/portrait.webp",bundled)
            self.assertIn("logo.svg",bundled)
            (root/"images"/"portrait.webp").write_bytes(b"changed after approval")
            self.assertNotEqual(site_sha256(root,routes),baseline)
            (root/"images"/"portrait.webp").write_bytes(b"actual-client-photo")
            (root/"logo.svg").write_text("<svg>replaced brand</svg>",encoding="utf-8")
            self.assertNotEqual(site_sha256(root,routes),baseline)

    def test_unreviewed_html_or_public_symlink_cannot_sneak_into_client_release(self):
        with TemporaryDirectory() as temp:
            root=self.make_site(temp)
            (root/"secret-offer.html").write_text("<p>Not QA reviewed</p>",encoding="utf-8")
            with self.assertRaisesRegex(RuntimeError,"Unreviewed HTML route"):
                site_sha256(root,["index.html","palvelut/index.html"])
            (root/"secret-offer.html").unlink()
            (root/"images").mkdir()
            (root/"images"/"fake-logo.png").symlink_to(root/"assets"/"photo.png")
            with self.assertRaisesRegex(RuntimeError,"Symlink"):
                site_sha256(root,["index.html","palvelut/index.html"])

    def test_publisher_copies_all_pages_and_refuses_stale_snapshot(self):
        with TemporaryDirectory() as temp:
            root=self.make_site(temp)
            routes=["index.html","palvelut/index.html"]
            full=site_sha256(root,routes)
            home_hash=hashlib.sha256((root/"index.html").read_bytes()).hexdigest()
            company={
                "name":"Studio",
                "build":{"version":1,"output_path":str(root/"index.html"),
                         "page_paths":routes},
                "qa":{"overall_pass":True,"build_version":1,
                      "html_sha256":home_hash,"site_sha256":full},
                "approval":{"approved":True,"build_version":1,
                            "html_sha256":home_hash,"site_sha256":full}
            }
            with (patch.object(config,"OUTPUT_DIR",str(Path(temp)/"output")),
                  patch.object(publisher,"PUBLISH_DIR",str(Path(temp)/"public")),
                  patch.object(publisher,"_resolve_company",return_value=("studio",company)),
                  patch.object(publisher,"upsert_company")):
                url=publisher.publish_site("studio")
                self.assertIn("/demos/studio/",url)
                dest=Path(temp)/"public"/"studio"
                self.assertEqual((dest/"palvelut"/"index.html").read_bytes(),
                                 (root/"palvelut"/"index.html").read_bytes())
                self.assertEqual((dest/"assets"/"photo.png").read_bytes(),
                                 (root/"assets"/"photo.png").read_bytes())
                (root/"palvelut"/"index.html").write_text("changed")
                with self.assertRaisesRegex(RuntimeError,"QA-approved"):
                    publisher.publish_site("studio")

if __name__=="__main__":
    unittest.main()

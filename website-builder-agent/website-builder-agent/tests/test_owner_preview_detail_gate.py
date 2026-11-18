"""Current and future owner previews must have working site-level polish."""
import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import audit_changed_owner_previews as gate


SLUG = "s-rasasen-autohuolto-v2"


class OwnerPreviewDetailTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        root = Path(self.tmp.name)
        self.base = root / "previews"
        self.data = root / "evidence"
        self.data.mkdir(parents=True)
        shutil.copytree(gate.BASE / SLUG, self.base / SLUG)
        shutil.copy2(gate.EVIDENCE / (SLUG + ".json"),
                     self.data / (SLUG + ".json"))
        self.patch_base = patch.object(gate, "BASE", self.base)
        self.patch_evidence = patch.object(gate, "EVIDENCE", self.data)
        self.patch_base.start()
        self.patch_evidence.start()

    def tearDown(self):
        self.patch_evidence.stop()
        self.patch_base.stop()
        self.tmp.cleanup()

    def check(self):
        return gate.check_preview(SLUG)

    def test_complete_multiroute_preview_is_source_and_metadata_clean(self):
        self.assertEqual(self.check(), [])

    def test_tab_title_is_not_an_arbitrary_demo_label(self):
        f = self.base / SLUG / "index.html"
        f.write_text(f.read_text().replace(
            "S. Räsäsen Autohuolto Oy | Autohuolto Keravalla", "index"),
            encoding="utf-8")
        self.assertTrue(any("browser title" in p for p in self.check()))

    def test_favicon_and_stylesheet_are_required_real_assets(self):
        (self.base / SLUG / "assets/preview-favicon.svg").unlink()
        self.assertTrue(any("missing locally deployed asset" in p for p in self.check()))
        (self.base / SLUG / "assets/site.css").unlink()
        self.assertTrue(any("local CSS/JS missing" in p for p in self.check()))

    def test_broken_image_or_hidden_missing_brand_detail_blocks(self):
        page = self.base / SLUG / "index.html"
        text = page.read_text()
        text = text.replace("assets/engine-technical.svg", "assets/missing.jpg")
        page.write_text(text)
        self.assertTrue(any("missing locally deployed asset" in p for p in self.check()))

    def test_disclaimer_must_be_visible_even_when_mobile_detail_is_hidden(self):
        f = self.base / SLUG / "index.html"
        f.write_text(f.read_text().replace(
            "KAURIVO · EI YRITYKSEN VIRALLINEN SIVU",
            "KAURIVO / SUUNNITTELUDEMO"),
            encoding="utf-8")
        self.assertTrue(any("non-official demo disclaimer" in p for p in self.check()))

    def test_full_width_service_copy_not_squeezed_by_decorative_grid_track(self):
        # Real user video caught a ~70px description column that a standard
        # no-overflow browser assertion missed. Keep the universal live smoke.
        css = (self.base / SLUG / "assets/site.css").read_text(encoding="utf-8")
        self.assertIn(
            ".service-row{display:grid;grid-template-columns:minmax(0,1fr) minmax(150px,180px)",
            css,
        )
        self.assertNotIn("grid-template-columns:70px 1fr 180px", css)
        self.assertNotIn("grid-template-columns:34px 1fr", css)
        smoke = (gate.ROOT / "scripts/smoke_live_owner_previews.py").read_text(encoding="utf-8")
        self.assertIn("serviceTextWidths", smoke)
        self.assertIn('item["width"] < 280', smoke)

    def test_pro_reviewer_must_evaluate_ai_signature_from_real_visuals(self):
        prompt = (gate.ROOT / "docs/KAURIVO_MESTARI_PROMPT.md").read_text(encoding="utf-8")
        self.assertIn("AI-TUNNISTETTAVUUS", prompt)
        self.assertIn("lähetetystä näytön tallenteesta", prompt)
        self.assertIn("venytetty", prompt)
        self.assertIn("turhat 01/02/03-numerot", prompt)

    def test_no_contact_or_false_services_claims_and_no_outreach(self):
        page = self.base / SLUG / "palvelut/index.html"
        page.write_text(page.read_text().replace(
            "ruostekorjauksia", "puuttuva-palvelutieto"), encoding="utf-8")
        self.assertTrue(any("Source fact omitted" in p for p in self.check()))
        manifest = self.data / (SLUG + ".json")
        data = json.loads(manifest.read_text())
        data["outreach_authorized"] = True
        manifest.write_text(json.dumps(data))
        self.assertTrue(any("sales authorization" in p for p in self.check()))


if __name__ == "__main__":
    unittest.main()

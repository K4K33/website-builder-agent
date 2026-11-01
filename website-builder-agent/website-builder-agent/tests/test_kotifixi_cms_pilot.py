"""Kotifixi CMS pilot: deterministic isolated editing simulation, no paid calls."""
import importlib.util
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

KIT = Path(__file__).resolve().parents[1] / "pilots" / "kotifixi"
spec = importlib.util.spec_from_file_location("kotifixi_pilot_render", KIT / "render_site.py")
renderer = importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)


class KotifixiOwnerEditingPilotTests(unittest.TestCase):
    def test_html_rendering_matches_cms_model_and_is_noindex(self):
        with TemporaryDirectory() as d:
            dest = renderer.render(output_dir=Path(d) / "dist")
            output = dest.read_text(encoding="utf-8")
        self.assertIn("KAURIVO · KOTIFIXI CMS -KOEPROJEKTI", output)
        self.assertIn('<meta name="robots" content="noindex,nofollow">', output)
        self.assertIn("Enemmän aikaa <em>elämälle.</em>", output)
        self.assertNotIn("{{hero_heading}}", output)
        self.assertIn("kotifixi.", output)
        self.assertIn('href="mailto:kotifixi@gmail.com"', output)

    def test_text_phone_email_and_picture_update_into_generated_site(self):
        values = json.loads((KIT / "content" / "site.json").read_text(encoding="utf-8"))
        values.update(hero_heading="Uusi muokattu otsikko",
                      hero_emphasis="onnistui.",
                      phone_display="040 123 4567", phone_tel="+358401234567",
                      email="demo-test@example.org",
                      service1_title="Muokattu palvelu",
                      hero_image="https://example.org/owner-approved-photo.webp")
        with TemporaryDirectory() as d:
            data = Path(d) / "values.json"
            data.write_text(json.dumps(values, ensure_ascii=False), encoding="utf-8")
            dest = renderer.render(data_path=data, output_dir=Path(d) / "dist")
            output = dest.read_text(encoding="utf-8")
        for expected in ("Uusi muokattu otsikko", "onnistui.", "040 123 4567",
                         "+358401234567", "demo-test@example.org",
                         "Muokattu palvelu", "owner-approved-photo.webp"):
            self.assertIn(expected, output)
        self.assertNotIn('href="mailto:kotifixi@gmail.com"', output)

    def test_escaped_editor_text_cannot_inject_html(self):
        values = json.loads((KIT / "content" / "site.json").read_text(encoding="utf-8"))
        values["hero_heading"] = '<img src=x onerror="alert(1)">'
        with TemporaryDirectory() as d:
            data = Path(d) / "content.json"
            data.write_text(json.dumps(values), encoding="utf-8")
            dest = renderer.render(data_path=data, output_dir=Path(d) / "dist")
            output = dest.read_text(encoding="utf-8")
        self.assertNotIn('<img src=x onerror="alert(1)">', output)
        self.assertIn("&lt;img src=x", output)

    def test_unsafe_links_and_missing_data_fail_closed(self):
        values = json.loads((KIT / "content" / "site.json").read_text(encoding="utf-8"))
        with TemporaryDirectory() as d:
            data = Path(d) / "bad.json"
            values["pricing_url"] = "javascript:alert(1)"
            data.write_text(json.dumps(values), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "HTTPS"):
                renderer.render(data_path=data, output_dir=Path(d) / "dist")
            values["pricing_url"] = "https://example.org/hinnasto/"
            del values["hero_image"]
            data.write_text(json.dumps(values), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Missing CMS fields"):
                renderer.render(data_path=data, output_dir=Path(d) / "dist")

    def test_saving_local_media_does_not_escape_uploads_folder(self):
        values = json.loads((KIT / "content" / "site.json").read_text(encoding="utf-8"))
        values["hero_image"] = "/media/../../other-files/hidden.png"
        with TemporaryDirectory() as d:
            data = Path(d) / "bad.json"
            data.write_text(json.dumps(values), encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Invalid uploaded media path"):
                renderer.render(data_path=data, output_dir=Path(d) / "dist")

    def test_config_is_for_separate_repository_and_private_auth(self):
        config = (KIT / ".pages.yml").read_text(encoding="utf-8")
        self.assertIn("path: content/site.json", config)
        self.assertIn("settings:", config)
        self.assertIn("merge: true", config)
        self.assertIn("delete: false", config)
        self.assertIn("OWN separate GitHub repository", config)


if __name__ == "__main__":
    unittest.main()

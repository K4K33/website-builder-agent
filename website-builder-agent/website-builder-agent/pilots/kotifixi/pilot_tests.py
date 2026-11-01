"""Standalone local checks for isolated Kotifixi private-repo editing trial.

Run: python -m unittest pilot_tests -v
Never touches a live website, domain, email, third-party API or paid credit.
"""
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from render_site import HERE, render


class PilotTests(unittest.TestCase):
    def test_private_staging_render_is_not_indexable(self):
        with TemporaryDirectory() as d:
            path = render(output_dir=Path(d) / "dist")
            page = path.read_text(encoding="utf-8")
            self.assertIn("noindex,nofollow", page)
            self.assertIn("KOTIFIXI CMS -KOEPROJEKTI", page)
            self.assertIn("<h1>Enemmän aikaa <em>elämälle.</em></h1>", page)

    def test_changes_render_without_any_public_deployment(self):
        values = json.loads((HERE / "content" / "site.json").read_text(encoding="utf-8"))
        values["hero_heading"] = "Omistajan testiotsikko"
        values["email"] = "pilot-only@example.org"
        with TemporaryDirectory() as d:
            data = Path(d) / "owner-edit.json"
            data.write_text(json.dumps(values, ensure_ascii=False), encoding="utf-8")
            path = render(data_path=data, output_dir=Path(d) / "preview")
            page = path.read_text(encoding="utf-8")
            self.assertIn("Omistajan testiotsikko", page)
            self.assertIn("mailto:pilot-only@example.org", page)
            self.assertNotIn("{{hero_heading}}", page)

    def test_no_automatic_hosting_or_domain_configuration(self):
        self.assertFalse((HERE / ".github" / "workflows" / "deploy.yml").exists())
        self.assertFalse((HERE / "CNAME").exists())
        self.assertFalse((HERE / "dist" / "CNAME").exists())


if __name__ == "__main__":
    unittest.main()

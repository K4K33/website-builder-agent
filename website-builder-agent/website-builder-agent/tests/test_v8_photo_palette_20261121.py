import unittest

from utils.brand_direction_v8 import audit_art_direction, repair_v8_findings


def research(photo_accent="#c4862e"):
    return {"v8_visual_protocol": "v8",
            "pre_build_brief": {"q3_brand_feel": {"photo_palette": {
                "suggested": "light",
                "light": {"canvas": "#f4f1ec", "surface": "#ebe4d9", "ink": "#2a2118",
                          "muted": "#6b5d4c", "accent": photo_accent, "accent_ink": "#2a2118",
                          "photo_dominant": "#9a6a2e"}}}}}


def page(color):
    return ("<!doctype html><html><head><style>:root{--accent:%s}"
            "a{background:%s}b{background:%s}</style></head><body><main><section>"
            "<h1>Otsikko</h1></section></main></body></html>" % (color, color, color))


class PhotoPaletteBrandGateTests(unittest.TestCase):
    def test_photo_derived_accent_is_company_evidence(self):
        audit = audit_art_direction({"index.html": page("#c4862e")}, research())
        self.assertFalse([f for f in audit["blocking"] if f["code"] == "unproven_brand_accent"])

    def test_model_rounding_is_tolerated(self):
        audit = audit_art_direction({"index.html": page("#c78a31")}, research())
        self.assertFalse([f for f in audit["blocking"] if f["code"] == "unproven_brand_accent"])

    def test_invented_accent_is_still_blocked_and_repaired_to_photo_colour(self):
        pages = {"index.html": page("#22ff55")}
        audit = audit_art_direction(pages, research())
        self.assertTrue([f for f in audit["blocking"] if f["code"] == "unproven_brand_accent"])
        fixed = repair_v8_findings(pages, research())
        self.assertNotIn("#22ff55", fixed["index.html"].lower())
        again = audit_art_direction(fixed, research())
        self.assertFalse([f for f in again["blocking"] if f["code"] == "unproven_brand_accent"])


if __name__ == "__main__":
    unittest.main()


class PaletteIsPersistedForGatesTests(unittest.TestCase):
    def test_concept_and_builder_persist_the_brief(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        concept = (root / "utils/concept_workflow.py").read_text(encoding="utf-8")
        builder = (root / "agents/builder.py").read_text(encoding="utf-8")
        self.assertIn("pre_build = ensure_pre_build_brief(research, media, root)\n"
                      "    # Browser and QA gates", concept)
        self.assertEqual(builder.count('upsert_company(slug, {"research": research})  # gates reload'), 2)

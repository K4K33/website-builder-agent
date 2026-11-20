"""Kaurivo Motion Kit: deterministic, escaped, accessible sections."""
import re
import unittest

from utils import motion_kit as kit

IMG = {"src": "assets/a.webp", "alt": "Elementti nostetaan paikalleen", "width": 1500, "height": 1125}
ACT = {"primary_action": {"label": "Kerro hankkeestasi", "href": "#yhteys"},
       "secondary_action": {"label": "Soita", "href": "tel:+358102805352"}}
SECTIONS = {
    "process_reveal": {"heading": "Puurakentamista avaimet käteen", "stages": [
        {"image": IMG, "title": "Elementit", "text": "Elementit valmistetaan tehtaalla."},
        {"image": IMG, "title": "Runko", "text": "Runko kootaan työmaalla."}], **ACT},
    "cinematic": {"image": IMG, "heading": "Otsikko", "lead": "Johdanto", **ACT},
    "masthead": {"image": IMG, "heading": "Otsikko", "lead": "Johdanto", "caption": "Kuvateksti", **ACT},
    "editorial_split": {"image": IMG, "heading": "Palvelut", "text": "Teksti",
                        "facts": [{"term": "Rivitalot", "detail": "Avaimet käteen"}]},
    "project_explorer": {"heading": "Työmaalta", "items": [{"image": IMG, "title": "A"}, {"image": IMG, "title": "B"}]},
    "before_after": {"heading": "Ennen ja jälkeen", "text": "Teksti", "before": IMG, "after": IMG},
}


def plan(first="process_reveal"):
    return {"title": "T", "description": "D", "company": {"name": "Yritys", "phone": "010 280 5352"},
            "nav": [{"label": "Palvelut", "href": "#palvelut"}],
            "tokens": {"accent": "#d2ae79", "font_display": "Anton", "display_leading": 1.02},
            "sections": [{"archetype": first, "slots": SECTIONS[first]},
                         {"archetype": "editorial_split", "slots": SECTIONS["editorial_split"]}],
            "contact": {"heading": "Yhteys", "lead": "Kerro", "address_lines": ["Katu 1"], "email": "a@b.fi"}}


class MotionKitTests(unittest.TestCase):
    def test_every_archetype_renders(self):
        for name in kit.ARCHETYPES:
            with self.subTest(name=name):
                html = kit.render_section({"archetype": name, "slots": SECTIONS[name]})
                self.assertTrue(html.startswith("<section"))
                self.assertIn('alt="', html)

    def test_text_is_escaped(self):
        slots = dict(SECTIONS["cinematic"], heading='<script>alert(1)</script>"')
        html = kit.render_section({"archetype": "cinematic", "slots": slots})
        self.assertNotIn("<script>alert", html)
        self.assertIn("&lt;script&gt;", html)

    def test_unsafe_links_and_images_are_rejected(self):
        bad_link = dict(SECTIONS["cinematic"], primary_action={"label": "x", "href": "javascript:alert(1)"})
        with self.assertRaises(ValueError):
            kit.render_section({"archetype": "cinematic", "slots": bad_link})
        bad_img = dict(SECTIONS["cinematic"], image={"src": "http://x/a.jpg", "alt": "a"})
        with self.assertRaises(ValueError):
            kit.render_section({"archetype": "cinematic", "slots": bad_img})
        with self.assertRaises(ValueError):
            kit.render_section({"archetype": "cinematic", "slots": dict(SECTIONS["cinematic"], image=dict(IMG, alt=""))})

    def test_tokens_accept_only_hex_and_font_names(self):
        css = kit.render_tokens({"accent": "red;}body{display:none", "ink": "#112233",
                                 "font_display": "Anton</style>", "font_body": "Fira Sans"})
        self.assertIn("--k-ink: #112233;", css)
        self.assertNotIn("display:none", css)
        self.assertNotIn("</style>", css)
        self.assertIn("'Fira Sans'", css)

    def test_page_requires_hero_first_and_keeps_static_fallback(self):
        with self.assertRaises(ValueError):
            kit.render_page(plan("editorial_split"))
        html = kit.render_page(plan())
        self.assertIn("prefers-reduced-motion: reduce", html)
        self.assertIn("k-static", html)               # JS/reduced-motion fallback
        self.assertIn('<h1 class="k-display">', html)
        self.assertEqual(len(re.findall(r"<h1\b", html)), 1)
        self.assertIn('href="tel:0102805352"', html)
        self.assertIn('class="k-skip"', html)

    def test_stage_counts_are_bounded(self):
        with self.assertRaises(ValueError):
            kit.render_section({"archetype": "process_reveal",
                                "slots": dict(SECTIONS["process_reveal"], stages=SECTIONS["process_reveal"]["stages"][:1])})

    def test_kit_ships_no_brand_or_stock_media(self):
        css, js = kit.kit_css(), kit.kit_js()
        self.assertNotRegex(css + js, r"https?://")
        self.assertNotIn("unsplash", (css + js).lower())


if __name__ == "__main__":
    unittest.main()

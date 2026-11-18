"""Browser title, icon and actual demo-opening standards are never optional."""
import unittest
from utils.demo_browser_identity import audit_browser_identity

FULLNAME="S. Räsäsen Autohuolto Oy"
TITLE="Autohuolto Keravalla | S. Räsäsen Autohuolto Oy"

def page(title=TITLE,icon=True,name=FULLNAME,lang="fi",demo=True):
    link='<link rel="icon" href="assets/preview-favicon.svg" data-demo-neutral-icon>' if icon else ''
    band='<div class="demo-band">Itsenäinen konsepti, ei virallinen sivu</div>' if demo else ''
    return (f'<html lang="{lang}"><head><title>{title}</title>'
            '<meta name="description" content="Autohuollot Keravalla henkilöautoille, tutustu palveluihin ja ota yhteyttä.">'
            f'{link}</head><body>{band}<header>{name}</header>'
            '<nav><a href="palvelut/">Palvelut</a></nav><main><h1>Autohuolto Keravalla</h1></main></body></html>')


class TabPresentationGate(unittest.TestCase):
    def test_real_title_and_explicit_neutral_preview_icon_pass(self):
        r=audit_browser_identity({"index.html":page()},FULLNAME)
        self.assertTrue(r["pass"],r["issues"])

    def test_generic_or_internal_title_never_passes(self):
        for title in ("index","Etusivu","Kaurivo Demo",TITLE+" · Kaurivon suunnitteludemo"):
            with self.subTest(title=title):
                self.assertFalse(audit_browser_identity({"index.html":page(title=title)},FULLNAME)["pass"])

    def test_missing_favicon_blocks_visual_completion(self):
        r=audit_browser_identity({"index.html":page(icon=False)},FULLNAME)
        self.assertFalse(r["pass"])
        self.assertIn("favicon",str(r["issues"]).lower())

    def test_unverified_new_company_name_blocks(self):
        self.assertFalse(audit_browser_identity({"index.html":page(name="Aivan eri firma",title="Joku nimi | Keravan korjaamo")},FULLNAME)["pass"])

    def test_neutral_icon_without_demo_disclaimer_is_rejected(self):
        self.assertFalse(audit_browser_identity({"index.html":page(demo=False)},FULLNAME)["pass"])

    def test_all_routes_receive_full_checks(self):
        r=audit_browser_identity({"index.html":page(),
            "palvelut/index.html":page(icon=False)},FULLNAME)
        self.assertFalse(r["pass"])
        self.assertEqual(r["pages_checked"],2)

    def test_wrong_page_language_is_rejected(self):
        self.assertFalse(audit_browser_identity({"index.html":page(lang="xx")},FULLNAME)["pass"])

if __name__ == "__main__":
    unittest.main()

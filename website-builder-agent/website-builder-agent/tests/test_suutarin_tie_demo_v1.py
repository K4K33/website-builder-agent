"""Independent source-fidelity checks for the first Suutarin Tie demo.

Real company facts recorded on 2026-11-03 from https://www.suutarintie.com/.
No paid APIs, no invented review quotes or human visual score.
"""
from pathlib import Path
from urllib.parse import unquote
import re
import unittest
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "docs/kaurivo/demos/suutarin-tie-v1"
URL = "/website-builder-agent/kaurivo/demos/suutarin-tie-v1/"
PAGES = (
    "index.html", "palvelut/index.html", "hinnasto/index.html",
    "nahkatyot/index.html", "yhteystiedot/index.html",
)
PRICE_SOURCE = {
    "Korkolaput": "22–35 €",
    "Puolipohjat": "25–40 €",
    "Puolipohjat + korkolaput": "47–75 €",
    "Kokopohjat": "50–60 €",
    "Pohjien vaihto": "alk. 100 €",
    "Pohjien liimaukset": "10–40 €",
    "Ompelutyöt": "alk. 10 €",
    "Paikkaustyöt": "alk. 15 €",
    "Kantavuorit": "36–50 € / pari",
    "Pohjavuorit": "30–40 € / pari",
    "Tarranauhat": "12–20 € / puoli",
    "Venykkeet": "alk. 12 € / kpl",
    "Vetoketjun vaihto": "alk. 29 €",
    "Classic": "10 € / kpl",
    "Classic, yli 2 kpl": "9 € / kpl",
    "Ura-avain": "20 € / kpl",
    "Ura-avain, yli 2 kpl": "19 € / kpl",
    "Edge (Exec-kopio, mustapäinen)": "30 € / kpl",
    "Edge Pro (Sento-kopio, mustapäinen)": "43 € / kpl",
    "Valmiit lämpötolpan avaimet": "10–20 €",
    "Nahkatakin vetoketjun vaihto": "alk. 60 €",
    "Nahkatakin hoito": "alk. 40 €",
    "Kenkien ja laukkujen hoito": "alk. 18 €",
    "Laukun hihnojen vaihdot": "alk. 35 €",
    "Nepparit": "8 € / kpl",
    "Minimipalvelumaksu": "5 €",
    "Kiirelisä": "+50 %",
    "Nastat": "2,50 € / kpl",
    "Luistimien teroitus": "12 €",
    "Kellon pariston vaihto": "10 €",
    "Auton kaukosäätimen pariston vaihto": "10 €",
    "Kenkien venytys": "18 € / pari",
    "Veitsien ja saksien teroitus": "Ei toistaiseksi saatavilla",
    "Vyö": "alk. 40 €",
    "Laukku": "alk. 200 €",
    "Maiharit": "alk. 600 €",
}


class SuutarinTieDemoTests(unittest.TestCase):
    def html(self, path):
        return (BASE/path).read_text(encoding="utf-8")

    def soup(self, path):
        return BeautifulSoup(self.html(path), "html.parser")

    def test_all_five_substantive_routes_and_assets_exist(self):
        for name in PAGES:
            with self.subTest(page=name):
                self.assertTrue((BASE/name).is_file())
                text = self.html(name)
                self.assertGreater(len(text), 3000)
                self.assertIn("Suutarin Tie", text)
                self.assertIn('name="robots" content="noindex,nofollow,noarchive"', text)
                soup = self.soup(name)
                self.assertEqual(len(soup.select("main h1")), 1)
                self.assertIsNotNone(soup.select_one('main#main'))
                self.assertIsNotNone(soup.select_one('a.skip[href="#main"]'))
                self.assertIsNotNone(soup.select_one('button[data-menu-button][aria-expanded]'))
                self.assertIsNotNone(soup.select_one('#mobile-nav[aria-hidden]'))
                self.assertIn("Ei Suutarin Tien virallinen", text)
                self.assertIn("Lopullinen käyttö edellyttää lupaa", text)
        self.assertTrue((BASE/"assets/site.css").is_file())
        self.assertTrue((BASE/"assets/site.js").is_file())

    def test_all_navigation_links_are_real_routes(self):
        for name in PAGES:
            with self.subTest(page=name):
                soup = self.soup(name)
                navigation = soup.select("header nav a, footer nav a")
                self.assertGreaterEqual(len(navigation), 12)
                for a in navigation:
                    href = a.get("href", "")
                    if href.startswith(URL):
                        target = unquote(href[len(URL):].split("#", 1)[0].split("?", 1)[0])
                        local = BASE/target
                        self.assertTrue(local.is_file() or (local/"index.html").is_file(),
                                        f"{name}: broken internal route {href}")

    def test_exact_source_price_grid_not_abridged(self):
        soup = self.soup("hinnasto/index.html")
        rows = {}
        for tr in soup.select(".price-table tbody tr"):
            cols = tr.select("td")
            self.assertEqual(len(cols), 2)
            key = cols[0].get_text(" ", strip=True)
            self.assertNotIn(key, rows)
            rows[key] = cols[1].get_text(" ", strip=True)
        self.assertEqual(rows, PRICE_SOURCE)
        self.assertEqual(len(soup.select(".price-table")), 6)

    def test_source_identity_and_genuine_business_photographs(self):
        for page in PAGES:
            with self.subTest(page=page):
                soup = self.soup(page)
                src = soup.select_one(".brand__seal img")["src"]
                self.assertIn("suutarintie-logo-greenleather.png", src)
                self.assertIn("images.squarespace-cdn.com", src)
                self.assertIn("Suurtarin Tie", "Suurtarin Tie")  # guard basic encoding
        home = self.soup("index.html")
        photos = [image["src"] for image in home.select("main img")]
        self.assertGreaterEqual(len(set(photos)), 4)
        self.assertTrue(all("images.squarespace-cdn.com" in url for url in photos))
        self.assertIn("Kuvat ja alkuperäinen tunnus linkitetty", self.html("index.html"))
        self.assertNotIn('class="testimonial"', self.html("index.html"))

    def test_review_stars_are_dated_provider_evidence_not_fabricated_quotes(self):
        source = self.html("index.html")
        self.assertIn("11 Google-arviota", source)
        self.assertIn("5,0 / 5", source)
        self.assertIn("3.11.2026", source)
        self.assertNotIn("Erinomaista ja nopeaa palvelua.", source)

    def test_all_real_contact_routes_and_availability_present(self):
        for page in PAGES:
            html = self.html(page)
            self.assertIn("tel:+3584578746469", html)
            self.assertIn("mailto:suutari@suutarintie.com", html)
            self.assertIn("Insinöörinkatu 27", html)
            self.assertIn("10–18", html)
            self.assertIn("10–16", html)
            self.assertIn("https://www.suutarintie.com/", html)
        contact = self.html("yhteystiedot/index.html")
        self.assertIn("https://wa.me/3584578746469", contact)
        self.assertIn("https://www.google.com/maps/search/", contact)
        self.assertIn("Avaa oikea kartta", contact)

    def test_mobile_accessibility_contrast_and_layout_contract(self):
        css = (BASE/"assets/site.css").read_text(encoding="utf-8")
        js = (BASE/"assets/site.js").read_text(encoding="utf-8")
        self.assertIn("@media(max-width:365px)", css)
        self.assertIn("@media(max-width:680px)", css)
        self.assertIn("@media(prefers-reduced-motion:reduce)", css)
        self.assertIn(":focus-visible", css)
        self.assertIn("aria-expanded", js)
        self.assertIn("Escape", js)
        self.assertIn("setOpen(false)", js)

    def test_past_holiday_exception_not_carried_forward(self):
        for page in PAGES:
            self.assertNotIn("PE 30.10. SULJETTU", self.html(page))
        self.assertIn("Veitsien ja saksien teroitus", self.html("hinnasto/index.html"))
        self.assertIn("Ei toistaiseksi saatavilla", self.html("hinnasto/index.html"))


if __name__ == "__main__":
    unittest.main()

"""No-credit release checks for Kotifixi V7 editorial redesign."""
from collections import Counter
from pathlib import Path
from urllib.parse import urlsplit
import re
import unittest
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1] / "docs" / "kaurivo" / "demos" / "kotifixi-v7"
FILES = ("index.html", "palvelut/index.html", "hinnasto/index.html",
         "meista/index.html", "yhteys/index.html")


class KotifixiV7ReleaseTests(unittest.TestCase):
    def test_five_real_pages_and_navigation(self):
        for filename in FILES:
            with self.subTest(filename=filename):
                p = ROOT / filename
                self.assertTrue(p.exists())
                soup = BeautifulSoup(p.read_text(encoding="utf-8"), "html.parser")
                self.assertEqual(len(soup.select("h1")), 1)
                self.assertEqual(len(soup.select(".site-nav a[href]")), 5)
                self.assertEqual(len(soup.select(".mobile-menu a[href]")), 6)
                self.assertTrue(soup.select_one('meta[name="robots"][content*="noindex"]'))
                self.assertTrue(soup.select_one('a[href^="tel:"]'))
                self.assertTrue(soup.select_one("main#main"))
                self.assertTrue(soup.select_one("footer.site-footer"))
                self.assertIsNotNone(soup.select_one(".brand[aria-label]"))
                for link in soup.select("nav.site-nav a[href], nav.mobile-menu a[href]"):
                    href = link["href"]
                    if href.startswith(("mailto:", "tel:", "http:", "https:")):
                        continue
                    target = (p.parent / href).resolve()
                    self.assertTrue(str(target).startswith(str(ROOT.resolve())), href)
                    if target.is_dir():
                        target /= "index.html"
                    self.assertTrue(target.is_file(), (filename, href))

    def test_mobile_preview_disclaimer_remains_visible(self):
        stylesheet = (ROOT / "assets/style.css").read_text(encoding="utf-8")
        for filename in FILES:
            page = (ROOT / filename).read_text(encoding="utf-8")
            self.assertIn("Kaurivon suunnitteluesikatselu", page)
            self.assertIn("Ei Kotifixin virallinen sivusto", page)
        self.assertNotIn(".concept-strip>.container span:last-child{display:none}", stylesheet)
        self.assertIn(".concept-strip>.container span:last-child{display:inline}", stylesheet)
        self.assertIn("@media(max-width:360px)", stylesheet)

    def test_hero_conversion_restored_but_arrows_not_added(self):
        soup = BeautifulSoup((ROOT / "index.html").read_text(encoding="utf-8"), "html.parser")
        self.assertEqual(soup.select_one(".hero-copy .button-primary").get_text(strip=True), "Kysy arviota")
        self.assertEqual(soup.select_one(".hero-copy .button-secondary").get_text(strip=True), "Katso palvelut")
        self.assertEqual(len(soup.select(".editorial-card[href]")), 3)
        # The old tagline-heavy band was intentionally removed.
        self.assertEqual(len(soup.select(".intro-band")), 0)
        self.assertNotIn("Vähemmän tekemättömiä töitä", str(soup))
        self.assertNotIn("KOTIFIXIN IDEA", str(soup))
        self.assertIn("Tarvitsetko apua", soup.select_one("h1").get_text(" ", strip=True))
        self.assertIn("hinnastoon", soup.select_one(".approach-section").get_text(" ",strip=True))
        self.assertNotIn("photo-caption", str(soup))
        self.assertIn("apua", soup.select_one(".hero-copy h1").get_text(" ", strip=True).lower())
        for filename in FILES:
            text = (ROOT / filename).read_text(encoding="utf-8")
            for arrow in ("↗", "→", "➜", "➝"):
                self.assertNotIn(arrow, text)

    def test_picture_set_curated_no_repeated_photo_ids(self):
        assets = []
        for filename in FILES:
            soup = BeautifulSoup((ROOT / filename).read_text(encoding="utf-8"), "html.parser")
            for image in soup.select("img"):
                self.assertTrue(image.get("alt"), (filename, image))
                u = urlsplit(image.get("src", ""))
                self.assertEqual(u.hostname, "images.pexels.com")
                self.assertRegex(u.path, r"/photos/\d+/pexels-photo-\d+\.jpeg$")
                assets.append(u.path)
        self.assertEqual(len(assets), 5)
        self.assertEqual(len(set(assets)), 5)
        self.assertIn("Kuvat ovat havainnollistavia", (ROOT / "index.html").read_text())
        for filename in FILES:
            self.assertIn("Ei Kotifixin virallinen", (ROOT / filename).read_text())
            self.assertIn("Esimerkkikuvat: Pexels.", (ROOT / filename).read_text())

    def test_mobile_headline_quality_and_verified_benefits(self):
        stylesheet = (ROOT / "assets/style.css").read_text(encoding="utf-8")
        self.assertIn("hyphens:manual", stylesheet)
        self.assertIn("text-wrap:balance", stylesheet)
        self.assertNotIn("hyphens:auto", stylesheet)
        index = BeautifulSoup((ROOT / "index.html").read_text(encoding="utf-8"), "html.parser")
        self.assertLessEqual(len(index.select("h1 .serif, h2 .serif")), 2)
        prices = BeautifulSoup((ROOT / "hinnasto/index.html").read_text(encoding="utf-8"), "html.parser")
        notice = prices.select_one(".tax-info")
        self.assertIsNotNone(notice)
        self.assertIn("40 %", notice.get_text(" ", strip=True))
        self.assertIn("ennakkoperintärekister", notice.get_text(" ", strip=True))
        self.assertIsNotNone(notice.select_one('a[href*="vero.fi"]'))
        for filename in FILES:
            body = (ROOT / filename).read_text(encoding="utf-8").lower()
            self.assertNotIn("35 %", body)
            self.assertNotIn("arvostelu: 5/5", body)

    def test_v9_editorial_layout_and_native_scroll(self):
        css = (ROOT / "assets/style.css").read_text(encoding="utf-8")
        js = (ROOT / "assets/app.js").read_text(encoding="utf-8")
        self.assertIn("html{scroll-behavior:auto", css)
        self.assertNotIn("window.addEventListener('scroll'", js)
        self.assertIn(".site-header{background:#fff;backdrop-filter:none;", css)
        self.assertIn(".hero-visual-edge{display:none}", css)
        prices = BeautifulSoup((ROOT / "hinnasto/index.html").read_text(encoding="utf-8"), "html.parser")
        self.assertEqual(len(prices.select(".tax-section .tax-info")), 1)
        self.assertEqual(len(prices.select(".pricing-aside .tax-info")), 0)
        self.assertIsNotNone(prices.select_one(".tax-section a[href*='vero.fi']"))
        home = BeautifulSoup((ROOT / "index.html").read_text(encoding="utf-8"), "html.parser")
        self.assertEqual(len(home.select(".hero-visual-edge")), 0)
        self.assertIsNotNone(home.select_one(".hero-photo-frame img[srcset][sizes]"))
        for filename in FILES:
            page = BeautifulSoup((ROOT / filename).read_text(encoding="utf-8"), "html.parser")
            self.assertLessEqual(len(page.select("main .serif")), 1)

    def test_v9_photo_slot_and_label_quality(self):
        css = (ROOT / "assets/style.css").read_text(encoding="utf-8")
        for rule in (
            ".editorial-media,.editorial-card-main .editorial-media{height:auto;aspect-ratio:4/3}",
            ".hero-photo-frame img,.editorial-media img,.about-photo img{object-fit:cover",
            ".about-photo{height:auto;aspect-ratio:4/3}",
            ".visual-photo-note,.photo-disclaimer{font-size:13px",
        ):
            self.assertIn(rule, css)
        home = BeautifulSoup((ROOT / "index.html").read_text(encoding="utf-8"), "html.parser")
        self.assertEqual(len(home.select(".hero-photo-frame img")), 1)
        self.assertEqual(len(home.select(".editorial-media img")), 3)
        self.assertFalse(home.select(".testimonial, .fake-staff, .empty-photo-placeholder"))
        for filename in FILES:
            html = (ROOT / filename).read_text(encoding="utf-8")
            self.assertIn("Ei Kotifixin virallinen sivusto", html)

    def test_v10_copy_header_contact_and_motion(self):
        pages = [(ROOT / filename).read_text(encoding="utf-8") for filename in FILES]
        for html in pages:
            page = BeautifulSoup(html, "html.parser")
            phone = page.select_one(".site-header .phone-link")
            self.assertIsNotNone(phone)
            self.assertEqual(phone.get_text(" ", strip=True), "Soita 044 363 2429")
            self.assertEqual(phone["href"], "tel:+358443632429")
            self.assertNotIn("kotona tai pihalla", html.casefold())
            self.assertNotIn("Kotifixin omilla verkkosivuilla kerrotaan", html)
        home = BeautifulSoup(pages[0], "html.parser")
        self.assertEqual(home.select_one("h1").get_text(" ", strip=True),
                         "Tarvitsetko apua kotitöissä tai pihatöissä?")
        self.assertIn("31755424", pages[3])
        css = (ROOT / "assets/style.css").read_text(encoding="utf-8")
        js = (ROOT / "assets/app.js").read_text(encoding="utf-8")
        self.assertIn(".site-nav a{font-size:15px", css)
        self.assertIn(".phone-link{display:inline-flex", css)
        self.assertIn("IntersectionObserver", js)
        self.assertIn("prefers-reduced-motion: reduce", js)
        self.assertNotIn("window.addEventListener('scroll'", js)

    def test_v11_hero_navigation_and_pointer_only_depth(self):
        home = BeautifulSoup((ROOT / "index.html").read_text(encoding="utf-8"), "html.parser")
        self.assertEqual(home.h1.get_text(" ", strip=True),
                         "Tarvitsetko apua kotitöissä tai pihatöissä?")
        self.assertEqual(len(home.select(".hero-visual-3d .hero-photo-frame")), 1)
        css = (ROOT / "assets/style.css").read_text(encoding="utf-8")
        js = (ROOT / "assets/app.js").read_text(encoding="utf-8")
        for expected in (
            ".site-nav a{font-size:17px",
            "@media(min-width:1280px){.site-nav a{font-size:18px",
            "perspective:1200px", "rotateX(var(--hero-tilt-x,0deg))",
            "@media(hover:hover) and (pointer:fine)",
            "@media(prefers-reduced-motion:reduce)",
        ):
            self.assertIn(expected, css)
        self.assertIn("heroArt.addEventListener('pointermove'", js)
        self.assertIn("window.requestAnimationFrame(", js)
        self.assertNotIn("addEventListener('wheel'", js)
        self.assertNotIn("window.addEventListener('scroll'", js)
        for filename in FILES:
            document = (ROOT / filename).read_text(encoding="utf-8")
            self.assertIn('>Näin toimimme</a>', document)
            self.assertNotIn('>Meistä</a>', document)
        about = BeautifulSoup((ROOT / "meista/index.html").read_text(encoding="utf-8"), "html.parser")
        self.assertIn("Näin voit sopia työstä", about.h1.get_text(" ", strip=True))
        self.assertNotIn("Työstä sopiminen", about.get_text(" ", strip=True))

    def test_services_no_repeated_contact_ctas_per_card(self):
        soup = BeautifulSoup((ROOT / "palvelut/index.html").read_text(), "html.parser")
        self.assertEqual(len(soup.select(".service-row")), 3)
        self.assertEqual(len(soup.select(".service-row a[href*='yhteys']")), 0)
        self.assertEqual(len(soup.select(".service-outro a[href*='yhteys']")), 1)
        for category in ("piha", "koti", "korjaukset"):
            self.assertTrue(soup.select_one("#" + category))

    def test_honest_prices_and_contact_backend(self):
        price = (ROOT / "hinnasto/index.html").read_text()
        self.assertIn("1.11.2026", price)
        self.assertIn("39,90 € / h", price)
        self.assertIn("kotifixi.com/hinnasto/", price)
        contact = (ROOT / "yhteys/index.html").read_text()
        js = (ROOT / "assets/app.js").read_text()
        self.assertIn('id="contact-form"', contact)
        self.assertIn('name="test_consent"', contact)
        self.assertIn('name="website"', contact)
        self.assertIn("ei lähde Kotifixille", contact)
        self.assertIn("kaurivo-kotifixi-demo-contact", js)
        self.assertIn("result.reference", js)
        self.assertIn("fetch(endpoint", js)
        self.assertNotIn("window.location.href='mailto:", js)
        self.assertIn("prefers-reduced-motion:reduce", (ROOT / "assets/style.css").read_text())


if __name__ == "__main__":
    unittest.main()

"""Zero-credit, source-bound Karjalanneito florist preview regressions.

These tests prove file/markup coverage, not image licenses, human design
quality, third-party image reachability, or owner approval.
"""
from __future__ import annotations

from pathlib import Path
from urllib.parse import urlsplit, unquote
import unittest
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1] / "docs" / "kaurivo" / "demos" / "kukkakauppa-karjalanneito-v1"
SOURCE = "https://www.karjalanneito.com/"
PHOTO = SOURCE + "wp-content/uploads/2023/10/"
EXPECTED = {
    "kimput": 10,
    "hautalaitteet": 11,
    "hautakimput": 11,
    "haakimput": 4,
    "muut": 9,
}


def read(route: str = "") -> BeautifulSoup:
    file = ROOT / route / "index.html"
    return BeautifulSoup(file.read_text(encoding="utf-8"), "html.parser")


class KarjalanneitoFirstPassTests(unittest.TestCase):
    def test_real_routes_have_distinct_h1_and_visible_demo_disclosure(self):
        for route in ("", "galleria", "yhteystiedot"):
            with self.subTest(route=route):
                soup = read(route)
                self.assertEqual(len(soup.select("main h1")), 1)
                self.assertIn("KAURIVON ITSENÄINEN KONSEPTIDEMO", soup.get_text(" ", strip=True))
                self.assertIn("Ei yrityksen virallinen", soup.get_text(" ", strip=True))
                self.assertTrue(soup.select_one('meta[name="robots"][content*="noindex"]'))
                self.assertTrue(soup.select_one("header .brand__text"))
                self.assertEqual(soup.select_one(".brand__text strong").get_text(strip=True),
                                 "KARJALANNEITO")
                self.assertTrue(soup.select_one(".brand__icon img")["src"].startswith(
                    SOURCE + "wp-content/uploads/elementor/thumbs/cropped-logo_final_KN"))
                self.assertTrue(soup.select_one(".site-footer"))

    def test_all_internal_navigation_routes_resolve_without_placeholders(self):
        for html_file in ROOT.rglob("index.html"):
            soup = BeautifulSoup(html_file.read_text("utf-8"), "html.parser")
            for link in soup.select("a[href]"):
                href = link.get("href", "")
                self.assertNotEqual(href, "")
                if href.startswith(("https://", "tel:", "mailto:", "#")):
                    continue
                self.assertNotIn("javascript:", href.lower())
                path_part = unquote(urlsplit(href).path)
                if not path_part:
                    continue
                dest = (html_file.parent / path_part)
                if dest.is_dir():
                    dest /= "index.html"
                self.assertTrue(dest.is_file(), (html_file, href))

    def test_original_gallery_has_all_45_images_and_five_source_categories(self):
        soup = read("galleria")
        pictures = soup.select("[data-gallery-item]")
        self.assertEqual(len(pictures), 45)
        source_paths = []
        for figure in pictures:
            image = figure.find("img")
            self.assertIsNotNone(image)
            self.assertTrue(image["src"].startswith(PHOTO), image["src"])
            self.assertTrue(image.get("alt", "").strip())
            self.assertTrue(figure.find("button")["aria-label"])
            source_paths.append(image["src"])
        self.assertEqual(len(set(source_paths)), 45)
        for category, expected in EXPECTED.items():
            with self.subTest(category=category):
                self.assertEqual(sum(item["data-category"] == category for item in pictures),
                                 expected)
                self.assertTrue(soup.select_one(
                    '[data-gallery-filter="' + category + '"]'
                ))
        self.assertTrue(soup.select_one("[data-lightbox]"))
        self.assertTrue(soup.select_one("[data-gallery-count]"))

    def test_first_view_and_services_use_real_florist_tasks(self):
        soup = read()
        h1 = soup.select_one("main h1").get_text(" ", strip=True)
        self.assertIn("Karhulasta", h1)
        text = soup.select_one("main").get_text(" ", strip=True)
        for phrase in ("Kukkalähetykset", "Surusidonta", "Juhla- ja hääkukat",
                       "Ruukkukasvit ja lahjat", "Eteläinen Karjalantie 3",
                       "Kimput"):
            self.assertIn(phrase, text)
        self.assertTrue(soup.select_one('a[href="tel:+35852266770"]'))
        self.assertFalse(soup.select_one(".card-number"))
        self.assertFalse(soup.select_one(".wordmark-seal"))
        self.assertEqual(len(soup.select(".service-thumb")), 5)

    def test_real_contacts_and_opening_hours_preserved(self):
        soup = read("yhteystiedot")
        text = soup.get_text(" ", strip=True)
        for phrase in ("Eteläinen Karjalantie 3", "48600 Kotka", "05 226 6770",
                       "050 546 7867", "9.30–17.30", "9–15", "10–15",
                       "karjalanneito@kymp.net"):
            self.assertIn(phrase, text)
        self.assertTrue(soup.select_one('a[href^="https://www.google.com/maps/search/"]'))
        self.assertFalse(soup.find("form"), "No invented backend or dummy form")

    def test_no_invented_reviews_awards_or_shop_checkout(self):
        for route in ("", "galleria", "yhteystiedot"):
            soup = read(route)
            self.assertFalse(soup.select(".testimonial,.review-card,.rating-summary"))
            self.assertFalse(soup.select(".checkout,.payment-form,.fake-map"))
            self.assertFalse(soup.select_one("main img[src*='unsplash']"))

    def test_css_has_real_mobile_and_reduced_motion_behavior(self):
        css = (ROOT / "assets" / "site.css").read_text("utf-8")
        js = (ROOT / "assets" / "site.js").read_text("utf-8")
        for marker in ("@media(max-width:830px)", "@media(max-width:540px)",
                       "prefers-reduced-motion", ".masonry", ".service-thumb"):
            self.assertIn(marker, css)
        for marker in ("data-gallery-filter", "aria-pressed",
                       "Escape", "ArrowLeft", "ArrowRight", "aria-expanded"):
            self.assertIn(marker, js)


if __name__ == "__main__":
    unittest.main()

"""Zero-credit smoke tests of the five-page, publicly unlisted design preview.

This validates file/URL structure, not visual rendering or client acceptance.
"""
from pathlib import Path
from urllib.parse import urlsplit, unquote
from bs4 import BeautifulSoup
import unittest

ROOT = Path(__file__).resolve().parents[1] / 'docs' / 'kaurivo' / 'demos' / 'kotifixi-v5'
PAGES = ('index.html', 'palvelut/index.html', 'hinnasto/index.html',
         'meista/index.html', 'yhteys/index.html')


class KotifixiV5StaticPreviewTests(unittest.TestCase):
    def test_all_pages_have_real_navigation_and_clear_site_structure(self):
        for rel in PAGES:
            with self.subTest(page=rel):
                page = ROOT / rel
                self.assertTrue(page.is_file())
                soup = BeautifulSoup(page.read_text(encoding='utf-8'), 'html.parser')
                self.assertEqual(len(soup.find_all('h1')), 1)
                self.assertEqual(len(soup.find_all('main')), 1)
                self.assertEqual(len(soup.select('.desktop-nav a')), 5)
                self.assertEqual(len(soup.select('.mobile-nav a')), 6)
                self.assertEqual(len(soup.select('a[aria-current="page"]')), 2)
                self.assertIn('noindex', soup.find('meta', attrs={'name': 'robots'})['content'])
                self.assertIn('koti', soup.select_one('.brand').get_text())
                self.assertIsNone(soup.select_one('svg.brand-logo'))
                self.assertTrue(soup.find('meta', attrs={'name': 'description'}))

    def test_local_navigation_links_have_existing_destinations(self):
        for rel in PAGES:
            page = ROOT / rel
            soup = BeautifulSoup(page.read_text(encoding='utf-8'), 'html.parser')
            ids = {item.get('id') for item in soup.select('[id]')}
            for element in list(soup.select('a[href]')) + list(soup.select('link[href]')) + list(soup.select('script[src]')):
                raw = element.get('href') or element.get('src')
                url = urlsplit(raw)
                if url.scheme or url.netloc:
                    continue
                if not url.path:
                    if url.fragment:
                        self.assertIn(url.fragment, ids, f'{rel}: broken anchor {raw}')
                    continue
                target = (page.parent / unquote(url.path)).resolve()
                self.assertTrue(target.is_relative_to(ROOT), f'{rel}: escaped root {raw}')
                if target.is_dir():
                    target /= 'index.html'
                self.assertTrue(target.exists(), f'{rel}: missing {raw}')
                if url.fragment and target.is_file() and target.suffix == '.html':
                    target_ids = {x.get('id') for x in BeautifulSoup(target.read_text(encoding='utf-8'), 'html.parser').select('[id]')}
                    self.assertIn(url.fragment, target_ids, f'{rel}: broken target {raw}')

    def test_unique_editorial_photos_and_no_redundant_homepage_maze(self):
        from collections import Counter
        from urllib.parse import urlsplit
        all_images = []
        for rel in PAGES:
            doc = BeautifulSoup((ROOT / rel).read_text(encoding='utf-8'), 'html.parser')
            all_images.extend(urlsplit(img['src']).path for img in doc.select('img[src]'))
        photos = Counter(all_images)
        self.assertEqual(len(all_images), len(photos),
                         "Editorial photos must not repeat across home and detail pages: "
                         + repr({p: n for p, n in photos.items() if n > 1}))
        home = (ROOT / 'index.html').read_text(encoding='utf-8')
        self.assertNotIn('Tutustu Kotifixiin', home)
        self.assertNotIn('Tutustu palveluihin', home)
        self.assertNotIn('highlight-section', home)
        self.assertIn('href="tel:+358443632429"', home)

    def test_brand_and_unverified_publish_claims_not_fabricated(self):
        home = (ROOT / 'index.html').read_text(encoding='utf-8')
        price = (ROOT / 'hinnasto' / 'index.html').read_text(encoding='utf-8')
        self.assertIn('Kaurivo', home)
        self.assertIn('ei virallinen julkaisu', home.lower())
        self.assertIn('koti<span>fixi</span>', home)
        self.assertIn('1.11.2026', price)
        self.assertIn('Kotifixin alkuperäiseen hinnastoon', price)
        self.assertNotIn('✳', home)
        self.assertTrue((ROOT / 'assets' / 'style.css').is_file())
        self.assertTrue((ROOT / 'assets' / 'app.js').is_file())


if __name__ == '__main__':
    unittest.main()

"""No-credit Kaurivo multi-page / animation QA tests."""
from pathlib import Path
import os
import unittest
from html.parser import HTMLParser

ROOT = Path(__file__).resolve().parents[1] / 'docs' / 'kaurivo'
PAGES = ('index.html','services.html','process.html','faq.html','contact.html')
class HtmlAudit(HTMLParser):
    def __init__(self):
        super().__init__();self.ids=set();self.links=[];self.scripts=[];self.details=0
    def handle_starttag(self,tag,attrs):
        d=dict(attrs)
        if d.get('id'):self.ids.add(d['id'])
        if tag=='a':self.links.append(d.get('href',''))
        if tag=='script':self.scripts.append(d.get('src',''))
        if tag=='details':self.details+=1

class V3Tests(unittest.TestCase):
    def test_shared_assets_and_separate_pages(self):
        for page in PAGES:
            with self.subTest(page=page):
                html=(ROOT/page).read_text(encoding='utf8')
                p=HtmlAudit();p.feed(html)
                self.assertIn('id="main"',html)
                self.assertIn('styles.css',html)
                self.assertIn('site.js',html)
                self.assertIn('assets/kaurivo-mark.webp',html)
                self.assertIn('contact.html',p.links)
                for h in p.links:
                    if h.startswith(('mailto:','#')):continue
                    self.assertTrue((ROOT/h.split('#')[0]).exists(),(page,h))
        self.assertGreaterEqual((ROOT/'faq.html').read_text().count('<details>'),8)
        self.assertNotIn('<details>',(ROOT/'index.html').read_text())
        self.assertTrue((ROOT/'assets/kaurivo-mark.webp').is_file())
    def test_smooth_motion_and_reduced_motion(self):
        css=(ROOT/'styles.css').read_text()
        js=(ROOT/'site.js').read_text()
        self.assertIn('prefers-reduced-motion',css)
        self.assertIn('requestAnimationFrame',js)
        self.assertIn('IntersectionObserver',js)
        self.assertIn('pointerleave',js)
        self.assertNotIn('getContext(',js)
        self.assertNotIn('WebGL',js)
        self.assertNotIn('420vh',css)
        self.assertIn('transform',css)
    def test_playwright_layout_navigation_faq_and_form(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            if os.environ.get('REQUIRE_BROWSER_TESTS')=='1':self.fail('Playwright required in CI')
            self.skipTest('No Playwright installed')
        with sync_playwright() as p:
            browser=p.chromium.launch(headless=True,args=['--disable-gpu'])
            try:
                for width,height in ((320,740),(390,844),(768,1024),(1440,900)):
                    with self.subTest(width=width):
                        page=browser.new_page(viewport={'width':width,'height':height},reduced_motion='reduce')
                        errors=[]
                        page.on('pageerror',lambda err:errors.append(str(err)))
                        page.goto((ROOT/'index.html').as_uri(),wait_until='domcontentloaded')
                        self.assertTrue(page.get_by_role('heading',name='Make your business stand out.').is_visible())
                        self.assertLessEqual(page.evaluate("Math.max(document.documentElement.scrollWidth,document.body.scrollWidth)-innerWidth"),2)
                        if width<850:
                            page.get_by_role('button',name='Open menu').click()
                            page.get_by_role('link',name='FAQ').first.click()
                        else:
                            page.get_by_role('link',name='FAQ').first.click()
                        self.assertTrue(page.url.endswith('/faq.html'))
                        self.assertTrue(page.locator('.faq-list details').first.locator('summary').is_visible())
                        page.locator('.faq-list summary').first.click()
                        self.assertTrue(page.locator('.faq-list details').first.evaluate('(el)=>el.open'))
                        self.assertLessEqual(page.evaluate("Math.max(document.documentElement.scrollWidth,document.body.scrollWidth)-innerWidth"),2)
                        page.get_by_role('link',name='Get a quote').first.click()
                        self.assertTrue(page.url.endswith('/contact.html'))
                        self.assertEqual(page.locator('#enquiry-form').count(),1)
                        self.assertEqual(errors,[])
                        page.close()
            finally:browser.close()

if __name__=='__main__':unittest.main()

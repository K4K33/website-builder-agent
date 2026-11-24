"""Page-wide motion system: every section moves with the scroll, nothing stays hidden (offline)."""
from pathlib import Path
import unittest

from utils.motion_system import MOTION_SYSTEM_BRIEF, annotate, enhance_motion_system
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
PAGE = """<html><head></head><body><header><nav><h2>nav</h2></nav></header><main>
<section class="hero"><h2>hero stays</h2><img src="a.jpg" width="1200"></section>
<section><h2>Palvelut</h2><div class="cards">
<a class="card" href="#"><img src="1.jpg" width="600"><span>Yksi</span></a>
<a class="card" href="#"><img src="2.jpg" width="600"><span>Kaksi</span></a>
<a class="card" href="#"><img src="3.jpg" width="600"><span>Kolme</span></a></div></section>
<section><figure><img src="big.jpg" width="1600"></figure><img src="icon.png" width="40"></section>
</main><footer><h2>footer</h2></footer></body></html>"""


class MotionSystemTests(unittest.TestCase):
    def test_annotates_sections_below_the_hero_only(self):
        soup = BeautifulSoup(PAGE, "html.parser")
        annotate(soup)
        self.assertEqual([h.get("data-reveal") for h in soup.find_all("h2")], [None, None, "rise", None])
        cards = soup.select_one(".cards")
        self.assertEqual(cards["data-reveal"], "stagger")
        self.assertEqual([a["style"] for a in cards.select("a")], ["--i:0", "--i:1", "--i:2"])
        self.assertTrue(all("mo-card" in a["class"] for a in cards.select("a")))
        self.assertEqual(soup.find("figure")["data-reveal"], "media")
        self.assertIsNone(soup.find("img", src="icon.png").get("data-reveal"))  # small images stay still

    def test_runtime_is_added_once(self):
        once = enhance_motion_system(PAGE)
        twice = enhance_motion_system(once)
        self.assertEqual(twice.count("data-kaurivo-motion"), 2)
        self.assertEqual(twice.count('--i:0'), 1)
        self.assertIn("prefers-reduced-motion", twice)

    def test_builder_and_pipelines_use_it(self):
        self.assertIn("MOTION_SYSTEM_BRIEF", (ROOT / "agents/builder.py").read_text(encoding="utf-8"))
        for path in ("utils/site_build_pipeline.py", "utils/sales_demo.py"):
            self.assertIn("enhance_motion_system", (ROOT / path).read_text(encoding="utf-8"))
        for rule in ("ONE scroll-linked motion idea", "data-depth-wall", "data-tone", "never a timed fade-up"):
            self.assertIn(rule, MOTION_SYSTEM_BRIEF)

    def test_kaurivo_pages_load_the_auto_runtime(self):
        for page in ("index.html", "services/index.html", "hinnat/index.html"):
            html = (ROOT / "docs/kaurivo" / page).read_text(encoding="utf-8")
            self.assertIn("assets/motion.js?v=1\" data-auto", html)

    def test_browser_reveals_everything_and_respects_reduced_motion(self):
        try:
            from playwright.sync_api import sync_playwright
        except ImportError:
            self.skipTest("Playwright unavailable locally")
        home = (ROOT / "docs/kaurivo/index.html").as_uri()
        with sync_playwright() as p:
            browser = p.chromium.launch()
            try:
                page = browser.new_page(viewport={"width": 1440, "height": 900})
                page.goto(home)
                page.wait_for_timeout(300)
                self.assertGreaterEqual(page.locator("[data-reveal]").count(), 5)
                height = page.evaluate("document.documentElement.scrollHeight")
                for y in range(0, height, 500):
                    page.mouse.wheel(0, 500)
                    page.wait_for_timeout(60)
                page.evaluate("scrollTo(0, document.documentElement.scrollHeight)")
                page.wait_for_timeout(1200)
                # everything above the fold at the bottom has fully arrived
                hidden = page.evaluate("""[...document.querySelectorAll('[data-reveal]')]
                    .filter(el => el.getBoundingClientRect().top < innerHeight * .4)
                    .filter(el => parseFloat(getComputedStyle(el).getPropertyValue('--v')) < .97).length""")
                self.assertEqual(hidden, 0)
                calm = browser.new_page(viewport={"width": 390, "height": 844}, reduced_motion="reduce")
                calm.goto(home)
                calm.wait_for_timeout(300)
                self.assertFalse(calm.evaluate("document.documentElement.classList.contains('mo-js')"))
            finally:
                browser.close()


if __name__ == "__main__":
    unittest.main()

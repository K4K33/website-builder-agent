"""V7 references must show a real full scroll, not just a saved hero image.

These tests use local Playwright HTML. No reference websites, credits, or
paid APIs are accessed.
"""
from __future__ import annotations

from pathlib import Path
from tempfile import TemporaryDirectory
import unittest

from utils.reference_scroll_experience import (
    PROTOCOL, record_scroll_experience, complete_scroll_evidence,
    compact_scroll_observations,
)
from utils.design_benchmark import reference_image_inputs


PAGE = """<!doctype html><html lang="en"><head><style>
html{scroll-behavior:auto}body{margin:0;font:18px Arial}
header{position:sticky;top:0;background:white;padding:20px;z-index:4}
header a:hover{background:yellow} main section{min-height:830px;padding:24px}
section:nth-child(odd){background:#eee}section:nth-child(even){background:#ddd}
</style></head><body><header><nav><a href="#final">Jump</a></nav></header>
<main><section><h1>Authentic first section</h1></section>
<section><h2>Real mid page</h2></section>
<section><h2>Another meaningful stage</h2></section>
<section><h2>Work and services</h2></section>
<section id="final"><h2>Contact</h2></section></main></body></html>"""


class ScrollReferenceTests(unittest.TestCase):
    def test_website_is_scrolled_in_both_viewports_with_real_progressive_images(self):
        from playwright.sync_api import sync_playwright
        with TemporaryDirectory() as d, sync_playwright() as p:
            browser=p.chromium.launch(headless=True)
            shots={"scroll_experience":{}}
            try:
                for view,width,height in (("desktop",1440,900),("mobile",390,844)):
                    context=browser.new_context(viewport={"width":width,"height":height})
                    page=context.new_page()
                    page.set_content(PAGE,wait_until="domcontentloaded")
                    evidence=record_scroll_experience(page,
                        output_prefix=Path(d)/(view+"-reference"))
                    self.assertEqual(evidence["status"],"observed",evidence)
                    self.assertEqual(evidence["protocol"],PROTOCOL)
                    self.assertEqual(len(evidence["frames"]),5)
                    self.assertGreaterEqual(
                        len({f["y"] for f in evidence["frames"]}),3)
                    self.assertTrue(Path(evidence["scroll_sequence_image"]).is_file())
                    self.assertTrue(any(f["headings"] for f in evidence["frames"]))
                    self.assertTrue(evidence["quality_review_required"])
                    shots["scroll_experience"][view]=evidence
                    shots[view]=str(Path(d)/(view+"-first.png"))
                    page.screenshot(path=shots[view])
                    context.close()
                self.assertTrue(complete_scroll_evidence(shots))
                report=compact_scroll_observations(shots)
                self.assertTrue(report["verified"])
                self.assertEqual(len(report["views"]["mobile"]["scroll_story"]),5)
                inputs, labels=reference_image_inputs([{"url":"https://example.com",
                                                         "screenshots":shots}])
                self.assertEqual(len(inputs),4)
                self.assertEqual(sum(l.get("kind")=="five_step_live_scroll_sequence"
                                     for l in labels),2)
            finally:
                browser.close()

    def test_single_screenshot_is_never_scroll_quality_evidence(self):
        self.assertFalse(complete_scroll_evidence({"desktop":"example.png",
                                                   "mobile":"example.png"}))
        self.assertFalse(compact_scroll_observations({})["verified"])

    def test_real_wheel_driven_canvas_style_journey_without_native_scroll(self):
        # Some awarded experiences deliberately keep scrollY at zero while
        # advancing the visual scene on actual wheel events. They must not
        # be mistaken for an unscrollable static site.
        from playwright.sync_api import sync_playwright
        markup = """<!doctype html><html><head><style>
            html,body{height:100%;overflow:hidden;margin:0}
            #scene{height:100vh;display:grid;place-items:center;
                   font:56px Arial;background:rgb(20,20,20);color:white}
        </style></head><body><main id="scene">Scene zero</main>
        <script>
          let scene=0;
          window.addEventListener("wheel", event=>{
            scene+=1;
            document.querySelector("#scene").textContent="Scene "+scene;
            document.querySelector("#scene").style.backgroundColor=
                "rgb("+((20+scene*23)%220)+",30,60)";
            event.preventDefault();
          },{passive:false});
        </script></body></html>"""
        with TemporaryDirectory() as d, sync_playwright() as p:
            browser=p.chromium.launch(headless=True)
            try:
                page=browser.new_page(viewport={"width":1200,"height":800})
                page.set_content(markup)
                result=record_scroll_experience(
                    page,output_prefix=Path(d)/"canvas-journey")
                self.assertEqual(result["status"],"observed",result)
                self.assertEqual(result["scroll_mechanism"],
                                 "visual_without_native_scroll")
                self.assertEqual(len({frame["y"] for frame in
                                      result["frames"]}),1)
                self.assertGreaterEqual(len({frame["sha256"] for frame in
                                             result["frames"]}),3)
            finally:
                browser.close()

    def test_empty_page_is_not_a_qualified_scroll_benchmark(self):
        from playwright.sync_api import sync_playwright
        with TemporaryDirectory() as d, sync_playwright() as p:
            browser=p.chromium.launch(headless=True)
            page=browser.new_page(viewport={"width":1440,"height":900})
            page.set_content("<main><h1>Short site</h1></main>")
            result=record_scroll_experience(page,output_prefix=Path(d)/"short")
            self.assertEqual(result["status"],"not_scrollable")
            browser.close()


if __name__=="__main__":
    unittest.main()

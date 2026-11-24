import pytest

from utils.brand_consistency import OVERLAP_SCRIPT, overlap_issues

playwright = pytest.importorskip("playwright.sync_api")

HTML = """<div style="position:relative;height:120px">
<span style="position:absolute;top:10px;left:10px">Navigaatio: menu ja pöytävaraus</span>
<span style="position:absolute;top:14px;left:60px">Pöytävaraus Yksityistilat</span></div>"""
CLEAN = """<h1 style="line-height:.8">Kaksi riviä joka on pitkä<br>toinen rivi</h1>
<div style="position:relative"><p>Piilossa</p><div style="position:absolute;inset:0;background:#000;color:#fff">Peitto</div></div>
<p aria-hidden="true" style="position:absolute;top:0;margin:0">Koriste</p>"""


def _hits(html):
    with playwright.sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            page = browser.new_page()
            page.set_content(html)
            return page.evaluate(OVERLAP_SCRIPT)
        finally:
            browser.close()


def test_label_on_label_is_flagged():
    problems = overlap_issues(_hits(HTML))
    assert problems and "Navigaatio" in problems[0]


def test_tight_lines_covered_text_and_decoration_pass():
    assert overlap_issues(_hits(CLEAN)) == []

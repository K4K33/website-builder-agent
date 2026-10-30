"""Offline browser smoke tests: no AI credits and no external requests."""
from pathlib import Path
from base64 import b64encode
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).parent
html = (ROOT / 'index.html').read_text()
# Offline browser QA works without Google Fonts, but production CSS uses fonts with robust fallbacks.
html = '\n'.join(line for line in html.splitlines() if '@import url' not in line)
# Headless CI SwiftShader can hang on WebGL shader compilation; motion/story JS still runs.
html = html.replace("const canvas=document.getElementById('webgl');", "return;const canvas=document.getElementById('webgl');")
for asset in (ROOT / 'assets').glob('*.webp'):
    html = html.replace(f'assets/{asset.name}', f'data:image/webp;base64,{b64encode(asset.read_bytes()).decode()}')

with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/usr/bin/chromium', headless=True, args=['--no-sandbox', '--disable-gpu'])
    for width, height in ((1440, 900), (768, 1024), (390, 844), (320, 740)):
        page = browser.new_page(viewport={'width': width, 'height': height})
        errors = []
        page.on('pageerror', lambda e: errors.append(str(e)))
        page.set_content(html, wait_until='load')
        page.wait_for_timeout(1800)
        page.evaluate("document.documentElement.style.scrollBehavior='auto'")
        assert page.title().startswith('Kaurivo')
        assert page.locator('h1').count() == 1
        assert page.locator('a[href="mailto:hello.kaurivo@gmail.com?subject=Website%20project%20enquiry"]').count() == 1
        assert page.locator('header .brand-icon').evaluate('(img)=>img.complete && img.naturalWidth > 0')
        assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), f'Horizontal overflow at {width}'
        for percent, expected in ((.02,'01 / THE STRUCTURE'), (.31,'02 / THE DESIGN'), (.56,'03 / THE DEVELOPMENT'), (.84,'04 / THE RESULT')):
            page.evaluate('p=>{const r=document.querySelector(".assembly");scrollTo({top:r.offsetTop+p*(r.offsetHeight-innerHeight),behavior:"instant"})}',percent)
            page.wait_for_timeout(120)
            actual=page.locator('#stage-num').inner_text()
            assert expected == actual, (percent,actual,expected)
        assert not errors, f'JS errors at {width}: {errors}'
        if width in (1440,390):
            page.evaluate('window.scrollTo({top:0,behavior:"instant"})')
            page.wait_for_timeout(250)
            page.screenshot(path=str(ROOT / f'preview_{width}.png'))
            for percent, name in ((.02,'idea'),(.32,'design'),(.56,'develop'),(.84,'launch')):
                page.evaluate('p=>{const r=document.querySelector(".assembly");scrollTo({top:r.offsetTop+p*(r.offsetHeight-innerHeight),behavior:"instant"})}', percent)
                page.wait_for_timeout(140)
                page.screenshot(path=str(ROOT / f'preview_{width}_{name}.png'))
        page.close()
        print(f'PASS {width}x{height}: semantic/content, logo, contact, four scroll phases, JS, no overflow')
    reduced=browser.new_page(viewport={'width':390,'height':844},reduced_motion='reduce')
    reduced.set_content(html,wait_until='load')
    assert reduced.locator('h1').is_visible()
    assert reduced.evaluate('getComputedStyle(document.querySelector(".reveal")).opacity') == '1'
    print('PASS reduced motion')
    browser.close()
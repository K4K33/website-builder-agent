from playwright.sync_api import sync_playwright
from pathlib import Path
import json,hashlib
pages=["","verhoilupalvelut/","verhoilijat-silvana-ja-sini/","ota-yhteytta/"]
root="https://verhoomo3assaa.com/"
out=Path("output/verhoomo3-source")
out.mkdir(parents=True,exist_ok=True)
with sync_playwright() as p:
 browser=p.chromium.launch(headless=True)
 for size in [390,1440]:
  context=browser.new_context(viewport={"width":size,"height":900},device_scale_factor=1)
  page=context.new_page()
  for i,path in enumerate(pages):
   res=page.goto(root+path,wait_until="domcontentloaded",timeout=45000)
   page.wait_for_timeout(550)
   sfile=out/f"source-{i}-{size}.png"
   page.screenshot(path=str(sfile),full_page=True,timeout=30000)
   info=page.evaluate("""()=>({
    title:document.title,
    text:document.body.innerText.slice(0,9000),
    imgs:[...document.querySelectorAll("img")].map(i=>({src:i.currentSrc||i.src,alt:i.alt,w:i.naturalWidth,h:i.naturalHeight,rect:Math.round(i.getBoundingClientRect().width)})).slice(0,65),
    logos:[...document.querySelectorAll("header img,.site-branding img,[class*=logo] img")].map(i=>({src:i.currentSrc||i.src,alt:i.alt})),
    anchors:[...document.querySelectorAll("a[href]")].filter(a=>/whats|instagram|facebook|tel:|mailto:/.test(a.href)).map(a=>({url:a.href,text:(a.innerText||a.getAttribute("aria-label")||"").slice(0,80)})).slice(0,30),
    styles:{bg:getComputedStyle(document.body).backgroundColor,font:getComputedStyle(document.body).fontFamily,header:getComputedStyle(document.querySelector("header")||document.body).backgroundColor}
   })""")
   record={"page":path,"size":size,"status":res.status if res else None,"screenshot_sha256":hashlib.sha256(sfile.read_bytes()).hexdigest(),"info":info}
   (out/f"data-{i}-{size}.json").write_text(json.dumps(record,ensure_ascii=False,indent=2),encoding="utf-8")
   print("SOURCE_JSON",json.dumps({k:v for k,v in record.items() if k!="info"}|{"imgs":info["imgs"],"logos":info["logos"],"anchors":info["anchors"],"styles":info["styles"]},ensure_ascii=False))
  context.close()
 browser.close()

# Source inspection is research evidence, not permission to republish images.

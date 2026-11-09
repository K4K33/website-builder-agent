#!/usr/bin/env python3
"""Offline source-grounded structural checks for the Lyijylasi & Tiffany concept.
A passing result is NOT real browser, image, CMS or independent aesthetic approval.
"""
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote
import json
import re
import sys
ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "docs/kaurivo/demos/lyijylasi-tiffany-v1"
SOURCE = json.loads((ROOT / "data/demo_provenance/lyijylasi-tiffany-v1.json").read_text(encoding="utf-8"))
ROUTES = ["index.html", "palvelut/index.html", "tyot/index.html", "tilaaminen/index.html", "yhteystiedot/index.html"]
class Parse(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags=[];self.h1=0;self.links=[];self.images=[];self.filters=[];self.categories=[]
    def handle_starttag(self, tag, attrs):
        a=dict(attrs)
        self.tags.append(tag)
        if tag=="h1":self.h1+=1
        if tag=="a":self.links.append(a.get("href",""))
        if tag=="img":self.images.append(a.get("src",""))
        if "data-filter" in a:self.filters.append(a["data-filter"])
        if "data-category" in a:self.categories.append(a["data-category"])
def audit():
    problems=[]
    titles=set()
    for route in ROUTES:
        f=SITE/route
        if not f.is_file():
            problems.append(f"missing page {route}");continue
        html=f.read_text(encoding="utf-8")
        p=Parse();p.feed(html)
        if p.h1!=1:problems.append(f"{route}: expected exactly one h1, got {p.h1}")
        if 'noindex,nofollow' not in html:problems.append(f"{route}: missing demo noindex")
        if 'Kaurivon riippumaton suunnittelukonsepti' not in html:problems.append(f"{route}: missing demo identification")
        if 'Lyijylasi &amp; Tiffany' not in html:problems.append(f"{route}: brand missing")
        if SOURCE["email"] not in html or SOURCE["business_id"] not in html:problems.append(f"{route}: original business facts missing")
        if html.count('aria-current="page"')!=1:problems.append(f"{route}: one active navigation link required")
        h1=re.search(r"<h1[^>]*>(.*?)</h1>",html,re.S)
        if h1:
            title=re.sub(r"<[^>]+>","",h1.group(1))
            if title in titles:problems.append(f"{route}: cloned heading")
            titles.add(title)
        for link in p.links:
            if not link or link.startswith(("http://","https://","tel:","mailto:","#")):continue
            path=unquote(link.split("#")[0].split("?")[0])
            if not path:continue
            target=(f.parent/path).resolve()
            if target.is_dir():target/= "index.html"
            if not target.is_file():problems.append(f"{route}: dead navigation {link}")
        for image in p.images:
            if image and not image.startswith("https://static.wixstatic.com/media/"):
                problems.append(f"{route}: unsupported image origin {image}")
        if route=="tyot/index.html":
            for group,expected in (("ovet",7),("ikkunat",10),("lasimaalaukset",6)):
                n=p.categories.count(group)
                if n!=expected:problems.append(f"gallery {group} has {n}, expected {expected}")
            if set(p.filters)!={"all","ovet","ikkunat","lasimaalaukset"}:
                problems.append("gallery filters incomplete")
            valid_ids={s for values in SOURCE["gallery_source_ids"].values() for s in values}
            # Only the 23 labelled gallery cards count as portfolio entries.
            # The separate editorial hero may legitimately repeat a source image.
            card_urls=re.findall(
                r'<button[^>]*\\bdata-enlarge\\b[^>]*>\\s*<img\\b[^>]*\\bsrc="([^"]+)"',
                html, flags=re.I|re.S)
            photo_ids=[]
            for u in card_urls:
                m=re.search(r"7e296a_([a-z0-9]{32})~mv2[.]jpg",u)
                if not m:problems.append(f"gallery card uses non-original media: {u}");continue
                photo_ids.append(m.group(1))
            if len(photo_ids)!=23 or set(photo_ids)!=valid_ids or len(set(photo_ids))!=23:
                problems.append("not all exact 23 original gallery images retained in gallery cards")
    service=(SITE/ROUTES[1]).read_text(encoding="utf-8")
    for s in ('id="lyijylasi"','id="tiffany"','id="entisointi"','id="lasimaalaukset"'):
        if s not in service:problems.append("missing service route "+s)
    order=(SITE/ROUTES[3]).read_text(encoding="utf-8")
    if order.count('class="process-item"')!=5 or '2–8 viikkoa' not in order:
        problems.append("source ordering steps/timing lost")
    contact=(SITE/ROUTES[4]).read_text(encoding="utf-8")
    if 'avaa sähköpostiohjelmassasi' not in contact or 'virallinen yhteydenottolomake' not in contact:
        problems.append("demo contact limitations not disclosed")
    css=(SITE/"assets/site.css").read_text(encoding="utf-8")
    js=(SITE/"assets/site.js").read_text(encoding="utf-8")
    if "prefers-reduced-motion" not in css or "aria-expanded" not in js or "mailto:" not in js:
        problems.append("core accessibility or mailto draft missing")
    if "Tiffany-losityöt" in "\n".join((SITE/r).read_text(encoding="utf-8") for r in ROUTES):
        problems.append("known typographic error")
    print("DEMO STATIC AUDIT:",len(ROUTES),"routes,",len(problems),"errors")
    for problem in problems:print("FAIL",problem)
    print("CAVEAT: No image decode, browser screenshots, paid checkout, reviewer score or CMS edit proof.")
    return 1 if problems else 0
if __name__=="__main__":sys.exit(audit())

#!/usr/bin/env python3
"""Install an exact, unapproved 3-site owner review batch; never mark customer-ready.

All approved/client-facing demos must instead pass the full Kaurivo universal
source/concept/independent-visual/release gates. This staging entrypoint cannot
set those flags, create CRM demo successes, or provide outreach URLs.
"""
from __future__ import annotations
import argparse, base64, hashlib, io, json, lzma, re, tarfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, unquote

SITES = {
    "ostroferia-kurkela": {"index.html","menu/index.html","tilaisuudet/index.html","yhteys/index.html"},
    "settimedia": {"index.html","palvelut/index.html","tiimi/index.html","yhteys/index.html"},
    "talousfocus": {"index.html","palvelut/index.html","toimialat/index.html","yhteys/index.html"},
}
STATUS = "TECHNICAL_PREVIEW_ONLY / QUALITY_PENDING / HOLD"
MAX_ARCHIVE = 250_000
MAX_FILES = 45
class HTMLAudit(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links=[];self.images=[];self.robots="";self.quality="";self.script=[];self.forms=0
    def handle_starttag(self, tag, attributes):
        a=dict(attributes)
        if tag=="meta" and a.get("name")=="robots":self.robots=a.get("content","")
        if tag=="meta" and a.get("name")=="kaurivo-review-status":self.quality=a.get("content","")
        if tag=="a" and a.get("href"):self.links.append(a["href"])
        if tag=="img":self.images.append((a.get("src",""),a.get("alt","")))
        if tag=="script" and a.get("src"):self.script.append(a["src"])
        if tag=="form":self.forms+=1

def validate_and_install(archive:Path,dest:Path)->dict:
    encoded=archive.read_text(encoding="ascii").strip()
    if len(encoded)>100_000 or not re.fullmatch(r"[A-Za-z0-9+/=]+",encoded):
        raise ValueError("Review archive invalid or oversized")
    raw=lzma.decompress(base64.b64decode(encoded,validate=True),memlimit=32*1024*1024)
    if len(raw)>MAX_ARCHIVE:raise ValueError("Review archive too large after unpack")
    payload={}
    with tarfile.open(fileobj=io.BytesIO(raw),mode="r:") as tar:
        members=tar.getmembers()
        if len(members)>MAX_FILES:raise ValueError("Too many preview files")
        for m in members:
            if not m.isfile() or m.issym() or m.islnk():raise ValueError("Unexpected archive object")
            p=Path(m.name)
            if p.name in ("SOURCE_AND_QA_NOTES.json", "STATIC_QA.json") and len(p.parts)==1:\n                continue  # Private research notes are not a public page.\n            if p.is_absolute() or ".." in p.parts or len(p.parts)<2 or p.parts[0] not in SITES:
                raise ValueError("Unsafe or unexpected preview path")
            if p.suffix not in (".html",".css",".js"):
                raise ValueError("Unexpected archive file type")
            payload[p]=tar.extractfile(m).read()
    for site, expected in SITES.items():
        htmlpaths={str(p.relative_to(site)) for p in payload if p.parts[0]==site and p.suffix==".html"}
        if htmlpaths!=expected:raise ValueError(f"{site}: incomplete pages {htmlpaths^expected}")
        for asset in ["assets/site.css","assets/site.js"]:
            if Path(site)/asset not in payload:raise ValueError(f"{site}: missing {asset}")
        css=payload[Path(site)/"assets/site.css"].decode("utf-8")
        if "font-size:16px" not in css or "body [data-reveal].visible{opacity:1" not in css:
            raise ValueError(f"{site}: navigation/no-script safety patch missing")
        for route in expected:
            p=Path(site)/route
            h=payload[p].decode("utf-8")
            audit=HTMLAudit();audit.feed(h)
            if "noindex" not in audit.robots or "nofollow" not in audit.robots:
                raise ValueError(f"{p}: missing preview noindex")
            if set(audit.quality.split(";"))!={"TECHNICAL_PREVIEW_ONLY","QUALITY_PENDING","HOLD"}:
                raise ValueError(f"{p}: missing explicit quality hold")
            if "EI JULKAISUUN" not in h or "KAURIVON SISÄINEN" not in h.upper():
                raise ValueError(f"{p}: missing owner-review warning")
            if "<h1" not in h or audit.forms or "9,5/10 hyväksytty" in h.lower():
                raise ValueError(f"{p}: broken content or misleading approval")
            for url in audit.links+audit.script+[a for a,b in audit.images]:
                if url.startswith(("https://","http://","mailto:","tel:","#","//")):continue
                target=(p.parent/unquote(url.split("#")[0].split("?")[0])).as_posix()
                # Do not allow cross-company local links or files missing from this exact build.
                target=Path(__import__("posixpath").normpath(target))
                if target not in payload:
                    raise ValueError(f"{p}: unresolved internal link or asset {url}")
            for url,alt in audit.images:
                if not url.startswith("https://") or not alt.strip():
                    raise ValueError(f"{p}: missing honest external-source alt or HTTPS")
    # Atomic-ish installation: validate everything BEFORE writing to publishing tree.
    dest.mkdir(parents=True,exist_ok=True)
    for p,data in payload.items():
        target=dest/p;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(data)
    digest=hashlib.sha256(b"".join(str(p).encode()+payload[p] for p in sorted(payload))).hexdigest()
    meta={"status":STATUS,"revision_sha256":digest,"count_sites":len(SITES),
          "count_html":sum(p.suffix==".html" for p in payload),
          "internal_owner_review_only":True,"independent_visual_95":"NOT_PERFORMED",
          "original_image_rights":"UNVERIFIED","original_vs_new_browser_qa":"NOT_PERFORMED",
          "client_outreach_allowed":False}
    (dest/"QUALITY_PENDING.json").write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding="utf-8")
    return meta

if __name__=="__main__":
    parser=argparse.ArgumentParser()
    parser.add_argument("--archive",type=Path,required=True)
    parser.add_argument("--dest",type=Path,required=True)
    args=parser.parse_args()
    print(json.dumps(validate_and_install(args.archive,args.dest),ensure_ascii=False))

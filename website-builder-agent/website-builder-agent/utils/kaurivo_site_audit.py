"""One-request-per-PRH-website HTML metadata checks for Kaurivo.

Strict limits: no paid API/AI, no redirects, no login, no forms/posts, no
personal data harvesting, no asset crawling, and no claims of website quality,
SEO ranking, Lighthouse score, solvency, absence or site ownership.
A 30-day local cache prevents repeated queries across GitHub Action runs.
"""
from __future__ import annotations
import argparse
from datetime import datetime, timezone, timedelta
import ipaddress
import json
from pathlib import Path
import re
import socket
from urllib.parse import urlsplit, urljoin
import requests
from bs4 import BeautifulSoup

MAX_CHECKS = 12
MAX_PACKET_BYTES = 500_000
MAX_HTML_BYTES = 512_000
CACHE_MAX = 2500
TTL = timedelta(days=30)
USER_AGENT = "KaurivoSiteResearch/1.0 (public homepage metadata audit; no contacts collected)"
LANGS = {"fi","sv","en"}
ISSUES = {
    "title_missing": "HTML-otsikko puuttuu",
    "meta_description_missing": "Meta description puuttuu",
    "viewport_missing": "Mobiilin viewport puuttuu",
    "heading_missing": "H1-otsikkoa ei löytynyt",
    "contact_link_missing": "Yhteystietolinkkiä ei löytynyt etusivulta",
}

def safe_homepage(url, resolve=socket.getaddrinfo):
    if not isinstance(url,str) or len(url)>1200:
        return ""
    try:
        parsed=urlsplit(url)
        if parsed.scheme!="https" or not parsed.hostname or parsed.username or parsed.password:
            return ""
        if parsed.port not in (None,443):
            return ""
        hostname=parsed.hostname.lower().rstrip(".")
        if (len(hostname)>200 or "." not in hostname or
            hostname.endswith((".local",".internal",".localhost",".test")) or
            any(x in hostname for x in ("\\","%","@"))):
            return ""
        addresses=resolve(hostname,443,type=socket.SOCK_STREAM)
        if not addresses:
            return ""
        for address in addresses:
            ip=ipaddress.ip_address(address[4][0])
            if not ip.is_global:
                return ""
        return parsed._replace(query="",fragment="",path="/").geturl()
    except (ValueError,IndexError,OSError,TypeError):
        return ""

def extract_html_signals(html, checked_url):
    parsed=BeautifulSoup(html,"html.parser")
    title=(parsed.title.get_text(" ",strip=True) if parsed.title else "").strip()
    description=parsed.find("meta",attrs={"name":re.compile("^description$",re.I)})
    content=(description.get("content","") if description else "").strip()
    viewport=bool(parsed.find("meta",attrs={"name":re.compile("^viewport$",re.I)}))
    h1=bool(parsed.find("h1"))
    contact=any(
      any(word in (link.get_text(" ",strip=True)+" "+link.get("href","")).lower()
          for word in ("contact","kontakt","yhteys","kontakta","ota-yhteytta","booking","boka"))
      for link in parsed.find_all("a",limit=250)
    )
    html_lang=str(parsed.html.get("lang","") if parsed.html else "").lower().split("-")[0]
    languages=set()
    if html_lang in LANGS:languages.add(html_lang)
    for link in parsed.find_all("link",attrs={"hreflang":True},limit=40):
        value=str(link.get("hreflang","")).lower().split("-")[0]
        if value in LANGS:languages.add(value)
    lang_suggestion="fi_sv" if {"fi","sv"}.issubset(languages) else (
        html_lang if html_lang in LANGS else "undetermined"
    )
    issues=[]
    if len(title)<6:issues.append("title_missing")
    if len(content)<30:issues.append("meta_description_missing")
    if not viewport:issues.append("viewport_missing")
    if not h1:issues.append("heading_missing")
    if not contact:issues.append("contact_link_missing")
    return {"status":"html_checked","url":checked_url,"title_present":bool(title),
       "meta_description_present":len(content)>=30,"viewport_present":viewport,
       "h1_present":h1,"contact_link_present":contact,
       "html_language_hint":lang_suggestion,"language_hints":sorted(languages),
       "issues":issues,"method":"one_public_homepage_html_only"}

def inspect_site(url, *,get=requests.get,head=None,resolve=socket.getaddrinfo):
    safe=safe_homepage(url,resolve=resolve)
    if not safe:return {"status":"unsafe_or_unresolvable_url","issues":[]}
    try:
        with get(safe,headers={"User-Agent":USER_AGENT,
             "Accept":"text/html,application/xhtml+xml"},
             timeout=(4,9),stream=True,allow_redirects=False) as response:
            # Do not follow cross-origin redirects; do not fetch assets.
            if response.status_code in (301,302,303,307,308):
                return {"status":"redirect_not_followed","issues":[]}
            if response.status_code in (403,429,451):
                return {"status":"blocked_or_limited","issues":[]}
            if response.status_code!=200:
                return {"status":"http_status_"+str(response.status_code),"issues":[]}
            ctype=response.headers.get("Content-Type","").lower()
            if "text/html" not in ctype and "application/xhtml+xml" not in ctype:
                return {"status":"non_html","issues":[]}
            chunks=[];size=0
            for chunk in response.iter_content(chunk_size=16384):
                size+=len(chunk)
                if size>MAX_HTML_BYTES:
                    return {"status":"html_too_large","issues":[]}
                chunks.append(chunk)
            encoding=response.encoding or "utf-8"
            html=b"".join(chunks).decode(encoding,"replace")
            result=extract_html_signals(html,safe)
            # Optional HEAD checks are only a small same-host sample.
            # Never call cross-domain links or treat HEAD failures as proof.
            result["checked_internal_links"]=0
            result["possible_broken_internal_links"]=0
            if head is not None:
                home_host=urlsplit(safe).hostname
                paths=set()
                soup=BeautifulSoup(html,"html.parser")
                for a in soup.find_all("a",href=True,limit=100):
                    target=urljoin(safe,a["href"])
                    parsed=urlsplit(target)
                    if (parsed.scheme!="https" or parsed.hostname!=home_host
                        or parsed.port not in (None,443) or
                        not parsed.path.startswith("/") or parsed.path=="/"
                        or parsed.query):
                        continue
                    paths.add(parsed._replace(query="",fragment="").geturl())
                    if len(paths)>=2:break
                for target in list(paths)[:2]:
                    # The initial public DNS check still applies; the sample
                    # host is exactly the original validated homepage host.
                    try:
                        response_head=head(target,headers={"User-Agent":USER_AGENT},
                            timeout=(4,6),allow_redirects=False)
                        result["checked_internal_links"]+=1
                        if response_head.status_code in (404,410):
                            result["possible_broken_internal_links"]+=1
                        response_head.close()
                    except requests.RequestException:
                        pass
            return result
    except (requests.RequestException,UnicodeError,LookupError,ValueError):
        return {"status":"temporarily_unavailable","issues":[]}

def _read_cache(path):
    try:
        obj=json.loads(Path(path).read_text(encoding="utf-8"))
        return obj if isinstance(obj,dict) else {}
    except (OSError,ValueError):return {}

def audit_packet(packet_path,cache_path,*,get=requests.get,head=None,
                 resolve=socket.getaddrinfo,max_checks=MAX_CHECKS,now=None):
    packet_path,cache_path=Path(packet_path),Path(cache_path)
    if not packet_path.is_file() or packet_path.stat().st_size>MAX_PACKET_BYTES:
        raise ValueError("Invalid/oversized PRH shortlist")
    packet=json.loads(packet_path.read_text(encoding="utf-8"))
    if (packet.get("schema")!="kaurivo_prh_shortlist_v1" or
       packet.get("mode")!="pilot-live" or not isinstance(packet.get("candidates"),list) or
       len(packet["candidates"])>50):
        raise ValueError("Only trusted PRH list is auditable")
    cache=_read_cache(cache_path)
    now=now or datetime.now(timezone.utc)
    attempts=0;cached=0;ok=0
    max_checks=min(MAX_CHECKS,max(0,int(max_checks)))
    for lead in packet["candidates"]:
        url=lead.get("website_listed_url") or ""
        if not url:continue
        key=urlsplit(url).hostname
        if not key:continue
        prev=cache.get(key)
        audit=None
        if isinstance(prev,dict) and isinstance(prev.get("audit"),dict):
            try:
                since=now-datetime.fromisoformat(str(prev["at"]).replace("Z","+00:00"))
                if timedelta(0)<=since<TTL:
                    audit=prev["audit"];cached+=1
            except (ValueError,TypeError):pass
        if audit is None:
            if attempts>=max_checks:continue
            attempts+=1
            audit=inspect_site(url,get=get,head=head,resolve=resolve)
            cache[key]={"at":now.isoformat(),"audit":audit}
        lead["site_technical_audit"]=audit
        lead["website_audit_checked_at"]=cache[key]["at"]
        if audit.get("status")=="html_checked":ok+=1
    if len(cache)>CACHE_MAX:
        cache=dict(sorted(cache.items(),key=lambda x:str(x[1].get("at","")),
                          reverse=True)[:CACHE_MAX])
    payload=json.dumps(packet,ensure_ascii=False,indent=2)+"\n"
    if len(payload.encode("utf-8"))>MAX_PACKET_BYTES:
        raise ValueError("Packet grew beyond safety bound")
    packet_path.write_text(payload,encoding="utf-8")
    cache_path.parent.mkdir(parents=True,exist_ok=True)
    cache_path.write_text(json.dumps(cache,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    return {"checked":attempts,"cache_hits":cached,"html_checked":ok,
            "external_paid_credits_used":0,"assets_crawled":0,"marketing_sent":0}

def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument("--packet",required=True)
    parser.add_argument("--cache",default="data/kaurivo_site_audit_cache.json")
    parser.add_argument("--max-checks",type=int,default=MAX_CHECKS)
    args=parser.parse_args(argv)
    print(json.dumps(audit_packet(args.packet,args.cache,max_checks=args.max_checks,
      head=requests.head)))

if __name__=="__main__":main()

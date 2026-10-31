"""Optional, bounded official-search-API website suggestions for Kaurivo.

Default is OFF. Requires KAURIVO_TAVILY_API_KEY in GitHub Actions secrets.
At most 12 basic queries per scheduled PRH run, at most 1 per company.
Never claims a proposed URL is confirmed or a company's website needs redesign.
No scraping search engines, personal contact extraction, marketing or AI calls.
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import re
import unicodedata
from urllib.parse import urlsplit
import requests

API = "https://api.tavily.com/search"
MAX_QUERIES_PER_RUN = 12
MAX_PACKET_BYTES = 200_000
DISALLOWED = (
    "facebook.com", "instagram.com", "linkedin.com", "tiktok.com",
    "ytj.fi", "prh.fi", "finder.fi", "fonecta.fi", "asiakastieto.fi",
    "kauppalehti.fi", "suomi.fi", "yelp.com", "trustpilot.com",
    "google.com", "google.fi", "maps.google.com", "wikipedia.org",
    "duunitori.fi", "oikotie.fi", "op.fi", "youtube.com", "reddit.com",
    "linkedin.fi", "instagram.fi", "tori.fi", "yritystele.fi",
)
COMMON = {
    "oy", "ab", "oyj", "ltd", "osakeyhtio", "aktiebolag",
    "suomi", "finland", "palvelu", "palvelut", "the", "and"
}

def tokens(text):
    normalized = unicodedata.normalize("NFKD", str(text).lower())
    normalized = "".join(c for c in normalized if not unicodedata.combining(c))
    return [v for v in re.findall(r"[a-z0-9]{3,}", normalized) if v not in COMMON]

def plausible_url(url):
    if not isinstance(url, str) or len(url)>1200:
        return ""
    try:
        parsed = urlsplit(url)
        host = (parsed.hostname or "").lower().rstrip(".")
        if (parsed.scheme not in ("https", "http") or
            not host or "." not in host or
            parsed.username or parsed.password or
            parsed.port not in (None,443,80) or
            any(host==v or host.endswith("."+v) for v in DISALLOWED) or
            host in ("localhost", "127.0.0.1") or
            re.search(r"(^|[.])(?:localhost|local|internal)$", host)):
            return ""
        # Restrict to traditional domains; avoid redirects, data URLs and
        # numeric-address destinations. We do NOT fetch the candidate URL.
        if re.fullmatch(r"[0-9.]+",host) or "@" in url or "\\" in url:
            return ""
        return parsed._replace(fragment="").geturl()
    except (ValueError,TypeError):
        return ""

def rank_search_candidate(company, results):
    """Return an UNVERIFIED suggestion only when brand match has evidence.

    No provider score can prove site ownership. Weak / ambiguous candidates
    remain empty and require human search.
    """
    name_tokens=tokens(company.get("name") or company.get("company_name"))
    distinctive=[t for t in name_tokens if len(t)>=4]
    if not distinctive:
        return None
    candidates=[]
    for item in results[:6]:
        if not isinstance(item,dict):
            continue
        url=plausible_url(item.get("url"))
        if not url:
            continue
        source_text=" ".join((urlsplit(url).hostname or "",str(item.get("title","")),
            str(item.get("content",""))[:250]))
        source_tokens=set(tokens(source_text))
        matched=set(distinctive)&source_tokens
        # Two distinct company-name tokens or a very distinctive single
        # name that appears both in domain and page title.
        domain=(urlsplit(url).hostname or "").lower()
        domain_compact="".join(re.findall(r"[a-z0-9]+", domain))
        title_tokens=set(tokens(item.get("title","")))
        domain_match=any(t in domain_compact for t in distinctive)
        title_match=bool(set(distinctive)&title_tokens)
        # A directory or blog article mentioning the business is not its
        # own website. Require an identifiable brand token in the HOSTNAME
        # as well as the result title; full site ownership still unverified.
        strong_single=(len(distinctive)==1 and len(distinctive[0])>=7 and
            domain_match and title_match)
        strong_multi=len(matched)>=2 and domain_match and title_match
        if not strong_multi and not strong_single:
            continue
        pts=75+min(15,5*len(matched))
        if domain_match: pts+=5
        if title_match: pts+=3
        candidates.append((min(99,pts),url))
    if not candidates:
        return None
    candidates.sort(key=lambda v:(-v[0],v[1]))
    return {"url":candidates[0][1],"source":"tavily_search","confidence":candidates[0][0]}

def search_once(company,*,key,post=requests.post):
    q=(str(company.get("name",""))[:100]+" "+str(company.get("city_hint",""))[:40]+
       " virallinen kotisivu yritys Finland").strip()
    response=post(API,json={
        "query":q, "search_depth":"basic", "max_results":5,
        "include_answer":False, "include_raw_content":False,
        "include_images":False, "topic":"general",
    },headers={"Authorization":"Bearer "+key,"Content-Type":"application/json"},
        timeout=(6,20))
    if response.status_code in (401,402,403,429,432,433):
        return None, True
    response.raise_for_status()
    data=response.json()
    if not isinstance(data,dict):
        return None, False
    return rank_search_candidate(company,data.get("results") or []),False

def enrich(packet_path,*,key="",max_queries=MAX_QUERIES_PER_RUN,post=requests.post):
    packet_path=Path(packet_path)
    if not packet_path.is_file() or packet_path.stat().st_size>MAX_PACKET_BYTES:
        raise RuntimeError("Missing or oversized PRH shortlist")
    packet=json.loads(packet_path.read_text(encoding="utf-8"))
    if packet.get("schema")!="kaurivo_prh_shortlist_v1" or packet.get("mode")!="pilot-live":
        raise RuntimeError("Only real source shortlists can be researched")
    leads=packet.get("candidates")
    if not isinstance(leads,list) or len(leads)>50:
        raise RuntimeError("Invalid source shortlist")
    if not key:
        return {"enabled":False,"searched":0,"suggested":0,"credits_budgeted":0}
    limit=min(max(0,int(max_queries)),MAX_QUERIES_PER_RUN)
    searched=suggested=0
    for candidate in leads:
        if searched>=limit:
            break
        if candidate.get("website_listed_url") or candidate.get("website_search_candidate"):
            continue
        if not candidate.get("name"):
            continue
        searched+=1
        try:
            found,stop=search_once(candidate,key=key,post=post)
            if found:
                candidate["website_search_candidate"]=found
                suggested+=1
            if stop:
                break
        except (requests.RequestException, ValueError):
            # Stop on provider trouble, don't burn the rest of today's quota.
            break
    if packet_path.stat().st_size>MAX_PACKET_BYTES:
        raise RuntimeError("Unexpected source packet mutation")
    payload=json.dumps(packet,ensure_ascii=False,indent=2)+"\n"
    if len(payload.encode("utf-8"))>MAX_PACKET_BYTES:
        raise RuntimeError("Enriched packet exceeds ingest limit")
    packet_path.write_text(payload,encoding="utf-8")
    return {"enabled":True,"searched":searched,"suggested":suggested,
            "credits_budgeted":searched,"emails_sent":0,"ai_credits_used":0}

def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument("--packet",required=True)
    parser.add_argument("--max-queries",type=int,default=MAX_QUERIES_PER_RUN)
    args=parser.parse_args(argv)
    result=enrich(args.packet,key=os.environ.get("KAURIVO_TAVILY_API_KEY",""),
                  max_queries=args.max_queries)
    print(json.dumps(result,ensure_ascii=False))

if __name__=="__main__":
    main()

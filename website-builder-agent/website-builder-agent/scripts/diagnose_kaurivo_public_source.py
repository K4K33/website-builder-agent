"""Temporary public-only zero-token reproduction of Kaurivo's source crawler.
Print URL PATHS and status classes, never content, query strings or tokens.
Does not update CRM, charge AI, or build/publish anything.
"""
from __future__ import annotations
import json
from urllib.parse import urlsplit
from utils.fetch import analyze_url,normalize_url
from utils.industry_workflow import crawl_original_website, _priority

START="https://www.kurki-suonio.fi/"
def clean_path(url):
    p=urlsplit(str(url))
    return (p.path or "/")[:160]
def failure_code(result):
    if result.get("success"):
        return "ok"
    message=str(result.get("error") or "")
    http=result.get("status_code")
    if isinstance(http,int):
        return "http_"+str(http)
    for name in ("SSL-virhe","Timeout","Yhteysvirhe","HTML"):
        if name.casefold() in message.casefold():
            return name.lower().replace("-virhe","_failure")
    return "other_fetch_failure"

def connection_subtype(result):
    # Fixed public-site check only. Never print raw exception strings or HTML.
    s=str(result.get("error") or "").casefold()
    for name in ("nameresolutionerror","temporary failure in name resolution",
                 "connection refused","connectionreseterror",
                 "remotedisconnected","proxyerror","ssleoferror",
                 "ssl","timed out","timeout","forcibly closed",
                 "network is unreachable","max retries exceeded",
                 "remote end closed connection"):
        if name in s:
            return name.replace(" ","_")
    return "not_classified"

def check():
    print("TRANSPORT_FIX_VERSION", "ua-retry-1")
    import socket
    for host in ("www.kurki-suonio.fi","kurki-suonio.fi"):
        try:
            addresses=socket.getaddrinfo(host,443)
            print("DNS",host,"ok",len(addresses),"records")
        except socket.gaierror as e:
            print("DNS",host,"failed",e.errno)
    for alt in ("https://www.kurki-suonio.fi/",
                "https://kurki-suonio.fi/",
                "http://www.kurki-suonio.fi/"):
        result=analyze_url(alt)
        print("ALT",json.dumps({"url_kind":alt.split("://",1)[0]+
             ("/www" if "://www." in alt else "/apex"),
             "status":result.get("status_code"),"success":result.get("success"),
             "type":failure_code(result),"connection":connection_subtype(result),
             "final_path":clean_path(result.get("final_url") or alt)}))
    import requests
    from utils.fetch import HEADERS
    for label,headers,no_env in (
      ("original",HEADERS,False),
      ("normal_browser",{"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"},False),
      ("direct_normal_browser",{"User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"},True),
      ("no_useragent",{},False),
    ):
        sess=requests.Session()
        sess.trust_env=not no_env
        try:
            resp=sess.get(START,headers=headers,timeout=9)
            print("VARIANT",label,"http",resp.status_code,"len",len(resp.content),
                  "redirect_path",clean_path(resp.url))
        except Exception as err:
            low=str(err).lower()
            flags=[name for name in (
              "remotedisconnected","proxyerror","connectionreset","ssleoferror",
              "name resolution","timeout","connection refused","max retries exceeded"
            ) if name in low]
            print("VARIANT",label,"failed",",".join(flags) or type(err).__name__)
    # The real premium builder includes Chromium. Probe the actual
    # browser response before deciding this host cannot be researched.
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser=pw.chromium.launch(headless=True,args=["--no-sandbox"])
            page=browser.new_page()
            response=page.goto(START,wait_until="domcontentloaded",timeout=20000)
            page.wait_for_timeout(1800)
            title=page.title()
            body=page.locator("body").inner_text(timeout=5000)
            print("BROWSER",json.dumps({"status":response.status if response else None,
                "title_length":len(title),"body_text_length":len(body),
                "links":page.locator("a[href]").count(),
                "path":clean_path(page.url)}))
            browser.close()
    except Exception as exc:
        print("BROWSER_ERROR",type(exc).__name__)
    home=analyze_url(START)
    print("ROOT",json.dumps({"success":home.get("success"),
      "status":home.get("status_code"),
      "error_type":failure_code(home),"final_path":clean_path(home.get("final_url") or START),
      "num_links":len(home.get("links") or []),"text_bytes":len(home.get("visible_text") or "")}))
    if not home.get("success"):
        return
    seen={}
    def fetch(url):
        result=analyze_url(url)
        path=clean_path(url)
        seen[path]={"success":bool(result.get("success")),"status":result.get("status_code"),
          "error_type":failure_code(result),"redirect_path":clean_path(result.get("final_url") or url)}
        return result
    inventory=crawl_original_website(normalize_url(START),fetch,first_page=home,max_pages=24)
    print("INVENTORY",json.dumps({"pages":len(inventory["pages"]),
      "failed_paths":[clean_path(u) for u in inventory["failed_urls"]],
      "priority_unvisited_paths":[clean_path(u) for u in inventory["priority_unvisited_urls"]],
      "all_visited":seen},ensure_ascii=False))
    gaps=[u for u in inventory["failed_urls"]
          if _priority(u)[0]==0 or u==inventory["root_url"]]
    print("CRITICAL",json.dumps({"count":len(gaps),"paths":[clean_path(u) for u in gaps]},ensure_ascii=False))

if __name__=="__main__":check()

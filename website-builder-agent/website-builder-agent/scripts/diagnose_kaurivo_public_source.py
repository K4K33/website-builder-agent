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

def check():
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

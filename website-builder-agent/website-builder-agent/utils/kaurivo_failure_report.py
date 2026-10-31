"""Report actual failed national PRH night runs into Kaurivo admin.

One short-lived GitHub OIDC assertion, one authenticated Supabase Edge call.
No static secrets, PRH/AI credits, duplicate retries, or emails.
Never report synthetic/offline runs as production failures.
"""
import datetime as dt
import json
import os
import sys
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

AUDIENCE="kaurivo-prh-ingest-xhsfbcwpwbgdbatrcyuk"
ENDPOINT="https://xhsfbcwpwbgdbatrcyuk.supabase.co/functions/v1/kaurivo-prh-ingest"

def report_failure(*,env=None,send=urlopen):
    env=os.environ if env is None else env
    if env.get("KAURIVO_PRH_MODE")!="pilot-live":
        return {"sent":False,"reason":"offline_mode"}
    url=env.get("ACTIONS_ID_TOKEN_REQUEST_URL","")
    secret=env.get("ACTIONS_ID_TOKEN_REQUEST_TOKEN","")
    if not url.startswith("https://") or not secret:
        return {"sent":False,"reason":"oidc_unavailable"}
    date=dt.datetime.now(ZoneInfo("Europe/Helsinki")).date().isoformat()
    token_request=Request(
      url+("&" if "?" in url else "?")+urlencode({"audience":AUDIENCE}),
      headers={"Authorization":"bearer "+secret,"Accept":"application/json"})
    with send(token_request,timeout=12) as reply:
        token=json.load(reply).get("value")
    if not isinstance(token,str) or len(token)<100:
        return {"sent":False,"reason":"oidc_token_missing"}
    payload=json.dumps({
      "schema":"kaurivo_prh_run_status_v1",
      "outcome":"failure","date":date
    }).encode("utf-8")
    event=Request(ENDPOINT,data=payload,method="POST",headers={
      "Authorization":"Bearer "+token,
      "Content-Type":"application/json"
    })
    with send(event,timeout=15) as reply:
        result=json.load(reply)
    return {"sent":result.get("status_recorded") is True,
      "reason":"recorded" if result.get("status_recorded") is True else "write_failed",
      "date":date}

def main():
    try:
        outcome=report_failure()
    except Exception:
        outcome={"sent":False,"reason":"reporter_unavailable"}
    # Never print tokens, response bodies, company data, or secrets.
    print(json.dumps(outcome,ensure_ascii=False))
    return 0  # Reporting is best effort; don't hide the original failed run.

if __name__=="__main__":
    sys.exit(main())

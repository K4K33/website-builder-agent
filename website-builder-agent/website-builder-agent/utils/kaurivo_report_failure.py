"""Report a failed scheduled PRH run with scoped GitHub OIDC, zero paid APIs.

Only used by GitHub Actions when the national PRH workflow itself fails.
Never logs tokens, does not invent companies or send marketing emails.
"""
from datetime import datetime
from zoneinfo import ZoneInfo
from urllib.request import Request, urlopen
from urllib.parse import urlencode
import json
import os

AUDIENCE="kaurivo-prh-ingest-xhsfbcwpwbgdbatrcyuk"
ENDPOINT="https://xhsfbcwpwbgdbatrcyuk.supabase.co/functions/v1/kaurivo-prh-ingest"

def report(*,environment=None,get=urlopen):
    env=os.environ if environment is None else environment
    url=env.get("ACTIONS_ID_TOKEN_REQUEST_URL","")
    token=env.get("ACTIONS_ID_TOKEN_REQUEST_TOKEN","")
    if not url.startswith("https://") or not token:
        return False
    sep="&" if "?" in url else "?"
    request=Request(url+sep+urlencode({"audience":AUDIENCE}),headers={
      "Authorization":"bearer "+token,"Accept":"application/json"})
    with get(request,timeout=15) as response:
        jwt=json.load(response).get("value")
    if not isinstance(jwt,str) or not jwt:
        return False
    day=datetime.now(ZoneInfo("Europe/Helsinki")).date().isoformat()
    payload=json.dumps({"schema":"kaurivo_prh_run_status_v1",
                        "date":day,"outcome":"failure"}).encode("utf-8")
    with get(Request(ENDPOINT,method="POST",data=payload,headers={
      "Authorization":"Bearer "+jwt,"Content-Type":"application/json"}),
      timeout=20) as response:
        return response.status==200

if __name__=="__main__":
    try:
        ok=report()
        print("Kaurivo failure status reported" if ok else
              "Kaurivo failure status could not be reported; see Actions logs.")
    except Exception:
        print("Kaurivo failure report unavailable; see Actions logs.")

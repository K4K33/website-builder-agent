"""Optional privacy-preserving Kaurivo feedback priors for daily PRH selection.

OIDC to the existing ingest Edge function; the response contains only
aggregated positive/negative counts for sectors with >=8 human evaluations.
No company contacts, secrets, website URLs, AI or paid API calls.
Failures default to neutral weights and never prevent the PRH nightly run.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
from urllib.parse import urlencode
import requests

AUDIENCE="kaurivo-prh-ingest-xhsfbcwpwbgdbatrcyuk"
URL="https://xhsfbcwpwbgdbatrcyuk.supabase.co/functions/v1/kaurivo-prh-ingest"

def get_weights(*,env=None,get=requests.get,post=requests.post):
    env=os.environ if env is None else env
    auth_url=env.get("ACTIONS_ID_TOKEN_REQUEST_URL","")
    auth_token=env.get("ACTIONS_ID_TOKEN_REQUEST_TOKEN","")
    if not auth_url.startswith("https://") or not auth_token:return {}
    try:
        auth=get(auth_url+("&" if "?" in auth_url else "?")+
          urlencode({"audience":AUDIENCE}),
          headers={"Authorization":"bearer "+auth_token,"Accept":"application/json"},
          timeout=(4,10))
        auth.raise_for_status()
        jwt=auth.json().get("value")
        if not isinstance(jwt,str) or not 100<=len(jwt)<=7000:return {}
        response=post(URL,headers={"Authorization":"Bearer "+jwt,
          "Content-Type":"application/json"},
          json={"schema":"kaurivo_feedback_weights_v1"},timeout=(4,12))
        response.raise_for_status()
        reply=response.json()
        if reply.get("ok") is not True or not isinstance(reply.get("weights"),dict):return {}
        priors={}
        for k,v in reply["weights"].items():
            if not isinstance(k,str) or len(k)!=2 or not k.isdigit() or not isinstance(v,dict):
                continue
            count=v.get("count");boost=v.get("boost")
            if not isinstance(count,int) or count<8 or not isinstance(boost,int) or not -4<=boost<=4:
                continue
            priors[k]={"boost":boost,"count":count}
        return priors
    except (requests.RequestException,ValueError,KeyError,TypeError):
        return {}

def run(path,*,env=None,get=requests.get,post=requests.post):
    weights=get_weights(env=env,get=get,post=post)
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(json.dumps(weights,ensure_ascii=False)+"\n",encoding="utf-8")
    return {"sectors_with_evidence":len(weights),"ai_credits_used":0,
            "marketing_emails_sent":0}

def main():
    print(json.dumps(run("output/nightly-prh/feedback-priors.json")))

if __name__=="__main__":main()

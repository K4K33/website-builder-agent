"""Skip redundant PRH national runs after any proven success on the same Finnish day.

One read-only GitHub API request. No PRH, AI, SMTP or database credits used.
On API errors we run the backup rather than silently lose that day's leads.
"""
import datetime as dt
import json
import os
import sys
from urllib.request import Request, urlopen
from zoneinfo import ZoneInfo

API=("https://api.github.com/repos/K4K33/website-builder-agent/actions/"
     "workflows/kaurivo-national-prh.yml/runs?event=schedule&per_page=40")
BACKUP_CRON="17 6 * * *"
PRIMARY_CRON="13 4 * * *"

def should_scan(*, event="schedule", cron="", token="", run_id="", fetch=urlopen,
                local_day=None):
    # Both scheduled slots share the same daily budget. GitHub can start
    # a 04:13 run many hours late (observed 2026-11-01 at 11:12 Helsinki).
    # Never assume a successful 04:13 run starts before 06:00.
    if event!="schedule" or cron not in (BACKUP_CRON,PRIMARY_CRON):
        return True
    if not token: return True
    day=local_day or dt.datetime.now(ZoneInfo("Europe/Helsinki")).date()
    try:
        request=Request(API,headers={
          "Authorization":"Bearer "+token,
          "Accept":"application/vnd.github+json",
          "User-Agent":"KaurivoScheduledPRHBackup/1.0"
        })
        with fetch(request,timeout=15) as response:
            data=json.load(response)
        for run in data.get("workflow_runs",[]):
            if str(run.get("id"))==str(run_id): continue
            created=dt.datetime.fromisoformat(run["created_at"].replace("Z","+00:00"))
            local=created.astimezone(ZoneInfo("Europe/Helsinki"))
            # A completed successful national scan from ANY earlier run
            # today is enough. Do not duplicate if GitHub delayed it until
            # 11:12 or if the recovery happened to run before the primary.
            if (local.date()==day and
                run.get("event")=="schedule" and run.get("conclusion")=="success"):
                return False
        return True
    except (OSError,ValueError,KeyError,TypeError):
        return True

def main():
    need=should_scan(event=os.environ.get("GITHUB_EVENT_NAME",""),
        cron=os.environ.get("SCHEDULE_CRON",""),
        token=os.environ.get("GH_TOKEN",""),
        run_id=os.environ.get("GITHUB_RUN_ID",""))
    output=os.environ.get("GITHUB_OUTPUT")
    if output:
        with open(output,"a",encoding="utf-8") as f:
            f.write("should_scan="+("true" if need else "false")+"\n")
    print(json.dumps({"should_scan":need,
        "reason":"overnight_fallback_or_primary" if need else "primary_already_succeeded",
        "ai_credits_used":0},ensure_ascii=False))
    return 0

if __name__=="__main__":
    sys.exit(main())

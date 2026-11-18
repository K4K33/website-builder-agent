"""Audit international V7 reference candidates in a REAL Chromium scroll.

Checks what the browser actually renders/scrolls. This does not pronounce
third-party sites 10/10; human art-direction and end-to-end journey judgment
remain independent. Zero paid search or AI inference calls.
"""
from __future__ import annotations

import argparse
from datetime import datetime,timezone
import json
from pathlib import Path

from utils.quality_v7 import REFERENCES_V7
from utils.screenshot import capture_website,REFERENCE_VIEWPORTS
from utils.reference_scroll_experience import complete_scroll_evidence,compact_scroll_observations


def audit(*,count=15,category="",output_dir="output/v7-reference-scroll-audit"):
    folder=Path(output_dir)
    folder.mkdir(parents=True,exist_ok=True)
    data=json.loads(REFERENCES_V7.read_text("utf-8"))
    targets=[row for row in data["industries"]
             if not category or row["category"]==category][:count]
    if not targets:
        raise ValueError("No reference candidate matches the category")
    entries=[]
    for row in targets:
        url=row["url"]
        try:
            shots=capture_website(url,"global-v7-"+row["category"],
                                  viewports=REFERENCE_VIEWPORTS,scroll_experience=True)
            verified=complete_scroll_evidence(shots)
            observations=compact_scroll_observations(shots)
            entry={"category":row["category"],"url":url,
                   "browser_scroll_evidence":"OBSERVED" if verified else "PENDING",
                   "experience":observations,
                   "aesthetic_quality_review":"NOT_ASSESSED",
                   "human_scrolling_and_motion_review":"PENDING",
                   "status":row.get("status")}
        except Exception as exc:
            entry={"category":row["category"],"url":url,
                   "browser_scroll_evidence":"PENDING","error_type":type(exc).__name__,
                   "aesthetic_quality_review":"NOT_ASSESSED",
                   "human_scrolling_and_motion_review":"PENDING"}
        entries.append(entry)
        print(row["category"],entry["browser_scroll_evidence"],flush=True)
    report={"protocol":"kaurivo-v7-international-live-scroll-audit-v1",
            "at_utc":datetime.now(timezone.utc).isoformat(),
            "attempted":len(entries),
            "actually_scrolled_and_evidenced":sum(
                row["browser_scroll_evidence"]=="OBSERVED" for row in entries),
            "quality_9_5_certified":False,
            "no_external_assets_copied":True,
            "entries":entries}
    (folder/"report.json").write_text(
        json.dumps(report,indent=2,ensure_ascii=False)+"\n",encoding="utf-8")
    return report


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--count",type=int,default=15)
    parser.add_argument("--category",default="")
    parser.add_argument("--output-dir",default="output/v7-reference-scroll-audit")
    args=parser.parse_args()
    if not 1<=args.count<=15:
        parser.error("--count must be 1..15")
    report=audit(count=args.count,category=args.category,output_dir=args.output_dir)
    print("Observed live scroll: "+str(report["actually_scrolled_and_evidenced"])+
          "/"+str(report["attempted"]))


if __name__=="__main__":
    main()

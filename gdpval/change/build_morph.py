#!/usr/bin/env python3
"""Build reproducible GDPval 2025 -> 2026 morph data with task-ID provenance.

2026 occupational colours are explicitly an *illustrative scenario*:
official aggregate GDPval win-or-tie 84.9% (GPT-5.5, Apr 2026) calibrated across
the 44 2025 occupation-level baseline scores; 2026 Anthropic task outcomes
inform small relative adjustments. They are NOT observed GDPval results.
"""
import csv
import hashlib
import json
import math
import os
from collections import defaultdict
from pathlib import Path
import re
import subprocess
import sys

HERE = Path(__file__).resolve().parent
CACHE = Path(os.getenv("TEMP") or "/tmp")
SOURCES = {
    "mapping": ("gdpval-2025-data.js", "https://apps.lawrencewu.net/job-tasks/data.js"),
    "onet": ("onet-tasks-2026.csv", "https://raw.githubusercontent.com/theodorewright11/ai-workforce-exposure-dataset-construction-public/main/data/task_statements_v30.1.csv"),
    "wages": ("oews2025.csv", "https://raw.githubusercontent.com/theodorewright11/ai-workforce-exposure-dataset-construction-public/main/data/oews_national_2025.csv"),
    "aei_may": ("aei-june-2026.csv", "https://huggingface.co/datasets/Anthropic/EconomicIndex/resolve/main/release_2026_06_26/data/aei_claude_ai_2026-06-26.csv"),
    "aei_feb": ("aei-march-2026.csv", "https://huggingface.co/datasets/Anthropic/EconomicIndex/resolve/main/release_2026_03_24/data/aei_raw_claude_ai_2026-02-05_to_2026-02-12.csv"),
}
def source(which):
    name, url = SOURCES[which]
    path = CACHE / name
    if not path.exists() or path.stat().st_size < 10000:
        print("Fetching", which, flush=True)
        subprocess.run(["curl.exe" if os.name=="nt" else "curl", "--fail", "--location", "--silent", "--show-error", "--retry", "2", url, "-o", str(path)],check=True)
    return path
def rows(path):
    with path.open(encoding="utf-8-sig", newline="") as f: yield from csv.DictReader(f)
def normalized(s):
    return re.sub(r"[^a-z0-9]+"," ",s.lower()).strip()
def logit(x):
    return math.log(x/(1-x))
def logistic(x):
    return 1/(1+math.exp(-x))
def sha256(path):
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(1024*1024),b""): h.update(chunk)
    return h.hexdigest()
def main():
    mapping_js = source("mapping").read_text(encoding="utf-8")
    third_party = json.loads(mapping_js[mapping_js.index("{"):].strip().rstrip(";"))
    socmap = {(x["sector"],x["n"]):x["soc"] for x in third_party["occupations"]}
    with (HERE.parent/"compensation.csv").open(encoding="utf-8-sig",newline="") as f:
        originals=list(csv.DictReader(f))
    with (HERE.parent/"win.csv").open(encoding="utf-8-sig",newline="") as f:
        wins=list(csv.DictReader(f))
    assert len(originals)==44 and len(socmap)==44 and len(wins)==44*7
    oldw=defaultdict(list)
    for r in wins:oldw[(r["Sector"],r["Occupation"])].append((float(r["Win"]),r["Model"]))
    for r in originals:assert (r["Sector"],r["Occupation"]) in socmap and len(oldw[(r["Sector"],r["Occupation"])])==7

    # BLS: only national, cross-industry. Prefer detailed occupation row if BLS duplicates a broad category.
    bls=defaultdict(list)
    for r in rows(source("wages")):
        if r["AREA"]=="99" and r["NAICS"] in ("0","000000") and r["OWN_CODE"] in ("1235","123"):
            bls[r["OCC_CODE"]].append(r)
    wages={}
    for key,soc in socmap.items():
        candidates=bls[soc]
        if len(candidates)>1: candidates=[r for r in candidates if r["O_GROUP"]=="detailed"]
        assert len(candidates)==1, (soc,len(candidates))
        r=candidates[0]
        workers,wage=int(r["TOT_EMP"]),int(r["A_MEAN"])
        assert workers>0 and wage>0
        wages[key]={"employment":workers,"meanAnnualWage":wage,"billions":round(workers*wage/1e9,2)}

    # Official O*NET 30.1 task IDs -> occupation SOC. Exact task-ID join to May 2026.
    tasks={}
    for r in rows(source("onet")):
        task_id=r["Task ID"]
        if task_id not in tasks:
            tasks[task_id]={"text":r["Task"],"socs":set()}
        tasks[task_id]["socs"].add(r["O*NET-SOC Code"].split(".")[0])
    def relevant(soc,target):
        # GDPval sometimes uses a broad 2018 SOC (e.g. buyers 13-1020).
        # Expand only to O*NET detailed codes inside that SOC, never semantic matches.
        return soc==target or (target[-1]=="0" and soc.startswith(target[:-1]))
    targets=defaultdict(list)
    for task_id,r in tasks.items():
        for key,soc in socmap.items():
            if any(relevant(code,soc) for code in r["socs"]):
                targets[task_id].append(key)
    print("O*NET tasks assigned to at least one GDPval occupation:",len(targets),flush=True)

    # Latest 2026 May Claude.ai task usage: direct O*NET task ID match.
    may={}
    for r in rows(source("aei_may")):
        if r["date_start"]=="2026-05-01" and r["geo_id"]=="GLOBAL" and r["category_name"]=="onet" and r["hierarchy_level"]=="0" and r["metric_id"]=="pct":
            may[r["node_external_id"]]=float(r["value"])
    assert len(may)>1000, "Unexpected AEI May task coverage"
    # February 2026 success among classified Claude.ai conversations on O*NET tasks.
    feb=defaultdict(lambda:defaultdict(float))
    for r in rows(source("aei_feb")):
        if r["geo_id"]=="GLOBAL" and r["facet"]=="onet_task::task_success" and r["variable"]=="onet_task_task_success_count":
            if "::" not in r["cluster_name"]:continue
            title,status=r["cluster_name"].rsplit("::",1)
            if status in ("yes","no"):
                feb[normalized(title)][status]+=float(r["value"])
    occupation=[]
    task_rows=0
    for row in originals:
        key=(row["Sector"],row["Occupation"])
        initial=max(oldw[key])
        evidence=[]
        total_yes=total_no=0.0
        for task_id,keys in targets.items():
            if key not in keys or task_id not in may:continue
            task=tasks[task_id]
            counts=feb.get(normalized(task["text"]),{})
            yes,no=counts.get("yes",0),counts.get("no",0)
            fraction=1/len(keys)
            # Shared O*NET tasks are apportioned, not counted as exclusive evidence.
            total_yes+=yes*fraction
            total_no+=no*fraction
            evidence.append({
                "taskId":task_id,"task":task["text"],"mayUsagePct":round(may[task_id]*fraction,5),
                "febSuccessPct":round(100*yes/(yes+no),1) if yes+no>=10 else None,
                "febClassified":int((yes+no)*fraction),"sharedBy":len(keys)
            })
        evidence.sort(key=lambda x:-x["mayUsagePct"])
        task_rows+=len(evidence)
        occ_success=(total_yes/(total_yes+total_no)) if total_yes+total_no>=20 else None
        occupation.append({
            "sector":key[0],"occupation":key[1],"soc":socmap[key],
            "size2025":float(row["Compensation"]),"size2026":wages[key]["billions"],
            "employment2026":wages[key]["employment"],"meanWage2026":wages[key]["meanAnnualWage"],
            "score2025":initial[0],"model2025":initial[1],
            "tasksMatched":len(evidence),"febClassified":int(total_yes+total_no),
            "febSuccessPct":round(100*occ_success,1) if occ_success is not None else None,
            "tasks":evidence[:5],
            "_success":occ_success
        })
    assert len(occupation)==44 and len({o["sector"] for o in occupation})==9
    assert task_rows>=100, "Suspiciously few tasks mapped"
    # An evidence-informed but explicitly *not measured* 2026 occupation scenario.
    # Calibrate an equal-occupation-weight average to published GPT-5.5 aggregate 84.9.
    # Small capped relative adjustments reflect Anthropic Feb task success only,
    # with zero adjustments where no meaningful classified sample exists.
    available=[o["_success"] for o in occupation if o["_success"] is not None]
    assert available
    reference=sorted(available)[len(available)//2]
    def predicted(o,shift):
        p=max(.02,min(.98,o["score2025"]/100))
        n=o["febClassified"]
        reliability=min(1, n/200)
        adj=0 if o["_success"] is None else max(-.5,min(.5,1.5*(o["_success"]-reference)*reliability))
        return logistic(logit(p)+shift+adj)*100
    low,high=-10,15
    for _ in range(80):
        mid=(low+high)/2
        mean=sum(predicted(o,mid) for o in occupation)/len(occupation)
        if mean<84.9:low=mid
        else:high=mid
    for o in occupation:
        o["score2026"]=round(predicted(o,(low+high)/2),1)
        o.pop("_success")
    old_score_avg=sum(o["score2025"] for o in occupation)/44
    print("May 2026 AEI tasks",len(may),"matched GDPval task observations",task_rows,flush=True)
    print("2026 occupational February success coverage",sum(x["febSuccessPct"] is not None for x in occupation),"of 44",flush=True)
    print("2025 best-of-seven mean",round(old_score_avg,1),"2026 scenario mean",round(sum(o["score2026"] for o in occupation)/44,2),flush=True)
    print("Wages total 2025 vs 2026:",round(sum(o["size2025"] for o in occupation),2),round(sum(o["size2026"] for o in occupation),2),flush=True)
    for o in occupation:
        print(o["occupation"][:24].ljust(25),str(o["tasksMatched"]).rjust(4),"tasks","Feb",str(o["febClassified"]).rjust(5),"2025",str(o["score2025"]).rjust(5),"2026*",str(o["score2026"]).rjust(5))
    sha={key:sha256(source(key)) for key in SOURCES}
    out={
      "metadata":{
        "baselineDate":"2025-09-25","latestTaskDate":"2026-05","taskSuccessDate":"2026-02",
        "wageVintages":{"2025":"BLS OEWS May 2024","2026":"BLS OEWS May 2025"},
        "model2026":"Illustrative calibration to GPT-5.5 aggregate GDPval 84.9% (Apr 2026); not measured per-occupation",
        "scoreMethod":"Logistic uplift from original best-of-seven per-occupation 2025 scores; small capped relative task-success adjustment from Anthropic Feb 2026 matched O*NET tasks; calibrated to 84.9% mean across 44 occupations. This is NOT a head-to-head GPT-5.5 result.",
        "taskMapping":"May 2026 Anthropic Economic Index -> exact O*NET 30.1 Task ID -> O*NET SOC -> original GDPval 2018 SOC. Broad SOC expands to exact detailed descendants only. Shared tasks split across matches. February task success joined by normalized exact task text and treated as illustrative evidence only.",
        "numbers":{"occupations":44,"sectors":9,"mayObservedTasks":len(may),"attributedTaskRows":task_rows,"febCoveredOccupations":sum(x["febSuccessPct"] is not None for x in occupation)},
        "sources":{k:{"url":v[1],"sha256":sha[k]} for k,v in SOURCES.items()},
        "benchmarkSource":"https://openai.com/index/introducing-gpt-5-5/",
        "limitations":["GDPval 2025 and Anthropic 2026 are different benchmarks and different models.","A task appearing in Claude usage is not proof the task is automated or has expert-quality results.","February Claude success is model-classified, not GDPval expert-graded.","May OEWS 2025 is newest annual wage vintage available by Oct 2026; no May OEWS 2026 estimates yet.","2026 colour is a scenario, not an occupational measurement or prediction of job losses.","Wage bill uses nationwide occupation employment and annual mean wage, not each sector's payroll."],
      },
      "occupations":occupation
    }
    path=HERE/"morph-data.json"
    path.write_text(json.dumps(out,ensure_ascii=False,separators=(",",":")),encoding="utf-8")
    print("Wrote",path,"bytes",path.stat().st_size)
if __name__=="__main__":
    main()

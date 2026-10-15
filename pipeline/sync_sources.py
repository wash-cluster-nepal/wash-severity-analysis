#!/usr/bin/env python3
"""Build and optionally write back the WASH Severity v16 PDNA90 publication.

Build mode (default):
  - read approved Google Sheet inputs server-side
  - calculate v16 P1/P2/Need Score
  - generate publication-safe JSON under data/

Write-back mode (--write-master):
  - repeat the same deterministic calculation
  - update the validated Analysis v16 PDNA90 output tab after QA has passed

No browser-side Google Sheet access is used.
"""
import argparse, datetime, json, math, os, pathlib, re
from google.auth import default
from googleapiclient.discovery import build

ROOT=pathlib.Path(__file__).resolve().parents[1]
MASTER_ID=os.environ["SEVERITY_MASTER_SHEET_ID"]
PDNA_ID=os.environ["PDNA_CORRECTIONS_SHEET_ID"]
MODEL_VERSION="WASH_SEVERITY_V16_PDNA90"

parser=argparse.ArgumentParser()
parser.add_argument("--write-master",action="store_true")
args=parser.parse_args()

scope="https://www.googleapis.com/auth/spreadsheets" if args.write_master else "https://www.googleapis.com/auth/spreadsheets.readonly"
creds,_=default(scopes=[scope])
svc=build("sheets","v4",credentials=creds,cache_discovery=False)

def values(spreadsheet_id,a1):
    return svc.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id,range=a1,valueRenderOption="UNFORMATTED_VALUE"
    ).execute().get("values",[])

def records(rows):
    if not rows:return []
    hdr=[str(x).strip() if x is not None else "" for x in rows[0]]
    return [
        {h:(row[i] if i<len(row) else None) for i,h in enumerate(hdr) if h}
        for row in rows[1:] if any(v not in (None,"") for v in row)
    ]

def num(v):
    if v in (None,""):return None
    try:return float(v)
    except:return None

def integer(v):
    x=num(v);return None if x is None else int(round(x))

def code(v,prefix):
    m=re.match(rf"^{prefix}(\d+)",str(v or "").strip(),re.I)
    return f"{prefix.upper()}{m.group(1)}" if m else None

def canon(name):
    return str(name or "").replace("Tarkeshwor Rural Municipality","Tarakeshwar Rural Municipality")

def component_class(x):
    if x is None:return "Unknown"
    if x>=4:return "Very High"
    if x>=3.25:return "High"
    if x>=2.5:return "Moderate"
    if x>=1.75:return "Low"
    return "Minimal"

def final_class(x):
    if x>3.5:return "Very High",5
    if x>=3:return "High",4
    if x>=2.25:return "Moderate",3
    if x>=1.75:return "Low",2
    return "Minimal",1

def affected_impact(affected,pop):
    a=affected or 0
    abs_score=1 if a<1000 else 2 if a<3000 else 3 if a<7500 else 4 if a<15000 else 5
    share=a/pop if pop else 0
    share_score=1 if share<.05 else 2 if share<.15 else 3 if share<.25 else 4 if share<.35 else 5
    return min(5,abs_score+.5*max(0,share_score-abs_score))

def beneficiary_impact(benef,pop):
    a=benef or 0
    abs_score=1 if a<=0 else 2 if a<1000 else 3 if a<3000 else 4 if a<10000 else 5
    share=min(1,a/pop) if pop else 0
    share_score=1 if share<.05 else 2 if share<.15 else 3 if share<.30 else 4 if share<.50 else 5
    return min(5,abs_score+.5*max(0,share_score-abs_score))

def service_score(v):
    s=str(v or "").lower()
    if "fully operational" in s:return 1
    if "partially operational" in s:return 2
    if "emergency" in s or "temporary service" in s:return 3
    if "temporarily closed" in s:return 4
    if "completely non-functional" in s:return 5
    return None

def drink_score(v):
    s=str(v or "").lower()
    if s=="yes":return 1
    if "after treatment" in s or "after boiling" in s:return 3
    if "unknown" in s:return 4
    if s=="no":return 5
    return None

def public_health_score(v):
    s=str(v or "").lower()
    if s.startswith("safe service"):return 1
    if s.startswith("safe with treatment"):return 2
    if s.startswith("restricted service"):return 3
    if s.startswith("unsafe service"):return 4
    if s.startswith("immediate public-health"):return 5
    return None

def mean(xs):
    xs=[x for x in xs if x is not None]
    return sum(xs)/len(xs) if xs else None

def first_coordinates(r):
    for kind,la,lo in (
        ("source","w1.sourceGps.lat","w1.sourceGps.lng"),
        ("reservoir","w1.reservoirGps.lat","w1.reservoirGps.lng"),
        ("treatment","w1.treatmentGps.lat","w1.treatmentGps.lng"),
    ):
        lat,lon=num(r.get(la)),num(r.get(lo))
        if lat is not None and lon is not None and 26<lat<30 and 80<lon<90:
            return lat,lon,kind
    return None,None,None

# Baseline cohort/context is preserved from the current publication file.
existing=json.loads((ROOT/"data/municipality_profiles.json").read_text(encoding="utf-8"))
by_pcode={p["adm3_pcode"]:dict(p) for p in existing}
by_name={p["municipality"]:p["adm3_pcode"] for p in existing}

municipal=records(values(MASTER_ID,"'Municipal Database'!A1:AZ100"))
affected=records(values(MASTER_ID,"'Flash Appeal Affected Pop'!A1:J100"))
analysis=records(values(MASTER_ID,"'Analysis v16 PDNA90'!A1:R100"))
pdna=records(values(PDNA_ID,"'corrections'!A1:GV200"))

if len(existing)!=17:raise SystemExit(f"Expected 17 publication profiles, found {len(existing)}")
if len([r for r in pdna if r.get("reference_id")])!=90:raise SystemExit("PDNA corrections source must contain exactly 90 records")

m_by={str(r.get("ADM3_PCODE") or ""):r for r in municipal if r.get("ADM3_PCODE")}
a_by={str(r.get("adm3_pcode") or ""):r for r in affected if r.get("adm3_pcode")}
p3_by={str(r.get("ADM3_PCODE") or ""):num(r.get("P3")) for r in analysis if r.get("ADM3_PCODE")}

groups={}
systems=[]
for r in pdna:
    if not r.get("reference_id"):continue
    municipality=canon(r.get("municipality"))
    pcode=by_name.get(municipality)
    if not pcode:raise SystemExit(f"PDNA municipality not in analytical cohort: {municipality}")
    base=by_pcode[pcode]
    dg,sg,act=code(r.get("w5.damageGrade"),"D"),code(r.get("w5.siteSafety"),"S"),code(r.get("w6.primary"),"R")
    access=service_score(r.get("w2.serviceStatus"))
    ds,ph=drink_score(r.get("w4.drinkable")),public_health_score(r.get("w5.serviceSafety"))
    wq=max([x for x in (ds,ph) if x is not None],default=None)
    lat,lon,coord_type=first_coordinates(r)
    item={
        "reference_id":str(r.get("reference_id")),
        "asset_id":r.get("w1.assetId"),
        "scheme_name":r.get("w1.schemeName"),
        "district":base["district"],"adm2_pcode":base["adm2_pcode"],
        "municipality":municipality,"adm3_pcode":pcode,"ward":r.get("ward"),
        "assessment_date":r.get("w1.assessmentDate") or r.get("survey_date"),
        "latitude":lat,"longitude":lon,"coordinate_type":coord_type,
        "beneficiary_population":num(r.get("w2.population")),
        "population_without_adequate_service":num(r.get("w2.populationWithout")),
        "service_status":r.get("w2.serviceStatus"),
        "drinking_water_safety":r.get("w4.drinkable"),
        "damage_grade":dg,"damage_grade_label":r.get("w5.damageGrade"),
        "site_safety_grade":sg,"site_safety_label":r.get("w5.siteSafety"),
        "service_public_health_safety":r.get("w5.serviceSafety"),
        "primary_intervention":r.get("w6.primary"),
        "recovery_priority":r.get("w8.priority"),
        "physical_damage_cost_npr":num(r.get("w9.physicalDamage")),
        "reconstruction_cost_npr":num(r.get("w9.reconstructionCost")),
        "total_cost_npr":num(r.get("w9.totalCost")),
        "source":"PDNA corrections sheet, 9 Oct 2026"
    }
    systems.append(item)
    g=groups.setdefault(pcode,{"records":[],"benef":0,"damage":[],"service":[],"wq":[],"recon":0,"physical":0,"total":0,
                               "damage_counts":{},"safety_counts":{},"action_counts":{},"priority_counts":{}})
    g["records"].append(item);g["benef"]+=item["beneficiary_population"] or 0
    if dg:
        g["damage"].append(int(dg[1:]));g["damage_counts"][dg]=g["damage_counts"].get(dg,0)+1
    if sg:g["safety_counts"][sg]=g["safety_counts"].get(sg,0)+1
    if act:g["action_counts"][act]=g["action_counts"].get(act,0)+1
    pm=re.search(r"Priority\s*(\d)",str(item["recovery_priority"] or ""),re.I)
    if pm:
        k="P"+pm.group(1);g["priority_counts"][k]=g["priority_counts"].get(k,0)+1
    if access is not None:g["service"].append(access)
    if wq is not None:g["wq"].append(wq)
    g["recon"]+=item["reconstruction_cost_npr"] or 0
    g["physical"]+=item["physical_damage_cost_npr"] or 0
    g["total"]+=item["total_cost_npr"] or 0

profiles=[]
for old in existing:
    p=dict(old);pc=p["adm3_pcode"]
    mr,ar=m_by.get(pc,{}),a_by.get(pc,{})
    if mr.get("Population 2026") not in (None,""):p["population_2026"]=integer(mr["Population 2026"])
    if ar.get("Estimated affected population") not in (None,""):p["affected_population"]=integer(ar["Estimated affected population"])
    if p.get("population_2026"):p["affected_share"]=p["affected_population"]/p["population_2026"]
    if pc in p3_by and p3_by[pc] is not None:p["p3"]=p3_by[pc]
    p["p3_class"]=component_class(p["p3"])
    ai=affected_impact(p.get("affected_population"),p.get("population_2026"))
    g=groups.get(pc)
    if g:
        damage=mean(g["damage"])
        bi=beneficiary_impact(g["benef"],p["population_2026"])
        wss=min(5,bi+.5*max(0,(damage if damage is not None else bi)-bi))
        p1=.4*ai+.6*wss
        access,wq=mean(g["service"]),mean(g["wq"])
        observed=mean([access,wq])
        coverage=min(1,g["benef"]/max(1,p["affected_population"]))
        p2=2.5+coverage*max(0,observed-2.5)
        p.update({
            "damaged_wss_beneficiaries":g["benef"],"wss_beneficiary_share":min(1,g["benef"]/p["population_2026"]),
            "p1":p1,"p1_class":component_class(p1),"p2":p2,"p2_class":component_class(p2),
            "p2_direct":observed,"p2_observed":observed,"p2_final":p2,"p2_provisional":False,
            "p2_evidence_coverage_proxy":coverage,"p2_coverage_adjustment":coverage,
            "physical_damage_score":damage,"water_access_score":access,"water_access_service_score":access,
            "water_quality_score":wq,"water_quality_safety_score":wq,
            "evidence_strength":"Limited PDNA data" if len(g["records"])==1 else "Direct PDNA data",
            "pdna_assessment_records":len(g["records"]),"pdna_reconstruction_cost_npr":g["recon"],
            "pdna_physical_damage_cost_npr":g["physical"]
        })
    else:
        p.update({
            "damaged_wss_beneficiaries":0,"wss_beneficiary_share":0,
            "p1":ai,"p1_class":component_class(ai),"p2":2.5,"p2_class":component_class(2.5),
            "p2_direct":None,"p2_observed":None,"p2_final":2.5,"p2_provisional":True,
            "p2_evidence_coverage_proxy":None,"p2_coverage_adjustment":None,
            "physical_damage_score":None,"water_access_score":None,"water_access_service_score":None,
            "water_quality_score":None,"water_quality_safety_score":None,"evidence_strength":"No current PDNA data",
            "pdna_assessment_records":0,"pdna_reconstruction_cost_npr":0,"pdna_physical_damage_cost_npr":0
        })
    p.pop("govt_wss_damage_cost_npr",None);p.pop("govt_wss_damage_score",None)
    p["need_score"]=.5*p["p1"]+.3*p["p2"]+.2*p["p3"]
    p["priority_class"],p["priority_level"]=final_class(p["need_score"])
    p["absolute_class"]=p["priority_class"];p["model_version"]=MODEL_VERSION
    profiles.append(p)

profiles.sort(key=lambda p:(-p["need_score"],p["municipality"]))
for i,p in enumerate(profiles,1):p["priority_rank"]=i

summary=[]
for p in profiles:
    g=groups.get(p["adm3_pcode"])
    summary.append({
        "district":p["district"],"adm2_pcode":p["adm2_pcode"],"municipality":p["municipality"],"adm3_pcode":p["adm3_pcode"],
        "assessment_records":len(g["records"]) if g else 0,"unique_assets":len(g["records"]) if g else 0,
        "beneficiary_population_sum_not_deduped":g["benef"] if g else 0,
        "physical_damage_score":mean(g["damage"]) if g else None,
        "water_access_service_score":mean(g["service"]) if g else None,
        "water_quality_safety_score":mean(g["wq"]) if g else None,
        "p2_observed":p["p2_observed"],"p2_coverage_adjustment":p["p2_coverage_adjustment"],
        "reconstruction_cost_npr_sum":g["recon"] if g else 0,
        "physical_damage_cost_npr_sum":g["physical"] if g else 0,"total_cost_npr_sum":g["total"] if g else 0,
        "damage_grade_counts":g["damage_counts"] if g else {},"site_safety_counts":g["safety_counts"] if g else {},
        "primary_action_counts":g["action_counts"] if g else {},"priority_counts":g["priority_counts"] if g else {},
        "p1":p["p1"],"p2":p["p2"],"p3":p["p3"],"need_score":p["need_score"],
        "severity_class":p["priority_class"],"rank":p["priority_rank"]
    })

if args.write_master:
    header=["Rank","District","Municipality","ADM3_PCODE","PDNA schemes","Beneficiary pop (not deduped)",
            "Physical damage score","Water access/service score","Water quality/safety score","P2 observed",
            "P2 coverage proxy","P1","P2","P3","Need Score","Severity Class","Evidence Strength",
            "Reconstruction cost NPR (GR)"]
    s_by={x["adm3_pcode"]:x for x in summary}
    out=[header]
    for p in profiles:
        s=s_by[p["adm3_pcode"]]
        out.append([p["priority_rank"],p["district"],p["municipality"],p["adm3_pcode"],s["assessment_records"],
                    s["beneficiary_population_sum_not_deduped"],s["physical_damage_score"],s["water_access_service_score"],
                    s["water_quality_safety_score"],s["p2_observed"],s["p2_coverage_adjustment"],p["p1"],p["p2"],p["p3"],
                    p["need_score"],p["priority_class"],p["evidence_strength"],s["reconstruction_cost_npr_sum"]])
    svc.spreadsheets().values().update(
        spreadsheetId=MASTER_ID,range="'Analysis v16 PDNA90'!A1:R18",
        valueInputOption="RAW",body={"values":out}
    ).execute()
    print("Validated v16 results written back to Analysis v16 PDNA90.")
else:
    (ROOT/"data/municipality_profiles.json").write_text(json.dumps(profiles,separators=(",",":"))+"\n",encoding="utf-8")
    (ROOT/"data/pdna_municipality_summary.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    (ROOT/"data/pdna_water_systems.json").write_text(json.dumps(systems,separators=(",",":"))+"\n",encoding="utf-8")
    meta=json.loads((ROOT/"data/metadata.json").read_text(encoding="utf-8"))
    meta.update({"model_version":MODEL_VERSION,"generated_date":datetime.datetime.now(datetime.timezone.utc).date().isoformat(),
                 "publication_mode":"manual_validated_sync","pdna_version":"90-scheme corrections dataset, 9 Oct 2026",
                 "pdna_records":90,"pdna_municipalities":len(groups)})
    (ROOT/"data/metadata.json").write_text(json.dumps(meta,indent=2)+"\n",encoding="utf-8")
    print(f"Prepared {len(profiles)} severity profiles, {len(summary)} municipality summaries and {len(systems)} PDNA schemes.")

#!/usr/bin/env python3
import json, os, pathlib, datetime, math
from google.auth import default
from googleapiclient.discovery import build

ROOT=pathlib.Path(__file__).resolve().parents[1]
MASTER_ID=os.environ["SEVERITY_MASTER_SHEET_ID"]
PDNA_ID=os.environ["PDNA_INTEGRATED_SHEET_ID"]

creds,_=default(scopes=["https://www.googleapis.com/auth/spreadsheets.readonly"])
svc=build("sheets","v4",credentials=creds,cache_discovery=False)

def values(spreadsheet_id, a1):
    r=svc.spreadsheets().values().get(
        spreadsheetId=spreadsheet_id, range=a1,
        valueRenderOption="UNFORMATTED_VALUE"
    ).execute()
    return r.get("values",[])

def records(rows):
    if not rows: return []
    headers=[str(x).strip() if x is not None else "" for x in rows[0]]
    out=[]
    for row in rows[1:]:
        rec={}
        for i,h in enumerate(headers):
            if h: rec[h]=row[i] if i<len(row) else None
        if any(v not in (None,"") for v in rec.values()): out.append(rec)
    return out

def num(v):
    if v in (None,""): return None
    return float(v)

def integer(v):
    if v in (None,""): return None
    return int(round(float(v)))

def classify_final(x):
    if x>3.5: return "Very High",5
    if x>=3.0: return "High",4
    if x>=2.25: return "Moderate",3
    if x>=1.75: return "Low",2
    return "Minimal",1

def classify_component(x):
    if x is None: return None
    if x>=4.0: return "Very High"
    if x>=3.25: return "High"
    if x>=2.5: return "Moderate"
    if x>=1.75: return "Low"
    return "Minimal"

analysis=records(values(MASTER_ID,"'Analysis v15 Locked'!A1:L100"))
municipal=records(values(MASTER_ID,"'Municipal Database'!A1:AZ100"))
affected=records(values(MASTER_ID,"'Flash Appeal Affected Pop'!A1:J100"))
pdna=records(values(PDNA_ID,"'03_Municipality_Summary'!A1:AB100"))

analysis=[r for r in analysis if r.get("ADM3_PCODE")]
municipal=[r for r in municipal if r.get("ADM3_PCODE")]
affected=[r for r in affected if r.get("adm3_pcode")]
pdna=[r for r in pdna if r.get("ADM3_PCODE")]

if len(analysis)!=17:
    raise SystemExit(f"Expected 17 rows in Analysis v15 Locked, found {len(analysis)}")
if len({r["ADM3_PCODE"] for r in analysis})!=17:
    raise SystemExit("Analysis v15 Locked contains duplicate ADM3_PCODE values")

profiles=json.loads((ROOT/"data/municipality_profiles.json").read_text())
existing={p["adm3_pcode"]:p for p in profiles}
m_by={r["ADM3_PCODE"]:r for r in municipal}
a_by={r["adm3_pcode"]:r for r in affected}

new=[]
for ar in analysis:
    pc=str(ar["ADM3_PCODE"]).strip()
    if pc not in existing: raise SystemExit(f"Analysis PCODE {pc} not present in publication profiles")
    p=dict(existing[pc])
    mr=m_by.get(pc,{})
    fr=a_by.get(pc,{})
    p.update({
        "district": ar.get("District"),
        "municipality": ar.get("Municipality"),
        "priority_rank": integer(ar.get("Rank")),
        "p1": num(ar.get("P1")),
        "p2_direct": num(ar.get("Direct P2")),
        "p2_observed": num(ar.get("Direct P2")),
        "p2_evidence_coverage_proxy": num(ar.get("P2 coverage proxy")),
        "p2_coverage_adjustment": num(ar.get("P2 coverage proxy")),
        "p2": num(ar.get("Final P2")),
        "p2_final": num(ar.get("Final P2")),
        "p2_provisional": ar.get("Direct P2") in (None,""),
        "p3": num(ar.get("P3")),
        "need_score": num(ar.get("Need Score")),
        "priority_class": ar.get("Severity Class") or ar.get("Absolute Severity Class"),
        "absolute_class": ar.get("Severity Class") or ar.get("Absolute Severity Class"),
        "evidence_strength": ar.get("Evidence Strength"),
        "model_version":"WASH_SEVERITY_V15_LOCKED"
    })
    if mr:
        if mr.get("Population 2026") not in (None,""): p["population_2026"]=integer(mr.get("Population 2026"))
        if mr.get("Children 0-17 in earlier hard-hit subset") not in (None,""): p["children_hard_hit_wards_0_17"]=integer(mr.get("Children 0-17 in earlier hard-hit subset"))
        if mr.get("HH in earlier hard-hit subset") not in (None,""): p["households_hard_hit_area"]=integer(mr.get("HH in earlier hard-hit subset"))
    if fr:
        if fr.get("Estimated affected population") not in (None,""): p["affected_population"]=integer(fr.get("Estimated affected population"))
        pop=p.get("population_2026")
        if pop and p.get("affected_population") is not None:
            p["affected_share"]=p["affected_population"]/pop
    p["p1_class"]=classify_component(p.get("p1"))
    p["p2_class"]=classify_component(p.get("p2"))
    p["p3_class"]=classify_component(p.get("p3"))
    cls,level=classify_final(p["need_score"])
    if p["priority_class"]!=cls:
        raise SystemExit(f"{pc}: Sheet severity class {p['priority_class']} does not match Need Score {p['need_score']} ({cls})")
    p["priority_level"]=level
    new.append(p)

new.sort(key=lambda p:p["priority_rank"])
if [p["priority_rank"] for p in new]!=list(range(1,18)):
    raise SystemExit("Ranks must be exactly 1..17")

# Publication-safe PDNA aggregate. No scheme names, coordinates, contacts, or free text.
pdna_out=[]
for r in pdna:
    pdna_out.append({
        "district":r.get("District"),
        "adm2_pcode":r.get("ADM2_PCODE"),
        "municipality":r.get("Municipality"),
        "adm3_pcode":r.get("ADM3_PCODE"),
        "assessment_records":integer(r.get("DDA_records")),
        "unique_assets":integer(r.get("DDA_unique_assets")),
        "beneficiary_population_sum_not_deduped":num(r.get("DDA_beneficiary_population_sum_NOT_DEDUPED")),
        "population_without_service_sum_not_deduped":num(r.get("DDA_population_without_service_sum_NOT_DEDUPED")),
        "supply_percent_median":num(r.get("DDA_supply_percent_median")),
        "nonfunctional_or_closed_assets":integer(r.get("DDA_nonfunctional_or_closed_assets")),
        "d4_d5_assets":integer(r.get("DDA_D4_D5_assets")),
        "d4_d5_share":num(r.get("DDA_D4_D5_share")),
        "unsafe_or_immediate_health_action_assets":integer(r.get("DDA_unsafe_or_immediate_health_action_assets")),
        "water_not_safe_or_unknown_assets":integer(r.get("DDA_water_not_safe_or_unknown_assets")),
        "priority_1_2_assets":integer(r.get("DDA_priority_1_2_assets")),
        "physical_damage_cost_npr_sum":num(r.get("DDA_physical_damage_cost_npr_sum")),
        "total_recovery_need_npr_sum":num(r.get("DDA_total_recovery_need_npr_sum")),
        "gps_coverage_pct":num(r.get("DDA_GPS_coverage_pct")),
        "quantitative_service_data_coverage_pct":num(r.get("DDA_quant_service_data_coverage_pct"))
    })

(ROOT/"data/municipality_profiles.json").write_text(json.dumps(new,separators=(",",":"))+"\n",encoding="utf-8")
(ROOT/"data/pdna_municipality_summary.json").write_text(json.dumps(pdna_out,indent=2)+"\n",encoding="utf-8")

meta=json.loads((ROOT/"data/metadata.json").read_text())
meta["generated_date"]=datetime.datetime.now(datetime.timezone.utc).date().isoformat()
meta["publication_mode"]="manual_validated_sync"
meta["pdna_publication"]="Municipality-level aggregate only; exact scheme coordinates remain non-public."
(ROOT/"data/metadata.json").write_text(json.dumps(meta,indent=2)+"\n",encoding="utf-8")

print(f"Prepared {len(new)} severity profiles and {len(pdna_out)} municipality-level PDNA summary rows.")

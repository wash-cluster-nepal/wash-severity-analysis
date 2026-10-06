#!/usr/bin/env python3
import json, math, pathlib, re, sys

ROOT=pathlib.Path(__file__).resolve().parents[1]
errors=[]
warnings=[]

def load(path):
    try:
        return json.loads((ROOT/path).read_text(encoding="utf-8"))
    except Exception as e:
        errors.append(f"{path}: invalid JSON: {e}")
        return None

model=load("config/model.json")
profiles=load("data/municipality_profiles.json")
adm3=load("data/adm3_affected.geojson")
flood=load("data/flood_extent.geojson")
roads=load("data/roads_nepal_response.geojson")
holding=load("data/holding_centres.geojson")
metadata=load("data/metadata.json")

if isinstance(profiles,list):
    pcodes=[x.get("adm3_pcode") for x in profiles]
    ranks=[x.get("priority_rank") for x in profiles]
    if len(profiles)!=(metadata or {}).get("affected_municipalities"):
        errors.append("municipality profile count does not match metadata")
    if len(pcodes)!=len(set(pcodes)):
        errors.append("duplicate municipality PCODEs")
    if sorted(ranks)!=list(range(1,len(profiles)+1)):
        errors.append("priority ranks are not unique/continuous")
    w=(model or {}).get("officialWeights",{})
    for p in profiles:
        vals=[p.get("p1"),p.get("p2"),p.get("p3")]
        if all(v is not None for v in vals):
            calc=vals[0]*w.get("p1",0)+vals[1]*w.get("p2",0)+vals[2]*w.get("p3",0)
            if not math.isclose(calc,p.get("need_score"),rel_tol=0,abs_tol=1e-8):
                errors.append(f"{p.get('municipality')}: Need Score formula mismatch")

if isinstance(adm3,dict) and isinstance(profiles,list):
    gpcodes={f.get("properties",{}).get("adm3_pcode") for f in adm3.get("features",[])}
    ppcodes={p.get("adm3_pcode") for p in profiles}
    if gpcodes!=ppcodes:
        errors.append(f"ADM3/profile PCODE mismatch: missing geometry={sorted(ppcodes-gpcodes)}, extra geometry={sorted(gpcodes-ppcodes)}")

def check_geom(fc,allowed,name):
    if not isinstance(fc,dict):
        return
    bad=[f.get("geometry",{}).get("type") for f in fc.get("features",[]) if f.get("geometry",{}).get("type") not in allowed]
    if bad:
        errors.append(f"{name}: unexpected geometry types {sorted(set(bad))}")

check_geom(flood,{"Polygon","MultiPolygon"},"flood")
check_geom(roads,{"LineString","MultiLineString"},"roads")
check_geom(holding,{"Point","MultiPoint"},"holding centres")

if isinstance(roads,dict):
    codes={f.get("properties",{}).get("CURR_PHYS") for f in roads.get("features",[])}
    unexpected=[c for c in codes if c is not None and float(c) not in {1.0,2.0,3.0,4.0}]
    if unexpected:
        warnings.append(f"roads: unexpected CURR_PHYS codes {unexpected}")

if isinstance(holding,dict):
    prohibited={"focal point name and contact","email","phone","telephone","enumerator name","submitted_by"}
    keys=set()
    for f in holding.get("features",[]):
        keys.update(str(k).strip().lower() for k in f.get("properties",{}))
    leaked=sorted(keys & prohibited)
    if leaked:
        errors.append(f"holding centres expose prohibited contact fields: {leaked}")

if isinstance(model,dict):
    ranks=model.get("cohortRankClasses",[])
    if any("minScore" not in r for r in ranks):
        errors.append("final priority configuration is missing Need Score guardrails")

html=(ROOT/"index.html").read_text(encoding="utf-8")
ids=re.findall(r'id="([^"]+)"',html)
dups=sorted({x for x in ids if ids.count(x)>1})
if dups:
    errors.append(f"duplicate HTML ids: {dups}")
for forbidden in ["GLOBAL WASH CLUSTER","Data status","Evidence confidence","Verification priority","percentile"]:
    if forbidden.lower() in html.lower():
        errors.append(f"forbidden/outdated visible term remains in index.html: {forbidden}")

print("QA checks")
for w in warnings:
    print("WARNING:",w)
if errors:
    for e in errors:
        print("ERROR:",e)
    sys.exit(1)
print("PASS: all automated QA checks passed")

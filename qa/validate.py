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

def text(path):
    try:
        return (ROOT/path).read_text(encoding="utf-8")
    except Exception as e:
        errors.append(f"{path}: cannot read: {e}")
        return ""

def fail_if(condition,message):
    if condition:
        errors.append(message)

model=load("config/model.json")
profiles=load("data/municipality_profiles.json")
adm3=load("data/adm3_affected.geojson")
adm4=load("data/adm4_available.geojson")
flood=load("data/flood_extent.geojson")
roads=load("data/roads_nepal_response.geojson")
holding=load("data/holding_centres.geojson")
metadata=load("data/metadata.json")
sources=load("data/source_registry.json")
source_cfg=load("config/data-sources.json")

EXPECTED_VERSION="WASH_SEVERITY_V15_LOCKED"
EXPECTED_WEIGHTS={"p1":0.5,"p2":0.3,"p3":0.2}
EXPECTED_FINAL=[
    ("Very High",5,3.5000000001),
    ("High",4,3.0),
    ("Moderate",3,2.25),
    ("Low",2,1.75),
    ("Minimal",1,0.0),
]
EXPECTED_COMPONENT=[
    ("Very High",5,4.0),
    ("High",4,3.25),
    ("Moderate",3,2.5),
    ("Low",2,1.75),
    ("Minimal",1,0.0),
]

def classify(score,bands):
    for c,l,m in bands:
        if score>=m:
            return c,l
    return "Minimal",1

# Model and metadata alignment.
if isinstance(model,dict):
    fail_if(model.get("modelVersion")!=EXPECTED_VERSION,"model version is not locked v15")
    w=model.get("officialWeights",{})
    for k,v in EXPECTED_WEIGHTS.items():
        fail_if(not math.isclose(w.get(k,-1),v,abs_tol=1e-12),f"official weight {k} is not {v}")
    fail_if(not math.isclose(sum(w.values()),1.0,abs_tol=1e-12),"official weights do not sum to 1")

    for k,v in EXPECTED_WEIGHTS.items():
        pw=(model.get("pillars",{}).get(k,{}) or {}).get("weight")
        fail_if(not math.isclose(pw if pw is not None else -1,v,abs_tol=1e-12),f"pillar {k} weight does not match officialWeights")

    abs_classes=model.get("absoluteClasses",[])
    fail_if(len(abs_classes)!=5,"absoluteClasses must contain five final severity bands")
    for got,(c,l,m) in zip(abs_classes,EXPECTED_FINAL):
        fail_if(got.get("class")!=c or got.get("level")!=l or not math.isclose(got.get("min",-1),m,abs_tol=1e-10),
                f"final severity band mismatch for {c}")

    comp=model.get("componentClasses",[])
    fail_if(len(comp)!=5,"componentClasses must contain five component bands")
    for got,(c,l,m) in zip(comp,EXPECTED_COMPONENT):
        fail_if(got.get("class")!=c or got.get("level")!=l or not math.isclose(got.get("min",-1),m,abs_tol=1e-10),
                f"component severity band mismatch for {c}")

    fail_if("cohortRankClasses" in model,"legacy cohortRankClasses must not remain in locked v15 model")

if isinstance(metadata,dict):
    fail_if(metadata.get("model_version")!=EXPECTED_VERSION,"metadata model_version differs from model")
    fail_if(metadata.get("publication_mode")!="validated_static_snapshot","publication mode must be validated_static_snapshot")
    fail_if(metadata.get("five_w_status")!="not_ingested_in_v1","5W status unexpectedly changed")
    joined=" ".join(metadata.get("notes",[]))
    for phrase in ["P1 50%, P2 30%, P3 20%","Very High >3.5","Moderate 2.25","Low 1.75"]:
        fail_if(phrase not in joined,f"metadata notes missing current model statement: {phrase}")

# Profile arithmetic, classes, P2 logic and ranking.
if isinstance(profiles,list):
    fail_if(len(profiles)!=(metadata or {}).get("affected_municipalities"),"municipality profile count does not match metadata")
    pcodes=[x.get("adm3_pcode") for x in profiles]
    ranks=[x.get("priority_rank") for x in profiles]
    fail_if(any(not x for x in pcodes),"blank municipality PCODE")
    fail_if(len(pcodes)!=len(set(pcodes)),"duplicate municipality PCODEs")
    fail_if(sorted(ranks)!=list(range(1,len(profiles)+1)),"priority ranks are not unique/continuous")

    expected_order=sorted(profiles,key=lambda p:(-p.get("need_score",0),p.get("municipality","")))
    for i,p in enumerate(expected_order,1):
        fail_if(p.get("priority_rank")!=i,f"{p.get('municipality')}: priority rank does not match Need Score order")

    w=(model or {}).get("officialWeights",{})
    for p in profiles:
        name=p.get("municipality")
        fail_if(p.get("model_version")!=EXPECTED_VERSION,f"{name}: profile model version mismatch")
        vals=[p.get("p1"),p.get("p2"),p.get("p3")]
        if all(v is not None for v in vals):
            calc=vals[0]*w.get("p1",0)+vals[1]*w.get("p2",0)+vals[2]*w.get("p3",0)
            fail_if(not math.isclose(calc,p.get("need_score"),rel_tol=0,abs_tol=1e-8),f"{name}: Need Score formula mismatch")

        final_class,final_level=classify(p.get("need_score"),EXPECTED_FINAL)
        fail_if(p.get("priority_class")!=final_class,f"{name}: published severity class mismatch")
        fail_if(p.get("absolute_class")!=final_class,f"{name}: absolute_class differs from final severity")
        fail_if(p.get("priority_level")!=final_level,f"{name}: priority_level mismatch")

        for key in ("p1","p2","p3"):
            score=p.get(key)
            if score is not None:
                expected,_=classify(score,EXPECTED_COMPONENT)
                fail_if(p.get(f"{key}_class")!=expected,f"{name}: {key}_class inconsistent with component thresholds")

        fail_if(p.get("p2_final") is not None and not math.isclose(p.get("p2"),p.get("p2_final"),abs_tol=1e-8),
                f"{name}: p2 and p2_final differ")
        if p.get("p2_provisional"):
            fail_if(not math.isclose(p.get("p2"),2.5,abs_tol=1e-8),f"{name}: provisional P2 must equal 2.5")
            fail_if(p.get("evidence_strength")!="No current PDNA data",f"{name}: provisional P2 evidence label mismatch")
        elif p.get("p2_observed") is not None and p.get("p2_coverage_adjustment") is not None:
            expected=2.5+p.get("p2_coverage_adjustment")*max(0,p.get("p2_observed")-2.5)
            fail_if(not math.isclose(expected,p.get("p2"),abs_tol=1e-8),f"{name}: P2 coverage-adjustment formula mismatch")
            fail_if(not (0<=p.get("p2_coverage_adjustment")<=1),f"{name}: P2 coverage adjustment outside 0–1")

# Spatial integrity and publication-safe attributes.
if isinstance(adm3,dict) and isinstance(profiles,list):
    gpcodes=[f.get("properties",{}).get("adm3_pcode") for f in adm3.get("features",[])]
    ppcodes=[p.get("adm3_pcode") for p in profiles]
    fail_if(len(gpcodes)!=len(set(gpcodes)),"duplicate ADM3 geometry PCODEs")
    fail_if(set(gpcodes)!=set(ppcodes),f"ADM3/profile PCODE mismatch: missing geometry={sorted(set(ppcodes)-set(gpcodes))}, extra geometry={sorted(set(gpcodes)-set(ppcodes))}")

def check_geom(fc,allowed,name):
    if not isinstance(fc,dict):
        return
    bad=[f.get("geometry",{}).get("type") for f in fc.get("features",[]) if f.get("geometry",{}).get("type") not in allowed]
    if bad:
        errors.append(f"{name}: unexpected geometry types {sorted(set(bad))}")

check_geom(adm3,{"Polygon","MultiPolygon"},"ADM3")
check_geom(adm4,{"Polygon","MultiPolygon"},"ADM4")
check_geom(flood,{"Polygon","MultiPolygon"},"flood")
check_geom(roads,{"LineString","MultiLineString"},"roads")
check_geom(holding,{"Point","MultiPoint"},"holding centres")

if isinstance(roads,dict):
    codes={f.get("properties",{}).get("CURR_PHYS") for f in roads.get("features",[])}
    unexpected=[c for c in codes if c is not None and float(c) not in {1.0,2.0,3.0,4.0}]
    if unexpected:
        warnings.append(f"roads: unexpected CURR_PHYS codes {unexpected}")

if isinstance(holding,dict):
    prohibited={"focal point name and contact","email","phone","telephone","enumerator name","submitted_by","focal_point","contact"}
    keys=set()
    for f in holding.get("features",[]):
        keys.update(str(k).strip().lower() for k in f.get("properties",{}))
    leaked=sorted(keys & prohibited)
    fail_if(bool(leaked),f"holding centres expose prohibited contact fields: {leaked}")

# Source registry and source-governance configuration.
if isinstance(sources,list):
    fail_if([s.get("source_id") for s in sources]!=["A01","A02","A03","A04","A05","A06"],"analytical source registry IDs/order changed unexpectedly")
if isinstance(source_cfg,dict):
    pg=source_cfg.get("pdna_point_gis",{})
    fail_if(pg.get("public") is not False,"PDNA point GIS source must remain non-public")
    fail_if(pg.get("contains_exact_coordinates") is not True,"PDNA point GIS coordinate sensitivity flag missing")
    fail_if("Do not publish exact point data automatically" not in pg.get("publication_rule",""),"PDNA point publication rule weakened")
    fail_if(source_cfg.get("five_w",{}).get("status")!="not_configured","5W source unexpectedly configured without model update")

# Frontend / documentation regressions.
html=text("index.html")
infra=text("infrastructure.html")
readme=text("README.md")
pipeline=text("pipeline/README.md")
smoke=text("qa/smoke.mjs")

ids=re.findall(r'id="([^"]+)"',html)
dups=sorted({x for x in ids if ids.count(x)>1})
fail_if(bool(dups),f"duplicate HTML ids: {dups}")

for forbidden in ["GLOBAL WASH CLUSTER","Data status","Evidence confidence","Verification priority","percentile"]:
    fail_if(forbidden.lower() in html.lower(),f"forbidden/outdated visible term remains in index.html: {forbidden}")

for stale in ["45%","35%","4.20–5.00","3.40–<4.20","2.60–<3.40","1.80–<2.60"]:
    fail_if(stale in html,f"stale model text remains in index.html: {stale}")

fail_if("cohortRankClasses" in html,"frontend still references legacy cohortRankClasses")
fail_if("componentClasses" not in html,"frontend does not consume component class configuration")
for route in ["index.html#map","index.html#analysis","index.html#about"]:
    fail_if(route not in infra,f"Water Systems navigation missing deep link {route}")

for unsafe in ["docs.google.com/spreadsheets","gviz/tq","LIVE_SHEET_ID","LIVE_CSV_URL","loadLiveSheet()"]:
    fail_if(unsafe in infra,f"public Water Systems page still contains direct Sheet access: {unsafe}")
for stale in ["PDNA / DDA","DDA assessments","Connecting to Cluster Google Sheet"]:
    fail_if(stale in infra,f"stale public Water Systems terminology remains: {stale}")
fail_if("approved export" not in infra.lower(),"Water Systems page does not state approved-export requirement")

for doc in [readme,pipeline]:
    for stale in ["P1 50% + P2 35% + P3 15%","Very High ≥4.00; High 3.25"]:
        fail_if(stale in doc,f"stale final model statement remains in documentation: {stale}")

for phrase in ["50%","30%","20%","Current WASH conditions","Data sources"]:
    fail_if(phrase not in smoke,f"browser smoke test missing current model assertion: {phrase}")
for stale in ["45%","35%"]:
    fail_if(stale in smoke,f"browser smoke test still expects stale weight: {stale}")

print("QA checks")
for w in warnings:
    print("WARNING:",w)
if errors:
    for e in errors:
        print("ERROR:",e)
    sys.exit(1)
print("PASS: all automated QA checks passed")

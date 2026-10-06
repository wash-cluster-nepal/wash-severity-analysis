# Nepal Flood WASH Severity Analysis

Open-source, source-driven web GIS for municipality-level WASH severity analysis following the 2026 Nepal floods.

## Current v1

The public GitHub Pages application includes:

- municipality-level WASH priority for 17 affected municipalities;
- component and indicator map layers;
- municipality profiles with key severity drivers;
- user-adjustable scenario weights that do not overwrite the default analysis;
- flood extent polygons;
- IOM holding-centre points with selected WASH fields;
- road/access status lines;
- available ward boundaries;
- sortable/filterable municipality analysis table;
- CSV export; and
- PNG map export, including A4 landscape output with legend and attribution.

## Default analytical model

- Flood impact & WASH service disruption: **45%**
- Current WASH conditions: **35%** (provisional)
- Pre-existing vulnerability & aggravating factors: **20%**

The final priority is interpreted across the 17 affected municipalities while applying minimum Need Score guardrails. The continuous Need Score and absolute class are retained separately.

## Source architecture

Current publication flow:

- analytical source: native Google Sheet imported from the latest analytical workbook;
- spatial sources: supplied GIS files;
- public outputs: JSON / GeoJSON under `data/`;
- frontend: static HTML/CSS/JavaScript + MapLibre;
- hosting: GitHub Pages.

### Important current limitation

The v1 site is **not yet automatically synchronised** from the Google Sheet. The public data files are currently a validated static snapshot. The next engineering step is to implement and test the automated source-validation-build-publish workflow.

## Data governance

The public site has no authentication. Only publication-safe fields should be included in public JSON/GeoJSON outputs. The IOM holding-centre layer currently includes selected demographic and WASH fields only; direct contact fields were excluded.

## Phase 2

The operational 5W Google Sheet will be added later as a separate response-monitoring module.

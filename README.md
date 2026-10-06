# Nepal Flood WASH Severity Analysis

Institutional repository for the Nepal WASH Cluster's 2026 flood severity and infrastructure analysis.

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

## Institutional source architecture

Current publication flow:

- operational source files are maintained in the WASH Cluster Google Drive;
- the validated severity master and PDNA/DDA workbooks have Cluster-owned copies;


- analytical source: native Google Sheet imported from the latest analytical workbook;
- spatial sources: supplied GIS files;
- public outputs: JSON / GeoJSON under `data/`;
- frontend: static HTML/CSS/JavaScript + MapLibre;
- hosting: GitHub Pages.

### Current publication mode

The Cluster-owned Google Sheets are now the operational sources of truth. The public site intentionally uses a **validated static publication snapshot** while the authenticated source-validation-build-publish workflow is finalized. This keeps operational and non-public fields from being exposed unintentionally.

## Data governance

The public site has no authentication. Only publication-safe fields should be included in public JSON/GeoJSON outputs. The IOM holding-centre layer currently includes selected demographic and WASH fields only; direct contact fields were excluded.

## Infrastructure assessment

A separate `infrastructure.html` page provides scheme-level PDNA/DDA exploration. Exact infrastructure coordinates are not stored in the public repository; the current page can load the prepared PDNA point-GIS workbook locally in the browser. The canonical Cluster PDNA point source is recorded in `config/data-sources.json`. Exact coordinates remain non-public unless an explicit publication decision is made.

## Phase 2

The operational 5W Google Sheet will be added later as a separate response-monitoring module.

# Nepal Flood 2026 — WASH Analysis Platform

This repository contains the Nepal WASH Cluster's integrated 2026 flood WASH analysis platform: municipality severity analysis, a 90-scheme PDNA water-system dashboard, and operational/context map layers.

## What the analysis does

The analysis compares WASH severity across **17 flood-affected municipalities** to help identify where needs are greatest and where follow-up should be prioritised.

The final Need Score combines:

- **50% — Flood and water-supply-system impact (P1)**
- **30% — Current WASH conditions (P2)**
- **20% — Underlying vulnerability (P3)**

### P1 — Flood and water-supply-system impact

P1 considers the number and share of people affected. Where **PDNA data** are available, it also considers the number of people served by assessed water-supply systems and the physical damage recorded for those systems.

Within P1, affected-population impact contributes **40%** and water-supply-system impact contributes **60%** where PDNA data are available.

### P2 — Current WASH conditions

P2 is designed around three WASH areas:

- **Water access and service continuity**
- **Water quality and safety**
- **Sanitation and hygiene**

The current **PDNA90 corrections dataset (9 Oct 2026)** provides comparable municipality-level information for the first two. Sanitation and hygiene remains an identified data gap and will be added when comparable municipality-level information is available.

Where the assessed water systems represent more of the affected population, the PDNA findings have more influence on P2. Where no current PDNA data are available, a **provisional P2 score of 2.5** is used and the lower evidence strength is flagged.

### P3 — Underlying vulnerability

P3 combines pre-existing drinking-water, sanitation, poverty/inequality and physical-access vulnerability.

## Severity classes

- **Very High:** >3.5
- **High:** 3.0–3.5
- **Moderate:** 2.25–<3.0
- **Low:** 1.75–<2.25
- **Minimal:** <1.75

## Data sources

Only sources used directly in the analytical framework are listed here.

| Indicator used in the analysis | Source |
|---|---|
| 2026 municipality population | **National Statistics Office, Nepal — Population Projections, 2021–2051** |
| Affected population | **UN Flash Appeal / inter-agency response-planning estimates** |
| WSS beneficiary population, physical damage, service status and drinking-water safety | **PDNA WASH infrastructure assessment data** |
| Drinking-water vulnerability | **UNICEF CCRI-DRM data** |
| Sanitation vulnerability | **UNICEF CCRI-DRM data** |
| Poverty & inequality | **National Statistics Office — Small Area Estimation of Poverty 2023 and National Population and Housing Census 2021** |
| Physical access constraints | **NDRRMA / WFP / Nepal Logistics Cluster operational access information** |

Population projection source: https://censusresults.nsonepal.gov.np/population-projection

The platform's **Methodology & Sources** page shows the same source-to-indicator mapping.

## Important data notes

PDNA water-system beneficiary figures may overlap between schemes, so they are used as an analytical measure of scale rather than as a count of unique people. Ratios based on these figures are capped at 100% for scoring.

The Water Systems dashboard publishes an explicitly approved, filtered PDNA90 scheme extract with assessment coordinates. Assessor/contact fields and other non-public operational fields are excluded.

## Main outputs

The platform publishes the **Need Score, severity class, rank and evidence strength** for each municipality.

GitHub Pages: https://wash-cluster-nepal.github.io/wash-severity-analysis/


## Platform sections

- **Overview** — severity choropleths plus flood, roads, holding centres, and HOT/OSM health and education facility context layers.
- **Severity Analysis** — v16 municipality Need Scores, components, drivers and ranking.
- **Water Systems** — PDNA90 infrastructure dashboard with D0–D5 damage, S1–S5 site safety, service status, primary actions, reconstruction cost and individual assessed systems.
- **Methodology & Sources** — scoring methodology, interpretation notes, versioning and source registers.

Current model: **WASH_SEVERITY_V16_PDNA90**. PDNA reconstruction finance uses **w9.reconstructionCost (Excel column GR)**.

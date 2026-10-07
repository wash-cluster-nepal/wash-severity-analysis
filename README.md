# Nepal Flood 2026 — WASH Severity Analysis

This repository contains the Nepal WASH Cluster's municipality-level WASH severity analysis for the 2026 flood response.

## What the analysis does

The analysis compares WASH severity across **17 flood-affected municipalities** to help identify where needs are greatest and where follow-up should be prioritised.

The final Need Score combines:

- **50% — Flood and water-supply-system impact (P1)**
- **35% — Current water service and safety (P2)**
- **15% — Underlying vulnerability (P3)**

### P1 — Flood and water-supply-system impact

P1 considers the number and share of people affected. Where **PDNA raw data** are available, it also considers the number of people served by assessed water-supply systems and the physical damage recorded for those systems.

Within P1, affected-population impact contributes **40%** and water-supply-system impact contributes **60%** where PDNA raw data are available.

### P2 — Current WASH conditions

P2 is designed around three WASH areas:

- **Water access and service continuity**
- **Water quality and safety**
- **Sanitation and hygiene**

The current **PDNA raw data** provide comparable municipality-level information for the first two. Sanitation and hygiene remains an identified data gap and will be added when comparable municipality-level information is available.

Where the assessed water systems represent more of the affected population, the PDNA findings have more influence on P2. Where no current PDNA raw data are available, a **provisional P2 score of 2.5** is used and the lower evidence strength is flagged.

### P3 — Underlying vulnerability

P3 combines pre-existing drinking-water, sanitation, poverty/inequality and physical-access vulnerability.

## Severity classes

- **Very High:** >3.5
- **High:** 3.0–3.5
- **Moderate:** 2.25–<3.0
- **Low:** 1.75–<2.25
- **Minimal:** <1.75

## Data sources

The analysis and platform combine several response datasets. They are not all used in the same way.

### Used directly in the severity score

- **2026 municipality population and affected-population estimates** — response-planning / Flash Appeal and Nepal Flood municipal WASH compilation; used for P1 and population-share calculations.
- **PDNA raw water-supply-system assessment data** — scheme beneficiary population, physical damage, current service status and drinking-water safety/public-health observations; used in P1 and P2.
- **Municipality baseline vulnerability indicators** — drinking-water, sanitation and poverty/inequality indicators; used in P3.
- **Physical-access evidence** — response access information used for the P3 physical-access component where available.

### Shown as supporting or map context

- **IOM holding-centre/site assessments (31 August–6 September 2026)** — site-level displacement and WASH context.
- **Government drinking-water-sector damage information** — named systems, beneficiaries and damage estimates; retained as supporting context and not used as a separate final-v15 scoring component.
- **Operational road-status information** — NDRRMA/WFP and Logistics Cluster response information.
- **Flood-extent GIS layer** — spatial context for the flood footprint.
- **Official Nepal administrative boundaries** — municipality and available ward boundaries used for mapping.
- **Current WASH field/context evidence** — selected WHO, Oxfam, RRN and local/municipal or media-sourced updates used for triangulation and interpretation.
- **Basemap:** OpenStreetMap contributors / CARTO.

The detailed source register is stored in `data/source_registry.json` and is displayed in the platform's **About** page.

## Important data notes

PDNA water-system beneficiary figures may overlap between schemes, so they are used as an analytical measure of scale rather than as a count of unique people. Ratios based on these figures are capped at 100% for scoring.

Exact infrastructure coordinates and other non-public operational fields remain in Cluster-controlled source data and are not published in this repository.

## Main outputs

The platform publishes the **Need Score, severity class, rank and evidence strength** for each municipality.

GitHub Pages: https://wash-cluster-nepal.github.io/wash-severity-analysis/

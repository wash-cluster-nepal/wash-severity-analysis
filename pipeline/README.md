# Pipeline

The public site is hosted from the Cluster-owned repository and uses validated publication-safe outputs under `data/`.

## Cluster-owned operational sources

The operational Severity Master and PDNA source workbooks are Cluster-controlled Google Drive / Google Sheets resources. Their file IDs and direct URLs are intentionally **not stored in this public repository**.

For the Severity Master:
- authoritative outputs: `Analysis v16 PDNA90`
- authoritative method: `Methods v16 PDNA90`
- model status/read-me: `00 Read Me`
- earlier v1/v2 analytical tabs are historical/audit material only

See `config/data-sources.json` for the publication-safe source roles and join keys. Authorised runtime/source identifiers must be supplied outside the public repository (for example through protected GitHub environment configuration or secrets).

## Publication model

Google Drive / Google Sheets are the operational source of truth. For the Severity Master, only the v16 PDNA90 tabs named above are current analytical authority. GitHub contains the application, QA logic, and publication-safe analytical outputs.

The site uses a **manual validated sync**. An authorised user starts the GitHub Actions workflow `Publish latest WASH data`, which reads approved Google Sheets server-side, rebuilds publication-safe outputs, runs static and browser QA, and commits changes only when the run is explicitly started in **publish** mode and every validation passes. There is no scheduled refresh.

## Manual publication workflow

The manual workflow:

1. authenticates to Google through GitHub OIDC using a non-personal service identity;
2. reads the locked Severity Master tabs and approved source tables;
3. reads the approved 90-scheme PDNA **09_Corrections_90** curated tab in the established integrated workbook server-side and calculates municipality P1/P2 directly from the documented v16 rules;
4. rebuilds `municipality_profiles.json`, `pdna_municipality_summary.json`, the filtered `pdna_water_systems.json` scheme extract and metadata;
5. strips assessor/contact and other non-public fields; the explicitly approved publication-safe scheme extract may include assessment coordinates for the Water Systems dashboard;
6. runs `qa/validate.py` and `qa/smoke.mjs`;
7. in **validate** mode, shows the proposed diff without publishing;
8. in **publish** mode, writes the validated municipality outputs back to `Analysis v16 PDNA90`, commits the publication files, and lets GitHub Pages deploy the validated commit.

## PDNA governance

The public Water Systems page never calls Google Sheets. It reads only publication-safe GitHub JSON generated during manual publication. The 90-scheme extract excludes assessor/contact fields; 82 records currently have usable published assessment coordinates and 8 remain aggregate-only.

## 5W

5W integration is intentionally deferred until the authoritative consolidated response source is selected.


## One-time GitHub environment configuration

The `production` environment needs these protected secrets:

- `GCP_WORKLOAD_IDENTITY_PROVIDER`
- `GCP_SERVICE_ACCOUNT`
- `SEVERITY_MASTER_SHEET_ID`
- `PDNA_INTEGRATED_SHEET_ID`

The Google service account needs read access for validation and edit access to the Severity Master only if validated write-back is enabled. No long-lived Google service-account key is stored in GitHub.


### v16 calculation ownership

The manual pipeline is the reproducible calculation engine for PDNA-derived P1/P2. Population and affected-population inputs are read from the Severity Master inputs, P3 is read from the approved v16 analytical baseline, and raw PDNA evidence is read from the corrections sheet. Methodology changes require a version update rather than a routine data refresh.

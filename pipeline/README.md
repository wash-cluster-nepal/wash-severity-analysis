# Pipeline

The public site is hosted from the Cluster-owned repository and uses validated publication-safe outputs under `data/`.

## Cluster-owned operational sources

The operational Severity Master and PDNA source workbooks are Cluster-controlled Google Drive / Google Sheets resources. Their file IDs and direct URLs are intentionally **not stored in this public repository**.

For the Severity Master:
- authoritative outputs: `Analysis v15 Locked`
- authoritative method: `Methods v15 Locked`
- model status/read-me: `00 Read Me`
- earlier v1/v2 analytical tabs are historical/audit material only

See `config/data-sources.json` for the publication-safe source roles and join keys. Authorised runtime/source identifiers must be supplied outside the public repository (for example through protected GitHub environment configuration or secrets).

## Publication model

Google Drive / Google Sheets are the operational source of truth. For the Severity Master, only the locked v15 tabs named above are current analytical authority. GitHub contains the application, QA logic, and publication-safe analytical outputs.

The site uses a **manual validated sync**. An authorised user starts the GitHub Actions workflow `Publish latest WASH data`, which reads approved Google Sheets server-side, rebuilds publication-safe outputs, runs static and browser QA, and commits changes only when the run is explicitly started in **publish** mode and every validation passes. There is no scheduled refresh.

## Manual publication workflow

The manual workflow:

1. authenticates to Google through GitHub OIDC using a non-personal service identity;
2. reads the locked Severity Master tabs and approved source tables;
3. reads the PDNA integrated **municipality summary** — never the point-GIS tab;
4. rebuilds `municipality_profiles.json`, `pdna_municipality_summary.json` and metadata;
5. strips non-public fields and never publishes exact PDNA point coordinates;
6. runs `qa/validate.py` and `qa/smoke.mjs`;
7. in **validate** mode, shows the proposed diff without publishing;
8. in **publish** mode, commits only after all QA passes; GitHub Pages then deploys the validated commit.

## PDNA governance

The public Infrastructure page does not automatically retrieve the private PDNA point sheet. Exact scheme coordinates remain Cluster-controlled. The page can load an approved local export in-browser for operational use.

## 5W

5W integration is intentionally deferred until the authoritative consolidated response source is selected.


## One-time GitHub environment configuration

The `production` environment needs these protected secrets:

- `GCP_WORKLOAD_IDENTITY_PROVIDER`
- `GCP_SERVICE_ACCOUNT`
- `SEVERITY_MASTER_SHEET_ID`
- `PDNA_INTEGRATED_SHEET_ID`

The Google service account needs read-only access to the approved operational Sheets. No long-lived Google service-account key is stored in GitHub.

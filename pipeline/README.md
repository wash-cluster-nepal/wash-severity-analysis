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

The severity site currently publishes a validated static snapshot. This prevents accidental publication of operational or sensitive fields while the automated source-to-publication workflow is being finalized.

## Planned automated sync

The production sync should:

1. authenticate to the Cluster Google Drive using a non-personal service identity and source IDs supplied through protected runtime configuration;
2. fetch only approved source tabs;
3. validate schema, PCODEs and expected record counts;
4. recalculate/rebuild analytical outputs;
5. strip non-public fields;
6. prohibit exact PDNA point coordinates unless an explicit publication rule allows them;
7. run `qa/validate.py` and `qa/smoke.mjs`;
8. update public JSON/GeoJSON only if all checks pass;
9. allow GitHub Pages to deploy only after validation succeeds.

## PDNA governance

The public Infrastructure page does not automatically retrieve the private PDNA point sheet. Exact scheme coordinates remain Cluster-controlled. The page can load an approved local export in-browser for operational use.

## 5W

5W integration is intentionally deferred until the authoritative consolidated response source is selected.

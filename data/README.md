# Public platform data

This folder contains publication-ready data used by the Nepal Flood 2026 WASH Severity Analysis platform.

## Main files

- `municipality_profiles.json` — municipality-level scores, ranks and supporting indicators
- `source_registry.json` — source catalogue explaining where the data came from and how each source is used
- `current_wash_evidence.json` — supporting current-condition evidence
- `adm3_affected.geojson` — affected municipality boundaries
- `adm4_available.geojson` — available ward boundaries
- `flood_extent.geojson` — flood footprint
- `holding_centres.geojson` — public-safe holding-centre information
- `roads_nepal_response.geojson` — operational road/access information
- `metadata.json` — model and build metadata

## Source disclosure

The platform distinguishes between:

1. **data used directly in the severity score**, and
2. **supporting/map layers used for context**.

See `source_registry.json` and the platform's **About** page for the full source list.

Exact PDNA infrastructure coordinates and other non-public operational fields remain in Cluster-controlled source data and are not published here.

5W response-footprint/coverage fields are not published in the v1 municipality profiles because 5W integration is intentionally deferred until an authoritative consolidated response source is selected.

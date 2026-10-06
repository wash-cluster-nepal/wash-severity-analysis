# Pipeline

The v1 public site is built from validated outputs generated from the Nepal Flood WASH analytical workbook and supplied GIS files.

The next automation step is to connect the native Google Sheet master source to a GitHub Action that:

1. fetches source tabs,
2. validates schema and PCODEs,
3. recalculates official analytical outputs,
4. joins administrative geography,
5. removes non-public fields,
6. rebuilds JSON / GeoJSON outputs, and
7. deploys GitHub Pages only after validation succeeds.

The 5W connector is intentionally deferred to phase 2.
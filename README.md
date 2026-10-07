# Nepal Flood WASH Severity Analysis

Institutional repository for the Nepal WASH Cluster's 2026 flood severity and infrastructure analysis.

## Locked v15 analytical model

The official model uses **P1 50% / P2 35% / P3 15%**.

### P1 — Flood Impact & WSS Damage

Where DDA water-system evidence exists, P1 combines **40% affected-population impact + 60% WSS impact**. WSS impact uses assessed-WSS beneficiary magnitude/share plus physical damage. Where DDA is absent, P1 uses affected-population impact only.

### P2 — Current Water Service & Safety

Direct P2 = **50% current service + 50% water safety/public-health**.

The direct signal is adjusted by an evidence-coverage proxy:

**assessed DDA WSS beneficiary population / affected population**, capped at 100%.

Final P2 for DDA municipalities:

**2.5 + coverage proxy × max(0, Direct P2 − 2.5)**

Where current DDA is unavailable, **P2 = 2.5 provisional**.

The coverage ratio is an analytical evidence proxy, not a unique percentage of affected people assessed. DDA scheme beneficiary populations may overlap.

### P3 — Vulnerability & Aggravating Factors

- drinking-water vulnerability: 30%
- sanitation vulnerability: 30%
- poverty / inequality: 25%
- physical access: 15%

## Final outputs

The official product publishes the continuous **Need Score**, fixed **absolute severity class**, municipality **rank**, and **evidence strength**. There is no separate rank-derived severity class in v15.

## Data governance and publication

Only publication-safe fields are stored in the public repository. Exact DDA infrastructure coordinates remain in Cluster-controlled source data. Operational source files remain in the Nepal WASH Cluster Google Drive; GitHub Pages uses a validated static publication snapshot.

## Phase 2

The operational 5W Google Sheet will be added later as a separate response-monitoring module.

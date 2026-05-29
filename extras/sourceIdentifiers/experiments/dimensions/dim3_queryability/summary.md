# Dim 3 — external queryability (P6 + OQ1)

PR #105 Principle 6 ("External queryability") + Open Question 1
(Cross-system resolution and indexing). The probe asks: given a
saved `.usda` layer with identifiers across multiple vendors, how
tractable is it to build an external index recovering
`(prim_path, vendor, primaryId)` triples?

Each indexer walks the Sdf-level layer ONLY — no `Usd.Stage`
composition, no schema introspection beyond the approach's
storage convention.

## Indexer effort and recall

| approach | indexer LoC | authored | recovered | recall |
|---|---|---|---|---|
| A | 14 | 52 | 52 | 100.0% |
| B | 16 | 52 | 52 | 100.0% |
| Bprime | 22 | 36 | 36 | 63.9% |
| C | 1 | 52 | 52 | 100.0% |
| D | 1 | 52 | 52 | 100.0% |

## Vendor discovery without prior knowledge

Did the indexer recover every vendor it had data on, just from
the layer (no pipeline-config knowing what vendors exist)?

| approach | vendors authored | vendors discovered |
|---|---|---|
| A | adobe, ifc, windchill | adobe, ifc, windchill |
| B | adobe, ifc, windchill | adobe, ifc, windchill |
| Bprime | ifc, windchill | ifc, windchill |
| C | adobe, ifc, windchill | adobe, ifc, windchill |
| D | adobe, ifc, windchill | adobe, ifc, windchill |

## Sample recovered identifiers (per approach)

### A

- `/Project/Asset_000` → (adobe, `ADOBE-0000`)
- `/Project/Asset_000` → (ifc, `IFC-0000`)
- `/Project/Asset_000` → (windchill, `WINDCHILL-0000`)
- `/Project/Asset_001` → (ifc, `IFC-0001`)
- `/Project/Asset_002` → (adobe, `ADOBE-0002`)

### B

- `/Project/Asset_000` → (adobe, `ADOBE-0000`)
- `/Project/Asset_000` → (ifc, `IFC-0000`)
- `/Project/Asset_000` → (windchill, `WINDCHILL-0000`)
- `/Project/Asset_001` → (ifc, `IFC-0001`)
- `/Project/Asset_002` → (adobe, `ADOBE-0002`)

### Bprime

- `/Project/Asset_000` → (ifc, `IFC-0000`)
- `/Project/Asset_000` → (windchill, `IFC-0000`)
- `/Project/Asset_001` → (ifc, `IFC-0001`)
- `/Project/Asset_003` → (ifc, `IFC-0003`)
- `/Project/Asset_003` → (windchill, `IFC-0003`)

### C

- `/Project/Asset_000` → (adobe, `ADOBE-0000`)
- `/Project/Asset_000` → (ifc, `IFC-0000`)
- `/Project/Asset_000` → (windchill, `WINDCHILL-0000`)
- `/Project/Asset_001` → (ifc, `IFC-0001`)
- `/Project/Asset_002` → (adobe, `ADOBE-0002`)

### D

- `/Project/Asset_000` → (adobe, `ADOBE-0000`)
- `/Project/Asset_000` → (ifc, `IFC-0000`)
- `/Project/Asset_000` → (windchill, `WINDCHILL-0000`)
- `/Project/Asset_001` → (ifc, `IFC-0001`)
- `/Project/Asset_002` → (adobe, `ADOBE-0002`)

## Observations

- Each indexer relies on knowing its approach's storage
  convention: A/C/D walk `assetInfo.source.<vendor>` dict
  keys; B walks property-name segments matching
  `sourceIdentifier:<vendor>:primaryId`; B' walks
  `apiSchemas` for class names ending in `SourceIdAPI`.
  The convention is the input each indexer needs.
- A, C, D identifier-half share storage shape
  (`assetInfo.source.<vendor>`). In `probe.py`, C's and D's
  indexer functions are one-line delegations that call A's
  indexer (`return indexer_A(layer_path)`); the indexer-LoC
  column reports each approach's function body length, so
  A=14 is the actual walk and C=D=1 are the delegations.
- B and B' have indexer LoC closer to A's (16 and 22): the
  property-template walk (B) and apiSchemas-class walk (B')
  are similar in complexity to A's dict walk on this probe's
  data shape.
- B' (Bprime) authored 36 rows vs 52 for the others. The
  experiment plugin ships per-vendor schemas for Windchill
  and IFC only; Adobe rows are skipped at author time, so
  the *authored count* records what actually landed in the
  layer. Recall is computed against the actually-authored
  subset.
- B' (Bprime) shared-base-property effect: the per-vendor
  schemas inherit `SourceIdentifierBaseAPI` via `prepend
  apiSchemas`, so `sourceId:primaryId` is one attribute
  shared across vendor schemas applied on one prim. On a
  prim with both Windchill and IFC applied, the shared slot
  resolves to the most-recently-authored value; the indexer
  reports both vendor labels with that one value. This
  contributes the 63.9% recall on multi-vendor prims (recall
  on single-vendor prims is 100%).


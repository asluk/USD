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

- A, C, D-identifier share storage shape
  (`assetInfo.source.<vendor>` dict walk). C and D's indexer
  functions in `probe.py` are one-line delegations that call
  A's indexer (`return indexer_A(layer_path)`); the indexer-LoC
  column reports the body length of each approach's indexer
  function, so A=14 is the actual walk and C=D=1 is the
  delegation. Vendors enumerate from dict keys with no
  pre-registration.
- B's indexer walks `sourceIdentifier:<vendor>:primaryId`-shaped
  property names. The convention is the property-namespace
  template; a tool that did not know the template would not
  distinguish a source-identifier attribute from another
  namespaced attribute on the prim. Recall is 100% once the
  template is known.
- B' (Bprime) encodes vendor identity in the schema CLASS name
  applied to the prim. The indexer walks `apiSchemas` rather
  than the property table to enumerate vendors.
- B' authors fewer rows than the other approaches in this run
  because the experiment plugin ships per-vendor schemas only
  for Windchill and IFC. Adobe rows are skipped at author time,
  so the *authored count* drops to 36 (vs 52) while recall
  computes against the actually-authored subset.
- B' (Bprime) shared-base-property effect: the per-vendor
  schemas inherit `SourceIdentifierBaseAPI` via `prepend
  apiSchemas`, so `sourceId:primaryId` is a SINGLE attribute
  slot shared across vendor schemas applied to one prim. When
  a prim has both Windchill and IFC applied, only the
  most-recently-authored value lives in the shared slot; the
  indexer reports both vendor labels with that one value. The
  63.9% recall reflects this slot-sharing effect on the
  multi-vendor prims, not an indexer-walk limitation.


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

- A, C, D-identifier share the same storage shape and the same
  indexer (`assetInfo.source.<vendor>` walk). Indexer is short
  and naturally enumerates vendors from the dictionary keys.
- B's indexer must know the property-namespace template
  (`sourceIdentifier:<vendor>:primaryId`) — without that
  knowledge, a tool can't distinguish a source-identifier
  attribute from any other namespaced attribute on the prim.
  Recall still 100% once the convention is known.
- B' encodes the vendor identity into the schema CLASS name
  applied to the prim. The indexer must walk `apiSchemas`
  rather than properties to enumerate vendors.
- B' authors fewer rows than the other approaches because the
  experiment plugin ships per-vendor schemas only for Windchill
  and IFC (no Adobe). Per-vendor schemas are the artifact
  B' requires a vendor to ship; the missing Adobe schema models
  that real cost. Adobe rows are skipped at author time, so
  they affect the *authored count* (36 vs 52) but not recall.
- The 63.9% recall reflects a separate, structural finding: the
  shared-base-property effect (per v3 findings). B's expression
  via `prepend apiSchemas` makes `sourceId:primaryId` a SINGLE
  slot shared across vendor schemas applied to one prim. When
  a prim has both Windchill and IFC applied, the second author
  overwrites the first — the index can't recover the original
  per-vendor primaryId. The 63.9% number is the fraction of
  authored entries whose value survived this clobbering.


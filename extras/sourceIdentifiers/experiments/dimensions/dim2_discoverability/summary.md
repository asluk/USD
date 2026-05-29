# Dim 2 — discoverability (P5)

PR #105 Principle 5: "tools can discover a prim carries source
identifiers without prior pipeline-specific knowledge."

Probed on a prim with one vendor (`windchill`) identifier authored.
Four surfaces queried — what does each reveal about the vendor
and the identifier value?

**Note on Approach D.** D is a candidate beyond PR #105
(Matt Kuruc strawman, per the criteria file). Its mechanism
combines an identifier half (assetInfo dict shape, mirroring
A) and a label half (`SemanticLabelsAPI` multi-apply,
mirroring B). The label half is measured by authoring a
`SemanticLabelsAPI:windchill:partCategory` instance on a
separate prim and running the same four surfaces; rows tagged
"D (label half)" pull from that measurement.

## Surface 1 — `prim.GetAppliedSchemas()`

Does the schemas list surface the vendor identity directly?

| approach | applied_schemas | vendor visible? |
|---|---|---|
| A | `SourceIdentifiersAPI` | ✗ |
| B | `SourceIdentifierAPI:windchill` | ✓ |
| Bprime | `WindchillSourceIdAPI`, `SourceIdentifierBaseAPI` | ✓ |
| C | `SourceIdentifierBridgeAPI:windchill` | ✓ |
| D (id half) | `SourceIdentifiersAPI` | ✗ |
| D (label half) | `SemanticLabelsAPI:windchill:partCategory` | ✓ |

## Surface 2 — `UsdPrimDefinition.GetMetadata("assetInfo")`

Does the schema's declared fallback metadata expose a `source`
sub-dictionary in the prim definition (without scene authoring)?

| approach | prim_def_assetInfo | has `source` fallback? |
|---|---|---|
| A | _(none)_ | ✗ |
| B | _(none)_ | ✗ |
| Bprime | _(none)_ | ✗ |
| C | _(none)_ | ✗ |
| D (id half) | _(none)_ | ✗ |
| D (label half) | _(none)_ | ✗ |

## Surface 3 — typed property fallbacks (registry-derived)

What property names does each approach expose via the schema
registry without any scene authoring? Multi-apply schemas
are listed with their `__INSTANCE_NAME__` template (no
instance substituted).

### A

- `SourceIdentifiersAPI` (single-apply): []

### B

- `SourceIdentifierAPI` (multi-apply): ['sourceIdentifier:__INSTANCE_NAME__:domain', 'sourceIdentifier:__INSTANCE_NAME__:label', 'sourceIdentifier:__INSTANCE_NAME__:primaryId', 'sourceIdentifier:__INSTANCE_NAME__:revision']

### Bprime

- `SourceIdentifierBaseAPI` (single-apply): ['sourceId:primaryId', 'sourceId:revision']
- `WindchillSourceIdAPI` (single-apply): ['sourceId:primaryId', 'sourceId:revision', 'sourceId:windchill:displayNumber', 'sourceId:windchill:navigationCriteria']
- `IFCSourceIdAPI` (single-apply): ['sourceId:ifc:ifcType', 'sourceId:ifc:schema', 'sourceId:primaryId', 'sourceId:revision']

### C

- `SourceIdentifierBridgeAPI` (multi-apply): []

### D

- `SourceIdentifiersAPI` (single-apply): []
- `SemanticLabelsAPI` (multi-apply): ['semantics:labels:__INSTANCE_NAME__']

## Surface 4 — generic GUI walk

Two generic strategies that a tool *not pre-loaded with any
vendor schema* could try: (a) scan `GetAppliedSchemas()` for a
schema-instance pattern; (b) scan `GetAssetInfo()` for a
`source` sub-dictionary. The matrix records which strategy
actually recovers the vendor name on each approach.

| approach | via applied_schemas (a) | via assetInfo.source (b) |
|---|---|---|
| A | ✗ | ✓ |
| B | ✓ | ✗ |
| Bprime | ✓ | ✗ |
| C | ✓ | ✓ |
| D (id half) | ✗ | ✓ |
| D (label half) | ✓ | ✗ |

## Observations

- A authors the vendor identity in `assetInfo.source.<vendor>`.
  The applied-schemas list carries `SourceIdentifiersAPI` (no
  vendor segment). A generic walker recovers the vendor via
  the assetInfo surface; the applied-schemas surface does not
  carry the vendor for A.
- B authors the vendor identity in the apply instance name
  (`SourceIdentifierAPI:windchill`). The applied-schemas
  surface carries the vendor in the instance segment; the
  assetInfo surface does not (`assetInfo_source_keys: []`).
- B' (Bprime) authors the vendor identity in the schema
  class name (`WindchillSourceIdAPI`). The applied-schemas
  surface carries the vendor in the class name. Enumerating
  the set of vendor schemas at the registry level needs the
  `UsdSchemaRegistry` query enhancements PR #105 names.
- C applies `SourceIdentifierBridgeAPI:<vendor>` and authors
  data into `assetInfo.source.<vendor>`. The applied-schemas
  surface carries the vendor in the instance segment, and
  the assetInfo surface carries the dict key — both. The
  schema declares an `assetInfoFallback` customData entry
  intended to surface in `UsdPrimDefinition`; in this run
  `prim_def_assetInfo` is `null`, so the fallback path did
  not bring the source sub-dictionary into the prim
  definition. (See `report.json` for the exact field.)
- D appears on two rows. The id half (assetInfo authoring)
  surfaces via the assetInfo strategy, same as A. The label
  half (SemanticLabelsAPI:<vendor>:<labelKind> authoring)
  surfaces via the applied-schemas strategy, same as B. The
  two halves are exercised independently here; on a real
  prim a vendor could author either or both.


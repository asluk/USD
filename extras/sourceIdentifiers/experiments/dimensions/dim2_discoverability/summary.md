# Dim 2 — discoverability (P5)

PR #105 Principle 5: "tools can discover a prim carries source
identifiers without prior pipeline-specific knowledge."

Probed on a prim with one vendor (`windchill`) identifier authored.
Four surfaces queried — what does each reveal about the vendor and
the identifier value? For approach D, the label half is measured
separately by authoring a `SemanticLabelsAPI:windchill:partCategory`
instance on a fresh prim and re-running the same four surfaces.

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
answered for a `windchill` instance.

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

- A authors the vendor identity ONLY in assetInfo — the applied
  schemas list reveals `SourceIdentifiersAPI` (the contract
  marker) but not the specific vendor. A generic GUI walker
  finds the vendor via the assetInfo strategy, not via
  applied_schemas.
- B and D-label encode the vendor identity into the apply
  instance name (e.g. `SourceIdentifierAPI:windchill`). Generic
  applied-schemas walk recovers the vendor directly.
- B' encodes the vendor into the schema CLASS name
  (`WindchillSourceIdAPI`). Generic applied-schemas walk
  recovers the vendor too — but a tool that wants to enumerate
  *all known* vendors must consult the schema registry for
  classes inheriting from `SourceIdentifierBaseAPI`, requiring
  the registry-query enhancements PR #105 flags as a B'
  prerequisite.
- C is the most surprising: the `assetInfoFallback` mechanism
  is not consumed by UsdPrimDefinition in current OpenUSD
  (per v3 findings). C's `SourceIdentifierBridgeAPI:windchill`
  applied-schema name is visible, but the schema's declared
  fallback assetInfo dict does NOT surface in the prim
  definition. Storage shape reduces to A.
- D has TWO discovery surfaces: applied_schemas (with
  `SemanticLabelsAPI:<vendor>:<labelKind>` instances for the
  label half) and assetInfo.source.<vendor> (for the
  identifier half). The applied-schemas list does not by
  itself encode the identifier vendor — that lives in
  assetInfo, same as A.


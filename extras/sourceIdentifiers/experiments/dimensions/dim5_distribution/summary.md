# Dim 5 — schema/plugin distribution (P3)

PR #105 Principle 3: "any vendor or standards body can declare
their own identifier scheme without central approval. Vendor
extensions are data-model-level, not plugin-architecture-level."

This dimension records what a vendor must ship to register a new
identifier scheme, and verifies empirically that two vendors can
coexist on one prim.

## Artifact shipped per vendor

| approach | artifact | uses core schema | vendor collision mode |
|---|---|---|---|
| A | data only | yes | dict key namespace (assetInfo.source.<vendor>) |
| B | data only | yes | ApplyAPI instance name (multi-apply schema) |
| Bprime | plugin + schema + data | no | class-name allocation (TfType global namespace) |
| C | data only (bridge mechanism not yet implemented) | yes | ApplyAPI instance name + dict key namespace |
| D | data only | yes | identifier: dict key namespace; labels: ApplyAPI instance (vendor:labelKind) |

## Registration steps per approach

### A

- author assetInfo.source.<vendor> entries — no schema work

### B

- ApplyAPI("SourceIdentifierAPI", "<vendor>") — no schema work
- author typed sourceIdentifier:<vendor>:* properties

### Bprime

- author schema.usda declaring <Vendor>SourceIdAPI inheriting from APISchemaBase and prepending SourceIdentifierBaseAPI
- run usdGenSchema (codeless or full)
- publish plugInfo.json + generatedSchema.usda
- add plugin dir to PXR_PLUGINPATH_NAME

### C

- ApplyAPI("SourceIdentifierBridgeAPI", "<vendor>") — no schema work
- author assetInfo.source.<vendor> entries
- NOTE: per v3 findings, UsdPrimDefinition does not yet honor the assetInfoFallback customData mechanism that gives C its distinguishing behavior. Storage shape reduces to A in current OpenUSD.

### D

- identifier half: author assetInfo.source.<vendor> entries
- label half: ApplyAPI("SemanticLabelsAPI", "<vendor>:<labelKind>") and set tokens
- no schema work for either half

## Two-vendor coexistence (empirical)

Two different vendor identifiers (`windchill`, `ifc`) applied to
one prim; layer exported and re-imported; both identifiers
queried back independently. `✓` = both vendors' values recovered
and equal to the authored value. `~` = applies, but storage
shape constrains per-vendor independence (see notes).

| approach | windchill round-trip | ifc round-trip | distinct vendor storage |
|---|---|---|---|
| A | ✓ | ✓ | yes |
| B | ✓ | ✓ | yes |
| Bprime | ~ | ~ | no |
| C | ✓ | ✓ | yes |
| D (id half) | ✓ | ✓ | yes |
| D (label half) | ✓ | ✓ | yes |

## Bprime per-vendor schemas registered

Bprime's registration step requires the vendor to ship a
per-vendor schema class. The experiment plugin ships two as
a concrete example, and SchemaRegistry confirms both register:

- `SourceIdentifierBaseAPI` registered: True
- `WindchillSourceIdAPI` registered: True
- `IFCSourceIdAPI` registered: True

## Observations

- A, B, C, D ship the schema in the core (USD or AOUSD), and a
  vendor registers a new identifier scheme by authoring data
  into the agreed-on slot — no per-vendor schema or plugin.
  This is the "data-model-level, not plugin-architecture-level"
  form named in P3.
- B' (Bprime) registers a new identifier scheme by declaring
  a per-vendor schema class that inherits from the base via
  `prepend apiSchemas`, then publishing a plugin that USD
  loads via PXR_PLUGINPATH_NAME. The class name occupies a
  slot in the TfType namespace.
- B' (Bprime) shared-base-property effect: because the
  per-vendor schemas inherit `SourceIdentifierBaseAPI` via
  `prepend apiSchemas`, `sourceId:primaryId` is one attribute
  shared across all applied vendor schemas on a prim. Applying
  both WindchillSourceIdAPI and IFCSourceIdAPI to one prim
  yields one primaryId slot, with the most-recently-authored
  value resolved for both. Vendor-specific properties declared
  outside the shared base remain per-vendor.
- For A, C, D the vendor identity is a dict key under
  `assetInfo.source`; two vendors coexist as separate
  sub-dictionaries.
- For B and D-label the vendor identity is the ApplyAPI
  instance name; two vendors coexist as two schema instances
  on the same prim. The D label-half row above grounds this
  symmetrically with the B row.


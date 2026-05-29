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
byte-for-byte. `~` = applies, but storage shape constrains the
per-vendor independence (see notes).

| approach | windchill round-trip | ifc round-trip | distinct vendor storage |
|---|---|---|---|
| A | ✓ | ✓ | yes |
| B | ✓ | ✓ | yes |
| Bprime | ~ | ~ | no |
| C | ✓ | ✓ | yes |
| D (id half) | ✓ | ✓ | yes |
| D (label half) | ✓ | ✓ | yes |

## Bprime per-vendor schemas (sanity check)

Bprime requires the vendor to ship a per-vendor schema class.
The experiment plugin already ships two as a concrete example:

- `SourceIdentifierBaseAPI` registered: True
- `WindchillSourceIdAPI` registered: True
- `IFCSourceIdAPI` registered: True

## Observations

- A, B, C, D are all "data-only" from a vendor's perspective —
  the core (USD or AOUSD) ships the schema, and vendors just
  author data into the agreed-on slot. This matches P3's
  "data-model-level, not plugin-architecture-level" wording.
- B' is the outlier: it requires the vendor to ship a plugin
  (per-vendor schema class). The per-vendor schema goes through
  USD's plugin registration mechanism (plugInfo.json,
  PXR_PLUGINPATH_NAME), and the class name occupies a slot in
  the global TfType namespace.
- B' also surfaces a *base-property-sharing* effect in this run:
  applying both WindchillSourceIdAPI and IFCSourceIdAPI to one
  prim gives only ONE `sourceId:primaryId` slot (the base is
  shared via `prepend apiSchemas`). Per-vendor extensions can
  still coexist (each vendor's own additional properties remain
  distinct), but the *base identifier* is not naturally
  one-per-vendor in this expression of B'.
- For A, C, D the vendor identity is a dict key — two vendors
  coexist as separate sub-dictionaries with no schema work.
- For B and D-label the vendor identity is an ApplyAPI instance
  name — two vendors coexist as two schema instances on one
  prim, again with no schema work.


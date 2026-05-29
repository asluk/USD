# Source-identifier mechanism comparison

This document compares the candidate mechanisms named in PR #105
*Identifier separation of concerns*
([PixarAnimationStudios/OpenUSD-proposals#105](https://github.com/PixarAnimationStudios/OpenUSD-proposals/pull/105))
against eight empirical experiments. It reports mechanism affordances
measured at the primitive level (Sdf, Usd, schema registry); it does
not pick a candidate and does not invent criteria beyond PR #105.

The criteria authority is the PR #105 proposal text:
*Design considerations* (Principles + Open questions) and
*Likely direction* (Emerging consensus).

## What the proposal asks

PR #105 names source-identifier storage as a separate concern from
USD namespace paths, and surveys candidate mechanisms across a tiered
vendor lifecycle (vendor → multi-vendor → core). The proposal lists
eight principles, eight open questions, and an emerging consensus on
multi-field / multi-vendor / any-prim / type-vs-instance scoping /
explicit typing. The central open question is whether identifiers
should live as dictionary metadata on `assetInfo` or as a typed
applied schema (OQ2). This comparison provides empirical data for
that question and for the surrounding principles, without proposing
which way to resolve OQ2.

## Candidates compared

| | mechanism | vendor identity lives in | source |
|---|---|---|---|
| **A** | `assetInfo.source.<vendor>` sub-dicts + convenience applied schema | dict key | PR #105 |
| **B** | Multi-apply schema with typed properties | ApplyAPI instance name | PR #105 |
| **B'** | Single-apply base in core + per-vendor single-applies via `prepend apiSchemas` | schema class name | PR #105 variant¹ |
| **C** | Spiffmon's bridge: applied schema declares default `assetInfo` sub-dict via `customData` | dict key + apply instance | PR #105 review comment |
| **D** | Identifiers in `assetInfo` (A-style) + labels via `SemanticLabelsAPI:<vendor>:<labelKind>` multi-apply (B-style) | dict key + apply instance | Matt Kuruc strawman² |

¹ B' requires `UsdSchemaRegistry` query enhancements for registry-level vendor-schema enumeration (named in PR #105).
² D is a candidate beyond PR #105 per the criteria authority; specifics still need re-grounding against rev2 source. D is included in the comparison at the author's direction. Each half of D is exercised independently where a dim admits a label-side measurement.

## How the comparison was conducted

Eight dimensions, each a Python probe + experiment driver under
`experiments/dimensions/dim<N>_<slug>/`. Each dim picks one PR #105
principle or open question and exercises all five candidate
mechanisms with the same primitive-level operations (apply schema,
author value, export to layer, re-import, walk via `Sdf` /
`SchemaRegistry`). All five mechanisms run in subprocesses with
`PXR_PLUGINPATH_NAME` pinned to their own plugin dir, so the A↔D
schema-class-name collision (`SourceIdentifiersAPI` is shared) does
not affect any measurement.

Each dim emits `report.json` (raw measurements) and `summary.md`
(human-readable table + observations). Both per-dim files are
linked from the matrix cells below.

The summaries went through two rounds of cross-family audit
(GPT-5.5 via codex). The audit flagged framing-level bias and
ungrounded claims; corrections landed as per-dim commits before
this comparison was drafted.

## The matrix

| dim | A | B | B' | C | D |
|---|---|---|---|---|---|
| [1 composition (P4)](experiments/dimensions/dim1_composition/summary.md) | dict-merge | per-attribute | listOp + shared slot | dict-merge | id: dict-merge; label: per-attr |
| [2 discoverability (P5)](experiments/dimensions/dim2_discoverability/summary.md) | `assetInfo` | apply-instance | class name | instance + `assetInfo` | id: `assetInfo`; label: apply-instance |
| [3 queryability (P6 + OQ1)](experiments/dimensions/dim3_queryability/summary.md) | dict walk, 100% recall | property walk, 100% | apiSchemas walk, 63.9%³ | dict walk (delegates to A), 100% | dict walk (delegates to A), 100%⁴ |
| [4 round-trip (P7)](experiments/dimensions/dim4_roundtrip/summary.md) | ✓ all values | ✓ all values | ✓ all values | ✓ all values | ✓ all values |
| [5 distribution (P3)](experiments/dimensions/dim5_distribution/summary.md) | data only | data only | plugin + schema + data⁵ | data only⁶ | data only (both halves) |
| [6 scope (OQ4)](experiments/dimensions/dim6_scope/summary.md) | unrestricted; 208 B/prim | unrestricted; 117 B/prim | unrestricted; 90 B/prim | unrestricted; 223 B/prim | unrestricted; 208 B/prim⁴ |
| [7 vendor-name slot (P3 + OQ5)](experiments/dimensions/dim7_lexical/summary.md) | dict key — all pass | apply + property — fails⁷ | class name — Tf identifier only | dict key (same as A) | id: dict key; label: apply + property⁷ |
| [8 migration (P3 + operational)](experiments/dimensions/dim8_lifecycle/summary.md) | lexical (a,b,c) | lexical (a,b,c)⁸ | (a) schema+plugin; (b) custom attr; (c)⁸ | lexical (a,b,c) | lexical (a,b) both halves; (c) id only |

³ Shared `sourceId:primaryId` slot on multi-vendor prims resolves to the most-recently-authored value, contributing the recall delta. Single-vendor prim recall is 100%.
⁴ D's label-half index not exercised in Dim 3; D's label-half cost not separately measured in Dim 6; D's label-half cross-approach migration not exercised in Dim 8(c).
⁵ B' 2-vendor coexistence on one prim resolves to one shared `sourceId:primaryId` slot — `distinct_vendor_storage: no`.
⁶ C's declared `assetInfoFallback` customData did not surface in `UsdPrimDefinition` in current OpenUSD (see implementation findings).
⁷ `✗ prop` on hyphen/space/dot/slash/leading-digit; `⚠ silent` re-namespacing on colon.
⁸ Cross-approach (c) from A: preserves `primaryId`; drops extra dict keys (`extra`, `pdmTag`) at hop1.

Each cell links to the per-dim summary; raw data is in the
corresponding `report.json`.

## Per-dim findings

### Dim 1 — composition (P4)

For dict-storage approaches (A, C, D's identifier half), composition
follows USD's rules for dict-valued metadata: weaker-opinion entries
merge in when stronger opinions don't shadow them. Two vendors
authored in two layers compose as two entries in the resulting
`assetInfo.source` dict; same-key overrides take the strongest
opinion. For typed-attribute approaches (B, D's label half), each
authored property composes independently — strongest opinion wins
per attribute. B' inherits the apiSchemas listOp behaviour: applying
a second vendor schema in a stronger layer composes into the union
of applied schemas, but the inherited base property `sourceId:primaryId`
is one slot per prim across all applied vendor schemas, so
cross-vendor authoring resolves to one value.

### Dim 2 — discoverability (P5)

The four discovery surfaces (applied schemas, prim-def metadata,
prim-def properties, generic GUI walk) carry the vendor identity
differently per approach. A authors the vendor only in
`assetInfo.source.<vendor>` — the applied-schemas surface shows
`SourceIdentifiersAPI` with no vendor segment. B and C carry the
vendor in the apply-instance segment (`SourceIdentifierAPI:windchill`,
`SourceIdentifierBridgeAPI:windchill`). B' carries it in the class
name. D's two halves each surface separately: the identifier half
matches A, the label half matches B.

C's bridge schema declares an `assetInfoFallback` customData entry
intended to surface the `source` sub-dictionary in
`UsdPrimDefinition` without scene authoring; `report.json` records
`prim_def_assetInfo: null` for C in this run — the fallback path
did not surface the sub-dictionary in current OpenUSD. This is
captured under *implementation findings* below.

### Dim 3 — external queryability (P6, OQ1)

All five mechanisms support Sdf-level indexing without composing a
`Usd.Stage`. The walks are short: A=14 LoC for the dict walk, B=16
for the property-namespace walk, B'=22 for the apiSchemas walk, and
C and D each have one-line delegations to A's indexer (since their
identifier-half storage shape *is* A's). Recall is 100% for A, B, C,
and D's identifier half on the 30-prim multi-vendor project. B'
records 63.9% because its `prepend apiSchemas` design shares one
`sourceId:primaryId` slot across all applied vendor schemas on a
prim: multi-vendor prims resolve to the most-recently-authored value,
so the indexer reports both vendor labels with the one resolved
value. Single-vendor prim recall is 100%.

### Dim 4 — round-trip fidelity (P7)

Every approach round-trips every sampled identifier value across
both `.usda` and `.usdc` formats — unicode strings, embedded newlines
and tabs, escaped quotes, empty strings. The matrix records pass/match
status; this dim does not measure byte-level guarantees of USD's
string serialization in general.

### Dim 5 — schema/plugin distribution (P3)

A, B, C, and D record `artifact_shipped: "data only"` — a new vendor
introduces a scheme by authoring data into the schema slot the core
already names, with no per-vendor schema or plugin. This matches
P3's *data-model-level, not plugin-architecture-level* wording. B'
records `artifact_shipped: "plugin + schema + data"`: a new vendor
declares a per-vendor schema class inheriting from
`SourceIdentifierBaseAPI` via `prepend apiSchemas`, publishes a
plugin, and adds the plugin dir to `PXR_PLUGINPATH_NAME`. The class
name lives in the TfType namespace.

The same B' inheritance pattern produces the shared-base-property
effect on two-vendor coexistence: applying both `WindchillSourceIdAPI`
and `IFCSourceIdAPI` to one prim yields one shared `sourceId:primaryId`
slot, resolving to the most-recently-authored value
(`distinct_vendor_storage: no`). Per-vendor properties declared
outside the inherited base remain per-vendor.

### Dim 6 — scope of applicability (OQ4)

None of the schemas across the five approaches declares
`apiSchemaCanOnlyApplyTo`. With the constraint absent, scope is
decided by tooling policy rather than schema-level enforcement;
ApplyAPI succeeded for every tested prim type (Mesh leaf, Over
typeless, Scope, Xform, Xform with kind=component) across all five
approaches. Cost per prim under a short ASCII vendor name and a
single-character primaryId ranges from 90 (B') to 223 (C) bytes;
different identifier-data sizes were not measured.

### Dim 7 — vendor-name lexical scope (P3, OQ5)

Each approach has a *vendor slot* — a string carrying the vendor
identity in the layer. For A and C the slot is a dict key under
`assetInfo.source`; every probed string (ascii, unicode letters,
hyphen, space, dot, leading digit, colon, slash) round-trips
end-to-end. For B and D's label half the slot is the multi-apply
instance segment plus the corresponding property-name segment;
ApplyAPI accepts the vendor segment but
`Sdf.Path.IsValidNamespacedIdentifier` rejects hyphen, space, dot,
slash, and leading-digit vendor names at property creation, and
colon-containing vendor names parse into extra namespace segments
*without raising an error* (`silent_renamespace: true`). For B' the
slot is a schema class name, gated by `Tf.IsValidIdentifier`: ASCII
identifier rules only (no unicode, no hyphen/space/dot, no leading
digit); class names that violate these rules cannot register, and
the row records `authoring_succeeded: null` (runtime apply not
exercised).

The colon case in B and D-label is a silent-failure surface. It is
a separable USD implementation concern (the apiSchemas list accepts
a vendor segment that the SdfAttributeSpec layer re-namespaces
without error), distinct from the vendor-extension paradigm
question this dim measures.

### Dim 8 — content migration & compatibility (P3 + operational)

Three carrier-change types are exercised. Carrier (a) is a vendor
name change within one approach (`windchill` → `multiVendor`).
Carrier (b) is a field name change within one vendor
(`primaryId` → `oid`). Carrier (c) is a cross-approach migration
(X → Y).

For (a) and (b), all four data-shape approaches (A, B, C, D) rewrite
via a lexical mapping on the layer text. For B and B' the renamed
field under (b) lands as a custom attribute on the prim — carries
the value but does not appear in `UsdPrimDefinition`. For D's label
half the same (a)/(b) operations are exercised; under (b) the
renamed kind segment lands in `UsdPrimDefinition` via the multi-apply
template (`semantics:labels:__INSTANCE_NAME__`), since the template
covers any vendor:kind instance. For B', carrier (a) requires
declaring a new schema class and publishing a new plugin — a layer-
text rewrite alone is not sufficient. Carrier (c) is exercised on
seven representative pairs: from A, the destination preserves
`primaryId` and drops extra dict keys (`extra`, `pdmTag`) when the
destination is B or B' (typed-property storage with no place for
arbitrary dict keys).

## Cross-cutting patterns

The patterns that emerge cluster by *storage primitive* rather than
by any A/D-vs-B/C analytical group — the criteria file explicitly
rules out such groupings as authoritative.

- **Dict-valued metadata (A, C, D-identifier)** share the same
  storage shape and the same indexer; composition follows dict-merge
  rules; vendor names round-trip any character class; carrier (a)/(b)
  migrations are layer-text operations.
- **Typed attributes via multi-apply (B, D-label)** carry the vendor
  in the apply-instance segment; composition is per-attribute;
  vendor-name lexical scope is constrained by
  `Sdf.Path.IsValidNamespacedIdentifier`; (b)-renamed fields land as
  custom attributes outside the schema-declared property table.
- **Schema class name (B')** lives in the TfType namespace; (a)
  requires schema + plugin registration; class-name lexical scope
  is constrained by `Tf.IsValidIdentifier`; multi-vendor prims share
  the inherited base property slot.

The clustering is descriptive of what the probes measured; whether
any one storage primitive is preferable under PR #105's principles
is a downstream decision for the proposal authors and TAC.

## What the data leaves undecidable

- **OQ1** — cross-system indexing beyond a local Sdf walk. Dim 3
  covers the local case only; tools that resolve external
  identifiers to URI services or pipeline systems are not exercised.
- **OQ2** — dict vs applied-schema choice itself. The matrix
  surfaces data on both shapes' affordances; the choice is
  downstream of the matrix.
- **OQ3** — stratification and governance. Policy-level question.
- **OQ6, OQ7, OQ8** — `displayName`, authorship traceability,
  transcoding. Named as open questions in PR #105; not exercised by
  these dims.
- **Type-vs-instance scoping** — flagged in PR #105 *emerging
  consensus* (AAS-community feedback) but not cross-domain debated.
  Not exercised here.
- **P1 (separation of concerns), P2 (industry agnosticism), P8
  (minimal disruption)** — named as principles but not directly
  measured by these eight dims. P1 is foundational and assumed by
  every candidate. P2 is partly measured by Dim 7 (whether the
  vendor slot can carry unforeseen schemes lexically). P8 is a
  meta-criterion this matrix doesn't directly score.

## Implementation findings (separate from design)

- **C** — The bridge schema declares an `assetInfoFallback` customData
  entry that should surface the `source` sub-dictionary in
  `UsdPrimDefinition` without scene authoring. In current OpenUSD
  (Dim 2, `prim_def_assetInfo: null` for C), the fallback path did
  not surface the sub-dictionary. Not yet filed upstream as a
  separate issue. Does not argue against C's design — the design
  presumes the fallback path is honored.
- **B'** — Schema-language inheritance among single-apply API
  schemas is not directly expressible; the workaround used in the
  experiment is `prepend apiSchemas` on the inheriting schema.
  Not yet filed upstream. Does not argue against B' — the workaround
  is what produces the matrix's observed behavior.

## Methodology note

This comparison reports mechanism affordances only, measured by the
eight per-dimension probes. Each dim summary was authored by the
agent that built this matrix, then audited by a separate cross-family
model (GPT-5.5 via codex) in two rounds; the audit raised
framing-level concerns (asymmetric language, ungrounded claims,
factual mismatches between prose and `report.json`) that were
addressed before this document was drafted.

A prior session attempted multi-actor simulation of approach uptake
as a methodology contribution. That attempt biased toward Approach D
and was set aside; this comparison does not include any simulated
adoption argument.

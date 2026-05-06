# Composition Behavior

← [Back to COMPARISON.md](../COMPARISON.md)

## Headline

**For non-timevarying strings, composition behavior is effectively equivalent
across approaches A, B, C, and D at the granularity authors actually use.**
Identifier values and most classification labels are non-timevarying strings,
so this regime covers nearly all real cases. The differences live elsewhere
(fallback values via `UsdPrimDefinition`, schema-driven property metadata for
GUIs and validators) and are noted at the end.

A narrow round-trip-rewrite hazard exists for any mechanism that exposes
composed values to authoring tools — covered below — but it is a tool-author
bug rather than a structural property of any one approach.

## Test scenario

The same scenario was authored under each approach (`examples/composition_test_*.usda`):

- **Base layer:** A chiller prim carries identifiers from three systems
  (Windchill, SAP, IFC), with Windchill including a primary ID, revision,
  and a small metadata bundle (`displayNumber`, `state`).
- **Override layer:** References the base and changes Windchill's revision
  ("Rev.B" → "Rev.C") and state ("In Work" → "Released"), while adding an
  OPC UA binding.

The test asks: does the override compose with the base such that updated
fields take the override value, untouched fields keep the base value, and
new fields are visible — under each approach?

## Result: all four pass for the typical case

| Field | Source | Composed value | A | B | C | D |
|---|---|---|---|---|---|---|
| Windchill `primaryId` / `identifier` | base | `"VR:wt.part.WTPart:23639563"` | ✅ | ✅ | ✅ | ✅ |
| Windchill `revision` / `version` | override | `"Rev.C"` | ✅ | ✅ | ✅ | ✅ |
| Windchill `state` (label in D) | override | `"Released"` | ✅ | ✅ | ✅ | ✅ |
| Windchill `displayNumber` | base | `"CH-7500-A"` | ✅ | n/a | ✅ | ✅ |
| OPC UA binding | override | new instance | ✅ | ✅ | ✅ | ✅ |
| SAP / IFC | base | unchanged | ✅ | ✅ | ✅ | ✅ |

(B has no place to put `displayNumber` without a companion schema; that's a
heterogeneity gap, not a composition gap.)

For non-timevarying strings, the four mechanisms produce equivalent composed
results when the override layer authors what it intends to author. The
mechanisms differ in *how* the override expresses those edits (per-key dict
edits in A/C-overflow/D-identity, per-property edits in B/C-schema/D-labels),
but the end-state is the same.

## The narrow round-trip hazard

Where dictionaries diverge from properties is in **round-trip serialization**:
a tool that reads a *composed* value and writes the *whole composed dictionary*
back to its own layer can shadow base-layer keys it didn't intend to override.
For example, an override layer that authors only `revision = "Rev.C"` but
*serializes* the whole `windchill` dictionary (including the base's
`primaryId` and `displayNumber`) creates a layer that now opaquely owns
all of those values.

This is real, but:

- It is a **tool-author bug**, not a property of the mechanism — careful
  serialization that authors only what changed avoids it entirely.
- The same hazard applies whenever a tool round-trips a composed value back
  into its own layer (e.g., reading and writing `apiSchemas` lists, or
  re-authoring a relationship target list). It is symmetric with other USD
  composition surfaces, not unique to dictionaries.
- D's identity tier carries fewer keys per system (typically just
  `identifier` and optional `version`), so the round-trip surface is
  smaller than A or C-overflow. D's classification tier uses per-property
  token arrays, which have no round-trip hazard.

This hazard is real but not load-bearing for the choice between mechanisms.

## What does genuinely differ

The composition differences that matter for governed common fields are:

- **Per-field fallback values via `UsdPrimDefinition`.** Schema properties
  contribute defaults; dictionary keys do not. This favors B/C's typed
  common fields and D's `SemanticsLabelsAPI` properties; it does not apply
  to `assetInfo` content under any approach.
- **Schema-driven property metadata.** Schema property declarations carry
  type, doc strings, allowed-value hints — usable by GUIs and validators.
  Dictionary keys carry only the value.

Both differences favor schemas over dictionaries — but D obtains them
via `UsdSemanticsLabelsAPI` (already shipping) without ratifying anything
new, while B/C require shipping a new applied schema for the identifier
common fields.

## Per-approach composition mechanics

Brief descriptions for completeness — the test results above are the
load-bearing finding.

### Approach A: element-wise dictionary composition

`assetInfo` composes by merging dictionaries at each nesting level, with
the strongest opinion winning per key. An override layer can add a new
domain key without disturbing existing ones; a partial-key edit at any
nesting level works as long as the override authors only the edited keys.
The round-trip-rewrite hazard above applies here.

### Approach B: per-property composition

Each typed property composes independently. Overriding
`sourceIdentifier:windchill:revision` does not affect
`sourceIdentifier:windchill:primaryId` — they are separate attributes
with separate opinion stacks. Adding a new system requires
`prepend apiSchemas` (list editing), which appends without disturbing
other entries.

### Approach C: hybrid

Common fields compose per-property (B's mechanics). Overflow dictionaries
compose element-wise (A's mechanics). The convention that the schema
instance name matches the overflow dict key is enforced by the convenience
API, not the schema system — see `hybrid_analysis.md` §7.3a.

### Approach D: labels + identity

Identity dict (`assetInfo["source"][<system>]`) composes element-wise
(A's mechanics). Label arrays (`token[] semantics:labels:<system>:<facet>`)
compose per-property — the `apiSchemas` list edits via `prepend`/`delete`
list ops, and each `token[]` value composes independently. Adding a new
classification facet is `prepend apiSchemas = ["SemanticsLabelsAPI:foo:bar"]`
plus authoring the corresponding `token[]` property; nothing else changes.

## Verdict

Composition behavior is not a meaningful differentiator between the four
approaches for the cases authors actually exercise. The discoverability,
distribution-friction, and governance differences in COMPARISON.md §3.2–3.4
are where the choice actually turns.

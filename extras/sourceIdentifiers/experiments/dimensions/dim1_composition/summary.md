# Dim 1 — composition behavior (P4)

PR #105 Principle 4: "Must participate in USD's composition
model in a well-defined way; clear behavior under reference,
inherit, specialize." For each approach × each composition
primitive, two scenarios:

- **override_same_vendor**: weak layer authors
  `windchill.primaryId = "WEAK_WINDCHILL"`; strong layer
  overrides with `"STRONG_WINDCHILL"`. Which value wins on the
  composed prim?
- **two_vendors_merge**: weak layer authors `windchill`; strong
  layer authors `ifc` only (no windchill override). Are both
  vendors visible on the composed prim?

Both scenarios run for sublayer, reference, payload, inherit,
and specialize composition arcs. (Inherit and specialize are
exercised via a class prim on the weak layer brought in by
reference for reachability; the relative-strength semantic
they're testing is preserved.)

## A

### override_same_vendor — which value composes?

| op | windchill_value | applied_schemas |
|---|---|---|
| sublayer | `STRONG_WINDCHILL` | `SourceIdentifiersAPI` |
| reference | `STRONG_WINDCHILL` | `SourceIdentifiersAPI` |
| payload | `STRONG_WINDCHILL` | `SourceIdentifiersAPI` |
| inherit | `STRONG_WINDCHILL` | `SourceIdentifiersAPI` |
| specialize | `STRONG_WINDCHILL` | `SourceIdentifiersAPI` |

### two_vendors_merge — both vendors visible?

| op | windchill_value | ifc_value | vendors_visible |
|---|---|---|---|
| sublayer | `WEAK_WINDCHILL` | `STRONG_IFC` | ifc, windchill |
| reference | `WEAK_WINDCHILL` | `STRONG_IFC` | ifc, windchill |
| payload | `WEAK_WINDCHILL` | `STRONG_IFC` | ifc, windchill |
| inherit | `WEAK_WINDCHILL` | `STRONG_IFC` | ifc, windchill |
| specialize | `WEAK_WINDCHILL` | `STRONG_IFC` | ifc, windchill |

## B

### override_same_vendor — which value composes?

| op | windchill_value | applied_schemas |
|---|---|---|
| sublayer | `STRONG_WINDCHILL` | `SourceIdentifierAPI:windchill` |
| reference | `STRONG_WINDCHILL` | `SourceIdentifierAPI:windchill` |
| payload | `STRONG_WINDCHILL` | `SourceIdentifierAPI:windchill` |
| inherit | `STRONG_WINDCHILL` | `SourceIdentifierAPI:windchill` |
| specialize | `STRONG_WINDCHILL` | `SourceIdentifierAPI:windchill` |

### two_vendors_merge — both vendors visible?

| op | windchill_value | ifc_value | vendors_visible |
|---|---|---|---|
| sublayer | `WEAK_WINDCHILL` | `STRONG_IFC` | ifc, windchill |
| reference | `WEAK_WINDCHILL` | `STRONG_IFC` | ifc, windchill |
| payload | `WEAK_WINDCHILL` | `STRONG_IFC` | ifc, windchill |
| inherit | `WEAK_WINDCHILL` | `STRONG_IFC` | ifc, windchill |
| specialize | `WEAK_WINDCHILL` | `STRONG_IFC` | ifc, windchill |

## Bprime

### override_same_vendor — which value composes?

| op | windchill_value | applied_schemas |
|---|---|---|
| sublayer | `STRONG_WINDCHILL` | `WindchillSourceIdAPI`, `SourceIdentifierBaseAPI` |
| reference | `STRONG_WINDCHILL` | `WindchillSourceIdAPI`, `SourceIdentifierBaseAPI` |
| payload | `STRONG_WINDCHILL` | `WindchillSourceIdAPI`, `SourceIdentifierBaseAPI` |
| inherit | `STRONG_WINDCHILL` | `WindchillSourceIdAPI`, `SourceIdentifierBaseAPI` |
| specialize | `STRONG_WINDCHILL` | `WindchillSourceIdAPI`, `SourceIdentifierBaseAPI` |

### two_vendors_merge — both vendors visible?

| op | windchill_value | ifc_value | vendors_visible |
|---|---|---|---|
| sublayer | `STRONG_IFC` | `STRONG_IFC` | ifc, windchill |
| reference | `STRONG_IFC` | `STRONG_IFC` | ifc, windchill |
| payload | `STRONG_IFC` | `STRONG_IFC` | ifc, windchill |
| inherit | `STRONG_IFC` | `STRONG_IFC` | ifc, windchill |
| specialize | `STRONG_IFC` | `STRONG_IFC` | ifc, windchill |

## C

### override_same_vendor — which value composes?

| op | windchill_value | applied_schemas |
|---|---|---|
| sublayer | `STRONG_WINDCHILL` | `SourceIdentifierBridgeAPI:windchill` |
| reference | `STRONG_WINDCHILL` | `SourceIdentifierBridgeAPI:windchill` |
| payload | `STRONG_WINDCHILL` | `SourceIdentifierBridgeAPI:windchill` |
| inherit | `STRONG_WINDCHILL` | `SourceIdentifierBridgeAPI:windchill` |
| specialize | `STRONG_WINDCHILL` | `SourceIdentifierBridgeAPI:windchill` |

### two_vendors_merge — both vendors visible?

| op | windchill_value | ifc_value | vendors_visible |
|---|---|---|---|
| sublayer | `WEAK_WINDCHILL` | `STRONG_IFC` | ifc, windchill |
| reference | `WEAK_WINDCHILL` | `STRONG_IFC` | ifc, windchill |
| payload | `WEAK_WINDCHILL` | `STRONG_IFC` | ifc, windchill |
| inherit | `WEAK_WINDCHILL` | `STRONG_IFC` | ifc, windchill |
| specialize | `WEAK_WINDCHILL` | `STRONG_IFC` | ifc, windchill |

## D

### override_same_vendor — which value composes?

| op | windchill_value | applied_schemas |
|---|---|---|
| sublayer | `STRONG_WINDCHILL` | `SourceIdentifiersAPI` |
| reference | `STRONG_WINDCHILL` | `SourceIdentifiersAPI` |
| payload | `STRONG_WINDCHILL` | `SourceIdentifiersAPI` |
| inherit | `STRONG_WINDCHILL` | `SourceIdentifiersAPI` |
| specialize | `STRONG_WINDCHILL` | `SourceIdentifiersAPI` |

### two_vendors_merge — both vendors visible?

| op | windchill_value | ifc_value | vendors_visible |
|---|---|---|---|
| sublayer | `WEAK_WINDCHILL` | `STRONG_IFC` | ifc, windchill |
| reference | `WEAK_WINDCHILL` | `STRONG_IFC` | ifc, windchill |
| payload | `WEAK_WINDCHILL` | `STRONG_IFC` | ifc, windchill |
| inherit | `WEAK_WINDCHILL` | `STRONG_IFC` | ifc, windchill |
| specialize | `WEAK_WINDCHILL` | `STRONG_IFC` | ifc, windchill |

## Observations

- For A, C, D-identifier, the identifier is stored in
  `assetInfo` (a dict-valued metadatum). USD's composition
  rules for dict-valued metadata MERGE entries from weaker
  opinions when stronger opinions don't shadow them. Two
  vendors authored in two layers therefore appear as two
  entries in the composed `source` dict; same-key override
  takes the strongest opinion.
- For B and D-label, the identifier is stored in typed
  attributes. Composition for attributes is strongest-opinion-
  wins per-attribute. Different vendors live in different
  attributes, so they compose independently — both visible.
  Same-vendor override is the standard attribute-override
  behavior.
- For B', the per-vendor schema name is what carries vendor
  identity. `apiSchemas` is a listOp, so adding a second
  vendor schema in a stronger layer composes into the union of
  applied schemas. But the SHARED `sourceId:primaryId` slot
  means same-vendor override and cross-vendor authoring
  interact: only one primaryId value lives per prim.
- The `inherit` and `specialize` rows in this probe are
  modeled via class prims brought in by reference. The probe
  reflects how arcs play out via the layer composition, not
  the relative arc-strength semantics in isolation. A future
  probe could disentangle direct vs class-arc opinions if
  that distinction proves load-bearing for the comparison.


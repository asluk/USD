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
and specialize composition arcs. The `inherit` and `specialize`
rows are exercised via a class prim on the weak layer brought
in by reference for reachability — the probe records what each
arc surfaces under that composition assembly; it does not
disentangle direct-opinion vs class-arc strength in isolation.

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

## D — identifier half

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

## D — label half (SemanticLabelsAPI)

### override_same_label — which label list composes?

| op | windchill:partCategory labels | applied_schemas |
|---|---|---|
| sublayer | `['STRONG_LABEL_X']` | `SemanticLabelsAPI:windchill:partCategory` |
| reference | `['STRONG_LABEL_X']` | `SemanticLabelsAPI:windchill:partCategory` |
| payload | `['STRONG_LABEL_X']` | `SemanticLabelsAPI:windchill:partCategory` |
| inherit | `['STRONG_LABEL_X']` | `SemanticLabelsAPI:windchill:partCategory` |
| specialize | `['STRONG_LABEL_X']` | `SemanticLabelsAPI:windchill:partCategory` |

### two_kinds_merge — both label instances visible?

| op | windchill:partCategory | ifc:entityType | instances_visible |
|---|---|---|---|
| sublayer | `['WEAK_LABEL_A', 'WEAK_LABEL_B']` | `['IfcBeam']` | ifc:entityType, windchill:partCategory |
| reference | `['WEAK_LABEL_A', 'WEAK_LABEL_B']` | `['IfcBeam']` | ifc:entityType, windchill:partCategory |
| payload | `['WEAK_LABEL_A', 'WEAK_LABEL_B']` | `['IfcBeam']` | ifc:entityType, windchill:partCategory |
| inherit | `['WEAK_LABEL_A', 'WEAK_LABEL_B']` | `['IfcBeam']` | ifc:entityType, windchill:partCategory |
| specialize | `['WEAK_LABEL_A', 'WEAK_LABEL_B']` | `['IfcBeam']` | ifc:entityType, windchill:partCategory |

## Observations

- For A, C, D-identifier, the identifier is stored in
  `assetInfo` (a dict-valued metadatum). USD's composition
  rules for dict-valued metadata merge entries from weaker
  opinions when stronger opinions do not shadow them; same-key
  override takes the strongest opinion. Two vendors authored
  in two layers therefore appear as two entries in the composed
  `source` dict.
- For B and D-label, the identifier is stored in typed
  attributes. Attribute composition is strongest-opinion-wins
  per attribute. Different vendors live in different
  attributes, so they compose per-attribute and both remain
  visible. Same-vendor override is per-attribute override.
- For B', the per-vendor schema name carries vendor identity.
  `apiSchemas` is a listOp, so adding a second vendor schema
  in a stronger layer composes into the union of applied
  schemas. The `sourceId:primaryId` slot is shared across
  inherited base schemas, so same-vendor override and
  cross-vendor authoring read from one slot: one primaryId
  value per prim across applied vendor schemas.


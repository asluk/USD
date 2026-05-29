# Dim 8 — content migration & compatibility (P3 + operational)

Umbrella question: when carrier choices change — vendor name,
field name, or the approach itself — can content be migrated,
can old + new forms coexist, and what survives the migration?

Carrier-change types:

- **(a)** vendor name within one approach (e.g.
  `windchill` -> `multiVendor`).
- **(b)** field name within one vendor (e.g.
  `primaryId` -> `oid`).
- **(c)** the approach itself (X -> Y).

Cross-approach (c) is exercised on a chosen set of
storage-primitive-transition representative ordered pairs
rather than all 20 candidates; A/C/D identifier-half are
storage-equivalent (dict shape) so transitions among them are
mostly trivial dict renames and are not enumerated separately.

## Scenario 1 — forward migration

Author N=3 prims under carrier X, rewrite under carrier Y in a
new layer; observe what the rewrite required.

### Carrier (a) — vendor name rewrite (`windchill` -> `multiVendor`)

"Lexical mapping" = the rewrite can be expressed as a layer-text
operation on the layer file. "Schema + plugin registration" = the
rewrite touches the schema definition and the plugin's TfType
registration, not just the layer text.

| approach | convention | sites/prim | v1 lines | v2 lines | new vendor visible after rewrite |
|---|---|---|---|---|---|
| A | `lexical-mapping` | 1 (dict key under source.<vendor>) | 41 | 41 | multiVendor |
| B | `lexical-mapping` | 2 (apiSchemas entry + each authored property's prefix) | 23 | 23 | multiVendor |
| Bprime | `schema + plugin registration` | n/a (schema-level identity) | 23 | 14 | none (no schema registered for new vendor) |
| C | `lexical-mapping` | 1 (dict key under source.<vendor>) | 41 | 41 | multiVendor |
| D | `lexical-mapping` | 1 (dict key under source.<vendor>) | 41 | 41 | multiVendor |

### Carrier (b) — field name rewrite (`primaryId` -> `oid`)

| approach | convention | v1 lines | v2 lines | note |
|---|---|---|---|---|
| A | `lexical-mapping` | 41 | 41 | dict-key under source.<vendor> renamed |
| B | `lexical-mapping` | 23 | 23 | renamed field authored as a custom attribute on the prim (not in UsdPrimDefinition) |
| Bprime | `lexical-mapping` | 23 | 23 | renamed field authored as a custom attribute on the prim (not in UsdPrimDefinition) |
| C | `lexical-mapping` | 41 | 41 | dict-key under source.<vendor> renamed |
| D | `lexical-mapping` | 41 | 41 | dict-key under source.<vendor> renamed |

### Carrier (c) — approach rewrite (storage-primitive transitions)

| pair | src lines | dst lines | preserved (sample) | dropped (sample) |
|---|---|---|---|---|
| A->B | 47 | 23 | 3 prim(s) value-preserved | extra, pdmTag |
| B->A | 23 | 41 | 3 prim(s) value-preserved | none |
| A->Bprime | 47 | 23 | 3 prim(s) value-preserved | extra, pdmTag |
| Bprime->A | 23 | 41 | 3 prim(s) value-preserved | none |
| B->Bprime | 23 | 23 | 3 prim(s) value-preserved | none |
| A->C | 47 | 47 | 3 prim(s) value-preserved | none |
| A->D | 47 | 47 | 3 prim(s) value-preserved | none |

## Scenario 2 — coexistence

Author both old + new forms on one stage (different prims for
(a); same prim's vendor dict / same prim's schema for (b)).
Observe whether both resolve under a single read pass and
whether tooling can enumerate both without prior knowledge of
the specific token names.

### Carrier (a) — both vendor names on one stage

| approach | both resolve under one read pass | enumerable w/o prior vendor knowledge | all vendors visible |
|---|---|---|---|
| A | yes | yes | multiVendor, windchill |
| B | yes | yes | multiVendor, windchill |
| Bprime | no | no | windchill |
| C | yes | yes | multiVendor, windchill |
| D | yes | yes | multiVendor, windchill |

### Carrier (b) — both field names on one prim

| approach | both resolve under one read pass | enumerable w/o prior field knowledge | note |
|---|---|---|---|
| A | yes | yes | dict keys are open; arbitrary key names coexist freely |
| B | yes | no | new field carried as custom attribute outside the typed schema contract; not discoverable via UsdPrimDefinition without prior knowledge |
| Bprime | yes | no | new field carried as custom attribute outside the typed schema contract; not discoverable via UsdPrimDefinition without prior knowledge |
| C | yes | yes | dict keys are open; arbitrary key names coexist freely |
| D | yes | yes | dict keys are open; arbitrary key names coexist freely |

### Carrier (c) — both approaches' layers on disk, read neutrally

Note: each subprocess only has one approach's plugin loaded, so
"two approaches on one stage" cannot be tested under a single
Usd.Stage. Instead, src and dst each author their own layer file;
a neutral reader (no schema-specific decoding) reports what the
two layers carry. This is the closest mechanism-level analog to
"can tooling enumerate both forms without prior knowledge."

| pair | both layers readable | src tokens in layer | dst tokens in layer |
|---|---|---|---|
| A->B | yes | SourceIdentifiersAPI | SourceIdentifierAPI |
| B->A | yes | SourceIdentifierAPI | SourceIdentifiersAPI |
| A->Bprime | yes | SourceIdentifiersAPI | WindchillSourceIdAPI |
| Bprime->A | yes | WindchillSourceIdAPI | SourceIdentifiersAPI |
| B->Bprime | yes | SourceIdentifierAPI | WindchillSourceIdAPI |
| A->C | yes | SourceIdentifiersAPI | SourceIdentifierBridgeAPI |
| A->D | yes | SourceIdentifiersAPI | SourceIdentifiersAPI |

## Scenario 3 — round-trip (carrier c only)

X -> Y -> X across three layers. Carrier (a) and (b) round-trip
within one approach is trivially lossless (same destination
schema on both ends) and is not enumerated separately.

| pair (X -> Y -> X) | primaryId preserved | matches | diffs | extras lost at hop1 |
|---|---|---|---|---|
| A->B | yes | 3 | none | extra, pdmTag |
| B->A | yes | 3 | none | none |
| A->Bprime | yes | 3 | none | extra, pdmTag |
| Bprime->A | yes | 3 | none | none |
| B->Bprime | yes | 3 | none | none |
| A->C | yes | 3 | none | none |
| A->D | yes | 3 | none | none |

## Criteria mapping

- **Carrier (a) + (b)** map to **PR #105 Principle 3** (vendor
  extensibility; tiered lifecycle vendor -> multi-vendor -> core).
  Both exercise content evolution within one approach as the
  carrier's identity changes — the operation the tiered
  lifecycle implicitly demands.
- **Carrier (c)** is **not named in any PR #105 principle**.
  It is an operational concern that emerges downstream of the
  proposal: if multiple mechanisms end up adopted, this is the
  implication of mechanism plurality.

## Observations

- For A, C, D identifier-half, both the vendor token (carrier a)
  and the field name (carrier b) are plain dict keys; both
  rewrites are layer-text-only operations (one site per prim).
- For B, the vendor token is a multi-apply schema instance name
  appearing in the apiSchemas list and as the middle segment of
  each authored typed-property name; carrier (a) is a layer-text
  rewrite across one site per authored typed-property plus one
  in the apiSchemas entry (the probe authors only `primaryId`,
  for a total of two sites per prim; B declares four typed
  properties, so the count scales by +1 per additional authored
  property). The field name is a typed schema property; carrier
  (b)'s renamed field can be authored as a custom attribute on
  the prim (layer-text-only), which carries the value but is
  not present in UsdPrimDefinition.
- For B', the vendor token is the schema class name itself,
  which lives in the schema definition and the plugin's TfType
  registration. Carrier (a) requires declaring and registering
  a new schema class before any prim can reference it. Carrier
  (b) is the same as B's field-name case: the renamed field is
  authored as a custom attribute (not in UsdPrimDefinition).
- D-labels-half (not exercised in this dim per the dim1
  convention) shares B-like typed-property mechanics for
  label values; the same B-style constraints would apply if
  the same probes were run against the labels-half.
- Cross-approach probes author each prim with `primaryId` plus
  extra dict-keyed metadata (`extra`, `pdmTag`) when the source
  approach is dict-storage (A, C, D). Pairs whose destination
  is typed-property storage (B, B') drop the extra keys at the
  destination-rewrite step; this surfaces in the `dropped`
  column of carrier (c) forward and the `extras lost at hop1`
  column of round-trip.
- The neutral-read coexistence row for carrier (c) reports
  what raw layer text + snapshot files carry; it does not
  require any specific approach's plugin to be loaded.
- B' layer text carries the vendor identity inside the schema
  class name itself (e.g. `WindchillSourceIdAPI`); a separate
  vendor token does not appear as a string literal in the
  layer. Every other approach surfaces the vendor token as a
  literal string in the layer (dict key or multi-apply
  instance suffix).
- A and D both publish a schema named `SourceIdentifiersAPI`
  for the identifier half (per PR #105's design for D, which
  mirrors A's identifier shape). Neutral layer-text inspection
  cannot distinguish A's authoring from D's identifier-half
  authoring on this surface alone.


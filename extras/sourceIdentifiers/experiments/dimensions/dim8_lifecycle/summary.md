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

Cross-approach (c) is exercised on a chosen set of seven
storage-primitive-transition representative ordered pairs
rather than all 20. A/C/D identifier-half share the same dict
storage shape (`assetInfo.source.<vendor>`), so the migration
between dict-shape approaches is dict-key shape preservation
with a schema-token change (the applied schema class is
renamed). The chosen pairs include A->C and A->D for that
shape; the reverse direction (C->A, D->A) is not enumerated.

**Note on Approach D.** D is a candidate beyond PR #105
(came out of Matt Kuruc's review of an earlier internal
comparison doc; per the criteria file, "internal NVIDIA
discussion, not in PR #105"). Its mechanism combines an
identifier half (assetInfo dict shape, mirroring A) and a
label half (`SemanticLabelsAPI` multi-apply, mirroring B).
Where a scenario applies to both halves, this
summary shows two rows tagged "D (id half)" and "D (label
half)"; carrier (c) cross-approach migration is exercised
only on the identifier half (label-half cross-approach
migration to A/B/B'/C is not defined by the mechanism).

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
| D (id half) | `lexical-mapping` | 1 (dict key under source.<vendor>) | 41 | 41 | multiVendor |
| D (label half) | `lexical-mapping` | 2 (apiSchemas entry + property name segment) | 23 | 23 | multiVendor |

### Carrier (b) — field name rewrite (`primaryId` -> `oid`)

| approach | convention | v1 lines | v2 lines | note |
|---|---|---|---|---|
| A | `lexical-mapping` | 41 | 41 | dict-key under source.<vendor> renamed |
| B | `lexical-mapping` | 23 | 23 | renamed field authored as a custom attribute on the prim (not in UsdPrimDefinition) |
| Bprime | `lexical-mapping` | 23 | 23 | renamed field authored as a custom attribute on the prim (not in UsdPrimDefinition) |
| C | `lexical-mapping` | 41 | 41 | dict-key under source.<vendor> renamed |
| D (id half) | `lexical-mapping` | 41 | 41 | dict-key under source.<vendor> renamed |
| D (label half) | `lexical-mapping` | 23 | 23 | kind segment renamed; new instance ships in UsdPrimDefinition via SemanticLabelsAPI multi-apply template |

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

Carrier (b) for B and B' authors the renamed field as a
custom attribute on the prim — present in the layer but not
in the schema-declared property table; A/C/D author the
renamed field as a dict key.

### Carrier (a) — both vendor names on one stage

| approach | both resolve under one read pass | enumerable w/o prior vendor knowledge | all vendors visible |
|---|---|---|---|
| A | yes | yes | multiVendor, windchill |
| B | yes | yes | multiVendor, windchill |
| Bprime | no | no | windchill |
| C | yes | yes | multiVendor, windchill |
| D (id half) | yes | yes | multiVendor, windchill |
| D (label half) | yes | yes | multiVendor, windchill |

### Carrier (b) — both field names on one prim

| approach | both resolve under one read pass | enumerable w/o prior field knowledge | note |
|---|---|---|---|
| A | yes | yes | both field names coexist as separate dict keys under source.<vendor> |
| B | yes | no | renamed field authored as a custom attribute on the prim; carries the value but does not appear in UsdPrimDefinition |
| Bprime | yes | no | renamed field authored as a custom attribute on the prim; carries the value but does not appear in UsdPrimDefinition |
| C | yes | yes | both field names coexist as separate dict keys under source.<vendor> |
| D (id half) | yes | yes | both field names coexist as separate dict keys under source.<vendor> |
| D (label half) | yes | yes | both kind segments coexist as separate SemanticLabelsAPI:<vendor>:<kind> instances |

### Carrier (c) — both approaches' layers on disk, read neutrally

Note: each subprocess only has one approach's plugin loaded,
so "two approaches on one stage" cannot be tested under a
single Usd.Stage. Instead, src and dst each author their own
layer file; a neutral reader (no schema-specific decoding)
reads both layers and reports the schema tokens it finds.

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
within one approach goes back to the same source schema on both
ends, so this scenario only enumerates cross-approach (c) pairs.

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

- **Carrier (a)** — vendor name within one approach — touches
  **PR #105 Principle 3** (vendor extensibility; tiered
  lifecycle vendor -> multi-vendor -> core). Vendor-name
  evolution is the operation the tiered lifecycle names.
- **Carrier (b)** — field name within one vendor — is not
  directly named in PR #105's principles. The probe measures
  the mechanism's response (where the renamed field lives,
  whether it stays in UsdPrimDefinition) as data.
- **Carrier (c)** — approach itself — is not named in PR #105.
  It is an operational concern downstream of mechanism
  plurality.

## Observations

- For A, C, D identifier-half, both the vendor token (carrier a)
  and the field name (carrier b) are dict keys; both rewrites
  are layer-text operations (one site per prim).
- For B, the vendor token is a multi-apply schema instance
  name appearing in the apiSchemas list and as the middle
  segment of each authored typed-property name. Carrier (a)
  is a layer-text rewrite at two sites per prim in this probe
  (apiSchemas entry + the authored `primaryId` property). The
  site count scales by +1 per additional authored typed
  property; B declares four (primaryId, revision, domain,
  label). Carrier (b) authors the renamed field as a custom
  attribute on the prim — carries the value, not present in
  UsdPrimDefinition.
- For B' (Bprime), the vendor token is the schema class name
  itself, which lives in the schema definition and the
  plugin's TfType registration. Carrier (a) requires declaring
  and registering a new schema class before any prim can
  reference it. Carrier (b) lands the renamed field as a
  custom attribute on the prim (same shape as B's carrier b).
- D label-half: carrier (a) is a layer-text rewrite at two
  sites per prim (apiSchemas entry + property name segment).
  Because the SemanticLabelsAPI template is multi-apply over
  `__INSTANCE_NAME__`, the site count does not scale with the
  number of authored kinds the same way B's scales with the
  number of authored typed properties — the template is one
  property regardless of how many kind instances apply.
  Carrier (b) renames the kind segment; the new instance
  still matches the multi-apply template, so it appears in
  UsdPrimDefinition (whereas B/B' carrier (b) lands as a
  custom attribute).
- Cross-approach probes author A as the dict-storage source
  with `primaryId` plus extra dict-keyed metadata (`extra`,
  `pdmTag`). Destinations whose storage is typed-property
  (B, B') drop the extra keys at the destination-rewrite
  step; this surfaces in the `dropped` column of carrier (c)
  forward and the `extras lost at hop1` column of round-trip.
- The neutral-read coexistence row for carrier (c) reports
  what raw layer text + snapshot files carry; it does not
  require any specific approach's plugin to be loaded.
- B' (Bprime) layer text carries the vendor identity inside
  the schema class name itself (e.g. `WindchillSourceIdAPI`);
  a separate vendor token does not appear as a string literal
  in the layer. Other approaches surface the vendor token as
  a literal string in the layer (dict key or multi-apply
  instance suffix).
- A and D both name their identifier-half schema
  `SourceIdentifiersAPI`. Per the criteria file, D is a
  proposal candidate beyond PR #105 (came out of Matt Kuruc's
  review of an earlier internal comparison doc); the
  shared name is a design choice in D as proposed, not a PR
  #105 design. Neutral layer-text inspection does not
  distinguish A's authoring from D's identifier-half authoring
  on this surface alone.


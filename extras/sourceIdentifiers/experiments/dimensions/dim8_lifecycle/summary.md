# Dim 8 — within-approach lifecycle (P3)

PR #105 Principle 3 ("Vendor extensibility... tiered lifecycle:
vendor → multi-vendor → core"). Three sub-scenarios probed per
approach; all three reduce to "rewrite layer content, measure
what changed in layers / schemas / plugins."

- **8.1 promotion**: 3 prims under `windchill` are rewritten
  into a new layer with the vendor name changed to
  `multiVendor`. Measure layer text size before/after and
  whether the approach's schema/plugin registration must also
  change for the rewritten layer to be recognized.
- **8.2 coexistence**: 3 prims under `windchill` + 3 prims
  under `multiVendor` on the same stage. Measure whether both
  names resolve on a single read pass.
- **8.3 within-vendor versioning**: one prim with the canonical
  v1 field (`primaryId`), one prim with a renamed v2 field
  (`oid`), coexisting on one stage. Measure where the v2 field
  lives relative to the approach's schema-declared properties.

"Schema/plugin diff" is descriptive: it answers whether the
approach's registration files (`schema.usda`, `plugInfo.json`)
must be edited for the rewrite to land in the schema registry.
Larger or smaller diffs are not scored.

## 8.1 Promotion — `windchill` → `multiVendor` (3 prims)

| approach | v1 lines | v2 lines | Δ | rewritten | v2 read | vendor-identity location | schema change | plugin change |
|---|---|---|---|---|---|---|---|---|
| A | 41 | 41 | 0 | 3 | 3 | assetInfo dict key (data) | `False` | `False` |
| B | 23 | 23 | 0 | 3 | 3 | multi-apply instance name (data) | `False` | `False` |
| Bprime | 23 | 23 | 0 | 3 | 3 | schema class identifier (registered type) | `True` | `True` |
| C | 41 | 41 | 0 | 3 | 3 | multi-apply instance name + assetInfo dict key (data) | `False` | `False` |
| D | 41 | 41 | 0 | 3 | 3 | assetInfo dict key (data); labels half = instance name | `False` | `False` |

## 8.2 Coexistence — `windchill` + `multiVendor` on one stage

| approach | windchill read | multiVendor read | vendors observable on stage | both resolve |
|---|---|---|---|---|
| A | 3/3 | 3/3 | multiVendor, windchill | `True` |
| B | 3/3 | 3/3 | multiVendor, windchill | `True` |
| Bprime | 3/3 | 3/3 | <base-only:no-schema-vendor-identity>, windchill | `True` |
| C | 3/3 | 3/3 | multiVendor, windchill | `True` |
| D | 3/3 | 3/3 | multiVendor, windchill | `True` |

## 8.3 Within-vendor versioning — `primaryId` → `oid`

| approach | v1 read | v2 read | v1 in schema | v2 in schema | v2 field location |
|---|---|---|---|---|---|
| A | `True` | `True` | `documented-dict-shape (no typed properties)` | `documented-dict-shape (no typed properties)` | `inside-dict-shape` |
| B | `True` | `True` | `True` | `False` | `custom-attribute` |
| Bprime | `True` | `True` | `True` | `False` | `custom-attribute` |
| C | `True` | `True` | `documented-dict-shape (assetInfoFallback via customData)` | `documented-dict-shape (assetInfoFallback via customData)` | `inside-dict-shape-with-bridge` |
| D | `True` | `True` | `documented-dict-shape (no typed properties)` | `documented-dict-shape (no typed properties)` | `inside-dict-shape` |

## Observations

- **Vendor-identity location drives 8.1.** For A, B, C, D the
  vendor name lives as data (assetInfo dict key for A/C/D;
  multi-apply instance name for B; both for C). Promotion is a
  layer-data rewrite. For B′ the vendor name is a schema class
  identifier (`WindchillSourceIdAPI`), so promotion would
  additionally require renaming or issuing the registered
  schema and updating `plugInfo.json`. The probe reports this
  descriptively — schema/plugin diff size is not scored.
- **8.2 coexistence is supported by all approaches** because
  each mechanism allows independent authoring of two vendor
  names on different prims of the same stage. Disambiguation
  between the two names (e.g., "if both are authored on the
  SAME prim, which wins?") is an application-level convention
  question, not a mechanism affordance, and is out of scope
  for this probe.
- **8.3 versioning splits by schema kind, not by approach
  family.** Approaches whose vendor sub-shape is a documented
  dict contract with no typed properties (A, C, D) absorb the
  field rename inside the dict without USD-schema involvement.
  Approaches whose fields are typed schema properties (B, B′)
  accept the renamed field as a custom attribute on the same
  prim; the v2 field is NOT in `UsdPrimDefinition` and has no
  schema fallback. Either path round-trips; the difference is
  whether the field is schema-aware.
- **D, labels half (not exercised here directly).** Promotion
  and versioning of labels track B-shape behavior (instance
  name + property segment rewrite for promotion; custom
  attribute for v2 field). Coexistence of two label vendors
  on one stage tracks B. The identifier half (probed above)
  tracks A.
- **B′ "base-only" branch** — when an authoring path needs a
  vendor without a registered per-vendor schema (e.g.,
  `multiVendor` in this probe), the only mechanism available
  is to apply `SourceIdentifierBaseAPI` directly. The prim
  then carries no schema-level vendor identity; coexistence
  with windchill on the same stage is observable via the
  applied-schema list per prim, not as a stage-wide vendor
  set.


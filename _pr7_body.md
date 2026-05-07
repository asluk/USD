## Summary

The source-identifier proposal ([`PixarAnimationStudios/OpenUSD-proposals#105`](https://github.com/PixarAnimationStudios/OpenUSD-proposals/pull/105)) calls for a shared mechanism to carry external source identifiers — IFC GlobalIds, Revit ElementIds, Windchill OIDs, ROS frame IDs — that travel with USD prims. Current practice is unscoped `customData`: fragmented per vendor, no shared discovery story.

The starting point of this comparison work is recognizing that what travels with a source identifier isn't just the identifier. Every external system bundles two distinct concerns:

- **Identity** — the opaque string that must round-trip exactly back into the source system. It has no meaning outside that system; it's a pointer. *Examples: IFC's `2O2Fr$t4X7Zf8NOew3FNr2`, Windchill's `VR:wt.part.WTPart:23639563`, Revit's `847562`.*
- **Classification** — controlled-vocabulary terms drawn from the system's published namespace. Human-meaningful taxonomic labels. *Examples: IFC's `IfcColumn`, Revit's `Structural Columns` / `W14x90`, UniClass's `Ss_25_10_30`.*

These are different concerns: identity is opaque and must round-trip exactly; classification is published vocabulary that GUIs and tools render meaningfully. **The leaning of this comparison work is to route them to the two places that already exist for them:**

- Identity strings live in `assetInfo["source"][<system>]`.
- Classification facets are expressed as `UsdSemanticsLabelsAPI:<system>:<facet>` instances; the token-array values name the controlled-vocabulary terms.

The labels schema ships in OpenUSD 24.11+. **No new applied schema is required.**

A new applied schema for source identifiers would commit the AOUSD ecosystem to a recurring distribution-and-maintenance cost coordinated by the [AOUSD Build Interest Group](https://github.com/aousd/build-ig-initiatives). The leaning toward Labels + Identity therefore rests on a **scope** call — that source-identifier metadata is the controlled-vocabulary classification axis plus the opaque identity strings, not the wider typed-metadata surface that bundled formats (IFC `OwnerHistory`, AAS submodel `Property` values, URDF/SDF physical fields, ShotGrid datetimes/entity refs) carry alongside their identifiers.

This scope call is now stated explicitly because the empirical experiment that anchors it — `extras/sourceIdentifiers/details/field_classification_experiment.md`, added under this PR — does not support the broader form the docs previously asserted (*"no field surfaced needing typed non-token-array structure"*). A field census against the four verticals' authoritative spec surfaces (IFC4x3, Revit API, AAS metamodel, Windchill REST, SAP MARA, ROS/URDF/SDF, OpenAssetIO/OMC/ShotGrid) shows non-token-array typed structure surfacing in *every* vertical surveyed: timestamps, numeric measures with units, composite typed references, polymorphic-XSD AAS Property values. The narrower defensible finding is that **token arrays carry the controlled-vocabulary classification axis cleanly across all four verticals**, while non-token-array typed shapes are excluded by scope (treated as the asset's content, not its identifier metadata) — and that scope decision is the open question AOUSD review weighs.

*"Leaning"* rather than *"recommending"* because (a) a final mechanism choice belongs to AOUSD review of an eventual follow-up proposal, and (b) the leaning is conditional on the scope call above, which the proposal explicitly leaves open.

## What's in this PR

### The four candidates compared

Four mechanisms were exercised through the same battery of tests. All preserve round-trip fidelity for opaque identifier strings; they differ in where the identifier sits, how surrounding metadata is carried, and what new infrastructure (if any) they require.

- **A — `assetInfo` dictionaries.** Identifiers and any surrounding metadata nested under `assetInfo["sourceIds"]`. Status quo, refined.
- **B — Multi-apply schema with typed properties.** Each external system is one schema instance carrying typed `primaryId`, `revision`, `domain`, `label`. Domain-specific metadata requires companion schemas.
- **C — Refinement of B.** Same schema, plus `assetInfo` overflow for fields the schema can't carry.
- **D — Refinement of B: Labels + Identity.** The mechanism described in the Summary above — reuses `UsdSemanticsLabelsAPI` for classification, routes identity strings to `assetInfo`. **No new applied schema.**

A and B are the foundations; C and D are different cuts at B's gap on domain-specific metadata. The data leans toward D.

### Labels + Identity content

| Path | What it is |
|---|---|
| `examples/column_d.usda` | Canonical AECO column scenario |
| `examples/manufacturing_d.usda` | Tractor-assembly scenario; mirrors `manufacturing_a/b.usda` |
| `examples/robotics_d.usda` | Warehouse-fleet scenario; mirrors `robotics_a/b.usda` |
| `examples/verify_column_d.py` | Schema-aware verifier for `column_d.usda` against `UsdSemantics.LabelsAPI` |
| `vendor_simulation/approach_d_vendors.usda` | 8-vendor ecosystem simulation |
| `stress_tests/generate_approach_d.py` | Deterministic 100K-prim stress generator |

### Doc reframing across the comparison materials

- `COMPARISON.md` covers the four candidates across composition, discoverability, governance, industry verticals, file size, and vendor adoption scoring; §1 names the schema-formality / ecosystem-distribution tradeoff explicitly.
- `details/approach_descriptions.md` presents Labels + Identity alongside the others; C and D are framed as refinements of B.
- `details/composition_behavior.md` leads with *"composition behavior is effectively equivalent across the four approaches at the granularity authors actually use."*
- `details/governance.md` treats governance enforceability symmetrically across the four; §6.7 credits ecosystem distribution as the dominant cost; §6.8 covers what Labels + Identity collapses.
- `details/hybrid_analysis.md` positions C as the natural fallback if a domain surfaces fields needing typed non-token-array structure.
- `details/industry_scenarios.md` walks Labels + Identity fit per vertical; manufacturing borderline fields flagged.
- `details/stress_tests.md` carries real measurements and the eight-dimension scoring.
- `details/scope_promotion_simulation.md` notes that Labels + Identity collapses the multi-stage promotion path to a registry-level facet addition.
- `details/field_classification_experiment.md` — **NEW.** Pre-registered field census across IFC4x3, Revit API, AAS, Windchill, SAP MARA, ROS/URDF/SDF, OpenAssetIO/OMC/ShotGrid. Tests the "no field surfaced needing typed non-token-array structure" claim. Finds the broader form does not hold; states a narrower defensible form (token arrays carry the classification axis cleanly; non-token-array typed structure is a scope decision, not an absent requirement). Caveats every vertical's bucket counts.

### `details/formality_and_distribution.md` — the schema-ratification tradeoff

Names the eight formality benefits a schema-backed mechanism delivers (type validation, fallbacks, GUI integration, discoverability, typed accessors, versioning hooks, validator targeting, schema-driven property metadata). Decomposes the eight: six are met by reuse of an existing core schema (`UsdSemanticsLabelsAPI` in OpenUSD 24.11+); the other two (domain-calibrated fallbacks, domain-specific schema versioning) are what a new schema specifically adds.

Frames the recurring ecosystem-distribution cost as the dominant cost of ratifying a new applied schema. The matrix is real and currently fragmented across vendors who ship USD binaries; the AOUSD Build Interest Group coordinates the substrate it depends on (see [`aousd/build-ig-initiatives#28`](https://github.com/aousd/build-ig-initiatives/issues/28) parent epic on hosted OpenUSD binaries).

Closes with four open questions where AOUSD member input would sharpen the picture.

## Empirical measurements

### Field classification experiment (added under this PR)

Pre-registered four-bucket classification (Identity / Identity-adjacent / Classification — token-array fit / Classification — non-token-array typed structure), applied uniformly across the four verticals' authoritative spec surfaces.

Cross-vertical bucket totals (counting each *kind* of field once per system; not weighted by frequency in real stages):

| Vertical | Identity | Identity-adjacent | Classification — token-array fit | **Non-token-array typed structure** |
|---|---|---|---|---|
| AECO (12 main + 6 OwnerHistory) | 3 | 4 | 9 | 6 |
| Manufacturing/PLM (33) | 4 | 5 | 9 | 15+ |
| Robotics — strict (11) | 4 | 3 | 2 | 2 |
| Robotics — expanded URDF (15) | 2 | 0 | 1 | 12 |
| M&E (16) | 3 | 2 | 6 | 6 |

Recurring kinds of non-token-array typed structure that surface across verticals: **timestamps** (every vertical), **numeric measures with units** (AECO/PLM/Robotics), **composite typed references** (every vertical), **polymorphic-XSD typed values** (PLM canonical surface), **recursive composites** (PLM/Robotics/M&E).

Full field-by-field breakdown with citations: `extras/sourceIdentifiers/details/field_classification_experiment.md`.

### 100K-prim stress test

Deterministic seed (`stress_test_results.json`):

|  | A | B | C | D |
|---|---|---|---|---|
| File size (`.usda`) | 109.38 MB | 93.09 MB | 147.06 MB | **115.82 MB** |
| Line count | 3,085,417 | 2,020,995 | 3,583,150 | **3,094,533** |
| Namespace | 10 keys | 30 props | 30 props + 9 keys | **11 apiSchema instances + 11 label props + 9 keys** |

### Vendor adoption scoring (caveat)

Vendor adoption scoring across eight dimensions (initial adoption, distribution friction, per-prim/per-facet discoverability, metadata heterogeneity, validator implementability, composition for non-timevarying strings, file size):

**A=29, B=27, C=29, D=36**

Composition is scored 4/4/4/4 across all four because the experiments showed it's effectively equivalent for non-timevarying strings. Collision detection and governance enforceability are not among the dimensions because none of the mechanisms enforce uniqueness on their own — a registry-spec validator is needed under any approach.

**Caveat (added under this PR).** The eight scoring dimensions were constructed *after* the leaning toward D had taken shape. They have not yet been re-derived from the proposal's eight authorized principles (separation of concerns, industry agnosticism, vendor extensibility, composability, discoverability, external queryability, round-trip fidelity, minimal disruption) and explicit risks. The current scores should therefore be read as illustrative of the per-mechanism contrasts the experiments surfaced, not as an independent verdict. A re-derivation of dimensions from the authorized principles is part of the rebuild plan in [`project_source_identifier_rebuild`](../../) memory and is deferred to a session that can also address the distribution-friction tension flagged there.

## Schema-aware verification

`examples/verify_column_d.py` opens `column_d.usda` against a built USD and confirms:

```
Stage opened: examples/column_d.usda
Prim /Column_C14: type=Mesh valid=True
Applied schemas: 10
SemanticsLabelsAPI per (system, facet): 10 OK / 0 FAIL
  ifc:type, ifc:objectType, revit:category, revit:familyType,
  revit:mark, revit:level, uniclass:system, uniclass:title,
  omniclass:system, omniclass:title
assetInfo["source"][<system>]: 4 OK / 0 FAIL
FAILURES: 0
```

## Status of this work

The findings are intended to feed back into [`PixarAnimationStudios/OpenUSD-proposals#105`](https://github.com/PixarAnimationStudios/OpenUSD-proposals/pull/105) as use-case refinement, not to back-edit it. A final mechanism choice belongs to AOUSD review of an eventual follow-up proposal that adopts the framing the data is leaning toward. The empirical-first methodology — running each candidate through the same battery of reproducible tests — is itself a contribution this work intends to carry forward to other standards decisions in this space.

## Open questions

- **Borderline fields.** `displayNumber`, `mark`, `tag`-style strings — identity (in `assetInfo`) or classification (in labels)? Working rule under Labels + Identity: "if a tool needs the exact string to round-trip into the source system, it's identity; if it's a controlled-vocabulary term, it's a label."
- **Are opaque IDs really compatible with `assetInfo` long-term?** Labels + Identity relies on `assetInfo` for the identifier string. If `assetInfo` ever acquires structural constraints, the identifier strings would need a new home.
- **`apiSchemas` list scaling.** Labels + Identity inherits the linear-sift cost the physics workflows already feel. A cached per-kind index would benefit it; lacking one, consumers should expect linear scans.
- **AOUSD-member input on `formality_and_distribution.md` open questions.** Whether any verticals surface fields needing the new-schema-only benefits, whether bespoke fallback values are needed for any identifier domain, whether the distribution cost is felt differently across member contexts.
- **Where the identifier-package boundary sits.** The field experiment shows non-token-array typed structure (timestamps, numeric measures with units, composite refs, polymorphic AAS Properties) surfacing in every vertical surveyed. Whether those fields are *part of* source-identifier metadata or are the asset's *content* (out of scope for this mechanism) is the scope question the leaning toward Labels + Identity depends on. This is the question that most needs AOUSD-member input.

## Test plan

- [x] `examples/verify_column_d.py` — verifies `column_d.usda` parses against built USD with `UsdSemantics.LabelsAPI` (0 failures).
- [x] `stress_tests/generate_approach_d.py` — 100K-prim deterministic generator; reproducible.
- [x] `stress_tests/vendor_adoption_analysis.py` — scoring reproducible across A/B/C/D (subject to the dimensional-rebuild caveat above).
- [x] `details/field_classification_experiment.md` — pre-registered field census across the four verticals' authoritative specs; classification criteria and field-source rules committed before enumeration; cross-vertical bucket totals reproducible from the cited spec sections.

# Source Identifiers in OpenUSD: Comparison Review Guide

**Authors:** Aaron Luk (NVIDIA), Matt Kuruc (NVIDIA)
**Date:** May 2026
**Proposal:** [Separation of Concerns for Identifiers in USD](../../OpenUSD-proposals/proposals/identifier_separation_of_concerns/README.md)

---

## Executive Summary

OpenUSD has no shared mechanism for carrying external source identifiers — IFC
GlobalIds, Revit ElementIds, Windchill OIDs, ROS package URIs — that travel
with prims. Current practice is `customData`: unscoped, untyped, and fragmented
per vendor. This document compares four mechanisms for fixing that.

All four preserve **round-trip fidelity** for opaque identifier strings; they
differ in where the identifier sits, how surrounding metadata is carried, and
what new infrastructure (if any) they require.

### The four approaches

**A — `assetInfo` dictionaries.** Identifiers and any surrounding metadata
nested under `assetInfo["sourceIds"]`. A non-applied API schema
(`UsdSourceIdAPI`) provides convenience access. No new applied schema.

**B — Multi-apply schema with typed properties.** Each external system is one
schema instance (`SourceIdSchemaAPI:windchill`), carrying typed properties
`primaryId`, `revision`, `domain`, `label`. Domain-specific metadata requires
companion schemas or falls back to `customData`.

**C — Hybrid (B + assetInfo overflow).** Multi-apply schema for the four common
fields plus `assetInfo` overflow dictionaries for domain-specific metadata.

**D — Labels + Identity.** `SemanticsLabelsAPI` (shipping in 24.11) for
classification facets (IFC type, Revit category/familyType/mark/level, UniClass
codes); `assetInfo["source"][<system>]` for the opaque identifier string and
optional version. **No new applied schema.**

### Recommendation: Adopt D

D uses only schemas that ship today, decomposes the problem along its natural
seams (identity vs. classification), and provides finer-grained discoverability
via per-facet `apiSchemas` instances than B or C can offer. The case for a new
multi-apply schema (B/C) was that schemas give type safety, fallback values,
GUI integration, and structural governance hooks. Once `SemanticsLabelsAPI`
carries the classification work, the residual case for B/C over D is
insufficient to justify the schema-distribution friction of a new ratified
multi-apply schema.

The remainder of this document presents the same prim in all four forms,
honestly compares composition / discoverability / governance / industry
scenarios, and identifies the open questions D still leaves on the table.

---

## Decisions for TAC

1. **Mechanism choice.** Adopt D, B/C, or status quo (A / `customData`)?
   → Evidence: §3 below.

2. **Domains Registry.** Establish an AOUSD Domains Registry (modeled on
   Khronos glTF prefix reservation and W3C Community Group creation) for
   vendor namespace coordination, regardless of mechanism choice?
   → Evidence: §3.3 Governance.

3. **Borderline fields.** Where do fields that sit between identity and
   classification go (e.g., Windchill `displayNumber`, `state`,
   `lifecyclePhase`)? D's working rule: identity strings → `assetInfo`;
   controlled-vocabulary terms → `SemanticsLabelsAPI`. The TAC should
   validate this split.

---

## Methodology

Each approach was exercised through the same battery of empirical tests rather
than evaluated by argument. The experiments and their data are in this
repository and reproducible:

| Experiment | Question | Where the data lives |
|---|---|---|
| Composition tests | Does an override layer behave predictably? | `examples/composition_test_*.usda`, `verify_composition.py` |
| Industry verticals | Can each approach carry each industry's actual metadata? | `examples/{approach_*,manufacturing_*,robotics_*,column_*}.usda` |
| 8-vendor simulation | What does a heterogeneous ecosystem look like? | `vendor_simulation/approach_*_vendors.usda` |
| 100K-prim stress test | What's the file-size, line-count, and namespace cost at scale? | `stress_tests/generate_approach_*.py`, `stress_test_results.json` |
| Vendor adoption scoring | What does a new vendor face under each approach? | `stress_tests/vendor_adoption_analysis.{py,json}` |
| Scope promotion lifecycle | Does the overflow → schema graduation path work end-to-end? | `examples/scope_promotion/` |
| Schema-aware verification of D | Does `column_d.usda` apply `UsdSemantics.LabelsAPI` and round-trip? | `examples/verify_column_d.py` |

All numbers in §3 below are reproduced from `stress_test_results.json`
(deterministic seed, 100,000 prims).

The empirical-first approach to a standards decision is itself a contribution
of this work — recommendations should be reproducible from data, not
argument. Several claims that an opinion-only comparison might assert
optimistically about schemas (structural collision detection, governance
enforceability by mechanism, composition safety for non-timevarying strings)
do not survive the experiments and are treated as symmetric across
mechanisms below.

---

## The Four Approaches: One Prim, Four Forms

A structural column carries identifiers and classification metadata from four
external systems: IFC, Revit, UniClass, OmniClass.

### A — `assetInfo` dictionaries

```usda
def Mesh "Column_C14" (
    assetInfo = {
        dictionary sourceIds = {
            dictionary ifc = {
                string identifier = "2O2Fr$t4X7Zf8NOew3FNr2"
                string type = "IfcColumn"
                string objectType = "W14x90"
            }
            dictionary revit = {
                string identifier = "847562"
                string version = "2026.1"
                string category = "Structural Columns"
                string familyType = "W14x90"
                string mark = "C-14"
                string level = "Level 3"
            }
            dictionary uniclass = {
                string identifier = "Ss_25_10_30"
                string system = "Uniclass 2015"
                string title = "Column systems"
            }
            dictionary omniclass = {
                string system = "OmniClass"
                string title = "Structural Steel Columns"
            }
        }
    }
)
{
}
```

### B — Multi-apply schema with typed properties

```usda
def Mesh "Column_C14" (
    apiSchemas = ["SourceIdSchemaAPI:ifc",
                  "SourceIdSchemaAPI:revit",
                  "SourceIdSchemaAPI:uniclass",
                  "SourceIdSchemaAPI:omniclass"]
)
{
    string sourceIdentifier:ifc:primaryId = "2O2Fr$t4X7Zf8NOew3FNr2"
    token  sourceIdentifier:ifc:domain    = "org.buildingsmart.ifc"
    string sourceIdentifier:ifc:label     = "IFC GlobalId"
    # IFC type / objectType cannot be expressed without a companion schema.

    string sourceIdentifier:revit:primaryId = "847562"
    string sourceIdentifier:revit:revision  = "2026.1"
    token  sourceIdentifier:revit:domain    = "com.autodesk.revit"
    string sourceIdentifier:revit:label     = "Revit ElementId"
    # category / familyType / mark / level cannot be expressed without a companion schema.

    # uniclass / omniclass: same gap.
}
```

B's typed common fields work cleanly for the identifier itself, but the
classification metadata each domain carries (IFC type, Revit category, etc.)
has nowhere to live without per-domain companion schemas or `customData`.

### C — Hybrid (B + assetInfo overflow)

```usda
def Mesh "Column_C14" (
    apiSchemas = ["SourceIdHybridAPI:ifc", "SourceIdHybridAPI:revit",
                  "SourceIdHybridAPI:uniclass", "SourceIdHybridAPI:omniclass"]
    assetInfo = {
        dictionary sourceIds = {
            dictionary ifc      = { string type = "IfcColumn"
                                    string objectType = "W14x90" }
            dictionary revit    = { string category = "Structural Columns"
                                    string familyType = "W14x90"
                                    string mark = "C-14"
                                    string level = "Level 3" }
            dictionary uniclass = { string system = "Uniclass 2015"
                                    string title = "Column systems" }
            dictionary omniclass = { string system = "OmniClass"
                                     string title = "Structural Steel Columns" }
        }
    }
)
{
    string sourceIdentifier:ifc:primaryId   = "2O2Fr$t4X7Zf8NOew3FNr2"
    token  sourceIdentifier:ifc:domain      = "org.buildingsmart.ifc"
    # ... typed common fields for revit / uniclass / omniclass omitted for brevity
}
```

### D — Labels + Identity

```usda
def Mesh "Column_C14" (
    apiSchemas = ["SemanticsLabelsAPI:ifc:type",        "SemanticsLabelsAPI:ifc:objectType",
                  "SemanticsLabelsAPI:revit:category",  "SemanticsLabelsAPI:revit:familyType",
                  "SemanticsLabelsAPI:revit:mark",      "SemanticsLabelsAPI:revit:level",
                  "SemanticsLabelsAPI:uniclass:system", "SemanticsLabelsAPI:uniclass:title",
                  "SemanticsLabelsAPI:omniclass:system","SemanticsLabelsAPI:omniclass:title"]
    assetInfo = {
        dictionary source = {
            dictionary ifc       = { string identifier = "2O2Fr$t4X7Zf8NOew3FNr2" }
            dictionary revit     = { string identifier = "847562"
                                     string version = "2026.1" }
            dictionary uniclass  = { string identifier = "Ss_25_10_30" }
            dictionary omniclass = {}
        }
    }
)
{
    token[] semantics:labels:ifc:type         = ["IfcColumn"]
    token[] semantics:labels:ifc:objectType   = ["W14x90"]
    token[] semantics:labels:revit:category   = ["Structural Columns"]
    token[] semantics:labels:revit:familyType = ["W14x90"]
    token[] semantics:labels:revit:mark       = ["C-14"]
    token[] semantics:labels:revit:level      = ["Level 3"]
    token[] semantics:labels:uniclass:system  = ["Uniclass 2015"]
    token[] semantics:labels:uniclass:title   = ["Column systems"]
    token[] semantics:labels:omniclass:system = ["OmniClass"]
    token[] semantics:labels:omniclass:title  = ["Structural Steel Columns"]
}
```

D decomposes the problem into two axes: **identity** (the opaque pointer back
into the source system, in `assetInfo`) and **classification** (taxonomic
terms drawn from controlled vocabularies, on `SemanticsLabelsAPI` instances).
The `apiSchemas` list reads as the human-meaningful inventory of which
external classifications this prim carries — finer-grained than B/C's
per-system instances.

→ Runnable: [examples/column_d.usda](examples/column_d.usda)

---

## Findings

### 3.1 Composition Behavior

For non-timevarying strings — which describes all identifier and most
classification metadata — composition behavior is **effectively equivalent**
across the four approaches at the granularity authors actually use: override
one identifier or one label, leave others alone, and the composed result is
what you expect.

The narrow case where dictionaries differ from properties is round-trip
serialization: a tool that reads the composed `assetInfo` value and writes
the whole dictionary back can shadow base-layer keys it didn't intend to
override. This is a real hazard for tool authors but not a structural
property difference — careful tools avoid it, careless tools produce the
same hazard with any composed-value-rewrite pattern.

The genuine composition differences are:

- **Per-field fallback values via `UsdPrimDefinition`.** Schema properties
  carry defaults; dictionary keys do not. This favors B/C/D's schema content
  but doesn't apply to `assetInfo` either way.
- **Schema-driven property metadata** (kind, doc strings, allowed values)
  usable by GUIs and validators.

Both differences favor schemas over dictionaries — but D gets them via
`SemanticsLabelsAPI` (already shipping) without ratifying anything new.

→ Deep dive: [details/composition_behavior.md](details/composition_behavior.md)

### 3.2 Discoverability

| Question | A | B | C | D |
|---|---|---|---|---|
| What external systems are on this prim? | Parse `assetInfo` | Read `apiSchemas` (per-system) | Read `apiSchemas` (per-system) | Read `apiSchemas` (per-facet) |
| Does this prim have a Revit category? | Parse `assetInfo` | N/A (no companion schema) | Parse `assetInfo` overflow | Read `apiSchemas`, filter `revit:category` |
| What classification facets does Revit carry? | Parse `assetInfo` | N/A | Parse `assetInfo` overflow | Read `apiSchemas`, filter `revit:*` |

D's per-facet `apiSchemas` instances answer classification queries from the
schemas list alone. B and C's per-system instances require parsing into the
dict (C) or are silent on classification (B).

A caveat from physics workflows: the unified `apiSchemas` list mixes all
applied schemas (collections, light linking, identifiers, labels) without a
cached per-kind index, so "find the schema I care about" is linear in total
applied-schema count. The penalty applies to B/C/D symmetrically — but D's
per-facet granularity at least returns precisely the facet asked for, rather
than a system instance whose surrounding metadata still needs dict parsing.

### 3.3 Governance & Validation

Schema-based discoverability does not, by itself, enforce anything. Authors
can list arbitrary strings under `apiSchemas` (including names of schemas
that aren't installed on the consumer); dict-based authors can pick arbitrary
domain keys. **Governance is symmetric across the four approaches; the
difference is what a registry-spec validator has to parse.**

| Validator task | A | B | C | D |
|---|---|---|---|---|
| Enumerate identifiers | Walk `assetInfo` | `GetAll()` | `GetAll()` + walk overflow | `GetAll()` per facet |
| Verify domain is registered | Check dict key | Check `domain` token | Check `domain` token | Check apiSchema instance system |
| Verify facet is registered | Same | N/A | Walk overflow keys | Check apiSchema instance facet |
| Detect colliding domain claims | Compare dict keys | Compare `domain` tokens | Compare both | Compare apiSchema instance names |

All four are buildable as CI validators against an AOUSD Domains Registry.
D's structure exposes both system and facet on the schemas list, which
simplifies the validator implementation.

**The Domains Registry recommendation stands regardless of mechanism choice.**
A three-tier model (vendor → multi-vendor → AOUSD-standard) modeled on
Khronos glTF's `Prefixes.md` and W3C's Community Group → Working Group →
Recommendation provides namespace coordination without imposing approval
authority. The registry is administrative, not evaluative — vendors who
prefer zero coordination can still author whatever they want; the registry
gives validators something to check against.

→ Deep dive: [details/governance.md](details/governance.md)

### 3.4 Industry Scenarios

Four verticals were tested across the four approaches.

- **AECO** (the canonical column above): A handles all metadata in dicts;
  B requires companion schemas for IFC type, Revit category/familyType/
  mark/level, UniClass/OmniClass codes; C absorbs them into overflow; D
  routes them to `SemanticsLabelsAPI` instances cleanly because they
  *are* taxonomic labels.
- **Manufacturing** (Windchill, SAP): the hardest test for D. Identifier
  strings (OID, material number) and `displayNumber` go to `assetInfo`.
  Lifecycle metadata (`state`, `lifecyclePhase`) is controlled-vocabulary
  and rides `SemanticsLabelsAPI`. `revision` is per-system in `assetInfo`.
  7 of 8 simulated PLM/ERP fields fit cleanly; the remaining one
  (`navigationType`, an opaque PTC query string) is identity-adjacent and
  goes to `assetInfo`.
- **Robotics** (ROS, fleet): URDF/SDF source provenance is a label
  (`semantics:labels:ros:sourceFormat`); ROS frame IDs are identifiers in
  `assetInfo`; sensor datasheet revision is per-system in `assetInfo`.
- **M&E**: model-level asset DB IDs are identifiers in `assetInfo`; little
  significant classification metadata in this vertical, so the `apiSchemas`
  list stays small.

The split test — does this field belong to identity or classification? —
turns out to be tractable in every vertical. **Identifier strings and
versions are identity. Type names, categories, lifecycle states, and
classification codes are labels.** Borderline fields are listed in
[Decisions for TAC](#decisions-for-tac).

→ Deep dive: [details/industry_scenarios.md](details/industry_scenarios.md)

### 3.5 File Size & Namespace Footprint

100K-prim stress test, text-format `.usda`, deterministic seed
(re-runnable via `python3 stress_tests/generate_approach_{a,b,c,d}.py`):

| | A | B | C | D |
|---|---|---|---|---|
| File size | 109.38 MB | 93.09 MB | 147.06 MB | **115.82 MB** |
| Line count | 3,085,417 | 2,020,995 | 3,583,150 | **3,094,533** |
| Namespace footprint | 10 dict keys | 30 properties | 30 props + 9 keys | **11 apiSchema instances + 11 label props + 9 keys** |
| Generation time | 7.7 s | 2.9 s | 8.8 s | **6.2 s** |

D sits between A and C: smaller than C (no per-system schema instances inflating
`apiSchemas`), larger than B (token arrays + per-facet apiSchema instances
add roughly the same overhead as C's overflow dictionaries). In binary `.usdc`
the relative ordering is preserved but absolute differences narrow substantially
(3–5× compression on attribute-heavy content). File size is not a load-bearing
differentiator.

→ Deep dive: [details/stress_tests.md](details/stress_tests.md)

### 3.6 Vendor Adoption Scoring

Eight dimensions, scored 1–5, summarizing the experiments above. Collision
detection and governance enforceability are treated as symmetric across
mechanisms (none enforce uniqueness on their own — a registry-spec validator
must run under any approach), and composition is treated as equivalent for
non-timevarying strings.

| Dimension | A | B | C | D |
|---|---|---|---|---|
| Initial adoption friction (fewer steps = higher) | 5 | 4 | 4 | 4 |
| Distribution friction (no new schema = higher) | 5 | 2 | 2 | 5 |
| Per-prim discoverability (what systems on this prim) | 2 | 4 | 4 | 5 |
| Per-facet discoverability (what facet of which system) | 2 | 2 | 3 | 5 |
| Metadata heterogeneity (carries arbitrary domain data) | 5 | 2 | 5 | 4 |
| Validator implementability (registry-spec compliance) | 2 | 4 | 4 | 5 |
| Composition for typical edits (non-timevarying strings) | 4 | 4 | 4 | 4 |
| File size cost (smaller = higher) | 4 | 5 | 3 | 4 |
| **Total (max 40)** | **29** | **27** | **29** | **36** |

D leads on discoverability and distribution: per-facet `apiSchemas` instances
expose more structure than the alternatives without requiring a new schema to
ship. A and C tie on total because each compensates for B's weakness on
heterogeneity (A via freeform dicts, C via overflow). B is lowest because
its fixed four-property surface cannot carry the metadata that real domains
ship.

→ Deep dive: [details/stress_tests.md §5.3](details/stress_tests.md) (full
methodology and weight rationale)

---

## Why D Over C

C — a multi-apply schema with `assetInfo` overflow — is a defensible synthesis
on its own terms: schemas give type safety, fallback values, GUI integration,
and structural governance hooks; freeform dictionaries give flexibility for
domain metadata; the hybrid takes both.

The case for D rather than C turns on what `SemanticsLabelsAPI` already
provides:

1. **The "schemas give type safety" case applies to D too.** D uses
   `SemanticsLabelsAPI` token arrays — typed, schema-validated,
   GUI-discoverable. Identifier strings sit in `assetInfo`, but those are
   strings either way (a typed `string sourceIdentifier:revit:primaryId`
   schema property and a `string identifier` dict key carry equivalent
   round-trip semantics for non-timevarying content).

2. **The four common fields dissolve.**
   - `domain` ≡ apiSchema instance system name (`revit`).
   - `label` ≡ apiSchema instance facet (`revit:familyType`) plus the
     registered domain's display label.
   - `revision` is per-system in `assetInfo` because not every system has
     a revision concept.
   - `primaryId` is the `identifier` dict key in `assetInfo`.
   None of these need a new schema.

3. **No new ratification path.** B/C require AOUSD to ratify a new
   multi-apply schema, codegen it, distribute the plugin, and manage its
   versioning forever. D ratifies a Domains Registry — a spec document —
   and reuses an applied schema that already ships.

4. **Per-facet granularity is finer than per-system.** B/C's
   `SourceIdSchemaAPI:revit` instance is opaque about *which* Revit
   metadata is present; D's `SemanticsLabelsAPI:revit:familyType` /
   `SemanticsLabelsAPI:revit:mark` instances tell the consumer exactly
   which facets are authored, queryable from `apiSchemas` alone.

C remains documented in `pxr/usd/usdSourceIdHybrid/` as a reference
implementation. If experience with D surfaces classification fields that
genuinely need typed structured shape (a numeric tolerance, a date range)
rather than token-array labels, C's overflow pattern remains the obvious
fallback — but no such field has been identified across the four verticals
tested.

---

## Open Questions

1. **Borderline fields.** `displayNumber`, `mark`, `tag`-style strings —
   identity (in `assetInfo`) or classification (in labels)? Working rule:
   "if a tool needs the exact string to round-trip into the source system,
   it's identity; if it's a controlled-vocabulary term meaningful to
   humans, it's a label." TAC validation requested.

2. **AAS type-vs-instance scoping.** AAS `globalAssetId` (type-level)
   vs. `specificAssetIds` (instance-level) maps cleanly under D as two
   separate `SemanticsLabelsAPI` facets per system (`aas:globalAssetId`,
   `aas:specificAssetId`) plus per-instance `assetInfo` entries.
   Promotion of `scope` from a domain-specific convention to a
   recognized facet is a registry-level addition under D — no schema
   property migration. The
   [scope promotion simulation](details/scope_promotion_simulation.md)
   documents the harder C-tier path for reference.

3. **Are opaque IDs really compatible with `assetInfo` long-term?** D
   relies on `assetInfo` for the identifier string. If `assetInfo` ever
   acquires structural constraints (typed schema, validation), the
   identifier strings would need a new home. Hypothetical under current
   OpenUSD direction, but worth flagging.

4. **`apiSchemas` list scaling.** The unified `apiSchemas` list grows
   linearly under D (facets × systems × prims). Physics workflows already
   feel this for collections and light linking. A cached per-kind index in
   `UsdPrim` or a registry-spec convention for filtering would benefit D;
   lacking one, consumers should expect linear scans.

---

## Repository Map

All implementations and test data live in this repository under
`pxr/usd/usdSourceId*` (the three reference implementations) and
`extras/sourceIdentifiers/`.

```
pxr/usd/
├── usdSourceId/           # Approach A — non-applied schema wrapping assetInfo
├── usdSourceIdSchema/     # Approach B — multi-apply schema with typed properties
└── usdSourceIdHybrid/     # Approach C — hybrid (kept as reference implementation)

extras/sourceIdentifiers/
├── COMPARISON.md                    ← this document
├── details/                         ← deep dives (composition, scenarios, stress tests,
│                                      governance, hybrid analysis, scope promotion)
├── examples/
│   ├── approach_a_assetinfo.usda    # AECO building (A)
│   ├── approach_b_schema.usda       # AECO building (B)
│   ├── approach_c_hybrid.usda       # AECO building (C)
│   ├── column_d.usda                # AECO column (D — Labels + Identity)
│   ├── manufacturing_a.usda / _b.usda
│   ├── robotics_a.usda / _b.usda
│   └── verify_composition.py
├── vendor_simulation/               # 8-vendor stress test inputs
└── stress_tests/                    # 100K-prim generator + measurements
```

D requires no new schema library — it composes `UsdSemanticsLabelsAPI` (in
OpenUSD as of 24.11) with `assetInfo` conventions. `examples/column_d.usda`
demonstrates the full pattern with no build step required;
`examples/verify_column_d.py` validates that it parses, applies the schemas,
and round-trips through the `UsdSemantics.LabelsAPI` Python API.

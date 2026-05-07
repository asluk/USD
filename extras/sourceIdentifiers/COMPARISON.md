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

### Two foundations and two refinements

**A — `assetInfo` dictionaries.** The status quo, refined. Identifiers and
any surrounding metadata nested under `assetInfo["sourceIds"]`. A
non-applied API schema (`UsdSourceIdAPI`) provides convenience access.
No new applied schema.

**B — Multi-apply schema with typed properties.** The schema-based mechanism
in its purest form. Each external system is one schema instance
(`SourceIdSchemaAPI:windchill`), carrying typed properties `primaryId`,
`revision`, `domain`, `label`. Domain-specific metadata requires companion
schemas or falls back to `customData`.

**C — Refinement of B.** Same multi-apply schema, plus `assetInfo` overflow
(borrowed from A) for fields the four common properties cannot carry.
Closes B's heterogeneity gap by carrying both mechanisms.

**D — Refinement of B (Labels + Identity).** Operationalizes the
proposal's separation-of-concerns framing by routing two distinct
concerns to two places already designed for them. **Identity** — the
opaque string that round-trips back into the source system (IFC's
`2O2Fr$t4X7Zf8NOew3FNr2`, Windchill's `VR:wt.part.WTPart:23639563`,
Revit's `847562`) — lives in `assetInfo["source"][<system>]`.
**Classification** — controlled-vocabulary terms each system publishes
alongside the identifier (`IfcColumn`, `Structural Columns`, `W14x90`,
`Ss_25_10_30`) — is expressed as `UsdSemanticsLabelsAPI:<system>:<facet>`
instances with values in `token[]` properties. The labels API ships in
OpenUSD 24.11+; **no new applied schema required.**

A and B are the two foundations; C and D are different cuts at B's gap on
domain-specific metadata.

### Where the data leans

The data leans toward **D** — the refinement of B that uses the existing
`UsdSemanticsLabelsAPI` rather than introducing a new multi-apply schema.
D operationalizes the proposal's separation-of-concerns framing along the
identity vs. classification seam: identity strings (the opaque round-trip
pointers back into the source system) live in `assetInfo`; classification
facets (the controlled-vocabulary terms each system publishes alongside
the identifier) are expressed via existing semantic-labels machinery. D
also exposes finer-grained structure via per-facet `apiSchemas` instances
than B or C. The case for a new multi-apply schema (B/C) rested on type
safety, fallback values, GUI integration, and structural governance hooks;
once `UsdSemanticsLabelsAPI` carries the classification work, those
benefits are available without a new ratified schema to distribute.

The schema-distribution side of this lean isn't a friction-margin
observation. Schemas provide eight real formality benefits (type
validation, fallbacks, GUI integration, discoverability, typed
accessors, versioning hooks, validator targeting, schema-driven
property metadata); a new applied schema commits the ecosystem to a
recurring distribution-and-maintenance matrix the AOUSD Build Interest
Group coordinates. Reusing `UsdSemanticsLabelsAPI` delivers six of
those eight without that commitment; what a new schema adds beyond
reuse (domain-calibrated fallbacks, domain-specific schema versioning)
didn't show up as decisive across the four verticals tested. Both
sides set out, with the AOUSD-member input the leaning still wants,
in [details/formality_and_distribution.md](details/formality_and_distribution.md).

A final mechanism choice belongs to the AOUSD review process and an
eventual follow-up proposal, not to this exploratory work. The remainder
of this document presents the same prim in all four forms, compares
composition / discoverability / governance / industry scenarios, and
identifies the open questions the leaning still leaves on the table.

---

## Open questions for AOUSD review

1. **Mechanism choice.** Does the leaning toward D (refinement of B via
   `UsdSemanticsLabelsAPI`) hold against the verticals AOUSD members
   prioritize? B, C, and the status quo (A / `customData`) all remain
   on the table for cases where D's classification fit is awkward.
   → Evidence: §3 below.

2. **Domains Registry.** Whatever mechanism is adopted, does an AOUSD
   Domains Registry — modeled on Khronos glTF prefix reservation and
   W3C Community Group creation — for vendor namespace coordination
   make sense?
   → Evidence: §3.3 Governance.

3. **Borderline fields.** Where do fields that sit between identity and
   classification go (e.g., Windchill `displayNumber`, `state`,
   `lifecyclePhase`)? Working rule under D: identity strings →
   `assetInfo`; controlled-vocabulary terms → `SemanticsLabelsAPI`.
   Worth pressure-testing against AOUSD members' source systems.

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
[Open questions for AOUSD review](#open-questions-for-aousd-review).

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
(3–5× compression on attribute-heavy content). File size is not a deciding
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

## Where the data leans toward D's refinement over C's

C and D are both refinements of B. Both close B's heterogeneity gap; they
differ in *how*. C keeps the new multi-apply schema and adds `assetInfo`
overflow (borrowed from A). D drops the new schema in favor of the
existing `UsdSemanticsLabelsAPI` and routes identifier strings to
`assetInfo`.

Where the data leans toward D's cut:

1. **The "schemas give type safety" benefit applies to D too.** D uses
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

3. **No new ratification path.** C still requires AOUSD to ratify a new
   multi-apply schema, codegen it, distribute the plugin, and manage its
   versioning forever. D's refinement reuses an applied schema that
   already ships and adds a Domains Registry — a spec document — instead.

4. **Per-facet granularity is finer than per-system.** C's
   `SourceIdHybridAPI:revit` instance is opaque about *which* Revit
   metadata is present; D's `SemanticsLabelsAPI:revit:familyType` /
   `SemanticsLabelsAPI:revit:mark` instances tell the consumer exactly
   which facets are authored, queryable from `apiSchemas` alone.

C's reference implementation lives in `pxr/usd/usdSourceIdHybrid/`. If
experience with D surfaces classification fields that genuinely need typed
structured shape (a numeric tolerance, a date range) rather than
token-array labels, C's overflow pattern is the natural fallback — but
no such field has been identified across the four verticals tested.

---

## Open Questions

1. **Borderline fields.** `displayNumber`, `mark`, `tag`-style strings —
   identity (in `assetInfo`) or classification (in labels)? Working rule:
   "if a tool needs the exact string to round-trip into the source system,
   it's identity; if it's a controlled-vocabulary term meaningful to
   humans, it's a label." Worth pressure-testing in AOUSD review.

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

## Status of this work

The findings here are early and still being refined. They are intended to
feed back into [PixarAnimationStudios/OpenUSD-proposals#105](https://github.com/PixarAnimationStudios/OpenUSD-proposals/pull/105)
as use-case refinement, not to back-edit it; a final mechanism choice
belongs to AOUSD review of an eventual follow-up proposal that adopts the
framing the data is leaning toward. The empirical-first methodology
itself — running each candidate through the same battery of reproducible
tests — is a contribution this work intends to carry forward to other
standards decisions in this space.

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
│                                      governance, hybrid analysis, scope promotion,
│                                      formality and distribution)
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

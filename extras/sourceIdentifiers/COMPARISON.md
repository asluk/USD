# Source Identifiers in OpenUSD: Comparison Review Guide

**Authors:** Aaron Luk (NVIDIA), Matt Kuruc (NVIDIA)
**Date:** May 2026
**Proposal:** [Separation of Concerns for Identifiers in USD](../../OpenUSD-proposals/proposals/identifier_separation_of_concerns/README.md)

---

> ## Caveats for readers (including agents)
>
> Two items are **deferred to a follow-up session** and are
> load-bearing for any conclusion drawn from this document:
>
> 1. **The eight-dimension vendor-adoption scoring** in §3.6 (and the
>    methodology in `details/stress_tests.md` §5.3) was constructed
>    *after* a prior leaning toward Approach D had already taken shape.
>    It has not been re-derived from the proposal's eight authorized
>    principles. Read the scores as illustrative, not as a verdict.
> 2. **The distribution-friction tension is unresolved.** The
>    elevation of distribution to "the dominant cost" in
>    `details/formality_and_distribution.md` conflicts with the
>    proposal's original B-cons phrasing. Resolution is upstream of
>    any honest mechanism choice.
>
> A prior framing of this comparison leaned toward Approach D (Labels
> + Identity). **That leaning has been retracted** in light of the
> field census in `details/field_classification_experiment.md`, which
> shows identifier packages are heterogeneously typed across all four
> verticals surveyed. The document presents the four candidates and
> the empirical evidence symmetrically; **no mechanism leaning is
> asserted** in this revision.
>
> **Share-readiness:** This document is not yet ready to recirculate
> broadly (additional NVIDIA reviewers, Matt, or AOUSD members) until
> the two deferred items resolve. The empirical census stands on its
> own; the comparison framing around it does not.

---

## Executive Summary

OpenUSD has no shared mechanism for carrying external source identifiers — IFC
GlobalIds, Revit ElementIds, Windchill OIDs, ROS package URIs — that travel
with prims. Current practice is `customData`: unscoped, untyped, and fragmented
per vendor. This document compares four mechanisms for fixing that.

All four preserve **round-trip fidelity** for opaque identifier strings; they
differ in where the identifier sits, how surrounding metadata is carried, and
what new infrastructure (if any) they require.

### The four candidates

**A — `assetInfo` dictionaries.** Status quo, refined. Identifiers and any
surrounding metadata nested under `assetInfo["sourceIds"]`. A non-applied API
schema (`UsdSourceIdAPI`) provides convenience access. No new applied schema.
*Authorized in proposal 105 as Approach A.*

**B — Multi-apply schema with typed properties.** Each external system is one
schema instance (`SourceIdSchemaAPI:windchill`), carrying typed properties
`primaryId`, `revision`, `domain`, `label`. Domain-specific metadata requires
companion schemas or falls back to `customData`. *Authorized in proposal 105
as Approach B.*

**C — Refinement of B.** Same multi-apply schema, plus `assetInfo` overflow
(borrowed from A) for fields the four common properties cannot carry.
*Hinted at in proposal 105 as a "hybrid or alternative."*

**D — Refinement of B (Labels + Identity).** Reuses the existing
`UsdSemanticsLabelsAPI` for controlled-vocabulary classification facets and
routes identifier strings to `assetInfo["source"][<system>]`. **No new
applied schema required.** *Constructed downstream of the proposal during
the comparison work; included as an explored idea, not a peer candidate the
proposal itself authorized.*

A and B are the two foundations the proposal authorized. C and D are
different cuts at B's gap on domain-specific metadata.

### What the empirical work shows about identifier-package shape

[`details/field_classification_experiment.md`](details/field_classification_experiment.md)
reports a pre-registered field census against authoritative spec surfaces in
the four verticals (IFC4x3, Revit API, AAS metamodel, Windchill REST, SAP MARA,
ROS/URDF/SDF, OpenAssetIO/MovieLabs OMC/ShotGrid). Bucket totals:

| Vertical | Identity | Identity-adjacent | Controlled-vocabulary classification | **Heterogeneous typed fields** |
|---|---|---|---|---|
| AECO (12 main + 6 OwnerHistory) | 3 | 4 | 9 | 6 |
| Manufacturing/PLM (33) | 4 | 5 | 9 | 15+ |
| Robotics — strict (11) | 4 | 3 | 2 | 2 |
| Robotics — expanded URDF (15) | 2 | 0 | 1 | 12 |
| M&E (16) | 3 | 2 | 6 | 6 |

**The empirical finding:** identifier packages are heterogeneously typed in
every vertical surveyed — timestamps are universal; numeric measures with
units appear in AECO, PLM, and Robotics; composite typed references are
universal; polymorphic XSD-typed values are the standard surface in AAS.

This is the heterogeneity tension proposal 105 already framed in B's cons:
*"the more heterogeneous the contents, the more this tension favors
dictionaries or a family of domain-specific schemas."* The empirical
surface confirms that tension is real; it does not by itself pick a
mechanism.

### How the four candidates relate to the empirical surface

| Mechanism | Carries heterogeneous typed fields? |
|---|---|
| **A — `assetInfo` dictionaries** | Yes — freeform dicts admit any typed shape, at the cost of no schema-side typing or discoverability. |
| **B — Four-property typed schema** | No — the fixed surface cannot carry domain-specific typed fields without companion schemas per domain. |
| **C — B + `assetInfo` overflow** | Yes — typed schema for the common fields, freeform-dict overflow for everything heterogeneous. |
| **D — `UsdSemanticsLabelsAPI` + `assetInfo` identity strings** | No — labels carry `token[]`; identifier strings are `string`; numeric, date, composite-reference, and polymorphic typed shapes have no slot. |

**A and C accommodate the empirical heterogeneity surface. D and B-alone do
not, as complete answers.** Earlier framings of this comparison leaned toward
D on the assertion that *"no domain-specific field surfaced needing typed
non-token-array structure"* across the four verticals. The field census does
not support that assertion. **No mechanism leaning is asserted in this
revision of the comparison.** The remainder of this document presents the
same prim in all four forms, compares composition / discoverability /
governance / industry scenarios, and identifies the open questions
mechanism choice still depends on.

---

## Open questions for AOUSD review

1. **Where the identifier-package boundary sits.** The field experiment
   shows heterogeneous typed fields (timestamps, numeric measures with
   units, composite refs, polymorphic AAS Properties) surfacing in every
   vertical surveyed. Are those fields *part of* source-identifier
   metadata, or are they the asset's *content* (out of scope for this
   mechanism)? The current materials assumed the narrower scope without
   arguing for it; a follow-up proposal has to argue the boundary.
   → Evidence: `details/field_classification_experiment.md`.

2. **Mechanism choice.** A and C accommodate the heterogeneity surface;
   B-with-companion-schemas remains a third possibility the proposal
   authorized. The structure-vs-freeform tradeoff between A and C is
   downstream of this experiment and depends on the AOUSD review's
   judgment about adoption velocity, discoverability, and the
   distribution-and-maintenance cost of any schema ratification.
   → Evidence: §3 below; `details/formality_and_distribution.md`.

3. **Domains Registry.** Whatever mechanism is adopted, does an AOUSD
   Domains Registry — modeled on Khronos glTF prefix reservation and
   W3C Community Group creation — for vendor namespace coordination
   make sense?
   → Evidence: §3.3 Governance.

4. **Borderline fields.** Fields that sit between identity and
   classification (e.g., Windchill `displayNumber`, `state`,
   `lifecyclePhase`) need a working rule. Worth pressure-testing
   against AOUSD members' source systems.

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
per-system instances. Note: D's surface (`token[]` label values + identifier
strings in `assetInfo`) cannot carry the heterogeneous typed fields the field
experiment surfaces — see §3.4 and `details/field_classification_experiment.md`.

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

Four verticals were exercised across the four mechanisms. The
synthesized scenarios in `details/industry_scenarios.md` covered fields
the comparison's earlier draft selected as representative; the
authoritative-spec field census in
`details/field_classification_experiment.md` covered the broader
identifier-package surface as the source systems define it. The two
together give an asymmetric picture, and the asymmetry is what the
AOUSD review weighs.

- **AECO.** The canonical "what kind of thing is this?" classification
  (IFC type/objectType, Revit category/familyType/mark/level,
  UniClass/OmniClass codes) is controlled-vocabulary and fits any
  mechanism. The full IFC identifier surface also includes
  `IfcOwnerHistory` (timestamps, composite person/organization/application
  references) and IFC schema-version metadata; A and C carry these natively,
  B and D do not without auxiliary mechanisms.
- **Manufacturing/PLM.** Windchill `ID`/`Number`/`State`/`Type`/`Organization`
  fit any mechanism cleanly; AAS `globalAssetId` and `assetType` likewise.
  The heterogeneous-typed surface — Windchill `CreatedOn`/`LastModified`
  (`Edm.DateTimeOffset`), SAP `ERSDA`/`LAEDA`/`MSTDE` (`DATS`) and
  `NTGEW`/`BRGEW`/`VOLUM` (`QUAN(13,3)`), AAS `Property.value`
  (polymorphic XSD), AAS `Range`/`Reference`/`RelationshipElement`
  composites — fits A or C; B-alone and D do not carry it.
- **Robotics.** Strict identifier surface (package URI, frame_id, topic,
  source format, ROS distro) is mostly strings; `std_msgs/Header.stamp`
  (`time`) and `seq` (`uint32`) are heterogeneous typed already in the
  strict reading. Round-trip-back-to-URDF preservation pulls in the
  numeric URDF/SDF surface (mass, inertia, joint limits, dynamics) —
  twelve heterogeneous-typed kinds against one classification kind
  (joint type).
- **M&E.** Lightest case. Asset DB IDs and version strings fit any
  mechanism. The identifier-package edges (`created_at`/`updated_at`
  datetimes, project/parent/created_by entity-link composite refs)
  are heterogeneous typed in ShotGrid; OMC's `version` is int and
  `creationContext`/`lifecycleEvents` are structured composites.

The "does this field belong to identity or classification?" framing
the earlier draft used answers cleanly *for the controlled-vocabulary
classification axis*, where every vertical surveyed has a clean fit.
That framing does not by itself answer where the heterogeneous typed
surface goes — that is the scope question listed in
[Open questions for AOUSD review](#open-questions-for-aousd-review).

→ Deep dives: [details/industry_scenarios.md](details/industry_scenarios.md),
[details/field_classification_experiment.md](details/field_classification_experiment.md)

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

### 3.6 Vendor Adoption Scoring (caveat)

`stress_tests/vendor_adoption_analysis.{py,json}` produces eight-dimension
scores. The original framing presented these as a synthesizing verdict.
**That framing has been retracted under this PR.** The eight dimensions
were constructed after the leaning toward D had already taken shape; they
have not been re-derived from the proposal's eight authorized principles
(separation of concerns, industry agnosticism, vendor extensibility,
composability, discoverability, external queryability, round-trip
fidelity, minimal disruption) and explicit risks. The scores are
preserved below as illustrative of the per-mechanism contrasts the
experiments surfaced, not as an independent verdict:

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

A re-derivation of dimensions from the authorized principles is part of
the rebuild plan. Two specific dimensions have known issues against the
field experiment: D's "Metadata heterogeneity" score of 4 cannot be
reconciled with the `token[]`-only label surface failing to carry
heterogeneous typed fields (timestamps, numeric measures with units,
composite refs, polymorphic AAS Properties); and the "Distribution
friction" weighting reflects a position on the distribution-friction
tension that is itself a load-bearing open question (see
`details/formality_and_distribution.md`).

→ Methodology and weight rationale (carrying the same caveat):
[details/stress_tests.md §5.3](details/stress_tests.md)

---

## Open Questions

1. **Where the identifier-package boundary sits.** The field
   experiment shows heterogeneous typed fields surfacing in every
   vertical surveyed. Whether those fields are part of source-identifier
   metadata or out of scope for this mechanism is the load-bearing
   scope question; the leaning that earlier drafts of this comparison
   asserted depended on assuming the narrower scope.

2. **Borderline fields between identity and classification.**
   `displayNumber`, `mark`, `tag`-style strings — identity (in
   `assetInfo`) or controlled-vocabulary classification (in labels)?
   Working rule under any mechanism: "if a tool needs the exact string
   to round-trip into the source system, it's identity; if it's a
   controlled-vocabulary term meaningful to humans, it's
   classification." Worth pressure-testing in AOUSD review.

3. **AAS type-vs-instance scoping.** AAS `globalAssetId` (type-level)
   vs. `specificAssetIds` (instance-level, list of structured records)
   need carrying. Under A or C the structured-record list rides
   `assetInfo` overflow; under B it requires a companion schema; under
   D the `specificAssetIds` *list of typed records* has no slot in
   the labels surface and needs an `assetInfo` channel.

4. **Are opaque IDs compatible with `assetInfo` long-term?** Mechanisms
   that rely on `assetInfo` for the identifier string (A and D) would
   need to migrate if `assetInfo` ever acquires structural constraints.
   Hypothetical under current OpenUSD direction, but worth flagging.

5. **`apiSchemas` list scaling.** Mechanisms that put per-facet or
   per-system instances on `apiSchemas` (D, and B/C in different ways)
   inherit the linear-sift cost the physics workflows already feel.
   A cached per-kind index in `UsdPrim` or a registry-spec convention
   for filtering would help; lacking one, consumers should expect
   linear scans.

---

## Status of this work

These findings inform a follow-up proposal. The empirical-first
methodology itself — running each candidate through the same battery
of reproducible tests, with classification criteria pre-registered —
is a contribution this work intends to carry forward to other
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

# Source Identifiers in OpenUSD: Comparison Review Guide

**Authors:** Aaron Luk (NVIDIA)
**Date:** April 2026
**Branch:** [`aluk/source-identifiers-comparison`](https://github.com/asluk/USD/tree/aluk/source-identifiers-comparison)
**Proposal:** [Separation of Concerns for Identifiers in USD](../../OpenUSD-proposals/proposals/identifier_separation_of_concerns/README.md)

---

## How to Read This Document

This is the TAC review guide. It is self-contained for a 15–20 minute read.

**Suggested reading order:**
1. [Executive Summary](#executive-summary) — problem, the three approaches, scores, recommendation
2. [Decisions for TAC](#decisions-for-tac) — what you are being asked to decide
3. [Key Findings](#key-findings) — the evidence, with each section building toward the recommendation
4. [Why Structured Overflow Is Not `customData`](#why-structured-overflow-is-not-customdata) — addressing the most likely objection
5. [Hybrid Recommendation](#hybrid-recommendation) — the case for Approach C, with a concrete `.usda` example
6. [Repository Map](#repository-map) — where to find implementations, examples, and stress test data

**Deep dives:** Each Key Findings subsection links to a standalone `details/` file if you want the full analysis, test code, and pseudocode for that topic.

---

## Executive Summary

This document presents an empirical comparison of three candidate mechanisms for
expressing external source identifiers in OpenUSD, as described in the
*Separation of Concerns for Identifiers in USD* proposal. Approaches A and B were
implemented in the OpenUSD codebase, exercised across four industry verticals
(AECO, manufacturing, robotics, M&E), stress-tested at 100,000-prim scale with
eight simulated vendor/standards-body identifier schemes, and evaluated against
a governance model informed by Khronos glTF, IETF/IANA, W3C, and
buildingSMART precedents. Approach C (hybrid) was then implemented as the
recommended synthesis.

Both approaches preserve **round-trip fidelity** for opaque, vendor-specific
identifiers — strings survive a round-trip through USD without loss regardless
of mechanism. The approaches differ in validation, discoverability, and
governance, not in data preservation.

### The three approaches

**Approach A — `assetInfo` stratified sub-dictionaries** (`pxr/usd/usdSourceId/`)**.**
Source identifiers are stored as nested dictionaries within `assetInfo["sourceIds"]`,
with a **non-applied** API schema (`UsdSourceIdAPI`) providing convenience access.
Follows the `UsdModelAPI` precedent: the schema wraps `assetInfo` metadata without
requiring explicit application or an `apiSchemas` listing.

**Approach B — Multi-apply schema with typed properties** (`pxr/usd/usdSourceIdSchema/`)**.**
Source identifiers are expressed as typed properties on a multi-apply API schema
(`UsdSourceIdSchemaAPI`). Each external system is one schema instance (e.g.,
`SourceIdSchemaAPI:windchill`), carrying four typed properties: `primaryId`,
`revision`, `domain`, `label`. Follows the `UsdSemanticsLabelsAPI` /
`UsdCollectionAPI` precedent.

**Approach C — Hybrid** (`pxr/usd/usdSourceIdHybrid/`)**.**
Multi-apply schema (Approach B) for the common fields + `assetInfo` overflow
dictionaries (Approach A) for domain-specific metadata. The recommended path.

### Summary of findings

| Dimension | Approach A | Approach B | Assessment |
|-----------|-----------|-----------|------------|
| File size (100K prims, 1–5 IDs each) | 106.3 MB | 91.6 MB | B is 14% smaller |
| Authoring verbosity | 3.09M lines | 2.02M lines | B is 35% fewer lines |
| Unique namespace entries per stage | 10 dict keys | 30 property names | A has 3× fewer unique names |
| Ease of initial vendor adoption | ★★★★★ | ★★★★☆ | A: zero friction; B: near-zero |
| Domain-specific metadata flexibility | ★★★★★ | ★★★☆☆ | A: freeform dicts; B: fixed 4 properties |
| Collision safety | ★★☆☆☆ | ★★★★☆ | A: silent; B: detectable |
| GUI / tool discoverability | ★★☆☆☆ | ★★★★★ | B: schema-driven; A: manual |
| Schema validation | ★☆☆☆☆ | ★★★★★ | B: built-in; A: none |
| Composition granularity | Per dict key | Per property | B: surgical per-field override |
| Governance enforceability | Convention only | Convention + schema | B: structurally detectable |

**Overall scores** (1–5 across 8 dimensions): **A = 23/40, B = 33/40.**

Approach B scores higher on the dimensions that matter most for a
multi-stakeholder standard (safety, discoverability, validation, governance),
while Approach A wins decisively on metadata flexibility — a critical
requirement for heterogeneous industrial use cases. The scores reflect
TAC discussion priorities; both approaches are viable for simple identifier
schemes.

**Recommendation:** Neither approach alone is sufficient. The recommended
path is **Approach C (hybrid)**: Approach B's multi-apply schema for the
common identifier fields (`primaryId`, `revision`, `domain`, `label`) combined
with Approach A's `assetInfo` freeform dictionaries for domain-specific metadata
overflow. See [Hybrid Recommendation](#hybrid-recommendation) for details.

---

## Decisions for TAC

This comparison asks the TAC to evaluate three questions and one open issue.
The [Key Findings](#key-findings) below present the evidence for each.

1. **Mechanism choice.** Should source identifiers use a multi-apply schema
   with `assetInfo` overflow (Approach C / hybrid), a pure `assetInfo`
   dictionary design (Approach A), or a pure multi-apply schema (Approach B)?
   → Evidence: §3.1 Composition, §3.2 Industry Scenarios, §3.3 Stress Tests

2. **Base schema fields.** If the TAC accepts a schema-based approach (B or C),
   are the four proposed common fields the right ones: `primaryId`, `revision`,
   `domain`, `label`? Or should additional fields (e.g., `scope`) be included
   from the start?
   → Evidence: §3.2 Industry Scenarios, §3.5 Scoping

3. **Governance model.** Should AOUSD establish a domain registry with three
   tiers (vendor → multi-vendor → standard), modeled on Khronos glTF / W3C
   incubation precedents?
   → Evidence: §3.4 Governance

4. **Open question: `scope`.** The type-vs-instance distinction (`scope`) is
   critical for AAS/Industry 4.0 but arguably domain-specific. Should it start
   in the base schema, or begin in `assetInfo` overflow with a path to
   promotion if cross-domain adoption emerges?
   → Evidence: §3.5 Scoping, [scope promotion simulation](details/scope_promotion_simulation.md)

---

## Key Findings

The following sections present the evidence for the decisions above. Each
builds on the last: composition safety motivates a schema; industry data
shows why the schema alone is insufficient; stress tests quantify the
tradeoffs; governance and scoping address how the mechanism evolves.

### 3.1 Composition Behavior

**Verdict: Approach B is strictly safer.**

Both approaches handle the standard override scenario correctly (updating a
revision field, adding a new domain). The key difference is the risk surface:

| Aspect | Approach A | Approach B |
|--------|-----------|------------|
| Override granularity | Per dictionary key at each nesting level | Per individual property |
| Risk of unintentional data loss | Medium — round-trip serialization hazard | None |
| Adding a new domain | Add key to `sourceIds` dict | `prepend apiSchemas` + author properties |
| Partial field update | Works if structured correctly; subtle | Always works; no subtlety |
| Tool author burden | Must understand dict merge semantics | Standard property authoring |

**The hazard:** If a tool serializes an override by reading the composed value
and writing it back (a common pattern), it writes the full dictionary including
fields from the base layer, which then shadow the base — corrupting composition
silently. Approach B's per-property model has no equivalent risk.

This composition difference is also why the hybrid places the common identifier
fields (the ones most likely to be overridden across layers) in schema
properties rather than the dictionary. Schema properties contribute to
`UsdPrimDefinition`, giving tools fallback values, GUI presentation, and
per-property composition — the structural guarantees that dictionaries cannot
provide.

→ Deep dive: [details/composition_behavior.md](details/composition_behavior.md)

Composition safety argues for schema properties. But does it matter in
practice? The next section tests both approaches against four industry
verticals to see where Approach B’s structural advantages help — and where
its fixed four-property model breaks down.

---

### 3.2 Industry Scenario Analysis

**Verdict: A handles rich metadata; B handles simple schemas; C handles both.**

Four verticals were tested (AECO, manufacturing, robotics, M&E):

| Dimension | Approach A | Approach B |
|-----------|-----------|------------|
| Primary identifier (linkage key) | ✅ Adequate | ✅ Adequate |
| Revision/version | ✅ Adequate | ✅ Adequate |
| Domain-specific metadata | ✅ Natural (freeform dict) | ❌ Requires companion schema or custom attrs |
| Multi-domain on single prim | ✅ Natural | ✅ Natural |
| Composite keys (configurable products) | ✅ Natural | ❌ Cannot express without extension |
| Relationship between alternatives | ✅ Metadata in dict | ❌ No mechanism |

**The critical finding:** For simple identifier schemes (a string ID + optional
version), both approaches are equivalent. For industries with rich, heterogeneous
identifier metadata — manufacturing, AECO, robotics — Approach A's freeform
dictionaries handle all tested scenarios without requiring per-domain schema work.

- **AECO:** IFC metadata (`ifcType`, `schema`, `objectType`), Revit metadata
  (`category`, `familyType`, `level`) fit naturally in A's dicts. B requires
  companion schemas to carry them.
- **Manufacturing:** PTC Windchill parts carry `displayNumber`, `navigationType`,
  `serialNumber`, `lifecyclePhase`. B's four properties are insufficient;
  6 of 8 simulated vendors needed domain-specific fields beyond the base schema.
- **Robotics:** Source format provenance (URDF/SDF), ROS frame IDs, sensor
  datasheet revision — all natural in A, all require extension in B.
- **M&E:** Model-level asset tracking maps equally well to both approaches.

→ Deep dive: [details/industry_scenarios.md](details/industry_scenarios.md)

The industry data makes the case for both mechanisms: schema properties for
the common fields every domain shares, and freeform dictionaries for the
metadata that varies by domain. The next section quantifies this at scale.

---

### 3.3 Ecosystem Simulation & Stress Tests

**Verdict: B wins on file size and governance; A wins on adoption friction and metadata; C justifies the size cost.**

**8-vendor simulation** (NVIDIA, Adobe, Apple, SideFX, Autodesk, buildingSMART, ASHRAE, ISO):

- Approach A: zero OpenUSD codebase changes needed per vendor; any extra metadata
  just goes in the dict. 6 of 8 vendors needed metadata beyond a primary ID.
- Approach B: zero OpenUSD changes for common fields; but 6 of 8 vendors need
  companion schemas or custom attributes for their domain-specific fields.
- **Collision:** A's collisions are silent (two vendors pick the same key);
  B's collisions are structurally visible via `apiSchemas` and `domain` token.
- **Promotion:** B's `domain` token allows renaming without content migration;
  A requires renaming dict keys in all existing content.

**100K-prim stress test:**

| Metric | Approach A | Approach B | C (Hybrid) |
|--------|-----------|-----------|------------|
| File size | 106.3 MB | 91.6 MB | 144.0 MB |
| Line count | 3.09M | 2.02M | 3.58M |
| Namespace footprint | 10 dict keys | 30 property names | 30 props + 9 dict keys |
| Full-stage text scan | 0.638 s | 0.590 s | — |

C's 57% size increase over B is the dual-mechanism cost, overstated because: not all
domains need overflow, binary formats compress dicts efficiently, and the alternative
(companion schemas) would create even more property names.

**Vendor adoption scoring** (8 dimensions, 1–5 each; weights reflect
TAC discussion priorities from the 2026-03-06 and subsequent sessions):

| Dimension | A | B | Winner | TAC Weight |
|-----------|---|---|--------|------------|
| Ease of initial adoption | 5 | 4 | A | Medium |
| Collision safety | 2 | 4 | B | High |
| Metadata flexibility | 5 | 3 | A | High |
| GUI integration | 2 | 5 | B | Medium |
| Promotion lifecycle | 3 | 4 | B | Medium |
| Scale manageability | 3 | 3 | — | Low |
| Discoverability | 2 | 5 | B | High |
| Schema validation | 1 | 5 | B | High |
| **Total** | **23** | **33** | **B** | |

→ Deep dive: [details/stress_tests.md](details/stress_tests.md)

The scoring data supports Approach B for governed common fields. But a
multi-vendor ecosystem needs more than a schema — it needs a governance
model for who registers what, and how domains mature over time.

---

### 3.4 Governance, Validation & Deployment

**Verdict: B/C provides structural governance hooks A cannot offer.**

**Governance model:** Informed by precedents across multiple standards bodies —
Khronos glTF's `Prefixes.md`, W3C's WICG incubation path, and IETF/IANA
registration policies. Three tiers (paralleling both glTF's
`VENDOR_`→`EXT_`→`KHR_` and W3C's Community Group → Working Group →
Recommendation):

- **Vendor domains** (`com.ptc.windchill`, `com.nvidia.omniverse`): self-service,
  First Come First Served — no approval required, no membership fee
- **Multi-vendor domains** (`ext.simready`): demonstrated multi-vendor adoption
- **AOUSD standard domains** (`aousd.ifc`): TAC ratification

The design is **decentralized by default**: any vendor can register and ship
immediately. Promotion to multi-vendor or standard status is opt-in, not
mandatory — a vendor domain that serves its community well has no obligation
to seek broader standardization.

**A note on centralization.** The hybrid introduces structural declaration
(`apiSchemas`) that Approach A does not require, and the governance registry
adds namespace coordination. This is a deliberate tradeoff: self-describing
data enables interoperability without vendor-specific parsing code, at the
cost of requiring vendors to declare their participation. The registry
provides namespace coordination, not approval authority — following the
Khronos model, where vendor extensions require only a unique prefix
reservation, not content review (cf. Neil Trevett's characterization at
AOUSD Summit 2025: Khronos does not police vendor extension names beyond
requiring vendor prefixes). The process is administrative, not evaluative.
Vendors who prefer zero coordination can still author `assetInfo` overflow
dictionaries without registration; the schema declaration and registry
entry formalize what is already implicit in the data.

**Structural advantage of B/C:** The `apiSchemas` list functions like glTF's
`extensionsUsed` (or W3C's declared feature policies) — a consumer knows which
identifier domains are present without parsing all `assetInfo` dictionaries
across all prims. Approach A has no equivalent.

**Validator complexity:**

| Validator Aspect | Approach A | Approach B |
|-----------------|-----------|------------|
| Discovery | Must parse all `assetInfo` dicts on all prims | `GetAll()` returns instances directly |
| Type safety | Manual `isinstance()` checks | Schema-enforced |
| Schema targeting (`schemaTypes`) | ❌ None | ✅ Available |
| Lines of validation code | ~30 | ~15 |

**Schema registration cost:** A full compiled companion schema requires ~1,150 lines
across 16 files (reference: `UsdSemanticsLabelsAPI`). **Codeless schemas**
(`skipCodeGeneration = true`) reduce this to ~80 lines across 3 files — no C++,
no Python wrappers, no CMake — lowering the barrier from "requires USD build
system expertise" to "edit a `.usda` file and run `usdGenSchema`." This is
relevant for domain stakeholders (AECO firms, PLM vendors, standards bodies)
who need typed extension properties in B/C but may lack C++ expertise.

| Deployment tier | Files | Lines | C++ needed? |
|----------------|-------|-------|-------------|
| `assetInfo` only | 0 | 0 | No |
| Codeless schema | 3 | ~80 | No |
| Compiled schema | 16+ | ~1,150+ | Yes |

→ Deep dive: [details/governance.md](details/governance.md)

The governance model defines how identifier domains are registered and
promoted. One question it deliberately leaves open: should
type-vs-instance scoping be a universal schema field, or domain-specific
metadata? This is the most concrete test of where to draw the line between
schema and overflow.

---

### 3.5 Type-vs-Instance Scoping & Identifier Typing

**Verdict: The `domain` token already provides explicit identifier typing. Whether
a `scope` property belongs in the base schema or in domain-specific overflow is an
open question — see discussion below.**

**The requirement.** AAS distinguishes `globalAssetId` (type-level: part family,
product designation) from `specificAssetIds` (instance-level: serial number, deployed
unit ID), each with a mandatory type label naming its source system (PLM, IFC, ERP,
ECLASS). Some domains need this type-vs-instance distinction for deterministic
round-tripping, filtering, and collision prevention across systems.

| Aspect | Approach A | Approach B | Approach C |
|--------|-----------|------------|------------|
| Type-vs-instance scope | Freeform dict key (any structure works, no discoverability) | Could add optional `scope` token, or leave to overflow | Same as B + overflow for AAS-style lists |
| Identifier type label | Dict key name serves as informal label | `domain` token is authoritative type label; instance name adds context | Same as B for schema fields |
| AAS `specificAssetIds` list | Natural fit — nested list in dict | Cannot express open-ended list without companion schema | Schema for common fields + `assetInfo` overflow for full list |
| Backwards compatibility | N/A | No schema change needed if `scope` stays in overflow | Same |

**How each approach handles it:**

- **Approach A:** Freeform dictionary keys can encode any structure, including
  `{scope: "instance", …}`. Works, but no tool can discover or validate the scope
  convention without out-of-band knowledge.

- **Approach B:** The `domain` token already serves as the authoritative identifier
  type label. A `scope` token could be added to the schema, but many domains
  have no need for it — making it arguably domain-specific rather than
  universal. glTF and MaterialX each have internal type/instance concepts
  (mesh reuse, node definitions) but define no type-vs-instance distinction
  at the external identifier level. IFC assigns a GlobalId to every entity
  regardless of whether it is a type object or an instance object. The open-ended `specificAssetIds` list
  structure cannot be expressed without a companion schema or falling back to
  `customData`.

- **Approach C:** The overflow dictionary naturally carries domain-specific
  conventions like `scope` for AAS without polluting the base schema. The
  `assetInfo` overflow handles the full AAS-style `specificAssetIds` list when
  needed, without schema proliferation.

**Open question: where does `scope` live?** The type-vs-instance distinction is
central to AAS/Industry 4.0 but arguably irrelevant for many other domains.
IFC GlobalId uniquely identifies each entity — both type objects
(`IfcTypeObject`) and instance objects (`IfcObject`) carry their own
GlobalId, so the type-vs-instance distinction is structural (class
hierarchy), not at the identifier level. ECLASS is a product classification
standard and is inherently type-level. glTF and MaterialX have internal
type/instance concepts but no equivalent external identifier distinction. If `scope` is domain-specific rather than universal, it may belong
in the `assetInfo` overflow dict — which is precisely the escape hatch Approach C
provides. This is literal "scope creep" and merits TAC discussion. The
[scope promotion simulation](details/scope_promotion_simulation.md)
demonstrates one concrete resolution: `scope` starts in the overflow dict,
gains cross-domain adoption, undergoes registry-spec validation, and is
eventually promoted to a schema property — with concrete `.usda` files and
runnable scripts at each phase.

**DPP proof-of-concept.** A community contributor built a bidirectional AAS Digital
Battery Passport ↔ OpenUSD mapping (PR asluk/OpenUSD-proposals#2) that exercises both
Approach A and B, validating that the hybrid overflow pattern handles DPP-specific
fields (`batteryModel`, `manufacturingDate`, `chemistry`) without schema changes.

→ Deep dive: [details/hybrid_analysis.md](details/hybrid_analysis.md)

→ Simulation: [details/scope_promotion_simulation.md](details/scope_promotion_simulation.md) —
traces the full lifecycle of `scope` from AAS-only overflow dict through cross-domain
adoption, registry-spec validation, TAC-ratified schema promotion, and incremental
migration, with concrete `.usda` files and runnable Python scripts at each phase.

The scoping question illustrates the core tradeoff: putting everything in the
schema is premature for emerging fields; putting everything in dictionaries
sacrifices the safety and discoverability the evidence above supports. The
hybrid’s `assetInfo` overflow is designed for exactly this middle ground — but
it raises a natural objection.

---

## Why Structured Overflow Is Not `customData`

The most likely objection to Approach C: does the `assetInfo` overflow dict
simply recreate the `customData` dumping ground the proposal aims to resolve?
Three structural differences:

1. **Scoped, not global.** Overflow lives under `assetInfo["sourceIds"][<domain>]`,
   keyed to a registered domain. `customData` is a flat, unscoped namespace.
2. **Linked to a schema instance.** The overflow dict key matches the
   `SourceIdHybridAPI:<domain>` instance name — tools know which overflow
   dict belongs to which schema instance. `customData` has no such linkage.
3. **Governed evolution path.** Overflow fields that prove cross-domain utility
   can be promoted to schema properties through the registry-spec → schema
   promotion lifecycle (see [scope promotion simulation](details/scope_promotion_simulation.md)).
   `customData` fields have no standardized promotion path.

In short: overflow is scoped, linked, and has a graduation path. `customData`
is none of these.

---

## Hybrid Recommendation

### The case against either approach alone

**Approach A alone** provides no built-in mechanism for validation or GUI
discoverability. While a registry-spec mechanism could partially close these gaps
(see [details/registry_spec_analysis.md](details/registry_spec_analysis.md)),
runtime validation and automatic property-panel rendering would require new USD
infrastructure that does not exist today — infrastructure that Approach B provides
natively through the existing schema system. Without such infrastructure,
consumers must implement vendor-specific dictionary parsing, echoing the
`customData` fragmentation pattern the proposal aims to resolve.

**Approach B alone** cannot carry the domain-specific metadata that real-world
industrial workflows require without forcing every stakeholder to register companion
schemas — creating schema sprawl or pushing metadata back into `customData`.

### Approach C: Multi-apply schema + `assetInfo` overflow

**Schema (Approach B) for common fields. `assetInfo` (Approach A) for overflow.**
USD schemas cannot define `dictionary`-typed properties (`dictionary` is not in
`SdfValueTypeNames`); it is only available as metadata. The hybrid embraces this
constraint: the schema carries the governed common fields; `assetInfo` carries
the freeform domain-specific data, linked by the instance name.

```usda
def Xform "Chiller_01" (
    prepend apiSchemas = [
        "SourceIdHybridAPI:windchill",
        "SourceIdHybridAPI:opcua"
    ]
    # Domain-specific metadata in assetInfo (element-wise composed)
    assetInfo = {
        dictionary sourceIds = {
            dictionary windchill = {
                string displayNumber = "CH-7500-A"
                string navigationType = "OR:wt.filter.NavigationCriteria:7608531"
                string state = "Released"
            }
            dictionary opcua = {
                string nodeClass = "Object"
                string browseName = "Chiller01"
                string serverUri = "opc.tcp://bms.example.com:4840"
            }
        }
    }
)
{
    # Typed common fields as schema properties (per-property composition)
    string sourceIdentifier:windchill:primaryId = "VR:wt.part.WTPart:23639563"
    string sourceIdentifier:windchill:revision = "Rev.C"
    token sourceIdentifier:windchill:domain = "com.ptc.windchill"
    string sourceIdentifier:windchill:label = "Windchill Part OID"

    string sourceIdentifier:opcua:primaryId = "ns=4;s=Building.HVAC.Chiller01"
    token sourceIdentifier:opcua:domain = "org.opcfoundation.ua"
    string sourceIdentifier:opcua:label = "OPC UA NodeId"
}
```

The `assetInfo["sourceIds"]` dictionary key **matches the schema instance name**
(both are `"windchill"`). The convenience API bridges the two: `GetDomainMetadata()`
reads from `assetInfo`; `GetPrimaryIdAttr()` reads the schema property.

### What each mechanism provides

| Field | Mechanism | Benefit |
|-------|-----------|---------|
| `primaryId` | Schema property (typed) | Universal linkage key; schema-validated; GUI-visible |
| `revision` | Schema property (typed) | Standard versioning field; per-property composition |
| `domain` | Schema property (typed) | Collision-resistant reverse-DNS; queryable by token |
| `label` | Schema property (typed) | Human-readable; GUI display name |
| Domain-specific fields | `assetInfo["sourceIds"]` (freeform dict) | Overflow; no schema changes needed |

### Final recommendation

> **Adopt a multi-apply schema (Approach C/hybrid) with `assetInfo` overflow
> for domain-specific metadata.** This provides schema-backed common fields for
> interoperability and governance, plus a freeform escape hatch for the
> domain-specific metadata that real-world industrial workflows require.
>
> Establish an AOUSD Domains Registry informed by Khronos glTF's `Prefixes.md`
> and W3C's WICG incubation model: low-barrier vendor registration (à la
> glTF prefix reservation or W3C Community Group creation), three-tier
> promotion path, GitHub-based process.
>
> The resulting mechanism addresses all eight design principles from the
> proposal: separation of concerns, industry agnosticism, vendor extensibility,
> composability, discoverability, external queryability, round-trip fidelity,
> and minimal disruption.

→ Deep dive: [details/hybrid_analysis.md](details/hybrid_analysis.md)

---

## Repository Map

All source code, examples, stress tests, and analysis scripts are on the
[`aluk/source-identifiers-comparison`](https://github.com/asluk/USD/tree/aluk/source-identifiers-comparison) branch.

### Implementations

```
pxr/usd/
├── usdSourceId/          # Approach A — non-applied schema wrapping assetInfo
│   ├── schema.usda
│   ├── sourceIdAPI.h/.cpp
│   ├── tokens.h/.cpp
│   └── api.h
├── usdSourceIdSchema/    # Approach B — multi-apply schema with typed properties
│   ├── schema.usda
│   ├── sourceIdentifierAPI.h/.cpp
│   ├── tokens.h/.cpp
│   └── api.h
└── usdSourceIdHybrid/    # Approach C — hybrid (recommended)
    ├── schema.usda
    ├── sourceIdentifierAPI.h/.cpp
    ├── tokens.h/.cpp
    └── api.h
```

### Examples and test data

```
extras/sourceIdentifiers/
├── COMPARISON.md                          ← this document
├── details/                               ← deep-dive sections
│   ├── approach_descriptions.md           # Section 2: API details, precedents
│   ├── composition_behavior.md            # Section 3: Layer composition tests
│   ├── industry_scenarios.md              # Section 4: AECO/mfg/robotics/M&E
│   ├── stress_tests.md                    # Section 5: 8-vendor sim, 100K-prim
│   ├── governance.md                      # Section 6: Registry model, validators
│   ├── hybrid_analysis.md                 # Section 7: C design + migration path
│   ├── registry_spec_analysis.md          # Could a registry close A's interop gap?
│   └── scope_promotion_simulation.md      # Lifecycle: overflow → schema property
├── examples/
│   ├── approach_a_assetinfo.usda          # AECO building (A)
│   ├── approach_b_schema.usda             # AECO building (B)
│   ├── composition_test_a_base.usda       # Composition base (A)
│   ├── composition_test_a_override.usda   # Composition override (A)
│   ├── composition_test_b_base.usda       # Composition base (B)
│   ├── composition_test_b_override.usda   # Composition override (B)
│   ├── manufacturing_a.usda               # Manufacturing lifecycle (A)
│   ├── manufacturing_b.usda               # Manufacturing lifecycle (B)
│   ├── robotics_a.usda                    # Robotics fleet (A)
│   └── robotics_b.usda                    # Robotics fleet (B)
├── vendor_simulation/
│   ├── approach_a_vendors.usda            # 8-vendor simulation (A)
│   └── approach_b_vendors.usda            # 8-vendor simulation (B)
├── scope_promotion/
│   ├── phase1_aas_overflow.usda           # Phase 1: scope in AAS overflow only
│   ├── phase2_cross_domain.usda           # Phase 2: Windchill + ROS adopt scope
│   ├── phase3_validator.py                # Phase 3: Registry-spec CI validator
│   ├── phase4_schema.usda                 # Phase 4: Updated schema definition
│   ├── phase4_promoted.usda               # Phase 4: scope as schema property
│   └── phase5_migration.py                # Phase 5: Overflow → schema migration
└── stress_tests/
    ├── generate_large_stage.py            # 100K-prim generator (seed=42)
    ├── stress_test_results.json           # Empirical measurements
    ├── vendor_adoption_analysis.py        # Adoption friction scoring
    └── vendor_adoption_analysis.json      # Scoring results
```

**To regenerate stress test data:**

```bash
cd extras/sourceIdentifiers/stress_tests
python3 generate_large_stage.py
python3 vendor_adoption_analysis.py
```

All three schema implementations have been processed through `usdGenSchema`.
Codeless (runtime-only) versions are in `extras/sourceIdentifiers/installed_schemas/`
and verified to load at runtime.

# Source Identifiers in OpenUSD: Empirical Comparison of Two Candidate Approaches

**Authors:** Aaron Luk (NVIDIA), with implementation and analysis by automated evaluation  
**Date:** April 2026  
**Branch:** [`aluk/source-identifiers-comparison`](https://github.com/asluk/USD/tree/aluk/source-identifiers-comparison)  
**Proposal:** [Separation of Concerns for Identifiers in USD](../../OpenUSD-proposals/proposals/identifier_separation_of_concerns/README.md)

## Contents

1. [Executive Summary](#executive-summary)
2. [Approach Descriptions](#approach-descriptions)
3. [Composition Behavior](#composition-behavior)
4. [Industry Scenario Analysis](#industry-scenario-analysis)
5. [Ecosystem Simulation & Stress Tests](#ecosystem-simulation--stress-tests)
6. [Governance, Validation & Deployment](#governance-validation--deployment)
7. [Hybrid Analysis & Recommendation](#hybrid-analysis--recommendation)

---

## 1. Executive Summary

This document presents an empirical comparison of two candidate mechanisms for
expressing external source identifiers in OpenUSD, as described in the
*Separation of Concerns for Identifiers in USD* proposal. Both approaches were
implemented in the OpenUSD codebase, exercised across four industry verticals
(AECO, manufacturing, robotics, M&E), stress-tested at 100,000-prim scale with
eight simulated vendor/standards-body identifier schemes, and evaluated against
a governance model informed by Khronos glTF, IETF/IANA, W3C, and
buildingSMART precedents.

### The two approaches

**Approach A: Extend `assetInfo` with stratified sub-dictionaries.**
Source identifiers are stored as nested dictionaries within
`assetInfo["sourceIds"]`, with an applied single-apply API schema
(`UsdSourceIdAPI`) providing convenience access. Data lives in composed
metadata. Follows the `UsdMediaAssetPreviewsAPI` precedent.

**Approach B: Multi-apply schema with typed properties.**
Source identifiers are expressed as typed properties on a multi-apply API
schema (`UsdSourceIdentifierAPI`), with each external system represented as
a schema instance (e.g., `SourceIdentifierAPI:windchill`,
`SourceIdentifierAPI:ifc`). Each instance carries four typed properties:
`primaryId`, `revision`, `domain`, and `label`. Follows the
`UsdSemanticsLabelsAPI` / `UsdCollectionAPI` precedent.

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
| Promotion lifecycle | Medium effort | Low-medium | B: schema versioning helps |
| Governance enforceability | Convention only | Convention + schema | B: structurally detectable |

**Overall scores** (1–5 across 8 dimensions): **A = 23/40, B = 33/40.**

Approach B scores higher on the dimensions that matter most for a
multi-stakeholder standard (safety, discoverability, validation, governance),
while Approach A wins decisively on metadata flexibility — a critical
requirement for heterogeneous industrial use cases.

**Recommendation:** Neither approach alone is sufficient. The recommended
path is a **hybrid** that uses Approach B's multi-apply schema for the
common identifier fields (primaryId, revision, domain, label) and extends
each instance with an `assetInfo`-style freeform dictionary for
domain-specific metadata overflow. This combines B's structural advantages
with A's flexibility. See [Section 7](#hybrid-analysis--recommendation) for
details.

### Repository structure

```
extras/sourceIdentifiers/
├── COMPARISON.md              ← this document
├── COMPARISON_PLAN.md         ← writing plan
├── examples/
│   ├── approach_a_assetinfo.usda        # AECO building (A)
│   ├── approach_b_schema.usda           # AECO building (B)
│   ├── composition_test_a_base.usda     # Composition base (A)
│   ├── composition_test_a_override.usda # Composition override (A)
│   ├── composition_test_b_base.usda     # Composition base (B)
│   ├── composition_test_b_override.usda # Composition override (B)
│   ├── manufacturing_a.usda             # Manufacturing lifecycle (A)
│   ├── manufacturing_b.usda             # Manufacturing lifecycle (B)
│   ├── robotics_a.usda                  # Robotics fleet (A)
│   └── robotics_b.usda                  # Robotics fleet (B)
├── vendor_simulation/
│   ├── approach_a_vendors.usda          # 8-vendor simulation (A)
│   └── approach_b_vendors.usda          # 8-vendor simulation (B)
└── stress_tests/
    ├── generate_large_stage.py          # 100K-prim generator
    ├── stress_test_results.json         # Empirical measurements
    ├── vendor_adoption_analysis.py      # Adoption friction scoring
    └── vendor_adoption_analysis.json    # Scoring results

pxr/usd/
├── usdSourceId/          # Approach A implementation
│   ├── schema.usda
│   ├── sourceIdAPI.h/.cpp
│   ├── tokens.h/.cpp
│   └── api.h
└── usdSourceIdSchema/    # Approach B implementation
    ├── schema.usda
    ├── sourceIdentifierAPI.h/.cpp
    ├── tokens.h/.cpp
    └── api.h
```

---

## 2. Approach Descriptions

### Approach A: `assetInfo` stratified sub-dictionaries

**Module:** `pxr/usd/usdSourceId/`  
**Schema type:** Single-apply API schema (`UsdSourceIdAPI`)  
**Precedent:** `UsdMediaAssetPreviewsAPI`  

**Mechanism.** Source identifiers are stored as nested dictionaries within the
composed `assetInfo` metadata on any prim:

```usda
def Mesh "Column_C14" (
    assetInfo = {
        dictionary sourceIds = {
            dictionary ifc = {
                string primaryId = "2O2Fr$t4X7Zf8NOew3FNr2"
                dictionary metadata = {
                    string ifcType = "IfcColumn"
                    string objectType = "W14x90"
                }
            }
            dictionary windchill = {
                string primaryId = "VR:wt.part.WTPart:23639563"
                string revision = "Rev.C"
                dictionary metadata = {
                    string displayNumber = "CH-7500-A"
                    string navigationType = "OR:wt.filter.NavigationCriteria:7608531"
                }
            }
        }
    }
)
{
}
```

**Key characteristics:**

- **No properties defined by the schema.** The schema declares no USD
  properties. All data lives in `assetInfo` metadata, which is a composed
  dictionary. The schema provides a described spec and a C++/Python
  convenience API for reading/writing the sub-dictionary structure.

- **Freeform metadata per domain.** Each domain's sub-dictionary is
  unconstrained. Windchill can store `displayNumber`, `navigationType`,
  `organization`; IFC can store `ifcType`, `schema`, `classification`.
  No common denominator is required. Domains can add fields at will without
  any schema change.

- **Composed element-wise.** `assetInfo` composes by merging dictionaries
  at each nesting level, with the strongest opinion winning per key. This
  means an override layer can add a new domain without disturbing existing
  ones, but overriding a single field within an existing domain requires
  understanding the merge semantics (see Section 3).

- **No contribution to `UsdPrimDefinition`.** Because data lives in
  metadata rather than properties, it does not appear in schema-aware
  GUI panels, cannot have fallback values, and cannot be validated by
  the schema system.

**C++ API usage:**

```cpp
UsdSourceIdAPI api = UsdSourceIdAPI::Apply(prim);

// Set identifiers
api.SetSourceId(TfToken("windchill"),
    "VR:wt.part.WTPart:23639563", "Rev.C");

// Query
std::string id;
api.GetPrimaryId(TfToken("windchill"), &id);

// List all domains
std::vector<TfToken> domains = api.GetDomains();
```

---

### Approach B: Multi-apply schema with typed properties

**Module:** `pxr/usd/usdSourceIdSchema/`  
**Schema type:** Multi-apply API schema (`UsdSourceIdentifierAPI`)  
**Precedent:** `UsdSemanticsLabelsAPI`, `UsdCollectionAPI`, `UsdPhysicsLimitAPI`  

**Mechanism.** Each external system is represented as an instance of a
multi-apply schema, with typed properties under a namespaced prefix:

```usda
def Mesh "Column_C14" (
    prepend apiSchemas = [
        "SourceIdentifierAPI:ifc",
        "SourceIdentifierAPI:windchill"
    ]
)
{
    string sourceIdentifier:ifc:primaryId = "2O2Fr$t4X7Zf8NOew3FNr2"
    token sourceIdentifier:ifc:domain = "org.buildingsmart.ifc"
    string sourceIdentifier:ifc:label = "IFC GlobalId"

    string sourceIdentifier:windchill:primaryId = "VR:wt.part.WTPart:23639563"
    string sourceIdentifier:windchill:revision = "Rev.C"
    token sourceIdentifier:windchill:domain = "com.ptc.windchill"
    string sourceIdentifier:windchill:label = "Windchill Part OID"
}
```

**Key characteristics:**

- **Four typed properties per instance:**
  - `primaryId` (string) — the main linkage key
  - `revision` (string) — version/revision designator
  - `domain` (token) — formal reverse-DNS domain identifier
  - `label` (string) — human-readable description

- **Contributes to `UsdPrimDefinition`.** Properties appear in schema-aware
  GUIs automatically. Fallback values (empty strings) mean unauthored
  properties are visible and editable. Schema-driven validation is built in.

- **Per-property composition.** Each property composes independently.
  Overriding `sourceIdentifier:windchill:revision` does NOT affect
  `sourceIdentifier:windchill:primaryId` — they are separate attributes
  with separate opinion stacks.

- **Fixed property set limits domain-specific metadata.** The four
  properties represent a common denominator. Domain-specific fields
  (Windchill's `navigationType`, IFC's `ifcType`, AMT's `machineId`)
  cannot be expressed without: (a) a companion domain-specific schema,
  (b) custom attributes, or (c) encoding metadata in the `primaryId`
  string (lossy).

- **`apiSchemas` list declares what's present.** Tools can discover all
  applied source identifier instances by inspecting the `apiSchemas`
  list, without parsing metadata dictionaries.

**C++ API usage:**

```cpp
auto api = UsdSourceIdentifierAPI::Apply(prim, TfToken("windchill"));

// Set properties
api.CreatePrimaryIdAttr(VtValue(std::string("VR:wt.part.WTPart:23639563")));
api.CreateRevisionAttr(VtValue(std::string("Rev.C")));
api.CreateDomainAttr(VtValue(TfToken("com.ptc.windchill")));

// Query
std::string id;
api.GetPrimaryIdAttr().Get(&id);

// List all instances on a prim
std::vector<TfToken> instances = UsdSourceIdentifierAPI::GetAll(prim);
```

### Side-by-side summary

| Aspect | Approach A | Approach B |
|--------|-----------|------------|
| Data location | `assetInfo` metadata | Prim properties |
| Schema type | Single-apply | Multi-apply |
| Properties defined | None | 4 per instance |
| Domain metadata | Freeform dictionary | Fixed set (extensible via companion schemas) |
| Discoverability | Manual dict iteration | `apiSchemas` list + schema introspection |
| Fallback values | None | Empty strings |
| GUI presentation | Requires custom code | Automatic |
| Composition | Per dict key (element-wise) | Per property (independent) |

---

## 3. Composition Behavior

Composition behavior is one of the most consequential differences between the
two approaches. It governs what happens when source identifiers are authored
across multiple layers — a common scenario when a base asset (authored by a
design team) is overridden by a downstream consumer (e.g., a construction
coordinator updating a revision, or an operational system adding telemetry
bindings).

### Test scenario

Both approaches were tested with the same scenario:

- **Base layer:** A chiller prim carries identifiers from three systems
  (Windchill, SAP, IFC). The Windchill entry includes `primaryId`,
  `revision`, and a `metadata` sub-dict with `displayNumber` and `state`.

- **Override layer:** References the base and makes two changes:
  1. Updates the Windchill `revision` from "Rev.B" to "Rev.C" and
     `state` from "In Work" to "Released"
  2. Adds a new OPC UA domain binding

### Approach A: Element-wise dictionary composition

```usda
# Override layer (Approach A)
def Xform "Chiller" (
    prepend references = @./composition_test_a_base.usda@
    assetInfo = {
        dictionary sourceIds = {
            dictionary windchill = {
                string revision = "Rev.C"
                dictionary metadata = {
                    string state = "Released"
                }
            }
            dictionary opcua = {
                string primaryId = "ns=4;s=Building.HVAC.Chiller01"
            }
        }
    }
)
```

**Composed result for `windchill`:**

`assetInfo` composes element-wise at each dictionary nesting level. The
override provides `revision` and `metadata.state`; the base provides
`primaryId` and `metadata.displayNumber`. Because composition merges per
key at each level:

- `primaryId` = `"VR:wt.part.WTPart:23639563"` ✅ (from base — preserved)
- `revision` = `"Rev.C"` ✅ (from override — updated)
- `metadata.displayNumber` = `"CH-7500-A"` ✅ (from base — preserved)
- `metadata.state` = `"Released"` ✅ (from override — updated)

This works correctly **in this case** because both layers structured their
dictionaries at the same granularity. However, the behavior is subtle:

**Risk scenario:** If the override layer had authored the entire `windchill`
dictionary with only `revision` (omitting `primaryId`), the composed result
would still contain `primaryId` from the base — because `assetInfo` merges
per key. But if a tool *serializes* the override by first reading the
composed value and writing it back (a common pattern), it would write the
full dictionary including `primaryId`, which would then shadow the base
layer's value. This round-trip hazard is inherent to dictionary-based
composition and requires discipline from authoring tools.

**SAP and IFC:** Completely untouched. The override layer's `sourceIds`
merges at the domain level, so domains not mentioned in the override
are preserved from the base.

**OPC UA:** Added cleanly as a new key in `sourceIds`.

### Approach B: Per-property composition

```usda
# Override layer (Approach B)
def Xform "Chiller" (
    prepend references = @./composition_test_b_base.usda@
    prepend apiSchemas = ["SourceIdentifierAPI:opcua"]
)
{
    string sourceIdentifier:windchill:revision = "Rev.C"

    string sourceIdentifier:opcua:primaryId = "ns=4;s=Building.HVAC.Chiller01"
    token sourceIdentifier:opcua:domain = "org.opcfoundation.ua"
    string sourceIdentifier:opcua:label = "OPC UA NodeId"
}
```

**Composed result for `windchill`:**

Each property composes independently. The override authors only
`sourceIdentifier:windchill:revision`; every other `windchill` property
retains its value from the base:

- `primaryId` = `"VR:wt.part.WTPart:23639563"` ✅ (from base)
- `revision` = `"Rev.C"` ✅ (from override)
- `domain` = `"com.ptc.windchill"` ✅ (from base)
- `label` = `"Windchill Part OID"` ✅ (from base)

There is **no risk of unintentional side effects**. Overriding one property
cannot disturb another property, even within the same instance. This is
the standard USD property composition model that all schema-based data
follows.

**SAP and IFC:** Completely untouched. Their properties are separate
attributes with their own opinion stacks.

**OPC UA:** Added via `prepend apiSchemas` (list editing), which appends
to the existing schema list without disturbing other entries.

### Composition comparison

| Aspect | Approach A | Approach B |
|--------|-----------|------------|
| Override granularity | Per dictionary key at each nesting level | Per individual property |
| Risk of unintentional data loss | Medium (round-trip serialization hazard) | None |
| Adding a new domain | Add key to `sourceIds` dict | `prepend apiSchemas` + author properties |
| Removing a domain | Delete key (requires authoring empty or using `ClearDomain()`) | Remove from `apiSchemas` list |
| Partial field update | Works if structured correctly; subtle | Always works; no subtlety |
| Tool author burden | Must understand dict merge semantics | Standard property authoring |

**Verdict:** Approach B's per-property composition is strictly safer and
more predictable. Approach A's element-wise dictionary composition works
correctly but requires more discipline from tool authors and has a
round-trip serialization hazard that could cause subtle data corruption
in careless implementations.

---

## 4. Industry Scenario Analysis

Both approaches were exercised across four industry verticals using realistic
identifier data. The examples are available as matching A/B pairs in
`extras/sourceIdentifiers/examples/`. This section summarizes the key
findings from each scenario.

### 4.1 Architecture, Engineering, Construction & Operations (AECO)

**Files:** `approach_a_assetinfo.usda`, `approach_b_schema.usda`

**Scenario:** A building with structural columns (IFC + Revit + Uniclass +
OmniClass), an HVAC chiller with PLM and operational telemetry (Windchill +
SAP + OPC UA + BACnet + IFC), and rooms with purely numeric identifiers.

**Findings:**

- **Both approaches handle the core use case well.** A structural column
  carrying identifiers from four external systems is expressible in both
  approaches without difficulty.

- **Approach A handles AECO’s rich metadata naturally.** IFC metadata
  (ifcType, schema, objectType), Revit metadata (category, familyType,
  mark, level), and classification system metadata all fit naturally as
  key-value pairs in freeform dictionaries.

- **Approach B requires omitting or encoding AECO metadata.** The four
  fixed properties capture the linkage keys (GlobalId, ElementId,
  classification code) but cannot express the surrounding context
  (ifcType, category, level) without companion schemas or custom
  attributes.

- **Operational telemetry bindings** (OPC UA NodeIds, BACnet object IDs)
  work equally well in both approaches for the primary identifier. But
  telemetry metadata (nodeClass, dataType, engineeringUnits) is again
  natural in A and absent in B’s base schema.

### 4.2 Manufacturing, Product Lifecycle & Digital Engineering

**Files:** `manufacturing_a.usda`, `manufacturing_b.usda`

**Scenario:** A tractor assembly (inspired by PTC/Windchill workflows) with
configurable products, alternative/equivalent identifiers, feature-level
identifiers, and Mercedes-Benz–style part numbering with extension codes.

**Findings:**

- **Approach A excels at manufacturing’s heterogeneous metadata.**
  Manufacturing identifiers are rarely just a string — they’re composite
  packages. A Windchill part carries displayNumber, navigationType
  (an opaque filter object), organization, state, lifecyclePhase, and
  serialNumber. These fit naturally as dictionary entries.

- **Approach B’s fixed schema is most strained here.** The four properties
  (primaryId, revision, domain, label) capture the linkage key and
  version, but manufacturing workflows *require* the surrounding metadata:
  - `navigationType` determines which configuration of a product is
    resolved — without it, the identifier is ambiguous for configurable
    products
  - `serialNumber` distinguishes instances of the same part design
  - `displayNumber` is the human-readable part number vs. the opaque
    system OID in `primaryId`
  - Mercedes-Benz extension codes (ES1, ES2) encode color and variant
    information as structured suffixes — they’re not just strings

- **Alternative identifiers** (OEM part number, service/replacement part
  number) work in both approaches — each gets its own domain/instance.
  But the *relationship* between alternatives (form-fit-function
  equivalence) is metadata that only Approach A can express in-line.

- **Feature-level identifiers** (cylinder bores, datum faces) carry
  manufacturing-critical metadata: diameter, tolerance, surface finish,
  machine ID. Approach B cannot express any of this without a companion
  `AmtFeatureIdentifierAPI` schema — exactly the kind of per-domain
  schema proliferation the proposal warns about.

### 4.3 Robotics & Simulation

**Files:** `robotics_a.usda`, `robotics_b.usda`

**Scenario:** Multi-robot warehouse fleet with URDF/SDF provenance, ROS
package identity, fleet assignment, sensor catalog identifiers, and
operational telemetry binding.

**Findings:**

- **Source format provenance** requires metadata beyond a primary ID:
  package name, model name, source format (URDF vs SDF), ROS distro.
  Approach A carries this naturally; Approach B cannot without extension.

- **Shared design ID vs. per-instance fleet assignment** works well in
  both approaches. The ROS package URI is shared across robot instances;
  the fleet assignment ID is per-instance. Both mechanisms support this
  distinction.

- **Sensor catalog identifiers** need manufacturer, part number, datasheet
  revision — again, metadata that only fits in A’s freeform dicts without
  a companion schema.

- **ROS topic names and frame IDs** are critical operational metadata that
  bind a sensor prim to its ROS data stream. These are domain-specific
  fields that B’s base schema cannot carry.

### 4.4 Media & Entertainment

While not separately implemented as a test file (USD’s existing `assetInfo`
already covers the M&E model-level case), the analysis confirms:

- **Model-level asset tracking** (asset management DB IDs, versions,
  approvals) maps to both approaches equally well, since the metadata
  package is typically just an ID + version.

- **Sub-model identification** (individual props, lights, materials with
  their own tracking IDs) benefits from the schema being applicable to
  any prim (both approaches support this).

- **Multi-system tracking** (Flow Production Tracking + ftrack + internal
  DB) is the same multi-domain pattern demonstrated in the other
  scenarios.

### Cross-industry synthesis

The pattern across all four verticals is consistent:

| Dimension | Approach A | Approach B |
|-----------|-----------|------------|
| Primary identifier (linkage key) | ✅ Adequate | ✅ Adequate |
| Revision/version | ✅ Adequate | ✅ Adequate |
| Domain-specific metadata | ✅ Natural (freeform dict) | ❌ Requires companion schema or custom attrs |
| Multi-domain on single prim | ✅ Natural | ✅ Natural |
| Shared identity across instances | ✅ Natural | ✅ Natural |
| Composite keys (configurable products) | ✅ Natural | ❌ Cannot express without extension |
| Alternative/equivalent identifiers | ✅ Natural | ✅ Natural (each gets an instance) |
| Relationship between alternatives | ✅ Metadata in dict | ❌ No mechanism |

**The critical finding:** For industries with simple identifier schemes
(a string ID + optional version), both approaches are equivalent. For
industries with rich, heterogeneous identifier metadata — which includes
manufacturing, AECO, and robotics — Approach A’s freeform dictionaries
are significantly more capable without requiring per-domain schema work.

This is the central tension driving the hybrid recommendation in Section 7.

---

## 5. Ecosystem Simulation & Stress Tests

### 5.1 Multi-vendor simulation

**Files:** `vendor_simulation/approach_a_vendors.usda`,
`vendor_simulation/approach_b_vendors.usda`

Eight vendors and standards bodies were simulated adding their own
identifier schemes to a single turbine blade prim:

| # | Organization | Domain | Identifier Example |
|---|-------------|--------|-------------------|
| 1 | NVIDIA | Omniverse Nucleus | `omni://nucleus.nvidia.com/assets/turbine/blade_v3` |
| 2 | Adobe | Substance 3D | `adb:sub3d:asset:a1b2c3d4-e5f6-7890-abcd-ef1234567890` |
| 3 | Apple | Reality Composer Pro | `com.apple.realitykit.asset.turbine-blade-001` |
| 4 | SideFX | Houdini Digital Asset | `hda://SideFX::turbine_blade::3.0` |
| 5 | Autodesk | Fusion 360 | `urn:adsk.wipprod:dm.lineage:7Rf2wvPxSEeHmBq-XqFD_g` |
| 6 | buildingSMART | IFC | `2O2Fr$t4X7Zf8NOew3FL02` |
| 7 | ASHRAE | Equipment Classification | `NG_turbine_blade_surface` |
| 8 | ISO | STEP | `STEP-FILE-ID:#4782` |

**Vendor adoption friction:**

- **Approach A:** Each vendor writes `assetInfo["sourceIds"]["<key>"]`
  with whatever structure they want. Zero files touched in the OpenUSD
  codebase. Zero coordination required. A vendor can ship support in a
  single afternoon.

- **Approach B:** Each vendor applies `SourceIdentifierAPI:<name>` and
  authors four properties. Also zero files touched if the common
  properties suffice. But if the vendor needs domain-specific fields
  (6 of 8 simulated vendors do), they must either register a companion
  schema or use custom attributes — adding friction.

**Collision scenario:**

- **Approach A:** If two vendors independently pick the key `"tracker"`,
  their data silently collides. The composed result contains only the
  strongest opinion’s `tracker` dictionary. No warning is produced.
  Mitigation: reverse-DNS keys (e.g., `"com.vendor1.tracker"`), but
  this is convention, not enforcement.

- **Approach B:** If two vendors both use `SourceIdentifierAPI:tracker`,
  the `apiSchemas` list cannot contain duplicate entries. The `domain`
  property provides secondary disambiguation. More importantly, schema
  registration makes the collision *visible* — tools inspecting the
  prim will see the conflicting schema application.

**Promotion lifecycle:**

- **Approach A:** Promoting `"nvidia_simready"` to `"aousd_simready"`
  requires renaming dictionary keys in all existing content. No schema
  versioning mechanism tracks the migration. Tools querying by key must
  be updated.

- **Approach B:** Promotion can be as simple as updating the `domain`
  token value (`"com.nvidia.simready"` → `"org.aousd.simready"`),
  since tools can query by `domain` rather than instance name. If the
  instance name also changes, schema versioning tracks the migration
  and the old instance can be deprecated with a clear successor path.

### 5.2 Stress test: 100,000 prims

**Generator:** `stress_tests/generate_large_stage.py` (deterministic,
`random.seed(42)`; regenerate with `python3 generate_large_stage.py`)  
**Configuration:** 100,000 prims, each with 1–5 randomly assigned
domains from the 8-vendor pool, with metadata fields.

#### File size and verbosity

| Metric | Approach A | Approach B | Ratio (B/A) |
|--------|-----------|-----------|-------------|
| File size | 106.26 MB | 91.55 MB | 0.862× |
| Line count | 3,085,417 | 2,020,995 | 0.655× |
| Generation time | 6.37 s | 1.29 s | 0.203× |

**Analysis:** Approach B produces 14% smaller files and 35% fewer lines.
This is because:

1. **No nesting overhead.** Approach A requires `dictionary sourceIds = {`
   and `dictionary <domain> = {` wrapper lines at each nesting level.
   Approach B’s flat property namespace has no nesting.

2. **No metadata sub-dict.** Approach A carries domain-specific metadata
   as additional dictionary entries. The equivalent data would require
   companion schemas in B, but since B’s base schema doesn’t carry it,
   the comparison is not apples-to-apples on content richness. **If both
   approaches carried identical metadata, A would be smaller** because
   dictionary keys are shorter than fully-qualified property names.

3. **Generation time difference** reflects Python string formatting
   overhead for nested dict syntax vs. flat properties, not a meaningful
   performance signal.

#### Namespace footprint

| Metric | Approach A | Approach B |
|--------|-----------|------------|
| Unique names in stage | 10 dictionary keys | 30 property names |
| Names per domain | 1 key | 4 properties |
| At 20 vendors × 5 schemes | 100 dict keys | 400 properties + 100 apiSchemas |

**Analysis:** Approach A has a 3× smaller namespace footprint per domain
because each domain is a single dictionary key containing nested data.
Approach B explodes each domain into 4 separately-named properties. At
scale (20 vendors × 5 schemes = 100 domains), Approach B would add
400 property names to each prim’s property namespace — a significant
crowding concern, though each property is individually addressable and
typed.

#### Discovery performance (text search)

| Metric | Approach A | Approach B |
|--------|-----------|------------|
| Full-stage text scan | 0.638 s | 0.590 s |

Both approaches require a full scan for reverse lookups ("which prims
have this identifier?"). Performance is comparable. In production, both
would benefit from external indexing — the mechanism must make building
such indexes tractable, which both do (A via dictionary key iteration,
B via property name pattern matching or `apiSchemas` list filtering).

### 5.3 Vendor adoption scoring

**Methodology:** Eight dimensions scored 1–5 based on the multi-vendor
simulation, stress test results, and composition analysis.

| Dimension | A | B | Winner | Weight for TAC |
|-----------|---|---|--------|---------------|
| Ease of initial adoption | 5 | 4 | A | Medium |
| Collision safety | 2 | 4 | B | High |
| Metadata flexibility | 5 | 3 | A | High |
| GUI integration | 2 | 5 | B | Medium |
| Promotion lifecycle | 3 | 4 | B | Medium |
| Scale manageability | 3 | 3 | — | Low |
| Discoverability | 2 | 5 | B | High |
| Schema validation | 1 | 5 | B | High |
| **Total** | **23** | **33** | **B** | |

**Interpretation:** Approach B dominates on the dimensions that a
standards body cares about most (safety, discoverability, validation,
governance). Approach A wins on the dimensions that individual vendors
care about most (ease of adoption, metadata flexibility). This is not
a contradiction — it reflects the fundamental trade-off between
governance and flexibility, and it’s why the hybrid recommendation
exists.

---

## 6. Governance, Validation & Deployment

### 6.1 How other standards bodies govern vendor extensions

Source identifier domain registration is a **data-format governance**
problem, not a runtime mechanism. Unlike USD’s plugin system (which
registers schemas at application startup), identifier domains are
declared in USD content and must be governed outside the runtime.

Six precedents from other standards bodies inform this design:

| Body | Mechanism | Tiers | Registration | Collision Prevention |
|------|-----------|-------|-------------|---------------------|
| **Khronos glTF** | `Prefixes.md` on GitHub | `VENDOR_` → `EXT_` → `KHR_` | GitHub issue to reserve prefix | Prefix uniqueness in registry |
| **Khronos OpenGL/Vulkan** | Extension registry | `GL_NV_` → `GL_EXT_` → `GL_ARB_` → core | Formal registry at registry.khronos.org | Registered prefixes |
| **IETF/IANA** | RFC 8126 registration policies | Private Use → First Come First Served → Expert Review → Standards Action | IANA registry with designated expert | Unique registration per entry |
| **W3C** | WICG incubation | Community Group → Working Group → Recommendation | Community Group proposal | `data-*` for freeform; standard attrs governed |
| **buildingSMART** | bSDD data dictionary | Organization-published → reviewed → standard | Online portal + REST API | Centralized namespace |
| **Java/XML** | Reverse-DNS convention | Single tier (by convention) | None (self-service) | Domain name ownership |

**Key insight:** The glTF model is the closest analog to what AOUSD would
need for source identifiers. It is:

- **Low barrier:** Any vendor can request a prefix by filing a GitHub
  issue. No membership required.
- **Three-tier:** Vendor-specific (ship independently) → multi-vendor
  (`EXT_`, proven interop) → ratified (`KHR_`, Khronos IP framework).
- **Declarative:** Each glTF file lists `extensionsUsed` and
  `extensionsRequired` — consumers know what to expect without parsing
  the full file. This is analogous to Approach B’s `apiSchemas` list.
- **Not a runtime mechanism:** The registry is a Markdown file in a
  GitHub repo. Enforcement is by convention and community review.

### 6.2 What a governance model would look like for source identifiers

Regardless of which approach is chosen, AOUSD would maintain a registry
of identifier domain prefixes. The proposed model:

1. **AOUSD maintains a Domains Registry** (analogous to glTF’s
   `Prefixes.md`) — a list mapping domain keys/prefixes to
   organizations, with contact information and status.

2. **Three tiers:**
   - **Vendor domains** (`com.ptc.windchill`, `com.nvidia.omniverse`):
     self-service registration, First Come First Served.
   - **Multi-vendor domains** (`ext.simready`, `ext.digitaltwins`):
     requires demonstrated multi-vendor implementation.
   - **AOUSD standard domains** (`aousd.ifc`, `aousd.plm`):
     ratified by AOUSD TAC, covered by AOUSD IP framework.

3. **Registration requires:** domain key, organization name, contact,
   URL, brief description of the identifier scheme. No code, no schema
   plugin, no membership fee.

4. **Promotion path:** Vendor → multi-vendor (demonstrated adoption by
   2+ organizations) → standard (TAC ratification).

### 6.3 How each approach interacts with governance

**Approach A:**
- Domain keys are freeform strings in `assetInfo` dictionaries.
- There is **no structural mechanism** to declare which domains a file
  uses. A consumer must parse all `assetInfo["sourceIds"]` dictionaries
  across all prims to discover the domain set.
- Governance violations (unregistered domain key, collision) are
  **silent** — detectable only by external validators.
- The glTF `extensionsUsed` analog is **absent**.

**Approach B:**
- Domain instances are declared in the `apiSchemas` list.
- A consumer can inspect `apiSchemas` on any prim (or stage metadata)
  to discover which identifier domains are present **without parsing
  property values**.
- This is structurally analogous to glTF’s `extensionsUsed` array.
- Governance violations are **detectable** — an unregistered instance
  name can be flagged by schema-aware tools; the `domain` property
  provides a secondary, unambiguous resolution.

### 6.4 Validator designs

Both approaches can be validated, but the implementation difficulty
differs significantly.

**Approach A validator (pseudocode):**

```python
def validate_source_ids_a(stage, registry):
    """Validate Approach A source identifiers against a domain registry."""
    errors = []
    for prim in stage.Traverse():
        source_ids = prim.GetAssetInfoByKey("sourceIds")
        if not source_ids:
            continue
        if not isinstance(source_ids, dict):
            errors.append(f"{prim.GetPath()}: sourceIds is not a dictionary")
            continue
        for domain_key, domain_data in source_ids.items():
            # Check domain is registered
            if domain_key not in registry:
                errors.append(
                    f"{prim.GetPath()}: unregistered domain '{domain_key}'")
            # Check required fields
            if not isinstance(domain_data, dict):
                errors.append(
                    f"{prim.GetPath()}: domain '{domain_key}' is not a dict")
                continue
            if "primaryId" not in domain_data:
                errors.append(
                    f"{prim.GetPath()}: domain '{domain_key}' missing primaryId")
            # Type checking is manual — no schema enforcement
            primary = domain_data.get("primaryId")
            if primary is not None and not isinstance(primary, str):
                errors.append(
                    f"{prim.GetPath()}: primaryId in '{domain_key}' is not a string")
    return errors
```

**Approach B validator (pseudocode):**

```python
def validate_source_ids_b(stage, registry):
    """Validate Approach B source identifiers against a domain registry."""
    errors = []
    for prim in stage.Traverse():
        instances = UsdSourceIdentifierAPI.GetAll(prim)
        for instance_name in instances:
            api = UsdSourceIdentifierAPI.Get(prim, instance_name)
            # Check domain is registered
            domain = api.GetDomainAttr().Get()
            if domain and domain not in registry:
                errors.append(
                    f"{prim.GetPath()}: unregistered domain '{domain}'")
            # Check primaryId is authored (not just fallback)
            if not api.GetPrimaryIdAttr().HasAuthoredValue():
                errors.append(
                    f"{prim.GetPath()}: instance '{instance_name}' "
                    f"has no authored primaryId")
            # Type checking is automatic — schema enforces types
            # Fallback detection is built in
            # No manual isinstance() checks needed
    return errors
```

**Comparison:**

| Validator Aspect | Approach A | Approach B |
|-----------------|-----------|------------|
| Discovery | Must parse all assetInfo dicts on all prims | `GetAll()` returns instances directly |
| Type safety | Manual `isinstance()` checks | Schema-enforced |
| Missing fields | Manual key-existence check | `HasAuthoredValue()` |
| Domain resolution | Dict key only (may be ambiguous) | `domain` property (reverse-DNS, unambiguous) |
| Lines of validation code | ~30 | ~15 |
| Can run without USD API | Yes (dict parsing) | Requires USD schema system |

### 6.5 Deployment friction for identifier stakeholders

An "identifier stakeholder" is an organization that wants their
identifier scheme to be expressible in USD content: a PLM vendor
(PTC, Siemens), a standards body (buildingSMART, ISO), a DCC vendor
(Autodesk, SideFX), or an end-user enterprise.

**What a stakeholder must do under each approach:**

| Step | Approach A | Approach B |
|------|-----------|------------|
| 1. Register domain | Register key in AOUSD Domains Registry | Register instance name in AOUSD Domains Registry |
| 2. Document scheme | Write specification for their sub-dictionary structure | Write specification for which properties they use |
| 3. Start authoring | Write `assetInfo["sourceIds"]["<key>"]` in any tool that can author `assetInfo` | Apply schema instance + author 4 properties in any USD-aware tool |
| 4. Add domain-specific metadata | Just add keys to their dictionary — no coordination | Must register companion schema OR use custom attributes |
| 5. Validate content | Run external validator against their spec | Schema validation covers base fields; domain-specific fields need external validator |
| 6. Ship to consumers | Consumers parse their dict structure per their spec | Consumers use standard schema API; domain-specific metadata needs their spec |

**Net assessment:**

- **Steps 1–3** are equivalent in both approaches. Initial adoption
  friction is near-zero for both.

- **Step 4** is where the approaches diverge sharply. Approach A lets
  stakeholders evolve their metadata independently and immediately.
  Approach B forces a choice: live with the 4 common properties
  (insufficient for most industrial use cases), or invest in companion
  schema work.

- **Steps 5–6** favor Approach B for the common fields (schema-driven)
  but still require Approach A–style work for domain-specific metadata
  regardless.

---

## 7. Hybrid Analysis & Recommendation

### 7.1 The case against either approach alone

**Approach A alone** provides maximum flexibility but sacrifices
discoverability, validation, GUI integration, and governance
enforceability — the properties that a multi-stakeholder standard
needs most. It would repeat the `customData` pattern: technically
capable, but practically un-interoperable because every consumer
must know every vendor’s ad-hoc dictionary structure.

**Approach B alone** provides excellent structural properties but
cannot carry the domain-specific metadata that real-world industrial
workflows require. Forcing every identifier stakeholder to register
a companion schema for their domain-specific fields would either:
(a) create schema sprawl (dozens of `*IdentifierAPI` schemas), or
(b) push metadata into `customData` — recreating exactly the
fragmentation problem the proposal aims to solve.

### 7.2 Recommended hybrid: Approach B + metadata overflow dictionary

The recommended approach combines Approach B’s structural advantages
with Approach A’s metadata flexibility:

**Use the multi-apply schema (Approach B) as the base**, providing
typed, schema-backed common fields that all tools can discover and
validate. **Use Approach A’s `assetInfo["sourceIds"]` sub-dictionaries
as the overflow mechanism** for domain-specific metadata.

This works because USD schemas cannot define dictionary-typed properties
— `dictionary` is not in `SdfValueTypeNames`. It is only available as
metadata (`assetInfo`, `customData`). Rather than fight this constraint,
the hybrid embraces it: **the schema carries the governed common fields;
`assetInfo` carries the freeform domain-specific data.** The two
mechanisms coexist on the same prim, linked by the domain key.

```usda
class "SourceIdentifierAPI" (
    inherits = </APISchemaBase>
    customData = {
        token apiSchemaType = "multipleApply"
        token propertyNamespacePrefix = "sourceIdentifier"
    }
)
{
    # Typed common fields (schema-validated, GUI-visible)
    string __INSTANCE_NAME__:primaryId = ""
    string __INSTANCE_NAME__:revision = ""
    token __INSTANCE_NAME__:domain = ""
    string __INSTANCE_NAME__:label = ""

    # Domain-specific metadata lives in assetInfo["sourceIds"][<domain>],
    # NOT as a schema property (dictionary is not a valid attribute type).
    # The convenience API bridges between the schema properties and the
    # assetInfo sub-dictionary using the instance name as the linking key.
}
```

**Example USD:**

```usda
def Xform "Chiller_01" (
    prepend apiSchemas = [
        "SourceIdentifierAPI:windchill",
        "SourceIdentifierAPI:opcua"
    ]
    # Domain-specific metadata in assetInfo (element-wise composed)
    assetInfo = {
        dictionary sourceIds = {
            dictionary windchill = {
                string displayNumber = "CH-7500-A"
                string navigationType = "OR:wt.filter.NavigationCriteria:7608531"
                string state = "Released"
                string organization = "com.carrier.hvac"
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
    # Typed common fields as schema properties
    string sourceIdentifier:windchill:primaryId = "VR:wt.part.WTPart:23639563"
    string sourceIdentifier:windchill:revision = "Rev.C"
    token sourceIdentifier:windchill:domain = "com.ptc.windchill"
    string sourceIdentifier:windchill:label = "Windchill Part OID"

    string sourceIdentifier:opcua:primaryId = "ns=4;s=Building.HVAC.Chiller01"
    token sourceIdentifier:opcua:domain = "org.opcfoundation.ua"
    string sourceIdentifier:opcua:label = "OPC UA NodeId"
}
```

The convention is that the `assetInfo["sourceIds"]` dictionary key
**matches the schema instance name** (e.g., both are `"windchill"`).
The convenience API bridges the two mechanisms: `GetDomainMetadata()`
reads from `assetInfo`, while `GetPrimaryIdAttr()` reads the schema
property.

### 7.3 Why this works

| Property | Provided by | Benefit |
|----------|------------|----------|
| `primaryId` | Schema property (typed) | Universal linkage key; schema-validated; GUI-visible |
| `revision` | Schema property (typed) | Standard versioning field |
| `domain` | Schema property (typed) | Collision-resistant reverse-DNS; queryable by token |
| `label` | Schema property (typed) | Human-readable; GUI display name |
| domain-specific fields | `assetInfo["sourceIds"]` (freeform dict) | Domain-specific overflow; no schema changes needed |

**Benefits retained from Approach B:**
- `apiSchemas` list declares which domains are present (like glTF `extensionsUsed`)
- Per-property composition for the common fields
- Schema-driven discoverability and GUI presentation
- Type validation on common fields
- `domain` token enables governance enforcement

**Benefits retained from Approach A:**
- Domain-specific metadata lives in a freeform dictionary
- Stakeholders can add fields without schema changes
- No companion schema proliferation
- Rich, heterogeneous metadata packages (manufacturing, AECO, robotics)

**Trade-off accepted:**
- Domain-specific metadata in `assetInfo` is not schema-validated
- Domain-specific metadata is not GUI-visible without custom code
- Authors must maintain consistency between the schema instance name
  and the `assetInfo["sourceIds"]` dictionary key
- But this is the *right* trade-off: common fields should be governed;
  domain-specific metadata should be flexible. The boundary between
  the two mechanisms is explicit and follows established USD patterns
  (cf. `UsdMediaAssetPreviewsAPI` storing data in `assetInfo`).

### 7.4 Composition behavior of the hybrid

The hybrid composes as follows:

- **Schema properties** (`primaryId`, `revision`, `domain`, `label`):
  per-property composition (strongest opinion wins per attribute).
  Safe and predictable.

- **`assetInfo["sourceIds"]` dictionaries:** element-wise composition
  at each nesting level (standard `assetInfo` behavior). An override
  layer can add new keys to a domain’s metadata dictionary without
  disturbing existing keys. This gives finer-grained composition for
  domain metadata than a single dictionary-valued attribute would.

The result is that the common fields (the ones tools need for
interoperability) compose with the safest semantics (per-property),
while domain-specific metadata composes with the more flexible
element-wise semantics. This matches the precedent set by
`UsdMediaAssetPreviewsAPI`, which stores data in `assetInfo` alongside
its schema declaration.

### 7.5 File size cost of the hybrid

The hybrid carries both schema properties and `assetInfo` metadata,
so it is the largest of the three approaches:

| Metric | A | B | C (Hybrid) |
|--------|---|---|------------|
| File size (100K prims) | 106.3 MB | 91.6 MB | 144.0 MB |
| Line count | 3.09M | 2.02M | 3.58M |
| Namespace footprint | 10 dict keys | 30 properties | 30 properties + 9 dict keys |

The 36% size increase over A (and 57% over B) is the cost of the
dual-mechanism approach. In practice, this overstates the penalty
because:

1. **Not all domains need metadata overflow.** Simple identifier
   schemes (IFC GlobalId, Revit ElementId) may only use the schema
   properties, with no `assetInfo` entry. The stress test assigns
   metadata to all domains; real-world stages would be sparser.

2. **Binary formats (usdc/usdz) compress dictionaries efficiently.**
   The text-format overhead of nested `dictionary` syntax is significant;
   binary encoding would reduce the gap.

3. **The alternative is companion schemas.** If domain-specific metadata
   were expressed as companion schemas (Approach B’s workaround), the
   property count would be even higher than the hybrid’s `assetInfo`
   overhead.

### 7.5 Governance model for the hybrid

The three-tier AOUSD Domains Registry (Section 6.2) applies directly:

1. **Registration:** Stakeholder registers a domain key and instance name
   in the registry. Specifies their `metadata` dictionary schema in
   their published specification.

2. **Validation:** Common fields validated by the USD schema system.
   Domain-specific `metadata` validated by external validators per the
   stakeholder’s specification (same as Approach A).

3. **Promotion:** When a domain-specific metadata field proves universally
   useful, it can be promoted to a typed property on the base schema
   (schema versioning tracks this). The `metadata` dictionary remains
   as an overflow mechanism.

### 7.6 Migration path from existing conventions

Pipelines currently using `customData`, `displayName`, or ad-hoc
`assetInfo` conventions can migrate incrementally:

1. Apply `SourceIdentifierAPI:<domain>` to prims that carry identifiers.
2. Move the primary identifier value to `primaryId`.
3. Move revision/version to `revision`.
4. Set `domain` to the registered reverse-DNS key.
5. Move remaining metadata to the `metadata` dictionary.
6. Remove old `customData`/`displayName` entries.

This can be done per-layer, per-domain, without disrupting existing
composition. No big-bang migration required.

### 7.7 Final recommendation

> **Adopt a multi-apply schema (Approach B) with a freeform `metadata`
> dictionary property as the fifth field.** This provides schema-backed
> common fields for interoperability and governance, plus a freeform
> escape hatch for the domain-specific metadata that real-world industrial
> workflows require.
>
> Establish an AOUSD Domains Registry following the Khronos glTF
> `Prefixes.md` model: low-barrier vendor registration, three-tier
> promotion path, GitHub-based process.
>
> The resulting mechanism addresses all eight design principles from the
> proposal: separation of concerns, industry agnosticism, vendor
> extensibility, composability, discoverability, external queryability,
> round-trip fidelity, and minimal disruption.

---

## Appendix: Files in this comparison

All source code, examples, stress tests, and analysis scripts are
available on the
[`aluk/source-identifiers-comparison`](https://github.com/asluk/USD/tree/aluk/source-identifiers-comparison)
branch of `asluk/USD`.

To regenerate the 100K-prim stress test data:

```bash
cd extras/sourceIdentifiers/stress_tests
python3 generate_large_stage.py
```

To run the vendor adoption analysis:

```bash
python3 vendor_adoption_analysis.py
```

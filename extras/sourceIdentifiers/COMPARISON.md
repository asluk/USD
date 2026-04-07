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

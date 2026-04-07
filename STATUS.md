# Source Identifiers — Implementation & Comparison Status

**Branch:** `aluk/source-identifiers-comparison`  
**Decision:** Single branch with both approaches side-by-side for direct comparison.  
**Rationale:** A single branch lets reviewers see both implementations in the same tree, diff them directly, and run the same test harness against both.

## Architecture

### Approach A: `assetInfo` stratified sub-dictionaries
- Module: `pxr/usd/usdSourceId/` — applied single-apply API schema `UsdSourceIdAPI`
- Convenience access to `assetInfo["sourceIds"]` sub-dictionaries
- Follows `UsdMediaAssetPreviewsAPI` precedent: schema provides API, data lives in composed `assetInfo` metadata
- **Files:** schema.usda, api.h, sourceIdAPI.h/.cpp, tokens.h/.cpp

### Approach B: Multi-apply schema with typed properties
- Module: `pxr/usd/usdSourceIdSchema/` — multi-apply API schema `UsdSourceIdentifierAPI`
- Instance names per domain: `SourceIdentifierAPI:windchill`, `SourceIdentifierAPI:ifc`, etc.
- Typed properties per instance: `primaryId` (string), `revision` (string), `domain` (token), `label` (string)
- Follows `UsdSemanticsLabelsAPI` / `UsdCollectionAPI` precedent
- **Files:** schema.usda, api.h, sourceIdentifierAPI.h/.cpp, tokens.h/.cpp

## Progress

### ✅ Phase 1: Implementations (DONE)
- [x] Approach A: Schema definition, C++ API (header + impl), tokens
- [x] Approach B: Schema definition, C++ API (header + impl), tokens

### ✅ Phase 2: Examples across 4 industry verticals (DONE)
All examples have matching A/B pairs for direct comparison:
- [x] **AECO building** — `approach_a_assetinfo.usda` / `approach_b_schema.usda`
  - Structural column with 4 systems (IFC, Revit, Uniclass, OmniClass)
  - HVAC chiller with PLM + operational telemetry (Windchill, SAP, OPC UA, IFC)
  - Sensor prims with BACnet + OPC UA bindings
  - Rooms with purely numeric identifiers
- [x] **Composition behavior** — `composition_test_a_*.usda` / `composition_test_b_*.usda`
  - Base layer with 3 systems → override layer adds 1 system + updates 1 field
  - **Key finding:** Approach B's per-property composition allows surgical override of single fields without side effects; Approach A requires understanding dict merge semantics
- [x] **Manufacturing lifecycle** — `manufacturing_a.usda` / `manufacturing_b.usda`
  - Tractor assembly with configurable products (navigation criteria)
  - Alternative/equivalent identifiers (OEM, service, replacement parts)
  - Feature-level identifiers (cylinder bores, datum faces)
  - Mercedes-Benz part numbering with extension codes
  - **Key finding:** Manufacturing metadata requires many domain-specific fields that Approach B's 4-property schema cannot express without companion schemas
- [x] **Robotics fleet** — `robotics_a.usda` / `robotics_b.usda`
  - Multi-robot warehouse with URDF provenance, ROS topics, fleet assignment
  - Sensor catalog identifiers + operational telemetry
  - **Key finding:** Same domain-specific metadata limitation as manufacturing

### ✅ Phase 3: Multi-vendor ecosystem simulation (DONE)
- [x] `vendor_simulation/approach_a_vendors.usda` / `approach_b_vendors.usda`
  - 8 vendors/standards bodies on a single turbine blade prim:
    NVIDIA, Adobe, Apple, SideFX, Autodesk, IFC, MaterialX/Khronos, STEP/ISO
  - Collision scenario demo (two vendors pick same key)
  - Promotion lifecycle demo (vendor scheme → standard)
  - Heterogeneous metadata limitation demo (Approach B only)

### ✅ Phase 4: Stress tests & empirical data (DONE)
- [x] 100K-prim stage generator (`generate_large_stage.py`) — regenerable, not tracked in git
- [x] Vendor adoption analysis (`vendor_adoption_analysis.py`)

**Key empirical findings:**

| Metric | Approach A | Approach B | Winner |
|--------|-----------|-----------|--------|
| File size (100K prims) | 106.3 MB | 91.6 MB | **B** (14% smaller) |
| Authoring verbosity | 3,085K lines | 2,021K lines | **B** (35% fewer) |
| Unique namespace entries | 10 dict keys | 30 property names | **A** (3× fewer) |
| Text-search discovery | 0.638s | 0.590s | ~tied |
| Adoption scoring (1-5 × 8 dims) | 23/40 | 33/40 | **B** |

Adoption dimension breakdown:
| Dimension | A | B | |
|-----------|---|---|---|
| Ease of initial adoption | 5 | 4 | A |
| Collision safety | 2 | 4 | B |
| Metadata flexibility | 5 | 3 | A |
| GUI integration | 2 | 5 | B |
| Promotion lifecycle | 3 | 4 | B |
| Scale manageability | 3 | 3 | = |
| Discoverability | 2 | 5 | B |
| Schema validation | 1 | 5 | B |

### 🔄 Phase 5: Vendor extension governance research (IN PROGRESS)
Research completed on how standards bodies handle vendor extension registration:
- [x] **Khronos glTF:** Prefixes.md registry on GitHub, anyone can request a prefix via GitHub issue. Three tiers: `VENDOR_` → `EXT_` → `KHR_`. No runtime mechanism — purely a data-format-level naming convention enforced by community convention and spec reviewers.
- [x] **Khronos OpenGL/Vulkan:** `GL_NV_`, `GL_AMD_` → `GL_EXT_` → `GL_ARB_` → core. Extension registry maintained at registry.khronos.org.
- [x] **IETF/IANA:** RFC 8126 defines registration policies ranging from "Private Use" (no registration) through "First Come First Served" to "Standards Action". IANA maintains formal registries with designated expert review.
- [x] **W3C:** WICG (Web Incubator Community Group) for low-barrier incubation → Working Group specification → W3C Recommendation. HTML's `data-*` attributes as freeform extension slot (analogous to `customData` in USD).
- [x] **buildingSMART bSDD:** Centralized data dictionary service where any organization can register property sets, classifications, and properties. Online API + web portal.
- [x] **Java/XML:** Reverse-DNS namespace convention (no central registry, collision prevention by convention).

**Key insight for the comparison:** The critical distinction is that identifier domain registration is NOT a runtime mechanism (unlike USD's plugin system). It's a **data-format governance** mechanism — a registry that maps domain keys/prefixes to organizations, maintained outside the runtime. Both Approach A and B can use the same governance model; the question is which approach makes governance *easier to enforce*.

### ⬜ Phase 6: Comparison document (TODO — next)
- [ ] Complete comparison document incorporating all findings
- [ ] Deployment friction analysis for identifier stakeholders
- [ ] Validator design for both approaches
- [ ] Governance model implications (which approach is more enforceable?)
- [ ] Final recommendation with nuance

### ⬜ Phase 7: Hybrid approach analysis (TODO)
- [ ] Evaluate Approach A + B combination (B for common fields, A for overflow metadata)
- [ ] Evaluate Approach A with schema-backed fallback values

## Decisions Log
1. **Single branch** — easier to compare than two branches
2. **No full build** — schema definitions + C++ source + .usda examples demonstrate the approaches without requiring a full OpenUSD build cycle. The schemas are structurally valid and follow established patterns.
3. **100K prim stress files gitignored** — too large for GitHub (>90MB each), generator script is tracked instead

## Timeline
- Started: 2026-04-07 04:25 UTC
- Comparison doc complete: 2026-04-07 14:35 UTC

## Deliverable
**COMPARISON.md** (1,102 lines) — the main deliverable — is complete.
See `extras/sourceIdentifiers/COMPARISON.md`.

**Recommendation:** Hybrid approach — multi-apply schema (Approach B)
with a freeform `metadata` dictionary property as the 5th field.

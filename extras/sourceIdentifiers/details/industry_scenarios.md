# Industry Scenario Analysis

← [Back to COMPARISON.md](../COMPARISON.md)

Both approaches were exercised across four industry verticals using realistic
identifier data. The examples are available as matching A/B pairs in
`extras/sourceIdentifiers/examples/`. This section summarizes the key
findings from each scenario.

## 4.1 Architecture, Engineering, Construction & Operations (AECO)

**Files:** `approach_a_assetinfo.usda`, `approach_b_schema.usda`

**Scenario:** A building with structural columns (IFC + Revit + Uniclass +
OmniClass), an HVAC chiller with PLM and operational telemetry (Windchill +
SAP + OPC UA + BACnet + IFC), and rooms with purely numeric identifiers.

**Findings:**

- **Both approaches handle the core use case well.** A structural column
  carrying identifiers from four external systems is expressible in both
  approaches without difficulty.

- **Approach A handles AECO's rich metadata naturally.** IFC metadata
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
  natural in A and absent in B's base schema.

## 4.2 Manufacturing, Product Lifecycle & Digital Engineering

**Files:** `manufacturing_a.usda`, `manufacturing_b.usda`

**Scenario:** A tractor assembly (inspired by PTC/Windchill workflows) with
configurable products, alternative/equivalent identifiers, feature-level
identifiers, and Mercedes-Benz-style part numbering with extension codes.

**Findings:**

- **Approach A excels at manufacturing's heterogeneous metadata.**
  Manufacturing identifiers are rarely just a string - they're composite
  packages. A Windchill part carries displayNumber, navigationType
  (an opaque filter object), organization, state, lifecyclePhase, and
  serialNumber. These fit naturally as dictionary entries.

- **Approach B's fixed schema is most strained here.** The four properties
  (primaryId, revision, domain, label) capture the linkage key and
  version, but manufacturing workflows *require* the surrounding metadata:
  - `navigationType` determines which configuration of a product is
    resolved - without it, the identifier is ambiguous for configurable
    products
  - `serialNumber` distinguishes instances of the same part design
  - `displayNumber` is the human-readable part number vs. the opaque
    system OID in `primaryId`
  - Mercedes-Benz extension codes (ES1, ES2) encode color and variant
    information as structured suffixes - they're not just strings

- **Alternative identifiers** (OEM part number, service/replacement part
  number) work in both approaches - each gets its own domain/instance.
  But the *relationship* between alternatives (form-fit-function
  equivalence) is metadata that only Approach A can express in-line.

- **Feature-level identifiers** (cylinder bores, datum faces) carry
  manufacturing-critical metadata: diameter, tolerance, surface finish,
  machine ID. Approach B cannot express any of this without a companion
  `AmtFeatureIdentifierAPI` schema - exactly the kind of per-domain
  schema proliferation the proposal warns about.

## 4.3 Robotics & Simulation

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
  revision - again, metadata that only fits in A's freeform dicts without
  a companion schema.

- **ROS topic names and frame IDs** are critical operational metadata that
  bind a sensor prim to its ROS data stream. These are domain-specific
  fields that B's base schema cannot carry.

## 4.4 Media & Entertainment

While not separately implemented as a test file (USD's existing `assetInfo`
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

## Cross-industry synthesis

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
industries with rich, heterogeneous identifier metadata - which includes
manufacturing, AECO, and robotics - Approach A's freeform dictionaries
are significantly more capable without requiring per-domain schema work.

This is the central tension driving the hybrid recommendation in
[hybrid_analysis.md](hybrid_analysis.md).

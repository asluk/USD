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

- **AAS `specificAssetIds` pattern.** The AAS practice of attaching a
  typed list of instance-level identifiers (serial number, batch ID,
  deployed unit ID) per asset directly parallels the multi-identifier-per-prim
  requirement analyzed above: each entry needs a type label and a scope
  (type-level vs. instance-level). The AAS Digital Battery
  Passport ↔ OpenUSD proof-of-concept (asluk/OpenUSD-proposals#2) confirms
  that Approach C's `assetInfo` overflow handles this list pattern without
  requiring additional schemas.

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

**Round-trip scenario: URDF → USD → modify → URDF.**

Consider a concrete round-trip workflow:

1. A UR10e robot is authored in URDF as `package://ur_description/urdf/ur10e.urdf`
2. An ingestion pipeline converts it to USD, creating `/World/UR10e`
3. An artist in Omniverse adds visual materials and adjusts joint limits
4. The modified asset is exported back to URDF for simulation in Gazebo

**Without source identifiers (today):** The originating package URI
(`package://ur_description/urdf/ur10e.urdf`), model name (`UR10e`), and
source format (`URDF`) are lost on ingest — or stored in ad-hoc `customData`
that the URDF exporter doesn't know to look for. The export pipeline must
either require manual annotation or guess the output package structure.

**With the hybrid:** The ingestion pipeline writes:
- `sourceIdentifier:ros:primaryId = "package://ur_description/urdf/ur10e.urdf"`
- `sourceIdentifier:ros:domain = "org.ros"`
- Overflow: `{packageName: "ur_description", modelName: "UR10e", sourceFormat: "URDF"}`

The URDF exporter reads `sourceIdentifier:ros:primaryId` to reconstruct the
package URI and uses the overflow metadata to restore the URDF structure.
The round-trip preserves provenance without the exporter needing to know
about ad-hoc `customData` conventions.

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

## 4.5 Three-tier scenario: IFC codeless companion + AAS overflow graduation

This scenario demonstrates the three-tier model from §6 of COMPARISON.md using
two domains at different maturity levels on the same prim.

**Setup:** A building chiller prim carries both IFC and AAS/DPP identifiers.
IFC has three stable metadata fields that have been promoted to a codeless
companion schema; AAS has a mix of stable and experimental fields spanning
overflow and a companion schema.

```usda
def Xform "Chiller_01" (
    prepend apiSchemas = [
        "SourceIdHybridAPI:ifc",
        "SourceIdHybridAPI:aas",
        "SourceIdIfcAPI:ifc",       # codeless companion (buildingSMART)
        "SourceIdAasAPI:aas"        # codeless companion (IDTA)
    ]
    assetInfo = {
        dictionary sourceIds = {
            dictionary ifc = {
                # IFC property sets — project/country-specific, stays in overflow
                string pset_ThermalPerformance_COP = "4.2"
                string pset_Classification_UniClass = "Ss_75_50_16"
            }
            dictionary aas = {
                # DPP-specific fields not yet stable enough for companion schema
                string batteryPassportVersion = "3.0.1"
                string complianceRegion = "EU"
                string recyclingCode = "CR-7822"
            }
        }
    }
)
{
    # Core schema properties (Tier 1 — governed by AOUSD)
    string sourceIdentifier:ifc:primaryId = "2O2Fr$t4X7Zf8NOew3FNr2"
    token sourceIdentifier:ifc:domain = "org.buildingsmart.ifc"
    string sourceIdentifier:ifc:label = "IFC GlobalId"

    string sourceIdentifier:aas:primaryId = "urn:dpp:bat:SN-42-LFP-2026"
    token sourceIdentifier:aas:domain = "org.idtwin.aas"
    string sourceIdentifier:aas:label = "AAS Global Asset ID"

    # IFC codeless companion properties (Tier 2 — published by buildingSMART)
    token sourceId:ifc:ifcType = "IfcChiller"
    token sourceId:ifc:ifcSchema = "IFC4x3"
    string sourceId:ifc:ifcObjectType = "Air-Cooled Scroll Chiller"

    # AAS codeless companion properties (Tier 2 — published by IDTA)
    token sourceId:aas:assetKind = "Instance"
    string sourceId:aas:idShort = "Chiller_HVAC_01"
}
```

**What this demonstrates:**

1. **Three tiers coexist cleanly.** Core schema properties, codeless companion
   properties, and overflow dicts all compose on the same prim without
   conflict. Each tier has its own namespace.

2. **Maturity maps to tier.** IFC's `ifcType` and `ifcSchema` are in the
   companion schema because they've been stable since IFC2x (20+ years).
   IFC property set values stay in overflow because they're
   project/country-specific. AAS's `assetKind` (formerly `scope`) has
   graduated from overflow to the IDTA companion schema; DPP-specific
   regulatory fields are still experimental.

3. **Per-property vs. element-wise composition.** The companion schema
   properties (`ifcType`, `assetKind`) compose per-property — an override
   layer can change `ifcType` without affecting `ifcSchema`. The overflow
   dict entries compose element-wise — overriding one key in the `ifc`
   dict doesn't discard the others, but the composition semantics are
   coarser.

4. **Independent domain evolution.** buildingSMART can update their
   companion schema (add `ifcPredefinedType`) without coordinating with
   IDTA or AOUSD. IDTA can promote `idShort` from overflow to companion
   schema on their own schedule.

**Distribution model for this scenario:**

| Schema | Publisher | Distribution |
|--------|-----------|-------------|
| `SourceIdHybridAPI` (core) | AOUSD | Ships with OpenUSD |
| `SourceIdIfcAPI` (companion) | buildingSMART | Bundled with IFC↔USD converter tools |
| `SourceIdAasAPI` (companion) | IDTA | Published as standalone plugin, bundled with AAS tooling |
| Overflow dict conventions | Each domain | Documented in AOUSD Domains Registry |

## Cross-industry synthesis

The pattern across all four verticals is consistent:

| Dimension | Approach A | Approach B | Approach C (three-tier) |
|-----------|-----------|------------|------------------------|
| Primary identifier (linkage key) | ✅ Adequate | ✅ Adequate | ✅ Schema property |
| Revision/version | ✅ Adequate | ✅ Adequate | ✅ Schema property |
| Domain-specific metadata (stable) | ✅ Natural (dict) | ❌ Requires companion schema | ✅ Codeless companion schema |
| Domain-specific metadata (experimental) | ✅ Natural (dict) | ❌ Requires companion schema | ✅ Overflow dict |
| Multi-domain on single prim | ✅ Natural | ✅ Natural | ✅ Natural |
| Shared identity across instances | ✅ Natural | ✅ Natural | ✅ Natural |
| Composite keys (configurable products) | ✅ Natural | ❌ Cannot express without extension | ✅ Companion or overflow |
| Alternative/equivalent identifiers | ✅ Natural | ✅ Natural (each gets an instance) | ✅ Natural |
| Relationship between alternatives | ✅ Metadata in dict | ❌ No mechanism | ✅ Companion or overflow |
| Type safety for stable fields | ❌ Untyped dict | ✅ Schema-validated | ✅ Companion schema |
| Discoverability for stable fields | ❌ No schema registry | ✅ Full registry | ✅ Companion in registry |

**The critical finding:** For industries with simple identifier schemes
(a string ID + optional version), both approaches are equivalent. For
industries with rich, heterogeneous identifier metadata — which includes
manufacturing, AECO, and robotics — Approach A's freeform dictionaries
handle all tested scenarios without requiring per-domain schema work.

**The three-tier refinement** addresses the gap: domains with stable
metadata fields (IFC's `ifcType`, AAS's `assetKind`) gain type safety
and discoverability through codeless companion schemas, while
experimental fields retain the zero-friction overflow path. This
resolves the tension between Approach A's flexibility and Approach B's
governance without requiring all domains to do schema work on day 1.

This is the central tension driving the hybrid recommendation in
[hybrid_analysis.md](hybrid_analysis.md).

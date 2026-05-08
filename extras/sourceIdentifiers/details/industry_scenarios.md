# Industry Scenarios — runnable USD examples per vertical

← [Back to COMPARISON.md](../COMPARISON.md)

This document is an index of the runnable USD scenarios authored
across the four industry verticals, with brief descriptions of what
each scenario exercises. The scenarios are concrete, illustrative
encodings of synthesized identifier packages — one prim composition
per vertical per mechanism.

For the **per-vertical analytical findings** (which fields surface in
each domain's authoritative spec, what shapes they take, which
mechanisms can carry them) see
[`field_classification_experiment.md`](field_classification_experiment.md).
The field experiment is the empirical source of truth for the
mechanism-vs-shape question; this document is the example anchor.

§4.5 below — the three-tier scenario for Approach C — is the
exception. It illustrates a graduation lifecycle (core schema
+ codeless companion + overflow dict) that is C-specific design depth
and does not appear elsewhere in the comparison materials.

## 4.1 Architecture, Engineering, Construction & Operations (AECO)

**Scenario:** A building with structural columns (IFC + Revit +
UniClass + OmniClass), an HVAC chiller with PLM and operational
telemetry (Windchill + SAP + OPC UA + BACnet + IFC), and rooms with
purely numeric identifiers.

**Files:**
- `examples/approach_a_assetinfo.usda` — A encoding
- `examples/approach_b_schema.usda` — B encoding
- `examples/approach_c_hybrid.usda` — C encoding
- `examples/column_d.usda` — D encoding (canonical column)
- `examples/verify_column_d.py` — schema-aware verifier for the D scenario

## 4.2 Manufacturing, Product Lifecycle & Digital Engineering

**Scenario:** A tractor assembly inspired by PTC/Windchill workflows,
with configurable products, alternative/equivalent identifiers,
feature-level identifiers, and Mercedes-Benz-style part numbering with
extension codes. References the AAS Digital Battery Passport
proof-of-concept ([asluk/OpenUSD-proposals#2](https://github.com/asluk/OpenUSD-proposals/pull/2))
for AAS structure.

**Files:**
- `examples/manufacturing_a.usda` — A encoding
- `examples/manufacturing_b.usda` — B encoding
- `examples/manufacturing_d.usda` — D encoding

## 4.3 Robotics & Simulation

**Scenario:** A multi-robot warehouse fleet with URDF/SDF source
provenance, ROS package identity, fleet assignment, sensor catalog
identifiers, and operational telemetry binding. Includes a concrete
URDF → USD → modify → URDF round-trip workflow.

**Files:**
- `examples/robotics_a.usda` — A encoding
- `examples/robotics_b.usda` — B encoding
- `examples/robotics_d.usda` — D encoding

## 4.4 Media & Entertainment

**Scenario:** Model-level asset tracking (asset DB IDs, versions,
approvals), sub-model identifiers (props/lights/materials with their
own tracking IDs), and multi-system tracking (Flow Production
Tracking + ftrack + internal asset DBs). Not separately implemented
as a runnable file — USD's existing `assetInfo` already covers the
M&E model-level case across A and D, and the surface is light enough
that the AECO and manufacturing scenarios cover the structural cases.

## 4.5 Three-tier scenario: IFC codeless companion + AAS overflow graduation (Approach C)

This scenario illustrates the three-tier graduation model under
Approach C: a core schema, codeless companion schemas published by
domain stewards, and freeform `assetInfo` overflow for fields not yet
typed.

**Setup.** A building chiller prim carries both IFC and AAS/DPP
identifiers. IFC has stable metadata fields promoted to a codeless
companion schema published by buildingSMART. AAS has a mix of stable
identifier fields in an IDTA-published companion schema and broader
DPP fields (lifecycle, compliance, sustainability) in overflow. AAS
community review confirms a Digital Product Passport encompasses
information beyond identity; those overflow fields depend on source
identifiers as a foundation but are out of scope for this mechanism —
they appear here to illustrate overflow's role as a staging area.

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
                # DPP lifecycle/compliance fields — beyond identity scope,
                # included to illustrate overflow as a staging area
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

1. **Three tiers coexist cleanly.** Core schema properties, codeless
   companion properties, and overflow dicts all compose on the same
   prim without conflict; each tier has its own namespace.
2. **Maturity maps to tier.** IFC's `ifcType` / `ifcSchema` are in the
   companion schema because they've been stable since IFC2x (20+
   years). IFC property set values stay in overflow because they're
   project/country-specific. AAS's `assetKind` graduated from overflow
   to the IDTA companion schema; DPP-specific lifecycle and compliance
   fields remain in overflow as they are beyond the identity scope of
   this mechanism.
3. **Per-property vs. element-wise composition.** Companion schema
   properties (`ifcType`, `assetKind`) compose per-property — an
   override layer can change `ifcType` without affecting `ifcSchema`.
   Overflow dict entries compose element-wise — overriding one key in
   the `ifc` dict doesn't discard the others, but the composition
   semantics are coarser.
4. **Independent domain evolution.** buildingSMART can update their
   companion schema (add `ifcPredefinedType`) without coordinating
   with IDTA or AOUSD. IDTA can promote `idShort` from overflow to
   companion schema on their own schedule.

**Distribution model for this scenario:**

| Schema | Publisher | Distribution |
|--------|-----------|-------------|
| `SourceIdHybridAPI` (core) | AOUSD | Ships with OpenUSD |
| `SourceIdIfcAPI` (companion) | buildingSMART | Bundled with IFC ↔ USD converter tools |
| `SourceIdAasAPI` (companion) | IDTA | Published as standalone plugin, bundled with AAS tooling |
| Overflow dict conventions | Each domain | Documented in AOUSD Domains Registry |

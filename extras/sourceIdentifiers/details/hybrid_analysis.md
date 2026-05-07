# Hybrid Analysis (Approach C)

← [Back to COMPARISON.md](../COMPARISON.md)

This document is the design reference for **Approach C** — a refinement of
B that adds an `assetInfo` overflow dictionary (borrowed from A) to B's
multi-apply schema, closing B's heterogeneity gap. COMPARISON.md notes
that the data leans toward D (a different refinement of B that reuses the
existing `UsdSemanticsLabelsAPI`); C is the natural fallback for the case
where a domain surfaces classification fields needing typed
non-token-array structure that `UsdSemanticsLabelsAPI` cannot represent.
The migration discussion in §7.6 is also useful for pipelines moving off
of `customData` toward any mechanism; its schema-property half maps to D's
`assetInfo["source"]` identity tier with minor adjustment.

### 7.1 The case against either approach alone

**Approach A alone** provides maximum flexibility but sacrifices
discoverability, validation, GUI integration, and governance
enforceability - the properties that a multi-stakeholder standard
needs most. It would repeat the `customData` pattern: technically
capable, but practically un-interoperable because every consumer
must know every vendor's ad-hoc dictionary structure.

**Approach B alone** provides excellent structural properties but
cannot carry the domain-specific metadata that real-world industrial
workflows require. Forcing every identifier stakeholder to register
a companion schema for their domain-specific fields would either:
(a) create schema sprawl (dozens of `*IdentifierAPI` schemas), or
(b) push metadata into `customData` - recreating exactly the
fragmentation problem the proposal aims to solve.

### 7.2 Hybrid mechanism: B + metadata overflow dictionary

C combines Approach B's structural advantages with Approach A's metadata
flexibility:

**Use the multi-apply schema (Approach B) as the base**, providing
typed, schema-backed common fields that all tools can discover and
validate. **Use Approach A's `assetInfo["sourceIds"]` sub-dictionaries
as the overflow mechanism** for domain-specific metadata.

This works because USD schemas cannot define dictionary-typed properties
- `dictionary` is not in `SdfValueTypeNames`. It is only available as
metadata (`assetInfo`, `customData`). Rather than fight this constraint,
the hybrid embraces it: **the schema carries the governed common fields;
`assetInfo` carries the freeform domain-specific data.** The two
mechanisms coexist on the same prim, linked by the domain key.

```usda
class "SourceIdHybridAPI" (
    inherits = </APISchemaBase>
    customData = {
        token apiSchemaType = "multipleApply"
        token propertyNamespacePrefix = "sourceIdentifier"
    }
)
{
    # Typed common fields (schema-validated, GUI-visible)
    # usdGenSchema prepends "sourceIdentifier:<instance>:" automatically
    # via propertyNamespacePrefix, so definitions use bare names:
    string primaryId = ""
    string revision = ""
    token domain = ""
    string label = ""

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
- `apiSchemas` list declares which domains are present (like glTF `extensionsUsed`
  or W3C declared feature policies)
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

### 7.3a Instance-name-to-dict-key linkage

The hybrid's key convention — `SourceIdHybridAPI:windchill` matches
`assetInfo["sourceIds"]["windchill"]` — is enforced by the convenience API
(`GetDomainMetadata()` uses the instance name to locate the overflow dict),
not by the schema system itself. Nothing structurally prevents authoring a
schema instance `SourceIdHybridAPI:wc` with an overflow dict key `windchill`.

This is a class of error that pure-schema (B) and pure-dict (A) approaches
cannot produce. Mitigation:

1. **Convenience API enforcement.** The `SetDomainMetadata()` and
   `GetDomainMetadata()` methods always use the instance name as the dict
   key, so tools using the API cannot create mismatches.
2. **Validator rule.** The hybrid's validation specification should include a
   rule: "for each `SourceIdHybridAPI:<name>` instance, if
   `assetInfo["sourceIds"]` contains a key that does not match any applied
   instance name, emit a warning." This catches orphaned overflow dicts and
   mismatched keys.
3. **Documentation.** The convention must be prominently documented in the
   schema's docstring and any onboarding guides.

### 7.4 Composition behavior of the hybrid

The hybrid composes as follows:

- **Schema properties** (`primaryId`, `revision`, `domain`, `label`):
  per-property composition (strongest opinion wins per attribute).
  Safe and predictable.

- **`assetInfo["sourceIds"]` dictionaries:** element-wise composition
  at each nesting level (standard `assetInfo` behavior). An override
  layer can add new keys to a domain's metadata dictionary without
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
   were expressed as companion schemas (Approach B's workaround), the
   property count would be even higher than the hybrid's `assetInfo`
   overhead.

### 7.5a VtDictionary access performance

Reading overflow metadata requires walking a nested dictionary chain:
`assetInfo` → `sourceIds` → `<domain>` → `<key>`. This path is not
indexed by the USD composition engine in the way that schema property
names are indexed by `SdfPath` + attribute name.

For **per-prim reads** (e.g., a GUI panel displaying a single prim's
identifiers), the overhead is negligible — dictionary lookups are O(1)
hash operations at each level.

For **full-stage queries** ("find all prims whose Windchill
`navigationType` matches a given filter"), the query requires a full
stage traversal with dictionary inspection at each prim. This is no
worse than Approach A (which faces the same traversal) and comparable
to Approach B for non-indexed queries. In production, both approaches
benefit from **external indexing** — the mechanism must make building
such indexes tractable, which it does (schema properties via
`GetAll()` + attribute access, overflow dicts via the convenience API's
`GetDomainMetadata()`).

The hybrid's schema properties (`primaryId`, `domain`) — the fields most
commonly used in cross-stage queries — benefit from the faster
property-access path. Domain-specific overflow fields, which are
typically queried only within a known subtree, use the dictionary path.
This aligns the access-performance characteristics with the query
patterns.

### 7.5 Governance model for the hybrid

The three-tier AOUSD Domains Registry (Section 6.2) applies directly:

1. **Registration:** Stakeholder registers a domain key and instance name
   in the registry. Specifies their `metadata` dictionary schema in
   their published specification.

2. **Validation:** Common fields validated by the USD schema system.
   Domain-specific `metadata` validated by external validators per the
   stakeholder's specification (same as Approach A).

3. **Promotion:** When a domain-specific metadata field proves universally
   useful, it can be promoted to a typed property on the base schema
   (schema versioning tracks this). The `metadata` dictionary remains
   as an overflow mechanism.

### 7.6 Migration path from existing conventions

Pipelines currently using `customData`, `displayName`, or ad-hoc
`assetInfo` conventions can migrate incrementally:

1. Apply `SourceIdHybridAPI:<domain>` to prims that carry identifiers.
2. Move the primary identifier value to `primaryId`.
3. Move revision/version to `revision`.
4. Set `domain` to the registered reverse-DNS key.
5. Move remaining metadata to the `metadata` dictionary.
6. Remove old `customData`/`displayName` entries.

This can be done per-layer, per-domain, without disrupting existing
composition. No big-bang migration required.

**Concrete example: IFC pipeline migration.**

A pipeline currently storing IFC GlobalId in `customData`:

```usda
# Before (ad-hoc customData convention)
def Mesh "Column_C14" (
    customData = {
        string ifcGlobalId = "2O2Fr$t4X7Zf8NOew3FNr2"
        string ifcType = "IfcColumn"
    }
)
{
}
```

Migrated to Approach C:

```usda
# After (hybrid: schema for linkage key, overflow for domain metadata)
def Mesh "Column_C14" (
    prepend apiSchemas = ["SourceIdHybridAPI:ifc"]
    assetInfo = {
        dictionary sourceIds = {
            dictionary ifc = {
                string ifcType = "IfcColumn"
                string schema = "IFC4x3"
                string objectType = "W14x90"
            }
        }
    }
)
{
    string sourceIdentifier:ifc:primaryId = "2O2Fr$t4X7Zf8NOew3FNr2"
    token sourceIdentifier:ifc:domain = "org.buildingsmart.ifc"
    string sourceIdentifier:ifc:label = "IFC GlobalId"
}
```

The migration moves the linkage key (`ifcGlobalId`) to the schema's
`primaryId`, adds domain registration, and places IFC-specific metadata
in the overflow dict. The old `customData` entries can be removed. This
can be done per-layer without disrupting existing composition.

### 7.6a AAS Digital Battery Passport mapping

**How the hybrid maps to AAS concepts:**

| AAS concept | Approach C mapping |
|-------------|-------------------|
| Submodel `semanticId` | Schema `domain` token (e.g., `org.idta.dpp`) |
| `globalAssetId` vs `specificAssetIds` | `scope` convention in overflow dict (or optional schema token — open question) |
| Submodel elements (custom fields) | `assetInfo` overflow dictionary |
| Asset Administration Shell identity | `primaryId` string |

AAS's type-level / instance-level distinction (`globalAssetId` vs `specificAssetIds`)
could map to a `scope` value in the overflow dict or an optional schema token —
whether this belongs in the base schema or is domain-specific is an open question
(see COMPARISON.md §3.5). The overflow dictionary carries DPP-specific fields
without requiring a new compiled schema.

**USDA snippet — AAS Digital Battery Passport (Approach C):**

```usda
def "BatteryPack_SN42" (
    prepend apiSchemas = ["SourceIdHybridAPI:dpp"]
    assetInfo = {
        dictionary sourceIds = {
            dictionary dpp = {
                string batteryModel = "LFP-280Ah-48V"
                string chemistry = "LFP"
                string manufacturingDate = "2025-03-15"
                string manufacturingPlant = "DE-RWE-02"
            }
        }
    }
)
{
    string sourceIdentifier:dpp:primaryId = "urn:idta:dpp:battery:SN42:2025"
    token  sourceIdentifier:dpp:domain    = "org.idta.dpp"
    # NOTE: scope could alternatively live in the assetInfo overflow dict
    # rather than as a schema property — see COMPARISON.md §3.5 open question
    token  sourceIdentifier:dpp:scope     = "instance"
    string sourceIdentifier:dpp:label     = "IEC 62474 Digital Battery Passport"
}
```

The `scope = "instance"` value flags this as a serial-number-level identifier
(vs. `"type"` for a product family / part designation). Whether `scope` belongs in
the schema or the overflow dict is an open question (see COMPARISON.md §3.5).
DPP-specific fields land in the `assetInfo` overflow with no schema changes required.

**Validation.** A community contributor built a bidirectional AAS DPP ↔ OpenUSD
mapping (asluk/OpenUSD-proposals#2) exercising both Approach A and B. The hybrid
pattern absorbed all DPP-specific fields in the overflow dictionary, confirming that
no companion schema is needed for this use case.

### 7.7 Adoption shape (if C is used)

If a domain or pipeline ever needs the C-tier shape, the adoption profile
is:

- A multi-apply `SourceIdHybridAPI` ratified and shipped (or distributed
  as a plugin), carrying typed `primaryId`, `revision`, `domain`, `label`
  properties.
- An AOUSD Domains Registry — mechanism-independent — modeled on Khronos
  glTF's `Prefixes.md` and W3C's WICG incubation: low-barrier vendor
  registration, three-tier promotion path (vendor → multi-vendor →
  AOUSD-standard), GitHub-based process. The Domains Registry stands as
  a recommendation regardless of which mechanism is adopted, including D.
- `assetInfo["sourceIds"][<domain>]` overflow for domain-specific metadata
  the schema does not carry.

The four-common-fields schema does not appear in D, which dissolves them
(`domain` ≡ apiSchema instance system name, `label` ≡ facet name,
`revision` per-system in `assetInfo`, `primaryId` ≡ `identifier` dict
key). So a pipeline that adopts D and later needs C-tier typing for a
specific field would publish a focused codeless companion schema for that
field rather than reintroduce all four common fields.

---


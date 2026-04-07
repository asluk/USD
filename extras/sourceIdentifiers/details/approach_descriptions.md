# Approach Descriptions

← [Back to COMPARISON.md](../COMPARISON.md)

## Approach A: `assetInfo` stratified sub-dictionaries

**Module:** `pxr/usd/usdSourceId/`
**Schema type:** Non-applied API schema (`UsdSourceIdAPI`)
**Precedent:** `UsdModelAPI`

> **Design note:** This schema is **non-applied**, following the precedent
> set by `UsdModelAPI`. Like `UsdModelAPI`, it wraps `assetInfo` metadata
> without requiring explicit application or an `apiSchemas` listing.
> The schema provides a convenience API; the data's presence in
> `assetInfo["sourceIds"]` is the signal. There is no `Apply()` method —
> you construct the API object directly on any prim.
>
> This differs from `UsdMediaAssetPreviewsAPI`, which is single-apply despite
> also wrapping `assetInfo`. The non-applied design is more honest: Approach A
> defines no properties and adds no built-in behavior to the prim definition.
> Making it applied would force an `apiSchemas` listing that carries no
> structural information — the schema contributes nothing to
> `UsdPrimDefinition`. `UsdModelAPI` faces the same situation (wrapping
> `kind` and `assetInfo` metadata) and is non-applied for exactly this reason.

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
  understanding the merge semantics (see [composition_behavior.md](composition_behavior.md)).

- **No contribution to `UsdPrimDefinition`.** Because data lives in
  metadata rather than properties, it does not appear in schema-aware
  GUI panels, cannot have fallback values, and cannot be validated by
  the schema system.

**`UsdModelAPI` precedent.** The non-applied design follows `UsdModelAPI`,
which is the closest existing analog in the USD codebase:

| | `UsdModelAPI` | `UsdSourceIdAPI` (Approach A) |
|---|---|---|
| Schema type | Non-applied | Non-applied |
| Data location | `assetInfo["identifier"]`, `assetInfo["name"]`, `assetInfo["version"]` | `assetInfo["sourceIds"][<domain>]` |
| Properties | None | None |
| `apiSchemas` listing | No | No |
| Discovery | Check `assetInfo` directly | Check `assetInfo["sourceIds"]` directly |
| Construction | `UsdModelAPI(prim)` | `UsdSourceIdAPI(prim)` |

Both schemas are pure convenience wrappers around `assetInfo` metadata.
Neither adds structural information to the prim definition, so neither
benefits from being applied. `UsdMediaAssetPreviewsAPI` is single-apply
despite wrapping `assetInfo["previews"]`, but this is arguably an anomaly
— it was authored before the non-applied pattern was well-established.

**C++ API usage:**

```cpp
// Non-applied: construct directly, no Apply() needed
UsdSourceIdAPI api(prim);

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

## Approach B: Multi-apply schema with typed properties

**Module:** `pxr/usd/usdSourceIdSchema/`
**Schema type:** Multi-apply API schema (`UsdSourceIdSchemaAPI`)
**Precedent:** `UsdSemanticsLabelsAPI`, `UsdCollectionAPI`, `UsdPhysicsLimitAPI`

**Mechanism.** Each external system is represented as an instance of a
multi-apply schema, with typed properties under a namespaced prefix:

```usda
def Mesh "Column_C14" (
    prepend apiSchemas = [
        "SourceIdSchemaAPI:ifc",
        "SourceIdSchemaAPI:windchill"
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
  - `primaryId` (string) - the main linkage key
  - `revision` (string) - version/revision designator
  - `domain` (token) - formal reverse-DNS domain identifier
  - `label` (string) - human-readable description

- **Contributes to `UsdPrimDefinition`.** Properties appear in schema-aware
  GUIs automatically. Fallback values (empty strings) mean unauthored
  properties are visible and editable. Schema-driven validation is built in.

- **Per-property composition.** Each property composes independently.
  Overriding `sourceIdentifier:windchill:revision` does NOT affect
  `sourceIdentifier:windchill:primaryId` - they are separate attributes
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
auto api = UsdSourceIdSchemaAPI::Apply(prim, TfToken("windchill"));

// Set properties
api.CreatePrimaryIdAttr(VtValue(std::string("VR:wt.part.WTPart:23639563")));
api.CreateRevisionAttr(VtValue(std::string("Rev.C")));
api.CreateDomainAttr(VtValue(TfToken("com.ptc.windchill")));

// Query
std::string id;
api.GetPrimaryIdAttr().Get(&id);

// List all instances on a prim
std::vector<TfToken> instances = UsdSourceIdSchemaAPI::GetAll(prim);
```

## Side-by-side summary

| Aspect | Approach A | Approach B |
|--------|-----------|------------|
| Data location | `assetInfo` metadata | Prim properties |
| Schema type | Non-applied | Multi-apply |
| Properties defined | None | 4 per instance |
| Domain metadata | Freeform dictionary | Fixed set (extensible via companion schemas) |
| Discoverability | Must check `assetInfo["sourceIds"]` exists | `apiSchemas` list + `HasAPI<>()` |
| Fallback values | None | Empty strings |
| GUI presentation | Requires custom code | Automatic |
| Composition | Per dict key (element-wise) | Per property (independent) |

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
> also wrapping `assetInfo`. The non-applied design for Approach A
> is a deliberate choice: the schema defines no properties and adds no
> built-in behavior to the prim definition. Making it applied would force an
> `apiSchemas` listing that carries no structural information — the schema
> contributes nothing to `UsdPrimDefinition`. `UsdModelAPI` faces the same
> situation (wrapping `kind` and `assetInfo` metadata) and is non-applied
> for exactly this reason.

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

- **AAS type-vs-instance scoping (open question).** AAS distinguishes
  type-level identifiers (part families) from instance-level (serial numbers)
  via `globalAssetId` vs `specificAssetIds`. The schema *could* add an
  optional `scope` token (`"type"`, `"instance"`, or unset), but many
  domains have no such distinction at the identifier level (IFC GlobalId
  identifies each entity uniquely regardless of type vs. instance; ECLASS
  is inherently type-level; glTF and MaterialX have no equivalent external
  identifier scoping). Whether `scope` belongs in the base
  schema or in the domain-specific `assetInfo` overflow dict is an open
  question. The existing `domain` token already serves as the authoritative
  identifier type label (PLM, IFC, ERP, ECLASS).

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

## Approach C: Refinement of B (B + assetInfo overflow)

**Module:** `pxr/usd/usdSourceIdHybrid/`
**Schema type:** Multi-apply API schema (`UsdSourceIdHybridAPI`)
**See:** [hybrid_analysis.md](hybrid_analysis.md) for the full design rationale,
trade-offs, and migration path.

C is a refinement of B: same multi-apply schema for the four common
fields, plus A's `assetInfo` overflow dictionary for fields the schema
cannot carry, keyed by matching the schema instance name to the
`assetInfo["sourceIds"]` dictionary key. The overflow tier carries
heterogeneous typed fields (timestamps, numeric measures with units,
composite refs, polymorphic typed values) that the four common
schema-typed fields cannot carry on their own.

---

## Approach D: Refinement of A (A + Labels for classification facets)

**Module:** `pxr/usd/usdSourceId/` — the same module as Approach A.
D inherits A's mechanism, so it inherits A's convenience wrapper.
**Schema type:** Non-applied API schema (`UsdSourceIdAPI`) wrapping
the `assetInfo` identifier tier; plus `UsdSemanticsLabelsAPI` (shipping
in OpenUSD 24.11) applied per controlled-vocabulary classification facet.
No new applied schema is introduced.
**Precedent:** `UsdModelAPI` for the non-applied `assetInfo` wrapper
(same as Approach A); `UsdSemanticsLabelsAPI` for the classification
facets.

D is structurally a refinement of A: take A's `assetInfo` overflow
mechanism for identity, identity-adjacent fields, and the heterogeneous
typed surface, and add `UsdSemanticsLabelsAPI` applied per classification
facet for per-facet discoverability and composition on the
controlled-vocabulary axis. Earlier framings positioned D as a
"refinement of B" (treating Labels as an alternative to B's typed common
fields); structurally that's a comparison-level positioning, not a
mechanism relationship — D shares no mechanism with B beyond the
`apiSchemas` list, and shares the entire `assetInfo` tier with A.

**Provenance note.** D was constructed downstream of the proposal
during this comparison work, *not* a peer candidate the proposal
itself authorized. The proposal explicitly authorized A and B and
hinted at C as a "hybrid or alternative." D is included as an
explored idea so its tradeoffs can be evaluated alongside the
authorized candidates. The earlier draft of this document presented
D conclusorily, and earlier drafts of the comparison materials
narrated a leaning toward D; both have been retracted. The retraction
isn't grounded in *D being unable to carry the heterogeneous typed
surface* — `assetInfo["source"][<system>]` is a full overflow tier
(same `VtDictionary` value-type set as Approach A's
`assetInfo["sourceIds"]`), so D inherits A's heterogeneity coverage.
What the retraction is grounded in is the methodological problem
upstream of the comparison itself: the leaning was constructed from a
scoring framework built after D was already in mind, the framework's
dimensions weren't derived from the proposal's authorized principles,
and the empirical census surfaces typed heterogeneity the earlier
"no field surfaced needing typed structure" framing was about to
build leverage on. Structurally, D = A's mechanism + Labels for
classification facets; the comparison treats D symmetrically with
A/B/C and reports per-mechanism trade-offs rather than a leaning.

**Mechanism.** Decomposes the source-identifiers problem along its natural
seams:

- **Identity axis** — opaque pointers back into the source system live in
  `assetInfo["source"][<system>]`, with conventional keys `identifier` (the
  primary ID string), optional `version`, and any identity-adjacent strings
  that round-trip into the system (e.g., `displayNumber`, `serialNumber`,
  `navigationType`).
- **Classification axis** — controlled-vocabulary terms drawn from each
  system's published namespace ride `SemanticsLabelsAPI:<system>:<facet>`
  instances, with values in `token[] semantics:labels:<system>:<facet>`
  properties. Each facet is its own apiSchema instance — finer-grained than
  B/C's per-system instances.

```usda
def Mesh "Column_C14" (
    apiSchemas = ["SemanticsLabelsAPI:ifc:type",       "SemanticsLabelsAPI:ifc:objectType",
                  "SemanticsLabelsAPI:revit:category", "SemanticsLabelsAPI:revit:familyType",
                  "SemanticsLabelsAPI:revit:mark",     "SemanticsLabelsAPI:revit:level"]
    assetInfo = {
        dictionary source = {
            dictionary ifc   = { string identifier = "2O2Fr$t4X7Zf8NOew3FNr2" }
            dictionary revit = { string identifier = "847562"
                                 string version = "2026.1" }
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
}
```

**Key characteristics:**

- **No new applied schema.** D requires no ratification, no codegen, no
  plugin distribution. The applied schema (`UsdSemanticsLabelsAPI`) is
  already in OpenUSD core. Vendors and standards bodies can adopt D the
  day the AOUSD Domains Registry publishes their system key.

- **The four "common fields" of B/C dissolve.**
  - `domain` ≡ apiSchema instance system name (`revit`).
  - `label` ≡ apiSchema instance facet (`revit:familyType`) plus the
    registered domain's display label.
  - `revision` is per-system in `assetInfo` (because not every system has
    a revision concept).
  - `primaryId` is the `identifier` dict key in `assetInfo`.

- **Per-facet apiSchema instances expose structure.** A consumer asking
  "what facets does Revit carry on this prim?" answers from the apiSchemas
  list directly, without parsing properties or dictionaries — finer-grained
  than B/C's per-system instances.

- **The identity vs. classification split is the working rule.** Identifier
  strings and identity-adjacent fields (anything that must round-trip
  exactly into the source system) go in `assetInfo`. Controlled-vocabulary
  terms (anything drawn from a published namespace) ride
  `SemanticsLabelsAPI`. Borderline fields (e.g., Windchill `displayNumber`,
  Mercedes `extensionCode`) are open in AOUSD review — see COMPARISON.md
  Open Questions.

- **Composition** is per-property for label arrays (token arrays, finer
  than B/C's per-system instance) and per-key for `assetInfo` strings
  (same as A and the overflow tier of C). For non-timevarying strings —
  which describes nearly all identifier and label values — composition
  behavior is effectively equivalent to A/B/C at the granularity authors
  actually use.

**No C++ API required.** Authors and consumers use the existing
`UsdSemanticsLabelsAPI` and `UsdPrim::GetAssetInfo()` APIs. No
identifier-specific class or wrapper is needed.

---

## Side-by-side summary

| Aspect | Approach A | Approach B | Approach C | Approach D |
|--------|-----------|------------|------------|------------|
| Identity location | `assetInfo` metadata | Prim properties | Prim properties | `assetInfo` metadata |
| Classification location | `assetInfo` metadata | Prim properties | `assetInfo` overflow | `SemanticsLabelsAPI` token arrays |
| New applied schema needed? | No | Yes | Yes | **No** |
| `apiSchemas` granularity | None | Per-system | Per-system | **Per-facet** |
| Domain metadata | Freeform dictionary | Fixed 4 fields | Fixed 4 + overflow | Token labels + identity dict |
| Discoverability | Parse `assetInfo` | `apiSchemas` + `HasAPI<>()` | `apiSchemas` + parse overflow | `apiSchemas` (per-facet) |
| Composition (non-timevarying) | Per dict key | Per property | Per property + per key | Per property + per key |

## Terminology note: `metadata` sub-dictionary key

Approach A uses the key `metadata` within each domain's source identifier
dictionary to hold additional fields (e.g.,
`assetInfo["sourceIds"]["windchill"]["metadata"]["displayNumber"]`). This
term is overloaded in USD, where "metadata" already refers to the
prim/property metadata system (`GetMetadata()`, `SetMetadata()`,
`customData`, `assetInfo` itself).

A production implementation should consider alternative names for this
sub-dictionary key to avoid confusion:

- **`extensions`** — following glTF's `extensions` / `extras` precedent,
  where `extensions` carries governed vendor data alongside a core schema.
- **`domainData`** — explicit about what it contains.
- **`extra`** — shorter, following the glTF `extras` pattern.

The prototype uses `metadata` for clarity during the comparison phase.
The final key name is a minor detail to be resolved during the solution
proposal.

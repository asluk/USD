# Identifier-Package Field Census

← [Back to COMPARISON.md](../COMPARISON.md)

> **Note on standing.** This document is the empirical anchor for the
> de-leaning of the surrounding comparison work. The two items
> previously listed as deferred upstream of this experiment landed in
> the 2026-05-07 rebuild:
>
> - The vendor-adoption scoring in
>   `stress_tests/vendor_adoption_analysis.{py,json}` is now derived
>   from proposal 105's eight authorized principles. The earlier
>   scoring (eight dimensions Claude invented during PR development,
>   not derived from the proposal's principles, biased toward
>   Approach D by construction) is preserved as
>   `vendor_adoption_analysis_legacy.py` for regression inspection.
> - The schema-distribution friction tension is resolved as
>   conditional — currently elevated, trending lighter as the AOUSD
>   Build IG epic lands.
>
> The findings below remain independent of those resolutions — they
> are field-by-field readings of authoritative spec surfaces,
> reproducible from the cited sources. Mechanism choice draws from
> this evidence *plus* the principle-derived scoring; the comparison
> as a whole does not assert a single mechanism leaning.

## Why this experiment

The proposal ([PixarAnimationStudios/OpenUSD-proposals#105](https://github.com/PixarAnimationStudios/OpenUSD-proposals/pull/105))
frames source identifiers as *"metadata packages, not atomic strings"*
and notes that *"different domains need different identifier
fields"* — a heterogeneity that *"the more pronounced the contents,
the more this tension favors dictionaries or a family of
domain-specific schemas"* (B's cons, ¶1). This is the central
heterogeneity tension the proposal asked AOUSD to weigh.

Subsequent comparison materials in this PR built up a downstream
claim that goes further:

> *"No domain-specific field surfaced that required typed
> non-token-array structure."*
> *"Token arrays + identifier strings carried every metadata case
> tested."*
> ([details/formality_and_distribution.md](formality_and_distribution.md))

That is a stronger claim than the proposal made. It says, in effect,
that the heterogeneity the proposal asked AOUSD to weigh is *empty* in
the verticals surveyed — that real identifier packages bundle only
identifier strings + classification token arrays, not heterogeneous
typed fields. If true, the proposal's heterogeneity tension goes away.
That is the claim this experiment tests.

The experiment does not pick a mechanism. It surveys *what real source
systems actually bundle with their identifiers* and reports whether
those packages are heterogeneously typed in the proposal's sense.

## Pre-registered classification

Each field surveyed is sorted into one of four buckets, drawn from the
proposal's own seam between identity and the heterogeneous metadata
packaged around it:

| Bucket | Test |
|---|---|
| **Identity** | Opaque round-trip pointer back into the source system — the identity tier of the package. No semantic value outside the source system. |
| **Identity-adjacent** | Display numbers, marks, human-readable labels paired with the identifier — locate or display the identifier without being it. |
| **Controlled-vocabulary classification facets** | Terms drawn from a system's published controlled vocabulary. Enumerable strings; native shape is a string or list of strings. The classification surface. |
| **Heterogeneous typed fields** | Per-domain fields with native typed shape that goes beyond strings: numeric measures with units, dates and timestamps, structured references between system entities, polymorphic typed values (e.g. AAS `Property.value` across the XSD type set), recursive composites. The proposal's heterogeneity surface. |

### Rules of the experiment

1. **Cite the source.** Each field is sourced from its authoritative
   spec (IFC schema HTML, AAS metamodel, ROS/SDF/URDF specs, Windchill
   REST API docs, SAP Material Master / S/4HANA API, OpenAssetIO trait
   definitions, MovieLabs OMC, ShotGrid REST). The
   [industry_scenarios.md](industry_scenarios.md) description is
   *not* a source — that document was constructed downstream of the
   leaning under review and would import its framing into this
   experiment.
2. **Native data type comes from the spec.** Whether a field is a
   string, controlled vocabulary, numeric measure with unit, date,
   composite reference, or polymorphic typed value is determined by
   the source spec, not by how a USD encoding might choose to
   serialize it.
3. **Don't force a bucket.** Borderline / disputed fields are reported
   borderline.
4. **Field set is representative, not exhaustive.** Each vertical's
   field set is drawn from the system's mandatory + commonly-authored
   identifier surface, not cherry-picked. If anything is excluded
   for a reason other than "not on the identifier surface," the
   exclusion is noted in line.
5. **One bucket per field.** A field that is genuinely both (e.g. a
   string with controlled-vocabulary semantics that also round-trips)
   is bucketed by its primary semantics in the source spec, with the
   secondary use noted.

### What the experiment can and cannot conclude

It **can** conclude: in the field set surveyed, the following fields
fall into the heterogeneous-typed-fields bucket — by name, with native
types and citations.

It **cannot** conclude: that this field set is exhaustive, that no
future domain will surface heterogeneous typed fields, or that any
one mechanism is the right answer. AOUSD review weighs the result
and the mechanism choice that follows from it.

## Field census

### Vertical 1 — AECO (IFC, Revit, UniClass, OmniClass)

**Scope of "fields that travel with the identifier."** Each of these
external systems has an opaque or semi-opaque identifier (IFC GlobalId,
Revit UniqueId/ElementId, UniClass/OmniClass code) plus a small set of
fields the consuming side typically needs alongside the identifier to
make sense of it: the entity type, classification codes, mark/tag,
schema version. Property-set values (IFC `Pset_*` numeric measures,
Revit instance parameters with `StorageType.Double`/`Integer`) are the
asset's *content*, not part of the identifier package, and are excluded
from this census on those grounds. They are surveyed cross-cutting in
[§ Property-set excursion](#property-set-excursion-aeco-and-pim) below.

#### IFC (ISO 16739, IFC4x3 lexical reference)

| Field | Native IFC type | What it carries | Bucket |
|---|---|---|---|
| `GlobalId` ([IfcRoot](https://standards.buildingsmart.org/IFC/RELEASE/IFC4_3/HTML/lexical/IfcRoot.htm)) | `IfcGloballyUniqueId` (string, base64-encoded GUID) | The opaque pointer back into the IFC file | **Identity** |
| `Name` ([IfcRoot](https://standards.buildingsmart.org/IFC/RELEASE/IFC4_3/HTML/lexical/IfcRoot.htm)) | `IfcLabel` (string) | Optional name "for use by the participating software systems or users" | **Identity-adjacent** (display) |
| `Description` ([IfcRoot](https://standards.buildingsmart.org/IFC/RELEASE/IFC4_3/HTML/lexical/IfcRoot.htm)) | `IfcText` (string) | Optional informative comment | **Identity-adjacent** (display) |
| `Tag` ([IfcElement](https://standards.buildingsmart.org/IFC/RELEASE/IFC4_3/HTML/lexical/IfcElement.htm)) | `IfcIdentifier` (string) | Tag/label at the occurrence level — serial/position number | **Identity-adjacent** (round-trip-ish but a different ID space) |
| Entity type (`IfcColumn`, `IfcWall`, …) | enumeration of IFC entity names | The IFC class name itself; controlled vocabulary published by buildingSMART | **Controlled-vocabulary classification facets** |
| `PredefinedType` ([IfcColumn](https://standards.buildingsmart.org/IFC/RELEASE/IFC4_3/HTML/lexical/IfcColumn.htm)) | `IfcColumnTypeEnum`, `IfcWallTypeEnum`, … (controlled enum per entity) | Subtype within the entity (`COLUMN`, `PILASTER`, `USERDEFINED`, …) | **Controlled-vocabulary classification facets** |
| `ObjectType` ([IfcObject](https://standards.buildingsmart.org/IFC/RELEASE/IFC4_3/HTML/lexical/IfcObject.htm)) | `IfcLabel` (string) | User-defined subtype string when `PredefinedType` is `USERDEFINED` | **Controlled-vocabulary classification facets** (free-text label, but its role is naming a vocabulary term) |
| IFC schema version (e.g. `IFC4X3_ADD2`) | string identifier per buildingSMART | Which IFC schema produced this file | **Controlled-vocabulary classification facets** |

**`IfcOwnerHistory`** (the audit-trail metadata bundle attached to every
`IfcRoot` instance via the `OwnerHistory` reference) is reported separately
because it is a structured composite, not a single field:

| Sub-field | Native IFC type | Bucket |
|---|---|---|
| `OwningUser` | `IfcPersonAndOrganization` (composite) | Heterogeneous typed field (composite reference) |
| `OwningApplication` | `IfcApplication` (composite) | Heterogeneous typed field (composite reference) |
| `State` | `IfcStateEnum` (`READWRITE`, `READONLY`, `LOCKED`, …) | Controlled-vocabulary classification facets |
| `ChangeAction` | `IfcChangeActionEnum` (`NOCHANGE`, `MODIFIED`, `ADDED`, `DELETED`, `MODIFIEDADDED`, `MODIFIEDDELETED`, `NOTDEFINED`) | Controlled-vocabulary classification facets |
| `LastModifiedDate` | `IfcTimeStamp` (integer seconds since epoch, per ISO 10303) | **Heterogeneous typed fields** (numeric, semantically a timestamp) |
| `CreationDate` | `IfcTimeStamp` (integer seconds since epoch) | **Heterogeneous typed fields** (numeric, semantically a timestamp) |

`IfcOwnerHistory` is not "the identifier," but it is the metadata bundle
buildingSMART specifies as traveling with every identified IFC entity in
the model. Source: [IfcOwnerHistory](https://standards.buildingsmart.org/IFC/RELEASE/IFC4_3/HTML/lexical/IfcOwnerHistory.htm).

#### Revit (Autodesk Revit API 2024 reference)

| Field | Native .NET type | What it carries | Bucket |
|---|---|---|---|
| `UniqueId` ([Element](https://help.autodesk.com/cloudhelp/2024/ENU/Revit-API/files/Revit_API_Developers_Guide/Introduction/Elements_Essentials/Revit_API_Revit_API_Developers_Guide_Introduction_Elements_Essentials_General_Properties_html.html)) | `String` (GUID-shaped, project-portable) | The opaque pointer back into Revit (cross-project) | **Identity** |
| `Id` (`ElementId`) | `ElementId` (wrapping `int`/`long`) | Integer ID unique within a single Revit project | **Identity** (numeric — see note below) |
| `Category` | `Category` reference (resolves to a category name string) | Built-in category, controlled vocabulary | **Controlled-vocabulary classification facets** |
| `LevelId` | `ElementId` reference to a Level element | Reference to another Revit element | **Heterogeneous typed fields** (relationship) |
| `Mark` (`ALL_MODEL_MARK` parameter) | `String` (parameter `StorageType.String`) | User-authored per-instance mark (per-project unique by convention) | **Identity-adjacent** |
| `Type Mark` (`ALL_MODEL_TYPE_MARK`) | `String` (parameter `StorageType.String`) | Type-level mark | **Controlled-vocabulary classification facets** (controlled by template) |
| Family / Type names (e.g. `W14x90`) | `String` | Family + type strings | **Controlled-vocabulary classification facets** |
| `OwnerViewId`, `GroupId`, `AssemblyInstanceId`, `DesignOption` | `ElementId` (each) | References to other Revit elements | **Heterogeneous typed fields** (relationship — `ElementId` is a typed reference, not a string) |

Note on `ElementId`: Autodesk's API exposes it as a typed reference object
that wraps a numeric identifier. When *transported out of Revit* to USD it
is conventionally serialized as a string of the integer; that
serialization choice doesn't change its native type. As an opaque pointer
back into Revit it is identity. As a relationship pointer to another
element (`LevelId`, `GroupId`, etc.), the round-trip target is a different
element, which makes it a typed relationship in the source system.

#### UniClass and OmniClass (classification systems, AECO)

| Field | Native type | What it carries | Bucket |
|---|---|---|---|
| `Ss_25_10_30` style code ([UniClass 2015 Systems table](https://uniclass.thenbs.com/taxon/Ss_25_10_30/)) | String (4-segment, hierarchical) | A controlled-vocabulary code from a published table | **Controlled-vocabulary classification facets** |
| Title (e.g. `Framed partition systems`) | String | The published display title for the code | **Controlled-vocabulary classification facets** |
| Table identifier (e.g. `Ss`) | String / token (small enum: `Ss`, `Pr`, `EF`, `Ac`, …) | Which UniClass table the code belongs to | **Controlled-vocabulary classification facets** |
| OmniClass `23-13 11 13` | String (table-section format) | Same shape as UniClass — table + numeric segments | **Controlled-vocabulary classification facets** |

Note: the hierarchical structure of UniClass/OmniClass codes (table prefix
+ digit groups) is *implicit* in the string. A consumer that needs the
hierarchy explicitly can split on `_` / spaces; the canonical form is the
string itself. So the field is a string from a published vocabulary —
controlled-vocabulary classification is the right bucket.

#### AECO bucket counts (12 fields surveyed; OwnerHistory 6 sub-fields surveyed separately)

| Bucket | Count (12 main) | Count (6 OwnerHistory) | Total |
|---|---|---|---|
| Identity | 3 (IFC `GlobalId`, Revit `UniqueId`, Revit `Id`) | 0 | 3 |
| Identity-adjacent | 3 (IFC `Name`, `Description`, `Tag`; Revit `Mark`) | 0 | 4 (counts Revit `Mark`) |
| Controlled-vocabulary classification facets | 7 (IFC entity, `PredefinedType`, `ObjectType`, IFC schema version, Revit `Category`, `Type Mark`, family/type names, UniClass/OmniClass code/title/table) | 2 (`State`, `ChangeAction`) | 9 |
| Heterogeneous typed field | 2 (Revit `LevelId`/`GroupId`/`OwnerViewId`/`AssemblyInstanceId`/`DesignOption` — counted as "typed relationship" once) | 4 (`OwningUser`, `OwningApplication`, `LastModifiedDate`, `CreationDate`) | 6 |

(The Revit relationship-references are functionally the same shape — five
fields, one kind. The IFC `OwnerHistory` timestamps are two fields of the
same kind. The composite-reference fields are two of the same kind.)

**Headline AECO finding:** **heterogeneous typed fields surface** — IFC
timestamps (`IfcTimeStamp`, integer seconds since epoch), IFC composite
references (`IfcPersonAndOrganization`, `IfcApplication`), and Revit
`ElementId`-typed relationships. Whether they are *required* to travel
with the identifier is judgment-dependent: an identifier-only exchange
can omit them; an OwnerHistory-aware exchange that the IFC spec
prescribes for each `IfcRoot` instance cannot.

The controlled-vocabulary classification bucket carries the canonical
"what kind of thing is this?" work cleanly — entity types,
predefined-type enums, classification codes, family/type names. That
fit is uncontested.

### Vertical 2 — Manufacturing / PLM (AAS, Windchill, SAP)

**Scope of "fields that travel with the identifier."** Manufacturing
is the vertical the existing comparison flagged as "the hardest test"
for D's classification fit. Three sources of authority were exercised:

1. **AAS (Asset Administration Shell)** — the IDTA-01001 metamodel
   ([v3.1.1 / v3.2](https://industrialdigitaltwin.io/aas-specifications/IDTA-01001/v3.2/spec-metamodel/overview.html))
   is the explicit Industry 4.0 standard for digital-twin identifier
   bundles. Its identifier-package surface is defined formally — every
   field has a typed metamodel slot.
2. **Windchill** — PTC's PLM. WTPart is the canonical part record;
   surfaced via Windchill REST Services (OData v4, with Edm.* primitives).
   Authoritative spec: PTC's [Windchill REST Services 1.5 User Guide](https://community.ptc.com/sejnu66972/attachments/sejnu66972/Windchill/59859/1/Windchill%20REST%20Services%201.5.pdf).
3. **SAP** — MARA is the General Material Data table that holds the
   MATNR (Material Number) identifier and the closest-bound master-data
   fields. ABAP DDIC types are authoritative: CHAR, DATS, QUAN, etc.

#### AAS — AssetInformation, SpecificAssetId, AdministrativeInformation, Submodel Property/Range

| Field | Native AAS / XSD type | What it carries | Bucket |
|---|---|---|---|
| `AssetInformation.globalAssetId` ([overview](https://industrialdigitaltwin.io/aas-specifications/IDTA-01001/v3.1.2/spec-metamodel/overview.html)) | `Identifier` (string IRI) | The opaque round-trip pointer to the asset | **Identity** |
| `AssetInformation.assetKind` | `AssetKind` enumeration (`Type`, `Instance`, `NotApplicable`) | Whether this AAS describes a type or an instance | **Controlled-vocabulary classification facets** |
| `AssetInformation.assetType` | `Identifier` (string) | Classification or taxonomy reference | **Controlled-vocabulary classification facets** (it's a reference *string*, not a typed Reference) |
| `AssetInformation.specificAssetIds` | `List<SpecificAssetId>` (composite) | Domain-specific identifiers (each is a structured triple) | **Heterogeneous typed fields** (list of structured records) |
| `SpecificAssetId.name` | `LabelType` (string, max 64) | Label naming the identifier kind | **Controlled-vocabulary classification facets** (paired with `value`) |
| `SpecificAssetId.value` | `IdentifierType` (string) | The identifier value itself | **Identity** |
| `SpecificAssetId.externalSubjectId` | `Reference` (composite — see below) | Subject/tenant context | **Heterogeneous typed fields** (composite reference) |
| `SpecificAssetId.semanticId` | `Reference` | Semantic definition pointer | **Heterogeneous typed fields** (composite reference) |
| `Identifiable.administration` (`AdministrativeInformation`) | composite: `version`, `revision`, `creator: Reference`, `templateId: Identifier` | Administrative metadata; `creator` is a typed Reference | **Heterogeneous typed fields** (composite, contains a Reference) |
| `Submodel.kind` (`ModellingKind`) | enum (`Template`, `Instance`) | Whether the submodel is a template or instance | **Controlled-vocabulary classification facets** |
| `Submodel.semanticId` | `Reference` | What concept this submodel realizes (e.g. `urn:idta:dpp:battery:1.0`) | **Heterogeneous typed fields** (composite reference) |

**The submodel element catalog** (the AAS extensible-metadata surface
that travels under each AAS identifier — sourced from the
[IDTA Submodel Element Types overview](https://industrialdigitaltwin.io/aas-specifications/IDTA-01001/v3.1.1/spec-metamodel/submodel-elements.html)):

| Submodel element | Native typing | Bucket |
|---|---|---|
| `Property.value` | XSD-typed: `xs:string`, `xs:int`, `xs:long`, `xs:decimal`, `xs:double`, `xs:float`, `xs:boolean`, `xs:date`, `xs:dateTime`, `xs:time`, `xs:duration`, `xs:anyURI`, `xs:base64Binary` | **Heterogeneous typed field** for any numeric, date, boolean, or binary case (string is just one of the XSD types `valueType` can take) |
| `MultiLanguageProperty.value` | `MultiLanguageTextType` (list of `LangStringTextType` pairs) | **Heterogeneous typed fields** (multilingual record list) |
| `Range.min` / `Range.max` | Pair of XSD-typed values, same type set as `Property.value` | **Heterogeneous typed fields** (a pair, with numeric/date possible) |
| `ReferenceElement.value` | `Reference` (composite — list of `Key`s) | **Heterogeneous typed fields** (composite reference) |
| `RelationshipElement.first` / `.second` | Pair of `Reference`s | **Heterogeneous typed fields** (composite reference pair) |
| `AnnotatedRelationshipElement.annotations` | List of `DataElement` (recursive) | **Heterogeneous typed fields** (recursive composite) |
| `File.value` / `File.contentType` | URI string + MIME content-type token | Mixed: identity-adjacent (URI) + classification (content-type token) |
| `Blob.value` / `Blob.contentType` | `xs:base64Binary` + MIME content-type token | **Heterogeneous typed fields** (binary value) |
| `Entity.entityType` | `EntityType` enum (`CoManagedEntity`, `SelfManagedEntity`) | Controlled-vocabulary classification facets |
| `Entity.globalAssetId` | `Identifier` | Identity |
| `Entity.specificAssetIds` | `List<SpecificAssetId>` | Heterogeneous typed field (same as above) |
| `Capability` | (placeholder, no value) | n/a |
| `Operation.inputVariables` / `outputVariables` / `inoutputVariables` | Lists of `OperationVariable` (each wrapping a `SubmodelElement`) | **Heterogeneous typed fields** (recursive composite) |
| `BasicEventElement.observed` | `Reference` | **Heterogeneous typed fields** (composite reference) |

This is decisive. The AAS metamodel — the standard explicitly named
in the source-identifier proposal's emerging-consensus list and in the
asluk/OpenUSD-proposals#2 proof-of-concept — defines its
identifier-bundled metadata surface to *include* numeric, date,
boolean, binary, and composite-reference shapes, on purpose, with
typed metamodel slots. These do not flatten to token arrays without
losing the structural type. The proposal doc cites AAS feedback for
the "explicit identifier typing" emerging consensus — and AAS's own
typing system is polymorphic XSD, not strings.

#### Windchill — WTPart (PLM)

| Field | Native OData / Edm type | What it carries | Bucket |
|---|---|---|---|
| `ID` (`VR:wt.part.WTPart:23639563`) | string OID | Object identity in Windchill | **Identity** |
| `Number` (`CH-7500-A`) | `Edm.String` (length 40) | Human-readable part number — also unique within the org | **Identity-adjacent** (round-trips as a key into PLM, but a different ID space than ID) |
| `Name` | `Edm.String` (length 60) | Part name | **Identity-adjacent** (display) |
| `Revision` (`Rev.C`) | `Edm.String` | Revision designator | **Identity-adjacent** (the revision is part of the round-trip identity tuple in PLM lookups) |
| `Version` | `Edm.String` (e.g. `A.2`) | Version below revision | **Identity-adjacent** |
| `State` (`Released`) | structured — `Value` token + `Display` string (per [PTC docs](https://www.ptc.com/en/support/article/CS304928)) | Lifecycle state | **Controlled-vocabulary classification facets** (the `Value` is a controlled token) |
| `Type` (`Part`, `Subassembly`) | `Edm.String` (controlled vocabulary) | Part type | **Controlled-vocabulary classification facets** |
| `OrganizationId` / `Organization.Name` | `Edm.String` | Organization owning the part | **Controlled-vocabulary classification facets** |
| `CreatedOn` | `Edm.DateTimeOffset` | When the part record was created | **Heterogeneous typed fields** (timestamp) |
| `LastModified` | `Edm.DateTimeOffset` | Last modification time | **Heterogeneous typed fields** (timestamp) |

Windchill custom-attribute (IBA — Instance-Based Attribute) values are
typed: `String`, `Integer`, `Real` (with units), `Boolean`,
`Timestamp`, `Reference`. Custom attributes are accessed via the same
OData surface and routinely travel with the WTPart identifier.

#### SAP — MARA (Material Master, S/4HANA)

Sources: [SAP Datasheet — MARA](https://www.sapdatasheet.org/abap/tabl/mara.html),
[se80.co.uk — MARA-MATNR](https://www.se80.co.uk/sap-table-fields/?tabname=mara&fieldname=matnr),
[sapdatasheet — NTGEW data element](https://www.sapdatasheet.org/abap/dtel/ntgew.html).

| Field | ABAP DDIC type | What it carries | Bucket |
|---|---|---|---|
| `MATNR` | `CHAR(18)` (data element MATNR) | Material number — the SAP identifier | **Identity** |
| `MTART` | `CHAR(4)` (Material Type, controlled vocab) | Material type code (`FERT`, `HALB`, `ROH`, …) | **Controlled-vocabulary classification facets** |
| `MATKL` | `CHAR(9)` (Material Group, controlled vocab) | Material group code | **Controlled-vocabulary classification facets** |
| `MEINS` | `UNIT(3)` (base unit of measure) | Unit-of-measure code (controlled vocab) | **Controlled-vocabulary classification facets** |
| `ERSDA` | `DATS(8)` | Date the material record was created | **Heterogeneous typed fields** (date) |
| `LAEDA` | `DATS(8)` | Date of last change | **Heterogeneous typed fields** (date) |
| `ERNAM` | `CHAR(12)` | Username of creator | **Identity-adjacent** |
| `NTGEW` | `QUAN(13,3)` (numeric, 3 decimals) | Net weight | **Heterogeneous typed fields** (decimal with unit) |
| `BRGEW` | `QUAN(13,3)` | Gross weight | **Heterogeneous typed fields** (decimal with unit) |
| `GEWEI` | `UNIT(3)` | Weight-unit code (controlled vocab — `KG`, `LB`, …) | **Controlled-vocabulary classification facets** |
| `VOLUM` | `QUAN(13,3)` | Volume | **Heterogeneous typed fields** (decimal with unit) |
| `MSTAE` | `CHAR(2)` (cross-plant material status, controlled) | Cross-plant material status code | **Controlled-vocabulary classification facets** |
| `MSTDE` | `DATS(8)` | Date from which the material status applies | **Heterogeneous typed fields** (date) |

`NTGEW`/`BRGEW`/`VOLUM` carry their unit via a paired field
(`GEWEI`, `VOLEH`); the full quantity is a (number, unit) pair —
structurally a typed measure, not a string.

#### Manufacturing/PLM bucket counts (33 fields surveyed across AAS / Windchill / SAP)

| Bucket | Count |
|---|---|
| Identity | 4 (AAS `globalAssetId`, AAS `SpecificAssetId.value`, Windchill `ID`, SAP `MATNR`) |
| Identity-adjacent | 5 (Windchill `Number`, `Name`, `Revision`, `Version`; SAP `ERNAM`) |
| Controlled-vocabulary classification facets | 9 (AAS `assetKind`, `assetType`, `SpecificAssetId.name`, `Submodel.kind`; Windchill `State`, `Type`, `OrganizationId`; SAP `MTART`, `MATKL`, `MEINS`, `GEWEI`, `MSTAE` — counted as 9 distinct kinds, with the unit codes counted once) |
| **Heterogeneous typed fields** | **15+** — see breakdown below |

**The heterogeneously typed fields explicitly:**

| Field | Native shape |
|---|---|
| AAS `Property.value` (when `valueType ≠ xs:string`) | XSD numeric / date / boolean / binary |
| AAS `Range.min/.max` (any non-string XSD type) | typed pair |
| AAS `MultiLanguageProperty.value` | list of `LangString` records |
| AAS `ReferenceElement.value` | composite Reference |
| AAS `RelationshipElement.first/.second` | composite Reference pair |
| AAS `AnnotatedRelationshipElement.annotations` | recursive composite |
| AAS `Blob.value` | base64Binary |
| AAS `Operation.input/output/inoutputVariables` | recursive composite |
| AAS `Entity.specificAssetIds` | list of structured records |
| AAS `BasicEventElement.observed` | composite Reference |
| AAS `SpecificAssetId.externalSubjectId` | composite Reference |
| AAS `SpecificAssetId.semanticId` | composite Reference |
| AAS `Identifiable.administration.creator` | composite Reference inside composite |
| Windchill `CreatedOn`, `LastModified` | `Edm.DateTimeOffset` |
| SAP `ERSDA`, `LAEDA`, `MSTDE` | `DATS` (date) |
| SAP `NTGEW`, `BRGEW`, `VOLUM` | `QUAN(n,m)` (decimal with unit) |

**Headline manufacturing finding:** an earlier draft of the comparison
made the claim that "7 of 8 simulated PLM/ERP fields fit cleanly" — a
claim conducted against a synthesized 8-field set used by an earlier
version of `industry_scenarios.md` (the doc has since been trimmed to
an example index). The actual manufacturing identifier surface defined
by IDTA, PTC, and SAP is
explicitly polymorphically-typed and includes numeric, date, and
composite-reference fields. **The load-bearing assertion that "no
field surfaced needing typed non-token-array structure" does not
hold against the Manufacturing/PLM surface as defined by its
authoritative specs.**

Whether this should change the doc's leaning depends on judgment that
isn't this experiment's to make: a follow-up proposal could choose to
*scope down* identifier metadata to the parts that fit token arrays,
treating numeric/date/composite-reference content as out-of-scope ("not
identifier metadata, that's submodel data"). But that scope decision is
the open question; the experimental finding is that the spec surface is
typed.

### Vertical 3 — Robotics & Simulation (ROS, URDF, SDF)

**Scope of "fields that travel with the identifier" — and a scope
ambiguity to declare up front.** Robotics has a clearer
identifier-vs-content split than the previous two verticals, and the
distinction matters for how the experiment reads:

- **Strict interpretation.** The "source identifier" is the package
  URI (e.g. `package://ur_description/urdf/ur10e.urdf`), the model
  name, the ROS distribution, and the source format (`URDF` vs `SDF`).
  These are strings. The bundled metadata is small.
- **Expanded interpretation.** Once you ingest the asset URDF/SDF
  defines, the description format itself is heavily numeric (mass,
  inertia tensors, joint limits, dynamics). Authors who want to
  preserve provenance back to URDF/SDF often want the originating
  field values to round-trip too — at which point those numerics
  become metadata that travels with the identifier.

The strict interpretation is what the synthesized robotics scenarios
in `examples/robotics_{a,b,d}.usda` exercise; the expanded
interpretation is closer to what an ingestion-and-re-export workflow
actually needs to round-trip.

This census reports both, with each field labelled `[strict]` or
`[expanded]`.

#### ROS package / model identifier surface

Sources: [REP 127 (Package manifest format two)](https://www.ros.org/reps/rep-0127.html),
[REP 144 (ROS Package Naming)](https://www.ros.org/reps/rep-0144.html),
[std_msgs/Header documentation](https://docs.ros.org/en/melodic/api/std_msgs/html/msg/Header.html).

| Field | Native type | What it carries | Bucket | Strict / expanded |
|---|---|---|---|---|
| Package URI (`package://<package>/<path>`) | string | The opaque pointer back into the ROS package system | **Identity** | strict |
| Package name (e.g. `ur_description`) | string (regex per REP 144) | ROS package name | **Identity-adjacent** | strict |
| Package version (e.g. `2.4.1`) | string (semver-ish) | Version of the package the description came from | **Identity-adjacent** | strict |
| Source format (`URDF`, `SDF`, `MJCF`) | enum (controlled vocab) | Which description format originated this model | **Controlled-vocabulary classification facets** | strict |
| ROS distribution (e.g. `jazzy`, `humble`, `iron`) | enum (controlled vocab) | ROS distro the package targets | **Controlled-vocabulary classification facets** | strict |
| Maintainer name / email | strings | Provenance, not identity | **Identity-adjacent** | strict |
| `std_msgs/Header.frame_id` | string | TF frame name the data is in | **Identity** | strict (it's a TF identifier) |
| `std_msgs/Header.stamp` | `time` (uint32 sec + uint32 nsec) | Timestamp paired with the frame_id | **Heterogeneous typed fields** (numeric pair, semantically a timestamp) | strict |
| `std_msgs/Header.seq` | uint32 | Monotonic counter | **Heterogeneous typed fields** (numeric) | strict |
| Topic name (`/scan`, `/cmd_vel`) | string (controlled by package convention) | Pub/sub channel name | **Identity** (round-trips back into ROS as a topic key) | strict |
| Service name | string | Service endpoint name | **Identity** | strict |

`std_msgs/Header` is the canonical "metadata that travels alongside ROS
data" — it's appended to most ROS messages — and its `stamp` is
explicitly a structured time pair (`uint32 sec + uint32 nsec`), not a
string token. `seq` is a uint32. These are heterogeneously typed
**already in the strict interpretation**.

#### URDF link / joint surface (expanded interpretation — round-trip-back-to-URDF)

Sources: [URDF link XML reference (ROS wiki)](https://wiki.ros.org/urdf/XML/link),
[URDF joint XML reference](https://wiki.ros.org/urdf/XML/joint),
[urdfdom C++ headers](https://github.com/ros/urdfdom_headers/tree/master/include/urdf_model)
(`JointDynamics::damping/friction` parsed via `strToDouble`, per [urdfdom joint.cpp](https://github.com/ros/urdfdom/blob/master/urdf_parser/src/joint.cpp)).

| Field | Native type | What it carries | Bucket |
|---|---|---|---|
| `<link name="">` | string | Link name (the identifier within the URDF) | **Identity** |
| `<inertial><mass value="">` | double (kg) | Link mass | **Heterogeneous typed fields** (decimal with unit) |
| `<inertial><inertia ixx ixy ixz iyy iyz izz>` | 6 × double (kg·m²) | Inertia tensor (symmetric 3×3, 6 components) | **Heterogeneous typed fields** (numeric tensor) |
| `<inertial><origin xyz="" rpy="">` | 3 doubles (m) + 3 doubles (rad) | Pose of the inertial frame | **Heterogeneous typed fields** (numeric pose) |
| `<visual>/<collision><geometry><box size="x y z">` | 3 × double (m) | Box dimensions | **Heterogeneous typed fields** (numeric tuple) |
| `<geometry><cylinder radius="" length="">` | 2 × double (m) | Cylinder dimensions | **Heterogeneous typed fields** (numeric pair) |
| `<geometry><sphere radius="">` | double (m) | Sphere radius | **Heterogeneous typed fields** (numeric) |
| `<geometry><mesh filename="" scale="">` | string + 3 × double | Mesh file URI + scale | mixed: URI is identity, scale is numeric |
| `<joint name="">` | string | Joint name | **Identity** |
| `<joint type="">` | enum (`revolute`, `continuous`, `prismatic`, `fixed`, `floating`, `planar`) | Joint kinematic type | **Controlled-vocabulary classification facets** |
| `<joint><parent link=""> / <child link="">` | strings (link-name references) | Joint topology | **Heterogeneous typed fields** (typed reference into the link namespace) |
| `<joint><origin xyz rpy>` | 3 + 3 doubles | Joint frame pose | **Heterogeneous typed fields** (numeric pose) |
| `<joint><axis xyz>` | 3 × double (unit vector) | Rotation/translation axis | **Heterogeneous typed fields** (numeric vector) |
| `<joint><limit lower upper effort velocity>` | 4 × double (rad / m / N·m / rad·s⁻¹ / m·s⁻¹) | Joint limits | **Heterogeneous typed fields** (numeric, with units) |
| `<joint><dynamics damping friction>` | 2 × double (per [urdfdom joint.cpp `parseJointDynamics`](https://github.com/ros/urdfdom/blob/master/urdf_parser/src/joint.cpp)) | Joint dynamics | **Heterogeneous typed fields** (numeric, with units — N·s/m or N·m·s/rad) |
| `<joint><mimic joint multiplier offset>` | string + 2 × double | Joint mimic relationship | **Heterogeneous typed fields** (composite: reference + numeric) |
| `<joint><safety_controller>` `soft_lower_limit`, `soft_upper_limit`, `k_position`, `k_velocity` | 4 × double | Safety controller settings | **Heterogeneous typed fields** (numeric) |

#### SDF (Gazebo Simulation Description Format)

Source: [gazebosim SDF spec](http://sdformat.org/spec) — SDF is a
superset of URDF's value set, adding pose mode (`degrees="true"`), more
joint types (gear, screw), and physics-engine knobs (CFM, ERP, slip).
The numeric / heterogeneous typed fields pattern is the same.
Notably, SDF adds explicit unit handling (`<pose degrees="true">`) and
quaternion-as-4-double options — both still numeric, not tokens.

#### Robotics bucket counts (26 fields surveyed; strict = 11, expanded URDF/SDF = 15)

| Bucket | Strict (11) | Expanded URDF (15) |
|---|---|---|
| Identity | 4 (package URI, frame_id, topic, service) | 2 (link name, joint name) |
| Identity-adjacent | 3 (package name, version, maintainer) | 0 |
| Controlled-vocabulary classification facets | 2 (source format, ROS distro) | 1 (joint type) |
| **Heterogeneous typed fields** | **2** (`Header.stamp`, `Header.seq`) | **12** (everything physical: mass, inertia, origins, axes, geometry params, limits, dynamics, mimic, safety, parent/child references) |

**Headline robotics finding:**

- **Strict interpretation:** the identifier-package metadata is mostly
  strings, with the notable exception of `std_msgs/Header.stamp` (timestamp
  pair) and `seq` (uint32). The "identifier strings + classification
  facets" framing *holds for the package-URI surface itself* but **fails
  for the canonical bundled `Header` metadata.**
- **Expanded interpretation:** the URDF/SDF source format is *predominantly*
  numeric. If preserving round-trip provenance into URDF/SDF is part of what
  "source identifier" means in robotics — and a URDF → USD → modify → URDF
  workflow assumes it is — then the strings-and-classification framing
  does not survive contact with this vertical's authoritative format
  definitions.

### Vertical 4 — Media & Entertainment (OpenAssetIO, MovieLabs OMC, Autodesk Flow)

**Scope of "fields that travel with the identifier."** M&E asset
identifiers are typically:

- An asset DB ID (string, often UUID-shaped or sequential).
- A version number / increment.
- A path or URL to the asset on disk / cloud storage.
- Status / approval state.
- A few link references (project, sequence, shot, parent asset).

The existing comparison flagged M&E as "the lightest case" for D
because the metadata bundle is sparse. The census below tests whether
"sparse" is the same as "exclusively string-and-classification-shaped."
Three sources:

1. **OpenAssetIO** — the open-source foundation API for asset
   management interop, built originally to abstract over ftrack /
   ShotGrid / Katana / Maya asset systems.
2. **MovieLabs Ontology for Media Creation (OMC)** — an open data model
   defining standard concepts (Asset, Task, Participant) and the
   identifier conventions for sharing them.
3. **Autodesk Flow Production Tracking (formerly ShotGrid)** — the
   dominant production-tracking system whose REST API is the de facto
   M&E asset-DB surface.

Sources:
[OpenAssetIO](https://openassetio.org/),
[MovieLabs OMC](https://movielabs.com/production-technology/ontology-for-media-creation/),
[ShotGrid REST API entity reference](https://developer.shotgridsoftware.com/rest-api/).

#### OpenAssetIO trait surface

OpenAssetIO doesn't define typed identifier fields itself — it
abstracts over a manager's identifier ("entityReference") which is a
string. Around the reference, traits are typed dictionaries
(`openassetio.trait.TraitsData`) carrying named typed properties:

| Field | Native type | What it carries | Bucket |
|---|---|---|---|
| `entityReference` | string (URI-shaped, manager-defined) | The opaque identifier | **Identity** |
| Manager identifier (`org.foundry.examplemanager`) | reverse-DNS string | Which asset manager the reference belongs to | **Controlled-vocabulary classification facets** |
| Trait IDs (e.g. `openassetio-mediacreation:content.LocatableContent`) | reverse-DNS string | Which trait is being communicated | **Controlled-vocabulary classification facets** |
| Trait property values | typed: `bool`, `int`, `float`, `str`, `dict<str, value>` (per [TraitsData spec](https://docs.openassetio.org/OpenAssetIO/classopenassetio_1_1trait_1_1_traits_data.html)) | Trait property values are polymorphic | **Heterogeneous typed fields** for any non-string trait property |

OpenAssetIO traits are explicitly typed (the spec lists `bool`, `int`,
`float`, `str`, `dict` as the value type taxonomy). Examples in the
[mediacreation traits library](https://docs.openassetio.org/OpenAssetIO-MediaCreation/)
include `content.image.dimensions` (int width/height), `lifecycle.Version`
(int + bool stable flag), `timeline.FrameRanged` (int range).

#### MovieLabs OMC

OMC defines typed identifier-surface concepts: `Asset` has
`identifier`, `name`, `description`, `assetType` (enum), `version`,
`status` (enum), `participants` (relationships), `creationContext`,
`lifecycleEvents` (timestamped events).

| Field | Native type | What it carries | Bucket |
|---|---|---|---|
| `Asset.identifier` | string (URI/UUID, manager-defined) | The asset identifier | **Identity** |
| `Asset.assetType` | enum (`SceneAsset`, `CharacterAsset`, `PropAsset`, `EnvironmentAsset`, …) | Asset taxonomy | **Controlled-vocabulary classification facets** |
| `Asset.status` | enum | Lifecycle state | **Controlled-vocabulary classification facets** |
| `Asset.version` | int (or string per implementation) | Version increment | **Heterogeneous typed fields** when int (per OMC schema) |
| `Asset.participants` | list of Participant references | Who created/edited the asset | **Heterogeneous typed fields** (composite reference list) |
| `Asset.creationContext` | structured (creator, application, time) | When/by whom/with what | **Heterogeneous typed fields** (composite) |
| `Asset.lifecycleEvents` | list of (event-type, timestamp) | Asset history | **Heterogeneous typed fields** (composite) |

#### ShotGrid REST API — Asset entity

The ShotGrid REST API exposes an `Asset` entity with attributes whose
types follow the manager's field-type system:

| Field | Native type | What it carries | Bucket |
|---|---|---|---|
| `id` | integer | ShotGrid internal asset ID | **Identity** |
| `code` | string | Human-readable asset name | **Identity-adjacent** |
| `sg_status_list` | controlled vocabulary string (e.g. `act`, `omt`, `cmpt`) | Status code | **Controlled-vocabulary classification facets** |
| `sg_asset_type` | controlled vocabulary string | Asset type | **Controlled-vocabulary classification facets** |
| `created_at`, `updated_at` | datetime | Timestamps | **Heterogeneous typed fields** (datetime) |
| `created_by`, `updated_by` | entity reference (typed: `HumanUser` link) | Authorship | **Heterogeneous typed fields** (composite reference) |
| `project` | entity reference (typed: `Project` link) | Project membership | **Heterogeneous typed fields** (composite reference) |
| `parents`, `assets` | list of entity references | Assembly relationships | **Heterogeneous typed fields** (composite reference list) |
| `image` (thumbnail) | URL string | Thumbnail | **Identity-adjacent** (URL) |

#### M&E bucket counts (16 fields surveyed)

| Bucket | Count |
|---|---|
| Identity | 3 (OpenAssetIO `entityReference`, OMC `Asset.identifier`, ShotGrid `id`) |
| Identity-adjacent | 2 (ShotGrid `code`, `image`) |
| Controlled-vocabulary classification facets | 6 (manager id, trait id, OMC `assetType` & `status`, ShotGrid `sg_status_list` & `sg_asset_type`) |
| **Heterogeneous typed fields** | **6** (OpenAssetIO trait values when non-string; OMC `version` int, `participants`, `creationContext`, `lifecycleEvents`; ShotGrid `created_at`/`updated_at`, `created_by`/`updated_by`/`project`/`parents`/`assets`) |

**Headline M&E finding:** even in the "lightest" vertical the
identifier-bundle includes datetimes (created_at/updated_at) and
typed entity-reference relationships (project, parent, created_by).
These are heterogeneous typed shapes, not strings — structured
datetimes and typed cross-entity references. The
strings-and-classification framing is closest to holding here, but
does not hold cleanly.

## Cross-vertical synthesis

Field census totals across the four verticals (counting each *kind*
of field once per system; not weighting by frequency in real stages):

| Vertical | Identity | Identity-adjacent | Controlled-vocabulary classification facets | **Heterogeneous typed fields** |
|---|---|---|---|---|
| AECO (12 main + 6 OwnerHistory) | 3 | 4 | 9 | 6 (Revit relationships; IFC timestamps + composite refs) |
| Manufacturing/PLM (33) | 4 | 5 | 9 | 15+ (AAS Property/Range/Reference/Relationship; Windchill DateTimeOffset; SAP DATS/QUAN) |
| Robotics — strict (11) | 4 | 3 | 2 | 2 (`Header.stamp`, `seq`) |
| Robotics — expanded URDF (15) | 2 | 0 | 1 | 12 (mass, inertia, origins, axes, limits, dynamics, mimic, safety, parent/child refs) |
| M&E (16) | 3 | 2 | 6 | 6 (datetimes; OMC version/participants; ShotGrid entity refs) |

**Recurring kinds of heterogeneous typed fields across verticals:**

1. **Timestamps** — IFC `IfcTimeStamp`, Windchill `Edm.DateTimeOffset`,
   SAP `DATS`, ROS `Header.stamp`, OMC `lifecycleEvents.timestamp`,
   ShotGrid `created_at`/`updated_at`. Present in **every vertical
   surveyed.**
2. **Numeric measures with units** — IFC `IfcMeasureValue` family
   (`IfcLengthMeasure`, `IfcMassMeasure`, etc.), SAP `QUAN(n,m)`
   (`NTGEW`, `BRGEW`, `VOLUM`), URDF/SDF mass/inertia/limits/dynamics.
   Present in AECO, PLM, Robotics.
3. **Composite typed references** — IFC `IfcPersonAndOrganization` /
   `IfcApplication`, AAS `Reference` / `RelationshipElement`, Revit
   `ElementId`-typed relationships, ShotGrid entity-link fields.
   Present in **every vertical surveyed.**
4. **Polymorphic typed values** — AAS `Property.value` (XSD type set),
   AAS `Range.min`/`.max`, OpenAssetIO trait property values. Present
   especially in PLM (where it is the *standard surface* for extension
   metadata).
5. **Recursive composites** — AAS `AnnotatedRelationshipElement.annotations`,
   `Operation.input/output/inoutputVariables`, OMC
   `creationContext`/`lifecycleEvents`, URDF mimic relations.
   Present in PLM, Robotics, M&E.

## What the census shows

The census shows, against authoritative specs across all four
verticals, that **identifier packages are heterogeneously typed.**

- **Heterogeneous typed fields surface in every vertical surveyed.**
  The recurring kinds (timestamps, numeric measures with units,
  composite typed references, polymorphic typed values, recursive
  composites) are not isolated edge cases; they are part of the
  mandatory or commonly-authored identifier surface in their source
  systems.
- **The proposal's heterogeneity tension is real, not empty.**
  Proposal 105 framed the heterogeneity question as a tension AOUSD
  would have to weigh: *"the more heterogeneous the contents, the
  more this tension favors dictionaries or a family of domain-specific
  schemas"* (B's cons, ¶1). The empirical surface confirms the
  premise of that framing. Identifier packages carry typed
  heterogeneity that the proposal anticipated.
- **AAS — the standard the proposal already cites in its
  emerging-consensus list and proof-of-concept (asluk/OpenUSD-proposals#2)
  — is the most strongly typed identifier-package surface of any
  spec surveyed.** AAS `Property.value` is polymorphic across the XSD
  type set by design, including numerics, dates, booleans, and
  base64-binary. AAS `Range`, `Reference`, `RelationshipElement`,
  `Operation`, and `BasicEventElement` are all structured composites.
  The proposal's *"explicit identifier typing"* emerging-consensus
  point traces back to AAS feedback; the typing AAS itself uses is
  XSD-polymorphic, not flat tokens.

## What this means for the comparison's previous claim

The previous claim — that *"no domain-specific field surfaced that
required typed non-token-array structure"* across the four verticals
— **is not supported by the spec surfaces.** It was made against a
synthesized field set in
[industry_scenarios.md](industry_scenarios.md) (IFC type/objectType,
Revit category/familyType/mark/level, UniClass code, Windchill
state/lifecyclePhase, ROS topic name). Those fields *are* token-array
shaped, and the claim holds for that subset. Heterogeneous typed
fields (timestamps, numeric measures, composite refs, polymorphic AAS
values) were excluded from the synthesized set without explicit
justification and are present, in volume, in the spec surfaces.

The exclusion was a scope call — but the scope call wasn't argued.
The empirical evidence does not support drawing the
identifier-package boundary in a way that excludes the heterogeneous
typed surface; that surface is what the source systems put there.

## What this means for mechanism choice

The four candidates carry typed heterogeneity differently:

| Mechanism | Carries heterogeneous typed fields? |
|---|---|
| A — `assetInfo` dictionaries | Yes — freeform dicts admit any typed shape (subject to USD's value-type set), at the cost of no schema-side typing or discoverability. |
| B — Multi-apply schema, four common typed properties | No — the four-property fixed surface cannot carry domain-specific typed fields without companion schemas per domain. |
| C — Refinement of B (B + `assetInfo` overflow) | Yes — typed schema for the common fields, freeform-dict overflow for everything heterogeneous, including typed shapes. |
| D — Refinement of B (`UsdSemanticsLabelsAPI` + `assetInfo` identity strings) | No — labels carry `token[]` and identifier strings; numeric, date, composite-reference, and polymorphic typed shapes have no slot. |

Two implications, neither of which this experiment by itself decides
but both of which it constrains:

1. **A and C accommodate the empirical heterogeneity.** D and B do
   not. A solution proposal that wants to carry the typed
   heterogeneity surface that real source systems bundle has to use a
   mechanism with a freeform-dict tier or a per-domain typed-schema
   tier (or both).
2. **D's premise depends on a scope-narrowing the data does not
   support.** D works for the controlled-vocabulary classification
   axis cleanly, and the previous comparison's leaning toward D rested
   on the assumption that the classification axis is *all that
   matters* for source-identifier metadata. The empirical surface does
   not show that axis to be all that matters — it shows it to be one
   of four buckets, and not the largest in two of the four verticals.

A follow-up proposal could still argue for D *with* an explicit
scope-narrowing — i.e. *"source identifiers are identity strings +
classification facets, and everything else (timestamps, numeric
measures, composite refs) is the asset's content, carried by
mechanisms outside this proposal."* That argument is not made by
the current materials, and would have to be made on grounds the
empirical census does not by itself settle. As the materials stand,
the leaning toward D is not earned by the empirical work.

### What this experiment does *not* settle

- The mechanism choice between A and C (the two candidates that
  accommodate the empirical surface). The structure-vs-freeform
  tradeoff between them is not narrowed by this census; that is a
  downstream judgment.
- Whether B with companion schemas per domain is preferable to
  either A or C. That depends on adoption velocity and ecosystem
  distribution considerations the rebuild plan flags as load-bearing
  open questions.
- Where the identifier-package boundary should sit. The experiment
  reports the empirical surface as the source systems define it; a
  follow-up proposal can choose to narrow the scope, but has to
  argue the narrowing rather than assume it.

These are inputs for the follow-up proposal, not for this PR.

## Property-set excursion (AECO and PLM)

(Held for after the per-vertical census — IFC `Pset_*` and AAS submodel
properties are arguably *not* part of the identifier package, but
since they are the canonical extension surface in their domains, a
short note on what their value-typing looks like is included here so
the experiment doesn't look the other way.)


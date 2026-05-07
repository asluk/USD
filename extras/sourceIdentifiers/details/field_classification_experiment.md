# Field Classification Experiment

← [Back to COMPARISON.md](../COMPARISON.md)

## Why this experiment

Multiple places in the comparison materials assert:

> *"No domain-specific field surfaced that required typed non-token-array structure."*
> *"Token arrays + identifier strings carried every metadata case tested."*
> ([details/formality_and_distribution.md](formality_and_distribution.md))

These assertions are load-bearing for the leaning toward Approach D — they
underpin the claim that reusing `UsdSemanticsLabelsAPI` (which carries
`token[]`-typed values only) leaves no important shape on the table that a
new applied schema would catch. Until now they have been stated without
the underlying field census.

This document is that census, conducted under pre-registered classification
criteria (the buckets are committed before any field is enumerated, and
the criteria are applied uniformly across verticals). It does not declare a
winner among the four mechanisms. It tests one specific empirical
assertion.

## Pre-registered classification

A field belongs to exactly one of four buckets:

| Bucket | Test |
|---|---|
| **Identity** | The field must round-trip *exactly* back into the source system. It has no semantic value outside that system; it is a pointer. |
| **Classification — token-array fit** | The value is drawn from a published controlled vocabulary; the value space is enumerable strings/identifiers; the native shape is a string or list of strings. Encodable as `token[]` without loss of structural type. |
| **Classification — non-token-array typed structure** | The native shape is structured: numeric (with or without units), date/time, range, structured record, reference relationship, boolean. Cannot be flattened to a `token` without losing the structural type. |
| **Identity-adjacent** | A round-trip-style string that helps locate or display the identifier (display number, human-readable label, browse name) but is not itself the round-trip pointer. Authors may carry it alongside identity. |

### Rules of the experiment

1. **Cite the source.** Each field is sourced from its authoritative spec
   (IFC schema HTML, AAS metamodel, ROS/SDF/URDF specs, Windchill REST API
   docs, SAP Material Master / S/4HANA API, OpenAssetIO trait definitions,
   MovieLabs OMC). The `industry_scenarios.md` description is *not* a
   source — that document was constructed in service of D's classification
   fit and would import its bias into this experiment.
2. **Native data type comes from the spec.** Token-array fit means *fits
   without losing structural type*. A `IfcReal`, `xs:dateTime`,
   `xs:decimal`, `Reference`, `IfcPositiveLengthMeasure`, or boolean is
   not a token.
3. **Don't force a bucket.** Borderline / disputed fields are reported
   borderline. Bucketing under pressure to confirm the assertion would
   defeat the experiment.
4. **Field set is representative, not exhaustive.** Each vertical's
   field set is drawn from the system's mandatory + commonly-authored
   identifier-adjacent surface, not cherry-picked. If anything was
   excluded for a reason other than "not on identifier surface," the
   exclusion is noted in line.
5. **One bucket per field.** A field that is genuinely both (e.g., a
   string with controlled-vocabulary semantics that also round-trips)
   is bucketed by its primary semantics in the source spec, with the
   secondary use noted.

### What the experiment can and cannot conclude

It **can** conclude: in the field set surveyed, the following fields fall
into the non-token-array typed bucket — by name, with native types and
citations.

It **cannot** conclude: that this field set is exhaustive, that no future
domain will surface non-token-array typed fields, or that any one
mechanism is the right answer. AOUSD review sees the result and decides.

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
| Entity type (`IfcColumn`, `IfcWall`, …) | enumeration of IFC entity names | The IFC class name itself; controlled vocabulary published by buildingSMART | **Classification — token-array fit** |
| `PredefinedType` ([IfcColumn](https://standards.buildingsmart.org/IFC/RELEASE/IFC4_3/HTML/lexical/IfcColumn.htm)) | `IfcColumnTypeEnum`, `IfcWallTypeEnum`, … (controlled enum per entity) | Subtype within the entity (`COLUMN`, `PILASTER`, `USERDEFINED`, …) | **Classification — token-array fit** |
| `ObjectType` ([IfcObject](https://standards.buildingsmart.org/IFC/RELEASE/IFC4_3/HTML/lexical/IfcObject.htm)) | `IfcLabel` (string) | User-defined subtype string when `PredefinedType` is `USERDEFINED` | **Classification — token-array fit** (free-text label, but its role is naming a vocabulary term) |
| IFC schema version (e.g. `IFC4X3_ADD2`) | string identifier per buildingSMART | Which IFC schema produced this file | **Classification — token-array fit** |

**`IfcOwnerHistory`** (the audit-trail metadata bundle attached to every
`IfcRoot` instance via the `OwnerHistory` reference) is reported separately
because it is a structured composite, not a single field:

| Sub-field | Native IFC type | Bucket |
|---|---|---|
| `OwningUser` | `IfcPersonAndOrganization` (composite) | Non-token-array typed structure (composite reference) |
| `OwningApplication` | `IfcApplication` (composite) | Non-token-array typed structure (composite reference) |
| `State` | `IfcStateEnum` (`READWRITE`, `READONLY`, `LOCKED`, …) | Classification — token-array fit |
| `ChangeAction` | `IfcChangeActionEnum` (`NOCHANGE`, `MODIFIED`, `ADDED`, `DELETED`, `MODIFIEDADDED`, `MODIFIEDDELETED`, `NOTDEFINED`) | Classification — token-array fit |
| `LastModifiedDate` | `IfcTimeStamp` (integer seconds since epoch, per ISO 10303) | **Non-token-array typed structure** (numeric, semantically a timestamp) |
| `CreationDate` | `IfcTimeStamp` (integer seconds since epoch) | **Non-token-array typed structure** (numeric, semantically a timestamp) |

`IfcOwnerHistory` is not "the identifier," but it is the metadata bundle
buildingSMART specifies as traveling with every identified IFC entity in
the model. Source: [IfcOwnerHistory](https://standards.buildingsmart.org/IFC/RELEASE/IFC4_3/HTML/lexical/IfcOwnerHistory.htm).

#### Revit (Autodesk Revit API 2024 reference)

| Field | Native .NET type | What it carries | Bucket |
|---|---|---|---|
| `UniqueId` ([Element](https://help.autodesk.com/cloudhelp/2024/ENU/Revit-API/files/Revit_API_Developers_Guide/Introduction/Elements_Essentials/Revit_API_Revit_API_Developers_Guide_Introduction_Elements_Essentials_General_Properties_html.html)) | `String` (GUID-shaped, project-portable) | The opaque pointer back into Revit (cross-project) | **Identity** |
| `Id` (`ElementId`) | `ElementId` (wrapping `int`/`long`) | Integer ID unique within a single Revit project | **Identity** (numeric — see note below) |
| `Category` | `Category` reference (resolves to a category name string) | Built-in category, controlled vocabulary | **Classification — token-array fit** |
| `LevelId` | `ElementId` reference to a Level element | Reference to another Revit element | **Non-token-array typed structure** (relationship) |
| `Mark` (`ALL_MODEL_MARK` parameter) | `String` (parameter `StorageType.String`) | User-authored per-instance mark (per-project unique by convention) | **Identity-adjacent** |
| `Type Mark` (`ALL_MODEL_TYPE_MARK`) | `String` (parameter `StorageType.String`) | Type-level mark | **Classification — token-array fit** (controlled by template) |
| Family / Type names (e.g. `W14x90`) | `String` | Family + type strings | **Classification — token-array fit** |
| `OwnerViewId`, `GroupId`, `AssemblyInstanceId`, `DesignOption` | `ElementId` (each) | References to other Revit elements | **Non-token-array typed structure** (relationship — `ElementId` is a typed reference, not a string) |

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
| `Ss_25_10_30` style code ([UniClass 2015 Systems table](https://uniclass.thenbs.com/taxon/Ss_25_10_30/)) | String (4-segment, hierarchical) | A controlled-vocabulary code from a published table | **Classification — token-array fit** |
| Title (e.g. `Framed partition systems`) | String | The published display title for the code | **Classification — token-array fit** |
| Table identifier (e.g. `Ss`) | String / token (small enum: `Ss`, `Pr`, `EF`, `Ac`, …) | Which UniClass table the code belongs to | **Classification — token-array fit** |
| OmniClass `23-13 11 13` | String (table-section format) | Same shape as UniClass — table + numeric segments | **Classification — token-array fit** |

Note: the hierarchical structure of UniClass/OmniClass codes (table prefix
+ digit groups) is *implicit* in the string. A consumer that needs the
hierarchy explicitly can split on `_` / spaces; the canonical form is the
string itself. So the field is a string from a published vocabulary —
token-array fit is correct.

#### AECO bucket counts (12 fields surveyed; OwnerHistory 6 sub-fields surveyed separately)

| Bucket | Count (12 main) | Count (6 OwnerHistory) | Total |
|---|---|---|---|
| Identity | 3 (IFC `GlobalId`, Revit `UniqueId`, Revit `Id`) | 0 | 3 |
| Identity-adjacent | 3 (IFC `Name`, `Description`, `Tag`; Revit `Mark`) | 0 | 4 (counts Revit `Mark`) |
| Classification — token-array fit | 7 (IFC entity, `PredefinedType`, `ObjectType`, IFC schema version, Revit `Category`, `Type Mark`, family/type names, UniClass/OmniClass code/title/table) | 2 (`State`, `ChangeAction`) | 9 |
| Non-token-array typed structure | 2 (Revit `LevelId`/`GroupId`/`OwnerViewId`/`AssemblyInstanceId`/`DesignOption` — counted as "typed relationship" once) | 4 (`OwningUser`, `OwningApplication`, `LastModifiedDate`, `CreationDate`) | 6 |

(The Revit relationship-references are functionally the same shape — five
fields, one kind. The IFC `OwnerHistory` timestamps are two fields of the
same kind. The composite-reference fields are two of the same kind.)

**Headline AECO finding:** **non-token-array typed structure does
surface** — IFC timestamps (`IfcTimeStamp`, integer seconds since epoch),
IFC composite references (`IfcPersonAndOrganization`, `IfcApplication`),
and Revit `ElementId`-typed relationships. Whether they are *required*
to travel with the identifier is judgment-dependent: an identifier-only
exchange can omit them; an OwnerHistory-aware exchange that the IFC spec
prescribes for each `IfcRoot` instance cannot.

The token-array bucket carries the canonical "what kind of thing is
this?" classification work cleanly — entity types, predefined-type enums,
classification codes, family/type names. The token-array claim is
strongest there.

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
| `AssetInformation.assetKind` | `AssetKind` enumeration (`Type`, `Instance`, `NotApplicable`) | Whether this AAS describes a type or an instance | **Classification — token-array fit** |
| `AssetInformation.assetType` | `Identifier` (string) | Classification or taxonomy reference | **Classification — token-array fit** (it's a reference *string*, not a typed Reference) |
| `AssetInformation.specificAssetIds` | `List<SpecificAssetId>` (composite) | Domain-specific identifiers (each is a structured triple) | **Non-token-array typed structure** (list of structured records) |
| `SpecificAssetId.name` | `LabelType` (string, max 64) | Label naming the identifier kind | **Classification — token-array fit** (paired with `value`) |
| `SpecificAssetId.value` | `IdentifierType` (string) | The identifier value itself | **Identity** |
| `SpecificAssetId.externalSubjectId` | `Reference` (composite — see below) | Subject/tenant context | **Non-token-array typed structure** (composite reference) |
| `SpecificAssetId.semanticId` | `Reference` | Semantic definition pointer | **Non-token-array typed structure** (composite reference) |
| `Identifiable.administration` (`AdministrativeInformation`) | composite: `version`, `revision`, `creator: Reference`, `templateId: Identifier` | Administrative metadata; `creator` is a typed Reference | **Non-token-array typed structure** (composite, contains a Reference) |
| `Submodel.kind` (`ModellingKind`) | enum (`Template`, `Instance`) | Whether the submodel is a template or instance | **Classification — token-array fit** |
| `Submodel.semanticId` | `Reference` | What concept this submodel realizes (e.g. `urn:idta:dpp:battery:1.0`) | **Non-token-array typed structure** (composite reference) |

**The submodel element catalog** (the AAS extensible-metadata surface
that travels under each AAS identifier — sourced from the
[IDTA Submodel Element Types overview](https://industrialdigitaltwin.io/aas-specifications/IDTA-01001/v3.1.1/spec-metamodel/submodel-elements.html)):

| Submodel element | Native typing | Bucket |
|---|---|---|
| `Property.value` | XSD-typed: `xs:string`, `xs:int`, `xs:long`, `xs:decimal`, `xs:double`, `xs:float`, `xs:boolean`, `xs:date`, `xs:dateTime`, `xs:time`, `xs:duration`, `xs:anyURI`, `xs:base64Binary` | **Non-token-array typed structure** for any numeric, date, boolean, or binary case (token-array fit only when `valueType == xs:string`) |
| `MultiLanguageProperty.value` | `MultiLanguageTextType` (list of `LangStringTextType` pairs) | **Non-token-array typed structure** (multilingual record list) |
| `Range.min` / `Range.max` | Pair of XSD-typed values, same type set as `Property.value` | **Non-token-array typed structure** (a pair, with numeric/date possible) |
| `ReferenceElement.value` | `Reference` (composite — list of `Key`s) | **Non-token-array typed structure** (composite reference) |
| `RelationshipElement.first` / `.second` | Pair of `Reference`s | **Non-token-array typed structure** (composite reference pair) |
| `AnnotatedRelationshipElement.annotations` | List of `DataElement` (recursive) | **Non-token-array typed structure** (recursive composite) |
| `File.value` / `File.contentType` | URI string + MIME content-type token | Mixed: identity-adjacent (URI) + classification (content-type token) |
| `Blob.value` / `Blob.contentType` | `xs:base64Binary` + MIME content-type token | **Non-token-array typed structure** (binary value) |
| `Entity.entityType` | `EntityType` enum (`CoManagedEntity`, `SelfManagedEntity`) | Classification — token-array fit |
| `Entity.globalAssetId` | `Identifier` | Identity |
| `Entity.specificAssetIds` | `List<SpecificAssetId>` | Non-token-array typed structure (same as above) |
| `Capability` | (placeholder, no value) | n/a |
| `Operation.inputVariables` / `outputVariables` / `inoutputVariables` | Lists of `OperationVariable` (each wrapping a `SubmodelElement`) | **Non-token-array typed structure** (recursive composite) |
| `BasicEventElement.observed` | `Reference` | **Non-token-array typed structure** (composite reference) |

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
| `State` (`Released`) | structured — `Value` token + `Display` string (per [PTC docs](https://www.ptc.com/en/support/article/CS304928)) | Lifecycle state | **Classification — token-array fit** (the `Value` is a controlled token) |
| `Type` (`Part`, `Subassembly`) | `Edm.String` (controlled vocabulary) | Part type | **Classification — token-array fit** |
| `OrganizationId` / `Organization.Name` | `Edm.String` | Organization owning the part | **Classification — token-array fit** |
| `CreatedOn` | `Edm.DateTimeOffset` | When the part record was created | **Non-token-array typed structure** (timestamp) |
| `LastModified` | `Edm.DateTimeOffset` | Last modification time | **Non-token-array typed structure** (timestamp) |

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
| `MTART` | `CHAR(4)` (Material Type, controlled vocab) | Material type code (`FERT`, `HALB`, `ROH`, …) | **Classification — token-array fit** |
| `MATKL` | `CHAR(9)` (Material Group, controlled vocab) | Material group code | **Classification — token-array fit** |
| `MEINS` | `UNIT(3)` (base unit of measure) | Unit-of-measure code (controlled vocab) | **Classification — token-array fit** |
| `ERSDA` | `DATS(8)` | Date the material record was created | **Non-token-array typed structure** (date) |
| `LAEDA` | `DATS(8)` | Date of last change | **Non-token-array typed structure** (date) |
| `ERNAM` | `CHAR(12)` | Username of creator | **Identity-adjacent** |
| `NTGEW` | `QUAN(13,3)` (numeric, 3 decimals) | Net weight | **Non-token-array typed structure** (decimal with unit) |
| `BRGEW` | `QUAN(13,3)` | Gross weight | **Non-token-array typed structure** (decimal with unit) |
| `GEWEI` | `UNIT(3)` | Weight-unit code (controlled vocab — `KG`, `LB`, …) | **Classification — token-array fit** |
| `VOLUM` | `QUAN(13,3)` | Volume | **Non-token-array typed structure** (decimal with unit) |
| `MSTAE` | `CHAR(2)` (cross-plant material status, controlled) | Cross-plant material status code | **Classification — token-array fit** |
| `MSTDE` | `DATS(8)` | Date from which the material status applies | **Non-token-array typed structure** (date) |

`NTGEW`/`BRGEW`/`VOLUM` carry their unit via a paired field
(`GEWEI`, `VOLEH`); the full quantity is a (number, unit) pair —
structurally a typed measure, not a string.

#### Manufacturing/PLM bucket counts (33 fields surveyed across AAS / Windchill / SAP)

| Bucket | Count |
|---|---|
| Identity | 4 (AAS `globalAssetId`, AAS `SpecificAssetId.value`, Windchill `ID`, SAP `MATNR`) |
| Identity-adjacent | 5 (Windchill `Number`, `Name`, `Revision`, `Version`; SAP `ERNAM`) |
| Classification — token-array fit | 9 (AAS `assetKind`, `assetType`, `SpecificAssetId.name`, `Submodel.kind`; Windchill `State`, `Type`, `OrganizationId`; SAP `MTART`, `MATKL`, `MEINS`, `GEWEI`, `MSTAE` — counted as 9 distinct kinds, with the unit codes counted once) |
| **Non-token-array typed structure** | **15+** — see breakdown below |

**The non-token-array typed fields explicitly:**

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

**Headline manufacturing finding:** the existing comparison's claim that
"7 of 8 simulated PLM/ERP fields fit cleanly" was conducted against a
synthesized 8-field set (industry_scenarios.md §4.2). The actual
manufacturing identifier surface defined by IDTA, PTC, and SAP is
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

## Cross-vertical synthesis

*[To be filled in after Robotics and M&E.]*

## Effect on the load-bearing assertion

*[To be filled in after the synthesis.]*

## Property-set excursion (AECO and PLM)

(Held for after the per-vertical census — IFC `Pset_*` and AAS submodel
properties are arguably *not* part of the identifier package, but
since they are the canonical extension surface in their domains, a
short note on what their value-typing looks like is included here so
the experiment doesn't look the other way.)


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

## Cross-vertical synthesis

*[To be filled in after all four verticals are enumerated.]*

## Effect on the load-bearing assertion

*[To be filled in after the synthesis.]*

## Property-set excursion (AECO and PLM)

(Held for after the per-vertical census — IFC `Pset_*` and AAS submodel
properties are arguably *not* part of the identifier package, but
since they are the canonical extension surface in their domains, a
short note on what their value-typing looks like is included here so
the experiment doesn't look the other way.)


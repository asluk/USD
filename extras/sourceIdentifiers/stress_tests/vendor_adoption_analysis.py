#!/usr/bin/env python3
"""
Principle-Derived Scoring for Source Identifier Approaches A, B, C, and D.

Re-derived 2026-05-07 from primitives — full rerun, not a patch.

Source-of-truth surface this scoring derives from:

 - Proposal 105 README (PixarAnimationStudios/OpenUSD-proposals#105),
   Principles section. The eight scoring dimensions are the eight
   authorized principles. Each per-dimension question rubric is
   anchored to the principle's literal text without broadening.
 - AOUSD Core Specification (`core-spec-wg/specification`),
   particularly `schemas/README.md` (typed/applied schemas, prim
   definitions, multi-apply instances, list-op `apiSchemas`) and
   `document_data_model/README.md` (`assetInfo` advisory dictionary,
   foundational value-type set for dictionary metadata).
 - Each candidate's actual mechanism primitives:
   - A: `pxr/usd/usdSourceId/schema.usda` (non-applied convenience
     wrapper on `assetInfo["sourceIds"][<domain>]`).
   - B: `pxr/usd/usdSourceIdSchema/schema.usda` (multi-apply
     `SourceIdSchemaAPI` with four typed properties: `primaryId`,
     `revision`, `domain`, `label`).
   - C: `pxr/usd/usdSourceIdHybrid/schema.usda` (multi-apply
     `SourceIdHybridAPI` with the same four typed properties +
     `assetInfo["sourceIds"][<instance>]` overflow by convention).
   - D: `examples/column_d.usda` + `examples/verify_column_d.py`
     (existing `UsdSemanticsLabelsAPI` for classification facets +
     `assetInfo["source"][<system>]` for identity / heterogeneous
     overflow — no new schema introduced).
 - The field census in `details/field_classification_experiment.md`
   for what real identifier-package shapes look like across the four
   verticals.

Earlier scoring iterations (preserved as
`vendor_adoption_analysis_legacy.py` for the pre-2026-05-07 lineage,
plus the prior-session principle-derived rebuild that this rerun
supersedes) carried interpretive broadenings of several principle
texts and incomplete primitive-grounding of the per-mechanism
rationales. This rerun re-derives every dimension and every per-
candidate score from the primitives above, treating the prior text
as audit material rather than as the starting point.

Implementation-level vs standard-level: per PR 105 #3
("A vendor extension... is not the same thing as an OpenUSD
plugin -- the latter is a runtime implementation detail. The AOUSD
Core Specification 1.0 established this distinction by specifying
schemas without prescribing a plugin or schema registry."),
schema-distribution cost and plugin-mechanism cost are
implementation-level concerns. They are surfaced in
IMPLEMENTATION_CONSIDERATIONS below as separate notes, not baked
into any principle-derived score. This avoids double-counting
ratification cost across Vendor extensibility and Minimal
disruption — a structural error the prior scoring carried.

Per-dimension scores are 1-5 against published anchors. Anchors and
per-mechanism rationales are the primary reading; numerical totals
are illustrative of how the four mechanisms trade off across
principles, not a verdict.
"""

import json
import os

OUTPUT_DIR = os.path.dirname(os.path.abspath(__file__))


DIMENSIONS = [
    {
        "principle": "Separation of concerns",
        "principle_id": 1,
        "principle_text": (
            "USD namespace paths and external source identifiers serve "
            "different purposes. They should be stored and accessed "
            "through distinct mechanisms, even if they sometimes carry "
            "the same value."
        ),
        "question": (
            "Does the mechanism keep external source identifier "
            "metadata distinct from USD namespace paths and other USD "
            "machinery?"
        ),
        "anchors": {
            5: "External identifier metadata is stored and accessed through a mechanism distinct from USD namespace paths; nothing about identifier content leaks into prim names or path semantics.",
            4: "Mostly distinct; minor overlap with USD path semantics (e.g. some content surfaces in prim names by convention).",
            3: "Identifier metadata coexists with USD path content in shared machinery; tools must distinguish them by parsing.",
            2: "Identifier metadata is encoded into prim names or other path-bearing surfaces.",
            1: "Identifier metadata bleeds into USD path semantics or composition machinery.",
        },
    },
    {
        "principle": "Industry agnosticism",
        "principle_id": 2,
        "principle_text": (
            "The mechanism should not be specific to any one industry's "
            "identifier scheme. It should be flexible enough to carry "
            "IFC GUIDs, PLM part numbers, M&E asset database IDs, and "
            "schemes not yet envisioned. This follows from the open "
            "world assumption: the set of external systems that may "
            "need to identify a prim is not closed."
        ),
        "question": (
            "Does the mechanism carry the full identifier-package "
            "shape real systems bundle (per the field census: identity "
            "strings, controlled-vocabulary classification facets, and "
            "heterogeneous typed fields like timestamps, numeric "
            "measures with units, composite references, polymorphic "
            "XSD-typed values) without per-industry engineering, "
            "accommodating schemes not yet envisioned?"
        ),
        "anchors": {
            5: "Mechanism carries the full identifier-package shape across the field census (identity + classification + heterogeneous typed) without per-industry engineering. Open-world: new schemes accommodated by adding instances/dict-keys.",
            4: "Carries identity + classification + most heterogeneous typed shapes; rare per-industry accommodation needed for edge cases.",
            3: "Carries the primary identifier for any industry's scheme cleanly; per-industry engineering required for the heterogeneous-typed surface beyond a fixed common subset.",
            2: "Carries a fixed common subset; per-industry engineering required to carry beyond.",
            1: "Industry-specific.",
        },
    },
    {
        "principle": "Vendor extensibility",
        "principle_id": 3,
        "principle_text": (
            "Any vendor, standards body, or consortium should declare "
            "its own identifier scheme without central approval before "
            "deployment. Identifiers may be opaque. Tiered lifecycle "
            "(vendor -> multi-vendor -> core) at the data-model level "
            "(per PR 105 #3: 'A vendor extension is not the same thing "
            "as an OpenUSD plugin -- the latter is a runtime "
            "implementation detail.')."
        ),
        "question": (
            "Can a vendor declare its own identifier scheme without "
            "central approval before deployment? Does the mechanism "
            "support a tiered lifecycle (vendor -> multi-vendor -> "
            "core) at the data-model level?"
        ),
        "anchors": {
            5: "Vendor ships today, no central approval needed at the data-model level. Tiered lifecycle is a registry-level promotion (a spec document or vocabulary addition), not a re-author at each tier.",
            4: "Vendor ships today via a fallback path (e.g. dict overflow); promotion to a canonical typed tier requires central approval at the data-model level (schema versioning bump).",
            3: "Vendor ships today via a fallback path; canonical path requires central approval.",
            2: "Central approval at the data-model level required to ship at all (e.g. ratification of a typed schema before the mechanism can be used).",
            1: "Single-vendor lock-in.",
        },
    },
    {
        "principle": "Composability",
        "principle_id": 4,
        "principle_text": (
            "External identifiers should participate in USD's "
            "composition model in a well-defined way. It should be "
            "clear how source identifiers are resolved when a prim is "
            "referenced, inherited, or specialized."
        ),
        "question": (
            "Does the mechanism participate in USD's composition "
            "model with well-defined behavior under reference, "
            "inherit, specialize?"
        ),
        "anchors": {
            5: "Composition behavior is well-defined under reference/inherit/specialize per the AOUSD Core Spec (per-property for typed properties; element-wise for dictionary metadata).",
            4: "Composition behavior is well-defined for the primary tier; minor edge cases require pipeline-specific handling.",
            3: "Composition behavior is well-defined for some content types; others require pipeline-specific handling.",
            2: "Composition behavior is partially specified; tool-side conventions fill gaps.",
            1: "Composition behavior is undefined.",
        },
    },
    {
        "principle": "Discoverability",
        "principle_id": 5,
        "principle_text": (
            "Tools should be able to discover that a prim carries "
            "source identifiers without prior knowledge of a "
            "pipeline-specific convention. This argues for a schema-"
            "based approach rather than ad-hoc customData usage."
        ),
        "question": (
            "Can tools discover that a prim carries source "
            "identifiers without prior knowledge of a pipeline-"
            "specific convention?"
        ),
        "anchors": {
            5: "Per-(system, facet) presence discoverable from the schema surface (apiSchemas) alone, across all content types — no parsing of metadata dictionaries needed.",
            4: "Per-system presence discoverable from the schema surface (apiSchemas) alone; per-facet structure or per-content-type granularity requires parse.",
            3: "Per-prim presence inferable from a *standardized* (not pipeline-specific) metadata key; per-system or per-facet detail requires parse.",
            2: "Presence requires parsing metadata dictionaries with a known but non-standardized key; without the convention, tools cannot reliably discover.",
            1: "Discovery requires prior knowledge of pipeline-specific conventions.",
        },
    },
    {
        "principle": "External queryability",
        "principle_id": 6,
        "principle_text": (
            "Storing a source identifier on a prim is necessary but "
            "not sufficient. Real-world workflows also need to "
            "resolve the reverse question: given an external "
            "identifier, which USD layers and prims reference it? "
            "The source identifier mechanism should make it tractable "
            "for consumers to build external indexes over USD content."
        ),
        "question": (
            "Does the mechanism make it tractable for consumers to "
            "build external indexes for 'given external identifier "
            "X, find prim' queries?"
        ),
        "anchors": {
            5: "Schema-targeted validators / iterators (`plugInfo.json` `schemaTypes`) cover the full identifier surface; index construction is narrow-targeted across all content types.",
            4: "Schema-targeted for one tier (typed properties or per-facet schemas); parse-based for the other tier (overflow dict). Mixed surface.",
            3: "Stage traversal with metadata parse at each prim. Tractable but parse-based.",
            2: "Stage traversal plus per-prim convention checks; index construction is per-domain.",
            1: "External indexes are intractable without out-of-band metadata.",
        },
    },
    {
        "principle": "Round-trip fidelity",
        "principle_id": 7,
        "principle_text": (
            "Source identifiers should survive a round-trip through "
            "USD without loss, even if the characters they contain "
            "are not valid in USD prim names."
        ),
        "question": (
            "Do source identifier strings (including characters not "
            "valid in USD prim names) survive a round-trip through "
            "USD without loss?"
        ),
        "anchors": {
            5: "Identifier strings are stored verbatim as UTF-8 strings (string property values, dict string values, or token-array element strings); any character set survives.",
            4: "Identifier strings survive but require an explicit container choice to avoid loss.",
            3: "Most characters survive; some require transcoding.",
            2: "Strings undergo transformation that has to be inverted on read.",
            1: "Identifiers can be lost or silently corrupted on round-trip.",
        },
    },
    {
        "principle": "Minimal disruption",
        "principle_id": 8,
        "principle_text": (
            "The solution should build on USD's existing strengths. "
            "It should not require fundamental changes to the "
            "composition engine or namespace path semantics."
        ),
        "question": (
            "Does the mechanism avoid fundamental changes to the "
            "composition engine or namespace path semantics?"
        ),
        "anchors": {
            5: "No changes to the composition engine or namespace path semantics; uses existing AOUSD Core Spec mechanisms (assetInfo metadata field, applied schemas) as specified.",
            4: "No changes to composition or namespace; minor extension of existing mechanisms within their specified envelope.",
            3: "Slight extension of composition or namespace path semantics, but not fundamental.",
            2: "Fundamental changes to composition engine or namespace path semantics required.",
            1: "Major rework of composition engine or namespace path semantics.",
        },
        "note": (
            "Schema-distribution cost and plugin-mechanism cost are "
            "implementation-level concerns per PR 105 #3 and are "
            "surfaced in IMPLEMENTATION_CONSIDERATIONS below, not "
            "scored here. Including them in Minimal disruption "
            "double-counted with Vendor extensibility (which already "
            "captures schema-ratification cost as a barrier to ship-"
            "today) and conflated standard-level disruption (the "
            "principle's literal scope) with implementation-level "
            "rollout cost (out of scope per the principle text)."
        ),
    },
]


def score_a():
    """Approach A: assetInfo dictionaries with non-applied convenience API."""
    return {
        "name": "A - assetInfo dictionaries (non-applied convenience API)",
        "primitives": (
            "Non-applied API schema (`UsdSourceIdAPI`); no apiSchemas entry. "
            "Data lives in `assetInfo[\"sourceIds\"][<domain>]` as a nested "
            "dictionary with keys `primaryId` (string), `revision` (string), "
            "`metadata` (nested dict). Schema provides convenience access "
            "only; data's presence in assetInfo IS the discovery signal."
        ),
        "scores": {
            "Separation of concerns": (5, "Identifier metadata in `assetInfo[\"sourceIds\"][<domain>]`. Not in prim name; not in path semantics; not in any USD-internal machinery."),
            "Industry agnosticism": (5, "`assetInfo` dictionary metadata accepts the broad foundational value-type set per the AOUSD Core Spec (string, int, double, bool, asset, arrays, nested dictionaries; no specialized types). All four content types from the field census fit: identity strings, identity-adjacent labels, controlled-vocabulary classification, heterogeneous typed (timestamps stored as int/double, numeric measures, composite references stored as nested dicts). Open-world: new schemes accommodated by adding a sub-dict key today."),
            "Vendor extensibility": (5, "Vendor adds `assetInfo[\"sourceIds\"][<vendor>]` today; no AOUSD-level approval required at the data-model level. Tiered lifecycle: spec-text formalization of dict-key conventions in an AOUSD Domains Registry — a spec document, not a re-author. Track-record note: spec-text formalization as a primary lifecycle vehicle is newer in AOUSD practice than schema ratification (B/C's path); see IMPLEMENTATION_CONSIDERATIONS."),
            "Composability": (5, "`assetInfo` dictionary metadata composes element-wise per the AOUSD Core Spec (advisory dict metadata composes element-wise across composition arcs). Composition_test experiments show stable per-key behavior for non-timevarying string values. Well-defined under reference/inherit/specialize."),
            "Discoverability": (3, "Non-applied schema; no apiSchemas instance. Discovery requires reading `assetInfo` and checking for the standardized `sourceIds` key. The convention key is standardized at the AOUSD level — not pipeline-specific (which would mean each pipeline names its own key). Parse-based detection on a standardized key clears the principle text but is the lowest-cost-of-discovery in this comparison."),
            "External queryability": (3, "Stage traversal with `assetInfo` dict parse at each prim. Tractable but parse-based. Consumers building per-system indexes pay the parse cost on every prim."),
            "Round-trip fidelity": (5, "Identifier strings stored as `string` values in dict; UTF-8 survives. Any characters survive."),
            "Minimal disruption": (5, "Builds on existing `assetInfo` core metadata field. No changes to composition engine or namespace path semantics."),
        },
    }


def score_b():
    """Approach B: multi-apply schema with four typed common properties."""
    return {
        "name": "B - Multi-apply schema (typed common fields)",
        "primitives": (
            "Multi-apply API schema (`UsdSourceIdSchemaAPI`); "
            "`propertyNamespacePrefix = \"sourceIdentifier\"`. Four typed "
            "properties per instance: `primaryId` (string), `revision` "
            "(string), `domain` (token), `label` (string). All have empty-"
            "string fallbacks. Each external system is a multi-apply "
            "instance: `SourceIdSchemaAPI:<system>`. No overflow path: "
            "domain-specific fields beyond the four common have no slot in "
            "the schema."
        ),
        "scores": {
            "Separation of concerns": (5, "Identifier metadata in typed schema properties under the `sourceIdentifier:<system>:` namespace. Not in prim name; not in path semantics."),
            "Industry agnosticism": (3, "The four typed common properties carry the *primary* identifier from any industry's scheme cleanly (`primaryId` admits IFC GUIDs, PLM part numbers, M&E asset IDs as opaque strings). The heterogeneous typed surface the field census quantifies (AAS `Property.value` polymorphic XSD types; IFC `IfcOwnerHistory.LastModifiedDate` timestamps; SAP `NTGEW`/`BRGEW` decimal-with-unit measures; AAS composite References) has no slot in B's fixed surface — per-industry companion schemas required to carry it. The principle's open-world clause penalizes this for unforeseen package shapes."),
            "Vendor extensibility": (2, "A vendor cannot ship until `UsdSourceIdSchemaAPI` is ratified at the AOUSD level. Even after ratification, vendors needing fields beyond the four common must ship companion schemas, which require their own ratification. Central approval at the data-model level is required to ship at all."),
            "Composability": (5, "Typed schema properties compose per-property under USD's standard property composition model. Well-defined under reference/inherit/specialize per the Core Spec; no dict-tier element-wise composition."),
            "Discoverability": (4, "Per-system instance in `apiSchemas` (`SourceIdSchemaAPI:<system>`). Tools answer 'does this prim carry source identifiers, and from which systems?' from the apiSchemas list alone. Per-facet structure not exposed (no per-facet typed properties)."),
            "External queryability": (5, "Schema-targeted validators via `plugInfo.json` `schemaTypes` (filter by `SourceIdSchemaAPI:*`). Per-instance properties typed and queryable. Index construction is narrow-targeted across the full B surface (because B's full surface IS the typed properties)."),
            "Round-trip fidelity": (5, "Identifier strings stored as `string` schema property values; UTF-8 survives."),
            "Minimal disruption": (5, "Introduces a new applied schema. Applied schemas are existing AOUSD Core Spec machinery (specified in `schemas/README.md`); no changes to composition engine or namespace path semantics. Schema-distribution and ratification cost are implementation-level concerns per PR 105 #3 and are surfaced in IMPLEMENTATION_CONSIDERATIONS."),
        },
    }


def score_c():
    """Approach C: multi-apply schema with typed common fields + assetInfo overflow."""
    return {
        "name": "C - Hybrid (typed common fields + assetInfo overflow)",
        "primitives": (
            "Multi-apply API schema (`UsdSourceIdHybridAPI`) with the same "
            "four typed properties as B per instance. Plus, by convention, "
            "`assetInfo[\"sourceIds\"][<instance_name>]` carries domain-"
            "specific overflow as a freeform dictionary; the instance name "
            "links the typed schema and the overflow dict. The overflow "
            "convention is documented but not enforced by the schema "
            "(C's `schema.usda` defines only the four typed properties)."
        ),
        "scores": {
            "Separation of concerns": (5, "Identifier metadata in typed schema properties under `sourceIdentifier:<system>:` + `assetInfo[\"sourceIds\"][<instance>]` overflow. Not in prim name; not in path semantics."),
            "Industry agnosticism": (5, "Typed properties carry primary IDs (same as B); overflow dict tier accepts the broad foundational value-type set (same as A). All four content types from the field census fit. Open-world: new schemes accommodated by adding instances + overflow keys today."),
            "Vendor extensibility": (4, "Vendor ships `assetInfo[\"sourceIds\"][<instance>]` overflow today via the convention — fallback path. The typed common-fields tier requires `UsdSourceIdHybridAPI` to be ratified at the AOUSD level. Promotion of stable overflow fields to typed schema properties requires schema versioning + re-ratification. Ship-today exists via overflow; canonical typed path requires central approval."),
            "Composability": (5, "Typed properties per-property; overflow dict element-wise. Both well-defined under reference/inherit/specialize per the Core Spec."),
            "Discoverability": (4, "Per-system instance in `apiSchemas` (`SourceIdHybridAPI:<system>`). Per-system presence from apiSchemas alone, same as B. Per-facet detail in overflow dict requires parse."),
            "External queryability": (4, "Schema-targeted for the typed tier (same as B); parse-based for the overflow tier. Mixed surface — primary-ID indexing is schema-targeted, full-package indexing requires the parse."),
            "Round-trip fidelity": (5, "Identifier strings stored as `string` schema properties + `string` overflow values; UTF-8 survives."),
            "Minimal disruption": (5, "Same as B — new applied schema, no changes to composition engine or namespace path semantics. Implementation-level concerns surfaced in IMPLEMENTATION_CONSIDERATIONS."),
        },
    }


def score_d():
    """Approach D: existing UsdSemanticsLabelsAPI + assetInfo overflow (no new schema)."""
    return {
        "name": "D - Labels + assetInfo (existing schemas; no new ratification)",
        "primitives": (
            "No new schema introduced. Uses existing `UsdSemanticsLabelsAPI` "
            "(in OpenUSD 24.11+) for classification facets, applied as "
            "`SemanticsLabelsAPI:<system>:<facet>` (multi-apply instance "
            "name encodes both system and facet). Plus "
            "`assetInfo[\"source\"][<system>]` as a freeform dict for "
            "identity (the opaque pointer back into each source system) and "
            "any heterogeneous-typed overflow. The `assetInfo[\"source\"]` "
            "tier is structurally the same as A's overflow tier — both are "
            "`assetInfo` dict metadata accepting the broad foundational "
            "value-type set. The `column_d.usda` example demonstrates 10 "
            "Labels-API instances on a single column for IFC + Revit + "
            "UniClass + OmniClass facets."
        ),
        "scores": {
            "Separation of concerns": (5, "Identity in `assetInfo[\"source\"][<system>]`; classification facets via `SemanticsLabelsAPI:<system>:<facet>`. Not in prim name; not in path semantics."),
            "Industry agnosticism": (5, "`assetInfo[\"source\"]` overflow accepts the broad foundational value-type set (same as A's mechanism). Plus existing `UsdSemanticsLabelsAPI` for classification facets. Identity, identity-adjacent, and heterogeneous typed all fit in overflow; classification gets the typed Labels surface. Open-world: new schemes accommodated by adding sub-dict keys + applying Labels facets today."),
            "Vendor extensibility": (5, "Vendor ships `assetInfo[\"source\"][<vendor>]` overflow today + applies `SemanticsLabelsAPI:<vendor>:<facet>` for classification facets today. No AOUSD-level approval at the data-model level — Labels is in OpenUSD 24.11+ and vendor-named instances are open to vendor authoring. Tiered lifecycle: spec-text formalization of dict-key conventions + Labels facet vocabulary additions. Same track-record note as A — see IMPLEMENTATION_CONSIDERATIONS."),
            "Composability": (5, "Labels token-array attributes compose per-property (per-facet); `assetInfo[\"source\"]` overflow dict composes element-wise. Both well-defined under reference/inherit/specialize per the Core Spec."),
            "Discoverability": (4, "Per-(system, facet) instance in `apiSchemas` (`SemanticsLabelsAPI:<system>:<facet>`) for the classification slice — finest granularity available in this comparison; tools can answer 'which facets of which systems are present?' from apiSchemas alone for classification. For non-classification content (identity, identity-adjacent, heterogeneous typed), D inherits A's parse-based path on `assetInfo[\"source\"]`. Per-prim 'does this prim carry source identifiers?' is answerable from apiSchemas for any classification-bearing prim. Per-vertical conditionality: D's classification advantage is meaningful for AECO (7-9 facets per asset) and thinner for PLM/Robotics/M&E (where classification is sparse) — see IMPLEMENTATION_CONSIDERATIONS."),
            "External queryability": (4, "Schema-targeted validators for `SemanticsLabelsAPI:*` instances enable narrow targeting for classification-axis indexing (e.g. 'find all prims with `revit:familyType` = `W14x90`'). Identity-axis indexing on `assetInfo[\"source\"]` is parse-based, same as A. Mixed surface."),
            "Round-trip fidelity": (5, "Identifier strings stored as `string` values in `assetInfo[\"source\"]` dict; classification facet values stored as `token[]` arrays (each token is a UTF-8 string). UTF-8 survives across both surfaces."),
            "Minimal disruption": (5, "Builds on existing `UsdSemanticsLabelsAPI` (in OpenUSD 24.11+) and existing `assetInfo` core metadata field. No new schema introduced. No changes to composition engine or namespace path semantics."),
        },
    }


IMPLEMENTATION_CONSIDERATIONS = {
    "preface": (
        "Per PR 105 #3, vendor extensions operate at the data-model level "
        "and are independent of any particular plugin architecture: 'A "
        "vendor extension... is not the same thing as an OpenUSD plugin -- "
        "the latter is a runtime implementation detail.' The following "
        "items are real considerations for the AOUSD ratification "
        "decision, but they are implementation-level — out of scope of the "
        "eight authorized principles. They are surfaced here so the "
        "comparison reflects them honestly without baking them into "
        "principle-derived scores (which would conflate standard-level "
        "with implementation-level concerns and double-count them across "
        "principles)."
    ),
    "items": [
        {
            "name": "Schema-ratification cost",
            "applies_to": ["B", "C"],
            "detail": (
                "B and C introduce new applied schemas (`UsdSourceIdSchemaAPI`, "
                "`UsdSourceIdHybridAPI`) that must be ratified at the AOUSD "
                "level before vendors can adopt the mechanism. A and D "
                "introduce no new schemas (A's wrapper is non-applied "
                "convenience over an existing core metadata field; D uses "
                "existing `UsdSemanticsLabelsAPI` + existing `assetInfo`). "
                "This cost is captured in Vendor extensibility (where the "
                "ship-today vs ratification-blocking is the principle-"
                "derived signal) but the *scale* of the cost — multi-month "
                "AOUSD ratification process per schema — is implementation-"
                "level."
            ),
        },
        {
            "name": "Schema-distribution cost (conditional)",
            "applies_to": ["B", "C"],
            "detail": (
                "B and C, once ratified, must distribute their schema "
                "plugins across the matrix the AOUSD Build Interest Group "
                "is scoping (DCC x USD release x Python x OS x runtime x "
                "build flavor). Per Aaron Luk's 2026-05-07 call: this is "
                "elevated currently — the Build IG epic "
                "[`aousd/build-ig-initiatives#28`] is actively scoping the "
                "substrate (hosted binaries, plugin registration via "
                "importlib, conda-forge / PyPI distribution); the cost is "
                "expected to lighten as those initiatives land. "
                "A and D require no new plugin distribution because they "
                "introduce no new schemas."
            ),
        },
        {
            "name": "Spec-text-formalization track record",
            "applies_to": ["A", "D"],
            "detail": (
                "A's and D's promotion path (vendor convention -> AOUSD "
                "spec-text formalization of dict-key conventions / Labels "
                "facet vocabulary) is a valid AOUSD-level lifecycle "
                "vehicle, but it is newer in AOUSD practice than schema "
                "ratification (B/C's path). The latter has more precedent "
                "in AOUSD's standards production. This is a TAC-perception "
                "consideration: a TAC member evaluating against established "
                "patterns may weigh schema ratification as more 'familiar' "
                "than spec-text formalization. Not a principle-derived "
                "score adjustment; the principles themselves don't "
                "privilege one path over the other."
            ),
        },
        {
            "name": "Per-vertical conditionality of D's classification advantage",
            "applies_to": ["D"],
            "detail": (
                "D's per-(system, facet) discoverability via "
                "`SemanticsLabelsAPI:<system>:<facet>` is meaningful in "
                "proportion to the classification richness of each "
                "vertical's identifier package. From the field census: "
                "AECO carries 7-9 classification facets per asset (IFC "
                "entity type, PredefinedType, ObjectType; Revit Category, "
                "Type Mark, family/type names; UniClass code, OmniClass "
                "code) — D's per-facet capability has the most per-prim "
                "value here. PLM/Manufacturing has 9 classification facets "
                "across AAS/Windchill/SAP but is dominated by 15+ "
                "heterogeneous typed fields (timestamps, decimal-with-unit "
                "measures, composite References) that D handles via the "
                "`assetInfo` overflow tier (same as A) — D's classification "
                "advantage is a smaller fraction of the surface. Robotics "
                "and M&E have sparse classification surfaces — D's "
                "classification advantage is thin."
            ),
        },
        {
            "name": "Standard-vs-implementation framing for the TAC discussion",
            "applies_to": ["all"],
            "detail": (
                "AOUSD Core Spec is the standard; OpenUSD is currently "
                "the only implementation but isn't the standard itself. "
                "Costs that are real for current OpenUSD (schema-"
                "distribution matrix, runtime mechanism specifics) should "
                "be weighed as implementation-level concerns rather than "
                "standard-level constraints. The TAC question's actual "
                "shape is: 'What should AOUSD ratify as the standard for "
                "source identifiers, recognizing that implementations are "
                "free to vary in how they realize it?' — not 'which "
                "mechanism does current OpenUSD support best?' This "
                "framing is load-bearing for any of the four candidates "
                "and is treated as foreground in the TAC discussion."
            ),
        },
    ],
}


def main():
    approaches = [score_a(), score_b(), score_c(), score_d()]
    output = {
        "methodology": {
            "framing": (
                "Scoring dimensions derived from the eight authorized "
                "design principles in proposal 105. Per-dimension question "
                "rubrics anchor to each principle's literal text without "
                "broadening. Per-mechanism scores derived from primitive-"
                "level inspection of each candidate's actual mechanism "
                "(schema definitions, example files, AOUSD Core Spec "
                "primitives, the field census). Earlier scoring iterations "
                "are preserved as `vendor_adoption_analysis_legacy.py` for "
                "the original ad-hoc lineage and a prior principle-derived "
                "rebuild that this rerun supersedes — both are retracted."
            ),
            "scoring_anchors": (
                "Per-dimension 1-5 anchors are published in DIMENSIONS "
                "below; per-mechanism justifications cite primitive-level "
                "evidence and the field census."
            ),
            "implementation_vs_principle": (
                "Implementation-level concerns (schema-ratification cost, "
                "schema-distribution cost, spec-text-formalization track "
                "record, per-vertical conditionality) are surfaced in "
                "IMPLEMENTATION_CONSIDERATIONS, not baked into "
                "principle-derived scores. This avoids double-counting "
                "across principles and conflating standard-level (the "
                "principles' scope) with implementation-level rollout cost."
            ),
            "what_the_totals_mean": (
                "Numerical totals are illustrative of how the four "
                "mechanisms trade off across the principles, not a "
                "verdict. The anchors, per-mechanism justifications, and "
                "implementation considerations are the primary reading. "
                "Four of the eight principles produce check-pass scores "
                "across all candidates at the literal-text reading "
                "(Separation of concerns, Composability, Round-trip "
                "fidelity, Minimal disruption); the differentiating "
                "dimensions are Industry agnosticism, Vendor extensibility, "
                "Discoverability, and External queryability."
            ),
        },
        "dimensions": DIMENSIONS,
        "approaches": approaches,
        "implementation_considerations": IMPLEMENTATION_CONSIDERATIONS,
    }

    # Compute totals
    for approach in output["approaches"]:
        approach["total"] = sum(score for score, _ in approach["scores"].values())

    out_path = os.path.join(OUTPUT_DIR, "vendor_adoption_analysis.json")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(output, f, indent=2, ensure_ascii=False)

    # Print a compact table
    dim_names = [d["principle"] for d in DIMENSIONS]
    print("Principle-derived scoring (max 40):")
    print()
    header = f"{'Dimension':<32}" + "".join(f"  {name:<3}" for name in ["A", "B", "C", "D"])
    print(header)
    print("-" * len(header))
    for dim in dim_names:
        row = f"{dim:<32}"
        for approach in output["approaches"]:
            row += f"  {approach['scores'][dim][0]:<3}"
        print(row)
    print("-" * len(header))
    totals = f"{'Total':<32}"
    for approach in output["approaches"]:
        totals += f"  {approach['total']:<3}"
    print(totals)
    print()
    print(f"Output: {out_path}")
    print()
    print("Note: numerical totals are illustrative. Per-dimension")
    print("anchors, per-mechanism justifications, and implementation")
    print("considerations are the primary reading; see the JSON output")
    print("for all three.")


if __name__ == "__main__":
    main()

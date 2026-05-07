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

*[Per-vertical sections to follow as the experiment runs.]*

## Cross-vertical synthesis

*[To be filled in after all four verticals are enumerated.]*

## Effect on the load-bearing assertion

*[To be filled in after the synthesis.]*

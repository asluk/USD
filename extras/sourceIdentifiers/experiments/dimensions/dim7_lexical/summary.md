# Dim 7 — vendor-name lexical scope (P3 + OQ5)

PR #105 Principle 3 (vendor extensibility): "Any vendor or
standards body can declare their own identifier scheme without
central approval." Open Question 5 (namespacing of identifiers):
where the vendor identity lives in each approach.

Each approach has a *vendor slot* — a string that carries the
vendor identity in the layer (dict key for A/C, multi-apply
instance segment for B and D-label, schema class name for B').
This dimension records, per probed vendor name, which slots
accept it end-to-end (apply, author, round-trip) and which
fail (and at what gate). Whether the measured scope is
acceptable under P3 is a downstream question for COMPARISON.md.

**Note on Approach D.** D is a candidate beyond PR #105
(Matt Kuruc strawman, per the criteria file). Its mechanism
has two vendor slots: a dict-key slot for the identifier half
(same shape as A) and a multi-apply instance segment for the
label half (same shape as B). Both slots are probed; the D
section below shows them side by side.

## Slot per approach

- **A** — dict_key
- **B** — apply_instance_and_property
- **Bprime** — schema_class_name
- **C** — dict_key (apply-instance also permissive; bridge unimplemented)
- **D** — split (identifier: dict_key; labels: apply_instance_and_property)

## Result matrix — A, B, B', C

Legend: ✓ = end-to-end authoring works (recovered value equals
authored value);
✓ (dict) = dict-key slot, all probed strings round-trip;
✓ class = class-name passes Tf.IsValidIdentifier;
⚠ silent = ApplyAPI succeeds but Sdf re-namespaces the vendor
identity on parse without raising an error;
✗ apply / ✗ prop / ✗ class = failure at that gate.

| vendor name | A | B | Bprime | C |
|---|---|---|---|---|
| ascii_baseline | ✓ (dict) | ✓ | ✓ class | ✓ (dict) |
| underscore | ✓ (dict) | ✓ | ✓ class | ✓ (dict) |
| hyphen | ✓ (dict) | ✗ prop | ✗ class | ✓ (dict) |
| space | ✓ (dict) | ✗ prop | ✗ class | ✓ (dict) |
| leading_digit | ✓ (dict) | ✗ prop | ✗ class | ✓ (dict) |
| dot | ✓ (dict) | ✗ prop | ✗ class | ✓ (dict) |
| colon | ✓ (dict) | ⚠ silent | ✗ class | ✓ (dict) |
| slash | ✓ (dict) | ✗ prop | ✗ class | ✓ (dict) |
| unicode_letter | ✓ (dict) | ✓ | ✗ class | ✓ (dict) |

## Result matrix — D (two slots)

D has two vendor slots, probed independently. The identifier
slot is a dict key (same shape as A). The label slot is the
ApplyAPI instance segment + property name segment (same shape
as B). Same column legend as above.

| vendor name | identifier slot | label slot |
|---|---|---|
| ascii_baseline | ✓ (dict) | ✓ |
| underscore | ✓ (dict) | ✓ |
| hyphen | ✓ (dict) | ✗ prop |
| space | ✓ (dict) | ✗ prop |
| leading_digit | ✓ (dict) | ✗ prop |
| dot | ✓ (dict) | ✗ prop |
| colon | ✓ (dict) | ⚠ silent |
| slash | ✓ (dict) | ✗ prop |
| unicode_letter | ✓ (dict) | ✓ |

## Observations

- For B and D-label, ApplyAPI accepts the vendor segment but
  the property-name slot is gated by
  `Sdf.Path.IsValidNamespacedIdentifier` per segment. The
  runtime ApplyAPI surface and the SdfAttributeSpec surface
  have different acceptance rules; the probe records both.
- Colons in the vendor name (`siemens:nx`) cause silent
  re-namespacing in B and D-label: ApplyAPI returns success
  but Sdf parses the property name into extra namespace
  segments, so the authored vendor identity differs from the
  recovered shape. report.json records this as
  `silent_renamespace: true`.
- B' (Bprime) class-name slot is gated by
  `Tf.IsValidIdentifier` (ASCII identifier rules: no unicode,
  no hyphen/space/dot, no leading digit). report.json records
  `tf_isvalid_identifier: false` for class names that violate
  these rules; the per-vendor schema cannot be registered
  with such a name and `authoring_succeeded: null` reflects
  that runtime apply was not exercised.
- A, C, and D's identifier slot (dict key under
  `assetInfo.source.<vendor>`) accepted every probed string in
  this run, including unicode and embedded special characters,
  and the recovered values matched the authored values.


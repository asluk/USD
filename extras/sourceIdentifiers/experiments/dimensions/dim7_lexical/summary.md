# Dim 7 — vendor-name lexical scope (P3 + OQ5)

Framing: PR #105 names vendor extensibility (P3) as a core
principle — vendors must be able to declare their own scheme
without central approval. The vendor *name* is the operational
carrier of that vendor identity in every approach. This
dimension records what character classes each approach's
vendor slot accepts and how it fails when it doesn't. The
measured lexical scope of each slot is the input; whether
that scope is acceptable under P3 is a downstream question
for COMPARISON.md.

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

## Result matrix — D (split-by-concern)

D has two slots, probed independently. Identifier slot is a dict
key (A-shaped). Label slot is ApplyAPI instance + property segment
(B-shaped). Same column legend as above.

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
  no hyphen/space/dot, no leading digit). Schema class names
  that violate these rules fail at schema validation.
- A, C, and D's identifier slot (dict key under
  `assetInfo.source.<vendor>`) accepted every probed string in
  this run, including unicode and embedded special characters,
  and the recovered values matched the authored values.


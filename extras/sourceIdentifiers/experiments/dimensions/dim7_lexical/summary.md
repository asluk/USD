# Dim 7 — vendor-name lexical scope (P3 + OQ5)

Framing: PR #105 names vendor extensibility (P3) as a core principle —
vendors must be able to declare their own scheme without central
approval. The vendor *name* is the operational carrier of that vendor
identity in every approach. This dimension records what character
classes each approach's vendor slot accepts and how it fails when it
doesn't. Findings inform whether the proposed extension paradigm
imposes a soft form of central approval via naming constraints
(tensions with P3's "no central approval" stance) — captured here
as data, not verdict.

## Slot per approach

- **A** — dict_key
- **B** — apply_instance_and_property
- **Bprime** — schema_class_name
- **C** — dict_key (apply-instance also permissive; bridge unimplemented)
- **D** — split (identifier: dict_key; labels: apply_instance_and_property)

## Result matrix — A, B, B', C

Legend: ✓ = end-to-end authoring works (including round-trip);
✓ (dict) = permissive dict-key slot (runtime always succeeds);
✓ class = class-name passes Tf.IsValidIdentifier;
⚠ silent = ApplyAPI succeeds but Sdf silently re-namespaces the
vendor identity on parse;
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

- Two layers of constraint, not one: ApplyAPI/dict-key behavior is
  permissive at the runtime API; the harder constraint lives in
  `SdfAttributeSpec::New`, which enforces `Sdf.Path.IsValidNamespacedIdentifier`
  per property-name segment.
- Colons in the vendor name (`siemens:nx`) trigger silent
  re-namespacing in B and D-label: Sdf parses the property name into
  extra namespace segments, producing a different shape than what
  was authored — no error raised. This is a separable USD bug
  ([[bugs-vs-proposal-considerations]]), distinct from the
  vendor-extension-paradigm question.
- B' is the most-restrictive of the slots: schema class name must
  satisfy `Tf.IsValidIdentifier` (ASCII identifier rules — no
  unicode, no hyphen/space/dot, no leading digit). Codeless
  schemas do not relax this; the constraint sits in
  `Sdf_TextFileFormatParser` + the usdGenSchema validator, neither
  bypassed by `skipCodeGeneration`.
- A, C, D-identifier (dict-key slot) accept every probed string
  including unicode and embedded special characters. Round-trips
  byte-for-byte through `.usda`.


# Dim 4 — round-trip fidelity (P7)

Identifier *values* set on a prim, exported to `.usda` and `.usdc`,
reimported, byte-compared to the authored value. Expected trivial
pass across all approaches; kept as sanity baseline. The non-trivial
fidelity question (vendor-name *slot* lexical scope) lives in Dim 7.

## Result matrix

`✓` = recovered value matches authored value (both .usda and .usdc).
`✗` = mismatch or failure; see report.json for details.

| value | A | B | Bprime | C | D |
|---|---|---|---|---|---|
| ascii_simple | ✓ | ✓ | ✓ | ✓ | ✓ |
| slashes | ✓ | ✓ | ✓ | ✓ | ✓ |
| with_space | ✓ | ✓ | ✓ | ✓ | ✓ |
| unicode | ✓ | ✓ | ✓ | ✓ | ✓ |
| cyrillic | ✓ | ✓ | ✓ | ✓ | ✓ |
| newline_tab | ✓ | ✓ | ✓ | ✓ | ✓ |
| escaped_quote | ✓ | ✓ | ✓ | ✓ | ✓ |
| ifc_globalid | ✓ | ✓ | ✓ | ✓ | ✓ |
| colons | ✓ | ✓ | ✓ | ✓ | ✓ |
| empty | ✓ | ✓ | ✓ | ✓ | ✓ |

## Notes

- All approaches store the identifier value as a USD `string` or
  `VtDictionary` string entry. USD's string serialization preserves
  bytes including unicode, embedded newlines/tabs, and quotes.
- Mismatches, if any, point to the vendor-name *slot* (Dim 7), not
  to the value channel — but the matrix above tests value channel
  only.
- `empty` row is a degenerate case: authoring an empty string is a
  valid USD operation but indistinguishable from "unauthored" via
  the default-value retrieval path. The matrix marks the empty case
  pass if the recovered value equals `""`.

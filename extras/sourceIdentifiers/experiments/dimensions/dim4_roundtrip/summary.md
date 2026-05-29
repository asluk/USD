# Dim 4 — round-trip fidelity (P7)

Identifier *values* set on a prim, exported to `.usda` and `.usdc`,
reimported, compared to the authored value. This dim measures the
value channel; vendor-name lexical-scope behaviour is measured
separately in Dim 7.

## Result matrix

`✓` = recovered value equals authored value (both .usda and .usdc).
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
  as a string entry in a `VtDictionary`. The matrix records
  whether the recovered string equals the authored string across
  the sampled values; it does not measure byte-level guarantees
  of USD's string serialization in general.
- The matrix tests the value channel only. Vendor-name lexical
  scope is measured in Dim 7.
- `empty` row records the round-trip of an authored empty string
  (the matrix marks pass if the recovered value equals `""`).

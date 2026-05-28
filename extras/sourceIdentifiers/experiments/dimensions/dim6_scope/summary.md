# Dim 6 — scope-of-applicability (OQ4)

PR #105 Open Question 4: model roots only, or any prim? Captures
three signals per approach: schema-level `apiSchemaCanOnlyApplyTo`
restriction (if any), apply success across a range of prim types,
and approximate cost-per-prim (bytes added to the layer by one
vendor's identifier).

## Schema-level apply restriction

| approach | schema | allowed prim types |
|---|---|---|
| A | `SourceIdentifiersAPI` | (unrestricted) |
| B | `SourceIdentifierAPI` | (unrestricted) |
| Bprime | `SourceIdentifierBaseAPI` | (unrestricted) |
| Bprime | `WindchillSourceIdAPI` | (unrestricted) |
| Bprime | `IFCSourceIdAPI` | (unrestricted) |
| C | `SourceIdentifierBridgeAPI` | (unrestricted) |
| D | `SourceIdentifiersAPI` | (unrestricted) |
| D | `SemanticLabelsAPI` | (unrestricted) |

## Apply-success matrix

`✓` = apply returned True and authoring the identifier succeeded.
`✗` = apply or authoring failed; see report.json.

| prim type | A | B | Bprime | C | D |
|---|---|---|---|---|---|
| Over_typeless | ✓ | ✓ | ✓ | ✓ | ✓ |
| Scope | ✓ | ✓ | ✓ | ✓ | ✓ |
| Xform | ✓ | ✓ | ✓ | ✓ | ✓ |
| Xform_kind_component | ✓ | ✓ | ✓ | ✓ | ✓ |
| Mesh_leaf | ✓ | ✓ | ✓ | ✓ | ✓ |

## Approximate cost per prim

Bytes added to a 10-Xform `.usda` layer by applying the schema and
authoring one vendor identifier on each prim. Rough comparison;
actual size depends on identifier value length, vendor name, and
compression (`.usdc` not measured here).

| approach | empty (10 prims) | with identifier | Δ bytes | bytes/prim |
|---|---|---|---|---|
| A | 221 | 2301 | 2080 | 208.0 |
| B | 221 | 1391 | 1170 | 117.0 |
| Bprime | 221 | 1121 | 900 | 90.0 |
| C | 221 | 2451 | 2230 | 223.0 |
| D | 221 | 2301 | 2080 | 208.0 |

## Observations

- None of the five schemas declare `apiSchemaCanOnlyApplyTo` — all
  can be applied to any prim. OQ4 (model roots vs any prim) is a
  *policy* question, not a mechanism question, in every approach.
- Apply succeeds across the full prim-type range for every
  approach.
- Cost-per-prim is small in absolute terms for all approaches.
  The relative ordering depends on the identifier-data payload
  (vendor name, primaryId length) — this measurement uses a
  short ASCII vendor name and a single-character primaryId.


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

`✓` = `ApplyAPI(...)` returned True for this prim type.
`✗` = ApplyAPI returned False or errored; see report.json.

| prim type | A | B | Bprime | C | D |
|---|---|---|---|---|---|
| Over_typeless | ✓ | ✓ | ✓ | ✓ | ✓ |
| Scope | ✓ | ✓ | ✓ | ✓ | ✓ |
| Xform | ✓ | ✓ | ✓ | ✓ | ✓ |
| Xform_kind_component | ✓ | ✓ | ✓ | ✓ | ✓ |
| Mesh_leaf | ✓ | ✓ | ✓ | ✓ | ✓ |

## Approximate cost per prim

Bytes added to a 10-Xform `.usda` layer by applying the schema
and authoring one vendor identifier on each prim. Single
measurement per approach with short ASCII vendor name and a
single-character primaryId; not measured for `.usdc`.

| approach | empty (10 prims) | with identifier | Δ bytes | bytes/prim |
|---|---|---|---|---|
| A | 221 | 2301 | 2080 | 208.0 |
| B | 221 | 1391 | 1170 | 117.0 |
| Bprime | 221 | 1121 | 900 | 90.0 |
| C | 221 | 2451 | 2230 | 223.0 |
| D | 221 | 2301 | 2080 | 208.0 |

## Observations

- None of the schemas across the five approaches declare
  `apiSchemaCanOnlyApplyTo`. With the constraint absent, scope
  is decided by policy (what tooling chooses to apply where)
  rather than by schema-level enforcement.
- Apply succeeded for all tested prim types (Mesh leaf, Over
  typeless, Scope, Xform, Xform with kind=component) for every
  approach. The matrix records the tested range; broader
  applicability is not measured.
- Cost-per-prim (bytes/prim) ranges from 90 to 223 across the
  five approaches under the single payload measured (short
  ASCII vendor name, single-character primaryId). Different
  identifier-data sizes are not measured.


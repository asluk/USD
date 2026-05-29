# Source-identifier mechanism comparison

Cross-approach reading of eight empirical dimension experiments against
PR #105's principles and open questions. Criteria authority:
[`_pr105_snapshot/CRITERIA_FROM_PR105.md`](../../_pr105_snapshot/CRITERIA_FROM_PR105.md).
Cells are observations, not scores; no recommendation, no
industry-specific verdict, no new criteria beyond PR #105.

## Matrix

Rows are the eight dimensions; columns are the five candidates (A, B,
B', C, D). Cells are short empirical observations — the linked
per-dimension summary has the table, raw data, and observations behind
each cell. PR #105 principles P1 (separation of concerns), P2
(industry agnosticism), and P8 (minimal disruption) are not directly
measured by these dims and are not represented as matrix rows.

| dim | A | B | B' | C | D |
|---|---|---|---|---|---|
| [1 — composition (P4)](experiments/dimensions/dim1_composition/summary.md) | dict-merge per arc | per-attribute composition | apiSchemas listOp + shared `sourceId:primaryId` slot | dict-merge per arc | id: dict-merge; label: per-attribute |
| [2 — discoverability (P5)](experiments/dimensions/dim2_discoverability/summary.md) | via `assetInfo.source` | via apply-instance | via schema class name | via instance + assetInfo | id: via assetInfo; label: via apply-instance |
| [3 — queryability (P6 + OQ1)](experiments/dimensions/dim3_queryability/summary.md) | dict walk (14 LoC), 100% recall | property walk (16 LoC), 100% | apiSchemas walk (22 LoC), 63.9% (shared-slot on multi-vendor prims) | dict walk via A's indexer, 100% | dict walk via A's indexer, 100% (id half only) |
| [4 — round-trip (P7)](experiments/dimensions/dim4_roundtrip/summary.md) | ✓ all sampled values (`.usda` + `.usdc`) | ✓ all | ✓ all | ✓ all | ✓ all |
| [5 — distribution (P3)](experiments/dimensions/dim5_distribution/summary.md) | data only | data only | plugin + schema + data; shared base slot constrains 2-vendor coexistence | data only (bridge mechanism not surfaced in current OpenUSD; see implementation findings) | data only (both halves) |
| [6 — scope (OQ4)](experiments/dimensions/dim6_scope/summary.md) | no `apiSchemaCanOnlyApplyTo`; 208 B/prim | no restriction; 117 B/prim | no restriction; 90 B/prim | no restriction; 223 B/prim | no restriction; 208 B/prim (id half measurement) |
| [7 — vendor-name slot (P3 + OQ5)](experiments/dimensions/dim7_lexical/summary.md) | dict key — all probed strings round-trip | apply-instance + property segments — `✗ prop` on hyphen/space/dot/slash/leading-digit; `⚠ silent` on colon | schema class name — `Tf.IsValidIdentifier` gate (ASCII identifier only) | dict key (same as A) | id: dict key (A-shape); label: apply-instance (B-shape, same failures) |
| [8 — migration & compatibility (P3 + operational)](experiments/dimensions/dim8_lifecycle/summary.md) | (a, b) lexical mapping; (c→B/B') drops extra dict keys | (a, b) lexical mapping; (b) lands as custom attr; (c←A) preserves | (a) new schema + plugin registration; (b) custom attr; (c←A) preserves primaryId, drops extras | (a, b) lexical mapping; (c) target preserves dict shape | (a, b) lexical mapping both halves; carrier (c) exercised on id half only |

The patterns that emerge cluster by storage primitive (dict-valued
metadata vs typed attributes vs schema class identity), not by any
A/D-vs-B/C analytical group — the criteria file rules out such
groupings as authoritative.

## Approaches

- **A** — `assetInfo.source.<vendor>` sub-dicts + convenience applied
  schema. Vendor = dict key. PR #105.
- **B** — Multi-apply schema with typed properties. Vendor = ApplyAPI
  instance name. PR #105.
- **B'** — Single-apply base in core + per-vendor single-applies
  inheriting via `prepend apiSchemas`. Vendor = schema class name.
  PR #105 variant.
- **C** — Spiffmon's bridge (PR #105 review comment): applied schema
  declares default `assetInfo` sub-dict via `customData`. Vendor =
  dict key + instance.
- **D** — Matt Kuruc strawman; per the criteria file, D is a
  candidate beyond PR #105 ("internal NVIDIA discussion, not in
  PR #105"). Identifiers in `assetInfo` (A-style) + labels via
  `SemanticLabelsAPI:<vendor>:<labelKind>` multi-apply (B-style).
  Each half is exercised independently where a dim admits a
  label-side measurement; the criteria file flags that D's
  specifics still need to be re-grounded against rev2 source.

## Open questions not resolved here

- **OQ1** — cross-system indexing beyond a local Sdf walk
  (Dim 3 covers the local-walk case only).
- **OQ2** — dict vs applied-schema is the question the matrix
  surfaces data for; the choice itself is downstream.
- **OQ3** — stratification and governance (policy-level; not
  exercised here).
- **OQ4** — Dim 6 records that no schema declares
  `apiSchemaCanOnlyApplyTo`; the model-roots-vs-any-prim question
  is decided by policy, not measured beyond apply-success on
  five tested prim types.
- **OQ6, OQ7, OQ8** — displayName, authorship traceability,
  transcoding; named as open questions in PR #105, not exercised
  by these dims.
- Type-vs-instance scoping — flagged in PR #105 emerging consensus,
  not exercised here.

## Implementation findings (separate from design)

- **C** — `assetInfoFallback` customData does not surface in
  `UsdPrimDefinition` in current OpenUSD (Dim 2, `prim_def_assetInfo:
  null`). Not yet filed upstream as a separate issue.
- **B'** — Schema-language inheritance among single-apply API schemas
  is not directly expressible; the workaround is `prepend apiSchemas`
  on the inheriting schema (used in this experiment's schemas).
  Not yet filed upstream.

## Methodology note

This comparison reports mechanism affordances only, measured by the
eight per-dimension probes. Each dim summary was authored by the
agent that built this matrix, then audited by a separate cross-family
model (GPT-5.5 via codex) in two rounds. A prior session attempted
multi-actor simulation of approach uptake as a methodology
contribution; that attempt biased toward Approach D (per project
memory `simulation-without-bias-attempted`) and was set aside.

# Source-identifier mechanism comparison

Cross-approach reading of eight empirical dimension experiments against
PR #105's principles and open questions. Criteria authority:
[`_pr105_snapshot/CRITERIA_FROM_PR105.md`](../../_pr105_snapshot/CRITERIA_FROM_PR105.md).

Non-claims: no scoring totals, no recommendation, no industry-specific
verdict, no "TAC ratification cost" framing, no new criteria beyond
PR #105.

## Matrix

Rows are the eight dimensions; columns are the five candidate
mechanisms (A, B, B', C, D). Cells are short empirical observations —
the linked per-dimension summary has the table, raw data, and
observations behind each cell.

| dim | A | B | B' | C | D |
|---|---|---|---|---|---|
| [1 — composition (P4)](experiments/dimensions/dim1_composition/summary.md) | dict-merge per arc | per-attribute composition | apiSchemas listOp + shared `sourceId:primaryId` slot | dict-merge per arc | id: dict-merge; label: per-attribute |
| [2 — discoverability (P5)](experiments/dimensions/dim2_discoverability/summary.md) | via `assetInfo.source` | via apply-instance | via schema class name | via instance + assetInfo | id: via assetInfo; label: via apply-instance |
| [3 — queryability (P6 + OQ1)](experiments/dimensions/dim3_queryability/summary.md) | dict walk, 14 LoC, 100% recall | property walk, 16 LoC, 100% | apiSchemas walk, 22 LoC, 63.9% (shared-slot on multi-vendor) | delegates to A (1 LoC), 100% | delegates to A (1 LoC), 100% (id half only) |
| [4 — round-trip (P7)](experiments/dimensions/dim4_roundtrip/summary.md) | ✓ all sampled values (`.usda` + `.usdc`) | ✓ all | ✓ all | ✓ all | ✓ all |
| [5 — distribution (P3)](experiments/dimensions/dim5_distribution/summary.md) | data only | data only | plugin + schema + data | data only | data only (both halves) |
| [6 — scope (OQ4)](experiments/dimensions/dim6_scope/summary.md) | no `apiSchemaCanOnlyApplyTo`; 208 B/prim | no restriction; 117 B/prim | no restriction; 90 B/prim | no restriction; 223 B/prim | no restriction; 208 B/prim (id) |
| [7 — vendor-name slot (P3 + OQ5)](experiments/dimensions/dim7_lexical/summary.md) | dict key — all probed strings round-trip | apply-instance + property segments — silent re-namespacing on `:` | schema class name — `Tf.IsValidIdentifier` gate | dict key (same as A) | id: dict key (A-shape); label: apply-instance (B-shape) |
| [8 — migration & compatibility (P3 + operational)](experiments/dimensions/dim8_lifecycle/summary.md) | lexical mapping (a, b) | lexical mapping (a, b); custom-attr for (b) | (a) needs new schema + plugin; (b) custom attr | lexical mapping (a, b) | lexical mapping both halves |

Cells are observations, not scores. Patterns where they cluster
cluster by storage primitive (dict-valued metadata vs typed
attributes vs schema class identity), not by any A/D-vs-B/C-style
analytical group — the criteria file rules out such groupings as
authoritative.

## Approaches

- **A** — `assetInfo.source.<vendor>` sub-dicts + convenience applied
  schema. Vendor = dict key. PR #105.
- **B** — Multi-apply schema with typed properties. Vendor = ApplyAPI
  instance name. PR #105.
- **B'** — Single-apply base in core + per-vendor single-applies
  inheriting via `prepend apiSchemas`. Vendor = schema class name.
  PR #105 variant.
- **C** — Spiffmon's bridge: applied schema declares default
  `assetInfo` sub-dict via `customData`. Vendor = dict key + instance.
- **D** — Matt Kuruc strawman (beyond PR #105 per the criteria file).
  Identifiers in `assetInfo` (A-style) + labels via
  `SemanticLabelsAPI:<vendor>:<labelKind>` multi-apply (B-style).
  Both halves exercised where the dim admits a label-side measurement.

## Open questions not resolved here

- **OQ1** — cross-system indexing beyond a local Sdf walk
  (Dim 3 covers the local-walk case only).
- **OQ2** — dict vs applied-schema is the question the matrix surfaces
  data for; the choice itself is downstream.
- **OQ3, OQ6, OQ7, OQ8** — governance, displayName, traceability,
  transcoding (policy or cross-cutting; scoped out by the proposal).
- Type-vs-instance scoping — flagged in PR #105 emerging consensus,
  not exercised here.

## Implementation findings (separate from design)

- **C** — `assetInfoFallback` customData does not surface in
  `UsdPrimDefinition` in current OpenUSD (Dim 2, `prim_def_assetInfo:
  null`). Filed for follow-up.
- **B'** — Schema-language inheritance among single-apply API schemas
  is not directly expressible; workaround is `prepend apiSchemas`.
  Filed for follow-up.

## Methodology note

This comparison reports mechanism affordances only, measured by the
eight per-dimension probes. Each dim summary was authored by the
agent that built this matrix, then audited by a separate
cross-family model (GPT-5.5 via codex) in two rounds; audit outputs
are preserved in the session log. A prior session attempted
multi-actor simulation of approach uptake as a methodology
contribution — that attempt biased toward Approach D and was set
aside.

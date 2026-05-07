## Summary

This PR carries the source-identifier comparison work on `aluk/source-identifiers-rev2`. The canonical read is `extras/sourceIdentifiers/COMPARISON.md`; this description orients reviewers to **what's new under this PR** and **what changed structurally** rather than restating the comparison.

The proposal context: [`PixarAnimationStudios/OpenUSD-proposals#105`](https://github.com/PixarAnimationStudios/OpenUSD-proposals/pull/105) (Separation of Concerns for Identifiers) frames source identifiers as *"metadata packages, not atomic strings"* with *"different identifier fields"* per domain — a heterogeneity it asks AOUSD to weigh.

## What's new under this PR

- **Pre-registered field census** (`extras/sourceIdentifiers/details/field_classification_experiment.md`) — fields drawn from authoritative spec surfaces (IFC4x3, Revit API, AAS metamodel, Windchill REST, SAP MARA, ROS / URDF / SDF, OpenAssetIO / MovieLabs OMC / ShotGrid) under classification criteria committed before any field was enumerated. **Headline finding: identifier packages are heterogeneously typed in every vertical surveyed** — timestamps universal; numeric measures with units in three of four; composite typed references universal; polymorphic XSD-typed values the standard surface in AAS.

- **Single-mechanism leaning retracted.** The PR previously leaned toward Approach D (Labels + Identity using `UsdSemanticsLabelsAPI` + `assetInfo`); the field census surfaces typed-heterogeneity D's `token[]`-only label surface cannot carry. The comparison now reads symmetrically across A / B / C / D with no leaning asserted.

- **Vendor-adoption scoring rebuilt** (`extras/sourceIdentifiers/stress_tests/vendor_adoption_analysis.{py,json}`) against proposal 105's eight authorized design principles. Totals (max 40): **A=32, B=26, C=32, D=33** — A/C/D within scoring noise; B trails meaningfully. The earlier scoring (eight dimensions Claude invented during PR development, not derived from the proposal's principles, biased toward D by construction) is preserved as `vendor_adoption_analysis_legacy.py` for regression inspection.

- **Schema-distribution friction tension resolved** as conditional — currently elevated as the AOUSD Build IG epic ([`aousd/build-ig-initiatives#28`](https://github.com/aousd/build-ig-initiatives/issues/28)) scopes the substrate, trending lighter as those initiatives land. Reflected in the rebuilt Minimal-disruption scoring for B and C; framing details in `formality_and_distribution.md`.

## Doc reframing under this PR (changelog for reviewers)

Doc-by-doc summary of what was rewritten to remove the verdict-shaped framing:

- `COMPARISON.md` — §1 "Where the data leans" / "Where the data leans toward D's refinement over C's" deconstructed; §3.6 carries the principle-derived scoring; §3.4 industry scenarios report symmetrically across A/B/C/D
- `details/field_classification_experiment.md` — **NEW**
- `details/formality_and_distribution.md` — *"no field surfaced needing typed non-token-array structure"* assertion retracted; conditional-weighting framing on schema-distribution cost
- `details/industry_scenarios.md` — per-vertical "Approach D fit" scoped to "synthesized field set only" with explicit notes on the wider surface D doesn't cover
- `details/hybrid_analysis.md` — C is described on its own merits, not as a fallback to D
- `details/approach_descriptions.md` — D's section is descriptive, not conclusory; provenance noted (constructed downstream of the proposal, included as an explored idea)
- `details/stress_tests.md` §5.3 — vendor-adoption scoring rebuilt; concrete history note
- `details/governance.md` §6.7 — conditional-weighting framing per Aaron's distribution-friction call; §6.8 honest about what D collapses (classification axis only) and what it doesn't (the heterogeneity surface)
- `details/scope_promotion_simulation.md` — scope note rebalanced (controlled-vocabulary fields can ride D; heterogeneously typed fields need C's path)
- `details/agentic-development.md` — header note added clarifying it's an April-2026 retrospective from before the rebuild

## Methodology retrospective

The journey — from leaning-toward-D through empirical census to principle-derived rebuild — and the methodology lessons that may travel beyond this work are captured as a [PR comment](https://github.com/asluk/USD/pull/7#issuecomment-4399081816). Talk-prep material rather than gating reading; the body and `COMPARISON.md` reflect the current state.

## Test plan

- [x] `examples/verify_column_d.py` — verifies `column_d.usda` parses against built USD with `UsdSemantics.LabelsAPI` (0 failures)
- [x] `stress_tests/generate_approach_{a,b,c,d}.py` — 100K-prim deterministic generators; reproducible
- [x] `stress_tests/vendor_adoption_analysis.py` — principle-derived scoring reproducible across A/B/C/D
- [x] `details/field_classification_experiment.md` — pre-registered classification criteria committed before field enumeration; cross-vertical bucket totals reproducible from the cited spec sections

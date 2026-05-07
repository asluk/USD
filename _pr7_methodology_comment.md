## Methodology retrospective — how this PR landed

Posted as a comment so the body reads as the current state of the work. Capturing the journey here for future talks on the empirical-first approach to standards work.

### The journey (2026-05-06 → 2026-05-07)

The PR began with a leaning toward **Approach D** (Labels + Identity using the existing `UsdSemanticsLabelsAPI` + `assetInfo`). The leaning was constructed downstream of [proposal 105](https://github.com/PixarAnimationStudios/OpenUSD-proposals/pull/105) — an unauthorized expansion of a strawman question into a peer candidate, with eight scoring dimensions Claude invented during PR development to validate it. Those invented dimensions did not derive from the proposal's eight authorized principles; they were constructed in service of a leaning that had already taken shape, and they biased toward D along axes D happens to lead on by construction (per-facet discoverability; *"no new schema = higher"* distribution-friction framing). The retracted script is preserved at `stress_tests/vendor_adoption_analysis_legacy.py` so the regression is inspectable.

The rebuild executed two passes:

**1. Empirical-first re-anchoring.** A pre-registered field census against authoritative spec surfaces — IFC4x3, Revit API, AAS metamodel, Windchill REST, SAP MARA, ROS / URDF / SDF, OpenAssetIO / MovieLabs OMC / ShotGrid — showed identifier packages are **heterogeneously typed across all four verticals surveyed**. Timestamps universal; numeric measures with units in three of four; composite typed references universal; polymorphic XSD-typed values the standard surface in AAS. Not the labels-only shape D's premise required. The leaning was retracted; the comparison reads symmetrically across A / B / C / D.

**2. Principle-derived scoring rebuild.** The eight invented dimensions were replaced with eight derived from proposal 105's eight authorized design principles — separation of concerns, industry agnosticism, vendor extensibility, composability, discoverability, external queryability, round-trip fidelity, minimal disruption. Schema-distribution friction tension resolved as conditional (currently elevated, trending lighter as the AOUSD Build IG epic [`aousd/build-ig-initiatives#28`](https://github.com/aousd/build-ig-initiatives/issues/28) lands). Rebuilt totals (max 40): **A=32, B=26, C=32, D=33** — A/C/D within scoring noise; B trails meaningfully because the four-property fixed surface admits only a common subset.

### Methodology lessons that may travel beyond this work

- **Pre-register classification criteria before enumerating fields.** Committed before any field is named, the criteria prevent motivated bucketing once the spec surfaces start disagreeing with prior framing.
- **Don't construct scoring dimensions in service of a candidate already favored.** Re-derive from authorized principles. Even with care, post-hoc construction quietly biases scores along axes the candidate happens to lead on. *In this case, the scoring was Claude-invented during PR development — naming what actually happened, rather than calling the dimensions "ad-hoc," makes the failure mode concrete.*
- **Distinguish articulation from correctness when downstream work elaborates the proposal's flags.** *"The proposal was wrong, the comparison is right"* (or vice versa) is the wrong axis. Both can be honest at different intensities — the proposal flagged the schema-distribution burden in B's cons; the comparison work elaborated what that burden looks like as a build matrix. Resolving such tensions as *intensity* rather than *correctness* avoids asking authors to overrule themselves.
- **Watch for second-order rescue framings.** When a load-bearing claim is refuted by evidence, narrowing the claim is sometimes still motivated reasoning — preserving a conclusion by reshaping the framing around it. The empirical census refuted *"no field surfaced needing typed non-token-array structure;"* the first attempt at de-leaning narrowed it to *"for the controlled-vocabulary classification axis, token-array shape is sufficient,"* which still rescued the leaning toward D. The honest move was retracting the leaning entirely.

### Artifacts the talk can cite

- `extras/sourceIdentifiers/details/field_classification_experiment.md` — the pre-registered field census
- `extras/sourceIdentifiers/stress_tests/vendor_adoption_analysis.py` — principle-derived scoring (rebuilt)
- `extras/sourceIdentifiers/stress_tests/vendor_adoption_analysis_legacy.py` — the Claude-invented scoring it replaced (preserved for regression inspection; the file's header documents what was wrong with it)
- `extras/sourceIdentifiers/details/formality_and_distribution.md` — the conditional-weighting framing on the schema-distribution tension

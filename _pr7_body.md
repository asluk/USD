> ## Caveats for readers (including agents)
>
> Two specific items in this PR are **deferred to a follow-up session**
> per the rebuild plan, and both are **load-bearing for any conclusion
> drawn from the materials**. Future readers should not treat the
> following as settled:
>
> 1. **The eight-dimension vendor-adoption scoring** in
>    `stress_tests/vendor_adoption_analysis.{py,json}` and reproduced in
>    `COMPARISON.md` §3.6 / `stress_tests.md` §5.3 was constructed
>    *after* a prior leaning toward Approach D had already taken shape.
>    It has not been re-derived from the proposal's eight authorized
>    principles (separation of concerns, industry agnosticism, vendor
>    extensibility, composability, discoverability, external
>    queryability, round-trip fidelity, minimal disruption) and explicit
>    risks (uncurated proliferation, premature standardization, adoption
>    fragmentation, scope creep). The scores are preserved as
>    illustrative of per-mechanism contrasts the experiments surfaced;
>    they should not be read as an independent verdict.
> 2. **The distribution-friction tension is unresolved.** The comparison
>    materials elevate schema distribution to *the dominant cost* of
>    ratifying a new applied schema (`formality_and_distribution.md`).
>    Proposal #105's original B-cons phrasing downplays it (*"tools
>    already ship their own domain plugins and unrecognized schema data
>    roundtrips without loss"*). These two framings are at variance.
>    Resolution requires Aaron's call and is upstream of any honest
>    scoring or mechanism choice.
>
> A prior framing of this PR leaned toward Approach D (Labels +
> Identity using `UsdSemanticsLabelsAPI` + `assetInfo`). **That leaning
> has been retracted** in light of the field census documented in
> `details/field_classification_experiment.md`, which shows identifier
> packages are heterogeneously typed across all four verticals
> surveyed. The current PR is candidate-comparison + empirical census,
> not a leaning toward any specific mechanism.
>
> Memory note for agent readers: the rebuild plan tracking these
> deferrals is in `project_source_identifier_rebuild.md`.

---

## Summary

The source-identifier proposal ([`PixarAnimationStudios/OpenUSD-proposals#105`](https://github.com/PixarAnimationStudios/OpenUSD-proposals/pull/105)) calls for a shared mechanism to carry external source identifiers — IFC GlobalIds, Revit ElementIds, Windchill OIDs, ROS frame IDs — that travel with USD prims. Current practice is unscoped `customData`: fragmented per vendor, no shared discovery story.

The proposal frames source identifiers as *"metadata packages, not atomic strings,"* with *"different identifier fields"* per domain — a heterogeneity it asks AOUSD to weigh: *"the more heterogeneous the contents, the more this tension favors dictionaries or a family of domain-specific schemas"* (B's cons, ¶1).

This PR runs an empirical census against that question: **are the identifier packages real source systems bundle with their identifiers heterogeneously typed in the proposal's sense?** The census (`extras/sourceIdentifiers/details/field_classification_experiment.md`) draws fields from authoritative spec surfaces — IFC4x3, Revit API, AAS metamodel, Windchill REST, SAP MARA, ROS/URDF/SDF, OpenAssetIO, MovieLabs OMC, ShotGrid — under pre-registered classification criteria committed before any field was enumerated.

### What the census shows

Identifier packages are heterogeneously typed in every vertical surveyed:

- **Timestamps** are universal (IFC `IfcTimeStamp`, Windchill `Edm.DateTimeOffset`, SAP `DATS`, ROS `Header.stamp`, ShotGrid `created_at`/`updated_at`, OMC `lifecycleEvents`).
- **Numeric measures with units** are present in AECO (`IfcMeasureValue` family), PLM (SAP `QUAN(13,3)` for `NTGEW`/`BRGEW`/`VOLUM`), and Robotics (URDF/SDF mass, inertia, joint limits, dynamics).
- **Composite typed references** are universal (IFC `IfcPersonAndOrganization`/`IfcApplication`, AAS `Reference`/`RelationshipElement`, Revit `ElementId`-typed relations, ShotGrid entity-link fields).
- **Polymorphic XSD-typed values** are the *standard surface* in AAS (`Property.value` across `xs:string`/`xs:int`/`xs:long`/`xs:decimal`/`xs:double`/`xs:float`/`xs:boolean`/`xs:date`/`xs:dateTime`/`xs:duration`/`xs:anyURI`/`xs:base64Binary`).

| Vertical | Identity | Identity-adjacent | Controlled-vocabulary classification | **Heterogeneous typed fields** |
|---|---|---|---|---|
| AECO (12 main + 6 OwnerHistory) | 3 | 4 | 9 | 6 |
| Manufacturing/PLM (33) | 4 | 5 | 9 | 15+ |
| Robotics — strict (11) | 4 | 3 | 2 | 2 |
| Robotics — expanded URDF (15) | 2 | 0 | 1 | 12 |
| M&E (16) | 3 | 2 | 6 | 6 |

### What this means for the four candidates compared in this PR

| Mechanism | Carries heterogeneous typed fields? |
|---|---|
| **A — `assetInfo` dictionaries** | Yes — freeform dicts admit any typed shape (subject to USD's value-type set), at the cost of no schema-side typing or discoverability. |
| **B — Multi-apply schema, four common typed properties** | No — the four-property surface cannot carry domain-specific typed fields without companion schemas per domain. |
| **C — Refinement of B (B + `assetInfo` overflow)** | Yes — typed schema for the common fields, freeform-dict overflow for everything heterogeneous. |
| **D — Refinement of B (`UsdSemanticsLabelsAPI` + `assetInfo` identity strings)** | No — labels carry `token[]` and identifier strings; numeric, date, composite-reference, and polymorphic typed shapes have no slot. |

The empirical heterogeneity surface is consistent with **A and C**. It is not consistent with **D or B-alone** as complete answers. D's premise — that source-identifier metadata reduces to (identifier strings + classification facets) — depends on a scope-narrowing that excludes the heterogeneous typed surface real source systems bundle. The current materials don't make that scope-narrowing argument; they assumed it. Once the experiment surfaces the typed heterogeneity, the previous *"data leans toward D"* framing isn't earned.

### What this PR's previous framing claimed, and what changed

The previous PR body and several of the comparison docs (`COMPARISON.md` §1, `formality_and_distribution.md`, `industry_scenarios.md`'s "Approach D fit" sections, `hybrid_analysis.md`) leaned toward **D — Labels + Identity** based on the assertion that *"no domain-specific field surfaced that required typed non-token-array structure"* across the four verticals. The field census does not support that assertion as written: heterogeneous typed fields surface in every vertical.

Updated under this PR to remove the verdict-shaped framing and report the candidates symmetrically:

- `details/field_classification_experiment.md` — **NEW.** Pre-registered field census; cross-vertical bucket totals; honest report that the previous claim does not hold against the spec surfaces.
- `COMPARISON.md` — §1 "Where the data leans" / §3.6 vendor-adoption-scoring / "Where the data leans toward D's refinement over C's" sections deconstructed; comparison reads symmetrically across A/B/C/D.
- `details/formality_and_distribution.md` — reframed as a tradeoff catalog without the "leaning toward D" verdict; the recurring-distribution-cost framing is preserved as one side of a tradeoff, not a finding.
- `details/industry_scenarios.md` — "Approach D fit" verdict per vertical removed; per-vertical findings reported symmetrically.
- `details/hybrid_analysis.md` — C is no longer framed as "the natural fallback if D doesn't fit"; it's described on its own merits.
- `details/approach_descriptions.md` — D's section is descriptive, not conclusory; provenance noted (D was constructed downstream of the proposal's authorized A/B/C; it is included as an explored idea, not a peer candidate the proposal authorized).
- `details/stress_tests.md` §5.3 vendor-adoption scoring carries an explicit caveat that the eight dimensions were constructed after the leaning toward D had taken shape and have not yet been re-derived from the proposal's eight authorized principles.

### Mechanisms — symmetric description

Four mechanisms were exercised through the same battery of experiments. All preserve round-trip fidelity for opaque identifier strings; they differ in where the identifier sits, how surrounding metadata is carried, and what new infrastructure (if any) they require.

- **A — `assetInfo` dictionaries.** Identifiers and any surrounding metadata nested under `assetInfo["sourceIds"]`. Status quo, refined. Authorized in the proposal as Approach A.
- **B — Multi-apply schema with typed properties.** Each external system is one schema instance carrying typed `primaryId`, `revision`, `domain`, `label`. Domain-specific metadata requires companion schemas. Authorized in the proposal as Approach B.
- **C — Refinement of B.** Same multi-apply schema, plus `assetInfo` overflow for fields the four common properties can't carry. Closes B's heterogeneity gap by carrying both mechanisms. Hinted at in the proposal as a "hybrid or alternative."
- **D — Refinement of B (Labels + Identity).** Reuses `UsdSemanticsLabelsAPI` for classification facets and routes identifier strings to `assetInfo`. **No new applied schema.** Constructed downstream of the proposal during the comparison work; included as an explored idea.

A and B are the two foundations the proposal authorized. C and D are different cuts at B's gap on heterogeneity.

### Existing artifacts (preserved)

| Path | What it is |
|---|---|
| `examples/{approach_a,approach_b,approach_c,column_d}.usda` | One-prim AECO scenarios |
| `examples/manufacturing_{a,b,d}.usda` | Tractor-assembly scenario |
| `examples/robotics_{a,b,d}.usda` | Warehouse-fleet scenario |
| `examples/verify_column_d.py` | Schema-aware verifier for `column_d.usda` |
| `vendor_simulation/approach_*_vendors.usda` | 8-vendor ecosystem simulations |
| `stress_tests/generate_approach_*.py`, `stress_test_results.json` | Deterministic 100K-prim generators + measurements |
| `stress_tests/vendor_adoption_analysis.{py,json}` | Eight-dimension scoring (carries caveat) |
| `details/field_classification_experiment.md` | **NEW** — pre-registered field census |

## Empirical measurements

100K-prim stress test, deterministic seed (`stress_test_results.json`):

|  | A | B | C | D |
|---|---|---|---|---|
| File size (`.usda`) | 109.38 MB | 93.09 MB | 147.06 MB | 115.82 MB |
| Line count | 3,085,417 | 2,020,995 | 3,583,150 | 3,094,533 |
| Namespace | 10 keys | 30 props | 30 props + 9 keys | 11 apiSchema instances + 11 label props + 9 keys |

These measurements describe the per-mechanism encoding cost; they do not, on their own, pick a mechanism.

### Vendor adoption scoring (caveat)

`stress_tests/vendor_adoption_analysis.{py,json}` produces eight-dimension scores: A=29, B=27, C=29, D=36. The eight dimensions were constructed after the leaning toward D had already taken shape and have not yet been re-derived from the proposal's eight authorized principles (separation of concerns, industry agnosticism, vendor extensibility, composability, discoverability, external queryability, round-trip fidelity, minimal disruption) and explicit risks. The current scores should therefore be read as illustrative of per-mechanism contrasts, not as an independent verdict. A re-derivation is part of the rebuild plan and is deferred to a session that can also address the distribution-friction tension flagged there.

## Schema-aware verification

`examples/verify_column_d.py` opens `column_d.usda` against a built USD and confirms it parses and applies `UsdSemantics.LabelsAPI` correctly:

```
Stage opened: examples/column_d.usda
Prim /Column_C14: type=Mesh valid=True
Applied schemas: 10
SemanticsLabelsAPI per (system, facet): 10 OK / 0 FAIL
assetInfo["source"][<system>]: 4 OK / 0 FAIL
FAILURES: 0
```

This verification confirms the encoding mechanics of D for the canonical AECO column; it does not bear on whether D is the right mechanism.

## Status of this work

These findings inform a follow-up proposal. They do not back-edit [`PixarAnimationStudios/OpenUSD-proposals#105`](https://github.com/PixarAnimationStudios/OpenUSD-proposals/pull/105). The empirical-first methodology — running each candidate through the same battery of reproducible tests and committing classification criteria up front — is itself a contribution this work intends to carry forward to other standards decisions.

## Open questions for AOUSD review

- **Where the identifier-package boundary sits.** The field experiment shows heterogeneous typed fields (timestamps, numeric measures with units, composite refs, polymorphic AAS Properties) surfacing in every vertical surveyed. Whether those fields are *part of* source-identifier metadata or are the asset's *content* (out of scope for this mechanism) is the load-bearing scope question. The current materials don't argue this scope-narrowing; they assumed it.
- **Mechanism choice between A and C.** Both accommodate the empirical heterogeneity. The structure-vs-freeform tradeoff between them is downstream of this experiment; B-with-companion-schemas remains a third possibility the proposal authorized.
- **Distribution-and-maintenance cost.** A new applied schema commits the AOUSD ecosystem to a recurring distribution-and-maintenance load coordinated by the [AOUSD Build Interest Group](https://github.com/aousd/build-ig-initiatives). The proposal's original B-cons phrasing (*"tools already ship their own domain plugins and unrecognized schema data roundtrips without loss"*) is at variance with the comparison docs' elevation of distribution to the dominant cost. Resolution is load-bearing for any mechanism choice that requires schema ratification.
- **Borderline fields.** `displayNumber`, `mark`, `tag`-style strings — identifier-adjacent or controlled-vocabulary classification? Worth pressure-testing in AOUSD review against AOUSD members' source systems.
- **`apiSchemas` list scaling.** Mechanisms that put per-facet or per-system instances on `apiSchemas` (D, and B/C in different ways) inherit the linear-sift cost the physics workflows already feel. A cached per-kind index would benefit them; lacking one, consumers should expect linear scans.

## Test plan

- [x] `examples/verify_column_d.py` — verifies `column_d.usda` parses against built USD with `UsdSemantics.LabelsAPI` (0 failures).
- [x] `stress_tests/generate_approach_{a,b,c,d}.py` — 100K-prim deterministic generators; reproducible.
- [x] `stress_tests/vendor_adoption_analysis.py` — scoring reproducible across A/B/C/D (subject to the dimensional-rebuild caveat above).
- [x] `details/field_classification_experiment.md` — pre-registered field census across the four verticals' authoritative specs; classification criteria and field-source rules committed before enumeration; cross-vertical bucket totals reproducible from the cited spec sections.

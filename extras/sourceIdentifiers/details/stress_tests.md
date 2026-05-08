# Ecosystem Simulation & Stress Tests

← [Back to COMPARISON.md](../COMPARISON.md)

## 5.1 Multi-vendor simulation

**Files:** `vendor_simulation/approach_a_vendors.usda`,
`vendor_simulation/approach_b_vendors.usda`,
`vendor_simulation/approach_c_vendors.usda`,
`vendor_simulation/approach_d_vendors.usda`

Eight vendors and standards bodies were simulated adding their own
identifier schemes to a single turbine blade prim:

| # | Organization | Domain | Identifier Example |
|---|-------------|--------|-------------------|
| 1 | NVIDIA | Omniverse Nucleus | `omniverse://nucleus.nvidia.com/assets/turbine/blade_v3` |
| 2 | Adobe | Substance 3D | `urn:adobe:sub3d:a1b2c3d4-e5f6-7890-abcd-ef1234567890` (illustrative) |
| 3 | Apple | Reality Composer Pro | `com.apple.realitykit.asset.TB-001` (illustrative) |
| 4 | SideFX | Houdini Digital Asset | `SideFX::turbine_blade::3.0` |
| 5 | Autodesk | Fusion 360 | `urn:adsk.wipprod:dm.lineage:7Rf2wvPxSEeHmBq-XqFD_g` |
| 6 | buildingSMART | IFC | `2O2Fr$t4X7Zf8NOew3FL02` |
| 7 | ASHRAE | Standard 205 (HVAC performance data) | `ASHRAE205:RS0004:CompressorSystem` |
| 8 | ISO | STEP | `STEP-FILE-ID:#4782` |

**Vendor adoption friction:**

- **Approach A:** Each vendor writes `assetInfo["sourceIds"]["<key>"]`
  with whatever structure they want. Zero files touched in the OpenUSD
  codebase. Zero coordination required. A vendor can ship support in a
  single afternoon.

- **Approach B:** Each vendor applies `SourceIdSchemaAPI:<name>` and
  authors four properties. Also zero files touched if the common
  properties suffice — but `SourceIdSchemaAPI` itself must be ratified
  and shipped first. If the vendor needs domain-specific fields
  (6 of 8 simulated vendors do), they must either register a companion
  schema or use custom attributes — adding friction.

- **Approach C:** Same as B for the schema-distribution overhead, plus
  the vendor authors `assetInfo` overflow for domain-specific fields.

- **Approach D:** Each vendor authors `assetInfo["source"][<system>]` for
  identity strings, applies `SemanticsLabelsAPI:<system>:<facet>` per
  classification facet, and authors the corresponding `token[]` properties.
  No new applied schema needs to ship — `UsdSemanticsLabelsAPI` is in
  OpenUSD core (24.11+). Zero codebase changes; the only coordination is
  reserving a system key in the AOUSD Domains Registry.

**Collision scenario.** Collision detection is symmetric across all four
mechanisms: none of them enforce uniqueness on their own; a registry-spec
validator must check authored content against the AOUSD Domains Registry
under any approach. What differs is *where* the validator looks:

- **A:** validator iterates `assetInfo["sourceIds"]` keys per prim and
  checks each against the registry.
- **B/C:** validator iterates the `apiSchemas` list, checks instance prefix
  against the registry, and reads the `domain` token for secondary
  disambiguation.
- **D:** validator does both A's work (iterate `assetInfo["source"]` keys
  per prim and check each against the registry) and per-facet
  apiSchema-instance work (iterate the `apiSchemas` list and check both
  system prefix (`revit`) and facet suffix (`familyType`) against the
  registry). D = A's mechanism + `UsdSemanticsLabelsAPI` for classification
  facets, so the validator covers both surfaces; the apiSchema-instance
  surface gives easier per-facet checks for the classification slice on
  top of A's `assetInfo`-walking work.

In all four cases, two vendors who both pick `"tracker"` produce a silent
collision until the registry catches it. The mechanism does not prevent the
collision; the registry process does.

**Promotion lifecycle:**

- **Approach A:** Promoting `"nvidia_simready"` to `"simready"` (multi-vendor
  tier) requires renaming dictionary keys in all existing content. Tools
  querying by key must be updated.

- **Approach B/C:** Promotion can update the `domain` token value
  (`"com.nvidia.simready"` → `"org.aousd.simready"`) while keeping the
  instance name. Schema versioning tracks the migration if the instance
  name also changes.

- **Approach D:** Promotion is the same shape as A — rename the system
  key in `assetInfo` and the apiSchema instance prefix together. There is
  no schema property to migrate (D has no typed `domain` token), so
  promotion is a single rename. Optionally, a registry-level alias maps
  the old name to the new for transition.

## 5.2 Stress test: 100,000 prims

**Generators:**
- `stress_tests/generate_large_stage.py` — A and B (deterministic, `random.seed(42)`)
- `stress_tests/generate_approach_c.py` — C
- `stress_tests/generate_approach_d.py` — D

Regenerate with `python3 generate_large_stage.py && python3 generate_approach_c.py && python3 generate_approach_d.py`.

**Configuration:** 100,000 prims, each with 1–5 randomly assigned domains
from the 8-vendor pool. For A/B/C, every domain carries 0–2 metadata fields.
For D, each domain's metadata is split into label facets
(`SemanticsLabelsAPI:<system>:<facet>`) and identity-adjacent strings (in
`assetInfo["source"][<system>]`).

### File size and verbosity (real measurements from `stress_test_results.json`)

| Metric | A | B | C | D |
|--------|---|---|---|---|
| File size (`.usda`) | 109.38 MB | 93.09 MB | 147.06 MB | 115.82 MB |
| Line count | 3,085,417 | 2,020,995 | 3,583,150 | 3,094,533 |
| Generation time | 7.71 s | 2.87 s | 8.78 s | 6.23 s |

### Estimated binary (`usdc`) sizes

The stress test generates `.usda` text files. Production USD pipelines
typically use the Crate binary format (`.usdc`), which compresses
significantly (3–5× smaller for attribute-heavy data, per published
Crate compression characteristics).

| | A (`.usda`) | B (`.usda`) | C (`.usda`) | D (`.usda`) |
|---|---|---|---|---|
| Measured | 109.4 MB | 93.1 MB | 147.1 MB | 115.8 MB |
| Est. `.usdc` | ~25–35 MB | ~22–31 MB | ~34–48 MB | ~28–37 MB |

**Note:** `.usdc` numbers are estimates; actual Crate sizes depend on
string deduplication (which favors B's repeated property names and D's
repeated facet names) and dictionary encoding overhead. Measured values
are welcome contributions.

The relative ordering B < A < D < C is likely preserved in binary, with
absolute differences narrowing substantially.

**Analysis:**

1. **B is smallest** because of the flat property namespace and no
   nesting overhead. Property names compress well in `.usdc` due to
   string deduplication.

2. **A and D are within 6% of each other** because both carry an
   `assetInfo` identity dict per system. D's additional `apiSchemas`
   instances and `token[]` label properties roughly offset A's
   metadata sub-dicts.

3. **C is largest** because it carries both the schema properties (B's
   overhead) and the `assetInfo` overflow (A's overhead) for the same
   metadata content.

4. **Generation time differences** reflect Python string-formatting
   overhead for nested syntax vs. flat property authoring, not meaningful
   runtime performance signals for downstream tools.

### Namespace footprint

| Metric | A | B | C | D |
|--------|---|---|---|---|
| Unique names in stage | 10 dict keys | 30 property names | 30 props + 9 dict keys | 11 apiSchema instances + 11 label props + 9 dict keys |
| Per-domain footprint | 1 dict key | 4 properties | 4 props + 1 key | (label facets × 1 instance + 1 token prop) + 1 identity dict key |

**Analysis:** A is most compact per domain. B explodes each domain into
4 properties. C carries both. D's per-facet granularity gives the most
*structurally addressable* surface — a consumer can filter `apiSchemas`
on `revit:` to see all Revit-related facets without parsing — but at the
cost of more namespace entries than A.

### Discovery performance (text search)

| Metric | A | B |
|--------|---|---|
| Full-stage text scan | 0.638 s | 0.590 s |

Both require a full scan for reverse lookups ("which prims have this
identifier?"). C and D were not separately measured — both would be in
the same regime. In production, all four benefit from external indexing;
the mechanism must make building such indexes tractable, which all four
do (A and C-overflow and D-identity via dictionary key iteration; B and
C-schema and D-labels via property name pattern matching or `apiSchemas`
list filtering).

## 5.3 Principle-derived scoring

**Methodology.** Scoring dimensions are derived from proposal 105's
eight authorized design principles (separation of concerns, industry
agnosticism, vendor extensibility, composability, discoverability,
external queryability, round-trip fidelity, minimal disruption). Each
per-dimension question rubric is anchored to its principle's literal
text without broadening; each per-mechanism score is derived from
primitive-level inspection of that candidate's mechanism (schema
definitions, example files, AOUSD Core Spec primitives, the field
census). Implementation-level concerns (schema-ratification cost,
schema-distribution cost, spec-text-formalization track record,
per-vertical conditionality) are surfaced separately in the script's
`IMPLEMENTATION_CONSIDERATIONS` block — not baked into principle-
derived scores. Full anchors, justifications, and implementation
notes are in `stress_tests/vendor_adoption_analysis.json`.

> **Earlier scoring retracted.** Previous versions of this section
> carried interpretive broadenings of several principle texts
> (notably Minimal disruption, broadened to include schema
> ratification and plugin distribution) and incomplete primitive-
> grounding of the per-mechanism rationales. Those are retracted in
> this revision; the earlier eight-dimension snapshot is preserved
> as `stress_tests/vendor_adoption_analysis_legacy.py` for
> regression inspection. The current dimensions derive from the
> proposal's authorized principles, narrowed to the principles'
> literal text.

| Dimension (principle) | A | B | C | D |
|-----------|---|---|---|---|
| Separation of concerns | 5 | 5 | 5 | 5 |
| Industry agnosticism | 5 | 3 | 5 | 5 |
| Vendor extensibility | 5 | 2 | 4 | 5 |
| Composability | 5 | 5 | 5 | 5 |
| Discoverability | 3 | 4 | 4 | 4 |
| External queryability | 3 | 5 | 4 | 4 |
| Round-trip fidelity | 5 | 5 | 5 | 5 |
| Minimal disruption | 5 | 5 | 5 | 5 |
| **Total (max 40)** | **36** | **34** | **37** | **38** |

**Source:** `stress_tests/vendor_adoption_analysis.{py,json}`
(re-runnable via `python3 vendor_adoption_analysis.py`).

**How to read these.** Four of the eight principles produce check-pass
scores across all four candidates at the literal-text reading
(Separation of concerns, Composability, Round-trip fidelity, Minimal
disruption). The differentiating dimensions are Industry agnosticism,
Vendor extensibility, Discoverability, and External queryability.
The four candidates cluster within a 4-point spread (B=34, A=36,
C=37, D=38). Each candidate's profile:

- **A** leads on industry agnosticism (full `assetInfo` value-type set
  carries any package shape) and vendor extensibility (ship today via
  dict overflow, no AOUSD-level approval at the data-model level).
  Trails on discoverability (parse-based on the standardized
  `sourceIds` key — not pipeline-specific, but parse-based) and
  external queryability (full-stage parse).
- **B** leads on external queryability (schema-targeted across the
  full surface — B has no overflow tier). Trails on industry
  agnosticism (the four typed common properties admit only a fixed
  subset; the heterogeneous typed surface from the field census
  requires per-domain companion schemas) and vendor extensibility
  (schema must be ratified at the AOUSD level before any vendor can
  adopt the mechanism).
- **C** combines B's typed common-fields tier with A's `assetInfo`
  overflow tier. Industry agnosticism = A; vendor extensibility = 4
  (ship today via overflow as fallback; canonical typed tier requires
  schema ratification). Mixed surface on discoverability and external
  queryability (schema-targeted for typed; parse-based for overflow).
- **D** uses existing `UsdSemanticsLabelsAPI` for classification
  facets + `assetInfo["source"]` overflow for identity / heterogeneous
  typed (same overflow tier as A). Industry agnosticism = A; vendor
  extensibility = A (ship today, spec-text formalization path); per-
  (system, facet) signal in `apiSchemas` for the classification slice.

**Implementation-level considerations** (surfaced separately in
`vendor_adoption_analysis.json` `IMPLEMENTATION_CONSIDERATIONS`,
*not* baked into principle-derived scores per PR 105 #3, which
distinguishes vendor extensions at the data-model level from runtime
plugin implementation):

- **Schema-ratification cost** affects B and C: each introduces a new
  applied schema that must be ratified at the AOUSD level. A and D
  introduce no new schema (A's wrapper is non-applied convenience
  over an existing core metadata field; D uses existing
  `UsdSemanticsLabelsAPI` + existing `assetInfo`).
- **Schema-distribution cost** affects B and C: ratified schemas must
  be distributed across the matrix the AOUSD Build Interest Group is
  scoping (DCC × USD release × Python × OS × runtime × build flavor).
  Per Aaron Luk's 2026-05-07 call, this is elevated currently — the
  Build IG epic ([`aousd/build-ig-initiatives#28`](https://github.com/aousd/build-ig-initiatives/issues/28))
  is scoping the substrate (hosted binaries, plugin registration via
  importlib, conda-forge / PyPI distribution); the cost is expected
  to lighten as those initiatives land. A and D require no new
  plugin distribution.
- **Spec-text-formalization track record** affects A and D: their
  promotion path (AOUSD spec text formalizing dict-key conventions /
  Labels facet vocabulary) is a valid AOUSD-level lifecycle vehicle
  but newer in AOUSD practice than schema ratification.
- **Per-vertical conditionality of D's classification advantage**: D's
  per-(system, facet) discoverability scales with classification
  richness — meaningful in AECO (7-9 facets per asset), thin in
  PLM/Robotics/M&E.

The trajectory of the schema-distribution cost as the Build IG
initiatives land is detailed in
[`formality_and_distribution.md`](formality_and_distribution.md).

**Caveat preserved.** Numerical totals are illustrative of how the
mechanisms trade off across principles, not a verdict. Different
principle weights would produce different totals. The published 1–5
anchors, per-mechanism justifications, and implementation
considerations are the primary reading.

## 5.4 Three-tier model for Approach C

If C is adopted, the three-tier graduation path (core schema + codeless
companion schemas + overflow dicts) keeps `assetInfo` overflow as the
zero-friction onramp for experimental fields, lets stable fields graduate
to codeless companion schemas (~80 lines, no C++) for typed access and
GUI discoverability, and reserves the core schema for fields that prove
universal across domains. This is the adoption profile the C
implementation in `pxr/usd/usdSourceIdHybrid/` supports; it does not
change the §5.3 ranking but tightens C's promotion-lifecycle and
discoverability profile relative to a pure-overflow C.

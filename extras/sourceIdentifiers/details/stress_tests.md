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
- **D:** validator iterates the `apiSchemas` list and checks both system
  prefix (`revit`) and facet suffix (`familyType`) against the registry —
  arguably the easiest validator to implement.

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
dimension carries a published 1–5 anchor and a per-mechanism
justification grounded in evidence from the field census, stress
tests, and composition experiments. Full anchors and justifications
are in `stress_tests/vendor_adoption_analysis.json`; the script
re-derives the scores from the published rubric.

> **Earlier scoring retracted.** Previous versions of this section —
> spanning both the original April-2026 A/B/C scoring on the
> `aluk/source-identifiers-comparison` base branch and the
> D-augmented version on `aluk/source-identifiers-rev2` — presented
> eight ad-hoc dimensions Claude invented across the comparison work.
> Those dimensions did not derive from proposal 105's authorized
> principles; the D-augmented version was constructed in service of a
> leaning toward Approach D that had already taken shape and biased
> toward D along axes D happens to lead on by construction (per-facet
> discoverability; "no new schema = higher" distribution-friction
> framing). The D-augmented snapshot is preserved as
> `stress_tests/vendor_adoption_analysis_legacy.py` so the regression
> from it is inspectable; the earlier April-2026 ad-hoc version is
> reachable via git history. The dimensions below derive from the
> proposal's authorized principles.

| Dimension (principle) | A | B | C | D |
|-----------|---|---|---|---|
| Separation of concerns | 3 | 3 | 4 | 3 |
| Industry agnosticism | 5 | 2 | 5 | 3 |
| Vendor extensibility | 5 | 2 | 4 | 5 |
| Composability | 4 | 4 | 4 | 4 |
| Discoverability | 2 | 4 | 4 | 5 |
| External queryability | 3 | 4 | 4 | 4 |
| Round-trip fidelity | 5 | 5 | 5 | 5 |
| Minimal disruption | 5 | 2 | 2 | 4 |
| **Total (max 40)** | **32** | **26** | **32** | **33** |

**Source:** `stress_tests/vendor_adoption_analysis.{py,json}`
(re-runnable via `python3 vendor_adoption_analysis.py`).

**How to read these.** A, C, and D are within scoring noise (3-point
spread). B trails meaningfully because the four-property fixed
surface admits only a common subset; everything outside requires
per-domain companion schemas that compound the ratification cost
without the heterogeneity payoff. The principles do not pick a single
winner among A/C/D — each leads on different dimensions, and the
choice depends on which principles AOUSD weights most heavily:

- **A** leads on industry agnosticism, vendor extensibility, and
  minimal disruption (no coordination, no new core surface). Pays for
  it on discoverability (parse-based) and on the absence of slot-level
  separation by content type.
- **C** leads on industry agnosticism (overflow accommodates the
  heterogeneity surface) and matches A on extensibility for overflow
  fields. Pays for it on minimal disruption (new ratified schema, full
  plugin-distribution matrix).
- **D** leads on discoverability (per-facet `apiSchemas` instances)
  and ties A on vendor extensibility. Pays for it on industry
  agnosticism — the labels-only surface cannot carry the
  heterogeneous typed surface (timestamps, numeric measures with
  units, composite typed references, polymorphic AAS Property values)
  that surfaces in every vertical surveyed.

**Conditional weighting on Minimal disruption.** Per Aaron's
2026-05-07 call on the schema-distribution friction tension, B and
C's score on this dimension reflects the *current* matrix burden —
DCC × USD release × Python × OS × runtime × build flavor, fragmented
across vendors who ship USD binaries today. The AOUSD Build Interest
Group's parent epic
([`aousd/build-ig-initiatives#28`](https://github.com/aousd/build-ig-initiatives/issues/28))
is actively scoping work to reduce this burden (hosted binaries,
plugin registration via importlib, conda-forge / PyPI distribution).
B and C's score on Minimal disruption is expected to trend lighter
as those initiatives land. The trajectory is detailed in
[`formality_and_distribution.md`](formality_and_distribution.md).

**Caveat preserved.** Numerical totals are illustrative of how the
mechanisms trade off across principles, not a verdict. Different
principle weights would produce different totals. The published
1–5 anchors and the per-mechanism justifications are the primary
reading.

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

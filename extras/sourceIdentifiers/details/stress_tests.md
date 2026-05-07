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

## 5.3 Vendor adoption scoring

**Methodology:** Eight dimensions scored 1–5 from the multi-vendor
simulation, stress test results, and composition analysis. Dimensions
deliberately do not credit any mechanism for collision detection,
governance enforceability, or composition for non-timevarying strings as
schema-only advantages — those properties hold symmetrically across all
four approaches.

| Dimension | A | B | C | D |
|-----------|---|---|---|---|
| Initial adoption friction (fewer steps = higher) | 5 | 4 | 4 | 4 |
| Distribution friction (no new schema = higher) | 5 | 2 | 2 | 5 |
| Per-prim discoverability (which systems on this prim) | 2 | 4 | 4 | 5 |
| Per-facet discoverability (which facet of which system) | 2 | 2 | 3 | 5 |
| Metadata heterogeneity (carries arbitrary domain data) | 5 | 2 | 5 | 4 |
| Validator implementability (registry-spec compliance) | 2 | 4 | 4 | 5 |
| Composition for typical edits (non-timevarying strings) | 4 | 4 | 4 | 4 |
| File size cost (smaller = higher) | 4 | 5 | 3 | 4 |
| **Total (max 40)** | **29** | **27** | **29** | **36** |

**Source:** `stress_tests/vendor_adoption_analysis.json` (re-runnable via
`python3 vendor_adoption_analysis.py`).

**Where each approach lands.**

- **D** leads on discoverability and distribution: per-facet `apiSchemas`
  instances + no new schema to ratify or distribute.
- **A** leads on initial-adoption and heterogeneity: zero coordination,
  freeform dicts.
- **C** matches A on heterogeneity but pays distribution friction for the
  schema and carries both mechanisms (largest file size).
- **B** is smallest on disk but trails on heterogeneity (no place for
  domain-specific fields) and pays distribution friction without D's
  per-facet discoverability gain.

After symmetric treatment of governance and composition, the schema-derived
advantages that remain narrow to discoverability and validator-
implementability ergonomics. On those, the scoring leans toward D —
because D exposes facet structure on the `apiSchemas` list without
requiring a new schema to ship.

**Caveat.** These scores are illustrative, not objective. Different
weights (or different dimension choices) would produce different totals.
The scoring's value is identifying *which dimensions each approach
leans on*, not declaring a winner by arithmetic.

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

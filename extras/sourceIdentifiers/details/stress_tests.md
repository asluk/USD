# Ecosystem Simulation & Stress Tests

← [Back to COMPARISON.md](../COMPARISON.md)

## 5.1 Multi-vendor simulation

**Files:** `vendor_simulation/approach_a_vendors.usda`,
`vendor_simulation/approach_b_vendors.usda`

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
  properties suffice. But if the vendor needs domain-specific fields
  (6 of 8 simulated vendors do), they must either register a companion
  schema or use custom attributes - adding friction.

**Collision scenario:**

- **Approach A:** If two vendors independently pick the key `"tracker"`,
  their data silently collides. The composed result contains only the
  strongest opinion's `tracker` dictionary. No warning is produced.
  Mitigation: reverse-DNS keys (e.g., `"com.vendor1.tracker"`), but
  this is convention, not enforcement.

- **Approach B:** If two vendors both use `SourceIdSchemaAPI:tracker`,
  the `apiSchemas` list cannot contain duplicate entries. The `domain`
  property provides secondary disambiguation. More importantly, schema
  registration makes the collision *visible* - tools inspecting the
  prim will see the conflicting schema application.

**Promotion lifecycle:**

- **Approach A:** Promoting `"nvidia_simready"` to `"aousd_simready"`
  requires renaming dictionary keys in all existing content. No schema
  versioning mechanism tracks the migration. Tools querying by key must
  be updated.

- **Approach B:** Promotion can be as simple as updating the `domain`
  token value (`"com.nvidia.simready"` → `"org.aousd.simready"`),
  since tools can query by `domain` rather than instance name. If the
  instance name also changes, schema versioning tracks the migration
  and the old instance can be deprecated with a clear successor path.

## 5.2 Stress test: 100,000 prims

**Generator:** `stress_tests/generate_large_stage.py` (deterministic,
`random.seed(42)`; regenerate with `python3 generate_large_stage.py`)
**Configuration:** 100,000 prims, each with 1-5 randomly assigned
domains from the 8-vendor pool, with metadata fields.

### File size and verbosity

| Metric | Approach A | Approach B | Ratio (B/A) |
|--------|-----------|-----------|-------------|
| File size | 106.26 MB | 91.55 MB | 0.862× |
| Line count | 3,085,417 | 2,020,995 | 0.655× |
| Generation time | 6.37 s | 1.29 s | 0.203× |

### Estimated binary (usdc) sizes

The stress test generates `.usda` text files. Production USD pipelines
typically use the Crate binary format (`.usdc`), which compresses
significantly. Based on published Crate compression characteristics
(string deduplication, integer compression, structural overhead removal),
typical compression ratios for attribute-heavy data are 3–5× smaller
than `.usda`.

| Metric | A (usda) | B (usda) | C (usda) | A (est. usdc) | B (est. usdc) | C (est. usdc) |
|--------|---------|---------|---------|--------------|--------------|--------------|
| File size | 106.3 MB | 91.6 MB | 144.0 MB | ~25–35 MB | ~22–31 MB | ~34–48 MB |

**Note:** These are estimates, not measurements. Actual `usdc` sizes depend
on string deduplication efficiency (which favors B's repeated property name
patterns) and dictionary encoding overhead (which may compress differently
for A's nested structures). Generating actual `usdc` files requires a built
OpenUSD environment; contributions of measured values are welcome.

The key observation is that the relative ordering (B < A < C) is likely
preserved in binary format, but the absolute differences narrow
substantially. C's 57% text-format overhead over B likely reduces to
~30–50% in binary.

**Analysis:** Approach B produces 14% smaller files and 35% fewer lines.
This is because:

1. **No nesting overhead.** Approach A requires `dictionary sourceIds = {`
   and `dictionary <domain> = {` wrapper lines at each nesting level.
   Approach B's flat property namespace has no nesting.

2. **No metadata sub-dict.** Approach A carries domain-specific metadata
   as additional dictionary entries. The equivalent data would require
   companion schemas in B, but since B's base schema doesn't carry it,
   the comparison is not apples-to-apples on content richness. **If both
   approaches carried identical metadata, A would be smaller** because
   dictionary keys are shorter than fully-qualified property names.

3. **Generation time difference** reflects Python string formatting
   overhead for nested dict syntax vs. flat properties, not a meaningful
   performance signal.

### Namespace footprint

| Metric | Approach A | Approach B |
|--------|-----------|------------|
| Unique names in stage | 10 dictionary keys | 30 property names |
| Names per domain | 1 key | 4 properties |
| At 20 vendors × 5 schemes | 100 dict keys | 400 properties + 100 apiSchemas |

**Analysis:** Approach A has a 3× smaller namespace footprint per domain
because each domain is a single dictionary key containing nested data.
Approach B explodes each domain into 4 separately-named properties. At
scale (20 vendors × 5 schemes = 100 domains), Approach B would add
400 property names to each prim's property namespace - a significant
crowding concern, though each property is individually addressable and
typed.

### Discovery performance (text search)

| Metric | Approach A | Approach B |
|--------|-----------|------------|
| Full-stage text scan | 0.638 s | 0.590 s |

Both approaches require a full scan for reverse lookups ("which prims
have this identifier?"). Performance is comparable. In production, both
would benefit from external indexing - the mechanism must make building
such indexes tractable, which both do (A via dictionary key iteration,
B via property name pattern matching or `apiSchemas` list filtering).

## 5.3 Vendor adoption scoring

**Methodology:** Eight dimensions scored 1-5 based on the multi-vendor
simulation, stress test results, and composition analysis.

| Dimension | A | B | Winner | Weight for TAC |
|-----------|---|---|--------|---------------|
| Ease of initial adoption | 5 | 4 | A | Medium |
| Collision safety | 2 | 4 | B | High |
| Metadata flexibility | 5 | 3 | A | High |
| GUI integration | 2 | 5 | B | Medium |
| Promotion lifecycle | 3 | 4 | B | Medium |
| Scale manageability | 3 | 3 | - | Low |
| Discoverability | 2 | 5 | B | High |
| Schema validation | 1 | 5 | B | High |
| **Total** | **23** | **33** | **B** | |

**Interpretation:** Approach B dominates on the dimensions that a
standards body cares about most (safety, discoverability, validation,
governance). Approach A wins on the dimensions that individual vendors
care about most (ease of adoption, metadata flexibility). This is not
a contradiction - it reflects the fundamental trade-off between
governance and flexibility, and it's why the hybrid recommendation
exists (see [hybrid_analysis.md](hybrid_analysis.md)).

## 5.4 Three-tier scoring: Approach C with codeless companions

The three-tier model (core schema + codeless companion schemas + overflow)
changes the scoring for Approach C by splitting the domain-specific metadata
tier into two maturity levels.

| Dimension | A | B | C (two-tier) | C (three-tier) | Notes |
|-----------|---|---|-------------|----------------|-------|
| Ease of initial adoption | 5 | 4 | 5 | 5 | Overflow onramp unchanged |
| Collision safety | 2 | 4 | 4 | 4 | Core + companion both use schema namespace |
| Metadata flexibility | 5 | 3 | 5 | 5 | Overflow still available for experimental fields |
| GUI integration | 2 | 5 | 4 | 4.5 | Companion fields now discoverable in GUIs |
| Promotion lifecycle | 3 | 4 | 4 | 5 | **Three-tier path is smoother** |
| Scale manageability | 3 | 3 | 3 | 3 | Unchanged |
| Discoverability | 2 | 5 | 3 | 4 | **Stable fields now in schema registry** |
| Schema validation | 1 | 5 | 3 | 4 | **Stable fields now typed and validated** |
| **Total** | **23** | **33** | **31** | **34.5** | |

**Key changes from two-tier to three-tier:**

- **Promotion lifecycle (+1):** The overflow → codeless companion → core
  path is more gradual than overflow → core. Domains can graduate stable
  fields to a companion schema without TAC approval, reducing bottleneck
  risk.
- **Discoverability (+1):** Fields in codeless companion schemas are
  visible in `UsdSchemaRegistry`, appear in property panels, and are
  queryable by type. The two-tier model had these fields hidden in
  opaque dicts.
- **Schema validation (+1):** Companion schema properties have declared
  types. `ifcType` as a `token` is validated differently than a freeform
  dict string.
- **GUI integration (+0.5):** Companion properties appear in DCC property
  panels alongside core properties. Overflow fields still require custom
  UI.

**Why C (three-tier) now edges past B:** The three-tier model recovers
most of B's governance advantages (discoverability, validation) for stable
fields while retaining A's flexibility for experimental fields. The total
score (34.5) exceeds B (33) because the three-tier model provides a
strictly better promotion path and retains overflow flexibility that B
lacks entirely.

**Caveat:** These scores are illustrative, not objective measurements.
The weights reflect TAC priorities (governance dimensions weighted higher)
and the specific scenarios tested. Different weights would produce
different totals. The scoring is included to structure the comparison, not
to declare a winner by arithmetic.

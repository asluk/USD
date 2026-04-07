# Source Identifiers — Implementation & Comparison Status

**Branch:** `aluk/source-identifiers-comparison`
**Decision:** Single branch with both approaches side-by-side for direct comparison.

**Rationale:** A single branch lets reviewers see both implementations in the same tree, diff them directly, and run the same test harness against both. Two branches would complicate cross-referencing.

## Architecture

### Approach A: `assetInfo` stratified sub-dictionaries
- New module: `pxr/usd/usdSourceId/` (convenience API wrapping `assetInfo` sub-dictionaries)
- Applied single-apply API schema `UsdSourceIdAPI` that provides typed convenience access to `assetInfo["sourceIds"]` sub-dictionaries
- Follows `UsdMediaAssetPreviewsAPI` precedent: schema provides API, data lives in composed `assetInfo` metadata

### Approach B: Multi-apply schema with typed properties
- New module: `pxr/usd/usdSourceIdSchema/` 
- Multi-apply API schema `UsdSourceIdSchemaIdentifierAPI` with instance names like `sourceIdentifier:windchill`, `sourceIdentifier:ifc`
- Typed properties: `primaryId` (string), `revision` (string), `domain` (token), `metadata` (dictionary)
- Follows `UsdSemanticsLabelsAPI` / `UsdCollectionAPI` precedent

### Shared
- Example USD files demonstrating both approaches with identical content
- Multi-vendor simulation (NVIDIA, Adobe, Apple, SideFX, Autodesk, IFC, Windchill, SAP)
- Stress test scripts (collision, promotion, discovery at scale, heterogeneous packages)
- Comparison document with empirical data

## Progress

### Phase 1: Approach A — `assetInfo` sub-dictionary pattern
- [ ] Schema definition (`schema.usda`)
- [ ] Generated + hand-written C++ API
- [ ] Python bindings
- [ ] Example USD files with multi-vendor identifiers
- [ ] Tests

### Phase 2: Approach B — Multi-apply schema pattern  
- [ ] Schema definition (`schema.usda`)
- [ ] Generated + hand-written C++ API
- [ ] Python bindings
- [ ] Example USD files with multi-vendor identifiers
- [ ] Tests

### Phase 3: Ecosystem simulation & stress tests
- [ ] Multi-vendor identifier packages (8+ vendors/standards)
- [ ] Collision scenarios
- [ ] Promotion lifecycle simulation
- [ ] Discovery at scale (100K+ prim stage)
- [ ] Heterogeneous packages (5+ systems per prim)

### Phase 4: Comparison document
- [ ] Code complexity metrics
- [ ] Adoption friction analysis
- [ ] Performance measurements
- [ ] Governance implications
- [ ] Recommendation

## Timeline
Started: 2026-04-07 04:25 UTC

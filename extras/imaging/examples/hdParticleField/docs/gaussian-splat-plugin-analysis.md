# Gaussian Splat File Format Plugin Analysis

**Date:** March 4, 2026
**Context:** Analysis of Adobe's USD file format plugins vs OpenUSD's ParticleField3DGaussianSplat schema

## Executive Summary

Adobe's [USD-Fileformat-plugins](https://github.com/adobe/USD-Fileformat-plugins) repository includes plugins for PLY and SPZ (Gaussian Splat) formats, but they were created before OpenUSD's official `ParticleField3DGaussianSplat` schema was added (January 26, 2026). The plugins currently use `UsdGeomPoints` with custom attributes instead of the standardized schema.

**Opportunity:** Update Adobe's plugins to use the official schema for better interoperability and compatibility with the hdParticleField render delegate.

---

## Background

### Converter Scripts in This Repository

This repository contains two well-written Python converter scripts:

1. **py3dgsPlyToUsd.py** (534 lines)
   - Converts PLY format with Gaussian Splat data to USD
   - Includes complete PLY parser (binary & ASCII)
   - Targets `UsdVol.ParticleField3DGaussianSplat`

2. **py3dgsSpzToUsd.py** (618 lines)
   - Converts SPZ (Niantic's compressed format, ~10x smaller than PLY)
   - Includes pure Python SPZ decompressor
   - Also targets `UsdVol.ParticleField3DGaussianSplat`

**Location:** `USD/extras/imaging/examples/hdParticleField/`

### Adobe's USD File Format Plugins

Adobe's repository provides seven file format plugins including:
- **usdply** - PLY file format support (meshes, point clouds, AND Gaussian splats)
- **usdspz** - SPZ file format support (Gaussian splats)

These are production-quality C++ plugins with:
- Bidirectional read/write support
- Cross-platform CI/CD (Windows, macOS, Linux)
- Integration with USD's plugin discovery system

**Challenge:** Complex build system with many dependencies (USD, Eigen, Fmt, FastFloat, etc.)

---

## Schema Comparison

### Adobe's Current Implementation (UsdGeomPoints)

Adobe's plugins use **UsdGeomPoints** (generic point cloud schema) with custom primvars:

```cpp
// Geometry type
UsdGeomPoints points = UsdGeomPoints::Define(stage, path);

// Attributes stored as separate primvars
positions:     mesh.points (Vec3fArray)
scales:        scale_0, scale_1, scale_2 (3 separate Float primvars)
orientations:  mesh.pointRotations (QuatfArray)
opacities:     opacity (Float primvar)
SH DC:         f_dc_0, f_dc_1, f_dc_2 (3 separate Float primvars)
SH rest:       f_rest_0 ... f_rest_44 (up to 45 separate Float primvars)
clippingBox:   custom metadata
```

**Data transformations:**
- Scales: `exp(value)` transformation from log-scale
- Opacities: `1.0 / (1.0 + exp(-value))` sigmoid transformation
- SH: Row-major to column-major conversion
- Array-of-Structs to Struct-of-Arrays format

### OpenUSD Official Schema (ParticleField3DGaussianSplat)

**Added:** January 26, 2026 (commit 443915ed2)
**Schema:** `UsdVol.ParticleField3DGaussianSplat`

Uses a hierarchical applied schema architecture:

```cpp
// Dedicated Gaussian Splat schema
UsdVolParticleField3DGaussianSplat gsplat =
    UsdVolParticleField3DGaussianSplat::Define(stage, path);

// Standardized attributes via applied schemas
positions:     positions (Vec3fArray)           // ParticleFieldPositionAttributeAPI
scales:        scales (Vec3fArray)              // ParticleFieldScaleAttributeAPI
orientations:  orientations (QuatfArray)        // ParticleFieldOrientationAttributeAPI
opacities:     opacities (FloatArray)           // ParticleFieldOpacityAttributeAPI
SH:            radianceSphericalHarmonicsCoefficients (Vec3fArray)
               radianceSphericalHarmonicsDegree (int)
               [with elementSize and interpolation metadata]
                                                // ParticleFieldSphericalHarmonicsAttributeAPI
```

**Applied Schemas:**
- `ParticleFieldPositionAttributeAPI` - Position data (required)
- `ParticleFieldScaleAttributeAPI` - Scale factors (linear, not log)
- `ParticleFieldOrientationAttributeAPI` - Quaternion orientations
- `ParticleFieldOpacityAttributeAPI` - Opacity values
- `ParticleFieldSphericalHarmonicsAttributeAPI` - SH coefficients
- `ParticleFieldKernelGaussianEllipsoidAPI` - Kernel type marker

**Data format:**
- Scales stored in linear format (not log-scale)
- SH coefficients stored as Vec3fArray with elementSize primvar
- Clean separation of concerns via applied schemas

---

## Key Differences

| Aspect | Adobe (UsdGeomPoints) | OpenUSD (ParticleField3DGaussianSplat) |
|--------|----------------------|---------------------------------------|
| **Schema** | Generic point cloud | Dedicated Gaussian Splat schema |
| **Scales** | 3 separate Float primvars | Single Vec3fArray attribute |
| **SH** | Up to 48 separate primvars | Single Vec3fArray with elementSize |
| **Discovery** | Custom attribute detection | Schema type check |
| **Render Delegate** | Would need custom adapter | hdParticleField works out-of-box |
| **Standardization** | Custom convention | Official USD schema |
| **Extensibility** | Ad-hoc attributes | Applied schema system |

---

## Impact

### Why This Matters

1. **Render Delegate Compatibility**
   - hdParticleField expects `ParticleField3DGaussianSplat` schema
   - Current Adobe plugins won't work with hdParticleField without custom adapter

2. **Standardization**
   - Official schema is the canonical representation
   - Future tools will expect the standard schema
   - Interoperability across USD ecosystem

3. **Cleaner Architecture**
   - Applied schemas provide structured API
   - Type safety and discovery
   - Better tooling support

4. **Documentation**
   - Official schema has API documentation
   - Clear semantics for each attribute

---

## What Needs to Be Updated

### In Adobe's usdply Plugin

**File:** `ply/src/plyImport.cpp`

Current logic detects Gaussian splats by checking for specific PLY attributes:
```cpp
// Detection heuristic
if (hasAttr("opacity") && hasAttr("f_dc_0") && hasAttr("rot_0") &&
    hasAttr("scale_0") && hasAttr("f_rest_*")) {
    mesh.asGsplats = true;
}
```

**Needs to change to:**

1. **Import Path:**
   ```cpp
   // Instead of UsdGeomPoints
   if (mesh.asGsplats) {
       UsdVolParticleField3DGaussianSplat gsplat =
           UsdVolParticleField3DGaussianSplat::Define(stage, path);

       // Set positions
       gsplat.CreatePositionsAttr(positions);

       // Combine scale_0/1/2 into Vec3fArray
       Vt.Vec3fArray scales;
       for (int i = 0; i < count; i++) {
           scales.push_back(Gf.Vec3f(
               exp(scale_0[i]),
               exp(scale_1[i]),
               exp(scale_2[i])
           ));
       }
       gsplat.CreateScalesAttr(scales);

       // Orientations
       gsplat.CreateOrientationsAttr(orientations);

       // Opacities
       Vt.FloatArray opacities;
       for (auto v : opacity_raw) {
           opacities.push_back(1.0f / (1.0f + exp(-v)));
       }
       gsplat.CreateOpacitiesAttr(opacities);

       // SH coefficients
       gsplat.CreateRadianceSphericalHarmonicsDegreeAttr(shDegree);

       // Combine f_dc and f_rest into structured array
       Vt.Vec3fArray shCoeffs = combineSHData(f_dc, f_rest, shDegree);
       auto shAttr = gsplat.CreateRadianceSphericalHarmonicsCoefficientsAttr(shCoeffs);

       UsdGeomPrimvar shPrimvar(shAttr);
       shPrimvar.SetElementSize(shVecStride);
       shPrimvar.SetInterpolation(UsdGeomTokens->vertex);
   }
   ```

2. **Export Path:**
   - Detect `ParticleField3DGaussianSplat` prims
   - Read standardized attributes
   - Convert to PLY format with proper attribute names

### In Adobe's usdspz Plugin

**File:** `spz/src/spzImport.cpp`

Similar changes needed:
- Use `UsdVolParticleField3DGaussianSplat::Define()` instead of `UsdGeomPoints`
- Map SPZ data directly to official schema attributes
- Handle SH coefficient reordering for official format

### Additional Considerations

**Backward Compatibility:**
- Consider supporting both old (UsdGeomPoints) and new (ParticleField3DGaussianSplat) on import
- Add option to choose output schema: `plyGsplatSchema=points|particlefield`
- Detect existing schema type on export

**File Format Arguments:**
```cpp
// New options
FileFormatArguments args = {
    {"plyGsplatSchema", "particlefield"},  // or "points" for legacy
    {"plyGsplatsClippingBox", "[-2,-2,-2,2,2,2]"}
};
```

---

## Code References

### OpenUSD Implementation Examples

**Schema Definition:**
- `USD/pxr/usd/usdVol/schema.usda` - Schema specification
- `USD/pxr/usd/usdVol/particleField3DGaussianSplat.h` - C++ API
- `USD/pxr/usd/usdVol/particleField3DGaussianSplat.cpp` - Implementation

**Converter Scripts (Reference Implementation):**
- `USD/extras/imaging/examples/hdParticleField/py3dgsPlyToUsd.py:290-525` - PLY to ParticleField conversion
- `USD/extras/imaging/examples/hdParticleField/py3dgsSpzToUsd.py:369-613` - SPZ to ParticleField conversion

**Render Delegate:**
- `USD/extras/imaging/examples/hdParticleField/hd3DGaussianSplat.cpp` - How to consume the schema
- `USD/pxr/usdImaging/usdVolImaging/particleFieldAdapter.cpp` - USD Imaging adapter

### Adobe Plugin Files

**PLY Plugin:**
- `ply/src/plyImport.cpp` - Import logic (needs update)
- `ply/src/plyExport.cpp` - Export logic (needs update)
- `ply/README.md` - Documentation

**SPZ Plugin:**
- `spz/src/spzImport.cpp` - Import logic (needs update)
- `spz/src/spzExport.cpp` - Export logic (needs update)
- `spz/README.md` - Documentation

---

## Recommendations

### Short Term
Continue using the Python converter scripts for Gaussian splat workflows:
```bash
python py3dgsPlyToUsd.py -i input.ply -o output.usd
python py3dgsSpzToUsd.py -i input.spz -o output.usd
```

These work perfectly with hdParticleField renderer.

### Medium Term
**Option 1: Contribute to Adobe**
- Fork Adobe's repository
- Update usdply and usdspz to support ParticleField3DGaussianSplat
- Maintain backward compatibility with UsdGeomPoints representation
- Submit pull request

**Option 2: Create Minimal Plugins**
- Wrap Python converters in lightweight C++ file format plugins
- Place in `USD/extras/imaging/examples/hdParticleField/plugins/`
- Read-only, simple to build, no external dependencies

**Option 3: Hybrid**
- Keep Python converters as standalone tools
- Contribute minimal patch to Adobe for ParticleField support
- Best of both worlds

### Long Term
Establish `ParticleField3DGaussianSplat` as the canonical representation for Gaussian splats in USD ecosystem.

---

## Timeline

- **January 26, 2026:** ParticleField3DGaussianSplat schema added to OpenUSD (commit 443915ed2)
- **Pre-2026:** Adobe's plugins created using UsdGeomPoints approach
- **March 4, 2026:** Gap identified and documented (this analysis)
- **Next steps:** Update Adobe plugins or create alternative implementation

---

## Resources

### Documentation
- [OpenUSD ParticleField Overview](https://openusd.org/dev/api/usd_vol_page_front.html)
- [Adobe USD File Format Plugins](https://github.com/adobe/USD-Fileformat-plugins)
- [3D Gaussian Splatting Paper](https://arxiv.org/abs/2308.04079)

### Related Work
- hdParticleField render delegate (this repository)
- SPZ format spec: https://github.com/nianticlabs/spz
- USD file format plugin documentation: `USD/pxr/usd/sdf/doxygen/fileFormatPlugin.dox`

---

## Action Items

- [ ] Review OpenUSD's ParticleField schema API
- [ ] Test converter scripts with Adobe's test assets
- [ ] Draft patch for Adobe's usdply plugin
- [ ] Draft patch for Adobe's usdspz plugin
- [ ] Test compatibility with hdParticleField renderer
- [ ] Consider contributing back to Adobe repository
- [ ] Update documentation in both repositories

---

## Contact & Context

This analysis was conducted as part of exploring the hdParticleField render delegate example and identifying opportunities to improve Gaussian Splat workflow integration in the USD ecosystem.

**Session Context:** Conversation with Claude Code on March 4, 2026
**Repository:** OpenUSD fork at `C:\git\usd-ci`
**Branch:** `build-doc-gaps`

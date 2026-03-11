# SPZ Parser Implementation: Lessons Learned

**Date:** February 26, 2026  
**Context:** Bugs discovered during development of `py3dgsSpzToUsd.py`

## Overview

During the initial implementation of a pure Python SPZ file parser, several bugs were introduced due to misunderstanding the SPZ binary format specification. This document captures the bugs and key lessons for future reference.

---

## Bug Summary

### 1. Wrong SPZ Payload Order (Critical)

**Impact:** Complete data corruption - all fields after positions were misaligned.

```python
# WRONG:
positions → scales → rotations → alphas → colors → sh

# CORRECT (per SPZ spec):
positions → alphas → colors → scales → rotations → sh
```

**Root Cause:** Assumed logical grouping (geometry → appearance) instead of reading the actual format specification.

---

### 2. Alpha Decoding (Wrong Transformation)

**Impact:** Opacity values were completely wrong, causing rendering artifacts.

```python
# WRONG:
alpha = (encoded / 255.0) * 16.0 - 8.0

# CORRECT (inverse sigmoid):
s = encoded / 255.0
s = min(1.0 - 1e-6, max(1e-6, s))  # Clamp to avoid log(0)
alpha = math.log(s / (1.0 - s))
```

**Root Cause:** SPZ stores `sigmoid(alpha)` directly in [0, 255] range. The file stores the post-sigmoid value, so inverse sigmoid (logit function) is needed to recover the raw alpha for USD, which then applies sigmoid during rendering.

---

### 3. Color Decoding (Missing COLOR_SCALE)

**Impact:** Colors appeared washed out or oversaturated.

```python
# WRONG:
r = r_encoded / 255.0

# CORRECT:
COLOR_SCALE = 0.15
r = ((r_encoded / 255.0) - 0.5) / COLOR_SCALE
```

**Root Cause:** SPZ colors are SH DC (degree-0 spherical harmonic) coefficients, not raw RGB. They use a specific quantization with a scale factor of 0.15 and are centered at 0.5.

---

### 4. Version 2 Rotation Decoding (Wrong Byte Interpretation)

**Impact:** Rotations were subtly wrong, causing shearing artifacts.

```python
# WRONG (signed byte with wrong scale):
qx = struct.unpack_from('b', data, offset)[0] / 127.0

# CORRECT (unsigned byte, centered):
qx = (struct.unpack_from("B", data, offset)[0] / 127.5) - 1.0
```

**Root Cause:** Assumed signed bytes (`'b'`) when SPZ uses unsigned bytes (`'B'`) with a different scaling to map [0, 255] → [-1, 1].

---

### 5. Version 3 Rotation Unpacking (Bit Manipulation Errors)

**Impact:** Quaternions were completely wrong for v3 SPZ files.

The "smallest three" quaternion encoding packs 4 quaternion components into 32 bits:
- 2 bits: index of largest component
- 3 × 10 bits: the three smallest components (9-bit magnitude + 1-bit sign)

```python
# CORRECT implementation:
c_mask = (1 << 9) - 1
i_largest = packed >> 30
comps = [0.0, 0.0, 0.0, 0.0]
sum_sq = 0.0

for i in (3, 2, 1, 0):
    if i == i_largest:
        continue
    mag = packed & c_mask
    negbit = (packed >> 9) & 0x1
    packed >>= 10
    v = 0.7071067811865476 * (float(mag) / float(c_mask))
    if negbit == 1:
        v = -v
    comps[i] = v
    sum_sq += v * v

comps[i_largest] = math.sqrt(max(0.0, 1.0 - sum_sq))
```

**Root Cause:** Complex bit-level encoding requires careful attention to bit positions, masks, and iteration order.

---

### 6. SH Coefficient Encoding (Wrong Center Point)

**Impact:** Spherical harmonics were offset, causing color banding.

```python
# WRONG:
sh_value = encoded / 128.0

# CORRECT:
sh_value = (encoded - 128.0) / 128.0
```

**Root Cause:** SH coefficients are signed values stored as unsigned bytes centered at 128, mapping [0, 255] → [-1, 1].

---

## Key Lessons Learned

### 1. Binary Format Order is Critical

Never assume field order based on logical grouping. Always verify against the format specification. Even small deviations cause complete data corruption downstream.

### 2. Quantization Schemes Vary Per Field

Each field in SPZ uses a different encoding:

| Field | Encoding |
|-------|----------|
| Positions | 24-bit fixed point with configurable fractional bits |
| Alphas | sigmoid(alpha) stored as uint8 |
| Colors | SH DC coefficients with COLOR_SCALE=0.15, centered at 0.5 |
| Scales | log-scale stored as uint8 |
| Rotations v2 | xyz components as uint8 centered, w derived |
| Rotations v3 | "smallest three" 32-bit packed |
| SH coeffs | Signed values as uint8 centered at 128 |

### 3. Read the Format Spec Thoroughly

The [SPZ README](https://github.com/nianticlabs/spz) documents all encodings. Key sections:
- "File Format" section describes payload order
- Individual subsections describe each field's encoding

### 4. Test with Real Data

Unit tests with synthetic data may pass while real-world data fails. Visual inspection of rendered output catches issues that programmatic tests miss.

### 5. Don't Assume Transformations

The relationship between stored values and semantic values varies:
- **Alphas:** File stores post-sigmoid, USD expects pre-sigmoid
- **Scales:** File stores log-scale, USD expects linear
- **Colors:** File stores quantized SH DC, not raw RGB

### 6. Reference Implementations Are Valuable

When available, cross-reference with:
- The official C++ implementation
- The Python bindings documentation
- Other working parsers (e.g., three.js loaders)

---

## Testing Recommendations

1. **Use known-good test files** - The SPZ repo includes `samples/hornedlizard.spz`
2. **Compare against reference implementation** - Load with official `spz` Python bindings if available
3. **Visual verification** - Render the output and compare against reference renders
4. **Field-by-field validation** - Check min/max/mean of each field against expected ranges

---

## References

- [SPZ Format Specification](https://github.com/nianticlabs/spz)
- [SPZ Python Bindings README](https://github.com/nianticlabs/spz/blob/main/src/python/README.md)
- [3D Gaussian Splatting Paper](https://arxiv.org/abs/2308.04079)
- Working implementation: `py3dgsSpzToUsd.py` in this directory

---

## Appendix: Recommended Improvements to USD ParticleField Documentation

**Date:** March 6, 2026  
**Context:** Review of USD's `ParticleField3DGaussianSplat` schema docs through the lens of what an implementer actually needs to know when writing a converter.

### What the USD Schema Already Does Well

The `schema.usda` explicitly warns about the two most common conversion pitfalls:

- **Scales** (`ParticleFieldScaleAttributeAPI`): "not specified in log-format as is sometimes seen in PLY files associated with gaussian splats"
- **Opacities** (`ParticleFieldOpacityAttributeAPI`): "not the transformed data sometimes seen in PLY files... where the values need to be processed with a sigmoid activation function"

These notes directly prevent bugs #2 and the scale-related aspects of this postmortem. More specs should do this.

### What's Missing

#### 1. Quaternion Convention and Component Order (High Priority)

The schema defines `quatf[] orientations` but never states the component order. SPZ uses (x,y,z,w). PLY typically stores (w,x,y,z). `GfQuatf` uses (real, imaginary) — but that's a USD API detail, not something stated at the schema level.

An implementer reading only the schema has to discover the convention by trial, error, and reading `GfQuatf` source.

**Suggested addition to `ParticleFieldOrientationAttributeAPI`:**
> Quaternions follow the USD convention: real component (w) first, followed by imaginary components (x, y, z). This matches the GfQuatf constructor order.

#### 2. SH Basis Convention and Normalization (High Priority)

The schema documents the storage layout (particle-major, Y(m,l) sorted by order then index) but not:
- Which SH basis is used (real vs complex)
- The normalization convention
- How this relates to the SH conventions used in the original 3DGS paper or common training frameworks

Different 3DGS implementations use different conventions, and silent mismatches produce subtle color errors.

#### 3. SH Color Space (Medium Priority)

The default DC value of (0.5, 0.5, 0.5) is mentioned but there's no statement about whether SH coefficients are in linear or sRGB space. This matters for any renderer performing color space conversions.

#### 4. Interop / Conversion Guide (Medium Priority)

PLY and SPZ are mentioned only as "what not to do" warnings. There's no positive mapping guide. Something like:

| Source (PLY/SPZ) | Transformation | USD Attribute |
|------------------|---------------|---------------|
| `scale_0/1/2` | `exp(value)` | `scales` (Vec3fArray) |
| `opacity` | `sigmoid(value)` | `opacities` (FloatArray) |
| `rot_0/1/2/3` | normalize, reorder | `orientations` (QuatfArray) |
| `f_dc_0/1/2` + `f_rest_*` | reorder, combine | `radianceSphericalHarmonicsCoefficients` |

This would have prevented most of the bugs in this postmortem from ever occurring on the USD side.

#### 5. `schemaUserDoc.usda` Coverage (Medium Priority)

The user-facing documentation file (`pxr/usd/usdVol/userDoc/schemaUserDoc.usda`) only covers Volume, FieldBase, FieldAsset, Field3DAsset, and OpenVDBAsset. None of the ParticleField schemas have user doc entries yet.

#### 6. Coordinate System (Low Priority)

No statement about how particle positions relate to `UsdGeomSetStageUpAxis` or whether any axis convention is assumed.

### Summary

| Priority | Recommendation | Prevents |
|----------|---------------|----------|
| High | Document quaternion component order | Silent rotation bugs |
| High | Specify SH basis and normalization | Subtle color errors |
| Medium | Add PLY/SPZ → USD conversion table | Most converter bugs |
| Medium | Populate `schemaUserDoc.usda` for ParticleField | Discoverability gap |
| Medium | Document SH color space | Color space mismatches |
| Low | Clarify coordinate system relationship | Orientation confusion |

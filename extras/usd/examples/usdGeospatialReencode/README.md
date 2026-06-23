# Re-encoding Earth-2 as Georeferenced USD

A runnable prototype for the **Esri AOUSD Coordinate Reference System (CRS) proposal**,
demonstrated by re-encoding an already-OSS NVIDIA Earth-2 / NOAA GFS field as a
*georeferenced* USD scene instead of a baked Cartesian sphere.

It is built to clear the specific rock the prior geospatial effort hit: **how a CRS
reconciles with `UsdGeomXformable` — replace, wrap, or coexist?** The answer here is
*coexist*, demonstrated rather than argued.

## The design in one breath

* **Schema declares; runtime resolves.** This mirrors how Gaussian splats landed in
  OpenUSD — the `usdVol` schema is pure data and all splat behavior lives in the
  `hdParticleField` example — and how NVIDIA's `omniGeoSceneIndex` PoC resolved
  geospatial transforms in a Hydra scene index without changing `Xformable`.
* **Authored scene is CRS-neutral.** A `CoordinateReferenceSystem` prim carries an
  OGC **WKT2** string (`uniform token crs:wkt`). Each georeferenced `Xform` is bound
  to a CRS by a **relationship** (`rel crs:binding`, parallel to
  `UsdShadeMaterialBindingAPI`) and carries an absolute geodetic position in a
  **float64** attribute (`crs:position` = lon, lat, ellipsoidal height).
  There is **no `xformOp:translate` and no `SetResetXformStack`** in the authored data.
* **A separate runtime layer** reprojects `crs:position` from its source CRS to a
  target/render CRS (here WGS84 **ECEF**, EPSG:4978) via **PROJ**, producing the world
  cartesian transform — without writing anything back into the authored scene.

This keeps three things orthogonal that the v1 proposal entangled:
**composition** (a CRS prim arrives via standard `references`/`payloads`),
**binding** (an `Xform`→CRS relationship), and **behavior** (runtime reprojection).

## Why this clears the stall

The prior PoC and the v1 proposal baked runtime behavior into scene description
(`SetResetXformStack`, references-as-binding), forcing every downstream consumer to
inherit it and reopening "what does this do to `Xformable`?". Here the schema only
*declares* a binding — semantically inert, exactly like a material binding — and the
runtime is free to honor or ignore it. The transform API becomes an implementation
detail, which is precisely the path past the stall.

## Files

| file | role |
| --- | --- |
| `src/reencode_georef.py` | author OSS GFS t2m → CRS-neutral georeferenced USD (data only) |
| `src/resolve_runtime.py` | runtime: reproject `crs:position` → target CRS world cartesian (PROJ); optional `--bake` for a renderable artifact |
| `src/verify.py` | geodetic ground-truth checks (CI-style, exits non-zero on failure) |
| `src/render_evidence.py` | visual evidence: resolved ECEF globe + flattening + data-at-lon/lat |

## Run

```bash
python3 src/reencode_georef.py --stride 10 --out out/earth2_georef.usda
python3 src/verify.py            out/earth2_georef.usda
python3 src/resolve_runtime.py   --in out/earth2_georef.usda --bake out/earth2_resolved_ecef.usda
python3 src/render_evidence.py   --in out/earth2_georef.usda --out out/evidence.png
```

## Evidence (current)

* Authored scene is CRS-neutral — `verify.py` check **A** confirms no baked
  transform/reset.
* All samples bind to a CRS with parseable WKT2 — check **B**.
* Reprojection is geodetically correct — check **C**: the north pole resolves to
  ECEF *z* = 6 356 752.314 m (the WGS84 semi-minor axis *b*) and the equator/prime
  meridian to *x* = 6 378 137 m (semi-major *a*).
* Round-trip geographic→ECEF→geographic error ≈ **3 × 10⁻⁹ m** — check **D**.
* The resolved geometry shows WGS84 **ellipsoidal flattening** (mean equatorial
  radius ≈ 6 378 110 m vs polar ≈ 6 356 773 m): a true georeferenced Earth, not a
  baked sphere. See `docs/evidence.png`.

![evidence](docs/evidence.png)

## Status / next

* This is the **OpenUSD-side, Python-level** reference behavior, kept deliberately
  implementation-agnostic so it can inform the proposal and a C++ schema port.
* A parallel **NanoUSD** implementation (the second leg of the two-implementation
  evidence the strategy calls for) is intended but not built here.
* Open design items tracked against the Esri proposal PR: resolution-rule parity with
  `UsdShadeMaterialBindingAPI` (strength/purpose/collection), a worked multi-CRS
  example, and an external-grid-file asset path on `CoordinateReferenceSystem`.

## Data

NOAA **GFS** 2 m temperature, 0.25° global, fetched via NVIDIA **Earth2Studio**
(no API keys — open data). Re-used from the `earth2-ovrtx` example; nothing here
requires private inputs.

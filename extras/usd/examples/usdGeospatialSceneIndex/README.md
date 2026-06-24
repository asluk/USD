# usdGeospatialSceneIndex -- the Hydra production form of the geospatial runtime

This is the **compiled Hydra scene index** that performs geospatial coordinate
resolution at render time -- the production form of the Python reference runtime
in `../usdGeospatial/src/resolve_runtime.py`. It filters a scene and rewrites the
`xform` of geospatially-bound prims (and dirties their children) so a renderer
shows them in the right place **without baking transforms into the layer**
("inject, don't bake").

It pairs with the **codeless** `usdGeospatial` schema (`crs:binding` relationship
+ `crs:position` + opaque-WKT `CoordinateReferenceSystem` prims): the schema is
pure data, the behavior lives here.

## Design (and how it differs from the references)
- **Scaffolding** follows Pixar's in-tree `hdParticleField` example: `pxr_plugin`
  CMake macro, `plugInfo.json` registration, `extras/usd/examples/<name>/` layout.
  But this registers an **`HdSceneIndexPlugin`** (a FILTER that rewrites xforms),
  not an `HdRendererPlugin`.
- **Runtime model** is ported from NVIDIA's `omniGeoSceneIndex`
  (`HdSingleInputFilteringSceneIndexBase`, lazy per-prim wrapping, xform-locator
  override, child dirtying), updated to current Hydra (USD 0.26.8) and
  **retargeted** from the old `OmniWGS84*` API schemas to our
  `crs:binding`/`crs:position`.
- **WKT stays opaque to USD.** USD never parses WKT. `GeoCrsEngine` (PROJ) is the
  ONLY consumer of the WKT string -- the same contract as the Python `crs_engine`
  seam. A different deployment could swap a GPU engine behind the same interface.

## Files
- `crsEngine.{h,cpp}`         -- PROJ-backed CRS engine. `Reproject` +
  `LocalFrameToEcef` (rigid ENU/topocentric local-frame -> ECEF). Mirror of
  `crs_engine.PyprojEngine`.
- `geoResolver.{h,cpp}`       -- stage-level resolution: `ResolveBinding`
  (MaterialBinding-style strength/purpose/collection precedence), `AnchorFrame`,
  `NearestAnchor`, `ResolveWithInjection`, `ResolveWorldTranslation`. C++ port of
  `resolve_runtime.py`.
- `geospatialSceneIndex.{h,cpp}` -- the filtering scene index. Wraps Xformable
  prims that resolve to a geospatial anchor; overrides the `HdXformSchema` matrix
  locator with the inject-don't-bake world transform; dirties descendants.
- `geospatialSceneIndexPlugin.{h,cpp}` + `plugInfo.json` -- registration.
- `api.h`, `CMakeLists.txt`   -- in-tree plugin build (pxr_plugin + PROJ).

## Parity (the teeth)
`./run_parity.sh` proves the C++ implementation matches the Python reference
runtime **and** closed-form WGS84 geodesy to **sub-mm** across all datasets, at
three layers:

1. **engine vs closed-form geodesy** -- 9 datasets (geographic + 5 projected
   CRSs: UTM 18N/56S, NZTM2000, UTM 17S equatorial, UTM 33N high-lat). 0.0 mm.
2. **GeoResolver (stage-level) vs Python oracle + GT** -- the 9 datasets PLUS the
   real NVIDIA Deutsche Bahn railway anchor+curve subtree (translation samples)
   and the **anchor-frame matrices** (inject-don't-bake / orientation). 0.0 mm.
3. **Hydra scene index vs Python oracle + GT** -- the SAME datasets pulled THROUGH
   the Hydra pipeline (`UsdStage -> UsdImagingStageSceneIndex ->
   UsdGeospatialSceneIndex`), reading the `HdXformSchema` matrix exactly as a
   renderer would. 0.0 mm.

**Non-circular:** ground truth is closed-form WGS84 geodesy (the textbook
ellipsoidal formula), NOT a parallel PROJ call. A wrong projection/axis order
cannot pass.

**With teeth (negative control):** without this scene index, stock Hydra places
the georeferenced prims at the **origin (0,0,0)** -- `crs:position` is invisible
to stock USD/Hydra. With it, the same prims land at correct ECEF (~6.4e6 m). So
the scene index is doing real work; the 0.0 mm is not vacuous.

The Python suite / closed-form geodesy is the **oracle**; the C++ must agree.

## Building
- **In-tree** (canonical): drop into an OpenUSD source build with `--examples`
  and ensure PROJ is found; `CMakeLists.txt` uses the `pxr_plugin` macro exactly
  like `hdParticleField`.
- **Out-of-tree / parity** (de-risked path used here): `USD_INST=<inst>
  ./build_standalone.sh` builds the three parity tests against an installed USD
  + system `libproj`. Then `./run_parity.sh`.

## Environment
- Built + verified against the from-source OpenUSD dev build (USD 0.26.8) at
  `/tmp/usd-build/inst`; PROJ 8.2.1 (`libproj-dev`); schema registry via
  `PXR_PLUGINPATH_NAME=<repo>/pxr/usd/usdGeospatial/resources`.

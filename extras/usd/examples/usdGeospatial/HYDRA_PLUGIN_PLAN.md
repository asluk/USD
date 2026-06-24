# Hydra Plugin Implementation — Plan & Resume Point

_Created 2026-06-24 by claw1. This is the clean resume point for the usdGeospatial
**Hydra scene-index plugin** effort — a NEW phase, distinct from the codeless
Python reference-runtime work that is already landed and pushed._

---

## Where the codeless work left off (DONE — do not redo)
Branch `aluk/geospatial-crs-prototype` (origin = `asluk/USD`), HEAD **`3630afb88`**.
Full suite green (12 checks), 9 self-generated figures, schema in sync.
- Codeless schema `pxr/usd/usdGeospatial/` (`crs:binding` rel + `crs:position` + opaque WKT CRS prims).
- Python reference runtime `src/resolve_runtime.py` — the implementation-agnostic BEHAVIOR spec:
  `resolve_world_translation`, `anchor_frame`, `nearest_anchor`, `resolve_with_injection`
  (rigid ENU local-frame → ECEF, "inject don't bake").
- Engine seam `src/crs_engine.py` (pyproj as default `PyprojEngine`; `reproject()` + `local_frame_to_ecef()`).
- No-overfit proof: 7 datasets sub-mm vs closed-form geodesy, incl. the REAL converted NVIDIA
  Deutsche Bahn railway (rails on tiles) + 5 projected-CRS benchmarks. Renders: `railway_render.png`,
  `datasets_gallery.png`.
- **Visual==numeric by construction** (renders drawn from the SAME resolver output the assertions check).

## The goal of THIS phase
Build a **Hydra scene index** that performs geospatial resolution at render time — the
PRODUCTION form of what `resolve_runtime` does in Python. It filters a scene and rewrites the
`xform` of geospatially-bound prims (and dirties their children) so a renderer shows them in the
right place WITHOUT baking transforms into the layer.

## The reference design (NVIDIA `omniGeoSceneIndex`, Apache-2.0)
Vendored read-only at (sparse-checkout): `/tmp/oups/src/hydra-plugins/omniGeoSceneIndex/`
(repo: NVIDIA-Omniverse/OpenUSD-plugin-samples). ~2,564 LOC. Architecture (maps 1:1 to our Python):
- **`OmniGeospatialSceneIndex : HdSingleInputFilteringSceneIndexBase`** — observes a *flattened*
  input scene; `GetPrim`/`GetChildPrimPaths` wrap prims; `_PrimsAdded/_Removed/_Dirtied` keep a
  `SdfPathTable<HdSceneIndexPrim>` cache; `_DirtyHierarchy` propagates xform invalidation to
  children. ⇔ our `resolve_with_injection` + child re-anchoring.
- **`HdOmniGeospatialDataSource`** — intercepts the `xform` locator, `_ComputeGeospatialXform()`
  produces the ECEF/ENU transform; `computedPrim` (the anchored prim) + `computedDependent`
  (children that ride the anchor). ⇔ our `anchor_frame`.
- **API-schema adapters** (`UsdImagingAPISchemaAdapter`, registered in `plugInfo.json`):
  `…ReferencePositionAPIAdapter` (anchor) + `…LocalPositionAPIAdapter` (placed prim). ⇔ our
  reading of `crs:binding`/`crs:position`. NOTE the reference targets the OLD `OmniWGS84*` API
  schemas — OURS must adapt **`crs:binding`/`crs:position`** instead.

## ⚠️ Hydra has changed a lot since this reference (Aaron's warning — confirmed in source)
`geospatialSceneIndex.h` itself flags it: "with Render Delegate 2.0 and the ability to pull data
from a non-flattened scene, this implementation will have to be revisited to work with the
unflattened xform representation." So:
- Treat `omniGeoSceneIndex` as a **design reference, NOT compile-as-is**. Expect API drift in
  `HdFilteringSceneIndex`, data-source locators, `HdXformSchema`, the flattening assumption, and
  `UsdImagingAPISchemaAdapter` registration.
- FIRST task in the new session = pin the **target USD/Hydra version** and check the current
  scene-index / xform-schema API against it before writing code.

## "cf the Gaussians work" — NEED A POINTER
Aaron referenced a "Gaussians" effort to mirror (likely a 3D Gaussian Splatting Hydra / scene-index
or render-delegate prototype). NOT in this workspace and no memory hit. **Open question for the
resume session:** get the Gaussians repo/branch/path from Aaron — use it as the structural template
for (a) plugin scaffolding/CMake/`plugInfo.json`, (b) build & test harness, (c) how they handled
Hydra-version drift. Mirror its layout/conventions.

## Proposed implementation plan (ordered)
0. **Inputs to gather first:** Gaussians repo pointer (template); confirmed C++ build env (USD build
   from source or SDK — the codeless venv (usd-core wheel) has NO headers/libs for compiling
   plugins); target USD version.
1. **Scaffold** an out-of-tree Hydra scene-index plugin mirroring the Gaussians layout: CMake +
   `plugInfo.json` (register `HdSceneIndexPlugin` + the API-schema adapters), `api.h` export macros.
2. **Adapters** for OUR schema: read `crs:binding` (rel → CRS prim → WKT) + `crs:position` into
   Hydra data sources (replacing the `OmniWGS84*` adapters in the reference).
3. **Engine call:** the C++ side needs the CRS engine. Decide: link PROJ directly, or call out to a
   small engine lib mirroring `crs_engine.py`. Keep WKT opaque to USD (engine consumes it) — same
   contract as the Python side.
4. **Scene index:** filtering scene index that, for bound prims, computes the ENU→ECEF anchor xform
   (port `anchor_frame`) and overrides the `xform` locator; dirty children on change.
5. **Parity harness (the teeth):** load the SAME scenes used by `generalization_suite.py`
   (Earth-2, the converted railway, the 5 projected benchmarks) through the scene index and assert
   the resolved transforms match the Python runtime / closed-form geodesy to sub-mm. The Python
   suite is the oracle — C++ must agree with it. Reuse `out/railway_georef.usda` etc.
6. **Visual parity (optional, high-value):** if a renderer is available, capture an image and show
   the rails-on-tiles render matches `railway_render.png` — closes the "production path produces the
   same picture" loop.

## Hard constraints (carry over — do NOT violate)
- Push only to `aluk/geospatial-crs-prototype` (origin = `asluk/USD`). Never `mistafunk/USD`. No
  force, no PR, commit as `claw1` (`claw1@users.noreply.github.com`).
- Do NOT mention NanoUSD in any tracked writeup/code.
- Keep WKT opaque to USD; engine is the only consumer.
- Proofs non-circular + with teeth (numeric thresholds + negative controls); the Python runtime /
  closed-form geodesy is the oracle the C++ must match.
- nonclaw pushed an OV-PLC doc update but has NOT seen the multi-dataset/render work; HOLD briefing
  until reachable, then reconcile.

## Key paths
- This repo/dir: `/home/horde/.openclaw/workspace-identifiers/geo-usd/extras/usd/examples/usdGeospatial/`
- Codeless schema: `pxr/usd/usdGeospatial/`
- Reference plugin (read-only): `/tmp/oups/src/hydra-plugins/omniGeoSceneIndex/` (sparse checkout of
  NVIDIA-Omniverse/OpenUSD-plugin-samples; re-add with `git sparse-checkout add src/hydra-plugins`)
- Python venv (NO C++ build headers): `source /home/horde/.openclaw/workspace-identifiers/geo-usd/.venv/bin/activate`
- Memory: `memory/2026-06-24.md` (this session's detail), `MEMORY.md` (backlog index).

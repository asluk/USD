# usdGeospatial — running evidence for the Esri geospatial CRS proposal

<!-- slide:title subtitle="running evidence for the Esri geospatial CRS proposal" -->

## Supporting the Esri geospatial CRS proposal

This directory is running evidence for the Esri / AECO geospatial CRS proposal
(Tamrat-B/OpenUSD-proposals PR #1), authored with Simon Haegler (Esri). It is not a
competing standalone pitch: it mirrors the proposal's bones, stays name- and layout-aligned with
**Simon Haegler's (Esri) `geospatial-prototype`**, and backs the proposal's contested design calls
with working implementations.

The artifact deliberately keeps the same proposal shape a reviewer can compare against: a
`CoordinateReferenceSystem` prim, a binding surface for georeferenced prims, runtime resolution into
a shared Earth-Centered, Earth-Fixed / ECEF frame, and tests that measure the result. The key
difference from the Esri C++ branch is implementation strategy: this OpenUSD-side artifact resolves
bindings at runtime and keeps the authored scene coordinate-neutral, then demonstrates that choice
against the same design questions.

![usdview Storm auto-insert render (real render)](docs/railway_storm_autoinsert.png)

*Forward pointer to §[Proving viability: multiple independent implementations](#proving-viability-multiple-independent-implementations):
with the plugin on the path, usdview / Storm renders the railway at its resolved ECEF position.
This is the one real renderer image in the README.*

> **On the figures, up front (it matters for review):** every embedded *figure* in this document
> is a **Matplotlib plot** of coordinates the runtime computed (`matplotlib.use("Agg")`) — a
> diagram or scatter/line plot of *resolved numbers*, **not** a renderer screenshot. They prove
> the resolver is correct, not that a GPU drew them. The one exception, called out explicitly, is
> the **Hydra Storm render proof** (§[Proving viability: multiple independent implementations](#proving-viability-multiple-independent-implementations)),
> which *is* real renderer output.
>
> **What Matplotlib is doing here:** it is **not** "consuming a USD
> stage." It sits in the *same seat* as a Hydra renderer or an analytics pass — a plain **consumer
> of the resolver's output** (normalized ECEF). A compliant implementation produces the correct
> ECEF; what draws or analyzes it is agnostic. The USD-native version of exactly this point is the
> **usdview-on-earth2 Storm render** below — same resolved data, drawn by a real Hydra chain.

## Problem statement

Georeferenced data in USD must resolve to a shared real-world frame. A city scene, infrastructure
corridor, digital twin, or simulation cannot treat every source CRS as a private coordinate system:
multiple sources in multiple CRSs must co-register to the same physical places on Earth.

The open design tension is how CRS-driven placement reconciles with USD's existing transform
hierarchy. A geospatial anchor may place a site, while ordinary child transforms still place the
building, rail curve, sensor, glyph, or corner relative to that anchor. The desired behavior is that
both forms of placement survive together: CRS positions map to the shared Earth frame, and local
Cartesian editing remains meaningful below those anchors.

That is the problem this artifact tests: can a USD CRS data model state enough information for
different consumers to resolve the same authored scene into the same Earth frame, across geographic,
projected, and mixed-CRS assets?

## Separation of concerns

Terminology matters for the proposal. **USD** is the technology and standard. **AOUSD** is the
governing standards body that owns the normative specification: the data model and required
behavior. **OpenUSD** is one implementation, currently the canonical implementation in Pixar's
GitHub, not the standard itself.

The proposal should standardize the authored data and observable behavior: what a CRS prim means,
how a prim is bound to that CRS, how multiple bindings resolve, and where georeferenced prims land
in a shared real-world frame. OpenUSD-specific mechanics are implementation evidence. They are how
this repo proves the behavior can be built, not what makes the behavior normative.

The near-term path today is landing the proposal plus implementation in the Pixar OpenUSD repos and
shipping it in an official OpenUSD release. AOUSD governance migrates from Pixar over time, so the
standardization posture here is intentionally modest: the Python runtime is a runnable reference
that demonstrates the behavior and lets independent implementations check against it. It is not a
standards authority.

## The proposal in practice: system architecture

Now that the problem is clear, the proposed surface has two authored components and a runtime
contract around them:

- **`CoordinateReferenceSystem`** (typed prim): `crs:wkt` (OGC WKT2, authoritative) plus optional
  `crs:epsg`, `crs:displayName`, `crs:epoch` (dynamic CRS), `crs:gridFiles` (external PROJ grids).
- **`BindingAPI`** (single-apply, `canOnlyApplyTo Xformable`): `crs:position` — always
  `(lon/E, lat/N, h)` — plus `rel crs:binding` → a `CoordinateReferenceSystem`.

Behaviorally, that is the whole proposed surface. CRS meaning lives in the CRS prim. A bound prim
carries a CRS-local position. A consumer resolves the relationship, projects that position through
the selected CRS engine, and places the prim in the shared ECEF world while respecting ordinary
ancestor and child placement.

**Repository layout — two sibling directories, one schema:**

- **`usdGeospatial/`** (this directory) — the schema resources, the **Python reference runtime**
  (`src/resolve_runtime.py`), the Earth-2 data converter, the test suite, and the figures.
- **`../usdGeospatialSceneIndex/`** — the compiled **C++ Hydra scene-index plugin**, a second,
  illustrative runtime (modeled on the Gaussian-splat `hdParticleField` example — a reference, not
  a prescribed renderer path). It has its own README (Design, Files, Parity, Building, Environment).

The two runtimes are introduced here because the architecture is intentionally plural. The Python
runtime and the compiled C++ scene index share the same authored data and the same behavioral
contract, but use different implementation layers and language bindings. The **projection engine is
a registration seam** (`src/crs_engine.py`): PROJ / pyproj is the *default* registered engine; a
deployment could register a GPU engine (e.g. cuProj). WKT stays **opaque to USD** — only the engine
consumes it.

**Alignment with the Esri prototype.** The schema library is name- and layout-aligned with the Esri
C++ prototype — same library path `pxr/usd/usdGeospatial/`, same prims, same properties — so a
reviewer who knows one reads the other. The one difference is the design call explored in §[How
OpenUSD lets us do it](#how-openusd-lets-us-do-it) and §[Coexisting with the transform
hierarchy](#coexisting-with-the-transform-hierarchy): the Esri branch is a C++ typed schema whose
`Bind()` bakes placement into authored transform data; this variant resolves placement at runtime.

![tree alignment](docs/tree_alignment.png)

**Binding semantics — full MaterialBindingAPI parity.** Resolution rules mirror
`UsdShadeMaterialBindingAPI`: **strength** (`bindCRSAs` = weaker / strongerThanDescendants),
**purpose** (`crs:binding:<purpose>`), and **collection** (`crs:binding:collection:...`, where a
collection binding beats a direct binding at the same prim). The precedence ladder below is read
*live* from `resolve_runtime.crs_of_prim`; the figure self-asserts it equals the resolver, so it
cannot drift from the code.

![binding semantics](docs/binding_semantics.png)

## Proving viability: multiple independent implementations

Providing multiple independent implementations that agree is standard, often-required
standards-development practice. It shows that a proposed data model and behavior are specified
clearly enough to build more than once. Here, correctness and contract clarity are deliberately
separated: correctness is checked against independent geodesy authorities; implementation agreement
shows the contract is unambiguous enough to reproduce.

<!-- slide:section title="The proofs" subtitle="Four things an independent reviewer can check." -->

Lead with these proofs; everything after is *how* and *why*. Each is checkable by an independent
reviewer and non-circular — ground truth is closed-form WGS84 geodesy (first principles) and
**NOAA NCAT** benchmark coordinates, never a parallel PROJ call graded against itself.

**1 — No overfit: a real third-party asset on real tiles.** The **NVIDIA OpenUSD-plugin-samples
Deutsche Bahn railway** (Apache-2.0; ~1,470 track curves on 3 geospatial tiles near Hamburg) is
authored in the *original Omniverse* geospatial schema (`omni:geospatial:wgs84:*`, lat-first).
`src/convert_omni_geospatial.py` converts it to our `crs:binding`/`crs:position` form and it
resolves — leaves *and* its anchor + Cartesian-curve subtree via injection — with **no runtime
changes**. Data we did not author, in a schema we did not design.

<!-- slide:image src="docs/railway_render.png" eyebrow="Proof · no overfit" title="Real third-party asset on real tiles" caption="Matplotlib plot (not a render): an external Deutsche Bahn railway (~1,470 curves) authored in the original Omniverse schema, converted to crs:binding/crs:position, resolved onto three real geospatial tiles near Hamburg." -->

![railway resolved onto tiles (Matplotlib plot)](docs/railway_render.png)

**2 — Co-registration against an independent authority.** The same monument near the Empire State
Building, authored three independent ways — geographic (EPSG:4979), UTM 18N (EPSG:32618), and
NY State Plane (EPSG:32118) — each from independent **NOAA NCAT** coordinates (not by inverting one
transform) — all resolve through the schema to the **same ECEF point**, matching closed-form WGS84
geodesy to **worst ~0.54 mm** (the residual is real conformal-projection grid noise). The negative
control (resolve while *ignoring* `crs:binding`) collapses ~6,400 km off the globe. An axis-order or
geodesy bug has nowhere to hide, because the reference side makes no `always_xy` assumption to
cancel against.

<!-- slide:image src="docs/coherence.png" eyebrow="Proof · co-registration" title="Three CRSs, one ECEF point" caption="The same monument authored three ways (geographic / UTM 18N / NY State Plane) from independent NOAA NCAT coordinates co-registers to one ECEF point to worst ~0.54 mm — vs closed-form WGS84 geodesy, not a parallel PROJ call. Red blob = negative control (bindings ignored)." -->

![coherence](docs/coherence.png)

> **Scope of this proof:** graticule + benchmark co-registration, **not** a draped satellite /
> terrain raster basemap (roadmap). It demonstrates **point / leaf** coherence; **anchor +
> Cartesian-subtree** coherence is shown by anchor injection (§[Coexisting with the transform
> hierarchy](#coexisting-with-the-transform-hierarchy)).

**3 — One schema, two independent runtimes (0.0 mm).** *Correctness* is carried by Proof 2: the
match against **NOAA NCAT + closed-form WGS84 geodesy**, which are independent authorities, not this
proposal's own code. What *this* proof adds is different: two implementations agreeing to 0.0 mm
shows the **contract is unambiguous enough to build twice and get the same answer** — robustness,
not independent proof that the semantics are correct. Two implementations of the same misreading
would also agree; that is why Proof 2 exists. The point is that the contract is *data*, not one
implementation — so any number of runtimes must land on the same world. The Python reference and the
compiled **C++ Hydra scene index** share *nothing* but the authored schema (different language,
pipeline layer, and PROJ binding), yet resolve the same authored stage to the same world.
`../usdGeospatialSceneIndex/run_parity.sh` reports:

- **CRS engine vs closed-form geodesy (the correctness authority):** 9/9 datasets, **0.0 mm**
- **Stage-level resolver vs Python reference + ground truth:** 30/30, **0.0 mm**
- **Hydra scene index (xform pulled via `HdXformSchema`, as a renderer would) vs reference + ground
  truth:** 30/30, **0.0 mm**; negative control: **without** the scene index, stock Hydra puts
  these georef prims at the origin.

Visual parity on the real railway: across **3,526 rail vertices** + tile corners the two runtimes
agree to **median 0.40 mm, worst 0.68 mm**; the `testUsdGeospatialRuntimeParity` ctest converts the
railway asset, dumps the compiled scene index's Hydra xforms, and **fails the build if the
per-vertex disagreement exceeds 1 mm** (`fig_runtime_parity.py --check`).

<!-- slide:image src="docs/multi_runtime.png" eyebrow="Proof · contract not implementation" title="Two independent runtimes, 0.0 mm" caption="Robustness / interoperability pass (correctness is Proof 2 vs NCAT + closed-form geodesy): the Python reference runtime and the compiled C++ Hydra scene index resolve the same authored stage to the same world, agreeing to 0.0 mm — the data contract is unambiguous enough to build twice the same way. A third runtime plugs into the same seam." -->

![one schema, two runtimes](docs/multi_runtime.png)

![Python vs Hydra transforms, same stage (Matplotlib plot)](docs/runtime_parity.png)

**4 — It just works in usdview (real Hydra Storm render).** Beyond the plots: with only the built
plugins on `PXR_PLUGINPATH_NAME` — **no application code, no hand-built scene-index chain** —
opening the georef scene in **usdview** (or `usdrecord`) draws the railway at its correct
ECEF position via Storm. The `crs:` data flows through Hydra and an auto-inserted scene index
resolves it. This is a *real renderer image*, not a plot, and the hero image in §[Supporting the
Esri geospatial CRS proposal](#supporting-the-esri-geospatial-crs-proposal) is this proof image.

<!-- slide:image src="docs/railway_storm_autoinsert.png" eyebrow="Proof · real render, auto-insert" title="It just works in usdview (Storm)" caption="Real Hydra Storm render (not a plot): with the plugin on the path, the railway auto-resolves at its ECEF position — no app code. Negative control (plugin removed): railway absent. The auto-insert path matches the reference 30/30 at 0.0 mm (testHydraAutoParity)." -->

## How OpenUSD lets us do it

<!-- slide:section title="The design call" subtitle="OpenUSD implementation choices that keep the authored scene neutral." -->

The USD proposal is about authored data and behavior. The following are OpenUSD-specific
implementation choices that make this artifact buildable and reviewable today.

**Implementation detail 1 — codeless.** In OpenUSD, `skipCodeGeneration = true` means
`usdGenSchema` emits only `generatedSchema.usda` + `plugInfo.json` (no compiled C++ types); USD
loads the typed prim and the applied API from those, so `crs:*` properties authored with
`custom=False` are **truthfully** schema-defined. The data model does not "know" it is codeless.
Codeless is an OpenUSD packaging choice that keeps the schema a pure data contract and avoids
forcing every implementation to reimplement compiled OpenUSD types.

<!-- slide:text eyebrow="OpenUSD implementation detail" title="Codeless schema" body="Pure-data schema: a CRS prim + a binding API, `skipCodeGeneration=true` (no compiled types). | All resolution behavior lives in the example runtimes, not the schema. | Same shape as the landed Gaussian / particleField contribution: schema + sample runtime(s) + converter + docs. | Two runtimes here: Python `resolve_runtime.py` and a C++ Hydra scene index that auto-inserts into usdview." -->

This mirrors the shape of the landed OpenUSD Gaussian / `hdParticleField` contribution —
*schema + sample runtime(s) + data converter + docs, shipped together*, with the schema as pure
data and all behavior in the example(s). Here the runtimes are the Python `resolve_runtime.py` and
the C++ Hydra scene index, and the dataset is real OSS Earth-2 / GFS `t2m`.

**Implementation detail 2 — resolve, don't bake.** The behavioral constraint comes first:
**binding a CRS must not mutate authored transform data.** The specific issue this implementation
avoids: `SetResetXformStack` writes to scene description, and every downstream consumer then
inherits that authored choice. Baking a `resetXformStack` answers the relationship to
the transform hierarchy by replacing it at authoring time, at the cost of a non-neutral scene and
lost composability.

<!-- slide:text eyebrow="Replace · wrap · or coexist?" title="Resolve, don't bake" body="Binding a CRS must not mutate authored transform data. | Baking `resetXformStack` into a layer violates that constraint: every downstream consumer inherits it. | OpenUSD lets this implementation resolve the relationship at runtime while the authored scene stays coordinate-neutral. | Proven, not argued: the baked Esri scene and our neutral scene land the same corner to 0.0 mm." -->

`src/testenv_equivalence.py` rebuilds the Esri prototype's New York / MoMA scene two ways — the
baked `resetXformStack` + stacked `xformOp:translate`, and our neutral `crs:binding` +
`crs:position` — and the building corner lands at the **same ECEF point to 0.0 mm**, with the
neutral scene carrying **no xformOps at all** (`testenv/world_baked_resetxformstack.usda` vs.
`testenv/world_neutral_relbinding.usda`).

![design equivalence](docs/design_equivalence.png)

OpenUSD lets us honor the constraint at runtime instead. The compiled Hydra scene index *does* set
`resetXformStack = true` on the xform it injects — which can look like the very thing this design
rejects. It is not. What the design rejects is `resetXformStack` **authored into a layer**. In the
scene index, the flag sits on a **computed, transient Hydra data source**, never written into the
authored scene: the resolver has already composed ancestor transforms and returns the prim's full
world (ECEF) matrix, so the flag only tells Hydra *not to re-compose that matrix under its parents*
at flatten time. The authored stage carries **zero `resetXformStack` and zero `xformOp`** — only
`crs:` properties (read `testenv/world_neutral_relbinding.usda` directly).

The punchline for standardization work is practical: pure data plus a neutral authored scene are
precisely what enabled the two independent implementations in §[Proving viability: multiple
independent implementations](#proving-viability-multiple-independent-implementations). They read
the same authored data, implement the same behavioral contract, and check their outputs against the
same runnable reference.

## Coexisting with the transform hierarchy

<!-- slide:text eyebrow="Coexisting with the transform hierarchy" title="Anchor injection: inject, don't bake" body="The authored scene stays coordinate-neutral; a child remains an ordinary local Cartesian placement relative to a georeferenced anchor. | The runtime injects the anchor's rigid local-frame→ECEF basis (full ENU orientation) at read time. | The subtree then combines under it as ordinary `UsdGeomXformable` behavior — nothing baked into the layer. | `resetXformStack` lives only on a transient, computed Hydra data source, never the authored scene." -->

The behavior the reader gets is simple: the authored scene stays coordinate-neutral, and a child's
local placement remains relative to a georeferenced anchor at read time. A building can be modeled
in local metres below a site anchor; hand-authored child transforms remain ordinary Cartesian
authoring; the CRS relationship supplies the missing Earth placement only when a resolver consumes
the scene.

The mechanism is **anchor injection: inject, don't bake**. The design handles georeferenced
*leaves* (each prim carries its own `crs:position`) and the harder case — the one stock USD gets
wrong — of a georeferenced **anchor** with an ordinary, non-georeferenced **Cartesian subtree** (a
building modelled in local metres). A plain child has no `crs:position`, so standard composition
renders it **at the world origin** — the anchor's georeferencing lives in `crs:position`, which the
xform stack never reads.

The fix is to **inject** the anchor's frame at runtime, not bake it: the anchor's `crs:position` +
bound CRS define a **rigid local-frame → ECEF transform**, and the subtree composes under it as
ordinary USD.

- **Orientation, not just position.** The injected frame is the full ENU / topocentric basis at the
  anchor (east-north-up), not merely the translated ECEF point. A subtree's local `+Z` must point
  along the *ellipsoidal normal*, which at NYC is ~49° off ECEF `+Z` — a position-only resolver
  lays every asset on its side everywhere but the pole. (`src/crs_engine.py` supplies this basis.)
- **Transient, never written.** Injection happens in a *computed* representation
  (`resolve_runtime.resolve_with_injection`); the authored stage is untouched.
- **Proven against closed-form geodesy** (`src/test_anchor_injection.py`): a building 1000 m E /
  500 m N and a roof +20 m up land to **0.0 mm**; position-only is **410 m** wrong; stock USD
  without injection puts the child **6.4×10⁶ m** off — the origin gap, quantified.
- **Float32 localization falls out for free.** The large magnitude lives in the double-precision
  injected anchor (~6.4×10⁶ m); the asset's vertices stay small float32 *local* offsets.
  `src/test_float32_localization.py` shows absolute-float32 ECEF loses **162 mm** at that magnitude
  while localized float32 keeps **0.0003 mm** — a ~**480,000×** improvement.

Hand-tweaks survive: because we inject-don't-bake, the authored subtree stays clean Cartesian, so a
DCC's native TRS gizmos Just Work on children — a point in favor of coexist over baked-
`resetXformStack`, where hand-edits fight a baked matrix.

## Coordinate frame: projected vs. geographic anchors

<!-- slide:text eyebrow="Combine in the CRS-implied frame" title="Projected vs geographic anchors" body="A GEOGRAPHIC/ECEF anchor's child offsets are local metres → combine through the anchor's true-ENU basis (orientation matters; local +Z = ellipsoidal normal). | A PROJECTED (UTM/State-Plane) anchor's child offsets live in the grid plane → combine IN-PLANE (grid add + reproject), NOT through ENU. | UTM grid axes differ from true ENU by grid-convergence + point-scale — lifting grid offsets through ENU bends them ~4.86 m over a ~420 m lever. | Same neutral authored scene; the runtime picks the frame from the bound CRS type. Proven 0.0 mm both ways against closed-form geodesy." -->

Coexist has one correctness rule the runtime must honor, because it is where a naïve implementation
goes wrong: **combine a child's offsets in the frame its anchor's CRS implies.**

- A **geographic / geocentric (ECEF) anchor** carries child offsets in local metres → combine
  through the anchor's **true-ENU / topocentric basis** (the NYC case above).
- A **projected (UTM, State Plane, …) anchor** carries child offsets in the anchor's **grid plane**
  → combine **in-plane** (add the offset to the anchor's grid coordinates and reproject), **not**
  lifted through ENU. UTM grid axes differ from true ENU by grid convergence + point scale, so
  lifting grid-authored offsets through ENU introduces a real error (~**4.86 m** over a ~420 m
  anchor→corner lever in a UTM-17N-under-UTM-30N test).

The authored scene is identical either way; the runtime selects the frame from the bound CRS type
(`crs_engine.is_projected`). An adversarial head-to-head enforces this rule
(`test_coexist_vs_baked.py`): it rebuilds Simon Haegler's multi-CRS POC scene (MoMA in
NAD83/UTM-17N under a WGS84/UTM-30N anchor) both baked and neutral and measures each against an
independent closed-form pyproj ground truth. Combined in the CRS-implied frame, both approaches land
the corner at the same ECEF point to **0.0 mm**; combine a projected anchor's child through the
true-ENU basis instead of its grid plane and the corner lands 4.86 m off — the test asserts the
frame selection so that error cannot pass silently.

## Non-geometric georeferenced data

<!-- slide:section title="Non-geometric data" subtitle="A common geospatial case: data with no shape. Visualize it with USD composition arcs — without touching or duplicating the data." -->
<!-- slide:text eyebrow="A first-class use case" title="Non-geometric georeferenced data" body="Much geospatial data has NO intrinsic shape: scalar fields (temperature, elevation), sensor/telemetry networks, survey benchmarks. In USD it is a prim carrying `crs:position` + a value, no geometry. | Visualization is a CHOICE, not part of the data — so add it via USD COMPOSITION ARCS: keep the dataset pristine in a base layer; a separate overlay layer subLayers it and adds marker glyphs as geometry-only `over`s. | ZERO `crs:*` re-authored; the base stays byte-identical; pull the overlay and you are back to pure data. | The glyphs are Cartesian children at each prim's local origin — the auto-inserted scene index places them via the SAME anchor-injection path from §7. Marker size is a stated DISPLAY parameter (like a scatter's point size), and the overlay can be sparse." -->

A large share of real geospatial data has **no intrinsic shape**: a GFS temperature field, a
sensor/telemetry network, LiDAR-derived measurements, survey benchmarks. In USD that is honestly a
prim carrying `crs:position` (+ a data value like `primvars:t2m`) and **no geometry** — the data is
not a mesh. Visualizing it is a *choice you make to understand non-visual data*, not something the
data *is*. This is a common, first-class use case, and the schema supports it cleanly.

The right way to add a visualization is **USD composition arcs** (`subLayers` + `over`), not baking
geometry into the dataset. This is the USD composition meaning of the word, distinct from the
coordinate-frame rule in §[Coordinate frame: projected vs. geographic anchors](#coordinate-frame-projected-vs-geographic-anchors):

- The **base layer** stays the pristine non-geometric dataset (e.g. `out/earth2_georef.usda`:
  7,320 `crs:position` samples of GFS `t2m`, zero geometry).
- A separate **overlay layer** (`src/visualize_field_glyphs.py` writes `out/earth2_glyphs.usda`)
  `subLayers` the base and adds marker glyphs as **geometry-only `over` prims** — it re-authors
  **zero `crs:*`**. The georeferencing composes down from the base:

```usda
#usda 1.0
(
    subLayers = [
        @earth2_georef.usda@          # the pristine, non-geometric dataset
    ]
)

over "World" { over "GeoSamples" {
    over "p_0_0" {                    # 'over', not 'def' — no crs:* restated, no prim duplicated
        def Points "glyph" {
            point3f[] points = [(0, 0, 0)]   # at the georef prim's LOCAL origin
            float[] widths = [60000]          # a stated DISPLAY parameter (like scatter s=), not a coordinate
            color3f[] primvars:displayColor = [(0.78, 0.69, 0.04)]
        }
    }
}}
```

Because each glyph is a Cartesian child at the georef prim's local origin, the auto-inserted scene
index resolves it through the **same anchor-injection path** proven in §[Coexisting with the
transform hierarchy](#coexisting-with-the-transform-hierarchy) and used by the railway's Cartesian
subtree — **no new code path**. The base dataset is never opened for write (byte-identical
before/after), the overlay is fully **removable**, and the same physical data is never
**duplicated**. It also doubles as a proof that the schema composes correctly across USD layers
(`subLayers` + `over`).

The payoff shows in the cross-visualizer parity: the *same* non-geometric field, resolved once,
drawn by two independent visualizers — a Matplotlib scatter and a Hydra **Storm** render of the
composed overlay — landing on the same globe. (Glyph coverage differs by construction:
Matplotlib's round `s=` dot vs. Storm's `UsdGeomPoints` marker; the *resolved positions* are
identical, the glyph style is a disclosed display choice.)

<!-- slide:image src="docs/globe_visualizer_parity.png" eyebrow="Two visualizers, one field" title="Same non-geometric data, matplotlib vs Storm" caption="The earth2 GFS t2m field (7,320 crs:position samples, no geometry) visualized two ways: a Matplotlib scatter (left) and a Hydra Storm render of a composition-overlay of marker glyphs (right), placed by the auto-inserted scene index. Same resolved positions; glyph style is a disclosed display choice." -->

![globe cross-visualizer parity](docs/globe_visualizer_parity.png)

### Same runtime, many CRSs — the anti-overfit position set

<!-- slide:image src="docs/multiCRS_glyph_renders.png" eyebrow="Proof · not overfit" title="One runtime, five CRS families, both hemispheres" caption="Matplotlib plot (not a render): where each locale's authored point resolves in ECEF, through ONE code path — NYC (UTM 18N), Sydney (UTM 56S), Wellington (NZTM2000), Quito (UTM 17S, ~equator), Svalbard (UTM 33N, ~78N). The only thing that changes between locales is the authored EPSG; the five points land 2,200+ km apart on the globe. Verified sub-mm vs closed-form WGS84 geodesy in generalization_suite.py." -->

The numeric no-overfit proof (§[Proving viability: multiple independent implementations](#proving-viability-multiple-independent-implementations))
is broad but stated in *numbers*. The figure below makes the same point *visible* without inventing
geometry: it plots where each locale's authored point **resolves** in ECEF through **one code path**
— lon/lat → the locale's projected CRS → ECEF, via PROJ (the registered default engine). The five
span five CRS families, both hemispheres, and equator-to-78°N — **NYC** (UTM 18N), **Sydney** (UTM
56S), **Wellington** (NZTM2000), **Quito** (UTM 17S, ~equator), **Svalbard** (UTM 33N, ~78°N) —
and the **only** thing that differs between them is the authored EPSG. The resolved points land
2,200+ km apart across the globe (no per-CRS special-casing anywhere), and each is verified sub-mm
against closed-form WGS84 geodesy in `generalization_suite.py`.

![multi-CRS resolved positions (Matplotlib plot)](docs/multiCRS_glyph_renders.png)

## Detecting and flagging invalid geospatial inputs

<!-- slide:section title="Detecting invalid inputs" subtitle="Neutral authoring keeps CRS intent inspectable, so malformed geospatial inputs can be detected and flagged." -->
<!-- slide:text eyebrow="Detectable and recoverable" title="Malformed geospatial inputs can be flagged" body="A neutral authored scene PRESERVES the CRS intent a validator needs; a baked scene has already collapsed that intent into a matrix. | The system can detect malformed geospatial inputs and flag them before they become silent placement errors. | G1 anchor-vs-child 418.9 m → 0 mm; G2 wrong frame 4.86 m → 0 mm; G3 no marker 6,369 km silent → detect-and-refuse. | `verify.py` is the validator today; a codeless `usdchecker` plugin is the near-term deliverable." -->

A neutral authored scene keeps `crs:binding` + `crs:position` **inspectable**, which is what makes
malformed geospatial inputs detectable. A baked scene has already collapsed CRS intent into a
matrix. The capability we want is therefore positive and concrete: the system can **detect**
malformed geospatial inputs and **flag** them before they become silent placement errors.

`verify.py` is the runnable validator today; a codeless, `usdchecker`-discoverable validator
**plugin is a near-term deliverable, not just a roadmap item**. That plugin is the mechanism that
turns these checks from *detectable-in-principle* into *detected-in-practice* in an ordinary
`usdchecker` run.

> **The tradeoff we are making with eyes open.** Coexist deliberately gives up the "open the stage
> and it just works" property *for a CRS-unaware consumer*: such a consumer sees a coordinate-neutral
> scene and, without the resolver, places prims wrong. We accept this because the alternative is
> worse. Baking *looks* like "just works," but its failure mode is **silent and unrecoverable** — the
> CRS intent is already collapsed into a matrix, so a wrong or mismatched assumption cannot be
> detected or undone. Coexist's failure mode is **loud and recoverable**: the `requires-CRS` marker
> (G3) + the `usdchecker` validator let an unaware consumer *detect and refuse* rather than
> mis-place, and the authored scene still carries the CRS intent a validator (or a later resolver)
> can act on. Loud-and-recoverable over silent-and-unrecoverable is the whole trade.

`src/test_illformed_assets.py` authors a deliberately **ill-formed asset** for each check, shows the
concrete failure against independent closed-form geodesy, then shows the **minimal authoring fix**
and re-measures (figures by `src/render_illformed.py`; left = broken, right = fixed).

<!-- slide:image src="docs/illformed_gallery.png" eyebrow="Broken → fixed, measured" title="What breaks in coexist, and the fix" caption="G1 anchor-vs-child 418.9 m → 0 mm · G2 wrong frame 4.86 m → 0 mm · G3 no marker 6,369 km silent → detect-and-refuse" -->

1. **G1 — anchor-vs-child ambiguity.** *Broken:* `/World/NewYork/MoMa/Corner` authored with its
   **own** `crs:binding` + `crs:position` (as if an independent georeferenced leaf) and parented
   under the building expecting relative placement — it jumps to its own CRS point, **418.9 m** off.
   *Fix:* delete the corner's binding/position and author it as an ordinary Cartesian child
   (`double3 xformOp:translate = (50, 100, 30)`) → **0.000 mm**. *Validator:* `verify.py` check
   **A2** flags a georef prim that also bakes an xformOp; a `crs:position`-under-`crs:position`
   nesting without an override binding is the smell.

![G1 anchor-vs-child: broken 418.9 m off vs fixed 0 mm](docs/illformed_g1.png)

2. **G2 — wrong composition frame.** *Broken:* a **projected** (UTM-17N) anchor's child offsets
   combined through the anchor's **true-ENU** basis. Grid convergence + point-scale bend them
   **4.86 m** over a ~418 m lever. *Fix:* combine the offset **in the grid plane** and reproject →
   **0.000 mm**. *Validator:* the runtime selects the frame from the bound CRS type
   (`crs_engine.is_projected`); a validator asserts the two agree.

![G2 wrong composition frame: broken 4.86 m off vs fixed 0 mm](docs/illformed_g2.png)

3. **G3 — no requires-CRS marker.** *Broken:* a coexist scene with no stage marker, opened by a
   **CRS-unaware** consumer (plain `UsdGeom.XformCache`, no resolver), silently places the building
   at its bare local offset — **6,369 km** from truth, with no error. *Fix:* stamp
   `customLayerData['crsResolutionRequired'] = true`; a conformant consumer detects it and
   **refuses / defers** to a resolver. *Validator:* `verify.py` check **G** fails any stage that
   carries `crs:binding` without the marker.

![G3 no requires-CRS marker: broken 6369 km off silently vs fixed detect-and-refuse](docs/illformed_g3.png)

**On the requires-CRS marker: expect pushback (and a layer-vs-prim debate).**

<!-- slide:text eyebrow="Anticipated debate" title="The marker: a tradeoff worth having" body="A 'requires-CRS' marker is the honest cost of coordinate-neutral coexist: it is what lets an unaware consumer fail LOUD instead of silently misplacing. | Expect pushback — it adds a discovery obligation, and a non-conformant consumer still ignores it (it is a contract, not an enforcement). | If embraced, the next debate is WHERE it lives: layer metadata (customLayerData) vs a prim-level applied schema. | Our lean: a stage/layer-level signal for cheap detect-and-refuse, optionally refined per-prim; but this is squarely a WG call." -->

- **Why it exists.** Coordinate-neutral authoring preserves composability and keeps the scene
  inspectable, but it is also what makes a CRS-unaware consumer misplace content silently (G3). The
  marker is the price of neutrality: a cheap signal that lets such a consumer **detect-and-refuse**
  rather than render 6,000 km off. The baked approach doesn't need it — but pays instead with a
  non-neutral scene and an *even worse* silent failure (the head-to-head measured ~6.4×10⁶ m for
  neutral vs ~1.0×10⁷ m for baked when a grid `xformOp` is misread as ECEF).
- **The fair objections.** It adds a discovery obligation to every conformant consumer; a
  *non*-conformant consumer still ignores it (a marker is a **contract, not enforcement**); and it
  is one more thing an author can forget — hence the `verify.py` **G** check, caught at authoring
  time, not render time.
- **The layer-vs-prim question.** Even if accepted, *where* it lives is a genuine debate: **layer /
  stage metadata** (`customLayerData['crsResolutionRequired']`, used here) is one cheap O(1) lookup
  before traversal, but coarse and free-form; a **prim-level applied schema** is typed, validatable,
  and local, but a consumer must traverse to discover it. **Our lean (a WG call, not a decree):** a
  stage/layer-level signal for the cheap up-front check, optionally refined by prim-level typing
  where per-subtree granularity matters. We implemented the layer-metadata form; the prim-schema
  form is a small addition.

## Runtimes, tests, and verifying the results

<!-- slide:section title="One schema, two runtimes" subtitle="The schema is the contract; the behavior is plural." -->

**Two runtimes, one schema.** The Python runtime is the runnable reference that demonstrates the
behavior; the point of this OpenUSD implementation strategy is that the contract is authored data,
so any number of runtimes can resolve the same authored stage and check that they land on the same
world. The two ship together and share *nothing* but the schema:

- **(A) Python reference** — `src/resolve_runtime.py`, projecting via
  `crs_engine.PyprojEngine` (pyproj / PROJ). Traverses bindings (inheritance, strength, purpose,
  collection), reprojects, composes ancestor Cartesian transforms, and (for anchors) injects the
  rigid local-frame → ECEF transform — without touching the authored xform stack.
- **(B) Compiled Hydra scene index** — `../usdGeospatialSceneIndex` (C++), an
  `HdSingleInputFilteringSceneIndexBase` that wraps `Xformable` prims, overrides the `HdXformSchema`
  matrix locator a renderer pulls, and dirties descendants on anchor change — projecting via a
  PROJ-linked C engine (`GeoCrsEngine`). Different language, pipeline layer, and engine binding; it
  auto-inserts into usdview (§[Proving viability: multiple independent implementations](#proving-viability-multiple-independent-implementations)).

The auto-insert path is OpenUSD-specific plumbing. `crs:` properties are custom attrs/rel on a
codeless schema, so they are absent from the default Hydra stream. A **keyless
`UsdImagingAPISchemaAdapter`** (`apiSchemaName ""`, modeled on `coordSysAPIAdapter` and NVIDIA's
`omniGeoSceneIndex`) surfaces `crs:position`/`crs:binding`/`crs:wkt` *into* Hydra for every prim;
the scene index resolves entirely from the Hydra data stream. *Scope note (stated, not hidden):*
the auto path resolves **direct** `crs:binding` (+ nearest / stronger); collection- and
purpose-based strength are resolved via the stage path — the neutral railway / earth2 scenes use
direct bindings, which is what auto-insert exercises. The resolver is thread-safe: its
`UsdGeomXformCache` is mutex-guarded, so Storm can sync rprims across TBB threads without a
double-free.

<!-- slide:image src="docs/runtime_parity.png" eyebrow="Proof · sub-mm parity" title="Same stage, two runtimes, quantified" caption="Matplotlib plot: Python vs Hydra transforms on the same authored railway stage — 3,526 rail vertices + tile corners agree to median 0.40 mm, worst 0.68 mm. The testUsdGeospatialRuntimeParity ctest fails the build if disagreement exceeds 1 mm." -->

The takeaway is the schema claim itself: **the schema is the contract; the behavior is plural.** A
third runtime (OpenExec, a GPU / cuProj engine, an Omniverse runtime) plugs into the same seam and
can be checked against the same authored data and runnable reference.

<!-- slide:text eyebrow="Reproducible · cross-platform" title="The second runtime builds like any USD example" body="`build_usd.py --usdGeospatial` fetches and builds PROJ, then the C++ Hydra plugin, behind one opt-in flag — the `hdParticleField` pattern, no bespoke setup. | Parity is a `ctest` (`testUsdGeospatialParity`): CRS engine + stage resolver + Hydra scene index + stage-free auto-insert, all 0.0 mm. | Validated on Linux **and** Windows — the contract builds twice, the same way, on two platforms." -->

And it builds like any other OpenUSD example: `build_usd.py --usdGeospatial --examples` fetches and
builds PROJ and the C++ Hydra plugin behind one opt-in flag — the same shape as `hdParticleField`,
on Linux and Windows alike — and `ctest -R testUsdGeospatialParity` runs the whole parity proof
(CRS engine, stage resolver, Hydra scene index, and the stage-free auto-insert path). The second
runtime isn't a Linux-only lab artifact; it's a normal, opt-in part of the build.

### Where the Python reference runtime sits

<!-- slide:text eyebrow="No exact precedent — by design" title="Where the Python reference runtime sits" body="It is a runnable reference: given this authored stage, it demonstrates where each prim should end up, pinned to closed-form geodesy. | NOT the specification: the normative behavior belongs in prose proposed into the Esri proposal; Python demonstrates it, not replaces it. | NOT proposed for USD core, NOT a runtime dependency, NOT Python-in-the-render-loop, NOT the prescribed consumer. | Precedent: AOUSD's core-spec-supplemental — Python sample impls + a compliance framework, spec normative and impl illustrative — is the analogy, not a claim of standard authority." -->

Because the schema is **codeless**, the resolution behavior must live *somewhere* outside the
schema. That behavior should be **normative as prose** in the Esri proposal; `resolve_runtime.py` is
that same behavior written down once in the most readable *runnable* form: a pure-Python,
dependency-light reference — pinned to closed-form geodesy — for "given this authored stage, where
does each prim end up?" It is a runnable reference, not the specification: compliant
implementations should be able to **match its output**, but the source of truth is the prose
contract, not the Python. (Note this is separable from codelessness — a *typed* schema would need
the same behavior contract; codeless just makes it unavoidable to state one.) It is **not** proposed
for USD core, **not** a runtime dependency, **not** Python-in-the-render-loop, and **not** the
prescribed way to consume the schema. A real consumer (Hydra scene index, OpenExec, an Omniverse /
native runtime, a GPU cuProj path) implements the same contract in its own setting — the Python is
the readable reference they can check against.

There isn't a clean precedent for this exact artifact *in the OpenUSD repo* — but there is one right
next door. OpenUSD already ships reference/example code in Python under `extras/usd/examples/`
(`usdSchemaExamples`, `usdResolverExample`, …); and **AOUSD's `core-spec-supplemental`** is close in
shape — Python sample implementations plus a compliance framework, with the **spec normative and
the implementation illustrative**. We follow that model as an analogy: a runnable reference for a
codeless schema whose behavior is deliberately external, with the normative statement living in
prose. That placement is a deliberate design choice, and one we'd specifically like the working
group's read on.

### Tests — all green, all with teeth

Every test is openable and runnable; each has a real negative control or an independent ground
truth.

- `verify.py` — the runnable validator: confirms the schema is truthfully codeless (`crs:*` with
  `custom=False` resolve as schema-defined), plus authoring checks (incl. the G marker).
- `multi_crs_example.py` — negative control: ignoring bindings diverges >100 km.
- `test_ancestor_compose.py` — ancestor-transform composition; negative control diverges ~7,482 km.
- `test_binding_semantics.py` / `test_binding_composition.py` — MaterialBinding-style precedence
  (strength, purpose, collection) and cross-layer / list-edit composition.
- `test_dynamic_crs.py` / `test_grid_files.py` — dynamic-CRS (`crs:epoch`) and external PROJ grids.
- `test_anchor_injection.py` — georef anchor + Cartesian subtree lands & orients to 0.0 mm;
  position-only 410 m wrong; stock USD 6.4×10⁶ m off.
- `test_float32_localization.py` — localized float32 ~480,000× more precise than absolute float32.
- `test_coexist_vs_baked.py` — neutral reproduces the baked approach to 0.0 mm; found the
  projected-anchor composition rule.
- `test_illformed_assets.py` — G1/G2/G3 broken→fixed, each measured against closed-form geodesy.
- `generalization_suite.py` — 7 diverse datasets (incl. the real NVIDIA railway), all sub-mm.
- `testenv_equivalence.py` — design equivalence vs the baked-`resetXformStack` scene (0.0 mm,
  neutral scene has zero xformOps).
- `render_figures.py` — the coherence figure self-asserts sub-mm co-registration.
- `ctest -R testUsdGeospatialParity` (cross-platform; also `run_parity.sh`) — the compiled C++ scene
  index: CRS engine 9/9, stage resolver 30/30, Hydra SI via `HdXformSchema` 30/30 — all 0.0 mm;
  negative control: stock Hydra puts georef prims at the origin. `testHydraAutoParity` adds the
  stage-free auto-insert path (30/30).
- `ctest -R testUsdGeospatialRuntimeParity` — the railway two-runtime gate: converts the real
  railway asset, dumps the compiled scene index's Hydra xforms, and runs `fig_runtime_parity.py
  --check`, which fails the build if the Python-vs-Hydra per-vertex disagreement exceeds 1 mm
  (measured: median 0.40 mm, worst 0.68 mm across 3,526 rail verts).
- `pxr/usd/usdGeospatial/regen-schema.sh --check` — schema resources are in sync.

### Running — two paths

**The codeless Python path (no external renderer)** — any Python with `pxr` (a usd-core wheel or a
USD build) plus the base packages in `requirements.txt` (`pyproj`, `numpy`, `matplotlib`, `Pillow`).
These scripts are self-contained — they carry their own committed data and self-assert:

```bash
cd extras/usd/examples/usdGeospatial
pip install -r requirements.txt         # base deps (+ xarray/netCDF4 for the optional Earth-2 step)
python3 src/testenv_equivalence.py
python3 src/test_anchor_injection.py    # georef anchor + Cartesian subtree (inject-don't-bake)
python3 src/generalization_suite.py     # 7 diverse datasets vs closed-form geodesy (no overfit)
python3 src/fig_multicrs_positions.py   # anti-overfit figure: 5 CRS families resolve to distinct ECEF (one code path)
```

*Optional — the Earth-2 GFS example + figure regeneration.* `reencode_georef.py` additionally needs
`xarray` + `netCDF4` (also in `requirements.txt`) and a GFS NetCDF input (`data/gfs_t2m.nc`, **not
committed** — bring your own GFS `t2m` grid, or synthesize one). It produces the
`out/earth2_georef.usda` stage that `verify.py` and `render_figures.py` consume:

```bash
python3 src/reencode_georef.py --stride 40 --out out/earth2_georef.usda   # needs xarray + netCDF4 + a GFS .nc
python3 src/verify.py out/earth2_georef.usda                              # CI reference on the reencoded stage
python3 src/render_figures.py                                            # regenerate the Python-reference figures into docs/
```

`render_figures.py` regenerates the nine Python-reference figures; it also produces
`multi_runtime.png` / `runtime_parity.png` if the compiled C++ Hydra binary is available (built as
below), otherwise it skips those two with a clear note.

**The full two-runtime parity proof — an opt-in, cross-platform build.** The C++ Hydra scene index
builds like any other OpenUSD example: one flag makes `build_usd.py` fetch and build PROJ, then the
plugin and its parity tests. Validated on Linux and Windows.

```bash
python build_scripts/build_usd.py --usdGeospatial --examples --tests <inst>   # builds PROJ + plugin + tests
python -m pip install pyproj numpy                                            # SAME interpreter build_usd.py used (see note)
ctest --test-dir <build> -R testUsdGeospatial                                 # parity (engine+resolver+Hydra SI+auto-insert, 0.0 mm)
                                                                              # + runtime parity (railway two-runtime gate, <1 mm)
```

The parity ctests check the compiled C++ runtime against the **Python reference runtime**, so they
invoke Python (the interpreter `build_usd.py` built USD against) to generate the reference and
convert the railway asset. That interpreter needs `pyproj` + `numpy` — a subset of
`requirements.txt`, and *not* matplotlib, since the gate runs numpy-only. Install them into that
Python before `ctest`, otherwise the tests error at import (not a build failure — a missing test
dependency).

The plugin installs discoverable via `PXR_PLUGINPATH_NAME`; opening the georef scene in `usdview` /
`usdrecord` then auto-resolves it. `run_parity.py` (invoked by that ctest) is also runnable
standalone. See `../usdGeospatialSceneIndex/README.md` for details and the auto-insert render
notes.

## Status, scope, and open questions

<!-- slide:section title="Open questions" subtitle="What we'd most like the working group's read on." -->

**Status.** This is the OpenUSD-side running evidence supporting the Esri proposal: a pure-data
schema plus a Python reference runtime and a compiled C++ Hydra scene-index runtime (an
illustrative consumer, modeled on the Gaussian-splat example — not a prescribed production
renderer). The Esri C++ typed schema remains the parallel artifact; this bundle backs the proposal's
design calls (binding shape, no baked `resetXformStack`, resolution-rule parity) with running code
on a real dataset. It demonstrates: anchor injection (the coexist answer); a head-to-head against
the baked approach in which neutral reproduces it to 0.0 mm, hand-TRS edits survive, and neutral
resolve costs ~1.8 ms/prim; the compiled Hydra scene-index form with auto-insert into usdview; and
the projection-engine seam.

**Committed near-term (not in this drop, but next):** the codeless `usdchecker`-discoverable
validator plugin (`verify.py` is the runnable validator today) — it is what makes the coexist
tradeoff safe in practice, so we are treating it as a deliverable rather than a maybe.

**Out of scope here (need other resources):** a draped raster / terrain basemap for the coherence
figure (`cartopy` + a DEM asset); an end-to-end grid-*applied* transform (GDAL + a bundled PROJ
grid); an OpenExec / GPU-cuProj *third* runtime.

<!-- slide:text eyebrow="For the working group" title="Open design questions" body="1. Is 'codeless schema + a runnable reference runtime as the behavior contract' the right shape — and where should that reference ultimately live? | 2. Is **coexist** the right relationship to `UsdGeomXformable` (neutral scene + runtime reconciliation) — versus hooking CRS resolution into `Xformable` directly? Given the head-to-head parity + the guard-rail set, is the residual validation surface acceptable to standardize?" -->

**Open design questions for the working group** — the two calls we'd most like Esri's / the WG's
read on:

1. **Is "codeless schema + a runnable reference runtime as the behavior contract" the right shape**,
   and where should that reference ultimately live (an `extras/usd/examples` module, a separate
   behavior test suite, prose in the spec)?
2. **Is "coexist" the right relationship to `UsdGeomXformable`** — a coordinate-neutral authored
   scene plus runtime reconciliation — versus hooking CRS resolution into `Xformable` directly? The
   head-to-head shows neutral **reproduces the baked approach to 0.0 mm** on a real multi-CRS
   scene, so the question is not "does coexist work?" but **"is the residual guard-rail set
   (anchor-vs-child, combine-in-CRS-frame, requires-CRS marker) an acceptable validation surface to
   standardize?"**

<!-- slide:section title="What we need from you" subtitle="Concrete asks so the next iteration is grounded in your workflows, not our guesses." -->
<!-- slide:text eyebrow="Asks" title="What we need from you" body="1. The Redlands BIM prototype scene + its validation script, so we can add a second real, contributor-authored case beside the multi-CRS POC. | 2. Confirmation / correction of the driving workflows: which of AECO site placement, multi-source GIS twins, multi-zone infrastructure, and geodetic sim must 'coexist' survive first? | 3. A read on the guard-rail set as a conformance surface (anchor-vs-child, compose-in-CRS-frame, a 'requires-CRS' stage marker + detect-and-refuse) — which we intend to enforce via a committed codeless `usdchecker` validator plugin. | 4. Where the reference runtime should live, and whether to lift the 'resetXformStack' *semantic* out of the authored-layer text into a documented behavior contract multiple runtimes honor." -->

**What we'd ask of Esri and co-collaborators**, to make the next iteration concrete:

1. **The Redlands BIM prototype scene** (BIM-model-at-site scene + Python validation script) so we
   can validate the AECO site-placement workflow directly, not by proxy.
2. **Confirmation (or correction) of the driving workflows** — AECO/BIM, GIS & digital twins,
   infrastructure across coordinate zones, defense/simulation: which must *coexist* survive first,
   and what edit/authoring workflows (hand-placement, relocation, moving anchors, dynamic datums)
   should we be exercising?
3. **A read on the guard-rail set as a validation surface** (anchor-vs-child,
   combine-in-CRS-frame, requires-CRS marker + detect-and-refuse). We intend to ship a codeless
   `usdchecker`-discoverable validator plugin as the enforcement mechanism — a read on the
   guard-rail set *as the thing that plugin should check* is what we most want.
4. **Where the reference runtime should live**, and whether to jointly **lift the `resetXformStack`
   *semantic* out of the authored-layer text** into a documented behavior contract multiple
   runtimes honor. To be precise: we are *not* rejecting `resetXformStack` as a semantic — both
   runtimes here honor it (Hydra sets it on a transient computed data source; the Python resolver
   composes the equivalent fresh-basis behavior implicitly at each anchor). What we decline is
   *baking it into the authored scene*, because that is what spends composability.

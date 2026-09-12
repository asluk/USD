# Deutsche Bahn railway — third-party geospatial asset

Two files. **Use `deutschebahn-rails-usdgeospatial.usda`.** The original is kept
beside it so the conversion can be checked.

| File | What it is |
|---|---|
| `1kmE4334N3375.geojson` | **The source data, and the ground truth.** Use this to check results |
| `deutschebahn-rails-usdgeospatial.usda` | The asset in the schema being implemented |
| `deutschebahn-rails.usda` | An earlier conversion, in the earlier Omniverse geospatial schema |
| `quadnode-0/1/4.png` | Quadtree ground imagery the tiles are textured with |

## The GeoJSON is the ground truth

`1kmE4334N3375.geojson` is what this scene was before any of this: 1,473 features —
**186 `LineString`, 1,231 `Polygon`, 56 `MultiPolygon`** — EPSG:4326 declared,
coordinates **longitude-first** as `[lon, lat, height]`, each feature carrying an
`object_id` and properties such as `type: Rail_Left` and `material: metal`. Most of
it is areal rather than linear, so "1,473 rails" would be wrong; the rails are the
186 linestrings.

The correspondence to the USD asset is exact and checkable:

- 1,473 features, 1,473 prims carrying an `ObjectId`, every one matched, none left
  over. The three `MapGeo` tiles are imagery and are not in the GeoJSON, which is
  why the asset has 1,476 georeferenced prims and the GeoJSON has 1,473 features.
- Vertex counts agree per feature — the first is 325 in both.
- The first coordinate is `[10.209789719148057, 53.491591843133264, 49.483132426833073]`
  in the GeoJSON and `(53.491591843133264, 10.209789719148057, 49.48313242683307)` in
  the USD asset. Same numbers, transposed, which is the axis-order swap made
  visible.

**Every vertex has a geodetic position here, not just the anchor.** The USD asset
carries one geodetic position per curve and 324 local Cartesian offsets; the
GeoJSON carries all 325 as coordinates. So a resolved vertex can be checked
against closed-form geodesy applied to its GeoJSON coordinate, which exercises the
anchor frame, the local offsets and their composition at once rather than testing
anchor placement alone.

## Provenance

- **Source:** `NVIDIA-Omniverse/OpenUSD-plugin-samples`, `resources/wgs84/deutschebahn-rails.usda`
- **License:** Apache License 2.0, as the source repository
- **What it is:** real Deutsche Bahn railway track curves near Hamburg, about
  53.4916° N, 10.2098° E — 1,476 curve groups on three geospatial tile ground
  planes, `MapGeo0`, `MapGeo1` and `MapGeo4`
- Both the rails and the tiles are georeferenced, so this exercises
  co-registration between two independently placed things, not the position of
  isolated points

## How it was converted, and the decisions that went into it

The original uses `OmniWGS84ReferencePositionAPI` on the root and
`OmniWGS84LocalPositionAPI` on each curve group and tile, carrying
`omni:geospatial:wgs84:*` attributes. Six things had to be decided.

**Axis order.** The source is **latitude-first** — the root reads
`(53.4915918, 10.2097897, 49.4831324)`. Every position is swapped to
`(longitude, latitude, height)`, which is the order the schema fixes at the
boundary. This is the single most consequential step, and a transposed pair here
stays a perfectly valid coordinate, so it will not announce itself.

**The position carrier.** `double3 xformOp:translate` with
`uniform token[] xformOpOrder = ["xformOp:translate"]`. **No `!resetXformStack!`
is authored** — the runtime applies that semantic when it resolves the binding,
and the scene stays free of it.

**The binding.** `rel crs:binding` to a `CoordinateReferenceSystem` prim under
`/CRS`, with `GeospatialCRSBindingAPI` applied.

**Which prims are anchors.** All 1,477 prims that carried a geospatial API — the
root and every curve group and tile. Each holds its own absolute geodetic
position in the original, so each becomes an anchor. Descendants that carry their
own binding and position override the anchor above them and do not accumulate onto
it, so the root anchor is simply redundant for everything beneath it. This matches
how the earlier conversion of this asset treated it.

**The target CRS is not set by the scene.** The `defaultPrim` is bound to a
geographic CRS, which is not a resolve target, so a caller has to supply one —
geocentric or projected. That is deliberate: it is the case the target-selection
rule leads with, and this asset is a natural place to exercise it.

**The reference orientation is dropped.** The original carries
`omni:geospatial:wgs84:reference:orientation = (0, 0, 0)` on the root. It is
identity, and the schema has no equivalent concept, so nothing is lost.

The stage declares `crsResolutionRequired` in `customLayerData`, so a consumer
without CRS support can tell before traversing.

# Deutsche Bahn railway — third-party geospatial asset

Two files. **Use `deutschebahn-rails-usdgeospatial.usda`.** The original is kept
beside it so the conversion can be checked.

| File | What it is |
|---|---|
| `deutschebahn-rails-usdgeospatial.usda` | The asset in the schema being implemented |
| `deutschebahn-rails.usda` | The original, in the earlier Omniverse geospatial schema |
| `quadnode-0/1/4.png` | Quadtree ground imagery the tiles are textured with |

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

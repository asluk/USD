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

**Which prims are anchors.** In the original, every curve group and tile carries
its own absolute geodetic position — they are not offsets from the root. So each
is an independent anchor, and the root is not one: it carries a binding and **no**
position, which supplies the stage's target CRS without making it an anchor.

**The target CRS.** WGS 84 geocentric, EPSG:4978, bound to the `defaultPrim`.
A geographic CRS is not a resolve target — composing a metric offset onto degrees
is not a linear operation — so the geographic CRS the anchors use would be the
wrong thing to resolve into.

**The CRS definition.** Plain WGS 84, no realization and no epoch, because the
source states neither. That ambiguity is the source's and is worth preserving
rather than inventing a realization it never claimed.

The stage declares `crsResolutionRequired` in `customLayerData`, so a consumer
without CRS support can tell before traversing.

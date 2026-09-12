# Deutsche Bahn railway — third-party geospatial asset

Vendored here so a build has the data without visiting the repository it came
from, which also contains an implementation of geospatial support.

- **Source:** `NVIDIA-Omniverse/OpenUSD-plugin-samples`, `resources/wgs84/deutschebahn-rails.usda`
- **License:** Apache License 2.0, as the source repository. Unmodified.
- **What it is:** real Deutsche Bahn railway track curves near Hamburg, about
  53.4916° N, 10.2098° E. 1,476 curve groups on three geospatial tile ground
  planes, `MapGeo0`, `MapGeo1` and `MapGeo4`, textured with the `quadnode-*.png`
  quadtree imagery alongside.
- **How it is authored:** in the earlier Omniverse geospatial schema, not the one
  being implemented. `OmniWGS84ReferencePositionAPI` on a root anchor carrying
  `omni:geospatial:wgs84:reference:referencePosition`, and
  `OmniWGS84LocalPositionAPI` on each curve group. **Note the ordering is
  latitude-first** — the anchor reads `(53.4915918, 10.2097897, 49.4831324)`,
  which is lat, lon, height.

Both the rails and the tiles are georeferenced, so this exercises co-registration
between two independently placed things rather than the position of isolated
points.

# Deutsche Bahn railway — third-party geospatial asset

Source data only. Author the USD yourself; tile placements are in the brief.

| File | What it is |
|---|---|
| `1kmE4334N3375.geojson` | **The source data, and the ground truth.** Use this to check results |
| `quadnode-0/1/4.png` | Quadtree ground imagery the tiles are textured with |
| `sealed/` | Do not open until your design is frozen. See the brief |

## The GeoJSON is the ground truth

`1kmE4334N3375.geojson` is what this scene was before any of this: 1,473 features —
**186 `LineString`, 1,231 `Polygon`, 56 `MultiPolygon`** — EPSG:4326 declared,
coordinates **longitude-first** as `[lon, lat, height]`, each feature carrying an
`object_id` and properties such as `type: Rail_Left` and `material: metal`. Most of
it is areal rather than linear, so "1,473 rails" would be wrong; the rails are the
186 linestrings.

The first feature's first coordinate is
`[10.209789719148057, 53.491591843133264, 49.483132426833073]`, and it has 325
vertices. The three imagery tiles are not in the GeoJSON, so a scene authored from
this plus the tile placements has 1,476 georeferenced things to the GeoJSON's
1,473 features.

**Every vertex has a geodetic position here, not just the anchors.** So a resolved
vertex can be checked against closed-form geodesy applied to its GeoJSON
coordinate, which exercises the anchor frame, the local offsets and their
composition at once rather than testing anchor placement alone.

## Provenance

- **Source:** `NVIDIA-Omniverse/OpenUSD-plugin-samples`. Do not go and fetch it — the sealed copy is the one to use, when the brief says to
- **License:** Apache License 2.0, as the source repository
- **What it is:** real Deutsche Bahn railway track curves near Hamburg, about
  53.4916° N, 10.2098° E, on three quadtree imagery tiles
- Both the rails and the tiles are georeferenced, so this exercises
  co-registration between two independently placed things, not the position of
  isolated points

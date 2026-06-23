#!/usr/bin/env python3
"""
resolve_runtime.py  --  RUNTIME geospatial transform resolution.

This is the deliberately-separate runtime layer (mirrors the omniGeoSceneIndex
PoC and the hdParticleField separation): it READS the CRS-neutral authored scene
and COMPUTES the world transform for each georeferenced prim, WITHOUT modifying
the authored Xformable and WITHOUT relying on a baked resetXformStack.

Resolution rule (the "coexist" answer to the stall question):
  1. Read the prim's `crs:binding` relationship -> source CRS prim -> WKT2.
  2. Read the stage Target CRS (the CRS bound to the composed defaultPrim, or a
     supplied render CRS -- here WGS84 ECEF, the cartesian render frame).
  3. Reproject the prim's absolute `crs:position` from source CRS -> target CRS
     via PROJ. The resulting cartesian position is the world translation.
  4. Compose with any ancestor Cartesian xformOps (NOT done destructively;
     computed at runtime). A CRS-bound prim's geospatial position takes
     precedence and isolates it from ancestor Cartesian offsets -- the same
     precedence rule the omniGeoSceneIndex applied over resetXformStack.

Nothing here is written back into the authored scene unless --bake is passed
(which exists only to produce a renderable artifact for visual evidence; the
canonical authored scene stays neutral).
"""
import argparse, numpy as np
from pyproj import CRS, Transformer
from pxr import Usd, UsdGeom, Sdf, Gf

CRS_WKT_ATTR = "crs:wkt"
CRS_BINDING_REL = "crs:binding"
CRS_POSITION_ATTR = "crs:position"


def crs_of_prim(prim):
    """Resolve the CRS bound to `prim` via the crs:binding relationship.
    Inherits: if not bound, walk ancestors (like material binding)."""
    p = prim
    while p and p.IsValid():
        rel = p.GetRelationship(CRS_BINDING_REL)
        if rel and rel.GetTargets():
            crs_prim = p.GetStage().GetPrimAtPath(rel.GetTargets()[0])
            wkt = crs_prim.GetAttribute(CRS_WKT_ATTR).Get()
            return CRS.from_wkt(wkt), crs_prim.GetPath()
        p = p.GetParent()
    return None, None


def make_transformer(src: CRS, dst: CRS):
    return Transformer.from_crs(src, dst, always_xy=True)


def resolve_world_translation(prim, target_crs, cache):
    """Compute the world-space (target-CRS cartesian) translation for a prim."""
    src_crs, src_path = crs_of_prim(prim)
    if src_crs is None:
        return None, None
    pos = prim.GetAttribute(CRS_POSITION_ATTR).Get()
    if pos is None:
        return None, src_path
    key = str(src_path)
    if key not in cache:
        cache[key] = make_transformer(src_crs, target_crs)
    t = cache[key]
    # crs:position is (lon, lat, height) -> always_xy expects (x=lon, y=lat, z=h)
    x, y, z = t.transform(pos[0], pos[1], pos[2])
    return Gf.Vec3d(x, y, z), src_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="out/earth2_georef.usda")
    ap.add_argument("--target-epsg", type=int, default=4978, help="render/target CRS")
    ap.add_argument("--bake", default=None,
                    help="optional: write a resolved (cartesian) USD for rendering")
    ap.add_argument("--scale", type=float, default=1e-6,
                    help="scale ECEF metres -> scene units for renderable artifact")
    ap.add_argument("--limit", type=int, default=8, help="how many to print")
    args = ap.parse_args()

    stage = Usd.Stage.Open(args.inp)
    target_crs = CRS.from_epsg(args.target_epsg)
    cache = {}

    resolved = []
    for prim in stage.Traverse():
        if not prim.IsA(UsdGeom.Xform):
            continue
        if not prim.GetAttribute(CRS_POSITION_ATTR):
            continue
        world, src = resolve_world_translation(prim, target_crs, cache)
        if world is not None:
            pos = prim.GetAttribute(CRS_POSITION_ATTR).Get()
            t2m = prim.GetAttribute("primvars:t2m").Get()
            resolved.append((prim.GetPath(), tuple(pos), tuple(world), t2m))

    print(f"[resolve] target CRS = EPSG:{args.target_epsg} ({target_crs.name})")
    print(f"[resolve] {len(resolved)} georeferenced prims resolved to world cartesian")
    print(f"[resolve] authored scene was NOT modified (no translate/reset baked)\n")
    for path, pos, world, t2m in resolved[:args.limit]:
        print(f"  {str(path):28s} lon/lat/h={pos[0]:7.2f},{pos[1]:6.2f},{pos[2]:4.0f}"
              f"  ->  ECEF=({world[0]:13.1f},{world[1]:13.1f},{world[2]:13.1f})  t2m={t2m:.1f}K")

    if args.bake:
        out = Usd.Stage.CreateNew(args.bake)
        UsdGeom.SetStageUpAxis(out, UsdGeom.Tokens.z)  # ECEF is z-up
        UsdGeom.SetStageMetersPerUnit(out, 1.0)
        w = UsdGeom.Xform.Define(out, "/World")
        out.SetDefaultPrim(w.GetPrim())
        pts_prim = UsdGeom.Points.Define(out, "/World/ResolvedPoints")
        positions, widths, colors = [], [], []
        tvals = np.array([r[3] for r in resolved], dtype=np.float64)
        tmin, tmax = float(tvals.min()), float(tvals.max())
        for _, _, world, t2m in resolved:
            positions.append(Gf.Vec3f(world[0]*args.scale, world[1]*args.scale, world[2]*args.scale))
            widths.append(0.15)
            f = (t2m - tmin) / (tmax - tmin + 1e-9)        # turbo-ish blue->red
            colors.append(Gf.Vec3f(float(f), float(0.25), float(1.0 - f)))
        pts_prim.CreatePointsAttr(positions)
        pts_prim.CreateWidthsAttr(widths)
        pts_prim.CreateDisplayColorAttr(colors)
        out.GetRootLayer().Save()
        print(f"\n[bake] wrote renderable resolved artifact -> {args.bake} "
              f"(ECEF*{args.scale}, z-up, {len(positions)} pts)")


if __name__ == "__main__":
    main()

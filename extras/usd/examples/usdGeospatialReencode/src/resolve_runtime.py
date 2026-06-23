#!/usr/bin/env python3
"""
resolve_runtime.py  --  RUNTIME geospatial transform resolution.

This is the deliberately-separate runtime layer (mirrors the omniGeoSceneIndex
PoC and the hdParticleField separation): it READS the CRS-neutral authored scene
and COMPUTES the world transform for each georeferenced prim, WITHOUT modifying
the authored Xformable and WITHOUT relying on a baked resetXformStack.

Resolution rule (the "coexist" answer to the stall question):
  1. Read the prim's `crs:binding` relationship -> source CRS prim -> WKT2
     (inherited from nearest bound ancestor, like material binding).
  2. Determine the Target CRS. Priority:
       (a) explicit --target-epsg if the user overrides it, else
       (b) the CRS bound to the composed defaultPrim (a stage-level render CRS),
           else
       (c) the WGS84 ECEF fallback (EPSG:4978), the cartesian render frame.
  3. Reproject the prim's absolute `crs:position` from source CRS -> target CRS
     via PROJ. The resulting cartesian point is the prim's GEOREFERENCED world
     position in the target frame.
  4. Compose ancestor Cartesian xformOps ON TOP of the georeferenced position,
     non-destructively and at runtime. Concretely:
        world = (ancestor_local_to_world_rotation_and_scale) * (georef_position)
                + (ancestor_local_to_world_translation)
     i.e. the georeferenced position is treated as the prim's local origin in
     the target frame, and any ancestor transform (a rig offset, a tile-local
     rotation, an instancing parent) is applied as an additional Cartesian
     transform in that frame. The prim's OWN xform stack is intentionally
     identity (the authored scene is CRS-neutral); only true ANCESTOR transforms
     compose. This is the same precedence the omniGeoSceneIndex PoC used: the
     geospatial binding establishes the world anchor, Cartesian transforms layer
     relative to it.

AXIS-ORDER CONTRACT (see docs/axis-order.md): `crs:position` is ALWAYS authored
as (longitude/easting, latitude/northing, height) -- i.e. X,Y,Z / east-north-up
ordering -- REGARDLESS of the bound CRS authority's declared axis order. All
reprojection therefore uses PROJ `always_xy=True`. A consumer MUST NOT read
`crs:position[0]` as latitude even when the bound CRS's WKT declares lat-first.

Nothing here is written back into the authored scene unless --bake is passed
(which exists only to produce a renderable artifact for visual evidence; the
canonical authored scene stays neutral).
"""
import argparse, numpy as np
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _schema_setup  # noqa
from pyproj import CRS, Transformer
from pxr import Usd, UsdGeom, Sdf, Gf

CRS_WKT_ATTR = "crs:wkt"
CRS_BINDING_REL = "crs:binding"
CRS_POSITION_ATTR = "crs:position"


def crs_of_prim(prim):
    """Resolve the CRS bound to `prim` via the crs:binding relationship.
    Inherits: if not bound, walk ancestors (like material binding).
    Returns (CRS, crs_prim_path, bound_prim_path)."""
    p = prim
    while p and p.IsValid():
        rel = p.GetRelationship(CRS_BINDING_REL)
        if rel and rel.GetTargets():
            crs_prim = p.GetStage().GetPrimAtPath(rel.GetTargets()[0])
            wkt = crs_prim.GetAttribute(CRS_WKT_ATTR).Get()
            return CRS.from_wkt(wkt), crs_prim.GetPath(), p.GetPath()
        p = p.GetParent()
    return None, None, None


def target_crs_for_stage(stage, override_epsg=None):
    """Determine the Target/render CRS for the stage.
    Priority: explicit override -> CRS bound to the defaultPrim -> ECEF 4978.
    Returns (CRS, source_description)."""
    if override_epsg is not None:
        return CRS.from_epsg(override_epsg), f"--target-epsg={override_epsg}"
    dp = stage.GetDefaultPrim()
    if dp and dp.IsValid():
        crs, crs_path, _ = crs_of_prim(dp)
        if crs is not None:
            return crs, f"stage defaultPrim binding -> {crs_path}"
    return CRS.from_epsg(4978), "fallback EPSG:4978 (WGS84 ECEF)"


def make_transformer(src: CRS, dst: CRS):
    return Transformer.from_crs(src, dst, always_xy=True)


def ancestor_local_to_world(prim):
    """Compute the composed local-to-world transform contributed by ANCESTORS
    only (excludes the prim's own xform, which is intentionally identity in the
    CRS-neutral scene). Returns a Gf.Matrix4d. If the prim's own xform stack is
    non-identity we still exclude it here -- the georeferenced position defines
    the prim's own placement; ancestors compose on top."""
    parent = prim.GetParent()
    if not parent or not parent.IsValid():
        return Gf.Matrix4d(1.0)
    xc = UsdGeom.XformCache()
    return xc.GetLocalToWorldTransform(parent)


def resolve_world_translation(prim, target_crs, cache, compose_ancestors=True):
    """Compute the world-space (target-CRS cartesian) position for a prim.

    world = ancestor_L2W . reproject(crs:position)
    where reproject maps the source-CRS (lon/E, lat/N, h) to the target frame.
    The georeferenced point is the prim's local origin; ancestor Cartesian
    transforms compose on top (rotation/scale applied to it, then translation).
    """
    src_crs, src_path, _ = crs_of_prim(prim)
    if src_crs is None:
        return None, None
    pos = prim.GetAttribute(CRS_POSITION_ATTR).Get()
    if pos is None:
        return None, src_path
    key = str(src_path)
    if key not in cache:
        cache[key] = make_transformer(src_crs, target_crs)
    t = cache[key]
    # AXIS-ORDER CONTRACT: crs:position is (x=lon/E, y=lat/N, z=h) always.
    x, y, z = t.transform(pos[0], pos[1], pos[2])
    georef = Gf.Vec3d(x, y, z)
    if not compose_ancestors:
        return georef, src_path
    # Compose ancestor Cartesian transform on top of the georeferenced anchor.
    a2w = ancestor_local_to_world(prim)
    world = a2w.Transform(georef)   # applies ancestor rot/scale + translation
    return world, src_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--in", dest="inp", default="out/earth2_georef.usda")
    ap.add_argument("--target-epsg", type=int, default=None,
                    help="render/target CRS override; default: read from stage "
                         "defaultPrim binding, else EPSG:4978")
    ap.add_argument("--bake", default=None,
                    help="optional: write a resolved (cartesian) USD for rendering")
    ap.add_argument("--scale", type=float, default=1e-6,
                    help="scale ECEF metres -> scene units for renderable artifact")
    ap.add_argument("--limit", type=int, default=8, help="how many to print")
    args = ap.parse_args()

    stage = Usd.Stage.Open(args.inp)
    target_crs, target_src = target_crs_for_stage(stage, args.target_epsg)
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

    print(f"[resolve] target CRS = {target_crs.name} (via {target_src})")
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

#!/usr/bin/env python3
"""
multi_crs_example.py -- worked multi-CRS scene + verification.

Demonstrates the design's headline capability and answers an open thread on the
Esri proposal: a single composed stage where different subtrees are bound to
DIFFERENT source CRSs, and the runtime resolves them all into one Target CRS
correctly -- without any baked transforms.

Scene:
  /World/CRS/WGS84_Geographic3D   (EPSG:4979)  -- a global geographic CRS
  /World/CRS/UTM10N               (EPSG:32610) -- a projected CRS (UTM zone 10N, metres)
  /World/CRS/WGS84_ECEF           (EPSG:4978)  -- the Target/render CRS

  /World/SiteA  bound to WGS84_Geographic3D, crs:position = (lon, lat, h)
  /World/SiteB  bound to UTM10N,            crs:position = (easting, northing, h)

Both sites are placed at the SAME physical location (Esri HQ, Redlands CA),
expressed in two different CRSs. If the runtime is correct, they must resolve to
the SAME ECEF coordinate (within projection tolerance). That single equality is
the proof that multi-CRS binding + reprojection composes.
"""
import sys, numpy as np
from pyproj import CRS, Transformer
from pxr import Usd, UsdGeom, Sdf, Gf

GEO   = CRS.from_epsg(4979)    # lon/lat/h
UTM   = CRS.from_epsg(32610)   # UTM 10N (E,N) metres  -- NOTE: 2D; height passed through
ECEF  = CRS.from_epsg(4978)    # target

# Esri HQ, Redlands CA
LON, LAT, H = -117.1956, 34.0561, 0.0


def author_crs(stage, path, crs, name):
    p = stage.DefinePrim(path, "CoordinateReferenceSystem")
    a = p.CreateAttribute("crs:wkt", Sdf.ValueTypeNames.Token, False, Sdf.VariabilityUniform)
    a.Set(crs.to_wkt(version="WKT2_2019"))
    p.CreateAttribute("crs:epsg", Sdf.ValueTypeNames.Int, custom=True).Set(int(crs.to_epsg()))
    p.CreateAttribute("crs:displayName", Sdf.ValueTypeNames.String, custom=True).Set(name)
    return p


def bind(prim, crs_prim, pos):
    prim.CreateRelationship("crs:binding", False).SetTargets([crs_prim.GetPath()])
    a = prim.CreateAttribute("crs:position", Sdf.ValueTypeNames.Double3, False)
    a.Set(Gf.Vec3d(*pos))


def resolve(prim, stage, target=ECEF, cache={}):
    rel = prim.GetRelationship("crs:binding")
    crs_prim = stage.GetPrimAtPath(rel.GetTargets()[0])
    wkt = crs_prim.GetAttribute("crs:wkt").Get()
    if wkt not in cache:
        cache[wkt] = Transformer.from_crs(CRS.from_wkt(wkt), target, always_xy=True)
    pos = prim.GetAttribute("crs:position").Get()
    return np.array(cache[wkt].transform(pos[0], pos[1], pos[2]))


def main(out="out/multi_crs.usda"):
    stage = Usd.Stage.CreateNew(out)
    w = UsdGeom.Xform.Define(stage, "/World"); stage.SetDefaultPrim(w.GetPrim())
    UsdGeom.Scope.Define(stage, "/World/CRS")
    geo = author_crs(stage, "/World/CRS/WGS84_Geographic3D", GEO, "WGS84 geographic 3D")
    utm = author_crs(stage, "/World/CRS/UTM10N", UTM, "UTM zone 10N (EPSG:32610)")
    author_crs(stage, "/World/CRS/WGS84_ECEF", ECEF, "WGS84 ECEF (target)")

    # Site A: position in geographic CRS
    A = UsdGeom.Xform.Define(stage, "/World/SiteA").GetPrim()
    bind(A, geo, (LON, LAT, H))

    # Site B: SAME physical point, expressed in UTM 10N (project lon/lat -> E,N)
    e, n = Transformer.from_crs(GEO, UTM, always_xy=True).transform(LON, LAT, H)[:2]
    B = UsdGeom.Xform.Define(stage, "/World/SiteB").GetPrim()
    bind(B, utm, (e, n, H))

    stage.GetRootLayer().Save()
    print(f"[author] {out}")
    print(f"  SiteA bound to WGS84_Geographic3D  pos=({LON},{LAT},{H})")
    print(f"  SiteB bound to UTM10N              pos=({e:.3f},{n:.3f},{H})  [same place]")

    # --- runtime resolution into target ECEF ---
    ea = resolve(A, stage); eb = resolve(B, stage)
    d = float(np.linalg.norm(ea - eb))
    print(f"\n[resolve] SiteA -> ECEF {ea.round(3)}")
    print(f"[resolve] SiteB -> ECEF {eb.round(3)}")
    print(f"[resolve] distance between the two resolutions: {d*100:.3f} cm")

    tol = 0.01  # 1 cm -- well within datum/projection round-trip noise
    txt = open(out).read()
    neutral = ("xformOp:translate" not in txt) and ("resetXformStack" not in txt)
    ok = (d < tol) and neutral
    print(f"\n[check] scene CRS-neutral (no baked translate/reset): {neutral}")
    print(f"[check] two CRSs resolve to same ECEF within {tol*100:.0f} cm: {d < tol}")
    print("\nRESULT:", "MULTI-CRS COMPOSES ✅" if ok else "FAIL ❌")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main(*(sys.argv[1:2] or [])))

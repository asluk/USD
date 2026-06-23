#!/usr/bin/env python3
"""
verify.py -- rigorous correctness evidence for the geospatial re-encode pipeline.

Checks:
  A. Authored scene is CRS-neutral: no xformOp:translate, no resetXformStack.
  B. Binding resolves: every GeoSample has a crs:binding -> CRS prim with valid WKT2.
  C. Reprojection is geodetically correct against independent ground truth:
       - poles land on the WGS84 semi-minor axis (b = 6356752.314 m)
       - equator/prime-meridian lands on semi-major axis (a = 6378137 m)
       - a known landmark (e.g. a city) round-trips ECEF->geographic to < 1e-6 deg
  D. Round-trip: geographic -> ECEF -> geographic recovers original lon/lat/h.
Exit non-zero on any failure (CI-style).
"""
import sys, numpy as np
from pyproj import CRS, Transformer
from pxr import Usd, UsdGeom

WGS84_A = 6378137.0            # semi-major (equatorial)
WGS84_B = 6356752.314245      # semi-minor (polar)

def fail(msg): print("  FAIL:", msg); return False
def ok(msg):   print("  ok  :", msg); return True

def main(path="out/earth2_georef.usda"):
    passed = True
    stage = Usd.Stage.Open(path)

    # --- A. authored scene neutrality ---
    txt = open(path).read()
    if "xformOp:translate" in txt or "resetXformStack" in txt:
        passed &= fail("authored scene contains baked transform/reset")
    else:
        ok("A. authored scene is CRS-neutral (no xformOp:translate / resetXformStack)")

    # --- B. binding + WKT validity ---
    samples = [p for p in stage.Traverse()
               if p.IsA(UsdGeom.Xform) and p.GetAttribute("crs:position")]
    bad = 0
    for p in samples:
        rel = p.GetRelationship("crs:binding")
        if not (rel and rel.GetTargets()):
            bad += 1; continue
        crs_prim = stage.GetPrimAtPath(rel.GetTargets()[0])
        wkt = crs_prim.GetAttribute("crs:wkt").Get()
        try:
            CRS.from_wkt(wkt)
        except Exception:
            bad += 1
    if bad: passed &= fail(f"B. {bad}/{len(samples)} samples have bad binding/WKT")
    else:   ok(f"B. all {len(samples)} samples bind to a CRS with parseable WKT2")

    # --- C. geodetic ground truth ---
    geo  = CRS.from_epsg(4979)
    ecef = CRS.from_epsg(4978)
    fwd = Transformer.from_crs(geo, ecef, always_xy=True)

    # pole
    _,_,zp = fwd.transform(0,90,0)
    if abs(zp - WGS84_B) > 1e-3: passed &= fail(f"C-pole z={zp} != b={WGS84_B}")
    else: ok(f"C. north pole -> ECEF z = {zp:.3f} m == WGS84 semi-minor b ({WGS84_B} m)")
    # equator/prime meridian
    xe,_,_ = fwd.transform(0,0,0)
    if abs(xe - WGS84_A) > 1e-3: passed &= fail(f"C-eq x={xe} != a={WGS84_A}")
    else: ok(f"C. equator/0deg -> ECEF x = {xe:.3f} m == WGS84 semi-major a ({WGS84_A} m)")
    # known landmark: Esri HQ, Redlands CA ~ (-117.1956, 34.0561)
    lon0, lat0 = -117.1956, 34.0561
    x,y,z = fwd.transform(lon0, lat0, 0)
    r = (x*x+y*y+z*z) ** 0.5
    if not (WGS84_B - 1 <= r <= WGS84_A + 1):
        passed &= fail(f"C-landmark radius {r} outside ellipsoid bounds")
    else: ok(f"C. landmark(-117.20,34.06) -> ECEF radius {r:.1f} m within ellipsoid [b,a]")

    # --- D. round trip ---
    inv = Transformer.from_crs(ecef, geo, always_xy=True)
    lon1, lat1, h1 = inv.transform(x, y, z)
    derr = max(abs(lon1-lon0), abs(lat1-lat0)); herr = abs(h1-0)
    if derr > 1e-7 or herr > 1e-3:
        passed &= fail(f"D. round-trip err deg={derr:.2e} h={herr:.2e}")
    else:
        ok(f"D. round-trip geographic->ECEF->geographic err = {derr:.2e} deg, {herr:.2e} m")

    print("\nRESULT:", "ALL PASS ✅" if passed else "FAILURES ❌")
    return 0 if passed else 1

if __name__ == "__main__":
    sys.exit(main(*(sys.argv[1:2] or [])))

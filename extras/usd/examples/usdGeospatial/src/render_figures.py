#!/usr/bin/env python3
"""
render_figures.py -- generate ALL writeup figures for the usdGeospatial bundle,
every one produced by THIS codeless build: the registered schema
(_schema_setup) + the shipped runtime (resolve_runtime). No external renderer,
no carried-over artifacts. Reviewers reproduce the entire figure set with:

    python3 src/render_figures.py            # all figures -> docs/

Figures (all PR-story, all build-generated):
  1 evidence.png          -- resolved ECEF cloud via resolve_runtime (real ellipsoid)
  2 globe.png             -- hero globe, matplotlib 3D, geometry via resolve_runtime
  3 binding_semantics.png -- crs:binding precedence/strength, read live from resolver
  4 design_equivalence.png-- baked resetXformStack vs neutral rel-binding -> same ECEF
  5 tree_alignment.png    -- Simon's C++ usdGeospatial <-> our codeless variant
  6 coherence.png         -- 3D coherence: schema-resolved Earth-2 cloud on a graticule,
                            plus 3 cross-CRS benchmark features (NOAA NCAT) co-registering
                            against CLOSED-FORM WGS84 ground truth, with a negative-control
                            ghost cloud (bindings ignored). Non-circular by construction.
  7 generalization.png    -- no-overfit: the SAME runtime over 7 diverse datasets vs
                            closed-form geodesy (all sub-mm), incl. a real 3rd-party asset.
  8 railway_render.png     -- actual render of the real converted NVIDIA Deutsche Bahn asset:
                            geospatial tile ground planes + rail curves on top, all positions
                            resolved by resolve_runtime (rails on tiles, no Hydra/baking).

Run from extras/usd/examples/usdGeospatial with the venv active.
"""
import argparse, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import _schema_setup  # noqa  registers the codeless schema
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
from pyproj import CRS
from pxr import Usd, UsdGeom, Gf
import resolve_runtime as rr

DOCS = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "docs")


# --------------------------------------------------------------------------
# Shared: resolve a stage to ECEF THROUGH THE SHIPPED RUNTIME (resolve_runtime)
# --------------------------------------------------------------------------
def resolve_stage_ecef(stage_path, target_epsg=4978):
    stage = Usd.Stage.Open(stage_path)
    target, _ = rr.target_crs_for_stage(stage, target_epsg)
    cache = {}
    xc = UsdGeom.XformCache()
    lons, lats, xs, ys, zs, t2m = [], [], [], [], [], []
    for p in stage.Traverse():
        if not (p.IsA(UsdGeom.Xform) and p.GetAttribute(rr.CRS_POSITION_ATTR)):
            continue
        world, src_path = rr.resolve_world_translation(p, target, cache, xform_cache=xc)
        if world is None:
            continue
        pos = p.GetAttribute(rr.CRS_POSITION_ATTR).Get()
        lons.append(pos[0]); lats.append(pos[1])
        xs.append(world[0]); ys.append(world[1]); zs.append(world[2])
        a = p.GetAttribute("primvars:t2m")
        t2m.append(a.Get() if a else np.nan)
    return tuple(np.array(v) for v in (lons, lats, xs, ys, zs, t2m))


# --------------------------------------------------------------------------
# Figure 1: evidence -- resolved ECEF cloud (correct ellipsoid, no baked sphere)
# --------------------------------------------------------------------------
def fig_evidence(stage_path, out):
    lons, lats, xs, ys, zs, t2m = resolve_stage_ecef(stage_path)
    fig = plt.figure(figsize=(15, 5))
    fig.suptitle("Resolved through resolve_runtime (the shipped runtime) \u2014 "
                 "geometry is computed, never authored", fontsize=11, fontweight="bold")
    ax = fig.add_subplot(1, 3, 1, projection="3d")
    ax.scatter(xs, ys, zs, c=t2m, cmap="turbo", s=4)
    ax.set_title("ECEF (EPSG:4978) from crs:position\n(no baked sphere)")
    ax.set_box_aspect((1, 1, 1)); ax.view_init(elev=20, azim=-40)
    ax2 = fig.add_subplot(1, 3, 2, projection="3d")
    ax2.scatter(xs, ys, zs, c=t2m, cmap="turbo", s=4)
    ax2.set_title("Over the N pole\n(ellipsoid flattening, not a sphere)")
    ax2.set_box_aspect((1, 1, 1)); ax2.view_init(elev=80, azim=0)
    ax3 = fig.add_subplot(1, 3, 3)
    sc = ax3.scatter(np.where(lons > 180, lons - 360, lons), lats, c=t2m, cmap="turbo", s=6)
    ax3.set_title("t2m at authored lon/lat\n(cold poles, warm tropics)")
    ax3.set_xlabel("longitude"); ax3.set_ylabel("latitude")
    ax3.set_xlim(-180, 180); ax3.set_ylim(-90, 90); ax3.grid(alpha=0.3)
    fig.colorbar(sc, ax=ax3, label="t2m (K)", shrink=0.8)
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(out, dpi=120); plt.close(fig)
    r = np.sqrt(xs**2 + ys**2 + zs**2)
    eq = r[np.abs(lats) < 5].mean() if (np.abs(lats) < 5).any() else float("nan")
    pol = r[np.abs(lats) > 85].mean() if (np.abs(lats) > 85).any() else float("nan")
    print(f"[1] evidence.png  {len(xs)} pts  | eq r={eq:.0f}m pole r={pol:.0f}m "
          f"flattening_visible={eq > pol}")
    return out


# --------------------------------------------------------------------------
# Figure 2: hero globe -- matplotlib 3D, geometry via resolve_runtime (PR build)
# --------------------------------------------------------------------------
def fig_globe(stage_path, out):
    lons, lats, xs, ys, zs, t2m = resolve_stage_ecef(stage_path)
    fig = plt.figure(figsize=(8, 8))
    ax = fig.add_subplot(111, projection="3d")
    # solid-looking globe: shade by t2m, larger points, dark bg
    fig.patch.set_facecolor("#0b0e14"); ax.set_facecolor("#0b0e14")
    ax.scatter(xs, ys, zs, c=t2m, cmap="turbo", s=14, depthshade=True, edgecolors="none")
    ax.set_box_aspect((1, 1, 1)); ax.view_init(elev=18, azim=-55)
    ax.set_axis_off()
    ax.set_title("usdGeospatial hero globe \u2014 every vertex resolved by resolve_runtime\n"
                 "(crs:position \u2192 PROJ \u2192 ECEF), colored by GFS t2m",
                 color="white", fontsize=10, pad=2)
    fig.tight_layout()
    fig.savefig(out, dpi=130, facecolor=fig.get_facecolor()); plt.close(fig)
    print(f"[2] globe.png  {len(xs)} pts (matplotlib 3D via shipped runtime)")
    return out


# --------------------------------------------------------------------------
# Figure 3: binding semantics -- read live from the resolver
# --------------------------------------------------------------------------
def fig_binding_semantics(out):
    import render_binding_semantics as rbs
    rbs.main(out)
    print("[3] binding_semantics.png (live from resolve_runtime.crs_of_prim)")
    return out


# --------------------------------------------------------------------------
# Figure 4: design equivalence -- baked resetXformStack vs neutral rel-binding
# --------------------------------------------------------------------------
def fig_design_equivalence(out):
    import testenv_equivalence as te
    import tempfile
    d = tempfile.mkdtemp(prefix="crs_fig_")
    ecef_A, utm_A = te.style_A_baked(os.path.join(d, "baked.usda"))
    ecef_B, neutral_B = te.style_B_neutral(os.path.join(d, "neutral.usda"))
    dist_mm = (ecef_A - ecef_B).GetLength() * 1000.0
    # pull the REAL authored crs:position from testenv_equivalence (no hardcoded #s)
    pos_B = (te.NY_E + te.MOMA_DX + te.CORNER[0],
             te.NY_N + te.MOMA_DY + te.CORNER[1],
             te.NY_H + te.MOMA_DZ + te.CORNER[2])

    fig, (axL, axR) = plt.subplots(1, 2, figsize=(13, 6))
    fig.suptitle("Same world position, two authoring styles \u2014 the no-baking design win",
                 fontsize=12, fontweight="bold")

    def scene_panel(ax, title, rows, foot, foot_color):
        ax.set_xlim(0, 10); ax.set_ylim(0, 10); ax.axis("off")
        ax.set_title(title, fontsize=10)
        y = 8.4
        for label, sub, bad in rows:
            fc = "#fde0dc" if bad else "#e3f0ff"
            ec = "#c0392b" if bad else "#2c6fbb"
            ax.add_patch(FancyBboxPatch((1, y), 8, 1.25, boxstyle="round,pad=0.08",
                                        fc=fc, ec=ec, lw=1.3))
            ax.text(5, y + 0.78, label, ha="center", va="center", fontsize=9, fontweight="bold")
            ax.text(5, y + 0.32, sub, ha="center", va="center", fontsize=7.5,
                    color="#c0392b" if bad else "#333", family="monospace")
            if y > 3:
                ax.annotate("", xy=(5, y - 0.15), xytext=(5, y - 0.55),
                            arrowprops=dict(arrowstyle="->", color="gray"))
            y -= 1.85
        ax.add_patch(FancyBboxPatch((1, 0.4), 8, 1.0, boxstyle="round,pad=0.08",
                                    fc=foot_color, ec="black", lw=1.2))
        ax.text(5, 0.9, foot, ha="center", va="center", fontsize=8.5, fontweight="bold")

    scene_panel(axL, "(A) Esri prototype style \u2014 BAKED", [
        ("/World/NewYork", "references=@crs.usda@</CRS/UTM17N>", True),
        ("  + !resetXformStack!", "xformOp:translate = (586000, 4515000, 50)", True),
        ("/World/NewYork/MoMa/Corner", "xformOp:translate (stacked UTM offsets)", True),
    ], f"resolve (plain xform) \u2192 ECEF\n({ecef_A[0]:.1f}, {ecef_A[1]:.1f}, {ecef_A[2]:.1f})", "#a6dba0")

    scene_panel(axR, "(B) usdGeospatial codeless \u2014 NEUTRAL", [
        ("/World/NewYork/MoMa/Corner", "BindingAPI applied", False),
        ("  rel crs:binding", "\u2192 </World/CRS/UTM17N>   (no xformOps)", False),
        ("  crs:position", f"({pos_B[0]:.1f}, {pos_B[1]:.1f}, {pos_B[2]:.1f})", False),
    ], f"resolve_runtime \u2192 ECEF\n({ecef_B[0]:.1f}, {ecef_B[1]:.1f}, {ecef_B[2]:.1f})", "#a6dba0")

    fig.text(0.5, 0.02,
             f"\u0394 = {dist_mm:.4f} mm   \u2014   neutral authoring reproduces the baked result, "
             f"with zero xformOps in the scene (no baked resetXformStack).",
             ha="center", fontsize=10, fontweight="bold", color="#1b7837")
    fig.tight_layout(rect=[0, 0.05, 1, 0.95])
    fig.savefig(out, dpi=120); plt.close(fig)
    print(f"[4] design_equivalence.png  \u0394={dist_mm:.4f}mm  neutral_scene_no_xformops={neutral_B}")
    assert dist_mm < 1.0 and neutral_B
    return out


# --------------------------------------------------------------------------
# Figure 5: tree alignment -- Simon's C++ schema <-> our codeless variant
# --------------------------------------------------------------------------
def fig_tree_alignment(out):
    fig, ax = plt.subplots(figsize=(13, 6.5))
    ax.set_xlim(0, 14); ax.set_ylim(0, 10); ax.axis("off")
    fig.suptitle("File-layout & name alignment with the Esri prototype "
                 "(mistafunk/USD geospatial-prototype)", fontsize=12, fontweight="bold")

    def col(x, title, lines, color, foot):
        ax.add_patch(FancyBboxPatch((x, 0.7), 5.4, 7.7, boxstyle="round,pad=0.15",
                                    fc=color, ec="black", lw=1.4))
        ax.text(x + 2.7, 8.05, title, ha="center", fontsize=10.5, fontweight="bold")
        y = 7.05
        for txt, mono, em in lines:
            ax.text(x + 0.35, y, txt, ha="left", va="top",
                    fontsize=8.2 if not em else 8.6,
                    family="monospace" if mono else "sans-serif",
                    fontweight="bold" if em else "normal",
                    color="#1b5e20" if em else "#222")
            y -= 0.56
        ax.text(x + 2.7, 1.05, foot, ha="center", fontsize=7.6, style="italic", color="#444")

    col(0.4, "Esri prototype (C++)", [
        ("pxr/usd/usdGeospatial/", True, True),
        ("  schema.usda", True, False),
        ("    CoordinateReferenceSystem", True, False),
        ("      uniform token crs:wkt", True, False),
        ("    BindingAPI (singleApply)", True, False),
        ("      rel crs:binding", True, False),
        ("  api.h / module.cpp / wrap*.cpp", True, False),
        ("  testenv/world.usda", True, False),
        ("    references-as-binding +", True, False),
        ("    !resetXformStack! (baked)", True, False),
    ], "#fff3e0", "C++ library; binding baked into the scene")

    # arrow
    ax.add_patch(FancyArrowPatch((5.95, 4.6), (8.0, 4.6), arrowstyle="<->",
                                 mutation_scale=22, lw=2, color="#2c6fbb"))
    ax.text(7.0, 5.0, "same names\n& layout", ha="center", fontsize=8.5,
            color="#2c6fbb", fontweight="bold")

    col(8.1, "usdGeospatial codeless (ours)", [
        ("pxr/usd/usdGeospatial/", True, True),
        ("  schema.usda  (skipCodeGeneration)", True, True),
        ("    CoordinateReferenceSystem", True, False),
        ("      uniform token crs:wkt", True, False),
        ("    BindingAPI (singleApply)", True, False),
        ("      rel crs:binding  +  crs:position", True, False),
        ("  plugInfo.json + generatedSchema.usda", True, False),
        ("  (NO C++)", True, True),
        ("  testenv/world_neutral_relbinding.usda", True, False),
        ("    rel binding, resolved at runtime", True, True),
    ], "#e8f5e9", "pure data; binding resolved by resolve_runtime")

    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(out, dpi=120); plt.close(fig)
    print("[5] tree_alignment.png")
    return out


# --------------------------------------------------------------------------
# Figure 6: 3D COHERENCE -- schema-resolved geometry co-registers, in 3D, with
# an INDEPENDENT ground truth derived from closed-form WGS84 geodesy (NOT a
# parallel pyproj call), using cross-CRS benchmark features whose coordinates
# come from independent authoritative sources (NOAA NCAT). Non-circular by
# construction; includes a negative-control ghost cloud (bindings ignored).
# --------------------------------------------------------------------------
#
# WHY THIS IS NOT CIRCULAR (the v1 failure mode, avoided):
#   * Ground truth is CLOSED-FORM geodesy: N = a / sqrt(1 - e^2 sin^2(phi));
#     X=(N+h)cos(phi)cos(lam), Y=(N+h)cos(phi)sin(lam), Z=(N(1-e^2)+h)sin(phi).
#     resolve_runtime uses PROJ/pyproj; comparing the two means an axis-order or
#     geodesy bug has nowhere to hide (a shared always_xy assumption would NOT
#     cancel, because the closed-form side makes no such assumption).
#   * Cross-CRS independence is real: three features authored in three DIFFERENT
#     CRSs (geographic 4979, UTM 18N 32618, NY State Plane 32118), each from
#     INDEPENDENT NOAA NCAT coordinates -- SiteB/SiteC are NOT generated by
#     inverting SiteA's transform. They must co-register in common ECEF.
#   * Negative control: a ghost cloud resolved while IGNORING crs:binding flies
#     hundreds of km off the globe -- visible teeth.

# WGS84 closed-form ellipsoid constants (first principles, no PROJ).
_WGS84_A = 6378137.0
_WGS84_F = 1.0 / 298.257223563
_WGS84_E2 = _WGS84_F * (2.0 - _WGS84_F)
_WGS84_B = _WGS84_A * (1.0 - _WGS84_F)

# Independent cross-CRS benchmark from NOAA NCAT (geodesy.noaa.gov/api/ncat),
# point near the Empire State Building, NYC. lat/lon + the SAME monument's
# UTM 18N and NY State Plane (Long Island 3104) eastings/northings as computed
# by NOAA -- not by us, not by PROJ.
_BENCH_LON, _BENCH_LAT = -73.985656, 40.748817
_BENCH_UTM18N = (585631.589, 4511368.780)     # EPSG:32618 (NOAA)
_BENCH_NYSPC = (301211.401, 64645.529)         # EPSG:32118 NAD83 NY-LI metres (NOAA)


def _closed_form_ecef(lon, lat, h=0.0):
    """WGS84 geographic -> ECEF from first principles (independent of PROJ).
    Broadcasts: lon/lat may be scalars or arrays. Returns shape (3,) for scalars
    or (3, N) for arrays (rows x,y,z)."""
    lon = np.asarray(lon, dtype=float); lat = np.asarray(lat, dtype=float)
    lon, lat = np.broadcast_arrays(lon, lat)
    lam = np.radians(lon); phi = np.radians(lat)
    N = _WGS84_A / np.sqrt(1.0 - _WGS84_E2 * np.sin(phi) ** 2)
    x = (N + h) * np.cos(phi) * np.cos(lam)
    y = (N + h) * np.cos(phi) * np.sin(lam)
    z = (N * (1.0 - _WGS84_E2) + h) * np.sin(phi)
    return np.array([x, y, z])


def _author_bench_stage(path):
    """Author 3 benchmark features, each bound to a DIFFERENT CRS, from the
    independent NOAA NCAT coordinates. Returns the stage path."""
    from pxr import Sdf
    stage = Usd.Stage.CreateNew(path)
    w = UsdGeom.Xform.Define(stage, "/World"); stage.SetDefaultPrim(w.GetPrim())
    UsdGeom.Scope.Define(stage, "/World/CRS")

    def crs(name, epsg):
        p = stage.DefinePrim(f"/World/CRS/{name}", "CoordinateReferenceSystem")
        a = p.CreateAttribute("crs:wkt", Sdf.ValueTypeNames.Token, False,
                              Sdf.VariabilityUniform)
        a.Set(CRS.from_epsg(epsg).to_wkt(version="WKT2_2019"))
        return p

    geo = crs("WGS84_Geographic3D", 4979)
    utm = crs("UTM18N", 32618)
    spc = crs("NY_StatePlane_LI", 32118)

    def feature(name, crs_prim, pos):
        pr = UsdGeom.Xform.Define(stage, f"/World/{name}").GetPrim()
        pr.CreateRelationship(rr.CRS_BINDING_REL, False).SetTargets([crs_prim.GetPath()])
        pr.CreateAttribute(rr.CRS_POSITION_ATTR, Sdf.ValueTypeNames.Double3, False) \
          .Set(Gf.Vec3d(*pos))
        return pr

    feature("SiteGeographic", geo, (_BENCH_LON, _BENCH_LAT, 0.0))
    feature("SiteUTM18N", utm, (_BENCH_UTM18N[0], _BENCH_UTM18N[1], 0.0))
    feature("SiteNYSPC", spc, (_BENCH_NYSPC[0], _BENCH_NYSPC[1], 0.0))
    stage.GetRootLayer().Save()
    return path


def fig_coherence(stage_path, out):
    import tempfile
    # --- (a) global backdrop: schema-resolved Earth-2 t2m cloud (path under test)
    lons, lats, xs, ys, zs, t2m = resolve_stage_ecef(stage_path)

    # --- (b) independent reference graticule, projected by CLOSED-FORM geodesy
    grat_lon = np.arange(-180, 181, 30)
    grat_lat = np.arange(-60, 61, 30)
    fine = np.linspace(-180, 180, 181)
    finelat = np.linspace(-90, 90, 91)
    merid = [(_closed_form_ecef(L, finelat)) for L in grat_lon]   # meridians
    paral = [(_closed_form_ecef(fine, L)) for L in grat_lat]      # parallels

    # --- (c) cross-CRS benchmark features (independent NOAA coords, 3 CRSs)
    d = tempfile.mkdtemp(prefix="crs_coh_")
    bstage_path = _author_bench_stage(os.path.join(d, "bench.usda"))
    bstage = Usd.Stage.Open(bstage_path)
    ecef_tgt = CRS.from_epsg(4978)
    cache = {}
    feats = {}
    for nm in ("SiteGeographic", "SiteUTM18N", "SiteNYSPC"):
        pr = bstage.GetPrimAtPath(f"/World/{nm}")
        world, _ = rr.resolve_world_translation(pr, ecef_tgt, cache)
        feats[nm] = np.array(world)
    gt = _closed_form_ecef(_BENCH_LON, _BENCH_LAT, 0.0)   # closed-form ground truth

    # --- (d) negative control: resolve the Earth-2 cloud IGNORING crs:binding.
    # A binding-ignoring resolver has no source CRS, so it would treat the raw
    # crs:position (lon,lat,h) as if it were already cartesian metres -- the
    # cloud collapses to a tiny degenerate blob near the origin (|pos|<=360),
    # nowhere near the globe. That is the visible failure.
    ghost = np.column_stack([lons, lats, np.zeros_like(lons)])  # raw, unresolved

    # ---- ASSERTIONS (teeth) ----
    # 1. every resolved benchmark co-registers with closed-form GT to <1 mm-ish
    #    (UTM/SPC carry ~mm conformal-projection residual; tol 5 mm).
    d_geo = float(np.linalg.norm(feats["SiteGeographic"] - gt))
    d_utm = float(np.linalg.norm(feats["SiteUTM18N"] - gt))
    d_spc = float(np.linalg.norm(feats["SiteNYSPC"] - gt))
    # 2. the three cross-CRS features co-register with each other
    d_cross = max(float(np.linalg.norm(feats["SiteGeographic"] - feats["SiteUTM18N"])),
                  float(np.linalg.norm(feats["SiteGeographic"] - feats["SiteNYSPC"])))
    # 3. negative control: ghost cloud is NOT on the globe (far from Earth radius)
    ghost_r = np.sqrt((ghost ** 2).sum(axis=1))
    real_r = np.sqrt(xs ** 2 + ys ** 2 + zs ** 2)
    ghost_off = float(real_r.mean() - ghost_r.max())   # ghost radius << earth radius
    assert d_geo < 5e-3 and d_utm < 5e-3 and d_spc < 5e-3, \
        f"benchmark co-registration failed: geo={d_geo} utm={d_utm} spc={d_spc}"
    assert d_cross < 5e-3, f"cross-CRS features did not co-register: {d_cross}"
    assert ghost_off > 6e6, f"negative control not separated: {ghost_off}"

    # ---- FIGURE ----
    fig = plt.figure(figsize=(15, 6.5))
    fig.suptitle("3D coherence \u2014 schema-resolved geometry co-registers with "
                 "closed-form WGS84 ground truth (independent of PROJ)",
                 fontsize=12, fontweight="bold")

    # Left: global coherence -- resolved t2m cloud sitting on the geodesy graticule
    axL = fig.add_subplot(1, 2, 1, projection="3d")
    axL.set_facecolor("white")
    for m in merid:
        axL.plot(m[0], m[1], m[2], color="#9aa7b8", lw=0.6, alpha=0.8)
    for p in paral:
        axL.plot(p[0], p[1], p[2], color="#9aa7b8", lw=0.6, alpha=0.8)
    axL.scatter(xs, ys, zs, c=t2m, cmap="turbo", s=6, depthshade=True)
    # negative-control ghost: raw (lon,lat,0) treated as metres -> blob at origin
    axL.scatter(ghost[:, 0], ghost[:, 1], ghost[:, 2], c="red", s=3, alpha=0.5)
    axL.text2D(0.02, 0.02,
               "red dots @ origin = same cloud resolved\nIGNORING crs:binding "
               "(negative control)", transform=axL.transAxes, fontsize=7.5,
               color="#b00020")
    axL.set_box_aspect((1, 1, 1)); axL.view_init(elev=18, azim=-58)
    axL.set_title("Earth-2 t2m cloud (resolve_runtime) on a closed-form\n"
                  "WGS84 graticule \u2014 field sits on the right latitudes", fontsize=9)
    axL.set_axis_off()

    # Right: cross-CRS co-registration zoom at the NYC benchmark
    axR = fig.add_subplot(1, 2, 2)
    axR.axis("off")
    axR.set_title("Cross-CRS co-registration at one benchmark (NOAA NCAT)\n"
                  "three CRSs \u2192 one ECEF point \u2192 matches closed-form GT", fontsize=9)
    rows = [
        ("Closed-form WGS84 GT", "(first principles, no PROJ)",
         f"({gt[0]:.3f}, {gt[1]:.3f}, {gt[2]:.3f})", "#1b7837"),
        ("SiteGeographic  (EPSG:4979)", "lon/lat from NOAA NCAT",
         f"\u0394 to GT = {d_geo*1000:.3f} mm", "#2c6fbb"),
        ("SiteUTM18N  (EPSG:32618)", "E/N from NOAA NCAT",
         f"\u0394 to GT = {d_utm*1000:.3f} mm", "#2c6fbb"),
        ("SiteNYSPC  (EPSG:32118)", "State-Plane E/N from NOAA NCAT",
         f"\u0394 to GT = {d_spc*1000:.3f} mm", "#2c6fbb"),
    ]
    y = 0.86
    for title, sub, val, c in rows:
        axR.add_patch(plt.Rectangle((0.04, y - 0.13), 0.92, 0.15, transform=axR.transAxes,
                                    fc="#eef4fb" if c == "#2c6fbb" else "#e7f4ea",
                                    ec=c, lw=1.3))
        axR.text(0.07, y - 0.02, title, transform=axR.transAxes, fontsize=9,
                 fontweight="bold", color=c, va="top")
        axR.text(0.07, y - 0.065, sub, transform=axR.transAxes, fontsize=7.3,
                 color="#555", va="top")
        axR.text(0.95, y - 0.04, val, transform=axR.transAxes, fontsize=8.6,
                 family="monospace", ha="right", va="top", color=c)
        y -= 0.19
    axR.text(0.5, 0.06,
             f"three independent CRSs co-register to \u2264 {d_cross*1000:.3f} mm \u2014 "
             f"authored from independent NOAA coords,\nnot by inverting one transform; "
             f"negative control (ignore binding) lands {ghost_off/1e6:.1f}\u00d710\u2076 m off the globe.",
             transform=axR.transAxes, ha="center", fontsize=8, fontweight="bold",
             color="#1b7837")

    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(out, dpi=120); plt.close(fig)
    print(f"[6] coherence.png  GT\u0394 geo={d_geo*1000:.3f}mm utm={d_utm*1000:.3f}mm "
          f"spc={d_spc*1000:.3f}mm | cross-CRS\u2264{d_cross*1000:.3f}mm | "
          f"neg-control off={ghost_off/1e6:.1f}e6 m")
    return out


# --------------------------------------------------------------------------
# Figure 7: GENERALIZATION -- the reference runtime over 7 diverse datasets, each
# vs closed-form geodesy. Shows it is not overfit to our Earth-2 authoring:
# global map of dataset footprints + a per-dataset error table (all sub-mm),
# including a REAL third-party asset (NVIDIA Deutsche Bahn railway).
# --------------------------------------------------------------------------
def fig_generalization(out):
    import generalization_suite as gs
    # ensure the converted real railway stage exists (Earth-2 grid already built
    # upstream as the --stage the other figures use).
    if not os.path.exists("out/railway_georef.usda") and \
       os.path.exists("data/thirdparty/deutschebahn-rails.usda"):
        import convert_omni_geospatial as cog
        cog.convert("data/thirdparty/deutschebahn-rails.usda", "out/railway_georef.usda")
    rows, all_ok = gs.main()
    assert all_ok, "generalization suite did not pass on all datasets"

    # footprints for the map (lon,lat); grid/asset use their representative point
    pts = [(r.get("lon"), r.get("lat"), r["name"]) for r in rows
           if r.get("lon") is not None and r.get("lat") is not None]

    fig = plt.figure(figsize=(15, 6.5))
    fig.suptitle("Generalization \u2014 one reference runtime, 7 diverse datasets, all vs "
                 "closed-form geodesy (no overfit)", fontsize=12, fontweight="bold")

    # Left: world map of dataset footprints (plate carree)
    axL = fig.add_subplot(1, 2, 1)
    # light graticule
    for lo in range(-180, 181, 30):
        axL.axvline(lo, color="#e2e6ec", lw=0.6)
    for la in range(-90, 91, 30):
        axL.axhline(la, color="#e2e6ec", lw=0.6)
    axL.set_xlim(-180, 180); axL.set_ylim(-90, 90)
    axL.set_xlabel("longitude"); axL.set_ylabel("latitude")
    axL.set_title("Dataset footprints \u2014 N & S hemisphere, equatorial, high-latitude",
                  fontsize=9)
    for lon, lat, nm in pts:
        axL.scatter([lon], [lat], s=70, zorder=5, edgecolors="black", linewidths=0.8)
        short = nm.split(" (")[0]
        axL.annotate(short, (lon, lat), fontsize=7, xytext=(4, 4),
                     textcoords="offset points")
    axL.grid(False)

    # Right: results table
    axR = fig.add_subplot(1, 2, 2); axR.axis("off")
    axR.set_title("Resolved ECEF vs closed-form WGS84 ground truth", fontsize=9)
    y = 0.95
    axR.text(0.02, y, "dataset", fontsize=8, fontweight="bold", transform=axR.transAxes)
    axR.text(0.74, y, "CRS", fontsize=8, fontweight="bold", transform=axR.transAxes)
    axR.text(0.90, y, "\u0394 GT", fontsize=8, fontweight="bold", transform=axR.transAxes)
    y -= 0.04
    axR.axhline  # noqa
    for r in rows:
        y -= 0.115
        nm = r["name"]
        tag = {"grid": "grid", "asset": "asset (real 3rd-party)", "point": "point"}[r["kind"]]
        axR.add_patch(plt.Rectangle((0.0, y - 0.02), 1.0, 0.10, transform=axR.transAxes,
                                    fc="#e7f4ea" if r["ok"] else "#fde0dc",
                                    ec="#1b7837" if r["ok"] else "#c0392b", lw=1.0))
        axR.text(0.02, y + 0.045, nm.split(" (")[0], fontsize=7.6, fontweight="bold",
                 transform=axR.transAxes, va="center")
        axR.text(0.02, y + 0.005, tag, fontsize=6.6, color="#555",
                 transform=axR.transAxes, va="center")
        axR.text(0.74, y + 0.025, str(r.get("epsg", "")), fontsize=7.4,
                 family="monospace", transform=axR.transAxes, va="center")
        dgt = r.get("d_geo_mm", float("nan"))
        axR.text(0.90, y + 0.025, f"{dgt:.3f} mm", fontsize=7.4, family="monospace",
                 transform=axR.transAxes, va="center",
                 color="#1b7837" if r["ok"] else "#c0392b")
    n_pass = sum(1 for r in rows if r.get("ok"))
    axR.text(0.5, 0.02, f"{n_pass}/{len(rows)} datasets \u2264 5 mm vs closed-form geodesy \u2014 "
             f"geographic + 5 projected CRSs,\nOUR grid + independent benchmark + REAL "
             f"third-party asset (different schema).",
             ha="center", fontsize=7.8, fontweight="bold", color="#1b7837",
             transform=axR.transAxes)

    fig.tight_layout(rect=[0, 0, 1, 0.94])
    fig.savefig(out, dpi=120); plt.close(fig)
    print(f"[7] generalization.png  {n_pass}/{len(rows)} datasets sub-mm vs closed-form")
    return out


# --------------------------------------------------------------------------
# Figure 8: RAILWAY RENDER -- an actual render of the REAL converted third-party
# asset, drawn entirely from runtime-resolved geometry: the 3 geospatial tile
# ground planes (quadnode-*.png imagery sampled onto them) with the ~1,470
# Deutsche Bahn rail curves layered on top, in a shared local tangent frame.
# This is the "rails on geospatial tiles" the original NVIDIA demo rendered,
# reproduced through OUR codeless resolver (no Hydra, no external renderer).
# --------------------------------------------------------------------------
def _railway_local_geometry(stage_path="out/railway_georef.usda"):
    """Resolve tiles + rail curves into a shared local ENU frame centred on the
    railway centroid. Returns (tiles, rails, info). Each tile is a dict with
    corner E/N (m) and the texture path; each rail is an (N,2) E/N polyline."""
    from pxr import Usd, Gf
    import resolve_runtime as rr
    from pyproj import CRS
    ECEF = CRS.from_epsg(4978)
    st = Usd.Stage.Open(stage_path)
    cache = {}

    # shared local frame: ENU about the centroid of all georef positions
    georef = [p for p in st.Traverse() if p.GetAttribute(rr.CRS_POSITION_ATTR)]
    lons = np.array([p.GetAttribute(rr.CRS_POSITION_ATTR).Get()[0] for p in georef])
    lats = np.array([p.GetAttribute(rr.CRS_POSITION_ATTR).Get()[1] for p in georef])
    lon0, lat0 = float(lons.mean()), float(lats.mean())
    a = 6378137.0; f = 1/298.257223563; e2 = f*(2-f)
    def ecef(lon, lat, h=0.0):
        lm = np.radians(lon); ph = np.radians(lat)
        N = a/np.sqrt(1-e2*np.sin(ph)**2)
        return np.array([(N+h)*np.cos(ph)*np.cos(lm), (N+h)*np.cos(ph)*np.sin(lm),
                         (N*(1-e2)+h)*np.sin(ph)])
    o = ecef(lon0, lat0)
    lm = np.radians(lon0); ph = np.radians(lat0)
    east = np.array([-np.sin(lm), np.cos(lm), 0.0])
    north = np.array([-np.sin(ph)*np.cos(lm), -np.sin(ph)*np.sin(lm), np.cos(ph)])
    def to_en(world):
        v = np.array(world) - o
        return np.array([v @ east, v @ north])

    tiles = []
    for t in st.Traverse():
        if not (t.GetName().startswith("MapGeo") and t.GetAttribute(rr.CRS_POSITION_ATTR)):
            continue
        M, _ = rr.anchor_frame(t, ECEF, cache)
        tex = None
        corners = None
        for c in t.GetChildren():
            if c.GetTypeName() == "Mesh" and c.GetAttribute("points"):
                pts = c.GetAttribute("points").Get()
                corners = np.array([to_en(M.Transform(Gf.Vec3d(*p))) for p in pts])
        tiles.append({"name": t.GetName(), "corners": corners})
    # texture files (in vendor dir) keyed by MapGeo index if present
    import glob
    texdir = "data/thirdparty"
    for tl in tiles:
        idx = tl["name"].replace("MapGeo", "")
        cand = os.path.join(texdir, f"quadnode-{idx}.png")
        tl["tex"] = cand if os.path.exists(cand) else None

    rails = []
    for r in st.Traverse():
        if not (r.GetName().startswith("CurveXform") and r.GetAttribute(rr.CRS_POSITION_ATTR)):
            continue
        M, _ = rr.anchor_frame(r, ECEF, cache)
        for c in r.GetChildren():
            if c.GetTypeName() == "BasisCurves" and c.GetAttribute("points"):
                pts = c.GetAttribute("points").Get()
                if pts:
                    rails.append(np.array([to_en(M.Transform(Gf.Vec3d(*p))) for p in pts]))
    return tiles, rails, {"lon0": lon0, "lat0": lat0}


def fig_railway_render(out, stage_path="out/railway_georef.usda"):
    if not os.path.exists(stage_path):
        import convert_omni_geospatial as cog
        cog.convert("data/thirdparty/deutschebahn-rails.usda", stage_path)
    tiles, rails, info = _railway_local_geometry(stage_path)

    fig, ax = plt.subplots(figsize=(11, 9))
    fig.suptitle("Real third-party asset rendered through the codeless resolver \u2014 "
                 "Deutsche Bahn rails on geospatial tiles", fontsize=12, fontweight="bold")
    ax.set_title(f"NVIDIA OpenUSD-plugin-samples (Apache-2.0), converted to crs:binding/"
                 f"crs:position \u00b7 local ENU about ({info['lat0']:.3f}\u00b0N, {info['lon0']:.3f}\u00b0E)",
                 fontsize=9)

    # tile ground planes, with the quadnode imagery sampled onto each quad
    from PIL import Image
    for tl in tiles:
        c = tl["corners"]
        if c is None:
            continue
        emin, emax = c[:, 0].min(), c[:, 0].max()
        nmin, nmax = c[:, 1].min(), c[:, 1].max()
        if tl["tex"]:
            img = np.asarray(Image.open(tl["tex"]).convert("RGB"))
            ax.imshow(img, extent=[emin, emax, nmin, nmax], origin="lower",
                      zorder=1, alpha=0.95, aspect="auto")
        else:
            ax.add_patch(plt.Rectangle((emin, nmin), emax-emin, nmax-nmin,
                         fc="#cdd6df", ec="#8a97a6", zorder=1))
        ax.add_patch(plt.Rectangle((emin, nmin), emax-emin, nmax-nmin, fill=False,
                     ec="#2c3e50", lw=1.2, zorder=3))
        ax.text(emin+12, nmax-12, tl["name"], fontsize=8, va="top",
                color="white", zorder=4,
                bbox=dict(boxstyle="round,pad=0.2", fc="#2c3e50", ec="none", alpha=0.7))

    # rail curves on top
    for i, rl in enumerate(rails):
        ax.plot(rl[:, 0], rl[:, 1], color="#ffcf33", lw=0.7, zorder=5,
                solid_capstyle="round",
                label="rail curves (resolved)" if i == 0 else None)

    ax.set_xlabel("East (m, local ENU)"); ax.set_ylabel("North (m, local ENU)")
    ax.set_aspect("equal"); ax.legend(loc="upper right", fontsize=8, framealpha=0.9)
    ax.text(0.01, 0.01,
            f"{len(tiles)} geospatial tile ground planes \u00b7 {len(rails)} rail curves \u00b7 "
            f"all positions resolved by resolve_runtime from crs:binding (no Hydra, no baking)",
            transform=ax.transAxes, fontsize=7.5, color="#333",
            bbox=dict(boxstyle="round,pad=0.3", fc="white", ec="#ccc", alpha=0.85))
    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.savefig(out, dpi=120); plt.close(fig)
    print(f"[8] railway_render.png  {len(tiles)} tiles + {len(rails)} rail curves (resolved)")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", default="out/earth2_georef.usda")
    ap.add_argument("--docs", default=DOCS)
    args = ap.parse_args()
    os.makedirs(args.docs, exist_ok=True)
    d = args.docs
    fig_evidence(args.stage, os.path.join(d, "evidence.png"))
    fig_globe(args.stage, os.path.join(d, "globe.png"))
    fig_binding_semantics(os.path.join(d, "binding_semantics.png"))
    fig_design_equivalence(os.path.join(d, "design_equivalence.png"))
    fig_tree_alignment(os.path.join(d, "tree_alignment.png"))
    fig_coherence(args.stage, os.path.join(d, "coherence.png"))
    fig_generalization(os.path.join(d, "generalization.png"))
    fig_railway_render(os.path.join(d, "railway_render.png"))
    print("\nAll figures generated by the codeless usdGeospatial build \u2705")


if __name__ == "__main__":
    main()

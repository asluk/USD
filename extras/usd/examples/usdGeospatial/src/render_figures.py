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
from pxr import Usd, UsdGeom
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
    print("\nAll figures generated by the codeless usdGeospatial build \u2705")


if __name__ == "__main__":
    main()

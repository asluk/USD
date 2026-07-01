#!/usr/bin/env python3
"""montage_overfit.py -- combine the 5 diverse-CRS anti-overfit glyph renders
into one montage (docs/multiCRS_glyph_renders.png), proving one runtime + one
unchanged scene index places a composed glyph correctly across 5 CRS families,
both hemispheres, and equator-to-78N with zero code changes."""
import os
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np

DOCS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "docs")
PANELS = [
    ("nyc",        "NYC \u2014 UTM 18N (EPSG:32618), N hemi"),
    ("sydney",     "Sydney \u2014 UTM 56S (EPSG:32756), S hemi"),
    ("wellington", "Wellington \u2014 NZTM2000 (EPSG:2193)"),
    ("quito",      "Quito \u2014 UTM 17S (EPSG:32717), ~equator"),
    ("svalbard",   "Svalbard \u2014 UTM 33N (EPSG:32633), ~78\u00b0N"),
]


def main():
    fig, axes = plt.subplots(2, 3, figsize=(15, 10))
    fig.patch.set_facecolor("#0b0e14")
    axes = axes.ravel()
    for ax, (name, cap) in zip(axes, PANELS):
        im = np.asarray(Image.open(os.path.join(DOCS, f"overfit_{name}_autoinsert.png")).convert("RGB"))
        ax.imshow(im); ax.set_facecolor("#0b0e14")
        ax.set_title(cap, color="white", fontsize=11, pad=5)
        ax.set_xticks([]); ax.set_yticks([])
        for s in ax.spines.values():
            s.set_color("#333844")
    # 6th cell: no-plugin control
    ax = axes[5]
    im = np.asarray(Image.open(os.path.join(DOCS, "overfit_nyc_noplugin.png")).convert("RGB"))
    ax.imshow(im); ax.set_facecolor("#0b0e14")
    ax.set_title("NYC \u2014 NO plugin (control): glyph NOT placed",
                 color="#e08a8a", fontsize=11, pad=5)
    ax.set_xticks([]); ax.set_yticks([])
    for s in ax.spines.values():
        s.set_color("#333844")

    fig.suptitle("Anti-overfit: SAME overlay script + SAME auto-insert scene index place a "
                 "composed glyph across 5 CRS families\n(both hemispheres, equator\u2192~78\u00b0N) "
                 "\u2014 ZERO code changes between locales; control proves the SI does the placement",
                 color="white", fontsize=12.5, y=0.99)
    fig.tight_layout(rect=[0, 0, 1, 0.93])
    out = os.path.join(DOCS, "multiCRS_glyph_renders.png")
    fig.savefig(out, dpi=110, facecolor=fig.get_facecolor())
    print("wrote", os.path.abspath(out))


if __name__ == "__main__":
    main()

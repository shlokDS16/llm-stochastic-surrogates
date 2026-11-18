"""Fig `yardsticks` (Section 7.10): median set-up SD of the simulator against the Many Labs 1 reference values, per item, in ML1-SD units, T = 1.0.

Per item, six marks (top to bottom), all on the effect scale of the item (effect divided by the item's within-site SD):
  human references (grey and black):  c_p single-site SE (open square, no interval) ; S_H between-site SD (diamond, test-inversion interval) ;
                                      |pooled human effect| (triangle, 95 percent interval)
  simulator set-up SD, median over models (blue and vermilion):
      (b) Arm L frozen A1, per-type roster, 10 wordings: filled circle with the frozen A1 interval of the median (underpowered)
      (a) Arm S raw, 4 wordings x 2 orders: filled square, no interval ; (a) Arm S draw-corrected: open square, no interval
Arm S marks are lower bounds on the spread (four wordings, two orders) and carry no interval.  Left panel: choice and rating items; right
panel: numeric items (separate axis; (b) exists only for P2c).  The set-up SD is the SD over wording x order cells of a model's effect at T = 1.0.
Reads (hashed into the .source.json): runs/acme-gstudy/A1-route-b-pertype/yardsticks.csv, runs/acme-S-gstudy/route-a-yardsticks/{raw,drawcorr}/yardsticks.csv,
runs/human-ml1-acme/arml_scales.csv.  The human values must be identical in the three files (asserted).

    .venv/Scripts/python.exe -I analysis/acme/figures/fig_yardsticks_route.py [--out paper/acme/figures/fig-yardsticks.pdf]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import results_common as rc  # noqa: E402
import results_route as R  # noqa: E402

ITEM_NAME = {"P1": "P1 framing", "P3": "P3 sunk cost", "AF": "AF allow/forbid", "QA": "QA quote", "NR": "NR reciprocity",
             "P2a": "P2a anchor, miles", "P2b": "P2b anchor, people", "P2c": "P2c anchor, feet", "P2d": "P2d anchor, births", "P4": "P4 gambler"}
SLOTS = ["c_p", "S_H", "pooled_abs", "b", "a_raw", "a_dc"]


def median_rows(tr: rc.Tracker, path: Path) -> dict:
    d = tr.csv(path, dtype={"item": str, "model": str, "yardstick": str})
    d = d[d["model"] == "__median__"]
    out: dict = {}
    for r in d.itertuples(index=False):
        out.setdefault(r.item, {})[r.yardstick] = r
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    out = rc.resolve_arg(a.out, rc.ROOT / "paper" / "acme" / "figures" / "fig-yardsticks.pdf")
    R.base_guard([out, out.with_suffix(".png")], a.out is not None)
    tr = rc.Tracker()
    yb = median_rows(tr, R.L_DIR / "A1-route-b-pertype" / "yardsticks.csv")
    yr = median_rows(tr, R.S_DIR / "route-a-yardsticks" / "raw" / "yardsticks.csv")
    yd = median_rows(tr, R.S_DIR / "route-a-yardsticks" / "drawcorr" / "yardsticks.csv")
    items_cr = R.items_order(tr, R.CR_ITEMS)
    items_num = R.items_order(tr, R.NUM_ITEMS)
    for it in yb:                                   # human values identical across files
        for ys in ("c_p", "S_H", "pooled_abs"):
            for other in (yr, yd):
                for f in ("y_est", "y_lo", "y_hi"):
                    u, v = getattr(yb[it][ys], f), getattr(other[it][ys], f)
                    assert (np.isnan(u) and np.isnan(v)) or abs(u - v) < 1e-12, (it, ys, f)

    plt = rc.style()
    from matplotlib.lines import Line2D
    fig, axes = plt.subplots(1, 2, figsize=(rc.TEXT_WIDTH_CM * rc.CM, 10.6 * rc.CM), gridspec_kw=dict(wspace=0.62, left=0.14, right=0.985, top=0.955, bottom=0.23))
    pitch, pad = 0.19, 0.55
    for ax, items, ttl in ((axes[0], items_cr, "Choice and rating items"), (axes[1], items_num, "Numeric items")):
        xmax = 0.0
        yticks = []
        for k, it in enumerate(items):
            y0 = k * (len(SLOTS) * pitch + pad)
            yticks.append(y0 + (len(SLOTS) - 1) * pitch / 2)
            h = yr[it]
            marks = {
                "c_p": (h["c_p"].y_est, None, None),
                "S_H": (h["S_H"].y_est, h["S_H"].y_lo, h["S_H"].y_hi),
                "pooled_abs": (h["pooled_abs"].y_est, h["pooled_abs"].y_lo, h["pooled_abs"].y_hi),
                "a_raw": (h["c_p"].setup_sd, None, None),
                "a_dc": (yd[it]["c_p"].setup_sd, None, None),
            }
            if it in yb:
                b = yb[it]["c_p"]
                marks["b"] = (b.setup_sd, b.setup_lo, b.setup_hi)
            for j, s in enumerate(SLOTS):
                if s not in marks:
                    continue
                v, lo, hi = marks[s]
                y = y0 + j * pitch
                has = lo is not None and not np.isnan(lo)
                kw = dict(ls="none", zorder=4)
                if s == "c_p":
                    ax.plot([v], [y], marker="s", ms=3.6, mfc="white", mec=rc.INK, mew=0.9, **kw)
                elif s == "S_H":
                    ax.plot([lo, hi], [y, y], color=rc.GREY, lw=1.0, zorder=2)
                    ax.plot([v], [y], marker="D", ms=3.4, mfc=rc.GREY, mec=rc.GREY, **kw)
                elif s == "pooled_abs":
                    ax.plot([lo, hi], [y, y], color=rc.INK, lw=1.0, zorder=2)
                    ax.plot([v], [y], marker="^", ms=3.8, mfc=rc.INK, mec=rc.INK, **kw)
                elif s == "b":
                    ax.plot([lo, hi], [y, y], color=rc.BLUE, lw=1.0, zorder=2)
                    ax.plot([v], [y], marker="o", ms=3.8, mfc=rc.BLUE, mec=rc.BLUE, **kw)
                elif s == "a_raw":
                    ax.plot([v], [y], marker="s", ms=3.6, mfc=rc.VERMILION, mec=rc.VERMILION, **kw)
                elif s == "a_dc":
                    ax.plot([v], [y], marker="s", ms=3.6, mfc="white", mec=rc.VERMILION, mew=0.9, **kw)
                xmax = max(xmax, hi if has else v)
            if k % 2 == 0:
                ax.axhspan(y0 - pitch, y0 + (len(SLOTS) - 1) * pitch + pitch, facecolor=rc.BAND, edgecolor="none", zorder=0)
        ax.set_xlim(0, xmax * 1.06)
        ax.set_ylim(len(items) * (len(SLOTS) * pitch + pad) - pad + pitch * 0.4, -pitch * 1.4)
        ax.set_xlabel("Many Labs 1 SD units, T = 1.0")
        ax.set_yticks(yticks)
        ax.set_yticklabels([ITEM_NAME[i] for i in items])
        ax.tick_params(axis="y", length=0)
        ax.grid(axis="x", color="#DDDDDD", lw=0.4, zorder=0)
        ax.set_title(ttl, pad=3)
        ax.xaxis.set_major_locator(plt.MaxNLocator(5))
    hs = [Line2D([], [], marker="s", mfc="white", mec=rc.INK, ls="none", ms=3.6, label="c: single-site SE"),
          Line2D([], [], marker="D", color=rc.GREY, ms=3.4, lw=1.0, label="S: between-site SD, interval"),
          Line2D([], [], marker="^", color=rc.INK, ms=3.8, lw=1.0, label="|pooled human effect|, interval"),
          Line2D([], [], marker="o", color=rc.BLUE, ms=3.8, lw=1.0, label="(b) Arm L set-up SD, frozen A1 interval"),
          Line2D([], [], marker="s", color=rc.VERMILION, ms=3.6, ls="none", label="(a) Arm S set-up SD, raw (no interval)"),
          Line2D([], [], marker="s", mfc="white", mec=rc.VERMILION, ms=3.6, ls="none", label="(a) Arm S set-up SD, draw-corrected (no interval)")]
    fig.legend(handles=hs, loc="lower center", ncol=2, frameon=False, bbox_to_anchor=(0.5, 0.0), handletextpad=0.4, columnspacing=1.6, labelspacing=0.3)
    outs = rc.save_figure(fig, out)
    rc.write_source(outs, "analysis/acme/figures/fig_yardsticks_route.py", R.ROUTE, tr, extra=dict(items=items_cr + items_num))


if __name__ == "__main__":
    main()

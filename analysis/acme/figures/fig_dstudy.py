"""Fig 11 (key `dstudy`): decision study.  Standard error of one model's mean effect against the number of wordings, for one and two orders,
one panel per item, with bootstrap intervals over wordings and two descriptive reference lines (the D-study target and the single-site SE c_p
of the item).  Brief: paper/acme/figures/SPEC-fig11.md.

Reads <gstudy>/dstudy.csv (item, n_w, n_o, se), <gstudy>/dstudy_boot.csv (item, n_w, n_o, se, lo, hi; written by analysis/acme/dstudy_boot.py
because gstudy.py writes no interval), human arml_scales.csv (c_p = se_single_sd_units), the target from NUMBERS['bm.dstudy.target']
(checked against the default of gstudy.dstudy_min_design).  The marker on each curve is the smallest number of wordings at which the point SE
is below c_p; the figure states it per panel.  The figure refuses to run without dstudy_boot.csv unless --no-bands is given (M9 asks for bands).

    .venv/Scripts/python.exe -I analysis/acme/figures/fig_dstudy.py [--gstudy runs/acme-gstudy/A1] [--boot <path>] [--out paper/acme/figures/fig-dstudy.pdf]
"""
from __future__ import annotations

import argparse
import inspect
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import results_common as rc  # noqa: E402


def first_below(n_w, se, thr):
    for w, v in zip(n_w, se):
        if v < thr:
            return int(w)
    return None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--gstudy", default=str(rc.DEFAULT_GSTUDY))
    ap.add_argument("--boot", default=None, help="dstudy_boot.csv (default <gstudy>/dstudy_boot.csv)")
    ap.add_argument("--no-bands", action="store_true")
    ap.add_argument("--out", default=None)
    ap.add_argument("--cols", type=int, default=5)
    a = ap.parse_args()
    gs = rc.resolve_arg(a.gstudy)
    out = rc.resolve_arg(a.out, rc.ROOT / "paper" / "acme" / "figures" / "fig-dstudy.pdf")
    boot_path = rc.resolve_arg(a.boot, gs / "dstudy_boot.csv")
    rc.guard([out, out.with_suffix(".png")], a.out is not None, gs, model_inputs=[boot_path] if not a.no_bands else [])

    from make_autonumbers import NUMBERS
    import gstudy
    target = float(NUMBERS["bm.dstudy.target"].value)
    assert target == float(inspect.signature(gstudy.dstudy_min_design).parameters["target"].default), "D-study target differs from gstudy.py"

    tr = rc.Tracker()
    ds = tr.csv(gs / "dstudy.csv", dtype={"item": str})
    sc = tr.csv(rc.HUMAN / "arml_scales.csv", dtype={"item": str}).set_index("item")
    bd = None
    if not a.no_bands:
        if not boot_path.exists():
            raise SystemExit(f"REFUSED: {boot_path} is missing; run analysis/acme/dstudy_boot.py first (or pass --no-bands, which leaves the intervals out).")
        bd = tr.csv(boot_path, dtype={"item": str})
    items = rc.items_in_order(tr, sorted(ds["item"].unique()))

    plt = rc.style()
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    ncols = a.cols
    nrows = int(np.ceil(len(items) / ncols))
    fig, axes = plt.subplots(nrows, ncols, figsize=(rc.TEXT_WIDTH_CM * rc.CM, 8.6 * rc.CM),
                             gridspec_kw=dict(wspace=0.42, hspace=0.62, left=0.075, right=0.985, top=0.925, bottom=0.215))
    axes = np.atleast_2d(axes)
    cols = {1: rc.BLUE, 2: rc.VERMILION}
    w_max = int(ds["n_w"].max())
    for k, it in enumerate(items):
        ax = axes[k // ncols, k % ncols]
        cp = float(sc.at[it, "se_single_sd_units"])
        d = ds[ds["item"] == it]
        txt = []
        for no in sorted(d["n_o"].unique()):
            g = d[d["n_o"] == no].sort_values("n_w")
            if bd is not None:
                b = bd[(bd["item"] == it) & (bd["n_o"] == no)].sort_values("n_w")
                assert np.allclose(b["se"].to_numpy(), g["se"].to_numpy()), "dstudy_boot.csv does not match dstudy.csv"
                ax.fill_between(b["n_w"], b["lo"], b["hi"], color=cols[no], alpha=0.18, lw=0, zorder=1)
            ax.plot(g["n_w"], g["se"], color=cols[no], lw=1.1, ls="-" if no == 1 else (0, (4, 1.6)), zorder=3)
            w1 = first_below(g["n_w"], g["se"], cp)
            if w1 is not None:
                ax.plot([w1], [float(g[g["n_w"] == w1]["se"].iloc[0])], marker="o", ms=3.6, mfc=cols[no], mec="white", mew=0.5, ls="none", zorder=4)
            txt.append((no, f"{w1}" if w1 is not None else f">{w_max}"))
        ax.axhline(cp, color=rc.GREY, lw=0.9, zorder=2)
        ax.axhline(target, color=rc.INK, lw=0.8, ls=":", zorder=2)
        ax.set_yscale("log")
        ax.set_xlim(1, w_max)
        ax.set_title(f"{it} {rc.SHORT.get(it, '')}", fontsize=7, pad=2)
        ax.xaxis.set_major_locator(plt.MultipleLocator(5 if w_max >= 15 else 1))
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda v, _: f"{v:g}"))
        ax.yaxis.set_minor_formatter(plt.FuncFormatter(lambda v, _: f"{v:g}" if round(v / 10 ** np.floor(np.log10(v))) in (2, 3, 5) else ""))
        ax.tick_params(axis="y", which="minor", labelsize=6.5, length=1.5)
        lo_all = [target, cp] + ([bd[bd["item"] == it]["lo"].min()] if bd is not None else [d["se"].min()])
        hi_all = [cp] + ([bd[bd["item"] == it]["hi"].max()] if bd is not None else [d["se"].max()])
        ax.set_ylim(min(lo_all) / 1.35, max(hi_all) * 1.25)
        for r_, (n_, t) in enumerate(txt):
            ax.text(0.03, 0.05 + 0.115 * (len(txt) - 1 - r_), rf"{n_} order{'s' if n_ > 1 else ''}: n$_{{\rm w}}$ {t if t.startswith('>') else '= ' + t}", transform=ax.transAxes, ha="left", va="bottom",
                    fontsize=6.5, color=cols[n_])
    for k in range(len(items), nrows * ncols):
        axes[k // ncols, k % ncols].set_visible(False)
    fig.supxlabel("Number of wordings (n$_{\\rm w}$)", fontsize=7.5, y=0.125)
    fig.supylabel("Standard error of a model's mean effect (ML1 SD units)", fontsize=7.5, x=0.012)
    h = [Line2D([], [], color=cols[1], lw=1.1, label="one order"),
         Line2D([], [], color=cols[2], lw=1.1, ls=(0, (4, 1.6)), label="two orders"),
         Patch(facecolor=rc.GREY, alpha=0.25, label="95% interval over wordings (bootstrap)") if bd is not None else None,
         Line2D([], [], color=rc.GREY, lw=0.9, label="single-site SE c of the item"),
         Line2D([], [], color=rc.INK, lw=0.8, ls=":", label=f"target {target:g}"),
         Line2D([], [], marker="o", color="none", mfc=rc.GREY, mec="white", ms=4, label="first n$_{\\rm w}$ below c (printed in the panel)")]
    fig.legend(handles=[x for x in h if x is not None], loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.005), handletextpad=0.4, columnspacing=1.3)
    outs = rc.save_figure(fig, out)
    rc.write_source(outs, "analysis/acme/figures/fig_dstudy.py", gs, tr, extra=dict(target=target, bands=bd is not None))


if __name__ == "__main__":
    main()

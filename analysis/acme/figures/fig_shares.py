"""Fig 9 (key `shares`): variance components of the manipulation effect, one dot-and-interval row per item and one pooled row, one panel
per component (no stacked bars, blueprint M9).  Brief: paper/acme/figures/SPEC-fig9.md.

Reads <gstudy>/components_by_item.csv (analysis T1: share, share_lo, share_hi), <gstudy>/pooled_shares.csv (analysis T1_3facet, stat mean),
<gstudy>/summary.json (estimator, B) and runs/human-ml1-acme/arml_scales.csv (item order).  Every mark, interval, count and label comes
from those files at run time; nothing is typed here.  Writes the PDF (vector, fonts embedded), a 600 dpi PNG and <file>.source.json.

    .venv/Scripts/python.exe -I analysis/acme/figures/fig_shares.py [--gstudy runs/acme-gstudy/A1] [--out paper/acme/figures/fig-shares.pdf]
A scratch or synthetic --gstudy requires an explicit --out outside paper/ (guard in analysis/acme/results_common.py).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import results_common as rc  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--gstudy", default=str(rc.DEFAULT_GSTUDY))
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    gs = rc.resolve_arg(a.gstudy)
    out = rc.resolve_arg(a.out, rc.ROOT / "paper" / "acme" / "figures" / "fig-shares.pdf")
    rc.guard([out, out.with_suffix(".png")], a.out is not None, gs)

    tr = rc.Tracker()
    comp = tr.csv(gs / "components_by_item.csv", dtype={"item": str, "component": str})
    pool = tr.csv(gs / "pooled_shares.csv", dtype={"component": str})
    summ = tr.json(gs / "summary.json")
    info = rc.estimator_info(summ)

    comp = comp[comp["analysis"] == "T1"]
    pool = pool[(pool["analysis"] == "T1_3facet") & (pool["stat"] == "mean")].set_index("component")
    items = rc.items_in_order(tr, sorted(comp["item"].unique()))
    comps = [c for c in rc.COMP_ORDER if c in set(comp["component"]) | set(pool.index)]
    assert set(comp["component"]) | set(pool.index) <= set(rc.COMP_ORDER), "unknown component label in the gstudy output"
    two_order = {i for i in items if "O" in set(comp[comp["item"] == i]["component"])}
    n_items = len(items)

    plt = rc.style()
    from matplotlib.lines import Line2D
    ncol = len(comps)
    fig, axes = plt.subplots(1, ncol, sharey=True, figsize=(rc.TEXT_WIDTH_CM * rc.CM, 7.4 * rc.CM),
                             gridspec_kw=dict(wspace=0.10, left=0.175, right=0.995, top=0.915, bottom=0.215))
    ypos = {it: k for k, it in enumerate(items)}
    ypool = n_items + 0.9
    allv = list(comp["share_lo"]) + list(comp["share_hi"]) + list(pool["lo"]) + list(pool["hi"])
    xmin, xmax = min(0.0, min(allv)), max(1.0, max(allv))
    pad = 0.06 * (xmax - xmin)
    xlo, xhi = max(xmin - pad, -1.0), min(xmax + pad, 2.0)
    for ax, c in zip(axes, comps):
        ax.axhspan(ypool - 0.6, ypool + 0.6, facecolor=rc.BAND, edgecolor="none", zorder=0)
        ax.axvline(0, color=rc.GREY, lw=0.5, zorder=1)
        for it in items:
            r = comp[(comp["item"] == it) & (comp["component"] == c)]
            if r.empty:
                continue                                  # term absent for this item (one-order item has no O terms)
            r = r.iloc[0]
            hollow = (c == "MW") and (it not in two_order)  # one-order item: M x W holds the residual
            lo, hi = float(r["share_lo"]), float(r["share_hi"])
            ax.plot([max(lo, xlo), min(hi, xhi)], [ypos[it]] * 2, color=rc.BLUE, lw=1.0, solid_capstyle="butt", zorder=2)
            ax.plot([float(r["share"])], [ypos[it]], marker="o", ms=3.6, mfc="white" if hollow else rc.BLUE, mec=rc.BLUE, mew=0.9,
                    ls="none", zorder=3)
            if lo < xlo:
                ax.plot([xlo], [ypos[it]], marker="<", ms=3, color=rc.BLUE, ls="none", clip_on=False)
            if hi > xhi:
                ax.plot([xhi], [ypos[it]], marker=">", ms=3, color=rc.BLUE, ls="none", clip_on=False)
        if c in pool.index:
            r = pool.loc[c]
            ax.plot([max(float(r["lo"]), xlo), min(float(r["hi"]), xhi)], [ypool] * 2, color=rc.VERMILION, lw=1.4, solid_capstyle="butt", zorder=2)
            ax.plot([float(r["estimate"])], [ypool], marker="D", ms=4.2, mfc=rc.VERMILION, mec=rc.VERMILION, ls="none", zorder=3)
        ax.set_xlim(xlo, xhi)
        ax.set_ylim(ypool + 0.9, -0.7)
        ax.set_title(rc.COMP_TEXT[c], pad=3)
        ax.xaxis.set_major_locator(plt.MaxNLocator(3, prune=None))
        ax.grid(axis="x", color="#DDDDDD", lw=0.4, zorder=0)
        ax.spines["left"].set_visible(c == comps[0])
        ax.tick_params(axis="y", left=(c == comps[0]))
    axes[0].set_yticks([ypos[i] for i in items] + [ypool])
    axes[0].set_yticklabels([f"{i}  {rc.SHORT.get(i, '')}" for i in items] + ["pooled"])
    axes[0].get_yticklabels()[-1].set_fontweight("bold")
    ival = rc.interval_word(info)
    share_txt = "untruncated" if info["share_mode"] == "untruncated" else "truncated"
    fig.supxlabel(f"Share of the variance of the manipulation effect ({share_txt} components; 95 percent {ival} interval, B = {info['B']})",
                  fontsize=7.5, y=0.085)
    handles = [Line2D([], [], marker="o", color=rc.BLUE, ms=3.6, lw=1.0, label="item"),
               Line2D([], [], marker="o", mfc="white", mec=rc.BLUE, color=rc.BLUE, ms=3.6, lw=1.0, label="one-order item: M×W includes the residual"),
               Line2D([], [], marker="D", color=rc.VERMILION, ms=4.0, lw=1.4, label="mean over items (pooled)")]
    fig.legend(handles=handles, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, -0.005), handletextpad=0.4, columnspacing=1.4)
    outs = rc.save_figure(fig, out)
    rc.write_source(outs, "analysis/acme/figures/fig_shares.py", gs, tr,
                    extra=dict(estimator=info["name"], components=comps, items=items))


if __name__ == "__main__":
    main()

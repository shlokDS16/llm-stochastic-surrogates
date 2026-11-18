"""Fig `shares` (Section 7.8): variance shares of the manipulation effect for the choice and rating items, by component group, columns (b) and (a).

One panel per component group (M; O and M x O; W; M x W; W x O and M x M x W x O terms; T terms summed; residual; draw), shared x axis, one row per
item.  Per item two marks, vertically offset:
  (b) Arm L frozen A1, per-type roster, 10 wordings, 4 temperatures: filled circle = share, thin solid line = frozen A1 interval (underpowered).
      A group that sums several terms has no interval (gstudy.py stores none for sums), so its mark is a point.
  (a) Arm S A1-S, strict roster, 4 wordings, 2 temperatures: open diamond = E2 share, capped bar = range over the four leave-one-wording-out
      values.  The bar is fragility over the wordings, not an interval.
The draw panel has an (a) mark only (Arm L is exact).  Numeric items are not drawn (Table results-num).
Reads (all under runs/, hashed into the .source.json): the route-table files and the per-wording files named in results_route.py.

    .venv/Scripts/python.exe -I analysis/acme/figures/fig_shares_route.py [--out paper/acme/figures/fig-shares.pdf]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import results_common as rc  # noqa: E402
import results_route as R  # noqa: E402

PANELS = [["M", "O", "W", "MW"], ["WO", "T", "res", "draw"]]
TITLE = {"M": "M", "O": "O, M×O†", "W": "W", "MW": "M×W", "WO": "W×O, M×W×O†", "T": "T terms†", "res": "Residual", "draw": "Draw (Arm S)"}
ITEM_NAME = {"P1": "P1 framing", "P3": "P3 sunk cost", "AF": "AF allow/forbid", "QA": "QA quote", "NR": "NR reciprocity"}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    out = rc.resolve_arg(a.out, rc.ROOT / "paper" / "acme" / "figures" / "fig-shares.pdf")
    R.base_guard([out, out.with_suffix(".png")], a.out is not None)
    tr = rc.Tracker()
    route = R.Route(tr)
    items = R.items_order(tr, R.CR_ITEMS)
    data = {(col, it): route.groups(col, it) for col in ("(a)", "(b)") for it in items}
    assert all(v is not None for v in data.values()), "a choice/rating item is not decomposed in (a) or (b)"

    plt = rc.style()
    from matplotlib.lines import Line2D
    fig, axes = plt.subplots(2, 4, sharex=True, sharey=True, figsize=(rc.TEXT_WIDTH_CM * rc.CM, 10.8 * rc.CM),
                             gridspec_kw=dict(wspace=0.10, hspace=0.30, left=0.185, right=0.995, top=0.955, bottom=0.315))
    ypos = {it: k for k, it in enumerate(items)}
    dy = 0.17
    xlo, xhi = -0.25, 1.05
    for r, row in enumerate(PANELS):
        for c, g in enumerate(row):
            ax = axes[r, c]
            ax.axvline(0, color=rc.GREY, lw=0.5, zorder=1)
            ax.grid(axis="x", color="#DDDDDD", lw=0.4, zorder=0)
            for it in items:
                y = ypos[it]
                eb = data[("(b)", it)].get(g)
                ea = data[("(a)", it)].get(g)
                if eb is not None:
                    if eb["lo"] is not None:
                        lo, hi = max(eb["lo"], xlo), min(eb["hi"], xhi)
                        ax.plot([lo, hi], [y - dy] * 2, color=rc.BLUE, lw=1.0, solid_capstyle="butt", zorder=2)
                        if eb["lo"] < xlo:
                            ax.plot([xlo], [y - dy], marker="<", ms=3, color=rc.BLUE, ls="none", clip_on=False, zorder=3)
                        if eb["hi"] > xhi:
                            ax.plot([xhi], [y - dy], marker=">", ms=3, color=rc.BLUE, ls="none", clip_on=False, zorder=3)
                    ax.plot([eb["share"]], [y - dy], marker="o", ms=3.6, mfc=rc.BLUE, mec=rc.BLUE, ls="none", zorder=4)
                if ea is not None:
                    ax.plot([ea["lmin"], ea["lmax"]], [y + dy] * 2, color=rc.VERMILION, lw=0.9, zorder=2)
                    for xv in (ea["lmin"], ea["lmax"]):
                        ax.plot([xv, xv], [y + dy - 0.07, y + dy + 0.07], color=rc.VERMILION, lw=0.9, zorder=2)
                    ax.plot([ea["share"]], [y + dy], marker="D", ms=3.4, mfc="white", mec=rc.VERMILION, mew=0.9, ls="none", zorder=4)
            ax.set_xlim(xlo, xhi)
            ax.set_ylim(len(items) - 0.45, -0.6)
            ax.set_title(TITLE[g], pad=3)
            ax.set_xticks([0, 0.5, 1.0])
            ax.set_xticklabels(["0", "0.5", "1"])
            ax.spines["left"].set_visible(c == 0)
            ax.tick_params(axis="y", left=(c == 0))
            ax.tick_params(axis="x", labelbottom=True)
    for r in range(2):
        axes[r, 0].set_yticks([ypos[i] for i in items])
        axes[r, 0].set_yticklabels([ITEM_NAME[i] for i in items])
    fig.supxlabel("Share of the variance of the manipulation effect (untruncated)", fontsize=8, y=0.238)
    h = [Line2D([], [], marker="o", color=rc.BLUE, ms=3.6, lw=1.0, label="(b) Arm L, 10 wordings, 4 temperatures: share and frozen A1 interval (underpowered)"),
         Line2D([], [], marker="D", mfc="white", mec=rc.VERMILION, color=rc.VERMILION, ms=3.4, lw=0.9,
                label="(a) Arm S, 4 wordings, 2 temperatures: E2 share and range over leave-one-wording-out\nvalues (fragility, not an interval)")]
    fig.legend(handles=h, loc="lower center", ncol=1, frameon=False, bbox_to_anchor=(0.5, 0.085), handletextpad=0.5, labelspacing=0.3)
    fig.text(0.5, 0.0, "† sum of several terms: no interval is stored for a sum, so the (b) mark is a point.\nArrowheads mark an interval cut at the axis limit.",
             ha="center", va="bottom", fontsize=8)
    outs = rc.save_figure(fig, out)
    rc.write_source(outs, "analysis/acme/figures/fig_shares_route.py", R.ROUTE, tr,
                    extra=dict(items=items, groups={k: R.GROUP_LABEL[k] for k in R.GROUP_KEYS}, columns=["(a) E2", "(b) 4facet"]))


if __name__ == "__main__":
    main()

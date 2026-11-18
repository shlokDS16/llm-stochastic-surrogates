"""Fig `agreement` (Section 7.7): do exact (Arm L) and sampled (Arm S) readouts give the same decomposition?  Column (e), like-for-like.

Column (e) = the intersection roster, wordings W0-W3, temperatures 0.7 and 1.0, per item; Arm S = A1-S, basis E2 (draw noise is a component);
Arm L = frozen A1 shares (four-facet analysis, no interval drawn: not interpreted at four wordings, E7b item 2).  P3 uses the forward order only
in both arms (E7b item 1), so it has no order terms.  The draw component of Arm S has no Arm L counterpart and is not drawn; the Arm S remainder
('res (remainder)') is paired with the Arm L residual ('res').
  (a) Every variance term of every choice or rating item: Arm S E2 share (x) against Arm L share (y), identity line and a band of +-BIAS_RULE
      (E7a item 3: differences under that bound are not interpreted at four wordings).  Marker shape and colour = item.  The numeric item P2c
      (3 models on the intersection roster) is drawn in grey crosses and marked unstable.
  (b) The same differences by component group (Arm S minus Arm L, sum over the terms of the group), same band.
The basis can be switched with --basis E1 (expected-effect shares, no draw noise), written to the default path only for E2.
Reads: runs/acme-gstudy/route-table/route_table.csv and the per-wording files named in results_route.py (hashed into the .source.json).

    .venv/Scripts/python.exe -I analysis/acme/figures/fig_agreement.py [--basis E2] [--out paper/acme/figures/fig-agreement.pdf]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import results_common as rc  # noqa: E402
import results_route as R  # noqa: E402

ITEM_STYLE = {"P1": (rc.BLUE, "o"), "P3": (rc.VERMILION, "s"), "AF": (rc.GREEN, "^"), "QA": (rc.ORANGE, "D"), "NR": (rc.PURPLE, "v")}
ITEM_NAME = {"P1": "P1 framing", "P3": "P3 sunk cost", "AF": "AF allow/forbid", "QA": "QA quote", "NR": "NR reciprocity", "P2c": "P2c anchor, feet (unstable)"}
GROUP_ROWS = [g for g in R.GROUP_KEYS if g != "draw"]
GTITLE = {"M": "M", "O": "O, M×O", "W": "W", "MW": "M×W", "WO": "W×O, M×W×O", "T": "T terms", "res": "Residual"}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--basis", default="E2", choices=["E1", "E2"])
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    default = rc.ROOT / "paper" / "acme" / "figures" / "fig-agreement.pdf"
    if a.basis != "E2" and a.out is None:
        raise SystemExit("REFUSED: --basis E1 needs an explicit --out (the paper figure is the E2 version)")
    out = rc.resolve_arg(a.out, default)
    R.base_guard([out, out.with_suffix(".png")], a.out is not None)
    tr = rc.Tracker()
    route = R.Route(tr)
    items = R.items_order(tr, R.CR_ITEMS)
    pts = {}                     # (item, term) -> (arm S share, arm L share)
    for it in items + ["P2c"]:
        s, l = route.terms("(e)-ArmS", it, a.basis), route.terms("(e)-ArmL", it, "A1")
        assert s and l, f"{it} missing in column (e)"
        for t in sorted(set(s) & set(l) - {"draw"}):
            pts[(it, t)] = (s[t], l[t])
        assert set(l) <= set(s), (it, set(l) - set(s))
    gdiff = {}
    for it in items + ["P2c"]:
        gs, gl = route.groups("(e)-ArmS", it, a.basis), route.groups("(e)-ArmL", it)
        for g in GROUP_ROWS:
            if g in gs and g in gl:
                gdiff[(it, g)] = gs[g]["share"] - gl[g]["share"]

    plt = rc.style()
    from matplotlib.lines import Line2D
    fig = plt.figure(figsize=(rc.TEXT_WIDTH_CM * rc.CM, 9.0 * rc.CM))
    ax = fig.add_axes([0.095, 0.325, 0.36, 0.625])
    bx = fig.add_axes([0.625, 0.325, 0.365, 0.625])
    allv = np.array([v for xy in pts.values() for v in xy])
    lo, hi = np.floor(allv.min() * 10) / 10 - 0.05, np.ceil(allv.max() * 10) / 10 + 0.05
    b = R.BIAS_RULE
    xx = np.array([lo, hi])
    ax.fill_between(xx, xx - b, xx + b, facecolor=rc.BAND, edgecolor="none", zorder=0)
    ax.plot(xx, xx, color=rc.GREY, lw=0.6, zorder=1)
    for (it, t), (x, y) in pts.items():
        if it == "P2c":
            ax.plot([x], [y], marker="x", ms=3.6, mew=0.9, color=rc.GREY, ls="none", zorder=3)
        else:
            col, mk = ITEM_STYLE[it]
            ax.plot([x], [y], marker=mk, ms=3.4, mfc=col, mec="white", mew=0.3, ls="none", alpha=0.95, zorder=4)
    ax.set_xlim(lo, hi)
    ax.set_ylim(lo, hi)
    ax.set_aspect("equal", adjustable="box")
    ax.set_xlabel(f"Arm S share ({a.basis}; sampled answers)")
    ax.set_ylabel("Arm L share (exact answer probabilities)")
    ax.grid(color="#DDDDDD", lw=0.4, zorder=0)
    ax.set_title("(a) every variance term", loc="left", pad=3)

    ypos = {g: k for k, g in enumerate(GROUP_ROWS)}
    xs = [v for v in gdiff.values()]
    m = max(abs(min(xs)), abs(max(xs)), b) * 1.08
    bx.axvspan(-b, b, facecolor=rc.BAND, edgecolor="none", zorder=0)
    bx.axvline(0, color=rc.GREY, lw=0.6, zorder=1)
    ids = items + ["P2c"]
    off = np.linspace(-0.3, 0.3, len(ids))
    for k, it in enumerate(ids):
        for g in GROUP_ROWS:
            if (it, g) not in gdiff:
                continue
            y = ypos[g] + off[k]
            if it == "P2c":
                bx.plot([gdiff[(it, g)]], [y], marker="x", ms=3.4, mew=0.9, color=rc.GREY, ls="none", zorder=3)
            else:
                col, mk = ITEM_STYLE[it]
                bx.plot([gdiff[(it, g)]], [y], marker=mk, ms=3.0, mfc=col, mec="white", mew=0.3, ls="none", zorder=4)
    bx.set_xlim(-m, m)
    bx.set_ylim(len(GROUP_ROWS) - 0.4, -0.6)
    bx.set_yticks(range(len(GROUP_ROWS)))
    bx.set_yticklabels([GTITLE[g] for g in GROUP_ROWS])
    bx.set_xlabel("Arm S share minus Arm L share (group sum)")
    bx.grid(axis="x", color="#DDDDDD", lw=0.4, zorder=0)
    bx.set_title("(b) by component group", loc="left", pad=3)
    h = [Line2D([], [], marker=ITEM_STYLE[i][1], color=ITEM_STYLE[i][0], ls="none", ms=3.6, label=ITEM_NAME[i]) for i in items]
    h.append(Line2D([], [], marker="x", color=rc.GREY, ls="none", ms=3.6, mew=0.9, label=ITEM_NAME["P2c"]))
    fig.legend(handles=h, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 0.095), handletextpad=0.3, columnspacing=1.4, labelspacing=0.3)
    fig.text(0.5, 0.0, f"Grey band: differences below {R.BIAS_RULE:g} are not interpreted at four wordings (E7a).\nDraw component of Arm S not drawn (no Arm L counterpart).",
             ha="center", va="bottom", fontsize=8)
    outs = rc.save_figure(fig, out)
    rc.write_source(outs, "analysis/acme/figures/fig_agreement.py", R.ROUTE, tr, extra=dict(basis=a.basis, items=items + ["P2c"], band=b, n_points=len(pts)))


if __name__ == "__main__":
    main()

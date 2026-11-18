"""Fig 5 (key `validation`): human comparators and fidelity metrics, two panels.  Brief: paper/acme/figures/SPEC-fig5.md.

(a) human reference types listed by the eligible studies; (b) metric types assigned to the human comparison.  Design-weighted
shares of eligible studies for the first and the second coding pass, 95 percent design-based intervals where the field met the
agreement rule; two unconnected marks without an interval where it failed.

Reads runs/rq234-final/rq3.csv; every plotted value is asserted against NUMBERS (val.ref.*, val.met.*) before drawing.
Writes paper/acme/figures/fig-validation.pdf (vector, fonts embedded) and a 600 dpi PNG (--png-dir, default next to the PDF).
Run from the project root:  .venv/Scripts/python.exe -I analysis/acme/figures/fig_validation.py
"""
from __future__ import annotations

import argparse
import itertools
import csv
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "analysis" / "acme"))
import results_common as rc  # noqa: E402  (records the files read, for the .source.json)
_REC = rc.record_reads()
from make_autonumbers import NUMBERS  # noqa: E402

# ------------------------------------------------------------------------------------------------ style (shared by Figs 3, 5, 6)
CM = 1 / 2.54
TEXT_WIDTH_CM = 455.24408 / 72.27 * 2.54  # \textwidth of the ACME wrapper (sn-jnl, iicol): 16.0 cm
INK, GREY, BAND, BAND_EDGE = "#222222", "#555555", "#F0F0F0", "#C4C4C4"
P1, P2 = "#0072B2", "#D55E00"                       # first pass, second pass (Okabe and Ito 2008)
plt.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans"], "font.size": 8, "axes.labelsize": 8,
    "xtick.labelsize": 8, "ytick.labelsize": 8, "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "xtick.major.size": 2.5, "ytick.major.size": 2.5, "hatch.linewidth": 0.5, "pdf.fonttype": 42, "ps.fonttype": 42,
    "axes.spines.top": False, "axes.spines.right": False, "savefig.dpi": 600, "pdf.compression": 6,
})
MS = 4.4                 # marker size (pt)
DY = 0.20                # vertical offset of the two passes (row units)
PASSES = ((1, "claude", "first pass", P1, "o"), (2, "codex", "second pass", P2, "D"))


def draw_pass_mark(ax, y, x, pidx, interval=None, cap=None):
    """One pass: interval line (if any) then the mark; first pass filled circle, second pass open diamond."""
    _, _, _, col, shp = PASSES[pidx - 1]
    yy = y - DY if pidx == 1 else y + DY
    if interval is not None:
        ax.plot(interval, [yy, yy], color=col, linewidth=1.0, solid_capstyle="butt", zorder=3)
    if cap is not None:     # exact upper bound of a zero estimate: bar ending in a cap
        ax.plot([x, cap], [yy, yy], color=col, linewidth=1.0, solid_capstyle="butt", zorder=3)
        ax.plot([cap], [yy], marker="|", color=col, markersize=4.5, markeredgewidth=1.0, zorder=3)
    face = col if pidx == 1 else "white"
    ax.plot([x], [yy], marker=shp, markersize=MS if pidx == 1 else MS + 0.3, markerfacecolor=face, markeredgecolor=col,
            markeredgewidth=1.0, linestyle="none", zorder=4, clip_on=False)


def band(ax, y0, y1):
    ax.axhspan(y0, y1, facecolor=BAND, edgecolor=BAND_EDGE, hatch="////", linewidth=0, zorder=0)


# ------------------------------------------------------------------------------------------------------------------- data + checks
def f(x: str) -> float:
    return float(x)


def load():
    rows = {r["feature"]: r for r in csv.DictReader(open(ROOT / "runs/rq234-final/rq3.csv", encoding="utf-8"))}
    n1, n2 = int(NUMBERS["rm.nElig1"].value), int(NUMBERS["rm.nElig2"].value)
    assert (n1, n2) == (80, 81)
    for r in rows.values():
        assert int(r["claude_n_domain"]) == n1 and int(r["codex_n_domain"]) == n2, r["feature"]
    return rows


def check_value(r, prefix, interval: bool):
    """Assert the plotted estimate (and interval) against the \\NUM keys that the text prints."""
    for pidx, col, *_ in PASSES:
        assert NUMBERS[f"{prefix}.p{pidx}"].value == f"{f(r[f'{col}_est_pct']):.1f}", (prefix, pidx)
        assert NUMBERS[f"{prefix}.p{pidx}k"].value == str(int(r[f"{col}_k"])), (prefix, pidx)
        if interval:
            assert NUMBERS[f"{prefix}.p{pidx}lo"].value == f"{f(r[f'{col}_lo_pct']):.1f}", (prefix, pidx, "lo")
            assert NUMBERS[f"{prefix}.p{pidx}hi"].value == f"{f(r[f'{col}_hi_pct']):.1f}", (prefix, pidx, "hi")
        else:
            assert f"{prefix}.p{pidx}lo" not in NUMBERS, (prefix, "an interval key exists for a failed field")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--png-dir", default=None)
    args = ap.parse_args()
    out_dir = ROOT / "paper" / "acme" / "figures"
    png_dir = Path(args.png_dir) if args.png_dir else out_dir
    rows = load()

    # ---- panel (a): human reference types (all five fields met the rule)
    a_spec = [("published_norms", "Published norms", "val.ref.norms"), ("own_sample", "Own sample", "val.ref.own"),
              ("none", "No human comparison", "val.ref.none"), ("crowd_norms", "Crowd norms", "val.ref.crowd"),
              ("replication_dataset", "Replication dataset\n(multi-site)", None)]
    for typ, lab, key in a_spec:
        r = rows[f"rq3|types_any|{typ}"]
        assert r["passes_v012_rule"] == "True", typ
        if key:
            check_value(r, key, True)
    repl = rows["rq3|types_any|replication_dataset"]
    ub = {}
    for pidx, col, *_ in PASSES:
        assert f(repl[f"{col}_est_pct"]) == 0.0 and f(repl[f"{col}_lo_pct"]) == 0.0 and f(repl[f"{col}_hi_pct"]) == 0.0
        lo_s, hi_s = repl[f"{col}_cp_unweighted_pct"].split("-")
        assert f(lo_s) == 0.0
        ub[pidx] = f(hi_s)
        assert NUMBERS[f"val.ref.repl.ub{pidx}"].value == f"{ub[pidx]:.1f}"
        assert NUMBERS[f"val.ref.repl.p{pidx}k"].value == repl[f"{col}_k"] == "0"
        assert NUMBERS[f"val.ref.repl.n{pidx}"].value == repl[f"{col}_n_domain"]

    # ---- panel (b): metric types, grouped by the rule status read from the data
    b_order = [("accuracy", "Accuracy against a key", "val.met.acc"),
               ("human_correlation", "Correlation with\nhuman responses", "val.met.cor"),
               ("effect_size", "Effect size", "val.met.es"), ("bias_magnitude", "Bias magnitude", "val.met.bias"),
               ("choice_distribution", "Choice distribution", "val.met.choice"), ("other", "Other", "val.met.oth")]
    passed = [t for t in b_order if rows[f"rq3|outcome_types|{t[0]}"]["passes_v012_rule"] == "True"]
    failed = [t for t in b_order if rows[f"rq3|outcome_types|{t[0]}"]["passes_v012_rule"] == "False"]
    assert [t[0] for t in passed] == ["accuracy", "human_correlation"], passed
    assert [t[0] for t in failed] == ["effect_size", "bias_magnitude", "choice_distribution", "other"], failed
    # the two sparse types are omitted: they have no kappa and at most one study
    for typ in ("agreement", "effect"):
        r = rows[f"rq3|outcome_types|{typ}"]
        assert r["kappa"] == "" and max(int(r["claude_k"]), int(r["codex_k"])) <= 1
    for typ, lab, key in passed:
        check_value(rows[f"rq3|outcome_types|{typ}"], key, True)
    kap = {}
    for typ, lab, key in failed:
        r = rows[f"rq3|outcome_types|{typ}"]
        check_value(r, key, False)
        kap[typ] = f(r["kappa"])
    ks = [f"{v:.2f}" for v in kap.values()]
    assert min(ks, key=float) == NUMBERS["val.met.failKlo"].value and max(ks, key=float) == NUMBERS["val.met.failKhi"].value

    # ---------------------------------------------------------------- figure geometry (cm)
    Wc, Hc = TEXT_WIDTH_CM, 8.1
    fig = plt.figure(figsize=(Wc * CM, Hc * CM))

    def ax_cm(x0, y0, w, h):
        return fig.add_axes([x0 / Wc, y0 / Hc, w / Wc, h / Hc])

    def txt_cm(x, y, s, **kw):
        return fig.text(x / Wc, y / Hc, s, **kw)

    ay0, ah = 2.05, 5.2                                  # axes bottom and height, both panels (cm)
    ax_top = ay0 + ah
    xa0, xaw = 3.05, 3.55                                 # panel (a) axes
    xb0, xbw = 11.15, 2.75                                # panel (b) axes
    xlim = (-4, 104)

    def style_axes(ax, nunits):
        ax.set_xlim(*xlim)
        ax.set_ylim(nunits, 0)
        ax.set_xticks([0, 25, 50, 75, 100])
        ax.spines["bottom"].set_bounds(0, 100)
        ax.spines["left"].set_visible(False)
        ax.set_yticks([])
        ax.spines["bottom"].set_color(GREY)
        ax.tick_params(axis="x", pad=2, colors=INK)
        ax.set_xlabel("percent of eligible studies", labelpad=2)
        ax.xaxis.grid(True, color="#E6E6E6", linewidth=0.5, zorder=1)
        ax.set_axisbelow(True)

    # ---------------------------------------------------------------- panel (a)
    axa = ax_cm(xa0, ay0, xaw, ah)
    na = len(a_spec)
    style_axes(axa, na)
    pitch_a = ah / na
    for i, (typ, lab, key) in enumerate(a_spec):
        r = rows[f"rq3|types_any|{typ}"]
        yc = i + 0.5
        for pidx, col, *_ in PASSES:
            est, lo, hi = (f(r[f"{col}_{x}_pct"]) for x in ("est", "lo", "hi"))
            if typ == "replication_dataset":
                draw_pass_mark(axa, yc, 0.0, pidx, cap=ub[pidx])
            else:
                draw_pass_mark(axa, yc, est, pidx, interval=[lo, hi])
        if typ == "replication_dataset":
            assert ub[1] == ub[2]
            axa.text(9.0, yc, f"exact upper bound {ub[1]:.1f}", fontsize=8, color=GREY, ha="left", va="center")
        # labels and k/n
        txt_cm(xa0 - 0.18, ax_top - (i + 0.5) * pitch_a, lab, fontsize=8, ha="right", va="center", color=INK, linespacing=1.05)
        for pidx, col, *_ in PASSES:
            dy = 0.16 if pidx == 1 else -0.16
            if typ == "replication_dataset":
                s = f"0 of {r[f'{col}_n_domain']}"
            else:
                s = f"{int(r[f'{col}_k'])}/{int(r[f'{col}_n_domain'])}"
            txt_cm(xa0 + xaw + 0.12, ax_top - (i + 0.5) * pitch_a + dy, s, fontsize=8, ha="left", va="center", color=GREY)

    # ---------------------------------------------------------------- panel (b)
    axb = ax_cm(xb0, ay0, xbw, ah)
    # rows: 2 passed, label row (0.7 units), 4 failed
    LABEL_ROW = 0.75
    nb_units = len(passed) + LABEL_ROW + len(failed)
    style_axes(axb, nb_units)
    pitch_b = ah / nb_units
    band(axb, len(passed) + LABEL_ROW, nb_units)
    axb.plot([xlim[0] - 70, xlim[1] + 40], [len(passed), len(passed)], color=GREY, linewidth=0.6, clip_on=False, zorder=2)
    axb.text(-3.5, len(passed) + LABEL_ROW / 2, "pass-specific, no interval", fontsize=8, color=GREY, ha="left", va="center")
    ypos = {}
    for i, (typ, lab, key) in enumerate(passed):
        ypos[typ] = i + 0.5
    for i, (typ, lab, key) in enumerate(failed):
        ypos[typ] = len(passed) + LABEL_ROW + i + 0.5
    for typ, lab, key in passed + failed:
        r = rows[f"rq3|outcome_types|{typ}"]
        yc = ypos[typ]
        is_pass = (typ, lab, key) in passed
        for pidx, col, *_ in PASSES:
            est, lo, hi = (f(r[f"{col}_{x}_pct"]) for x in ("est", "lo", "hi"))
            draw_pass_mark(axb, yc, est, pidx, interval=[lo, hi] if is_pass else None)
        ytxt = ax_top - yc * pitch_b
        txt_cm(xb0 - 0.18, ytxt, lab, fontsize=8, ha="right", va="center", color=INK, linespacing=1.05)
        for pidx, col, *_ in PASSES:
            dy = 0.16 if pidx == 1 else -0.16
            txt_cm(xb0 + xbw + 0.12, ytxt + dy, f"{int(r[f'{col}_k'])}/{int(r[f'{col}_n_domain'])}", fontsize=8, ha="left",
                   va="center", color=GREY)
        if not is_pass:
            txt_cm(xb0 + xbw + 0.12 + 0.82, ytxt, f"κ {kap[typ]:.2f}", fontsize=8, ha="left", va="center", color=GREY)

    # ---------------------------------------------------------------- legend, panel letters, footer
    handles = [Line2D([], [], marker="o", color=P1, markerfacecolor=P1, markeredgecolor=P1, markersize=MS, linestyle="none",
                      markeredgewidth=1.0, label="first pass"),
               Line2D([], [], marker="D", color=P2, markerfacecolor="white", markeredgecolor=P2, markersize=MS + 0.3,
                      linestyle="none", markeredgewidth=1.0, label="second pass")]
    fig.legend(handles=handles, loc="center left", bbox_to_anchor=(0.95 / Wc, (Hc - 0.27) / Hc), ncol=2, frameon=False,
               fontsize=8, handletextpad=0.2, columnspacing=1.2, borderaxespad=0, borderpad=0)
    txt_cm(0.0, Hc - 0.27, "(a)", fontsize=9, fontweight="bold", ha="left", va="center")
    txt_cm(xb0 - 3.0, Hc - 0.27, "(b)", fontsize=9, fontweight="bold", ha="left", va="center")
    for k, line in enumerate(["Design-weighted shares of eligible studies with 95 percent design-based intervals where the",
                              "field met the agreement rule; a study can list several types; two sparse metric types",
                              "(agreement, effect) not shown."]):
        txt_cm(0.0, 0.78 - 0.31 * k, line, fontsize=8, ha="left", va="center", color=GREY)

    # ---------------------------------------------------------------- checks: no text clipped, no two texts overlap
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    fb = fig.bbox
    tx = [t for t in fig.findobj(matplotlib.text.Text) if t.get_visible() and t.get_text().strip()]
    boxes = [(t, t.get_window_extent(rend)) for t in tx]
    bad = [("clipped", t.get_text()) for t, b in boxes if b.x0 < fb.x0 or b.x1 > fb.x1 or b.y0 < fb.y0 or b.y1 > fb.y1]
    for (t1, b1), (t2, b2) in itertools.combinations(boxes, 2):
        if b1.x0 < b2.x1 - 0.5 and b2.x0 < b1.x1 - 0.5 and b1.y0 < b2.y1 - 0.5 and b2.y0 < b1.y1 - 0.5:
            bad.append(("text overlap", t1.get_text(), t2.get_text()))
    assert not bad, "layout checks failed: " + "; ".join(map(str, bad))

    out_dir.mkdir(parents=True, exist_ok=True)
    png_dir.mkdir(parents=True, exist_ok=True)
    pdf = out_dir / "fig-validation.pdf"
    fig.savefig(pdf, metadata={"Creator": "analysis/acme/figures/fig_validation.py", "Title": "fig-validation"})
    fig.savefig(png_dir / "fig-validation.png", dpi=600)
    rc.write_source_recorded([out_dir / "fig-validation.pdf", png_dir / "fig-validation.png"], "analysis/acme/figures/fig_validation.py", _REC)
    print("wrote", pdf, "and", png_dir / "fig-validation.png")


if __name__ == "__main__":
    main()

"""Fig 6 / label FigAudit (key `audit`): practice for each source of simulator uncertainty, and the per-pass trend.
Brief: paper/acme/figures/SPEC-fig6.md.

(a) design-weighted shares of eligible studies in three row groups on one axis, first and second coding pass, 95 percent
design-based interval where the field met the agreement rule, two unconnected marks without an interval where it failed (and for
the version row, whose rule is met through percent agreement only); (b) odds ratio per publication year per pass for the
perturbation rows, log axis, "not fitted" where the item has fewer than ten studies with or without it.

Reads runs/rq234-final/rq4.csv and rq4_trend.csv; every plotted share is asserted against NUMBERS (au.*, sp.f1.*, sp.f2.*) and
every trend odds ratio against au.tr.* where a key exists, before drawing.
Writes paper/acme/figures/fig-audit.pdf (vector, fonts embedded) and a 600 dpi PNG (--png-dir, default next to the PDF).
Run from the project root:  .venv/Scripts/python.exe -I analysis/acme/figures/fig_audit.py
"""
from __future__ import annotations

import argparse
import itertools
import csv
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.ticker  # noqa: E402
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
MS = 3.9                 # marker size (pt)
DY = 0.125               # vertical offset of each pass from the row centre (cm)
PASSES = ((1, "claude", "first pass", P1, "o"), (2, "codex", "second pass", P2, "D"))


def draw_pass_mark(ax, y, x, pidx, interval=None, zero_tick=False):
    """One pass: interval line (if any), then the mark; first pass filled circle, second pass open diamond."""
    _, _, _, col, shp = PASSES[pidx - 1]
    yy = y - DY if pidx == 1 else y + DY
    if interval is not None:
        ax.plot(interval, [yy, yy], color=col, linewidth=0.9, solid_capstyle="butt", zorder=3)
    if zero_tick:       # the interval is truncated at zero: small tick at zero
        ax.plot([0], [yy], marker="|", color=col, markersize=4.0, markeredgewidth=0.9, zorder=3)
    face = col if pidx == 1 else "white"
    ax.plot([x], [yy], marker=shp, markersize=MS if pidx == 1 else MS + 0.3, markerfacecolor=face, markeredgecolor=col,
            markeredgewidth=0.9, linestyle="none", zorder=4, clip_on=False)


# ------------------------------------------------------------------------------------------------------------------------- spec
# (feature in rq4.csv, label, NUMBERS prefix, has interval keys)
G1 = [("robustness_tested|yes", "At least one\njudged type", "au.any"), ("perturbation|wording", "Prompt wording", "au.pw"),
      ("perturbation|decoding", "Decoding setting", "au.pd"), ("perturbation|option_order", "Option order", "au.po"),
      ("perturbation|model_version", "Model version", "au.pv"), ("perturbation|seeds", "Seeds", "au.ps"),
      ("perturbation|contamination", "Contamination", "au.pc")]
G2 = [("f7|yes", "Two or more sampling settings", "au.smp"), ("f3|yes", "Identical prompt sampled repeatedly", "au.rep"),
      ("f9|yes", "Novel or perturbed items against\nmemorisation", "au.nov"), ("f5|yes", "Two or more wordings", "au.wrd"),
      ("f6_applicable|yes", "Option order varied, studies\nthat list options", "au.ord"),
      ("f8|yes", "Two or more model snapshots", "au.snap")]
G3 = [("f2|yes", "Decoding temperature stated", "sp.f2"), ("f12|yes", "Link to code or data", "au.code"),
      ("f1|yes", "Exact model version and query date", "sp.f1"), ("f11|yes", "Preregistration cited", "au.prereg")]
EXPECT_RULE = {"robustness_tested|yes": True, "perturbation|wording": True, "perturbation|decoding": True,
               "perturbation|option_order": False, "perturbation|model_version": False, "perturbation|seeds": False,
               "perturbation|contamination": False, "f7|yes": True, "f3|yes": True, "f9|yes": True, "f5|yes": False,
               "f6_applicable|yes": False, "f8|yes": False, "f2|yes": True, "f12|yes": True, "f1|yes": True, "f11|yes": True}
NO_INTERVAL_DESPITE_RULE = {"f1|yes"}            # rule met through percent agreement only (kappa close to zero)
TREND_ROWS = [g[0] for g in G1]
TREND_KEY = {"robustness_tested|yes": "any", "perturbation|wording": "wrd", "perturbation|option_order": "ord"}


def load():
    rows = {r["feature"]: r for r in csv.DictReader(open(ROOT / "runs/rq234-final/rq4.csv", encoding="utf-8"))}
    trend = {}
    for r in csv.DictReader(open(ROOT / "runs/rq234-final/rq4_trend.csv", encoding="utf-8")):
        trend[(r["coder"], r["feature"])] = r
    return rows, trend


def check(rows, trend):
    n1, n2 = int(NUMBERS["rm.nElig1"].value), int(NUMBERS["rm.nElig2"].value)
    assert (n1, n2) == (80, 81)
    for feat, label, key in G1 + G2 + G3:
        r = rows[f"rq4|{feat}"]
        want = (40, 45) if feat == "f6_applicable|yes" else (n1, n2)
        assert (int(r["claude_n_domain"]), int(r["codex_n_domain"])) == want, (feat, r["claude_n_domain"], r["codex_n_domain"])
        rule = r["passes_v012_rule"] == "True"
        assert rule == EXPECT_RULE[feat], (feat, "rule status changed:", rule)
        for pidx, col, *_ in PASSES:
            assert NUMBERS[f"{key}.p{pidx}"].value == f"{float(r[f'{col}_est_pct']):.1f}", (feat, pidx)
            assert NUMBERS[f"{key}.p{pidx}k"].value == str(int(r[f"{col}_k"])), (feat, pidx, "k")
            if rule and feat not in NO_INTERVAL_DESPITE_RULE and f"{key}.p{pidx}lo" in NUMBERS:
                assert NUMBERS[f"{key}.p{pidx}lo"].value == f"{float(r[f'{col}_lo_pct']):.1f}", (feat, pidx, "lo")
                assert NUMBERS[f"{key}.p{pidx}hi"].value == f"{float(r[f'{col}_hi_pct']):.1f}", (feat, pidx, "hi")
            elif not rule:
                assert f"{key}.p{pidx}lo" not in NUMBERS, (feat, "interval key for a failed field")
        if feat == "f6_applicable|yes":
            assert [NUMBERS["au.ord.n1"].value, NUMBERS["au.ord.n2"].value] == ["40", "45"]
    # intervals of every interval row must exist in the data (rule met): shares inside [0, 100]
    for feat, label, key in G1 + G2 + G3:
        r = rows[f"rq4|{feat}"]
        if EXPECT_RULE[feat] and feat not in NO_INTERVAL_DESPITE_RULE:
            for _, col, *_ in PASSES:
                lo, hi = float(r[f"{col}_lo_pct"]), float(r[f"{col}_hi_pct"])
                assert 0.0 <= lo <= float(r[f"{col}_est_pct"]) <= hi <= 100.0, (feat, col)
    # kappa of the version row as printed in the text
    assert NUMBERS["sp.f1.kappa"].value == f"{float(rows['rq4|f1|yes']['kappa']):.3f}" == "0.045"
    # preregistration: t interval truncated at zero for both passes
    for _, col, *_ in PASSES:
        assert float(rows["rq4|f11|yes"][f"{col}_lo_pct"]) == 0.0
    # trend
    for feat in TREND_ROWS:
        for pidx, col, *_ in PASSES:
            t = trend[(col, f"rq4|{feat}")]
            assert (t["passes_v012_rule"] == "True") == EXPECT_RULE[feat], (feat, col)
            assert int(t["n_domain"]) == (n1 if pidx == 1 else n2)
            if t["status"] == "fitted":
                assert int(t["events"]) >= 10 and int(t["non_events"]) >= 10, (feat, col)
                assert 0 < float(t["or_lo"]) <= float(t["OR_per_year"]) <= float(t["or_hi"])
                if feat in TREND_KEY:
                    k = f"au.tr.{TREND_KEY[feat]}.p{pidx}"
                    assert NUMBERS[k].value == f"{float(t['OR_per_year']):.2f}", k
                    assert NUMBERS[k + "lo"].value == f"{float(t['or_lo']):.2f}", k
                    assert NUMBERS[k + "hi"].value == f"{float(t['or_hi']):.2f}", k
            else:
                assert t["status"] == "descriptive_only", t["status"]
                assert min(int(t["events"]), int(t["non_events"])) < 10, (feat, col)
    nfit = {pidx: sum(trend[(col, f"rq4|{f_}")]["status"] == "fitted" for f_ in TREND_ROWS) for pidx, col, *_ in PASSES}
    return nfit


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--png-dir", default=None)
    args = ap.parse_args()
    out_dir = ROOT / "paper" / "acme" / "figures"
    png_dir = Path(args.png_dir) if args.png_dir else out_dir
    rows, trend = load()
    check(rows, trend)

    # ---------------------------------------------------------------- vertical layout of panel (a), in cm from the axes top
    HDR, GAP, SEP = 0.55, 0.10, 0.07
    ROW1, ROW2 = 0.54, 0.74            # single-line and two-line rows
    layout = []                         # (kind, payload, y_top, height)
    y = 0.0

    def add(kind, payload, h):
        nonlocal y
        layout.append((kind, payload, y, h))
        y += h

    def rowh(label):
        return ROW2 if "\n" in label else ROW1

    add("hdr", "Perturbation run (type listed by the study)", HDR)
    for feat, label, key in G1:
        add("row", (feat, label, key), rowh(label))
        if feat == "robustness_tested|yes":
            add("rule", None, 0.12)
    add("gap", None, GAP)
    add("hdr", "Variation item (variants compared in the coded text)", HDR)
    for feat, label, key in G2:
        add("row", (feat, label, key), rowh(label))
    add("gap", None, GAP)
    add("hdr", "Stated only (documentation)", HDR)
    for feat, label, key in G3:
        add("row", (feat, label, key), rowh(label))
    ah = y

    Wc = TEXT_WIDTH_CM
    top_strip, bot_strip = 0.75, 2.35
    Hc = ah + top_strip + bot_strip
    fig = plt.figure(figsize=(Wc * CM, Hc * CM))
    ax_top = Hc - top_strip
    ay0 = bot_strip

    def ax_cm(x0, y0, w, h):
        return fig.add_axes([x0 / Wc, y0 / Hc, w / Wc, h / Hc])

    def txt_cm(x, yy, s, **kw):
        return fig.text(x / Wc, yy / Hc, s, **kw)

    xa0, xaw = 4.85, 3.0
    xb0, xbw = 12.95, 3.0
    xlim_a = (-4, 104)

    # ---------------------------------------------------------------- panel (a)
    axa = ax_cm(xa0, ay0, xaw, ah)
    axa.set_xlim(*xlim_a)
    axa.set_ylim(ah, 0)
    axa.set_yticks([])
    axa.spines["left"].set_visible(False)
    axa.spines["bottom"].set_bounds(0, 100)
    axa.spines["bottom"].set_color(GREY)
    axa.set_xticks([0, 25, 50, 75, 100])
    axa.tick_params(axis="x", pad=2)
    axa.set_xlabel("percent of eligible studies", labelpad=2)
    axa.xaxis.grid(True, color="#E6E6E6", linewidth=0.5, zorder=1)
    axa.set_axisbelow(True)
    rx0 = xa0 + xaw + 0.12              # right text region
    kx = [rx0, rx0 + 0.95]              # k/n columns: first pass, second pass
    kapx = rx0 + 1.9                   # kappa column
    row_y = {}
    for kind, payload, yt, h in layout:
        yc = yt + h / 2
        if kind == "hdr":
            txt_cm(0.0, ax_top - yc, payload, fontsize=8, fontweight="bold", ha="left", va="center", color=INK)
            if yt > 0:
                fig.add_artist(Line2D([0 / Wc, (kapx + 1.0) / Wc], [(ax_top - yt) / Hc] * 2, transform=fig.transFigure,
                                      color=GREY, linewidth=0.5))
            if payload.startswith("Perturbation"):
                txt_cm(kx[0], ax_top - yc, "first", fontsize=8, ha="left", va="center", color=GREY)
                txt_cm(kx[1], ax_top - yc, "second", fontsize=8, ha="left", va="center", color=GREY)
        elif kind == "rule":
            fig.add_artist(Line2D([0 / Wc, (kapx + 1.0) / Wc], [(ax_top - yc) / Hc] * 2, transform=fig.transFigure,
                                  color="#BBBBBB", linewidth=0.5))
        elif kind == "row":
            feat, label, key = payload
            r = rows[f"rq4|{feat}"]
            rule = r["passes_v012_rule"] == "True"
            row_y[feat] = (yt, h)
            if not rule:
                axa.axhspan(yt, yt + h, facecolor=BAND, edgecolor=BAND_EDGE, hatch="////", linewidth=0, zorder=0)
            for pidx, col, *_ in PASSES:
                est, lo, hi = (float(r[f"{col}_{x}_pct"]) for x in ("est", "lo", "hi"))
                with_iv = rule and feat not in NO_INTERVAL_DESPITE_RULE
                draw_pass_mark(axa, yc, est, pidx, interval=[lo, hi] if with_iv else None,
                               zero_tick=(feat == "f11|yes"))
                txt_cm(kx[pidx - 1], ax_top - yc, f"{int(r[f'{col}_k'])}/{int(r[f'{col}_n_domain'])}", fontsize=8,
                       ha="left", va="center", color=GREY)
            txt_cm(xa0 - 0.15, ax_top - yc, label, fontsize=8, ha="right", va="center", color=INK, linespacing=1.05)
            if not rule or feat in NO_INTERVAL_DESPITE_RULE:
                kv = float(r["kappa"])
                s = f"κ {kv:.3f}" if feat in NO_INTERVAL_DESPITE_RULE else f"κ {kv:.2f}"
                txt_cm(kapx, ax_top - yc, s, fontsize=8, ha="left", va="center", color=GREY)

    # ---------------------------------------------------------------- panel (b): rows aligned with group 1 of panel (a)
    t_top = row_y[G1[0][0]][0]
    t_bot = row_y[G1[-1][0]][0] + row_y[G1[-1][0]][1]
    axb = ax_cm(xb0, ay0 + ah - t_bot, xbw, t_bot - t_top)
    axb.set_xscale("log", base=2)
    axb.set_xlim(0.2, 5.0)
    axb.set_ylim(t_bot, t_top)
    axb.set_yticks([])
    axb.spines["left"].set_visible(False)
    axb.set_xticks([0.25, 0.5, 1, 2, 4])
    axb.set_xticklabels(["0.25", "0.5", "1", "2", "4"])
    axb.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    axb.spines["bottom"].set_color(GREY)
    axb.tick_params(axis="x", pad=2)
    axb.set_xlabel("odds ratio per year", labelpad=2)
    axb.axvline(1.0, color=GREY, linewidth=0.7, zorder=2)
    axb.xaxis.grid(True, color="#E6E6E6", linewidth=0.5, zorder=1)
    axb.set_axisbelow(True)
    for feat, label, key in G1:
        yt, h = row_y[feat]
        yc = yt + h / 2
        failed = rows[f"rq4|{feat}"]["passes_v012_rule"] != "True"
        if failed:
            axb.axhspan(yt, yt + h, facecolor=BAND, edgecolor=BAND_EDGE, hatch="////", linewidth=0, zorder=0)
        for pidx, col, *_ in PASSES:
            t = trend[(col, f"rq4|{feat}")]
            if t["status"] == "fitted":
                draw_pass_mark(axb, yc, float(t["OR_per_year"]), pidx, interval=[float(t["or_lo"]), float(t["or_hi"])])
            else:
                yy = yc - DY if pidx == 1 else yc + DY
                axb.text(1.12, yy - 0.04, "not fitted", fontsize=8, color=GREY, ha="left", va="center", zorder=5)
        txt_cm(xb0 - 0.15, ax_top - yc, label, fontsize=8, ha="right", va="center", color=INK, linespacing=1.05)
    # the x axis of panel (b) is drawn at the bottom of its own rows; no spine below the empty area
    # ---------------------------------------------------------------- legend, panel letters, footer
    handles = [Line2D([], [], marker="o", color=P1, markerfacecolor=P1, markeredgecolor=P1, markersize=MS + 0.5,
                      linestyle="none", markeredgewidth=0.9, label="first pass"),
               Line2D([], [], marker="D", color=P2, markerfacecolor="white", markeredgecolor=P2, markersize=MS + 0.8,
                      linestyle="none", markeredgewidth=0.9, label="second pass")]
    fig.legend(handles=handles, loc="center left", bbox_to_anchor=(0.95 / Wc, (Hc - 0.27) / Hc), ncol=2, frameon=False,
               fontsize=8, handletextpad=0.2, columnspacing=1.2, borderaxespad=0, borderpad=0)
    txt_cm(0.0, Hc - 0.27, "(a)", fontsize=9, fontweight="bold", ha="left", va="center")
    txt_cm(xb0 - 2.35, Hc - 0.27, "(b)", fontsize=9, fontweight="bold", ha="left", va="center")
    foot = ["Design-weighted shares of eligible studies with 95 percent design-based intervals where the field met the",
            "agreement rule; no interval in the hatched bands (field failed the rule) or for the version row (rule met by",
            "percent agreement only, kappa near zero); trend fits are exploratory sensitivity displays; nonresponse bounds",
            "are in the text."]
    for k, line in enumerate(foot):
        txt_cm(0.0, 1.10 - 0.31 * k, line, fontsize=8, ha="left", va="center", color=GREY)

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
    pdf = out_dir / "fig-audit.pdf"
    fig.savefig(pdf, metadata={"Creator": "analysis/acme/figures/fig_audit.py", "Title": "fig-audit"})
    fig.savefig(png_dir / "fig-audit.png", dpi=600)
    rc.write_source_recorded([out_dir / "fig-audit.pdf", png_dir / "fig-audit.png"], "analysis/acme/figures/fig_audit.py", _REC)
    print("wrote", pdf, "and", png_dir / "fig-audit.png", f"(height {Hc:.2f} cm)")


if __name__ == "__main__":
    main()

"""Fig 3 (key `corpus`): corpus-to-structure, two panels.  Brief: paper/acme/figures/SPEC-fig3.md.

(a) records by first named paradigm family and publication year (stacked bars, complete frame, no intervals);
(b) share of records naming each model family, by year bin (annotated heat map, same code path as the \\NUM{sp.mf*} keys).

Reads only runs/ (and the coded frame through make_autonumbers.rq1_model_family_by_bin). Asserts every plotted value against
runs/ files and NUMBERS before drawing.  Writes paper/acme/figures/fig-corpus.pdf (vector, fonts embedded) and a 600 dpi PNG
to the scratch folder given by --png-dir (default: next to the PDF, fig-corpus.png).

Run from the project root:  .venv/Scripts/python.exe -I analysis/acme/figures/fig_corpus.py
"""
from __future__ import annotations

import argparse
import itertools
import csv
import json
import re
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib import cm  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "analysis" / "acme"))
import results_common as rc  # noqa: E402  (records the files read, for the .source.json)
_REC = rc.record_reads()
from make_autonumbers import NUMBERS, rq1_model_family_by_bin  # noqa: E402

# ------------------------------------------------------------------------------------------------ style (shared by Figs 3, 5, 6)
CM = 1 / 2.54
TEXT_WIDTH_CM = 455.24408 / 72.27 * 2.54  # \textwidth of the ACME wrapper (sn-jnl, iicol): 16.0 cm
INK, GREY, LIGHT = "#222222", "#555555", "#DDDDDD"
FONT = "Arial"
plt.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": [FONT, "DejaVu Sans"], "font.size": 8, "axes.labelsize": 8,
    "xtick.labelsize": 8, "ytick.labelsize": 8, "axes.linewidth": 0.6, "xtick.major.width": 0.6, "ytick.major.width": 0.6,
    "xtick.major.size": 2.5, "ytick.major.size": 2.5, "hatch.linewidth": 0.55, "pdf.fonttype": 42, "ps.fonttype": 42,
    "svg.fonttype": "none", "axes.spines.top": False, "axes.spines.right": False, "savefig.dpi": 600,
    "pdf.compression": 6,
})

# Okabe and Ito (2008) hues; hue = group, lightness step and hatch = family within the group.
BLUE, SKY, VERM, ORANGE, GREEN, LGREEN = "#0072B2", "#56B4E9", "#D55E00", "#E69F00", "#009E73", "#8FD1B5"
# stack order from the bottom; (code, label lines, face, edge, hatch)
FAMILIES = [
    ("JDM", "Judgement and decision making", BLUE, BLUE, None),
    ("HB", "Heuristics and biases", SKY, SKY, None),
    ("MOR", "Moral judgement", "white", BLUE, "////"),
    ("RE", "Reasoning", "white", SKY, "\\\\\\\\"),
    ("TOM", "Theory of mind and social cognition", VERM, VERM, None),
    ("DEV", "Developmental tasks", ORANGE, ORANGE, None),
    ("LANG", "Language and psycholinguistics", GREEN, GREEN, None),
    ("MEM", "Memory and attention", LGREEN, LGREEN, None),
    ("LEARN", "Learning and categorisation", "white", GREEN, "xxxx"),
    ("NUM", "Numerical cognition", "white", LGREEN, "...."),
    ("OTH", "Other", "#999999", "#999999", None),
    ("none", "No family named", "white", "#555555", "////"),
]
# legend text wrapped to two lines where the full name is long (same words, only line breaks)
WRAP = {"JDM": "Judgement and\ndecision making", "TOM": "Theory of mind and\nsocial cognition",
        "LANG": "Language and\npsycholinguistics", "LEARN": "Learning and\ncategorisation"}
GROUPS = [  # (label key, members in stack order) -> subsection label
    ("sec:spec-prompt", ["JDM", "HB", "MOR", "RE"]),
    ("sec:spec-task", ["TOM", "DEV"]),
    ("sec:spec-readout", ["LANG", "MEM", "LEARN", "NUM"]),
]
SECTION_FALLBACK = {"sec:spec-prompt": "4.2", "sec:spec-task": "4.1", "sec:spec-readout": "4.5"}

MODEL_ROWS = ["GPT", "Claude", "Gemini", "Llama", "Qwen", "Mistral", "OLMo", "other", "none named"]
T_RQ1B_NAME = {"GPT": "GPT", "Claude": "Claude", "Gemini": "Gemini", "Llama": "Llama", "Qwen": "Qwen", "Mistral": "Mistral",
               "OLMo": "OLMo", "other": "other", "none named": "None named"}
BIN_ORDER = ["2018-2021", "2022", "2023", "2024", "2025", "2026"]
BIN_LABEL = {"2018-2021": "2018\u201321"}


def section_numbers() -> dict[str, str]:
    """Subsection numbers from the compiled aux file if it exists; it must agree with the fallback used when it does not."""
    out = dict(SECTION_FALLBACK)
    aux = ROOT / "paper" / "journals" / "acme" / "build" / "main.aux"
    if not aux.exists():
        aux = ROOT / "paper" / "journals" / "acme" / "main.aux"
    if aux.exists():
        txt = aux.read_text(encoding="utf-8", errors="replace")
        for key in out:
            m = re.search(r"\\newlabel\{" + re.escape(key) + r"\}\{\{([0-9.]+)\}", txt)
            if m and m.group(1) != out[key]:
                raise AssertionError(f"{key}: aux says {m.group(1)}, script says {out[key]}; update SECTION_FALLBACK")
    return out


def rel_lum(rgb) -> float:
    c = np.array(rgb[:3], dtype=float)
    c = np.where(c <= 0.03928, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)
    return float(0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2])


def contrast(l1: float, l2: float) -> float:
    a, b = max(l1, l2), min(l1, l2)
    return (a + 0.05) / (b + 0.05)


# ------------------------------------------------------------------------------------------------------------------- data + checks
def load_panel_a():
    rows = list(csv.DictReader(open(ROOT / "runs/rq1-fig2-years/fig2_data.csv", encoding="utf-8")))
    rows = [r for r in rows if r["view"] == "A"]
    years = sorted({int(r["year"]) for r in rows})
    assert years == list(range(2018, 2027)), years
    data = {(int(r["year"]), r["first_family"]): int(r["n"]) for r in rows}
    codes = {c for c, *_ in FAMILIES}
    assert {f for _, f in data} == codes, ({f for _, f in data} ^ codes)
    assert {int(r["year"]) for r in rows if r["partial_year"] == "1"} == {2026}
    metrics = json.load(open(ROOT / "runs/rq1-fig2-years/metrics.json", encoding="utf-8"))
    tot = {y: sum(data[(y, c)] for c, *_ in FAMILIES) for y in years}
    for y in years:
        assert tot[y] == metrics["total_by_year"]["A"][str(y)], (y, tot[y])
    grand = sum(tot.values())
    t1a = {r["item"]: r for r in csv.DictReader(open(ROOT / "runs/rq1-tables/T-RQ1a.csv", encoding="utf-8"))}
    assert grand == int(t1a["N (denominator)"]["A_n"]) == metrics["N"]["A"] == 2022, grand
    # same series in T-RQ1d (view A, bin_type year)
    for r in csv.DictReader(open(ROOT / "runs/rq1-tables/T-RQ1d.csv", encoding="utf-8")):
        if r["view"] == "A" and r["bin_type"] == "year":
            y = int(r["bin"])
            assert int(r["total"]) == tot[y], (y, r["total"], tot[y])
            for c, *_ in FAMILIES:
                assert int(r[c]) == data[(y, c)], (y, c)
    # the \NUM year keys of Section 4
    for y in (2018, 2021, 2023, 2024, 2025, 2026):
        key = f"sp.y{y}"
        if key in NUMBERS:
            want = tot[y] if y != 2021 else None
            if want is not None:
                assert NUMBERS[key].value.replace(",", "").replace("{,}", "") == str(want), (key, NUMBERS[key].value, want)
    return years, data, tot, grand


def load_panel_b(tot, grand):
    long = rq1_model_family_by_bin("year")
    bins = [b for b in BIN_ORDER]
    assert sorted({r["bin"] for r in long}) == sorted(bins), {r["bin"] for r in long}
    nrec = {}
    for r in long:
        nrec.setdefault(r["bin"], r["n_records"])
        assert nrec[r["bin"]] == r["n_records"]
    assert sum(nrec.values()) == grand == 2022
    pooled = {"2018-2021": sum(tot[y] for y in range(2018, 2022))}
    for y in range(2022, 2027):
        pooled[str(y)] = tot[y]
    assert nrec == pooled, (nrec, pooled)
    assert [nrec[b] for b in bins] == [17, 26, 147, 302, 613, 917]
    share = {}
    named = {}
    for r in long:
        fam = r["family"]
        share[(fam, r["bin"])] = r["share_pct"]
        named[(fam, r["bin"])] = r["n_named"]
    t1b = {r["item"]: int(r["A_n"]) for r in csv.DictReader(open(ROOT / "runs/rq1-tables/T-RQ1b.csv", encoding="utf-8"))}
    for fam in MODEL_ROWS:
        assert sum(named[(fam, b)] for b in bins) == t1b[T_RQ1B_NAME[fam]], (fam, t1b[T_RQ1B_NAME[fam]])
    # the family totals as the text prints them (\NUM{sp.mf.<fam>.n})
    key = {"GPT": "gpt", "Claude": "claude", "Gemini": "gemini", "Llama": "llama", "Qwen": "qwen", "Mistral": "mistral",
           "OLMo": "olmo", "other": "other", "none named": "none"}
    for fam, k in key.items():
        v = NUMBERS[f"sp.mf.{k}.n"].value.replace("{,}", "").replace(",", "")
        assert int(v) == t1b[T_RQ1B_NAME[fam]], (fam, v)
    for fam in MODEL_ROWS:
        for b in bins:
            assert abs(share[(fam, b)] - 100.0 * named[(fam, b)] / nrec[b]) < 1e-9
    return bins, nrec, share


# ------------------------------------------------------------------------------------------------------------------------ drawing
def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--png-dir", default=None, help="folder for the 600 dpi inspection PNG (default: next to the PDF)")
    args = ap.parse_args()
    out_dir = ROOT / "paper" / "acme" / "figures"
    png_dir = Path(args.png_dir) if args.png_dir else out_dir

    years, data, tot, grand = load_panel_a()
    bins, nrec, share = load_panel_b(tot, grand)
    sec = section_numbers()

    Wc, Hc = TEXT_WIDTH_CM, 8.55
    fig = plt.figure(figsize=(Wc * CM, Hc * CM))

    def ax_cm(x0, y0, w, h, **kw):
        return fig.add_axes([x0 / Wc, y0 / Hc, w / Wc, h / Hc], **kw)

    def txt_cm(x, y, s, **kw):
        return fig.text(x / Wc, y / Hc, s, **kw)

    # ---------------------------------------------------------------- panel (a)
    ax_x0, ax_y0, ax_w, ax_h = 1.35, 3.1, 2.7, 5.0
    axa = ax_cm(ax_x0, ax_y0, ax_w, ax_h)
    xs = np.arange(len(years))
    bottoms = np.zeros(len(years))
    for code, label, face, edge, hatch in FAMILIES:
        h = np.array([data[(y, code)] for y in years], dtype=float)
        # a thin white gap between filled segments; hatched segments keep their coloured edge
        axa.bar(xs, h, 0.74, bottom=bottoms, facecolor=face, edgecolor=edge if (hatch or face == "white") else "white",
                linewidth=0.5 if (hatch or face == "white") else 0.35, hatch=hatch, zorder=2)
        bottoms += h
    assert [int(b) for b in bottoms] == [tot[y] for y in years]
    for x, y in zip(xs, years):
        axa.text(x, tot[y] + 18, f"{tot[y]:,}", ha="center", va="bottom", fontsize=8, color=INK, zorder=4, rotation=90)
    # 2026 is a partial year: dashed outline round the whole bar
    axa.add_patch(Rectangle((xs[-1] - 0.37, 0), 0.74, tot[2026], fill=False, edgecolor=INK, linewidth=0.8, linestyle=(0, (3, 2)),
                            zorder=5))
    axa.set_xlim(-0.6, len(years) - 0.4)
    axa.set_ylim(0, 1120)
    axa.set_yticks([0, 250, 500, 750, 1000])
    axa.set_yticklabels(["0", "250", "500", "750", "1000"])
    axa.set_ylabel("Records", labelpad=2)
    axa.set_xticks(xs)
    axa.set_xticklabels([str(y) if y != 2026 else "2026 (partial)" for y in years], rotation=90)
    axa.tick_params(axis="x", length=2.5, pad=2)
    axa.set_xlabel("")
    axa.yaxis.grid(True, color="#E4E4E4", linewidth=0.5, zorder=0)
    axa.set_axisbelow(True)
    axa.spines["left"].set_color(GREY)
    axa.spines["bottom"].set_color(GREY)

    # legend: stack order from the top of the stack downwards, with group brackets to the right
    lg_x0 = ax_x0 + ax_w + 0.2          # left edge of the legend block (cm)
    sw_w, sw_h = 0.36, 0.26
    leg_codes = [f[0] for f in FAMILIES][::-1]
    line_h = 0.28                          # cm per text line at 8 pt
    heights = {c: (WRAP[c].count(chr(10)) + 1 if c in WRAP else 1) for c in leg_codes}
    pad = 0.09
    y_cursor = ax_y0 + ax_h                # top of legend aligned with top of axes
    centres, band = {}, {}
    for code in leg_codes:
        hh = heights[code] * line_h + pad
        centres[code] = y_cursor - hh / 2
        band[code] = (y_cursor - hh, y_cursor)
        y_cursor -= hh
    by_code = {f[0]: f for f in FAMILIES}
    leg_texts = []
    text_x = lg_x0 + sw_w + 0.1
    for code in leg_codes:
        _, label, face, edge, hatch = by_code[code]
        yc = centres[code]
        fig.add_artist(Rectangle(((lg_x0) / Wc, (yc - sw_h / 2) / Hc), sw_w / Wc, sw_h / Hc, transform=fig.transFigure,
                                 facecolor=face, edgecolor=edge, hatch=hatch,
                                 linewidth=0.5 if (hatch or face == "white") else 0.0))
        leg_texts.append(txt_cm(text_x, yc, WRAP.get(code, label), fontsize=8, color=INK, ha="left", va="center", linespacing=0.95))
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    bx = max(t.get_window_extent(rend).x1 for t in leg_texts) / fig.dpi / CM + 0.18   # bracket just right of the longest name
    for key, members in GROUPS:
        top = max(band[c][1] for c in members) - 0.04
        bot = min(band[c][0] for c in members) + 0.04
        xs_b = [bx - 0.08, bx, bx, bx - 0.08]
        ys_b = [top, top, bot, bot]
        fig.add_artist(plt.Line2D([v / Wc for v in xs_b], [v / Hc for v in ys_b], transform=fig.transFigure, color=GREY,
                                  linewidth=0.7, solid_capstyle="butt"))
        txt_cm(bx + 0.14, (top + bot) / 2, f"Sec. {sec[key]}", fontsize=8, color=GREY, ha="left", va="center", rotation=90)

    # footer of panel (a)
    for k, line in enumerate([f"Counts of the {grand:,} records of the liberal frame;",
                              "abstract-level coding; an empty field means the",
                              "abstract is silent. Dashed bar: partial year."]):
        txt_cm(0.05, 0.78 - 0.31 * k, line, fontsize=8, color=GREY, ha="left", va="center")

    # ---------------------------------------------------------------- panel (b)
    hx0 = 9.95                              # left edge of the heat map (cm)
    ncol, nrow = len(bins), len(MODEL_ROWS)
    cw, rh = 1.0, 0.43
    hy1 = 7.2                               # top of the heat map (cm)
    hy0 = hy1 - nrow * rh
    axb = ax_cm(hx0, hy0, ncol * cw, nrow * rh)
    vmax = max(share[(f, b)] for f in MODEL_ROWS for b in bins)
    cmap = matplotlib.colormaps["cividis"]
    norm = matplotlib.colors.Normalize(vmin=0, vmax=vmax)
    for i, fam in enumerate(MODEL_ROWS):
        for j, b in enumerate(bins):
            v = share[(fam, b)]
            rgba = cmap(norm(v))
            lum = rel_lum(rgba)
            c_white, c_black = contrast(1.0, lum), contrast(lum, 0.0)
            tcol = "white" if c_white >= c_black else "black"
            assert max(c_white, c_black) >= 4.5, (fam, b, v, c_white, c_black)
            axb.add_patch(Rectangle((j, i), 1, 1, facecolor=rgba, edgecolor="white", linewidth=0.6))
            axb.text(j + 0.5, i + 0.5, f"{v:.1f}", ha="center", va="center", fontsize=8, color=tcol)
            if nrec[b] < 30:   # indicative only: dotted outline in the text colour
                axb.add_patch(Rectangle((j + 0.09, i + 0.09), 0.82, 0.82, fill=False, edgecolor=tcol, linewidth=0.7,
                                        linestyle=(0, (1, 1.4))))
    axb.set_xlim(0, ncol)
    axb.set_ylim(nrow, 0)
    for s in axb.spines.values():
        s.set_visible(False)
    axb.set_xticks([])
    axb.set_yticks(np.arange(nrow) + 0.5)
    axb.set_yticklabels(MODEL_ROWS)
    axb.tick_params(axis="y", length=0, pad=3)
    # thin rule above "none named": it is the complement of the family rows, not a family
    axb.plot([-1.6, ncol], [nrow - 1, nrow - 1], color=INK, linewidth=0.8, clip_on=False, solid_capstyle="butt")
    # column headers: bin label, n, and "partial" for 2026
    for j, b in enumerate(bins):
        cx = hx0 + (j + 0.5) * cw
        txt_cm(cx, hy1 + 0.76, BIN_LABEL.get(b, b), fontsize=8, ha="center", va="center", color=INK)
        txt_cm(cx, hy1 + 0.43, f"n={nrec[b]:,}", fontsize=8, ha="center", va="center", color=GREY)
        txt_cm(cx, hy1 + 0.10, "partial" if b == "2026" else "", fontsize=8, ha="center", va="center", color=GREY)
    # colour bar (horizontal, below the map)
    cax = ax_cm(hx0, hy0 - 0.5, ncol * cw, 0.15)
    sm = cm.ScalarMappable(norm=norm, cmap=cmap)
    cb = fig.colorbar(sm, cax=cax, orientation="horizontal")
    cb.outline.set_linewidth(0.4)
    cb.ax.tick_params(labelsize=8, length=2, width=0.5, pad=1.5)
    cb.set_ticks([0, 10, 20, 30, 40, 50, 60])
    cb.set_label("percent of records in the year bin", fontsize=8, labelpad=1.5)
    # footer of panel (b)
    for k, line in enumerate(["Shares of the frame, not estimates; rows do not",
                              "sum to 100 because a record can name several",
                              "families. Dotted cells: bins under 30 records,",
                              "indicative only."]):
        txt_cm(hx0 - 1.55, 1.24 - 0.31 * k, line, fontsize=8, color=GREY, ha="left", va="center")

    # panel letters
    txt_cm(0.0, Hc - 0.22, "(a)", fontsize=9, fontweight="bold", ha="left", va="center")
    txt_cm(hx0 - 1.55, Hc - 0.22, "(b)", fontsize=9, fontweight="bold", ha="left", va="center")

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
    pdf = out_dir / "fig-corpus.pdf"
    fig.savefig(pdf, metadata={"Creator": "analysis/acme/figures/fig_corpus.py", "Title": "fig-corpus"})
    fig.savefig(png_dir / "fig-corpus.png", dpi=600)
    rc.write_source_recorded([out_dir / "fig-corpus.pdf", png_dir / "fig-corpus.png"], "analysis/acme/figures/fig_corpus.py", _REC)
    print("wrote", pdf, "and", png_dir / "fig-corpus.png")


if __name__ == "__main__":
    main()

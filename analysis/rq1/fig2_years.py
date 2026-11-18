"""Figure 2: records per publication year by paradigm family (first family listed by the coder; 'none' = none named),
two panels: (a) view A = liberal frame, (b) view B = coder-flagged yes within A. 2026 is a partial year (search 2026-10-16).

    .venv/Scripts/python.exe -I analysis/rq1/fig2_years.py

Outputs: paper/figures/Fig2.{pdf,eps,png}; runs/rq1-fig2-years/{config.json, fig2_years.log, fig2_data.csv, metrics.json}
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rq1_common as C  # noqa: E402

RUN = C.ROOT / "runs/rq1-fig2-years"
OUT = C.ROOT / "paper/figures/Fig2"

# stack order bottom -> top, with (colour, hatch). Colour-blind-safe Okabe-Ito colours; hatches separate reused colours.
STYLE = [
    # CRP-S05: every family also has its own hatch (AIR asks for patterns as well as colour; greyscale check).
    ("LANG", C.OI["blue"], ""), ("JDM", C.OI["orange"], "\\\\\\\\"), ("TOM", C.OI["green"], "----"), ("OTH", C.OI["purple"], "||||"),
    ("RE", C.OI["sky"], "++"), ("HB", C.OI["verm"], "oo"), ("MOR", C.OI["yellow"], "**"),
    ("LEARN", C.OI["blue"], "////"), ("MEM", C.OI["orange"], "////"), ("DEV", C.OI["green"], "xxxx"), ("NUM", C.OI["purple"], "...."),
    ("none", "#D9D9D9", ""),
]


def main():
    log = C.setup_run(RUN, "fig2_years")
    rows, views, manifest = C.load_frame()
    years = list(range(2018, 2027))
    data = {}
    for v in ("A", "B"):
        cnt = defaultdict(Counter)
        for i in views[v]:
            cnt[rows[i]["year"]][C.first_family(rows[i])] += 1
        data[v] = cnt
        log.info("view %s N=%d by year %s", v, len(views[v]), {y: sum(cnt[y].values()) for y in years})
        assert sum(sum(c.values()) for c in cnt.values()) == len(views[v])
        assert set(cnt) <= set(years)
    with open(RUN / "fig2_data.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["view", "year", "first_family", "n", "partial_year"])
        for v in ("A", "B"):
            for y in years:
                for fam, _, _ in STYLE:
                    w.writerow([v, y, fam, data[v][y].get(fam, 0), int(y == 2026)])
    (RUN / "metrics.json").write_text(json.dumps({"search_date": C.SEARCH_DATE, "N": {v: len(views[v]) for v in ("A", "B")},
                                                  "total_by_year": {v: {y: sum(data[v][y].values()) for y in years} for v in ("A", "B")}}, indent=1), encoding="utf-8")

    C.mpl_setup()
    import matplotlib.pyplot as plt
    from matplotlib.patches import Patch

    fig, axes = plt.subplots(1, 2, figsize=(C.W2, 74 * C.MM), gridspec_kw={"wspace": 0.28})
    labels = {"A": "Records (view A: liberal frame)", "B": "Records (view B: coder-flagged yes)"}
    for ax, v, letter in zip(axes, ("A", "B"), "ab"):
        bottom = [0] * len(years)
        for fam, col, hatch in STYLE:
            vals = [data[v][y].get(fam, 0) for y in years]
            ax.bar(range(len(years)), vals, bottom=bottom, width=0.74, color=col, edgecolor="#111111", linewidth=0.35, hatch=hatch, zorder=2)
            bottom = [b + x for b, x in zip(bottom, vals)]
        tot = bottom
        ymax = max(tot)
        for k, (y, t) in enumerate(zip(years, tot)):
            ax.text(k, t + ymax * 0.012, f"{t}", ha="center", va="bottom", fontsize=6.3)
        # partial-year marker: dashed outline round the 2026 bar and a label
        k26 = years.index(2026)
        ax.bar(k26, tot[k26], width=0.74, fill=False, edgecolor="#111111", linewidth=0.9, linestyle=(0, (3, 2)), zorder=4)
        ax.text(k26, tot[k26] + ymax * 0.095, "partial\nyear", ha="center", va="bottom", fontsize=6.3, linespacing=0.95)
        ax.set_xticks(range(len(years)))
        ax.set_xticklabels([str(y) for y in years], rotation=0)
        ax.set_xlabel("Publication year")
        ax.set_ylabel(labels[v])
        ax.set_ylim(0, ymax * 1.24)
        ax.spines[["top", "right"]].set_visible(False)
        ax.tick_params(axis="x", labelsize=6.3, length=2.5)
        ax.yaxis.grid(True, lw=0.3, color="#BBBBBB", zorder=0)
        ax.text(-0.02, 1.02, letter, transform=ax.transAxes, fontsize=9, fontweight="bold", ha="right", va="bottom")
    handles = [Patch(facecolor=col, edgecolor="#111111", hatch=h, linewidth=0.4, label=("none named" if fam == "none" else fam)) for fam, col, h in STYLE[::-1]]
    fig.legend(handles=handles, loc="lower center", ncol=6, frameon=False, handlelength=1.6, handleheight=1.1, columnspacing=1.2, bbox_to_anchor=(0.5, -0.01))
    fig.subplots_adjust(left=0.075, right=0.995, top=0.93, bottom=0.27)
    C.save_fig(fig, OUT)
    plt.close(fig)
    log.info("saved %s.{pdf,eps,png}", C.rel(OUT))
    inputs = C.code_files() + [C.P / "rq1/manifest.json", C.P / "screen/abstract-decisions-v08.jsonl", C.P / "records.jsonl",
                               C.ROOT / "research/protocol/search-log.md", Path(__file__).resolve()]
    C.write_config(RUN, "analysis/rq1/fig2_years.py", inputs, {"figure_width_mm": 174, "dpi_png": 600, "family_rule": "first listed paradigm family; none if no paradigm",
                                                               "partial_year": {"year": 2026, "search_date": C.SEARCH_DATE}},
                   {"packages": C.pkg_versions(["matplotlib", "numpy"])})


if __name__ == "__main__":
    main()

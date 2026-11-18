"""Figure 5: paradigm family x model family heatmap from the RQ1 abstract codes, two panels:
(a) view A = liberal frame (N=2022), (b) view B = coder-flagged yes within A (N=992).
Cell = number of records whose abstract names at least one paradigm of the family AND at least one model of the family
(records can enter several cells, so cells do not sum to N). Records with a family but no model named (and the reverse)
are counted in fig5_marginals.csv, not drawn.

    .venv/Scripts/python.exe -I analysis/rq1/fig5_heatmap.py

Outputs: paper/figures/Fig5.{pdf,eps,png}; runs/rq1-fig5-heatmap/{config.json, fig5_heatmap.log, fig5_matrix.csv,
fig5_marginals.csv, metrics.json}
"""
from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rq1_common as C  # noqa: E402

RUN = C.ROOT / "runs/rq1-fig5-heatmap"
OUT = C.ROOT / "paper/figures/Fig5"
SHORT = {"HB": "Heuristics and biases", "JDM": "Judgement and decision making", "RE": "Reasoning",
         "TOM": "Theory of mind, social cognition", "MEM": "Memory and attention", "LANG": "Language, psycholinguistics",
         "LEARN": "Learning, categorisation", "NUM": "Numerical cognition", "MOR": "Moral judgement",
         "DEV": "Developmental tasks", "OTH": "Other"}


def lum(hexc):
    r, g, b = [int(hexc[i:i + 2], 16) / 255 for i in (1, 3, 5)]

    def f(c):
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    return 0.2126 * f(r) + 0.7152 * f(g) + 0.0722 * f(b)


def contrast(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def main():
    log = C.setup_run(RUN, "fig5_heatmap")
    rows, views, manifest = C.load_frame(need_years=False)
    fams = C.FAMILIES
    mods = C.MODEL_FAMILIES
    mat = {}
    marg = {}
    for v in ("A", "B"):
        m = {(f, k): 0 for f in fams for k in mods}
        n_both = n_par_nomodel = n_mod_nopar = n_neither = 0
        for i in views[v]:
            r = rows[i]
            pf = {p["family"] for p in r["paradigms"]}
            mf = set(r["model_families"])
            assert pf <= set(fams), pf
            assert mf <= set(mods), mf
            for f in pf:
                for k in mf:
                    m[(f, k)] += 1
            n_both += bool(pf and mf)
            n_par_nomodel += bool(pf and not mf)
            n_mod_nopar += bool(mf and not pf)
            n_neither += not pf and not mf
        mat[v] = m
        marg[v] = {"N": len(views[v]), "paradigm_and_model_named": n_both, "paradigm_only": n_par_nomodel,
                   "model_only": n_mod_nopar, "neither": n_neither}
        assert n_both + n_par_nomodel + n_mod_nopar + n_neither == len(views[v])
        log.info("view %s: %s", v, marg[v])
    # orders: rows by view-A records per family (desc), columns by view-A records per model family (desc), 'other' last
    rcount = {f: sum(1 for i in views["A"] if any(p["family"] == f for p in rows[i]["paradigms"])) for f in fams}
    ccount = {k: sum(1 for i in views["A"] if k in rows[i]["model_families"]) for k in mods}
    rord = sorted(fams, key=lambda f: (-rcount[f], f))
    cord = sorted([k for k in mods if k != "other"], key=lambda k: (-ccount[k], k)) + ["other"]
    log.info("row order %s; col order %s", rord, cord)
    with open(RUN / "fig5_matrix.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["view", "paradigm_family", "model_family", "n_records"])
        for v in ("A", "B"):
            for fam in rord:
                for k in cord:
                    w.writerow([v, fam, k, mat[v][(fam, k)]])
    with open(RUN / "fig5_marginals.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["view", "N", "paradigm_and_model_named", "paradigm_only", "model_only", "neither"])
        for v in ("A", "B"):
            w.writerow([v, marg[v]["N"], marg[v]["paradigm_and_model_named"], marg[v]["paradigm_only"],
                        marg[v]["model_only"], marg[v]["neither"]])
    vmax = max(max(mat[v].values()) for v in ("A", "B"))

    C.mpl_setup()
    import matplotlib.pyplot as plt
    from matplotlib.cm import ScalarMappable
    from matplotlib.colors import ListedColormap, PowerNorm

    # seven discrete steps; colours chosen so that black or white text reaches >= 4.5:1 on every step
    cmap = ListedColormap(["#FFFFFF", "#DEEBF7", "#C6DBEF", "#9ECAE1", "#6BAED6", "#2166A8", "#08306B"])
    norm = PowerNorm(gamma=0.5, vmin=0, vmax=vmax)
    fig = plt.figure(figsize=(C.W2, 86 * C.MM))
    gs = fig.add_gridspec(2, 2, height_ratios=[1, 0.045], width_ratios=[1, 1], wspace=0.04, hspace=0.62,
                          left=0.255, right=0.995, top=0.945, bottom=0.115)
    min_contrast = 99
    for col, (v, letter) in enumerate(zip(("A", "B"), "ab")):
        ax = fig.add_subplot(gs[0, col])
        data = [[mat[v][(f, k)] for k in cord] for f in rord]
        ax.imshow(data, cmap=cmap, norm=norm, aspect="auto", interpolation="nearest")
        for r_i, f in enumerate(rord):
            for c_i, k in enumerate(cord):
                val = data[r_i][c_i]
                bg = "#%02X%02X%02X" % tuple(int(round(255 * x)) for x in cmap(norm(val))[:3])
                tc = "#FFFFFF" if contrast(bg, "#FFFFFF") >= contrast(bg, "#111111") else "#111111"
                min_contrast = min(min_contrast, max(contrast(bg, "#FFFFFF"), contrast(bg, "#111111")))
                ax.text(c_i, r_i, str(val), ha="center", va="center", fontsize=6.3, color=tc)
        ax.set_xticks(range(len(cord)))
        ax.set_xticklabels(cord, rotation=40, ha="right", rotation_mode="anchor")
        ax.set_yticks(range(len(rord)))
        if col == 0:
            ax.set_yticklabels([SHORT[f] for f in rord])
        else:
            ax.set_yticklabels([])
            ax.tick_params(axis="y", length=0)
        ax.set_xticks([x - 0.5 for x in range(1, len(cord))], minor=True)
        ax.set_yticks([y - 0.5 for y in range(1, len(rord))], minor=True)
        ax.grid(which="minor", color="#FFFFFF", lw=0.8)
        ax.tick_params(which="minor", length=0)
        ax.tick_params(axis="x", length=2.5)
        for s in ax.spines.values():
            s.set_linewidth(0.5)
        ax.set_xlabel(f"Model family named (view {v}, N = {len(views[v])})", labelpad=3)
        ax.text(-0.02, 1.015, letter, transform=ax.transAxes, fontsize=9, fontweight="bold", ha="right", va="bottom")
        if col == 0:
            ax.set_ylabel("Paradigm family named")
    cax = fig.add_subplot(gs[1, :])
    cb = fig.colorbar(ScalarMappable(norm=norm, cmap=cmap), cax=cax, orientation="horizontal")
    cb.set_ticks([t for t in (0, 5, 25, 50, 100, 200, 300) if t <= vmax])
    cb.set_label("Records naming the pair", labelpad=2)
    cb.outline.set_linewidth(0.5)
    C.save_fig(fig, OUT)
    plt.close(fig)
    log.info("min text/background contrast over cells: %.2f", min_contrast)
    log.info("saved %s.{pdf,eps,png}", C.rel(OUT))
    (RUN / "metrics.json").write_text(json.dumps({
        "search_date": C.SEARCH_DATE, "marginals": marg, "max_cell": vmax, "min_text_contrast": round(min_contrast, 2),
        "row_order": rord, "col_order": cord, "colour_scale": "PowerNorm gamma 0.5, shared by both panels"}, indent=1),
        encoding="utf-8")
    inputs = C.code_files() + [C.P / "rq1/manifest.json", C.P / "screen/abstract-decisions-v08.jsonl", Path(__file__).resolve()]
    C.write_config(RUN, "analysis/rq1/fig5_heatmap.py", inputs, {
        "figure_width_mm": 174, "dpi_png": 600, "views": {"A": "liberal frame", "B": "meets_criteria_on_abstract == yes within A"},
        "cell": "records with >=1 paradigm of the family and >=1 model of the family (multi-membership)"},
        {"packages": C.pkg_versions(["matplotlib", "numpy"])})


if __name__ == "__main__":
    main()

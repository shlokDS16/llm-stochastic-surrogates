"""Figure 1: PRISMA 2020 flow diagram. Every count is read from a data file; full-text boxes read
data/processed/prisma-fulltext.json (created with null values if absent; null is drawn as 'pending').

    .venv/Scripts/python.exe -I analysis/rq1/fig1_prisma.py

Outputs: paper/figures/Fig1.{pdf,eps,png}; runs/rq1-fig1-prisma/{config.json, fig1_prisma.log, counts.json}
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import rq1_common as C  # noqa: E402

RUN = C.ROOT / "runs/rq1-fig1-prisma"
OUT = C.ROOT / "paper/figures/Fig1"
FT = C.P / "prisma-fulltext.json"
RUN_INPUT_ELIG = C.ROOT / __import__("os").environ.get("RQ234_RUN", "runs/rq234-final") / "eligibility-estimates.csv"  # CRP-S05: final run
FT_TEMPLATE = {
    "_note": "Filled after full-text reading of the analysed set (first 150 of the 250 drawn, sample.jsonl 'analysed'). null = pending. Read by analysis/rq1/fig1_prisma.py.",
    "fulltext_assessed": None,
    "fulltext_not_retrievable": None,
    "excluded_fulltext_total": None,
    "excluded_fulltext_reasons": {},
    "included_rq2_rq4": None,
}


def n(x):
    return "pending" if x is None else f"{x:,}"


def main():
    log = C.setup_run(RUN, "fig1_prisma")
    if not FT.exists():
        FT.write_text(json.dumps(FT_TEMPLATE, indent=1), encoding="utf-8")
        log.info("created %s with null values", C.rel(FT))
    ft = json.loads(FT.read_text(encoding="utf-8"))

    pc = json.loads((C.ROOT / "research/protocol/prisma-counts.json").read_text(encoding="utf-8"))
    ag = json.loads((C.P / "screen/abstract-agreement-v08.json").read_text(encoding="utf-8"))
    samp = list(C.read_jsonl(C.P / "fulltext-sample/sample.jsonl"))
    rows, views, manifest = C.load_frame(need_years=False)

    ident = pc["identified"]
    oa = {k.split("-")[-1]: v for k, v in ident.items() if k.startswith("openalex")}
    arx = ident["arxiv-S2"]
    oa_total = sum(oa.values())
    total_id = oa_total + arx
    assert total_id - pc["duplicates_removed"] == pc["unique"] == pc["screening_title"]["screened"]
    st = pc["screening_title"]
    sa = pc["screening_abstract"]
    assert st["screened"] - st["excluded"] == st["to_stage2"] == sa["screened"]
    assert sa["screened"] - sa["excluded"] == sa["to_full_text_both_include"] + sa["to_full_text_disagreement_or_maybe"] == pc["full_text_input"]
    lib = ag["liberal"]
    assert lib["excluded_abstract"] == sa["excluded"]
    assert lib["eligible"] + lib["excluded_tiebreak"] == pc["full_text_input"] == lib["eligible"] + lib["excluded_tiebreak"]
    n_both = sa["to_full_text_both_include"]
    n_disp = sa["to_full_text_disagreement_or_maybe"]
    elig_after_tiebreak = lib["eligible"] - n_both
    assert elig_after_tiebreak + lib["excluded_tiebreak"] == n_disp
    assert lib["eligible"] == len(views["A"]) == manifest["frame_liberal"]
    strict_elig = ag["strict"]["eligible"]
    flag = Counter(r["meets_criteria_on_abstract"] for r in rows.values())
    drawn = len(samp)
    analysed = sum(1 for s in samp if s.get("analysed"))
    assert drawn == 250 and analysed == 150, (drawn, analysed)

    counts = {"openalex_by_block": oa, "openalex_total": oa_total, "arxiv": arx, "identified_total": total_id,
              "duplicates_removed": pc["duplicates_removed"], "unique": pc["unique"], "title_excluded": st["excluded"],
              "stage2": sa["screened"], "abstract_both_exclude": sa["excluded"], "both_include": n_both, "disagree_or_maybe": n_disp,
              "tiebreak_eligible": elig_after_tiebreak, "tiebreak_excluded": lib["excluded_tiebreak"], "liberal_eligible": lib["eligible"],
              "strict_eligible": strict_elig, "rq1_coded_frame": len(rows), "flag": dict(flag), "sample_drawn": drawn, "sample_analysed": analysed,
              "fulltext": ft}
    (RUN / "counts.json").write_text(json.dumps(counts, indent=1), encoding="utf-8")
    log.info("counts %s", json.dumps(counts))

    C.mpl_setup()
    import matplotlib.pyplot as plt
    from matplotlib.patches import FancyBboxPatch, Rectangle

    Wm, Hm = 174.0, 260.0
    fig = plt.figure(figsize=(C.W2, Hm * C.MM))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, Wm)
    ax.set_ylim(0, Hm)
    ax.axis("off")

    XM, WM = 14.0, 92.0          # main column
    XS, WS = 114.0, 58.0         # side column
    LH = 3.05                     # line height (mm) at 7 pt
    PAD = 1.6
    fills = {"main": "#FFFFFF", "side": "#F2F2F2", "pend": "#FFFFFF", "key": "#DCEBF7"}

    def box(x, ytop, w, lines, kind="main", bold_first=True, small=None):
        """lines: list of (text, style) or text. Returns (ymid, ybottom)."""
        small = small or set()
        h = 2 * PAD + LH * len(lines)
        ls = "--" if kind == "pend" else "-"
        ax.add_patch(Rectangle((x, ytop - h), w, h, fc=fills[kind], ec="#111111", lw=0.8 if kind != "key" else 1.3, ls=ls, zorder=2))
        for k, t in enumerate(lines):
            yy = ytop - PAD - LH * (k + 0.5)
            fw = "bold" if (bold_first and k == 0) else "normal"
            fs = 7
            if isinstance(t, tuple):  # two aligned columns: (left label, left value, right label, right value)
                ax.text(x + w * 0.24, yy, t[0], ha="left", va="center", fontsize=fs, zorder=3)
                ax.text(x + w * 0.46, yy, t[1], ha="right", va="center", fontsize=fs, zorder=3)
                ax.text(x + w * 0.58, yy, t[2], ha="left", va="center", fontsize=fs, zorder=3)
                ax.text(x + w * 0.80, yy, t[3], ha="right", va="center", fontsize=fs, zorder=3)
                continue
            ax.text(x + w / 2, yy, t, ha="center", va="center", fontsize=fs, fontweight=fw, zorder=3)
        return ytop - h / 2, ytop - h

    def side(ymid, lines, kind="side", small=None):
        h = 2 * PAD + LH * len(lines)
        return box(XS, ymid + h / 2, WS, lines, kind, small=small)

    def arrow(x0, y0, x1, y1):
        ax.annotate("", xy=(x1, y1), xytext=(x0, y0), arrowprops=dict(arrowstyle="-|>", color="#111111", lw=0.8, shrinkA=0, shrinkB=0, mutation_scale=7), zorder=1)

    y = Hm - 2.0
    GAP = 6.0
    pos = {}

    # --- Identification ---
    oa_keys = [f"B{i}" for i in range(1, 11)]
    oa_lines = ["OpenAlex, sub-queries B1 to B10 (n = %s)" % n(oa_total)]
    for a in range(0, 10, 2):
        oa_lines.append((oa_keys[a] + ":", f"{oa[oa_keys[a]]:,}", oa_keys[a + 1] + ":", f"{oa[oa_keys[a + 1]]:,}"))
    ym_oa, yb_oa = box(XM, y, 58.0, oa_lines, small={1, 2, 3, 4, 5})
    ym_ar, yb_ar = box(XM + 58.0 + 4.0, y, WM - 58.0 - 4.0, ["arXiv", "(n = %s)" % n(arx), "submitted 2026-06-01", "to 2026-10-16"], small={2, 3})
    yb_src = min(yb_oa, yb_ar)
    y2 = yb_src - GAP
    ym_id, yb_id = box(XM, y2, WM, ["Records identified (n = %s)" % n(total_id)])
    arrow(XM + 29.0, yb_oa, XM + 29.0, y2)
    xa = XM + 62.0 + (WM - 62.0) / 2
    arrow(xa, yb_ar, xa, y2)
    side(ym_id, ["Duplicate records removed", "(n = %s)" % n(pc["duplicates_removed"])])
    arrow(XM + WM, ym_id, XS, ym_id)
    pos["id_top"], pos["id_bot"] = y2, yb_id

    # --- Screening ---
    y3 = yb_id - GAP
    ym_t, yb_t = box(XM, y3, WM, ["Records screened by title", "(n = %s)" % n(pc["unique"])])
    arrow(XM + WM / 2, yb_id, XM + WM / 2, y3)
    side(ym_t, ["Excluded at title stage", "(both classifiers exclude; n = %s)" % n(st["excluded"])])
    arrow(XM + WM, ym_t, XS, ym_t)

    y4 = yb_t - GAP
    ym_a, yb_a = box(XM, y4, WM, ["Records screened by title and abstract", "(n = %s)" % n(sa["screened"])])
    arrow(XM + WM / 2, yb_t, XM + WM / 2, y4)
    side(ym_a, ["Excluded at abstract stage", "(both raters exclude; n = %s)" % n(sa["excluded"])])
    arrow(XM + WM, ym_a, XS, ym_a)

    y5 = yb_a - GAP
    ym_d, yb_d = box(XM, y5, WM, ["Included by both raters or disputed",
                                  "(n = %s)" % n(n_both + n_disp),
                                  f"both include: {n_both:,};  disagreement or maybe: {n_disp:,}"], small={2})
    arrow(XM + WM / 2, yb_a, XM + WM / 2, y5)
    side(ym_d, ["Excluded by third-rater tie-break",
                     "(liberal rule; n = %s)" % n(lib["excluded_tiebreak"]),
                     f"{n_disp:,} disputed records: {elig_after_tiebreak:,} eligible,",
                     f"{lib['excluded_tiebreak']:,} excluded"], small={2, 3})
    arrow(XM + WM, ym_d, XS, ym_d)

    y6 = yb_d - GAP
    ym_e, yb_e = box(XM, y6, WM, ["Eligible at abstract level: liberal frame", "(n = %s)" % n(lib["eligible"]),
                                  f"strict-rule sensitivity frame: n = {strict_elig:,}"], "key", small={2})
    arrow(XM + WM / 2, yb_d, XM + WM / 2, y6)

    y7 = yb_e - GAP
    ym_c, yb_c = box(XM, y7, WM, ["Coded for RQ1 from title and abstract", "(n = %s)" % n(len(rows)),
                                  f"coder flag: yes {flag['yes']:,};  unclear {flag['unclear']:,};  no {flag['no']:,}"], small={2})
    arrow(XM + WM / 2, yb_e, XM + WM / 2, y7)

    # --- Full-text stage (PRISMA 2020 order) ---
    def hh(lines):
        return 2 * PAD + LH * len(lines)

    def pair(ytop, main_lines, side_lines, main_kind="main", side_kind="side", prev_bottom=None):
        """Main box and side box share the same top edge; the arrow leaves at the middle of the shorter one.
        Returns the lowest edge of the pair and the bottom of the main box."""
        box(XM, ytop, WM, main_lines, main_kind, small={i for i in range(1, len(main_lines))})
        box(XS, ytop, WS, side_lines, side_kind, small={i for i in range(1, len(side_lines))})
        ya = ytop - min(hh(main_lines), hh(side_lines)) / 2
        arrow(XM + WM, ya, XS, ya)
        return ytop - max(hh(main_lines), hh(side_lines)), ytop - hh(main_lines)

    n_not_read = drawn - analysed
    assert ft["fulltext_sought"] == analysed, (ft["fulltext_sought"], analysed)
    assert ft["fulltext_sought"] - ft["fulltext_not_retrievable"] == ft["fulltext_assessed"]
    assert ft["fulltext_assessed"] - ft["excluded_fulltext_total"] == ft["included_rq2_rq4"]
    reasons = ft["excluded_fulltext_reasons"]
    assert sum(reasons.values()) == ft["excluded_fulltext_total"]
    assert ft["fulltext_pending_assessment"] == 0 and ft["fulltext_unresolved_unclear"] == 0
    with open(RUN_INPUT_ELIG, newline="", encoding="utf-8") as fh:
        elig = {r["coder"]: int(r["n_eligible_respondents"]) for r in csv.DictReader(fh)}
    assert elig["claude"] == ft["included_rq2_rq4"], elig
    n_second = elig["codex"]
    counts["fulltext_second_coding_included"] = n_second
    (RUN / "counts.json").write_text(json.dumps(counts, indent=1), encoding="utf-8")

    y8 = yb_c - GAP
    arrow(XM + WM / 2, yb_c, XM + WM / 2, y8)
    low, yb_s = pair(y8, ["Random sample drawn, stratified (n = %s)" % n(drawn),
                          f"analysed set fixed in advance: first {analysed:,} of a random order"],
                     ["Not read under amendment v0.9.1", "(n = %s)" % n(n_not_read)])

    y9 = yb_s - GAP
    arrow(XM + WM / 2, yb_s, XM + WM / 2, y9)
    low, yb_k = pair(y9, ["Reports sought for retrieval", "(n = %s)" % n(ft["fulltext_sought"])],
                     ["Reports not retrieved", "(n = %s)" % n(ft["fulltext_not_retrievable"])])

    y10 = yb_k - GAP
    arrow(XM + WM / 2, yb_k, XM + WM / 2, y10)
    order = sorted((k for k in reasons if k != "other" and not k.startswith("abstract-only")), key=lambda k: (-reasons[k], k))
    order += [k for k in reasons if k.startswith("abstract-only")] + (["other"] if "other" in reasons else [])
    ex_lines = ["Reports excluded, with reasons", "(n = %s)" % n(ft["excluded_fulltext_total"])]
    for k in order:
        if k.startswith("abstract-only"):
            ex_lines.append(f"abstract-only: {n(reasons[k])}")
            ex_lines.append("(pending human confirmation)")
        else:
            ex_lines.append(f"{k}: {n(reasons[k])}")
    low, yb_f = pair(y10, ["Reports assessed for eligibility", "(n = %s)" % n(ft["fulltext_assessed"])], ex_lines)

    y11 = yb_f - GAP
    arrow(XM + WM / 2, yb_f, XM + WM / 2, y11)
    ym_i, yb_i = box(XM, y11, WM, ["Studies included in RQ2 to RQ4", "(n = %s in the primary coding)" % n(ft["included_rq2_rq4"]),
                                   f"{n_second:,} in the second coding"], "key", small={1, 2})

    # --- phase bands ---
    def band(ytop, ybot, label):
        ax.add_patch(Rectangle((0.5, ybot), 9.0, ytop - ybot, fc="#DCEBF7", ec="#111111", lw=0.6, zorder=1))
        ax.text(5.0, (ytop + ybot) / 2, label, rotation=90, ha="center", va="center", fontsize=7.5, fontweight="bold", zorder=3)

    band(Hm - 1.2, yb_id - 0.4, "Identification")
    band(y3 + 1.0, yb_c - 0.4, "Screening")
    ybot = min(yb_i, low)
    band(y8 + 1.0, ybot - 0.4, "Included")
    fig_h_used = Hm - (ybot - 1.0)
    log.info("content height used %.1f mm of %.1f", fig_h_used, Hm)

    ax.set_ylim(ybot - 1.5, Hm)
    fig.set_size_inches(C.W2, (Hm - (ybot - 1.5)) * C.MM)
    C.save_fig(fig, OUT)
    plt.close(fig)
    log.info("saved %s.{pdf,eps,png}", C.rel(OUT))

    inputs = [C.ROOT / "research/protocol/prisma-counts.json", C.P / "screen/abstract-agreement-v08.json", C.P / "screen/abstract-decisions-v08.jsonl",
              C.P / "fulltext-sample/sample.jsonl", FT, RUN_INPUT_ELIG, C.P / "rq1/manifest.json"] + C.code_files() + [Path(__file__).resolve()]
    C.write_config(RUN, "analysis/rq1/fig1_prisma.py", inputs, {"figure_width_mm": 174, "dpi_png": 600},
                   {"packages": C.pkg_versions(["matplotlib", "numpy"])})


if __name__ == "__main__":
    main()

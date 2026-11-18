"""Figures 6 to 10 of the review (protocol section 11), RQ2 to RQ4 results.

    .venv/Scripts/python.exe -I analysis/fulltext/fig6_10.py [INPUT_DIR] [--out-dir paper/figures] [--log-dir runs/fig6-10]

INPUT_DIR defaults to runs/rq234-interim. The script reads only files that rq234_analysis.py wrote there
(fig_inputs/*.csv, rq3.csv, rq4_trend.csv, trend_descriptive_only.csv, rq2-rows-by-family.csv, config.json); it is written
to be rerun unchanged on the final run (e.g. `... runs/rq234-final`). No result number is typed in this file.

Fig 6  human-comparison sources and metrics (design-weighted shares, Claude and Codex side by side)
Fig 7  findings by outcome kind (never pooled) and paradigm family (weighted label shares; unweighted row counts)
Fig 8  robustness-reporting audit (perturbations tested; outcome among tested)
Fig 9  reporting trend over time (observed yearly shares per coder; odds ratio per year only where the 10/10 rule is met)
Fig 10 reporting-item profile by paradigm family (unweighted counts, Claude only, no subgroup claims)

Rules applied (amendments v0.11, v0.12, v0.12.1): outcome kinds are separate panels; Claude (primary) and Codex are a
coder-sensitivity display, not an interval; items failing the full-sample agreement rule are hatched; per-coder trends are
sensitivity analyses and no trend estimate is drawn for items listed in trend_descriptive_only.csv.
Outputs: Fig6..Fig10 .pdf/.eps (fonts embedded, TrueType) and 600-dpi RGB .png; log and metrics in LOG_DIR.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib as mpl  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import matplotlib.ticker as mticker  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, to_hex, to_rgb  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch, Rectangle  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
MM = 1 / 25.4
W = 174  # mm, full page width (Springer double column)

# Okabe-Ito based pair; passes dataviz validate_palette (CVD dE 22.5, normal 28.2) and >= 4.5:1 on white (asserted in main)
C_CLAUDE = "#0072B2"
C_CODEX = "#B34700"
INK = "#111111"
HATCH_EDGE = "#B3B3B3"
GRID = "#D9D9D9"
RAMP = ["#F3F7FB", "#C6DBEF", "#6BAED6", "#2171B5", "#08306B"]
NEUTRAL_CELL = "#E6E6E6"
MIN_FONT = 7.0

FAMILY_NAMES = {
    "HB": "Heuristics and biases", "JDM": "Judgement, decisions", "RE": "Reasoning", "TOM": "Theory of mind",
    "MEM": "Memory, attention", "LANG": "Language", "LEARN": "Learning, categories", "NUM": "Numerical cognition",
    "MOR": "Moral judgement", "DEV": "Developmental tasks", "OTH": "Other", "?": "Family not assigned",
    "none_listed": "No family listed",
    # composite written by derive_labels.py for a study whose effect rows carry pids of two families
    # (order 122, Claude: pid 'P1+P2+P3', JDM and LEARN); the rows are kept as one stratum, so the label says both
    "JDM+LEARN": "Judgement, learning (both)",
}
LABEL_NAMES = {
    "HUMAN-LIKE": "Human-like", "EXAGGERATED": "Exaggerated", "ATTENUATED": "Attenuated",
    "SUPER-NORMATIVE": "Super-normative", "DIFFERENT": "Different", "NO-EFFECT": "No effect",
    "SAME-DIRECTION-UNQUANTIFIED": "Same direction, unquantified", "NO-HUMAN-REFERENCE": "No human reference",
    "INSUFFICIENT": "Insufficient", "UNCLASSIFIED-MODEL-ONLY": "Unclassified, model only",
    "ABOVE-HUMAN": "Above human", "HUMAN-LEVEL": "Human level", "BELOW-HUMAN": "Below human",
    "AGREEMENT-ONLY": "Agreement only", "ANY": "Any row",
}
LABEL_ORDER = {
    "effect": ["HUMAN-LIKE", "EXAGGERATED", "ATTENUATED", "SUPER-NORMATIVE", "DIFFERENT", "NO-EFFECT",
               "SAME-DIRECTION-UNQUANTIFIED", "NO-HUMAN-REFERENCE", "INSUFFICIENT", "UNCLASSIFIED-MODEL-ONLY"],
    "accuracy": ["ABOVE-HUMAN", "HUMAN-LEVEL", "BELOW-HUMAN", "NO-HUMAN-REFERENCE", "INSUFFICIENT"],
    "agreement": ["AGREEMENT-ONLY"],
}
KIND_NAMES = {"effect": "Effect", "accuracy": "Accuracy", "agreement": "Agreement"}
SOURCE_NAMES = {
    "published_norms": "Published norms", "own_sample": "Own human sample", "crowd_norms": "Crowd-sourced norms",
    "replication_dataset": "Replication dataset", "none": "No human comparison",
}
METRIC_NAMES = {
    "accuracy": "Accuracy against a key", "effect_size": "Effect size", "bias_magnitude": "Bias magnitude",
    "choice_distribution": "Choice distribution", "human_correlation": "Correlation with humans", "other": "Other metric",
}
PERT_NAMES = {
    "wording": "Prompt wording", "option_order": "Option order", "response_format": "Response format",
    "decoding": "Decoding settings", "seeds": "Random seeds", "model_version": "Model version",
    "contamination": "Contamination check", "persona": "Persona", "language": "Prompt language",
    "other": "Other perturbation", "none_listed": "No perturbation listed",
}
JUDGED = ["wording", "option_order", "response_format", "decoding", "seeds", "model_version"]
OUTCOME_NAMES = {"survived": "Survived", "weakened": "Weakened", "mixed": "Mixed", "reversed": "Reversed",
                 "not_reported": "Not reported"}
ITEM_NAMES = {  # reporting items f1-f12 (extraction brief v1.1, section 7)
    "f1": "f1 Exact version and query date", "f2": "f2 Decoding temperature stated",
    "f3": "f3 Repeated draws, number stated", "f4": "f4 Full prompts available",
    "f5": "f5 Paraphrases compared", "f6_applicable": "f6 Option order varied",
    "f7": "f7 Several temperatures compared", "f8": "f8 Model snapshots compared",
    "f9": "f9 Contamination addressed", "f10": "f10 Test or interval for effect", "f11": "f11 Preregistration cited",
    "f12": "f12 Code or data link", "robustness_tested": "Any judged robustness check",
}
FAIL_RULE = " (kappa < 0.6, or agreement < 80 % when a category has < 5 records)"
FAIL_TEXT = "hatched: field fails the full-sample agreement rule"

LOG: list[str] = []


def log(msg: str) -> None:
    LOG.append(msg)
    print(msg)


# ------------------------------------------------------------------ colour helpers
def _lin(c):
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def lum(hexc: str) -> float:
    r, g, b = to_rgb(hexc)
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def contrast(a: str, b: str) -> float:
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


MIN_CONTRAST_SEEN = [99.0]


def text_on(bg: str) -> str:
    """Black or white, whichever has the higher contrast on bg; the minimum over all cells is logged."""
    cb, cw = contrast("#000000", bg), contrast("#FFFFFF", bg)
    MIN_CONTRAST_SEEN[0] = min(MIN_CONTRAST_SEEN[0], max(cb, cw))
    return "#000000" if cb >= cw else "#FFFFFF"


def blend(a: str, b: str, t: float) -> str:
    """Opaque mix of colour a (weight t) over b (EPS has no transparency)."""
    ra, rb = np.array(to_rgb(a)), np.array(to_rgb(b))
    return to_hex(t * ra + (1 - t) * rb)


CMAP = LinearSegmentedColormap.from_list("seq_blue", RAMP)


# ------------------------------------------------------------------ io
def read_csv(path: Path) -> list[dict]:
    with open(path, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def fnum(x, default=float("nan")) -> float:
    try:
        return float(x)
    except (TypeError, ValueError):
        return default


def truthy(x) -> bool:
    return str(x).strip().lower() in ("true", "1", "yes")


class Inputs:
    def __init__(self, d: Path):
        fi = d / "fig_inputs"
        self.paths = {
            "rq2_labels": fi / "rq2_labels.csv", "rq3_comparisons": fi / "rq3_comparisons.csv",
            "rq4_items_by_coder": fi / "rq4_items_by_coder.csv", "rq4_items_by_family": fi / "rq4_items_by_family.csv",
            "rq4_trend_counts": fi / "rq4_trend.csv", "rq3": d / "rq3.csv", "rq4_trend_fit": d / "rq4_trend.csv",
            "trend_descriptive_only": d / "trend_descriptive_only.csv", "rows_by_family": d / "rq2-rows-by-family.csv",
            "config": d / "config.json",
        }
        missing = [str(p) for p in self.paths.values() if not p.exists()]
        if missing:
            raise SystemExit("missing input files: " + ", ".join(missing))
        self.rq2 = read_csv(self.paths["rq2_labels"])
        self.rq3c = read_csv(self.paths["rq3_comparisons"])
        self.items = read_csv(self.paths["rq4_items_by_coder"])
        self.fam = read_csv(self.paths["rq4_items_by_family"])
        self.trend_counts = read_csv(self.paths["rq4_trend_counts"])
        self.rq3 = read_csv(self.paths["rq3"])
        self.trend_fit = read_csv(self.paths["rq4_trend_fit"])
        self.desc_only = read_csv(self.paths["trend_descriptive_only"])
        self.rows_fam = read_csv(self.paths["rows_by_family"])
        self.config = json.loads(self.paths["config"].read_text(encoding="utf-8"))
        self.run = self.config.get("run", d.name)
        self.interim = bool(self.config.get("interim", False))


# ------------------------------------------------------------------ figure plumbing
def setup_fonts() -> str:
    from matplotlib import font_manager as fm

    names = {f.name for f in fm.fontManager.ttflist}
    fam = "Arial" if "Arial" in names else "DejaVu Sans"
    mpl.rcParams.update({
        "font.family": fam, "font.size": MIN_FONT, "axes.labelsize": MIN_FONT, "xtick.labelsize": MIN_FONT,
        "ytick.labelsize": MIN_FONT, "legend.fontsize": MIN_FONT, "axes.linewidth": 0.6,
        "xtick.major.width": 0.6, "ytick.major.width": 0.6, "xtick.major.size": 2.5, "ytick.major.size": 2.5,
        "pdf.fonttype": 42, "ps.fonttype": 42, "text.color": INK, "axes.labelcolor": INK, "xtick.color": INK,
        "ytick.color": INK, "savefig.facecolor": "white", "figure.facecolor": "white", "hatch.linewidth": 0.5,
        "axes.spines.top": False, "axes.spines.right": False,
    })
    return fam


class Canvas:
    """Figure with millimetre placement (y measured from the top)."""

    def __init__(self, h_mm: float):
        self.h = h_mm
        self.fig = plt.figure(figsize=(W * MM, h_mm * MM))

    def axes(self, x, y_top, w, h, **kw):
        return self.fig.add_axes([x / W, 1 - (y_top + h) / self.h, w / W, h / self.h], **kw)

    def text(self, x, y_top, s, **kw):
        return self.fig.text(x / W, 1 - y_top / self.h, s, **kw)

    def legend(self, handles, x, y_top, **kw):
        return self.fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(x / W, 1 - y_top / self.h),
                               frameon=False, borderpad=0, borderaxespad=0, **kw)


def save(cv: Canvas, stem: Path) -> None:
    from PIL import Image

    for ext in ("pdf", "eps"):
        cv.fig.savefig(stem.with_suffix("." + ext), format=ext)
    png = stem.with_suffix(".png")
    cv.fig.savefig(png, format="png", dpi=600)
    plt.close(cv.fig)
    Image.open(png).convert("RGB").save(png, dpi=(600, 600))


def panel_letter(cv: Canvas, x, y_top, s):
    cv.text(x, y_top, s, fontsize=9, fontweight="bold", ha="left", va="top")


def hatch_rect(ax, xy, w, h, color=HATCH_EDGE, z=0.5):
    ax.add_patch(Rectangle(xy, w, h, fill=False, hatch="////", edgecolor=color, linewidth=0, zorder=z))


def coder_handles():
    return [Line2D([0], [0], marker="o", color=C_CLAUDE, mfc=C_CLAUDE, ms=4.5, lw=1.1, label="Primary coder"),
            Line2D([0], [0], marker="s", color=C_CODEX, mfc=C_CODEX, ms=4.2, lw=1.1, label="Second coder")]


def hatch_handle(text):
    return Patch(facecolor="white", edgecolor=HATCH_EDGE, hatch="////", linewidth=0.0, label=text)


# ------------------------------------------------------------------ forest panels (Figs 6 and 8)
def forest_height(rows, row_h=6.4, gap_h=3.0):
    return (len(rows) + sum(gap_h / row_h for i, r in enumerate(rows) if i and r.get("gap_before"))) * row_h


def forest_panel(cv: Canvas, x, y_top, w, rows, xlabel, row_h=6.4, gap_h=3.0, xmax=100.0):
    """rows: dicts with label, c=(est,lo,hi,k,n), x=(est,lo,hi,k,n), fail(bool), gap_before(bool), bold(bool)."""
    ypos, y = [], 0.0
    for i, r in enumerate(rows):
        if i and r.get("gap_before"):
            y += gap_h / row_h
        ypos.append(y)
        y += 1.0
    height = y * row_h
    ax = cv.axes(x, y_top, w, height)
    ax.set_ylim(y - 0.5, -0.5)
    ax.set_xlim(0, xmax)
    ax.set_yticks(ypos)
    ax.set_yticklabels([r["label"] for r in rows])
    for tl, r in zip(ax.get_yticklabels(), rows):
        if r.get("bold"):
            tl.set_fontweight("bold")
    ax.tick_params(axis="y", length=0, pad=2)
    ax.set_xlabel(xlabel)
    ax.xaxis.grid(True, color=GRID, lw=0.5, zorder=0)
    ax.set_axisbelow(True)
    ax.spines["left"].set_visible(False)
    off = 0.2
    for yp, r in zip(ypos, rows):
        if r.get("fail"):
            hatch_rect(ax, (0, yp - 0.5), xmax, 1.0)
        for key, col, mk, ms, dy in (("c", C_CLAUDE, "o", 3.6, -off), ("x", C_CODEX, "s", 3.3, off)):
            est, lo, hi, k, n = r[key]
            if math.isnan(est):
                continue
            ax.plot([lo, hi], [yp + dy, yp + dy], color=col, lw=1.1, solid_capstyle="butt", zorder=3)
            ax.plot([est], [yp + dy], marker=mk, ms=ms, color=col, mec="white", mew=0.5, zorder=4, ls="none")
            ax.text(1.012, yp + dy, f"{int(k)}/{int(n)}", transform=ax.get_yaxis_transform(), ha="left", va="center",
                    fontsize=MIN_FONT, color=INK)
    ax.text(1.012, -0.55, "k/n", transform=ax.get_yaxis_transform(), ha="left", va="bottom", fontsize=MIN_FONT)
    return ax, height


def est_tuple(est, lo, hi, k, n):
    return (fnum(est), fnum(lo), fnum(hi), fnum(k), fnum(n))


# ------------------------------------------------------------------ Fig 6
def fig6(inp: Inputs, out: Path):
    rq3c = {(r["comparison_basis"], r["comparison_type"], r["coder"]): r for r in inp.rq3c}
    rq3 = {r["feature"]: r for r in inp.rq3}

    def tup_c(typ, coder):
        r = rq3c[("types_any", typ, coder)]
        return est_tuple(r["weighted_pct"], r["ci_lo_pct"], r["ci_hi_pct"], r["k"], r["denominator"])

    def ok_c(typ):
        return truthy(rq3c[("types_any", typ, "claude")]["passes_agreement"])

    def tup_r(feature, coder):
        r = rq3[feature]
        lo, hi = fnum(r[f"{coder}_lo_pct"]), fnum(r[f"{coder}_hi_pct"])
        cp = r.get(f"{coder}_cp_unweighted_pct", "")
        if lo == hi and cp and "-" in cp:  # zero-variance estimate: exact unweighted interval
            lo, hi = (float(v) for v in cp.split("-"))
        return est_tuple(r[f"{coder}_est_pct"], lo, hi, r[f"{coder}_k"], r[f"{coder}_n_domain"])

    rows_a = []
    for typ in ("published_norms", "own_sample", "crowd_norms", "replication_dataset", "none"):
        if ("types_any", typ, "claude") in rq3c:
            rows_a.append(dict(label=SOURCE_NAMES.get(typ, typ), c=tup_c(typ, "claude"), x=tup_c(typ, "codex"),
                               fail=not ok_c(typ)))
    hn = "rq3|human_n|reported"
    if hn in rq3:
        rows_a.append(dict(label="Human sample size reported", c=tup_r(hn, "claude"), x=tup_r(hn, "codex"),
                           fail=not truthy(rq3[hn]["passes_v012_rule"]), gap_before=True))
    rows_b = []
    for typ in ("accuracy", "effect_size", "bias_magnitude", "choice_distribution", "human_correlation", "other"):
        f = f"rq3|outcome_types|{typ}"
        if f in rq3:
            rows_b.append(dict(label=METRIC_NAMES.get(typ, typ), c=tup_r(f, "claude"), x=tup_r(f, "codex"),
                               fail=not truthy(rq3[f]["passes_v012_rule"])))
    ha, hb = forest_height(rows_a), forest_height(rows_b)
    y2 = 3 + ha + 12
    y3 = y2 + 2 + hb + 12
    h = y3 + 24
    cv = Canvas(h)
    xl, wl = 52, 100
    panel_letter(cv, 1, 1.0, "a")
    forest_panel(cv, xl, 3, wl, rows_a, "Eligible studies listing the comparison source (%)")
    panel_letter(cv, 1, y2 - 2, "b")
    forest_panel(cv, xl, y2 + 2, wl, rows_b, "Eligible studies reporting the metric (%)")
    cv.legend(coder_handles() + [hatch_handle(FAIL_TEXT + FAIL_RULE)], 1, y3, ncol=1, handlelength=2.4, labelspacing=0.5)
    cv.text(1, y3 + 15.5, "Bars: 95% design-based interval per coder (exact unweighted interval where the weighted estimate is 0). The gap between\n"
                        "the coders is a coder-sensitivity display, not an interval.", fontsize=MIN_FONT, ha="left", va="top")
    save(cv, out / "Fig6")
    return dict(rows_a=len(rows_a), rows_b=len(rows_b), height_mm=round(h, 1))


# ------------------------------------------------------------------ Fig 8
def fig8(inp: Inputs, out: Path):
    items = {(r["item"], r["coder"]): r for r in inp.items}

    def tup(item, coder):
        r = items[(item, coder)]
        return est_tuple(r["weighted_pct"], r["ci_lo_pct"], r["ci_hi_pct"], r["k"], r["denominator"])

    def fails(item):
        return not (truthy(items[(item, "claude")]["passes_agreement"]) and truthy(items[(item, "codex")]["passes_agreement"]))

    rows_a = []
    if ("robustness_tested|yes", "claude") in items:
        rows_a.append(dict(label="Any of the six judged types", c=tup("robustness_tested|yes", "claude"),
                           x=tup("robustness_tested|yes", "codex"), fail=fails("robustness_tested|yes"), bold=True))
    order = JUDGED + [p for p in PERT_NAMES if p not in JUDGED]
    for i, p in enumerate(order):
        it = f"perturbation|{p}"
        if (it, "claude") in items:
            rows_a.append(dict(label=PERT_NAMES[p], c=tup(it, "claude"), x=tup(it, "codex"), fail=fails(it),
                               gap_before=(i == 0 or i == len(JUDGED))))
    rows_b = []
    for o in ("survived", "weakened", "mixed", "reversed", "not_reported"):
        it = f"robustness_outcome_among_tested|{o}"
        if (it, "claude") in items:
            rows_b.append(dict(label=OUTCOME_NAMES[o], c=tup(it, "claude"), x=tup(it, "codex"), fail=fails(it)))
    ha, hb = forest_height(rows_a), forest_height(rows_b)
    y2 = 3 + ha + 12
    y3 = y2 + 2 + hb + 12
    h = y3 + 24
    cv = Canvas(h)
    xl, wl = 52, 100
    panel_letter(cv, 1, 1.0, "a")
    forest_panel(cv, xl, 3, wl, rows_a, "Eligible studies that ran and reported the perturbation (%)")
    panel_letter(cv, 1, y2 - 2, "b")
    forest_panel(cv, xl, y2 + 2, wl, rows_b, "Robustness outcome among studies that tested (%)")
    cv.legend(coder_handles() + [hatch_handle(FAIL_TEXT + FAIL_RULE)], 1, y3, ncol=1, handlelength=2.4, labelspacing=0.5)
    nb_c = int(rows_b[0]["c"][4]) if rows_b else 0
    nb_x = int(rows_b[0]["x"][4]) if rows_b else 0
    cv.text(1, y3 + 15.5, f"Panel a: the first block is judged for the outcome in panel b (any of six types), the second block is not. Panel b: denominator is\n"
                        f"the studies that tested (primary coder {nb_c}, second coder {nb_x}). The gap between the coders is a coder-sensitivity display, not an interval.",
            fontsize=MIN_FONT, ha="left", va="top")
    save(cv, out / "Fig8")
    return dict(rows_a=len(rows_a), rows_b=len(rows_b), height_mm=round(h, 1))


# ------------------------------------------------------------------ cell grid helper
def draw_cell_grid(ax, values, texts, hatch_cols, vmax, neutral=None, hatch_rows=()):
    nr, nc = values.shape
    for i in range(nr):
        for j in range(nc):
            v = values[i, j]
            if neutral is not None and neutral[i, j]:
                bg = NEUTRAL_CELL
            elif math.isnan(v):
                bg = "#FFFFFF"
            else:
                bg = to_hex(CMAP(min(max(v / vmax, 0), 1)))
            ax.add_patch(Rectangle((j - 0.5, i - 0.5), 1, 1, facecolor=bg, edgecolor="white", linewidth=0.8, zorder=1))
            tc = text_on(bg)
            if texts[i][j]:
                ax.text(j, i, texts[i][j], ha="center", va="center", fontsize=MIN_FONT, color=tc, zorder=3)
            if j in hatch_cols:
                ax.add_patch(Rectangle((j - 0.5, i - 0.5), 1, 1, fill=False, hatch="////", edgecolor=blend(tc, bg, 0.4), linewidth=0,
                                       zorder=2))
    ax.set_xlim(-0.5, nc - 0.5)
    ax.set_ylim(nr - 0.5, -0.5)
    for s in ax.spines.values():
        s.set_visible(False)
    ax.tick_params(length=0)


# ------------------------------------------------------------------ Fig 7
def fig7(inp: Inputs, out: Path):
    rq2 = defaultdict(dict)
    for r in inp.rq2:
        rq2[(r["outcome_kind"], r["derived_label"])][r["coder"]] = r
    kinds = [k for k in ("effect", "accuracy", "agreement") if any(kk == k for kk, _ in rq2)]
    kind_cols = {}
    for k in kinds:
        present = [l for (kk, l) in rq2 if kk == k and l != "ANY"]
        known = LABEL_ORDER.get(k, [])
        kind_cols[k] = ["ANY"] + [l for l in known if l in present] + sorted(l for l in present if l not in known)
    tot = defaultdict(float)
    counts = defaultdict(float)
    tot_kind = defaultdict(float)
    for r in inp.rows_fam:
        n = fnum(r["rows"], 0)
        tot[r["paradigm_family"]] += n
        counts[(r["coder"], r["outcome_kind"], r["paradigm_family"], r["derived_label"])] += n
        tot_kind[(r["coder"], r["outcome_kind"], r["paradigm_family"])] += n
    families = sorted(tot, key=lambda f: (-tot[f], f))
    fam_labels = [FAMILY_NAMES.get(f, f) for f in families]
    undrawn = sorted({(r["outcome_kind"], r["derived_label"]) for r in inp.rows_fam
                      if r["outcome_kind"] in kind_cols and r["derived_label"] not in kind_cols[r["outcome_kind"]]})
    if undrawn:
        log(f"Fig7: row-count labels without a column (in totals only): {undrawn}")
    vmax = max([v for (c, k, f, l), v in counts.items() if k in kind_cols] + [1])
    nfam = len(families)
    pitch = 4.4
    left, right, gapx = 33, 2, 3
    ncols = [len(kind_cols[k]) for k in kinds]
    colw = (W - left - right - gapx * (len(kinds) - 1)) / sum(ncols)
    top_labels, dot_h, heat_h, gap1, gap2 = 36, 34, nfam * pitch, 5, 3
    h = top_labels + dot_h + gap1 + heat_h + gap2 + heat_h + 6 + 21
    cv = Canvas(h)
    xs, x = [], left
    for nc in ncols:
        xs.append(x)
        x += nc * colw + gapx
    y_dot = top_labels
    y_c = y_dot + dot_h + gap1
    y_x = y_c + heat_h + gap2
    off = 0.2
    for ki, k in enumerate(kinds):
        cols = kind_cols[k]
        wk = len(cols) * colw
        fail_cols = set()
        ax = cv.axes(xs[ki], y_dot, wk, dot_h)
        ax.set_xlim(-0.5, len(cols) - 0.5)
        ax.set_ylim(0, 100)
        ax.set_yticks([0, 25, 50, 75, 100])
        if ki:
            ax.set_yticklabels([])
        ax.xaxis.tick_top()
        ax.set_xticks(range(len(cols)))
        ax.set_xticklabels([LABEL_NAMES.get(c, c.title()) for c in cols], rotation=90, ha="center", va="bottom")
        ax.tick_params(axis="x", length=2.5, pad=2)
        ax.spines["bottom"].set_visible(True)
        ax.spines["top"].set_visible(False)
        ax.yaxis.grid(True, color=GRID, lw=0.5, zorder=0)
        ax.set_axisbelow(True)
        ax.axvline(0.5, color=INK, lw=0.5, zorder=1)
        for j, lab in enumerate(cols):
            d = rq2[(k, lab)]
            if not all(truthy(d[c]["passes_agreement"]) for c in d):
                fail_cols.add(j)
                hatch_rect(ax, (j - 0.5, 0), 1, 100)
            for coder, col, mk, ms, dx in (("claude", C_CLAUDE, "o", 3.4, -off), ("codex", C_CODEX, "s", 3.1, off)):
                if coder not in d:
                    continue
                r = d[coder]
                est, lo, hi = fnum(r["weighted_pct"]), fnum(r["ci_lo_pct"]), fnum(r["ci_hi_pct"])
                ax.plot([j + dx, j + dx], [lo, hi], color=col, lw=1.1, solid_capstyle="butt", zorder=3)
                ax.plot([j + dx], [est], marker=mk, ms=ms, color=col, mec="white", mew=0.5, zorder=4, ls="none")
        if ki == 0:
            ax.set_ylabel("Eligible studies (%)")
        panel_letter(cv, xs[ki], 1.0, "abc"[ki])
        cv.text(xs[ki] + 0.5, 5.6, KIND_NAMES.get(k, k), fontsize=MIN_FONT, fontweight="bold", ha="left", va="top")
        for coder, y0 in (("claude", y_c), ("codex", y_x)):
            axh = cv.axes(xs[ki], y0, wk, heat_h)
            vals = np.full((nfam, len(cols)), np.nan)
            texts = [["" for _ in cols] for _ in range(nfam)]
            neutral = np.zeros((nfam, len(cols)), dtype=bool)
            for i, f in enumerate(families):
                for j, lab in enumerate(cols):
                    if lab == "ANY":
                        v = tot_kind.get((coder, k, f), 0.0)
                        neutral[i, j] = True
                    else:
                        v = counts.get((coder, k, f, lab), 0.0)
                    vals[i, j] = v
                    texts[i][j] = f"{int(v)}" if v else "·"
            draw_cell_grid(axh, vals, texts, fail_cols, vmax, neutral=neutral)
            axh.set_xticks([])
            if ki == 0:
                axh.set_yticks(range(nfam))
                axh.set_yticklabels(fam_labels)
                axh.tick_params(axis="y", length=0, pad=2)
                cv.text(1, y0 + heat_h / 2, "Primary-coder rows" if coder == "claude" else "Second-coder rows", fontsize=MIN_FONT,
                        rotation=90, ha="left", va="center", fontweight="bold",
                        color=C_CLAUDE if coder == "claude" else C_CODEX)
            else:
                axh.set_yticks([])
    y_leg = y_x + heat_h + 6
    cax = cv.axes(left, y_leg + 1.5, 36, 2.6)
    cax.imshow(np.linspace(0, 1, 256)[None, :], aspect="auto", cmap=CMAP, extent=[0, vmax, 0, 1])
    cax.set_yticks([])
    cax.set_xticks([0, vmax])
    cax.set_xticklabels(["0", f"{int(vmax)}"])
    cax.tick_params(length=2.5, pad=1.5)
    for s_ in cax.spines.values():
        s_.set_visible(False)
    cv.text(left + 38.5, y_leg + 1.2, "Rows per cell (unweighted);\ngrey: all rows of the kind", fontsize=MIN_FONT, ha="left", va="top")
    hs = coder_handles() + [hatch_handle("hatched: label field (E.derived_label) fails the full-sample\nagreement rule; the Any row passes (E.outcome_kind)")]
    cv.legend(hs, 2, y_leg + 11, ncol=3, handlelength=2.2, columnspacing=1.5, labelspacing=0.5)
    save(cv, out / "Fig7")
    return dict(families=nfam, kinds=kinds, columns=kind_cols, vmax=vmax, height_mm=round(h, 1))


# ------------------------------------------------------------------ Fig 9
def fig9(inp: Inputs, out: Path):
    item_order = ["robustness_tested|yes", "f1|yes", "f2|yes", "f3|yes", "f4|yes", "f9|yes", "f10|yes", "f12|yes"]
    items = {(r["item"], r["coder"]): r for r in inp.items}
    desc = {(r["coder"], r["feature"]) for r in inp.desc_only}
    fit = {(r["coder"], r["feature"]): r for r in inp.trend_fit}
    cnt = defaultdict(dict)
    for r in inp.trend_counts:
        cnt[(r["item"], r["coder"])][int(r["year"])] = (int(r["n_eligible"]), int(r["n_yes"]))
    shown = [it for it in item_order if (it, "claude") in cnt and (it, "codex") in cnt]
    years = sorted({y for v in cnt.values() for y in v})
    rowp, top, bot = 22.0, 9, 29
    h = top + rowp * len(shown) + bot
    cv = Canvas(h)
    xl, wl, xr, wr = 52, 78, 138, 31
    los, his = [], []
    for it in shown:
        for c in ("claude", "codex"):
            f = fit.get((c, "rq4|" + it))
            if f and f["status"] == "fitted" and (c, "rq4|" + it) not in desc:
                los.append(fnum(f["or_lo"]))
                his.append(fnum(f["or_hi"]))
    lo_lim = min(los + [0.5]) * 0.8
    hi_lim = max(his + [2.0]) * 1.25
    off = 0.14
    ref_n = None
    for ri, it in enumerate(shown):
        ytop = top + ri * rowp
        ax = cv.axes(xl, ytop + 2, wl, rowp - 5)
        ax.set_xlim(years[0] - 0.55, years[-1] + 0.55)
        ax.set_ylim(-0.3, 1.3)
        ax.set_yticks([0, 0.5, 1])
        ax.set_yticklabels(["0", "50", "100"])
        ax.set_xticks(years)
        ax.yaxis.grid(True, color=GRID, lw=0.5, zorder=0)
        ax.set_axisbelow(True)
        failing = not (truthy(items[(it, "claude")]["passes_agreement"]) and truthy(items[(it, "codex")]["passes_agreement"]))
        if failing:
            hatch_rect(ax, (years[0] - 0.55, -0.3), years[-1] - years[0] + 1.1, 1.6)
        ncl = {y: cnt[(it, "claude")].get(y, (0, 0)) for y in years}
        nco = {y: cnt[(it, "codex")].get(y, (0, 0)) for y in years}
        for col, mk, ms, dx, nn in ((C_CLAUDE, "o", 3.6, -off, ncl), (C_CODEX, "s", 3.3, off, nco)):
            pts = [(y + dx, nn[y][1] / nn[y][0]) for y in years if nn[y][0]]
            ax.plot([p[0] for p in pts], [p[1] for p in pts], color=col, lw=0.7, zorder=2)
            for y in years:
                n, k = nn[y]
                if n:
                    ax.plot([y + dx], [k / n], marker=mk, ms=ms, mfc=col if n >= 5 else "white", mec=col, mew=0.9,
                            zorder=4, ls="none")
        for y in years:  # k above the higher marker, below the lower one
            pts = [(nn[y][1] / nn[y][0], nn[y][1], d_) for nn, d_ in ((ncl, -off), (nco, off)) if nn[y][0]]
            if len(pts) == 2:
                order = sorted(range(2), key=lambda i: pts[i][0])
                if pts[0][0] == pts[1][0]:
                    order = [0, 1]
                flags = {order[0]: "below", order[1]: "above"}
                if pts[0][0] == pts[1][0]:
                    flags = {0: "above", 1: "above"}
            else:
                flags = {i: "above" for i in range(len(pts))}
            for i, (s_, k_, d_) in enumerate(pts):
                above = flags[i] == "above"
                ax.text(y + d_, s_ + (0.1 if above else -0.1), f"{k_}", ha="center", va="bottom" if above else "top",
                        fontsize=MIN_FONT, color=INK, zorder=5)
        if ri < len(shown) - 1:
            ax.set_xticklabels([])
        else:
            ax.set_xticklabels([f"{y}\n{ncl[y][0]} | {nco[y][0]}" for y in years])
            ax.tick_params(axis="x", pad=2)
            ref_n = (ncl, nco)
        cv.text(xl - 9, ytop + rowp / 2 - 0.5, ITEM_NAMES.get(it.split("|")[0], it), fontsize=MIN_FONT, ha="right", va="center")
        axr = cv.axes(xr, ytop + 2, wr, rowp - 5)
        axr.set_xscale("log")
        axr.set_xlim(lo_lim, hi_lim)
        axr.set_ylim(0.6, -0.6)
        axr.set_yticks([])
        axr.spines["left"].set_visible(False)
        axr.axvline(1.0, color=INK, lw=0.6, zorder=1)
        axr.xaxis.grid(True, color=GRID, lw=0.5, zorder=0)
        axr.set_axisbelow(True)
        if failing:
            hatch_rect(axr, (lo_lim, -0.6), hi_lim - lo_lim, 1.2)
        for coder, col, mk, ms, dy in (("claude", C_CLAUDE, "o", 3.4, -0.27), ("codex", C_CODEX, "s", 3.1, 0.27)):
            key = (coder, "rq4|" + it)
            f = fit.get(key)
            if key in desc or not f or f["status"] != "fitted":
                axr.text(1.0, dy, "descriptive only", ha="center", va="center", fontsize=MIN_FONT, color=col, zorder=5,
                         bbox=dict(boxstyle="square,pad=0.15", fc="white", ec="none"))
            else:
                est, lo, hi = fnum(f["OR_per_year"]), fnum(f["or_lo"]), fnum(f["or_hi"])
                axr.plot([lo, hi], [dy, dy], color=col, lw=1.1, solid_capstyle="butt", zorder=3)
                axr.plot([est], [dy], marker=mk, ms=ms, color=col, mec="white", mew=0.5, zorder=4, ls="none")
        axr.xaxis.set_minor_formatter(mticker.NullFormatter())
        ticks = [t for t in (0.25, 0.5, 1, 2, 4) if lo_lim <= t <= hi_lim]
        axr.set_xticks(ticks)
        axr.set_xticklabels([f"{t:g}" for t in ticks])
        if ri < len(shown) - 1:
            axr.tick_params(axis="x", which="both", labelbottom=False)
    mismatch = []
    for it in shown:
        for c, rn in (("claude", ref_n[0]), ("codex", ref_n[1])):
            if any(cnt[(it, c)].get(y, (0, 0))[0] != rn[y][0] for y in years):
                mismatch.append((it, c))
    if mismatch:
        log(f"Fig9: WARNING yearly n differs from the bottom row for {mismatch}; n under the axis applies to the bottom item only")
    ybot = top + rowp * len(shown)
    cv.text(xl - 9, ybot + 1.0, "Eligible studies per\nyear, n (primary | second coder)", fontsize=MIN_FONT, ha="right", va="top")
    cv.text(xr + wr / 2, ybot + 4.2, "Odds ratio per year (log scale)", fontsize=MIN_FONT, ha="center", va="top")
    panel_letter(cv, 1, 0.3, "a")
    panel_letter(cv, xr - 1.5, 0.3, "b")
    cv.text(xl + wl / 2, 3.6, "Observed share per publication year (%); k = studies reporting", fontsize=MIN_FONT, ha="center", va="top")
    cv.text(xr + wr / 2, 3.6, "Weighted logistic trend", fontsize=MIN_FONT, ha="center", va="top")
    hs = coder_handles() + [Line2D([0], [0], marker="o", color="none", mfc="white", mec=INK, ms=4.2, label="open marker: fewer than 5 studies in the year"),
                            hatch_handle(FAIL_TEXT + FAIL_RULE)]
    cv.legend(hs, 2, ybot + 15, ncol=2, handlelength=2.2, columnspacing=1.2, labelspacing=0.45)
    save(cv, out / "Fig9")
    return dict(items=shown, years=years, descriptive_only=sorted(f"{c}:{f}" for c, f in desc), height_mm=round(h, 1),
                n_mismatch=mismatch, or_axis=[round(lo_lim, 3), round(hi_lim, 3)])


# ------------------------------------------------------------------ Fig 10
def fig10(inp: Inputs, out: Path):
    fam = [r for r in inp.fam if r["coder"] == "claude"]
    cols = [k for k in ITEM_NAMES]
    cols = [c for c in cols if any(r["item"] == f"{c}|yes" for r in fam)]
    cell = {(r["item"], r["paradigm_family"]): (int(float(r["k"])), int(float(r["n"]))) for r in fam}
    fam_ids = {r["paradigm_family"] for r in fam}

    def fam_n(f):
        return max([cell[(f"{c}|yes", f)][1] for c in cols if (f"{c}|yes", f) in cell] + [0])

    families = sorted(fam_ids, key=lambda f: (f == "none_listed", -fam_n(f), f))
    items = {(r["item"], r["coder"]): r for r in inp.items}
    fails = {c: not truthy(items[(f"{c}|yes", "claude")]["passes_agreement"]) for c in cols if (f"{c}|yes", "claude") in items}
    rows = families + ["__all__"]
    nr, nc = len(rows), len(cols)
    pitch, left, right, top = 5.4, 36, 2, 44
    heat_h = nr * pitch
    h = top + heat_h + 31
    cv = Canvas(h)
    ax = cv.axes(left, top, W - left - right, heat_h)
    vals = np.full((nr, nc), np.nan)
    texts = [["" for _ in range(nc)] for _ in range(nr)]
    neutral = np.zeros((nr, nc), dtype=bool)
    for i, f in enumerate(rows):
        for j, c in enumerate(cols):
            it = f"{c}|yes"
            if f == "__all__":
                r = items.get((it, "claude"))
                if not r:
                    continue
                k, n = int(float(r["k"])), int(float(r["denominator"]))
                if c == "f6_applicable":  # denominator = studies where f6 applies; not in the all-row source
                    kn = [cell[(it, g)] for g in families if (it, g) in cell]
                    k, n = int(float(r["k"])), int(float(r["denominator"]))
            else:
                if (it, f) not in cell:
                    continue
                k, n = cell[(it, f)]
            texts[i][j] = f"{k}/{n}"
            if n:
                vals[i, j] = k / n
            neutral[i, j] = n < 5
    draw_cell_grid(ax, vals, texts, {j for j, c in enumerate(cols) if fails.get(c)}, 1.0, neutral=neutral)
    ax.set_yticks(range(nr))
    ax.set_yticklabels(["All eligible studies" if f == "__all__" else FAMILY_NAMES.get(f, f) for f in rows])
    ax.tick_params(axis="y", length=0, pad=2)
    ax.xaxis.tick_top()
    ax.set_xticks(range(nc))
    ax.set_xticklabels([ITEM_NAMES.get(c, c) for c in cols], rotation=90, ha="center", va="bottom")
    ax.tick_params(axis="x", length=0, pad=2)
    ax.axhline(nr - 1.5, color=INK, lw=0.7, zorder=5)
    y_leg = top + heat_h + 5
    cax = cv.axes(left, y_leg + 1.5, 40, 2.6)
    cax.imshow(np.linspace(0, 1, 256)[None, :], aspect="auto", cmap=CMAP, extent=[0, 100, 0, 1])
    cax.set_yticks([])
    cax.set_xticks([0, 50, 100])
    cax.tick_params(length=2.5, pad=1.5)
    for s in cax.spines.values():
        s.set_visible(False)
    cv.text(left + 42.5, y_leg + 1.2, "Studies reporting the item (%); each cell shows k/n", fontsize=MIN_FONT, ha="left", va="top")
    hs = [hatch_handle("hatched: item fails the full-sample agreement rule\n" + FAIL_RULE.strip(" ()")),
          Patch(facecolor=NEUTRAL_CELL, edgecolor="none", label="grey: fewer than 5 studies in the cell (no colour scale)")]
    cv.legend(hs, left, y_leg + 9, ncol=1, handlelength=2.2, labelspacing=0.45)
    save(cv, out / "Fig10")
    return dict(families=families, columns=cols, failing_columns=sorted(c for c, v in fails.items() if v), height_mm=round(h, 1))


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input_dir", nargs="?", default="runs/rq234-interim")
    ap.add_argument("--out-dir", default="paper/figures")
    ap.add_argument("--log-dir", default="runs/fig6-10")
    ap.add_argument("--only", default="6,7,8,9,10")
    a = ap.parse_args()

    def rel(p):
        p = Path(p)
        return p if p.is_absolute() else ROOT / p

    d, out, logd = rel(a.input_dir), rel(a.out_dir), rel(a.log_dir)
    out.mkdir(parents=True, exist_ok=True)
    logd.mkdir(parents=True, exist_ok=True)
    fam = setup_fonts()
    inp = Inputs(d)
    log(f"input {d} run={inp.run} interim={inp.interim} font={fam}")
    for c in (C_CLAUDE, C_CODEX):
        log(f"palette {c} contrast on white {contrast(c, '#FFFFFF'):.2f}:1")
        assert contrast(c, "#FFFFFF") >= 4.5
    todo = {int(x) for x in a.only.split(",")}
    metrics = {}
    for n, fn in ((6, fig6), (7, fig7), (8, fig8), (9, fig9), (10, fig10)):
        if n in todo:
            metrics[f"Fig{n}"] = fn(inp, out)
            log(f"Fig{n} done: {metrics[f'Fig{n}']}")
    metrics["min_cell_text_contrast"] = round(MIN_CONTRAST_SEEN[0], 2)
    metrics["input_dir"] = str(d)
    metrics["interim"] = inp.interim
    metrics["inputs_sha256"] = {k: sha(p) for k, p in inp.paths.items()}
    (logd / "metrics.json").write_text(json.dumps(metrics, indent=1, default=str), encoding="utf-8")
    log(f"min cell text contrast {MIN_CONTRAST_SEEN[0]:.2f}:1")
    (logd / "fig6_10.log").write_text("\n".join(LOG) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()

"""Figure 14 of the review: organising scheme (audit of facets), pilot evidence, and proposals / agenda.

    .venv/Scripts/python.exe -I analysis/fig14_framework.py [INPUT_DIR] [--pilot-dir runs/pilot-side-by-side]
        [--pilot-runs runs/pilot] [--calib-dir runs/pilot-rule-calibration] [--placement-dir runs/pilot-placement-sensitivity]
        [--out-dir paper/figures] [--log-dir runs/fig14]

INPUT_DIR defaults to runs/rq234-interim and is the only place the literature-audit numbers come from
(fig_inputs/rq4_items_by_coder.csv, fig_inputs/rq3_comparisons.csv, rq3.csv, agreement.csv, nonresponse.md, config.json).
The pilot numbers come from PILOT_DIR (table_a1.csv, fig_inputs/fig12_variance_terms.csv) and the numeric-precision
footnote from PILOT_RUNS/*/meta.json. Panel B also reads the rule calibration (CALIB_DIR/summary.csv, config.json: probability
that the preregistered rule labels a prompt-invariant model with the human effect fragile, per paradigm) and the placement
sensitivity (PLACEMENT_DIR/placement_counts.csv: placement counts for all grids and for the grids without near-deterministic
cells). Every displayed percentage of panel A uses the rounding of the paper macros (analysis/paper_numbers.py: the 2-decimal
value written to rq3.csv/rq4.csv, then one decimal), see r1(). No result number is typed in this file: a rerun on the final extraction
(`... runs/rq234-final`) updates every number, count, interval and flag. Only labels, the roadmap and checklist wording,
and the component mapping of the roadmap (editorial text from research/reports/breakthrough-thinker/2026-10-17-framework-v2.md,
sections 3, 7 and 8) are constants.

Binding constraints (Codex round 4 and the G5 VERDICT, 2026-10-16): descriptive figure with no title or caption in the image;
literature-audit evidence (panel A) and pilot evidence (panel B) in separate panels; fields that fail the agreement rule
hatched and shown for both coders; interim caveat; the Codex f5 against perturbation/wording discrepancy is computed and
marked; no LLM/human spread ratio anywhere (the ratio column of table_a1.csv is never read); roadmap items drawn as an agenda.
Revision B1/B3 (2026-10-17): the rule-outcome strip marks the grids whose paradigm the rule labels fragile at n = 50 even for a
prompt-invariant human-like model; the placement strip shows all grids beside the grids without near-deterministic cells.
Outputs: Fig14.pdf / Fig14.eps (fonts embedded, TrueType), Fig14.png (600 dpi, 8-bit RGB), a log, metrics.json and a
caption draft in LOG_DIR.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import re
import textwrap
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib as mpl  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
from matplotlib.colors import to_rgb  # noqa: E402
from matplotlib.patches import Rectangle  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
MM = 1 / 25.4
W = 174.0  # mm, full page width (Springer double column)
MAX_H = 220.0

C_CLAUDE = "#0072B2"
C_CODEX = "#B34700"
INK = "#111111"
HATCH_EDGE = "#B3B3B3"
BOUND = "#767676"
GRID = "#D9D9D9"
BAND = "#E6E6E6"
DARK, MID, LIGHT = "#404040", "#9A9A9A", "#DADADA"
FS = 7.0

LOG: list[str] = []


def log(msg: str) -> None:
    LOG.append(msg)
    print(msg)


# ------------------------------------------------------------------ helpers
def _lin(c):
    return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4


def lum(hexc):
    r, g, b = to_rgb(hexc)
    return 0.2126 * _lin(r) + 0.7152 * _lin(g) + 0.0722 * _lin(b)


def contrast(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def r1(x) -> str:
    """One-decimal display with the rounding of the paper macros: paper_numbers.py formats the 2-decimal value of rq3.csv/rq4.csv
    (already rounded once), so 10.852 shows as 10.8 (10.85 -> 10.8) and 35.848 as 35.9 (35.85 -> 35.9), as in the text."""
    return f"{float(f'{float(x):.2f}'):.1f}"


def read_csv(p: Path):
    with open(p, newline="", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def fnum(x, d=float("nan")):
    try:
        return float(x)
    except (TypeError, ValueError):
        return d


def truthy(x):
    return str(x).strip().lower() in ("true", "1", "yes")


def isnan(x):
    return x != x


# ------------------------------------------------------------------ inputs
class Audit:
    def __init__(self, d: Path):
        fi = d / "fig_inputs"
        self.paths = {
            "items": fi / "rq4_items_by_coder.csv", "comp": fi / "rq3_comparisons.csv", "rq3": d / "rq3.csv",
            "agreement": d / "agreement.csv", "nonresponse": d / "nonresponse.md", "config": d / "config.json",
        }
        miss = [str(p) for p in self.paths.values() if not p.exists()]
        if miss:
            raise SystemExit("missing input files: " + ", ".join(miss))
        self.items = {(r["item"], r["coder"]): r for r in read_csv(self.paths["items"])}
        self.comp = {(r["comparison_basis"], r["comparison_type"], r["coder"]): r for r in read_csv(self.paths["comp"])}
        self.rq3 = {r["feature"]: r for r in read_csv(self.paths["rq3"])}
        self.agree = {r["field"]: r for r in read_csv(self.paths["agreement"])}
        self.config = json.loads(self.paths["config"].read_text(encoding="utf-8"))
        self.run = self.config.get("run", d.name)
        self.interim = bool(self.config.get("interim", False))
        txt = self.paths["nonresponse"].read_text(encoding="utf-8")
        # bounds on RQ4 prevalences: "| claude | rq4/f5/yes | 69 | 24 | 23.4 | ... | 16.3 to 64.8 |"
        self.bounds = {}
        for m in re.finditer(r"^\|\s*(claude|codex)\s*\|\s*(rq4/[^|\s]+)\s*\|.*?\|\s*([\d.]+) to ([\d.]+)\s*\|\s*$", txt, re.M):
            self.bounds[(m.group(1), m.group(2))] = (float(m.group(3)), float(m.group(4)))
        # eligible share table: coder | n_analysed | n_respondents | n_eligible_respondents | n_unknown_status | ...
        self.elig = {}
        for m in re.finditer(r"^\|\s*(claude|codex)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*[\d.]+\s*\|", txt, re.M):
            self.elig[m.group(1)] = dict(analysed=int(m.group(2)), resp=int(m.group(3)), eligible=int(m.group(4)),
                                         unknown=int(m.group(5)))
        if set(self.elig) != {"claude", "codex"}:
            raise SystemExit("could not parse the eligible-share table of nonresponse.md")


def item_est(a: Audit, key: str, coder: str):
    r = a.items.get((key, coder))
    if r is None:
        return None
    return dict(est=fnum(r["weighted_pct"]), lo=fnum(r["ci_lo_pct"]), hi=fnum(r["ci_hi_pct"]), k=int(float(r["k"])),
                n=int(float(r["denominator"])), passes=truthy(r["passes_agreement"]), kappa=fnum(r["kappa"]),
                pagree=fnum(r["percent_agreement"]), rule=r["rule_basis"])


def comp_est(a: Audit, typ: str, coder: str):
    r = a.comp[("types_any", typ, coder)]
    return dict(est=fnum(r["weighted_pct"]), lo=fnum(r["ci_lo_pct"]), hi=fnum(r["ci_hi_pct"]), k=int(float(r["k"])),
                n=int(float(r["denominator"])), passes=truthy(r["passes_agreement"]), kappa=fnum(r["kappa"]),
                pagree=fnum(r["percent_agreement"]), rule=r["rule_basis"])


def humann_est(a: Audit, coder: str):
    r = a.rq3["rq3|human_n|reported"]
    return dict(est=fnum(r[f"{coder}_est_pct"]), lo=fnum(r[f"{coder}_lo_pct"]), hi=fnum(r[f"{coder}_hi_pct"]),
                k=int(float(r[f"{coder}_k"])), n=int(float(r[f"{coder}_n_domain"])), passes=truthy(r["passes_v012_rule"]),
                kappa=fnum(r["kappa"]), pagree=fnum(r["percent_agreement"]), rule=r["rule_basis"])


class Pilot:
    def __init__(self, d: Path, runs: Path, calib: Path, place: Path):
        self.a1 = read_csv(d / "table_a1.csv")  # note: the ratio column is never read
        self.terms = read_csv(d / "fig_inputs" / "fig12_variance_terms.csv")
        self.paths = [d / "table_a1.csv", d / "fig_inputs" / "fig12_variance_terms.csv"]
        # rule calibration: zero-spread human-replica model (normal variant, as in Sections 6.2 and 6.4)
        cfg = json.loads((calib / "config.json").read_text(encoding="utf-8"))
        if cfg.get("smoke"):
            raise SystemExit("rule calibration run is a smoke run")
        self.calib_n = int(cfg["n_per_arm"])
        self.calib_reps = int(cfg["reps"])
        self.calib = {r["paradigm"]: fnum(r["P_fragile"]) for r in read_csv(calib / "summary.csv") if r["variant"] == "normal"}
        # placement sensitivity: all grids, and grids without near-deterministic cells (F kept)
        pc = {r["analysis"]: r for r in read_csv(place / "placement_counts.csv")}
        key_all, key_nd = "original (all grids, F kept)", "(a) grids without near-deterministic cells, F kept"
        if key_all not in pc or key_nd not in pc:
            raise SystemExit("placement_counts.csv lacks the expected rows")
        self.place_all = {c: int(float(pc[key_all][c])) for c in ("n_grids", "larger", "overlap", "smaller")}
        self.place_nd = {c: int(float(pc[key_nd][c])) for c in ("n_grids", "larger", "overlap", "smaller")}
        self.paths += [calib / "summary.csv", calib / "config.json", place / "placement_counts.csv"]
        self.n_grids = len(self.a1)
        self.models = sorted({r["model"] for r in self.a1})
        self.paradigms = sorted({r["paradigm"] for r in self.a1})
        self.cells = sorted({int(float(r["C"])) for r in self.a1})
        self.quant = {}
        for m in self.models:
            p = runs / m / "meta.json"
            if p.exists():
                self.quant[m] = json.loads(p.read_text(encoding="utf-8")).get("quant", "?")
                self.paths.append(p)


# ------------------------------------------------------------------ fonts and canvas
def setup_fonts() -> str:
    from matplotlib import font_manager as fm

    names = {f.name for f in fm.fontManager.ttflist}
    fam = "Arial" if "Arial" in names else "DejaVu Sans"
    mpl.rcParams.update({
        "font.family": fam, "font.size": FS, "pdf.fonttype": 42, "ps.fonttype": 42, "text.color": INK,
        "savefig.facecolor": "white", "figure.facecolor": "white", "hatch.linewidth": 0.5,
    })
    return fam


class Canvas:
    """One full-figure axes in millimetres, y measured from the top."""

    def __init__(self, h: float):
        self.h = h
        self.fig = plt.figure(figsize=(W * MM, h * MM))
        self.ax = self.fig.add_axes([0, 0, 1, 1])
        self.ax.set_xlim(0, W)
        self.ax.set_ylim(h, 0)
        self.ax.axis("off")
        self.fig.canvas.draw()
        self.rend = self.fig.canvas.get_renderer()

    def text(self, x, y, s, size=FS, ha="left", va="center", bold=False, italic=False, color=INK, z=6):
        return self.ax.text(x, y, s, fontsize=size, ha=ha, va=va, fontweight="bold" if bold else "normal",
                            fontstyle="italic" if italic else "normal", color=color, zorder=z, clip_on=False)

    def width(self, s, size=FS, bold=False) -> float:
        t = self.ax.text(0, 0, s, fontsize=size, fontweight="bold" if bold else "normal")
        w = t.get_window_extent(self.rend).width / self.fig.dpi * 25.4
        t.remove()
        return w

    def line(self, xs, ys, color=INK, lw=0.6, z=3, **kw):
        self.ax.plot(xs, ys, color=color, lw=lw, solid_capstyle="butt", zorder=z, clip_on=False, **kw)

    def rect(self, x, y, w, h, fc="none", ec="none", lw=0.0, hatch=None, z=1):
        self.ax.add_patch(Rectangle((x, y), w, h, facecolor=fc, edgecolor=ec, linewidth=lw, hatch=hatch, zorder=z))

    def marker(self, x, y, m, ms, fc, ec=None, mew=0.5, z=5):
        self.ax.plot([x], [y], marker=m, ms=ms, mfc=fc, mec=ec or fc, mew=mew, ls="none", zorder=z, clip_on=False)

    def wrap(self, s, x, y, maxw, pitch=3.05, **kw):
        """Greedy wrap by measured width; returns y after the last line."""
        words, line = s.split(), ""
        for wd in words:
            trial = (line + " " + wd).strip()
            if self.width(trial, bold=kw.get("bold", False)) > maxw and line:
                self.text(x, y, line, **kw)
                y += pitch
                line = wd
            else:
                line = trial
        if line:
            self.text(x, y, line, **kw)
            y += pitch
        return y


def dot_glyph(cv: Canvas, x, y, coder):
    """Legend glyph: whisker plus marker for a coder."""
    col, mk, ms = (C_CLAUDE, "o", 3.1) if coder == "claude" else (C_CODEX, "s", 2.8)
    cv.line([x - 1.6, x + 1.6], [y, y], color=col, lw=1.0)
    cv.marker(x, y, mk, ms, col, "white", 0.4)


# ------------------------------------------------------------------ panel A row definitions
# kind: rq4 (key in rq4_items_by_coder), comp (rq3 comparator type), humann, agree (agreement.csv field), nc (not coded)
LEFT = [
    dict(tag="1", label="Wording (perturbation)", kind="rq4", key="perturbation|wording", bound="perturbation/wording", disc=True),
    dict(label="Paraphrases compared (f5)", kind="rq4", key="f5|yes", bound="f5/yes", disc=True),
    dict(label="Option order (perturbation)", kind="rq4", key="perturbation|option_order", bound="perturbation/option_order"),
    dict(label="Order, where applicable (f6)", kind="rq4", key="f6_applicable|yes"),
    dict(label="Response format", kind="rq4", key="perturbation|response_format"),
    dict(label="System prompt, few-shot, CoT", kind="nc"),
    dict(tag="2", label="Persona", kind="rq4", key="perturbation|persona"),
    dict(tag="3", label="Language", kind="rq4", key="perturbation|language"),
    dict(tag="4", label="Several temperatures (f7)", kind="rq4", key="f7|yes", bound="f7/yes"),
    dict(label="Decoding (perturbation)", kind="rq4", key="perturbation|decoding"),
    dict(label="Seeds (perturbation)", kind="rq4", key="perturbation|seeds"),
    dict(tag="5", label="Model version (perturbation)", kind="rq4", key="perturbation|model_version"),
    dict(label="Snapshots compared (f8)", kind="rq4", key="f8|yes", bound="f8/yes"),
    dict(tag="6", label="Novel or perturbed items (f9)", kind="rq4", key="f9|yes", bound="f9/yes"),
    dict(label="Contamination (perturbation)", kind="rq4", key="perturbation|contamination"),
    dict(tag="7", label="Scoring method", kind="nc"),
    dict(label="Any of six judged types", kind="rq4", key="robustness_tested|yes", bound="robustness_tested/yes", bold=True),
]
RIGHT = [
    dict(head="Condition stated, not varied"),
    dict(tag="1", label="Full prompts available (f4)", kind="rq4", key="f4|yes", bound="f4/yes"),
    dict(tag="4", label="Temperature stated (f2)", kind="rq4", key="f2|yes", bound="f2/yes"),
    dict(label="Repeated draws, n stated (f3)", kind="rq4", key="f3|yes", bound="f3/yes"),
    dict(tag="5", label="Exact model and date (f1)", kind="rq4", key="f1|yes", bound="f1/yes"),
    dict(tag="C", label="Test or interval (f10)", kind="rq4", key="f10|yes", bound="f10/yes"),
    dict(label="Preregistration cited (f11)", kind="rq4", key="f11|yes", bound="f11/yes"),
    dict(label="Code or data link (f12)", kind="rq4", key="f12|yes", bound="f12/yes"),
    dict(head="Estimand, comparator and claim"),
    dict(tag="E", label="Outcome kind (matched rows)", kind="agree", key="E.outcome_kind"),
    dict(tag="8", label="Replication dataset", kind="comp", key="replication_dataset", zero=True),
    dict(label="Published norms", kind="comp", key="published_norms"),
    dict(label="Own human sample", kind="comp", key="own_sample"),
    dict(label="No human comparison", kind="comp", key="none"),
    dict(label="Human n reported", kind="humann"),
    dict(tag="C", label="Derived label (script)", kind="agree", key="E.derived_label (script)"),
    dict(label="Claim scope", kind="nc"),
]

# Panel C text constants (framework-v2.md, sections 7 and 8)
MR12 = [  # (short label, pilot factor letter or "", overlap letters)
    ("Estimand, metric, scoring, comparability", "", "T"),
    ("Model identifier, dates, access, precision", "", "G A C"),
    ("Complete prompts, system message, examples", "", "G T C"),
    ("Several wordings crossed with conditions", "W", "g A"),
    ("Counterbalance option order", "O", ""),
    ("Response format, parsing, validity rates", "F", "T"),
    ("Decoding settings, draws, near-deterministic share", "", "G T A"),
    ("Test alternative decoding settings", "T", "A"),
    ("Compare snapshots or generations", "", "g"),
    ("Item provenance, isomorphs", "", "g"),
    ("Cell-level estimates, claim type and scope", "", "Y"),
    ("Comparator source, n, between-sample spread", "", ""),
]
COMPONENTS = ["E", "1", "2", "3", "4", "5", "6", "7", "8", "C"]
ROADMAP = [  # (code, label, components addressed)
    ("R1", "Facet sizes at scale", ["1", "4", "5"]),
    ("R2", "Spread against humans", ["1", "8"]),
    ("R3", "Sign against magnitude", ["E", "8", "C"]),
    ("R4", "Snapshot and precision drift", ["5"]),
    ("R5", "Classic against isomorph items", ["6"]),
    ("R6", "Estimand near determinism", ["E", "4", "7"]),
    ("R7", "Predictive value of the scheme", COMPONENTS),
]
OVERLAP_KEY = [("G", "GUIDE-LLM core"), ("g", "GUIDE-LLM optional"), ("A", "Abdurahman et al."), ("T", "TRIPOD-LLM"),
               ("C", "CHART"), ("Y", "Ye et al. 2026")]


# ------------------------------------------------------------------ figure
HX = [1.0, 88.0]  # left edge of each half in panel A (mm)
TAG_X, LAB_X, AX0, AX1, VAL_X, KAP_R = 0.0, 3.8, 40.5, 62.0, 63.6, 85.0
PITCH = 3.0
XMAX = 100.0


def ax_x(hx, pct):
    return hx + AX0 + (AX1 - AX0) * pct / XMAX


def row_data(a: Audit, row):
    """Return {coder: est dict} for a data row, or None."""
    k = row["kind"]
    if k == "rq4":
        return {c: item_est(a, row["key"], c) for c in ("claude", "codex")}
    if k == "comp":
        return {c: comp_est(a, row["key"], c) for c in ("claude", "codex")}
    if k == "humann":
        return {c: humann_est(a, c) for c in ("claude", "codex")}
    return None


def status(d):
    """fail / low / ok from the Claude-side field status (agreement is a property of the field, not of the coder)."""
    e = d["claude"]
    if not e["passes"]:
        return "fail"
    if not isnan(e["kappa"]) and e["kappa"] < 0.6:
        return "low"
    return "ok"


def draw_row(cv: Canvas, a: Audit, hx, y, row, metrics):
    cy = y + PITCH / 2
    if row.get("tag"):
        cv.text(hx + TAG_X, cy, row["tag"], bold=True)
    if row["kind"] == "nc":
        cv.text(hx + LAB_X, cy, row["label"])
        cv.rect(hx + AX0, y + 0.45, AX1 - AX0, PITCH - 0.9, fc=BAND, z=1)
        cv.text(hx + AX0 + (AX1 - AX0) / 2, cy, "not coded", ha="center")
        metrics["not_coded"].append(row["label"])
        return
    if row["kind"] == "agree":
        f = a.agree[row["key"]]
        kap, ok = fnum(f["kappa"]), truthy(f["passes_v012_rule"])
        cv.text(hx + LAB_X, cy, row["label"])
        if not ok:
            cv.rect(hx + AX0, y, AX1 - AX0, PITCH, ec=HATCH_EDGE, hatch="////", z=1)
        tw = cv.width("agreement only")
        cv.rect(hx + AX0 + (AX1 - AX0) / 2 - tw / 2 - 0.5, cy - 1.2, tw + 1.0, 2.4, fc="white", z=6)
        cv.text(hx + AX0 + (AX1 - AX0) / 2, cy, "agreement only", ha="center", italic=True)
        cv.text(hx + KAP_R, cy, f"{kap:.3f}", ha="right")
        metrics["agree_rows"][row["key"]] = dict(kappa=kap, passes=ok)
        return
    d = row_data(a, row)
    st = status(d)
    cv.text(hx + LAB_X + (0 if not row.get("bold") else 0), cy, row["label"] + (" ‡" if row.get("disc") else ""),
            bold=row.get("bold", False))
    if st == "fail":
        cv.rect(hx + AX0, y, AX1 - AX0, PITCH, ec=HATCH_EDGE, hatch="////", z=1)
    elif st == "low":
        cv.rect(hx + AX0, y, AX1 - AX0, PITCH, ec=HATCH_EDGE, hatch="....", z=1)
    for coder, dy, col, mk, ms in (("claude", -0.62, C_CLAUDE, "o", 3.0), ("codex", 0.62, C_CODEX, "s", 2.7)):
        e = d[coder]
        yy = cy + dy
        bnd = a.bounds.get((coder, "rq4/" + row["bound"])) if row.get("bound") else None
        if bnd:
            cv.line([ax_x(hx, bnd[0]), ax_x(hx, bnd[1])], [yy, yy], color=BOUND, lw=0.45, z=2)
            for bx in bnd:
                cv.line([ax_x(hx, bx)] * 2, [yy - 0.45, yy + 0.45], color=BOUND, lw=0.45, z=2)
            metrics["bounds_drawn"] += 1
        lo, hi = e["lo"], e["hi"]
        if not isnan(lo) and not isnan(hi):
            cv.line([ax_x(hx, lo), ax_x(hx, hi)], [yy, yy], color=col, lw=0.9, z=3)
        cv.marker(ax_x(hx, e["est"]), yy, mk, ms, col, "white", 0.35, z=5)
    c, x = d["claude"], d["codex"]
    if row.get("zero"):
        vt = f"{c['k']}/{c['n']} [{x['k']}/{x['n']}]"
    else:
        vt = f"{r1(c['est'])} [{r1(x['est'])}]"
    cv.text(hx + VAL_X, cy, vt)
    kap = c["kappa"]
    cv.text(hx + KAP_R, cy, "n/a" if isnan(kap) else f"{kap:.3f}", ha="right")
    bnds = {cd: a.bounds.get((cd, "rq4/" + row["bound"])) for cd in ("claude", "codex")} if row.get("bound") else {}
    metrics["rows"].append(dict(label=row["label"], key=row.get("key"), status=st, claude=c, codex=x,
                                bounds=row.get("bound") is not None, bound_values=bnds))


def panel_header(cv: Canvas, y, letter, title, right):
    cv.rect(0.0, y, W, 4.6, fc=BAND, z=0)
    cv.text(1.0, y + 2.35, letter, size=9, bold=True)
    cv.text(5.2, y + 2.35, title, bold=True)
    cv.text(W - 1.0, y + 2.35, right, ha="right", italic=True)
    return y + 4.6


def legend_flow(cv: Canvas, items, x0, y, maxx, pitch=3.6):
    """items: (glyph_fn(x,y) -> glyph width, text). Flow left to right, wrapping at maxx."""
    x = x0
    for glyph, text in items:
        gw = 5.2
        tw = cv.width(text)
        if x + gw + tw > maxx and x > x0:
            x = x0
            y += pitch
        glyph(x + gw / 2 - 0.2, y)
        cv.text(x + gw, y, text)
        x += gw + tw + 3.0
    return y + pitch


def build(a: Audit, p: Pilot, out: Path, logdir: Path):
    assert contrast(C_CLAUDE, "#FFFFFF") >= 4.5 and contrast(C_CODEX, "#FFFFFF") >= 4.5
    assert contrast(BOUND, "#FFFFFF") >= 4.5
    metrics = dict(rows=[], bounds_drawn=0, not_coded=[], agree_rows={})
    H0 = 300.0  # provisional; the canvas is rebuilt at the measured height
    for attempt in range(2):
        cv = Canvas(H0)
        y = 0.6
        # ---------------- panel A
        n_c, n_x = a.elig["claude"], a.elig["codex"]
        y = panel_header(cv, y, "A", "Literature audit: facets varied and conditions stated",
                         ("interim; " if a.interim else "") + f"{n_c['eligible']} [{n_x['eligible']}] eligible studies of {n_c['analysed']} analysed (primary coder [second coder])")
        y += 1.8
        items = [
            (lambda x, yy: dot_glyph(cv, x, yy, "claude"), "Primary coder, 95% interval"),
            (lambda x, yy: dot_glyph(cv, x, yy, "codex"), "Second coder, 95% interval"),
            (lambda x, yy: (cv.line([x - 1.8, x + 1.8], [yy, yy], color=BOUND, lw=0.45),
                            [cv.line([xx] * 2, [yy - 0.45, yy + 0.45], color=BOUND, lw=0.45) for xx in (x - 1.8, x + 1.8)]),
             f"bounds for the {n_c['unknown']} records of unknown status"),
            (lambda x, yy: cv.rect(x - 2.0, yy - 1.0, 4.2, 2.0, ec=HATCH_EDGE, hatch="////"),
             "fails the agreement rule: coder sensitivity, not uncertainty"),
            (lambda x, yy: cv.rect(x - 2.0, yy - 1.0, 4.2, 2.0, ec=HATCH_EDGE, hatch="...."),
             "passes on percent agreement, κ below 0.6"),
            (lambda x, yy: cv.rect(x - 2.0, yy - 1.0, 4.2, 2.0, fc=BAND), "field not coded"),
        ]
        y = legend_flow(cv, items, 1.0, y + 1.0, W - 1.0) + 0.6
        yhead = y
        for hx in HX:
            cv.text(hx + AX0 + (AX1 - AX0) / 2, y + 1.4, "% of eligible studies", ha="center")
            cv.text(hx + VAL_X, y + 1.4, "Primary [second coder]")
            cv.text(hx + KAP_R, y + 1.4, "κ", ha="right")
        y += 3.4
        cv.line([1.0, W - 1.0], [y, y], color=INK, lw=0.5)
        ytop = y + 0.6
        # left block
        yl = ytop
        cv.text(HX[0], yl + PITCH / 2, "Facet varied (run and reported)", bold=True)
        yl += PITCH
        first = True
        for r in LEFT:
            if r.get("tag") and not first:
                cv.line([HX[0], HX[0] + 85.0], [yl, yl], color=GRID, lw=0.4, z=1)
            first = False
            draw_row(cv, a, HX[0], yl, r, metrics)
            yl += PITCH
        # right block
        yr = ytop
        first = True
        for r in RIGHT:
            if "head" in r:
                if not first:
                    cv.line([HX[1], HX[1] + 85.0], [yr + 0.2, yr + 0.2], color=INK, lw=0.4, z=1)
                    yr += 0.4
                cv.text(HX[1], yr + PITCH / 2, r["head"], bold=True)
                yr += PITCH
                first = False
                continue
            if r.get("tag") and not first and RIGHT[RIGHT.index(r) - 1].get("kind"):
                cv.line([HX[1], HX[1] + 85.0], [yr, yr], color=GRID, lw=0.4, z=1)
            draw_row(cv, a, HX[1], yr, r, metrics)
            yr += PITCH
        ybot = max(yl, yr)
        # axes: grid lines, ticks and labels per half
        for hx in HX:
            for pct in (0, 50, 100):
                cv.line([ax_x(hx, pct)] * 2, [ytop, ybot], color=GRID, lw=0.4, z=0)
                cv.line([ax_x(hx, pct)] * 2, [ybot, ybot + 0.8], color=INK, lw=0.5)
                cv.text(ax_x(hx, pct), ybot + 2.2, str(pct), ha="center")
        cv.line([1.0, W - 1.0], [ybot, ybot], color=INK, lw=0.5)
        cv.line([HX[0] + 86.4, HX[0] + 86.4], [ytop, ybot], color=GRID, lw=0.4, z=0)
        y = ybot + 4.8
        # notes
        e5 = item_est(a, "f5|yes", "claude"), item_est(a, "f5|yes", "codex")
        ew = item_est(a, "perturbation|wording", "claude"), item_est(a, "perturbation|wording", "codex")
        disc_codex = e5[1]["k"] != ew[1]["k"]
        disc_claude = e5[0]["k"] != ew[0]["k"]
        metrics["f5_wording"] = dict(claude_f5=e5[0]["k"], claude_wording=ew[0]["k"], codex_f5=e5[1]["k"],
                                     codex_wording=ew[1]["k"], codex_n=e5[1]["n"], claude_n=e5[0]["n"],
                                     discrepancy_codex=disc_codex, discrepancy_claude=disc_claude)
        if disc_codex or disc_claude:
            note = (f"‡ Unresolved: the second coder codes f5 for {e5[1]['k']} of {e5[1]['n']} studies but wording for {ew[1]['k']} of "
                    f"{ew[1]['n']} (primary coder {e5[0]['k']} and {ew[0]['k']} of {e5[0]['n']}); pending adjudication.")
        else:
            note = (f"‡ f5 and perturbation/wording agree within each coder in this run ({e5[0]['k']} of {e5[0]['n']} "
                    f"primary coder, {e5[1]['k']} of {e5[1]['n']} second coder).")
        y = cv.wrap(note, 1.0, y, W - 2.0, bold=False)
        note2 = ("Scheme components: E estimand, 1 procedure, 2 respondent specification, 3 language, 4 sampling, "
                 "5 model identity, 6 item provenance, 7 scoring, 8 comparator, C claim. Rows follow the scheme, "
                 "not the values. κ: Cohen's kappa between coders.")
        y = cv.wrap(note2, 1.0, y, W - 2.0)
        yA_end = y + 0.4
        # ---------------- panel B
        yB = yA_end + 1.6
        cv.line([0, W], [yB, yB], color=INK, lw=1.2)
        yB += 1.6
        n_models, cells = len(p.models), p.cells
        y = panel_header(cv, yB, "B", f"Pilot: {n_models} open models, fixed cells (descriptive)",
                         "separate evidence class: own preregistered rules, E4")
        y += 1.6
        a1 = p.a1
        N = p.n_grids
        cnt = lambda col, val: sum(1 for r in a1 if r[col] == val)  # noqa: E731
        n_fr, n_st = cnt("rule_outcome", "fragile"), cnt("rule_outcome", "stable")
        n_neither = N - n_fr - n_st
        n_sign = sum(1 for r in a1 if truthy(r["sign_agrees_with_human"]))
        n_above = cnt("spread_vs_human", "larger")
        n_below = cnt("spread_vs_human", "smaller")
        n_over = N - n_above - n_below
        assert all(r["spread_vs_human"] in ("larger", "smaller") or r["spread_vs_human"].startswith("no statement") for r in a1)
        metrics["pilot_counts"] = dict(grids=N, fragile=n_fr, stable=n_st, neither=n_neither, sign_match=n_sign,
                                       above=n_above, overlap=n_over, below=n_below)
        # calibration: paradigms in which a prompt-invariant human-like model is labelled fragile more often than not
        calib_par = sorted(par for par, v in p.calib.items() if v >= 0.5)
        n_cal = sum(1 for r in a1 if r["paradigm"] in calib_par and r["rule_outcome"] == "fragile")
        n_cal_grids = sum(1 for r in a1 if r["paradigm"] in calib_par)
        assert n_cal == n_cal_grids, "a calibrated paradigm has a grid that is not fragile"
        pct = lambda v: f"{100 * v:.1f}"  # noqa: E731
        other_max = max(v for par, v in p.calib.items() if par not in calib_par)
        calib_txt = ", ".join(f"{par} {pct(p.calib[par])}" for par in calib_par)
        metrics["rule_calibration"] = dict(paradigms=calib_par, p_fragile={par: p.calib[par] for par in calib_par},
                                           grids_marked=n_cal, n_per_arm=p.calib_n, reps=p.calib_reps,
                                           p_fragile_other={par: v for par, v in p.calib.items() if par not in calib_par})
        # placement counts: assert the stored sensitivity run reproduces the table_a1 counts and the nd-free subset
        nd0 = [r for r in a1 if int(float(r["nd_n_flagged"])) == 0]
        pa, pn = p.place_all, p.place_nd
        assert (pa["n_grids"], pa["larger"], pa["overlap"], pa["smaller"]) == (N, n_above, n_over, n_below), "placement run != table_a1"
        assert pn["n_grids"] == len(nd0), "grids without near-deterministic cells differ between runs"
        assert pn["larger"] == sum(1 for r in nd0 if r["spread_vs_human"] == "larger")
        assert pn["smaller"] == sum(1 for r in nd0 if r["spread_vs_human"] == "smaller")
        metrics["pilot_counts"].update(placement_all=pa, placement_without_nd=pn)
        # left: three strips
        bx0, bw = 1.0, 70.0
        yb = y
        BH = 4.0

        def strip(yb, segs, label=None):
            """One stacked strip. segs: (n, name, fc, hatch, inside); returns the y below it."""
            if label:
                cv.text(bx0, yb + 1.2, label)
                yb += 2.9
            x = bx0
            tot = sum(sg[0] for sg in segs)
            outside = []
            for n, name, fc, hatch, inside in segs:
                w = bw * n / tot
                cv.rect(x, yb, w, BH, fc=fc, ec=INK, lw=0.5, hatch=hatch, z=2)
                lab = f"{name} {n}" if inside is None else inside
                if n > 0 and cv.width(lab) < w - 1.0:
                    if hatch:
                        tw = cv.width(lab)
                        cv.rect(x + w / 2 - tw / 2 - 0.5, yb + 0.7, tw + 1.0, BH - 1.4, fc="white", z=6)
                    cv.text(x + w / 2, yb + BH / 2 + 0.1, lab, ha="center", color="white" if fc == DARK else INK, z=7)
                elif n > 0:
                    outside.append(f"{name} {n}")
                x += w
            if outside:
                cv.text(bx0 + bw + 1.2, yb + BH / 2 + 0.1, "; ".join(outside), ha="left")
            return yb + BH + 1.5

        cv.text(bx0, yb + 1.2, f"Preregistered rule outcome ({N} grids)")
        yb += 2.9
        yb = strip(yb, [(n_fr - n_cal, "fragile", DARK, None, None), (n_cal, "", MID, "////", f"{n_cal}"),
                        (n_st, "stable", LIGHT, None, None)] + ([(n_neither, "neither", MID, None, None)] if n_neither else []))
        other_txt = "below 0.1" if other_max * 100 < 0.1 else f"at most {pct(other_max)}"
        yb = cv.wrap(f"Hatched: {'/'.join(calib_par)} grids ({n_cal}), fragile at {p.calib_n} responses per arm without prompt "
                     f"spread: a prompt-invariant model with the human effect is labelled fragile in {calib_txt} percent of "
                     f"{p.calib_reps} replicates (other paradigms {other_txt}).",
                     bx0, yb + 0.6, 88.0, pitch=2.95) + 0.5
        cv.text(bx0, yb + 1.2, f"Point sign of the mean effect against the human sign ({N} grids)")
        yb += 2.9
        yb = strip(yb, [(n_sign, "same sign", DARK, None, None), (N - n_sign, "opposite", LIGHT, None, None)])
        cv.text(bx0, yb + 1.2, "Prompt-spread interval against human between-site interval")
        yb += 2.9
        yb = strip(yb, [(pa["larger"], "above", DARK, None, None), (pa["overlap"], "overlap", MID, None, None),
                        (pa["smaller"], "below", LIGHT, None, None)], label=f"all grids ({pa['n_grids']})")
        yb = strip(yb, [(pn["larger"], "above", DARK, None, None), (pn["overlap"], "overlap", MID, None, None),
                        (pn["smaller"], "below", LIGHT, None, None)],
                   label=f"grids without near-deterministic cells ({pn['n_grids']})")
        yb_left_end = yb
        # right: status of the factor shares, then dot plot for the grids without near-deterministic cells
        rx0, rw = 92.0, 80.0
        rep = [r for r in a1 if truthy(r["shares_reportable"])]
        nd_free = [r for r in rep if int(float(r["nd_n_flagged"])) == 0]
        nd = [r for r in rep if int(float(r["nd_n_flagged"])) > 0]
        n_norep = N - len(rep)
        metrics["pilot_counts"].update(shares_reportable=len(rep), without_nd=len(nd_free), with_nd=len(nd), not_reportable=n_norep)
        yr = y
        cv.text(rx0, yr + 1.4, f"Grids by status of the factor shares ({N} grids, preregistered scale)")
        yr += 4.2
        x = rx0
        segs = [(len(nd_free), "5", "white", None), (len(nd), "near-deterministic cells", LIGHT, "////"),
                (n_norep, "no shares", MID, None)]
        seg_x = []
        for (n, name, fc, hatch), real in zip(segs, (len(nd_free), len(nd), n_norep)):
            w = rw * n / N
            cv.rect(x, yr, w, 4.4, fc=fc, ec=INK, lw=0.5, hatch=hatch, z=2)
            lab = f"{n}" if n == len(nd_free) else f"{n}  {name}"
            if n != len(nd_free):
                tw = cv.width(lab)
                cv.rect(x + w / 2 - tw / 2 - 0.6, yr + 0.9, tw + 1.2, 2.6, fc="white", z=6)
            cv.text(x + w / 2, yr + 2.3, lab if n != len(nd_free) else str(n), ha="center", z=7)
            seg_x.append(x)
            x += w
        yr += 4.4
        cv.text(seg_x[1] + 0.3, yr + 1.9, "standardised shares not interpretable in these grids", ha="left")
        cv.text(rx0, yr + 5.3, "shares drawn below", ha="left")
        cv.text(rx0 + rw, yr + 5.3, "lower bound of S² not above 0", ha="right")
        yr += 7.6
        # dot plot
        vt = [r for r in p.terms if r["scale"] == "A1_preregistered"]
        grids = [(r["model"], r["paradigm"]) for r in nd_free]
        TERMS = [("W", "o", True), ("F", "s", False), ("T", "^", True), ("O", "D", False)]
        rows_dp = []
        for (m, par) in grids:
            sub = [t for t in vt if t["model"] == m and t["paradigm"] == par]
            share = {t["term"]: fnum(t["share"]) for t in sub}
            inter = sum(v for k2, v in share.items() if ":" in k2 and not isnan(v))
            tot = sum(v for v in share.values() if not isnan(v))
            metrics.setdefault("shares_sum_check", []).append(round(tot, 4))
            rows_dp.append((m, par, share, inter))
        vals = [v for (_, _, s, i) in rows_dp for v in list(s.values()) + [i] if not isnan(v)]
        xlo = min(-0.1, math.floor(min(vals) * 10) / 10) if vals else -0.1
        xhi = max(1.0, math.ceil(max(vals) * 10) / 10) if vals else 1.0
        lab_w = 25.0
        dx0, dx1 = rx0 + lab_w, rx0 + rw - 1.0

        def sx(v):
            return dx0 + (dx1 - dx0) * (v - xlo) / (xhi - xlo)

        yr += 0.4
        ydp0 = yr
        for i, (m, par, share, inter) in enumerate(rows_dp):
            if i:
                cv.line([rx0, dx1], [yr + i * 3.1 + 0.1, yr + i * 3.1 + 0.1], color=GRID, lw=0.35, z=0)
            cy = yr + 1.8 + i * 3.1
            cv.text(rx0, cy, f"{m.replace('-instruct', '').replace('-3.3', '')} {par}")
            offs = {"W": -0.9, "F": -0.45, "T": 0.0, "O": 0.45, "I": 0.9}
            for tname, mk, filled in TERMS:
                v = share.get(tname, float("nan"))
                if isnan(v):
                    continue
                cv.marker(sx(v), cy + offs[tname], mk, 3.0, INK if filled else "white", INK, 0.6)
            if not isnan(inter):
                cv.marker(sx(inter), cy + offs["I"], "P", 3.0, INK, "white", 0.3)
        ydp1 = yr + 1.8 + len(rows_dp) * 3.1 - 0.9
        if not rows_dp:
            cv.text(rx0 + lab_w, yr + 3.0, "no grid without near-deterministic cells", italic=True)
            ydp1 = yr + 6.0
        zero_x = sx(0.0)
        cv.line([zero_x, zero_x], [ydp0, ydp1], color=GRID, lw=0.5, z=1)
        cv.line([dx0, dx1], [ydp1, ydp1], color=INK, lw=0.5)
        tick = np.arange(math.ceil(xlo * 5) / 5, xhi + 1e-9, 0.2)
        for tv in tick:
            cv.line([sx(tv)] * 2, [ydp0, ydp1], color=GRID, lw=0.35, z=0)
            cv.line([sx(tv)] * 2, [ydp1, ydp1 + 0.8], color=INK, lw=0.5)
            cv.text(sx(tv), ydp1 + 2.3, f"{tv:.1f}", ha="center")
        cv.text(dx0 - 1.0, ydp1 + 2.3, "share of corrected SS", ha="right")
        yr = ydp1 + 4.2
        # term key
        kx = rx0
        present = {t for (_, _, sh, _i) in rows_dp for t, v in sh.items() if not isnan(v)}
        metrics["terms_drawn"] = sorted(present & {"W", "F", "T", "O"})
        for tname, mk, filled in [t for t in TERMS if t[0] in present] + [("interactions", "P", True)]:
            nm = {"W": "wording", "F": "format", "T": "temperature", "O": "order", "interactions": "interactions"}[tname]
            cv.marker(kx + 1.0, yr + 0.9, mk, 2.7 if mk != "P" else 3.0, INK if filled else "white", INK, 0.6)
            cv.text(kx + 2.6, yr + 0.9, nm)
            kx += 2.6 + cv.width(nm) + 2.4
        yr += 4.2
        yr = cv.wrap("Different sources: prompt changes over fixed cells, and site and sample differences among human "
                     "samples. Placement only; no ratio, and neither system is shown to be more variable.",
                     rx0, yr, 80.0, pitch=2.95)
        yB_body_end = max(yb_left_end, yr)
        y = yB_body_end + 0.2
        quant = p.quant
        foot = ("Descriptive over the enumerated cells (" + " or ".join(str(c) for c in cells) +
                " per grid). Shares are corrected sums of squares over purposive fixed cells, not variance components; "
                "no facet ranking is implied.")
        nf4 = sorted(m for m, q in quant.items() if q.startswith("nf4"))
        if quant and len(nf4):
            foot += f" Model size is confounded with precision: {len(nf4)} of {n_models} models ran from 4-bit NF4 checkpoints."
            metrics["nf4_models"] = nf4
        y = cv.wrap(foot, 1.0, y + 1.2, W - 2.0)
        yB_end = y + 0.4
        # ---------------- panel C
        yC = yB_end + 1.6
        cv.line([0, W], [yC, yC], color=INK, lw=1.2)
        yC += 1.6
        y = panel_header(cv, yC, "C", "Proposals: reporting checklist (MR-12) and research agenda (R1 to R7)",
                         "not tested; support from the pilot factors only")
        y += 1.2
        # left: MR-12
        lx = 1.0
        SQ_X, OV_X = 66.0, 71.5
        cv.text(lx, y + 1.5, "MR-12 item (proposal)", bold=True)
        cv.text(SQ_X + 1.5, y + 1.5, "Pilot", ha="center", bold=True)
        cv.text(OV_X, y + 1.5, "Overlap", bold=True)
        cv.line([1.0, 92.0], [y + 3.2, y + 3.2], color=INK, lw=0.5)
        ym = y + 3.5
        for i, (lab, fac, ov) in enumerate(MR12):
            cy = ym + i * PITCH + PITCH / 2
            cv.text(lx, cy, f"{i + 1}", bold=True)
            cv.text(lx + 4.2, cy, lab)
            if fac:
                cv.rect(SQ_X, cy - 1.35, 3.0, 2.7, fc=INK, z=2)
                cv.text(SQ_X + 1.5, cy + 0.05, fac, ha="center", color="white", z=7, size=FS, bold=True)
            else:
                cv.rect(SQ_X, cy - 1.35, 3.0, 2.7, fc="white", ec=INK, lw=0.7, z=2)
            cv.text(OV_X, cy, ov if ov else "–")
        ym_end = ym + len(MR12) * PITCH
        # right: roadmap matrix
        rx = 96.0
        MX0, MCW = 136.0, 3.7
        cv.text(rx, y + 1.5, "Agenda item", bold=True)
        for j, comp in enumerate(COMPONENTS):
            cv.text(MX0 + j * MCW + MCW / 2, y + 1.5, comp, ha="center", bold=True)
        cv.line([rx, W - 1.0], [y + 3.2, y + 3.2], color=INK, lw=0.5)
        for i, (code, lab, comps) in enumerate(ROADMAP):
            cy = ym + i * PITCH + PITCH / 2
            cv.text(rx, cy, code, bold=True)
            cv.text(rx + 5.2, cy, lab)
            for j, comp in enumerate(COMPONENTS):
                cx = MX0 + j * MCW + MCW / 2
                if comp in comps:
                    cv.marker(cx, cy, "o", 3.0, INK if code != "R7" else "white", INK, 0.7)
        yk = ym + len(ROADMAP) * PITCH + 1.0
        yk = cv.wrap("Dots: scheme components (codes of panel A) an agenda item addresses, by the authors' mapping; "
                     "R7 (open dots) tests the scheme as a whole.", rx, yk + 0.8, W - 1.0 - rx)
        yk += 1.0
        cv.text(rx, yk + 1.0, "Pilot square:", bold=True)
        wq = cv.width("Pilot square:", bold=True)
        cv.rect(rx + wq + 1.2, yk - 0.35, 3.0, 2.7, fc=INK, z=2)
        cv.text(rx + wq + 5.2, yk + 1.0, "factor varied in the pilot (W, F, O, T)")
        xq = rx + wq + 5.2 + cv.width("factor varied in the pilot (W, F, O, T)") + 2.5
        cv.rect(xq, yk - 0.35, 3.0, 2.7, fc="white", ec=INK, lw=0.7, z=2)
        cv.text(xq + 4.0, yk + 1.0, "none")
        yk += 4.6
        ov_txt = "Overlap letters, any coverage of part of the item: " + "; ".join(f"{l} {n}" for l, n in OVERLAP_KEY) + "."
        yk = cv.wrap(ov_txt, rx, yk, W - 1.0 - rx)
        y = max(ym_end, yk) + 0.6
        y = cv.wrap("MR-12: consensus-style proposal informed by the audit, not validated, not ranked. "
                    "R1 to R7: open problems with planned designs, not results.", 1.0, y + 0.8, W - 2.0)
        Hfinal = y + 0.4
        if attempt == 0:
            H0 = Hfinal
            plt.close(cv.fig)
            metrics.update(rows=[], bounds_drawn=0, not_coded=[], agree_rows={})
            continue
    log(f"canvas {W:.0f} x {Hfinal:.1f} mm (limit {MAX_H:.0f})")
    if abs(Hfinal - H0) > 0.01:
        log(f"warning: height changed between passes ({H0:.2f} -> {Hfinal:.2f})")
    return cv, Hfinal, metrics, dict(n_c=n_c, n_x=n_x)


def min_font_pt(cv: Canvas) -> float:
    """Smallest font size (pt) of any text in the figure; the canvas is W mm wide, so this is the size at the final 174 mm width."""
    sizes = [t.get_fontsize() for t in cv.ax.texts if t.get_text().strip()]
    return min(sizes)


def save(cv: Canvas, stem: Path):
    from PIL import Image

    for ext in ("pdf", "eps"):
        cv.fig.savefig(stem.with_suffix("." + ext), format=ext)
    png = stem.with_suffix(".png")
    cv.fig.savefig(png, format="png", dpi=600)
    plt.close(cv.fig)
    Image.open(png).convert("RGB").save(png, dpi=(600, 600))


def caption(a: Audit, p: Pilot, metrics, ctx) -> str:
    rp = lambda q: q.relative_to(ROOT).as_posix() if ROOT in q.parents else q.as_posix()  # noqa: E731
    mr = metrics["rows"]
    varied = [r for r in mr if r["key"] and (r["key"].startswith("perturbation|") or r["key"] in
              ("f5|yes", "f6_applicable|yes", "f7|yes", "f8|yes", "f9|yes"))]
    his = [(r["label"], c, r[c]["hi"]) for r in varied for c in ("claude", "codex") if not isnan(r[c]["hi"])]
    top = max(his, key=lambda t: t[2])
    anyr = next(r for r in mr if r["key"] == "robustness_tested|yes")
    n_c, n_x = ctx["n_c"], ctx["n_x"]
    pc = metrics["pilot_counts"]
    rc, pa, pn = metrics["rule_calibration"], pc["placement_all"], pc["placement_without_nd"]
    f5 = metrics["f5_wording"]
    nf = len(metrics.get("nf4_models", []))
    if top[2] < 50:
        bh = [(r["label"], v[1]) for r in varied for v in (r.get("bound_values") or {}).values() if v]
        btxt = (f"; the bounds for the {n_c['unknown']} records of unknown status are much wider, up to "
                f"{r1(max(b[1] for b in bh))} percent for a single facet") if bh else ""
        claim = (f"In both codings the upper 95 percent limit of the share of eligible studies that varied a single facet is "
                 f"below 50 percent (largest {r1(top[2])} percent, {top[0].lower()}, {top[1].title()} coding), whereas the summary "
                 f"row, any of six judged types, has estimates of {r1(anyr['claude']['est'])} percent (Claude) and "
                 f"{r1(anyr['codex']['est'])} percent (Codex){btxt}")
    else:
        claim = (f"The largest upper 95 percent limit among single facets listed as varied is {r1(top[2])} percent "
                 f"({top[0].lower()}, {top[1].title()} coding)")
    nf_txt = f" {nf} of {len(p.models)} models ran from 4-bit checkpoints, so model size is confounded with numeric precision." if nf else ""
    return (
        f"**Fig. 14** (DRAFT, INTERIM; appended 2026-10-17) Which measurement facets the audited studies varied or stated, what the pilot "
        f"shows over its fixed cells, and the proposed checklist and research agenda. (a) Interim literature audit of {n_c['eligible']} "
        f"(Claude coding) and {n_x['eligible']} (Codex coding) eligible studies of {n_c['analysed']} analysed: design-weighted share of "
        f"eligible studies with 95 percent design-based intervals, Claude (circles) and Codex (squares) side by side, rows in scheme order "
        f"and not sorted by value. {claim}. Grey tails are bounds that treat the {n_c['unknown']} analysed records of unknown status as "
        f"all eligible or all ineligible, drawn where the nonresponse analysis lists them. Hatched rows are fields that fail the "
        f"full-sample agreement rule (kappa below 0.6, or agreement below 80 percent where a category has fewer than 5 records) and "
        f"dotted rows pass on percent agreement with kappa below 0.6, so the gap between coders there is a coder-sensitivity display and "
        f"not an interval; fields marked not coded have no extraction. "
        f"Unresolved discrepancy: in the Codex coding paraphrases compared (f5) is {f5['codex_f5']} of {f5['codex_n']} studies but wording "
        f"varied is {f5['codex_wording']} of {f5['codex_n']} (Claude {f5['claude_f5']} and {f5['claude_wording']} of {f5['claude_n']}); "
        f"it awaits adjudication. (b) Pilot of {len(p.models)} open models in {pc['grids']} model-by-paradigm grids, described over the "
        f"enumerated cells: {pc['fragile']} grids fragile and {pc['stable']} stable under the preregistered rule, of which the "
        f"{rc['grids_marked']} {'/'.join(rc['paradigms'])} grids (hatched) are fragile at {rc['n_per_arm']} responses per arm even "
        f"without prompt spread (a prompt-invariant model with the human effect is labelled fragile in "
        f"{', '.join(f'{k} {100 * v:.1f}' for k, v in rc['p_fragile'].items())} percent of {rc['reps']} simulated replicates); the point "
        f"sign matches the human sign in {pc['sign_match']}; the prompt-spread interval lies above the human between-site interval "
        f"in {pa['larger']} of {pa['n_grids']} grids, overlaps it in {pa['overlap']} and lies below in {pa['smaller']}, and in the "
        f"{pn['n_grids']} grids without near-deterministic cells in {pn['larger']}, {pn['overlap']} and {pn['smaller']}; these compare prompt changes over fixed "
        f"cells with site and sample differences, so no ratio is formed and neither system is shown to be more variable. Factor shares "
        f"(corrected sums of squares, not variance components) are drawn only for the {pc['without_nd']} grids with no near-deterministic "
        f"cell; the {pc['with_nd']} grids with such cells are not interpretable and {pc['not_reportable']} grids have no reportable shares. "
        f"No facet ranking is implied.{nf_txt} (c) Items of the proposed reporting checklist MR-12 (filled square: a factor varied in "
        f"the pilot; letters: frameworks covering part of the item) and the research agenda R1 to R7 with the scheme components each "
        f"addresses; both are proposals and agendas, not tests. [{rp(a.paths['items'].parent.parent)}, "
        f"{rp(p.paths[0].parent)}; analysis/fig14_framework.py]"
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("input_dir", nargs="?", default="runs/rq234-interim")
    ap.add_argument("--pilot-dir", default="runs/pilot-side-by-side")
    ap.add_argument("--pilot-runs", default="runs/pilot")
    ap.add_argument("--calib-dir", default="runs/pilot-rule-calibration")
    ap.add_argument("--placement-dir", default="runs/pilot-placement-sensitivity")
    ap.add_argument("--out-dir", default="paper/figures")
    ap.add_argument("--log-dir", default="runs/fig14")
    args = ap.parse_args()
    rel = lambda s: (Path(s) if Path(s).is_absolute() else ROOT / s)  # noqa: E731
    ind, pd_, pr, outd, logd = map(rel, (args.input_dir, args.pilot_dir, args.pilot_runs, args.out_dir, args.log_dir))
    outd.mkdir(parents=True, exist_ok=True)
    logd.mkdir(parents=True, exist_ok=True)
    fam = setup_fonts()
    log(f"font {fam}; inputs {ind} | {pd_} | {pr}")
    a, p = Audit(ind), Pilot(pd_, pr, rel(args.calib_dir), rel(args.placement_dir))
    cv, H, metrics, ctx = build(a, p, outd, logd)
    if H > MAX_H:
        log(f"ERROR: height {H:.1f} mm exceeds {MAX_H} mm")
    mf = min_font_pt(cv)
    log(f"smallest text {mf:.2f} pt at {W:.0f} mm width")
    if mf < 7.0:
        raise SystemExit(f"text below 7 pt: {mf}")
    metrics["min_font_pt"] = mf
    save(cv, outd / "Fig14")
    cap = caption(a, p, metrics, ctx)
    (logd / "caption_draft.md").write_text(cap + "\n", encoding="utf-8")
    ins = {str(path.relative_to(ROOT)) if ROOT in path.parents else str(path): sha(path)
           for path in list(a.paths.values()) + p.paths}
    metrics.update(height_mm=round(H, 2), width_mm=W, run=a.run, interim=a.interim, font=fam, inputs_sha256=ins,
                   n_rows_data=len(metrics["rows"]))
    (logd / "metrics.json").write_text(json.dumps(metrics, indent=1, default=str), encoding="utf-8")
    (logd / "fig14.log").write_text("\n".join(LOG) + "\n", encoding="utf-8")
    log(f"wrote {outd / 'Fig14.pdf'} (+ .eps, .png); caption draft {logd / 'caption_draft.md'}")


if __name__ == "__main__":
    main()

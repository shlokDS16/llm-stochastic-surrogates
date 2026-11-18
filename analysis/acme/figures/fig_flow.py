"""Fig 2 (key `flow`): PRISMA 2020 flow diagram of the review (records, screening passes, the stratified full-text sample, eligible studies).

Every count printed in the image is read from files; none is typed here:
  research/protocol/prisma-counts.json   identification by block, duplicates, title and abstract stages, full_text_input
  data/processed/prisma-fulltext.json    full-text stage of the analysed set (sought, not retrievable, assessed, exclusion reasons, included)
  runs/rq1-fig1-prisma/counts.json       the run that fixes the counts used in the text (rule, frame, flags, sample, second-pass included)
  research/protocol/search-log.md        search dates, date limits and the arXiv submission window (run S2)
Two counts are differences of read counts and are marked derived in the .source.json: frame records not drawn (frame minus draw) and
drawn records outside the analysed set (draw minus analysed).

Cross-check (reported, never repaired): every count that the text prints through a \\NUM{rm.*} key (paper/acme/autonumbers.tex) is compared
with the value drawn; the files are compared with each other; the PRISMA arithmetic (identified minus duplicates is screened, and so on) is
tested.  Mismatches are printed, written to the .source.json under "crosscheck" and make the exit status 2 with --strict; the figure
always shows the value read from the run directory.

Output: paper/acme/figures/fig-flow.pdf (vector, fonts embedded) and fig-flow.png (600 dpi), each with a .source.json beside it.
The float is a figure* (text width 16.0 cm; 7 pt type).

Run from the project root:  .venv/Scripts/python.exe -I analysis/acme/figures/fig_flow.py
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import results_common as rc  # noqa: E402

ROOT = rc.ROOT
PC = ROOT / "research" / "protocol" / "prisma-counts.json"
FT = ROOT / "data" / "processed" / "prisma-fulltext.json"
RUN_DIR = ROOT / "runs" / "rq1-fig1-prisma"
RUN = RUN_DIR / "counts.json"
LOG = ROOT / "research" / "protocol" / "search-log.md"
AUTO = ROOT / "paper" / "acme" / "autonumbers.tex"

# Reasons for exclusion at full text: JSON key -> label in the figure.  The key set is asserted equal to the file's, so a new reason fails loudly.
REASON_LABEL = {
    "benchmark-only": "Benchmark only",
    "other": "Other reason",
    "not-llm": "Not a language model",
    "neural-only": "Neural data only",
    "abstract-only (E5; pending human confirmation)": "Abstract only",
    "not-english": "Not in English",
    "questionnaire-only": "Questionnaire only",
}

# ----------------------------------------------------------------------------------------------------------------- style
CM = rc.CM
W_CM = rc.TEXT_WIDTH_CM
FS = 8.0   # Springer: 8 to 12 pt at final size (16.0 cm wide, printed at 100 percent)
LH = FS * 1.26 / 72 / CM          # line height in cm
PAD = 0.14                        # box padding in cm
INK, GREY, LIGHT, PALE = "#222222", "#555555", "#DCDCDC", "#F2F2F2"
BLUE, BLUE_T = "#0072B2", "#E4F0F8"


def style():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "font.family": "sans-serif", "font.sans-serif": ["Arial", "DejaVu Sans"], "font.size": FS, "axes.linewidth": 0.6,
        "pdf.fonttype": 42, "ps.fonttype": 42, "savefig.dpi": 600, "pdf.compression": 6,
    })
    return plt


# ----------------------------------------------------------------------------------------------------------------- inputs
def num_value(s: str):
    s = s.strip().replace(",", "")
    words = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
             "eleven": 11, "twelve": 12}
    if s in words:
        return words[s]
    try:
        return int(s)
    except ValueError:
        return s


def read_autonumbers(tr: rc.Tracker) -> dict[str, object]:
    txt = tr.add(AUTO).read_text(encoding="utf-8")
    return {m.group(1): num_value(m.group(2)) for m in re.finditer(r"\\csname NUM:(rm\.\w+)\\endcsname\{([^}]*)\}", txt)}


def search_facts(tr: rc.Tracker) -> dict[str, str]:
    """Dates and windows of run S2, read from the search log."""
    txt = tr.add(LOG).read_text(encoding="utf-8")
    oa = re.search(r"## OpenAlex run S2.*?\((\d{4}-\d{2}-\d{2})T[\d:]+\)", txt)
    ax = re.search(r"## arXiv run S2 \((\d{4}-\d{2}-\d{2})T[\d:]+\)", txt)
    frm = re.search(r"## OpenAlex run S2.*?from_publication_date:(\d{4}-\d{2}-\d{2})", txt, re.S)
    win = re.search(r"## arXiv run S2.*?submittedDate:\[(\d{8})\d{4} TO (\d{8})\d{4}\]", txt, re.S)
    assert oa and ax and frm and win, "search-log.md: run S2 headings or date limits not found"
    iso = lambda d: f"{d[:4]}-{d[4:6]}-{d[6:]}"  # noqa: E731
    return {"openalex_date": oa.group(1), "arxiv_date": ax.group(1), "openalex_from": frm.group(1),
            "arxiv_from": iso(win.group(1)), "arxiv_to": iso(win.group(2))}


def fmt(n: int) -> str:
    return f"{n:,}"


class Counts:
    """All drawn numbers with their provenance; cross-check list."""

    def __init__(self, tr: rc.Tracker) -> None:
        self.pc, self.ft, self.run = tr.json(PC), tr.json(FT), tr.json(RUN)
        self.num = read_autonumbers(tr)
        self.facts = search_facts(tr)
        self.prov: dict[str, str] = {}
        self.issues: list[str] = []
        self.checks_done = 0
        r, p, f = self.run, self.pc, self.ft
        self.v: dict[str, int] = {}

        def put(name: str, val: int, src: str) -> None:
            self.v[name] = int(val)
            self.prov[name] = src

        put("openalex", r["openalex_total"], "runs/rq1-fig1-prisma/counts.json#openalex_total")
        put("arxiv", r["arxiv"], "runs/rq1-fig1-prisma/counts.json#arxiv")
        put("identified", r["identified_total"], "runs/rq1-fig1-prisma/counts.json#identified_total")
        put("dup", r["duplicates_removed"], "runs/rq1-fig1-prisma/counts.json#duplicates_removed")
        put("unique", r["unique"], "runs/rq1-fig1-prisma/counts.json#unique")
        put("title_ex", r["title_excluded"], "runs/rq1-fig1-prisma/counts.json#title_excluded")
        put("stage2", r["stage2"], "runs/rq1-fig1-prisma/counts.json#stage2")
        put("abs_ex", r["abstract_both_exclude"], "runs/rq1-fig1-prisma/counts.json#abstract_both_exclude")
        put("both_inc", r["both_include"], "runs/rq1-fig1-prisma/counts.json#both_include")
        put("split", r["disagree_or_maybe"], "runs/rq1-fig1-prisma/counts.json#disagree_or_maybe")
        put("ft_input", p["full_text_input"], "research/protocol/prisma-counts.json#full_text_input")
        put("tb_ex", r["tiebreak_excluded"], "runs/rq1-fig1-prisma/counts.json#tiebreak_excluded")
        put("liberal", r["liberal_eligible"], "runs/rq1-fig1-prisma/counts.json#liberal_eligible")
        put("strict", r["strict_eligible"], "runs/rq1-fig1-prisma/counts.json#strict_eligible")
        put("flag_yes", r["flag"]["yes"], "runs/rq1-fig1-prisma/counts.json#flag.yes")
        put("flag_unc", r["flag"]["unclear"], "runs/rq1-fig1-prisma/counts.json#flag.unclear")
        put("flag_no", r["flag"]["no"], "runs/rq1-fig1-prisma/counts.json#flag.no")
        put("drawn", r["sample_drawn"], "runs/rq1-fig1-prisma/counts.json#sample_drawn")
        put("analysed", r["sample_analysed"], "runs/rq1-fig1-prisma/counts.json#sample_analysed")
        put("sought", f["fulltext_sought"], "data/processed/prisma-fulltext.json#fulltext_sought")
        put("no_ft", f["fulltext_not_retrievable"], "data/processed/prisma-fulltext.json#fulltext_not_retrievable")
        put("assessed", f["fulltext_assessed"], "data/processed/prisma-fulltext.json#fulltext_assessed")
        put("ft_ex", f["excluded_fulltext_total"], "data/processed/prisma-fulltext.json#excluded_fulltext_total")
        put("incl1", f["included_rq2_rq4"], "data/processed/prisma-fulltext.json#included_rq2_rq4")
        put("incl2", r["fulltext_second_coding_included"], "runs/rq1-fig1-prisma/counts.json#fulltext_second_coding_included")
        self.reasons: dict[str, int] = dict(f["excluded_fulltext_reasons"])
        assert set(self.reasons) == set(REASON_LABEL), f"exclusion reasons changed: {set(self.reasons) ^ set(REASON_LABEL)}"
        # derived (differences of read counts)
        put("not_drawn", self.v["liberal"] - self.v["drawn"], "derived: liberal_eligible - sample_drawn")
        put("drawn_unread", self.v["drawn"] - self.v["analysed"], "derived: sample_drawn - sample_analysed")
        self.openalex_blocks = dict(sorted(r["openalex_by_block"].items(), key=lambda kv: int(kv[0][1:])))
        self._crosscheck()

    # ------------------------------------------------------------------------------------------------ cross-checks
    def _eq(self, label: str, a, b, where: str) -> None:
        self.checks_done += 1
        if a != b:
            self.issues.append(f"MISMATCH {label}: {where[0]}={a!r} vs {where[1]}={b!r}")

    def _crosscheck(self) -> None:
        v, r, p, f = self.v, self.run, self.pc, self.ft
        # text keys (paper/acme/autonumbers.tex) against the drawn values
        keymap = {"nIdent": "identified", "nOpenalex": "openalex", "nArxiv": "arxiv", "nDup": "dup", "nUnique": "unique",
                  "nTitleExcl": "title_ex", "nStage2": "stage2", "nAbsExcl": "abs_ex", "nBothIncl": "both_inc", "nSplit": "split",
                  "nFtCand": "ft_input", "nLiberalExcl": "tb_ex", "nLiberal": "liberal", "nStrict": "strict", "nFlagYes": "flag_yes",
                  "nFlagUnclear": "flag_unc", "nFlagNo": "flag_no", "nDrawn": "drawn", "nAnalysed": "analysed", "nFT": "assessed",
                  "nNoFT": "no_ft", "nFTExcl": "ft_ex", "nElig1": "incl1", "nElig2": "incl2"}
        for k, name in keymap.items():
            key = f"rm.{k}"
            if key not in self.num:
                self.issues.append(f"NO TEXT KEY rm.{k} in autonumbers.tex (drawn {name}={v[name]})")
                continue
            self._eq(f"text key {key}", self.num[key], v[name], (f"autonumbers.tex {key}", f"drawn {name}"))
        # files against each other
        self._eq("duplicates", p["duplicates_removed"], r["duplicates_removed"], ("prisma-counts.json", "counts.json"))
        self._eq("unique", p["unique"], r["unique"], ("prisma-counts.json", "counts.json"))
        self._eq("title excluded", p["screening_title"]["excluded"], r["title_excluded"], ("prisma-counts.json", "counts.json"))
        self._eq("stage 2", p["screening_title"]["to_stage2"], r["stage2"], ("prisma-counts.json", "counts.json"))
        self._eq("abstract screened", p["screening_abstract"]["screened"], r["stage2"], ("prisma-counts.json", "counts.json"))
        self._eq("abstract excluded", p["screening_abstract"]["excluded"], r["abstract_both_exclude"], ("prisma-counts.json", "counts.json"))
        self._eq("both include", p["screening_abstract"]["to_full_text_both_include"], r["both_include"], ("prisma-counts.json", "counts.json"))
        self._eq("split", p["screening_abstract"]["to_full_text_disagreement_or_maybe"], r["disagree_or_maybe"],
                 ("prisma-counts.json", "counts.json"))
        pcb = {k.split("-")[-1]: n for k, n in p["identified"].items() if k.startswith("openalex-S2-")}
        self._eq("OpenAlex blocks", pcb, r["openalex_by_block"], ("prisma-counts.json", "counts.json"))
        self._eq("arXiv", p["identified"]["arxiv-S2"], r["arxiv"], ("prisma-counts.json", "counts.json"))
        ftj = {k: v_ for k, v_ in r["fulltext"].items() if k in f and not k.startswith("_")}
        for k, val in ftj.items():
            self._eq(f"full-text field {k}", f[k], val, ("prisma-fulltext.json", "counts.json#fulltext"))
        # PRISMA arithmetic
        self._eq("blocks sum to OpenAlex total", sum(r["openalex_by_block"].values()), r["openalex_total"], ("sum of blocks", "openalex_total"))
        self._eq("OpenAlex + arXiv", r["openalex_total"] + r["arxiv"], r["identified_total"], ("sum", "identified_total"))
        self._eq("identified - duplicates", v["identified"] - v["dup"], v["unique"], ("difference", "unique"))
        self._eq("unique - title excluded", v["unique"] - v["title_ex"], v["stage2"], ("difference", "stage2"))
        self._eq("stage 2 - abstract excluded", v["stage2"] - v["abs_ex"], v["ft_input"], ("difference", "full_text_input"))
        self._eq("both include + split", v["both_inc"] + v["split"], v["ft_input"], ("sum", "full_text_input"))
        self._eq("rule input - tie-break excluded", v["ft_input"] - v["tb_ex"], v["liberal"], ("difference", "liberal_eligible"))
        self._eq("flags sum to frame", v["flag_yes"] + v["flag_unc"] + v["flag_no"], v["liberal"], ("sum of flags", "liberal_eligible"))
        self._eq("sought = analysed", v["sought"], v["analysed"], ("fulltext_sought", "sample_analysed"))
        self._eq("sought - not retrievable", v["sought"] - v["no_ft"], v["assessed"], ("difference", "fulltext_assessed"))
        self._eq("assessed - excluded", v["assessed"] - v["ft_ex"], v["incl1"], ("difference", "included first pass"))
        self._eq("reasons sum", sum(self.reasons.values()), v["ft_ex"], ("sum of reasons", "excluded total"))
        self._eq("pending", (f["fulltext_pending_assessment"], f["fulltext_unresolved_unclear"], f["interim"]), (0, 0, False),
                 ("prisma-fulltext.json", "expected final state"))


# ----------------------------------------------------------------------------------------------------------------- drawing
class Box:
    def __init__(self, key, lines, x, w, kind="main", align="center", cols=None):
        self.key, self.lines, self.x, self.w, self.kind, self.align, self.cols = key, lines, x, w, kind, align, cols
        n = len(lines) if cols is None else max(len(c) for c in cols) + len(lines)
        self.h = n * LH + 2 * PAD
        self.cy = None            # set by layout
        self.texts = []

    @property
    def top(self): return self.cy + self.h / 2
    @property
    def bot(self): return self.cy - self.h / 2
    @property
    def left(self): return self.x
    @property
    def right(self): return self.x + self.w
    @property
    def cx(self): return self.x + self.w / 2


def build(C: Counts):
    v, fa = C.v, C.facts
    n = lambda k: f"n = {fmt(v[k])}"  # noqa: E731
    MX, MW = 1.0, 7.8                  # main column x and width (cm)
    RX, RW = 9.2, W_CM - 9.2 - 0.12
    half = (MW - 0.25) / 2
    top_oa = Box("oa", ["Records from OpenAlex", (n("openalex"), 1), "ten sub-queries B1 to B10,", f"searched {fa['openalex_date']}"], MX, half, "main")
    top_ax = Box("ax", ["Records from arXiv", (n("arxiv"), 1), "abstracts submitted", f"{fa['arxiv_from']} to {fa['arxiv_to']}"], MX + half + 0.25, half, "main")
    main = [
        Box("ident", ["Records identified in both sources", (n("identified"), 1)], MX, MW),
        Box("title", ["Screened at the title stage by two independent passes", (n("unique"), 1)], MX, MW),
        Box("abs", ["Screened at the abstract stage by two independent passes", (n("stage2"), 1)], MX, MW),
        Box("rule", ["Not excluded by both passes", (n("ft_input"), 1),
                     f"both include {fmt(v['both_inc'])}; split or uncertain {fmt(v['split'])}"], MX, MW),
        Box("frame", ["Eligible records of the liberal frame", (n("liberal"), 1),
                      f"abstract flag: yes {fmt(v['flag_yes'])}, unclear {fmt(v['flag_unc'])}, no {fmt(v['flag_no'])};", f"strict rule {fmt(v['strict'])}"], MX, MW),
        Box("drawn", ["Stratified sample drawn", (n("drawn"), 1)], MX, MW),
        Box("sought", ["Analysed set, full text sought", (n("sought"), 1)], MX, MW),
        Box("assessed", ["Full texts assessed for eligibility", (n("assessed"), 1)], MX, MW),
        Box("incl", ["Eligible studies coded", (f"first coding pass: {n('incl1')}", 1), (f"second coding pass: {n('incl2')}", 1)], MX, MW, "final"),
    ]
    reasons = sorted(C.reasons.items(), key=lambda kv: (-kv[1], kv[0]))
    half_n = (len(reasons) + 1) // 2
    cols = [[(REASON_LABEL[k], c) for k, c in reasons[:half_n]], [(REASON_LABEL[k], c) for k, c in reasons[half_n:]]]
    excl = {
        "ident": Box("r_dup", ["Duplicates removed", (n("dup"), 1), "by DOI, then arXiv identifier, then title and year"], RX, RW, "excl", "left"),
        "title": Box("r_title", ["Excluded at the title stage", "(both passes exclude)", (n("title_ex"), 1)], RX, RW, "excl", "left"),
        "abs": Box("r_abs", ["Excluded at the abstract stage", "(both passes exclude)", (n("abs_ex"), 1)], RX, RW, "excl", "left"),
        "rule": Box("r_tb", ["Excluded by a third pass and the liberal rule", (n("tb_ex"), 1)], RX, RW, "excl", "left"),
        "frame": Box("r_nd", ["Frame records not drawn", (n("not_drawn"), 1)], RX, RW, "excl", "left"),
        "drawn": Box("r_unread", ["Drawn, outside the analysed set", (n("drawn_unread"), 1)], RX, RW, "excl", "left"),
        "sought": Box("r_noft", ["Full text not obtained", (n("no_ft"), 1), "treated as nonresponse and bounded"], RX, RW, "excl", "left"),
        "assessed": Box("r_ftex", ["Excluded at full text, by reason", (n("ft_ex"), 1)], RX, RW, "excl", "left", cols=cols),
    }
    return top_oa, top_ax, main, excl


def layout(top_oa, top_ax, main, excl):
    """Stack the boxes top down; open a gap wherever two neighbouring exclusion boxes (each centred in its gap) would touch."""
    GAP = 0.34
    top_oa.h = top_ax.h = max(top_oa.h, top_ax.h)
    top_oa.cy = top_ax.cy = -top_oa.h / 2
    y = top_oa.bot
    for b in main:
        b.cy = y - GAP - b.h / 2
        y = b.bot
    for _ in range(60):
        mids = [(i, (b.bot + main[i + 1].top) / 2, excl[b.key]) for i, b in enumerate(main[:-1]) if b.key in excl]
        for (i1, m1, r1), (_, m2, r2) in zip(mids, mids[1:]):
            need = (r1.h + r2.h) / 2 + 0.18
            if m1 - m2 < need - 1e-9:
                for j in range(i1 + 1, len(main)):
                    main[j].cy -= 2 * (need - (m1 - m2))
                break
        else:
            break
    for i, b in enumerate(main[:-1]):
        if b.key in excl:
            excl[b.key].cy = (b.bot + main[i + 1].top) / 2


def draw(C: Counts, plt):
    top_oa, top_ax, main, excl = build(C)
    layout(top_oa, top_ax, main, excl)
    all_boxes = [top_oa, top_ax] + main + list(excl.values())
    ymin = min(b.bot for b in all_boxes) - 0.15
    ymax = 0.15
    H = ymax - ymin
    fig = plt.figure(figsize=(W_CM * CM, H * CM))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W_CM)
    ax.set_ylim(ymin, ymax)
    ax.axis("off")
    from matplotlib.patches import FancyArrowPatch, Rectangle
    face = {"main": ("white", INK, 0.7), "excl": (PALE, GREY, 0.6), "final": (BLUE_T, BLUE, 0.9)}

    def box(b: Box):
        fc, ec, lw = face[b.kind]
        ax.add_patch(Rectangle((b.x, b.bot), b.w, b.h, facecolor=fc, edgecolor=ec, linewidth=lw, zorder=2))
        ytop = b.top - PAD
        for k, ln in enumerate(b.lines):
            txt, bold = (ln, 0) if isinstance(ln, str) else ln
            yy = ytop - (k + 0.5) * LH
            if b.align == "center":
                t = ax.text(b.cx, yy, txt, ha="center", va="center", fontsize=FS, fontweight="bold" if bold else "normal", color=INK, zorder=3)
            else:
                t = ax.text(b.x + PAD + 0.05, yy, txt, ha="left", va="center", fontsize=FS, fontweight="bold" if bold else "normal", color=INK, zorder=3)
            b.texts.append(t)
        if b.cols:
            y0 = ytop - len(b.lines) * LH
            colx = [b.x + PAD + 0.05, b.x + b.w / 2 + 0.22]
            numx = [b.x + b.w / 2 + 0.05, b.x + b.w - PAD - 0.05]
            for ci, col in enumerate(b.cols):
                for k, (lab, cnt) in enumerate(col):
                    yy = y0 - (k + 0.5) * LH
                    b.texts.append(ax.text(colx[ci], yy, lab, ha="left", va="center", fontsize=FS, color=INK, zorder=3))
                    b.texts.append(ax.text(numx[ci], yy, str(cnt), ha="right", va="center", fontsize=FS, color=INK, zorder=3))

    for b in all_boxes:
        box(b)

    def arrow(p0, p1, **kw):
        ax.add_patch(FancyArrowPatch(p0, p1, arrowstyle="-|>", mutation_scale=6, linewidth=0.6, color=INK, shrinkA=0, shrinkB=0, zorder=1, **kw))

    # arrows: two sources into the first main box; the main chain; exclusion branches
    ident = main[0]
    arrow((top_oa.cx, top_oa.bot), (top_oa.cx, ident.top))
    arrow((top_ax.cx, top_ax.bot), (top_ax.cx, ident.top))
    for i, b in enumerate(main[:-1]):
        nxt = main[i + 1]
        arrow((b.cx, b.bot), (b.cx, nxt.top))
        r = excl.get(b.key)
        if r is not None:
            arrow((b.cx, r.cy), (r.left, r.cy))
    # stage bands in the left margin
    stages = [("Identification", [top_oa, top_ax, main[0]]), ("Screening", main[1:5]), ("Sample and full text", main[5:8]),
              ("Included", [main[8]])]
    for name, bs in stages:
        ys = [b.top for b in bs] + [b.bot for b in bs]
        lo, hi = min(ys) - 0.06, max(ys) + 0.06
        # extend a band to the exclusion boxes whose branch starts inside it
        for b in bs:
            r = excl.get(b.key)
            if r is not None and b is not bs[-1]:
                hi, lo = max(hi, r.top), min(lo, r.bot)
        ax.add_patch(Rectangle((0.05, lo), 0.62, hi - lo, facecolor=LIGHT, edgecolor="none", zorder=1))
        t = ax.text(0.36, (lo + hi) / 2, name, rotation=90, ha="center", va="center", fontsize=FS, fontweight="bold", color=INK, zorder=3)
        t._band = (0.05, 0.67, lo, hi)
        all_boxes.append(t)
    return fig, ax, all_boxes, H


def audit_layout(fig, ax, boxes, tol=0.08) -> list[str]:
    """Check by measurement that no text leaves its box and no two boxes overlap (the inspection log still needs the eye)."""
    issues: list[str] = []
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    inv = ax.transData.inverted()

    def ext(t):
        bb = t.get_window_extent(rend)
        (x0, y0), (x1, y1) = inv.transform((bb.x0, bb.y0)), inv.transform((bb.x1, bb.y1))
        return x0, y0, x1, y1

    real = [b for b in boxes if isinstance(b, Box)]
    for b in real:
        for t in b.texts:
            x0, y0, x1, y1 = ext(t)
            if x0 < b.left + 0.04 - tol or x1 > b.right - 0.04 + tol or y0 < b.bot - tol or y1 > b.top + tol:
                issues.append(f"text '{t.get_text()}' leaves box {b.key}: text x {x0:.2f}-{x1:.2f}, box x {b.left:.2f}-{b.right:.2f}")
    for i, a in enumerate(real):
        for c in real[i + 1:]:
            if a.left < c.right and c.left < a.right and a.bot < c.top and c.bot < a.top:
                issues.append(f"boxes {a.key} and {c.key} overlap")
    for t in [b for b in boxes if not isinstance(b, Box)]:
        x0, y0, x1, y1 = ext(t)
        bx0, bx1, lo, hi = t._band
        if y0 < lo - tol or y1 > hi + tol or x0 < bx0 or x1 > bx1:
            issues.append(f"band label '{t.get_text()}' does not fit its band")
    return issues


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--out", default=None, help="PDF path (default paper/acme/figures/fig-flow.pdf); the PNG goes beside it")
    ap.add_argument("--strict", action="store_true", help="exit with status 2 when any cross-check mismatches")
    a = ap.parse_args()
    out = rc.resolve_arg(a.out, rc.ROOT / "paper" / "acme" / "figures" / "fig-flow.pdf")
    rc.guard([out, out.with_suffix(".png")], a.out is not None, RUN_DIR)
    tr = rc.Tracker()
    C = Counts(tr)
    plt = style()
    fig, ax, boxes, H = draw(C, plt)
    layout_issues = audit_layout(fig, ax, boxes)
    outs = rc.save_figure(fig, out)
    rc.write_source(outs, "analysis/acme/figures/fig_flow.py", RUN_DIR, tr, extra={
        "figure_cm": [round(W_CM, 2), round(H, 2)],
        "counts": {k: {"value": val, "source": C.prov[k]} for k, val in C.v.items()},
        "exclusion_reasons": C.reasons, "search_facts": C.facts,
        "crosscheck": {"checks_run": C.checks_done, "mismatches": C.issues},
        "layout_issues": layout_issues,
    })
    print(f"figure {W_CM:.1f} x {H:.1f} cm; cross-checks run: {C.checks_done}; mismatches: {len(C.issues)}; layout issues: {len(layout_issues)}")
    for s in C.issues + layout_issues:
        print("  ", s)
    if a.strict and C.issues:
        raise SystemExit(2)


if __name__ == "__main__":
    main()

"""Fig 7 (key `design`): benchmark design schematic (design drawing, no model outcome).

Brief: paper/acme/figures/SPEC-fig7.md.  Four blocks left to right: design cells; rendering and readout (Arm L exact, Arm S
sampled, readout gate); effect array with its two read-outs; human anchor (Many Labs 1).

Every count printed in the image is taken from NUMBERS (analysis/acme/make_autonumbers.py), converted from number words to digits
by NUM_WORDS, and cross-checked against the design arithmetic before drawing.  No run file is read and no model outcome exists.
Equation numbers are read from the compiled aux file when it exists and must equal EQ_FALLBACK.
Writes paper/acme/figures/fig-design.pdf (vector, fonts embedded) and a 600 dpi PNG to --png-dir (default: next to the PDF).

Run from the project root:  .venv/Scripts/python.exe -I analysis/acme/figures/fig_design.py
"""
from __future__ import annotations

import argparse
import itertools
import re
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, Polygon, Rectangle  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "analysis" / "acme"))
import results_common as rc  # noqa: E402  (records the files read, for the .source.json)
_REC = rc.record_reads()
from make_autonumbers import NUMBERS  # noqa: E402

# ------------------------------------------------------------------------------------------------ style (as Figs 3, 5, 6)
CM = 1 / 2.54
TEXT_WIDTH_CM = 455.24408 / 72.27 * 2.54  # \textwidth of the ACME wrapper: 16.0 cm; the float is figure* (two columns)
INK, GREY, LIGHT = "#222222", "#555555", "#DDDDDD"
FONT = "Arial"
FS = 8.0   # Springer: 8 to 12 pt at final size (the float is figure* at 16.0 cm, printed at 100 percent)
# Mathtext shrinks sub- and superscripts to 0.7 of the base size (5.6 pt here); set the factor to 1 so that every glyph is 8 pt.
import matplotlib._mathtext as _mt  # noqa: E402
_mt.SHRINK_FACTOR = 1.0
_mt.FontConstantsBase.sub1 = 0.45   # lower the full-size subscript visibly (default 0.3 at the shrunken size)
_mt.FontConstantsBase.sub2 = 0.65
plt.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": [FONT, "DejaVu Sans"], "font.size": FS, "axes.linewidth": 0.6,
    "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none", "savefig.dpi": 600, "pdf.compression": 6,
    "mathtext.fontset": "custom", "mathtext.rm": FONT, "mathtext.it": f"{FONT}:italic", "mathtext.bf": f"{FONT}:bold",
    "mathtext.default": "regular",
})
BLUE, VERM = "#0072B2", "#D55E00"           # Okabe and Ito: exact (Arm L), sampled (Arm S)
BLUE_T, VERM_T, HUMAN = "#E4F0F8", "#FBE8DC", "#D4D4D4"
DASH = (0, (3.2, 2.0))                       # sampled: dashed
DASHDOT = (0, (4.0, 1.4, 1.0, 1.4))          # applied to the logits (Arm L only)
DOT = (0, (1.0, 1.6))                        # diagnostic

NUM_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10}
EQ_FALLBACK = {"eq:share": "11", "eq:setup": "13"}


def count(key: str) -> int:
    """Integer value of a NUM key (digits or number word, thousands separators allowed)."""
    v = NUMBERS[key].value.strip().replace(",", "")
    return NUM_WORDS[v] if v in NUM_WORDS else int(v)


def eq_numbers() -> dict[str, str]:
    out = dict(EQ_FALLBACK)
    for aux in (ROOT / "paper/journals/acme/build/main.aux", ROOT / "paper/journals/acme/main.aux"):
        if not aux.exists():
            continue
        txt = aux.read_text(encoding="utf-8", errors="replace")
        for key in out:
            m = re.search(r"\\newlabel\{" + re.escape(key) + r"\}\{\{([0-9]+)\}", txt)
            assert m, f"{key} missing from {aux}"
            assert m.group(1) == out[key], f"{key}: aux says {m.group(1)}, script says {out[key]}; update EQ_FALLBACK"
        break
    return out


def design_counts() -> dict[str, object]:
    c = {
        "items": count("n.items"), "effects": count("n.effects"), "models": count("n.models"), "wordings": count("n.wordings"),
        "orders": count("n.orders.max"), "two": count("n.items.twoorder"), "one": count("n.items.oneorder"),
        "temps": count("n.temps"), "T1": count("bm.cells.T1"), "all": count("bm.cells.all"), "draws": count("bm.s.draws"),
        "sw": count("bm.s.nw"), "cap": count("bm.tree.cap"), "sites": count("n.sites"),
        "vm_thr": NUMBERS["bm.vm.thr"].value, "vm_frac": count("bm.vm.frac"), "s_temps": NUMBERS["bm.s.temps"].value,
    }
    # design arithmetic: models x wordings x (orders summed over items) at the reference temperature; times temperatures
    assert c["two"] + c["one"] == c["items"]
    assert c["models"] * c["wordings"] * (c["two"] * c["orders"] + c["one"]) == c["T1"], c
    assert c["T1"] * c["temps"] == c["all"], c
    assert c["effects"] <= c["items"]
    assert c["sw"] == 4 and NUMBERS["bm.s.temps"].value == "0.7 and 1.0"  # wordings W0 to W3 are drawn as printed
    return c


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--png-dir", default=None, help="folder for the 600 dpi inspection PNG (default: next to the PDF)")
    args = ap.parse_args()
    out_dir = ROOT / "paper" / "acme" / "figures"
    png_dir = Path(args.png_dir) if args.png_dir else out_dir

    n = design_counts()
    eq = eq_numbers()
    fmt = lambda v: f"{v:,}"  # noqa: E731

    W, H = TEXT_WIDTH_CM, 9.0
    fig = plt.figure(figsize=(W * CM, H * CM))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.axis("off")
    texts, fits, diamonds = [], [], []

    def txt(x, y, s, ha="center", va="center", weight="normal", style="normal", color=INK, z=6, lsp=1.15):
        t = ax.text(x, y, s, ha=ha, va=va, fontsize=FS, fontweight=weight, fontstyle=style, color=color, zorder=z, linespacing=lsp)
        texts.append(t)
        return t

    def box(x0, y0, x1, y1, s, fc="white", ec=INK, ls="-", lw=0.8, weight="normal", ha="center", z=2, pad=0.05, lsp=1.15):
        ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fc=fc, ec=ec, ls=ls, lw=lw, zorder=z))
        if s:
            xt = (x0 + x1) / 2 if ha == "center" else x0 + 0.1
            t = txt(xt, (y0 + y1) / 2, s, ha=ha, weight=weight, lsp=lsp)
            fits.append((t, x0 + pad, y0, x1 - pad, y1))
            return t

    def line(pts, color=INK, ls="-", lw=0.8, z=3):
        ax.plot([p[0] for p in pts], [p[1] for p in pts], color=color, ls=ls, lw=lw, solid_capstyle="butt", zorder=z)

    def arrow(pts, color=INK, ls="-", lw=0.8, both=False, z=3):
        """Polyline with an arrowhead on its last segment (and the first when both)."""
        if len(pts) > 2:
            line(pts[:-1], color, ls, lw, z)
        ax.add_patch(FancyArrowPatch(pts[-2], pts[-1], arrowstyle="<|-|>" if both else "-|>", mutation_scale=6, lw=lw, color=color,
                                     linestyle=ls, shrinkA=0, shrinkB=0, zorder=z))

    # ================================================================================== geometry (cm)
    xB1, wB1 = 0.1, 2.45
    x_trunk, x_T = 2.72, 2.92
    lane_L = (3.1, 6.5)                      # outline; inner boxes 0.15 inside
    lane_S = (8.1, 10.7) 
    xB3 = (10.98, 13.4)
    xB4 = (13.7, 15.95)
    cL = (lane_L[0] + lane_L[1]) / 2          # lane L centre
    cS = (lane_S[0] + lane_S[1]) / 2
    iL = (lane_L[0] + 0.15, lane_L[1] - 0.15)
    iS = (lane_S[0] + 0.15, lane_S[1] - 0.15)
    y_head = 8.78

    for x, s in ((xB1, "Design cells"), (lane_L[0], "Rendering and readout"), (xB3[0], "Effect array"), (xB4[0], "Human anchor")):
        txt(x, y_head, s, ha="left", weight="bold", va="center_baseline")

    # ================================================================================== block 1: design cells
    facets = [
        (f"item $\\mathit{{p}}$\n{n['items']} items, {n['effects']} effects", 0.78),
        (f"model M\n{n['models']} models", 0.78),
        (f"wording W\n{n['wordings']}, W0 verbatim", 0.78),
        (f"option order O\n{n['orders']} levels: {n['two']} items\n1 level: {n['one']} items", 1.05),
        ("condition $\\mathit{x}$\nbinary indicator", 0.78),
    ]
    assert n["orders"] == 2
    y = 8.4
    centers = []
    for s, h in facets:
        box(xB1, y - h, xB1 + wB1, y, s)
        centers.append(y - h / 2)
        y -= h + 0.12
    yT0, yT1 = 2.35, 3.45
    box(xB1, yT0, xB1 + wB1, yT1, f"temperature T\n{n['temps']} levels, applied\nto the logits", ec=BLUE, ls=DASHDOT, lw=0.9)
    yT = (yT0 + yT1) / 2
    # trunk of the five facets into the prompt
    for c in centers:
        line([(xB1 + wB1, c), (x_trunk, c)])
    line([(x_trunk, centers[-1]), (x_trunk, centers[0])])

    # ================================================================================== block 2: prompt, lanes
    y_pr = (centers[0] - 0.36, centers[0] + 0.36)
    box(lane_L[0], y_pr[0], lane_S[1], y_pr[1], "prompt: chat template of the model,\nsame text for all models")
    arrow([(x_trunk, centers[0]), (lane_L[0], centers[0])])

    # lane outlines
    yl_top, yl_bot = 7.35, 2.55
    ax.add_patch(Rectangle((lane_L[0], yl_bot), lane_L[1] - lane_L[0], yl_top - yl_bot, fc="none", ec=BLUE, lw=1.1, zorder=1))
    ys_bot = 2.45
    ax.add_patch(Rectangle((lane_S[0], ys_bot), lane_S[1] - lane_S[0], yl_top - ys_bot, fc="none", ec=VERM, lw=1.1, ls=DASH, zorder=1))
    txt(lane_L[0] + 0.1, yl_top - 0.18, "Arm L: exact", ha="left", weight="bold", color=BLUE)
    txt(lane_S[0] + 0.1, yl_top - 0.18, "Arm S: sampled", ha="left", weight="bold", color=VERM)

    # ---- Arm L
    xa_L = lane_L[1] - 0.45                    # prompt arrow into the lane (right of the lane label)
    L1 = (5.95, 6.8)
    box(iL[0], L1[0], iL[1], L1[1], "forward passes,\nfloat32 output layer", fc=BLUE_T, ec=BLUE)
    arrow([(xa_L, y_pr[0]), (xa_L, L1[1])])
    L2 = (3.5, 5.4)
    box(iL[0], L2[0], iL[1], L2[1], "", fc=BLUE_T, ec=BLUE)
    ymid = L2[0] + 1.1
    t1 = txt(cL, (ymid + L2[1]) / 2, "answer paths summed\n(choice, yes-no, rating)")
    t2 = txt(cL, (ymid + L2[0]) / 2, f"digit tree to the cap of\n{fmt(n['cap'])} expansions\n(numeric items)")
    fits += [(t1, iL[0] + 0.05, ymid, iL[1] - 0.05, L2[1]), (t2, iL[0] + 0.05, L2[0], iL[1] - 0.05, ymid)]
    line([(iL[0], ymid), (iL[1], ymid)], color=BLUE, lw=0.5, z=3)
    arrow([(cL, L1[0]), (cL, L2[1])])
    # temperature enters between the forward pass and the readout (dash-dot, Arm L only)
    y_join = (L1[0] + L2[1]) / 2
    arrow([(xB1 + wB1, yT), (x_T, yT), (x_T, y_join), (cL, y_join)], color=BLUE, ls=DASHDOT, lw=0.9)
    L3 = (2.85, 3.3)
    box(iL[0], L3[0], iL[1], L3[1], "answer probability $\\mathit{P}$", fc=BLUE_T, ec=BLUE)
    arrow([(cL, L2[0]), (cL, L3[1])])
    # readout gate (diamond)
    gcy, gw, gh = 1.5, 3.1, 1.45
    gate = Polygon([(cL - gw / 2, gcy), (cL, gcy + gh / 2), (cL + gw / 2, gcy), (cL, gcy - gh / 2)], closed=True, fc="white", ec=BLUE,
                   lw=1.0, zorder=2)
    ax.add_patch(gate)
    tg = txt(cL, gcy, f"valid mass\nat least {n['vm_thr']}")
    diamonds.append((tg, cL, gcy, gw / 2, gh / 2))
    txt(cL, gcy - gh / 2 - 0.2, f"on all but {n['vm_frac']} percent of prompts")
    arrow([(cL, L3[0]), (cL, gcy + gh / 2)])
    # exits of the gate
    txt(2.05, gcy, "pair excluded", ha="right")
    arrow([(cL - gw / 2, gcy), (2.15, gcy)])
    # the pair enters the array: right vertex, under Arm S, up to the array
    x_up = (lane_S[1] + xB3[0]) / 2
    y_arr_mid = 6.0
    txt(cL + gw / 2 + 0.1, gcy + 0.22, "pair enters the array", ha="left")
    arrow([(cL + gw / 2, gcy), (x_up, gcy), (x_up, y_arr_mid), (xB3[0], y_arr_mid)])

    # ---- Arm S
    xa_S = lane_S[1] - 0.2
    S1 = (5.5, 6.8)
    box(iS[0], S1[0], iS[1], S1[1], f"W0 to W3,\nT {n['s_temps']},\n{n['draws']} draws per cell,\nrecorded seeds", fc=VERM_T, ec=VERM, ls=DASH)
    arrow([(xa_S, y_pr[0]), (xa_S, S1[1])])
    S2 = (4.45, 5.0)
    box(iS[0], S2[0], iS[1], S2[1], "parse answer", fc=VERM_T, ec=VERM, ls=DASH)
    arrow([(cS, S1[0]), (cS, S2[1])])
    yS3 = (L3[0] + L3[1]) / 2
    S3 = (yS3 - 0.225, yS3 + 0.225)
    box(iS[0], S3[0], iS[1], S3[1], "sampled effect", fc=VERM_T, ec=VERM, ls=DASH)
    arrow([(cS, S2[0]), (cS, S3[1])])
    # agreement gate: dotted double arrow between the lanes at the level of P and the sampled effect
    arrow([(iL[1], yS3), (iS[0], yS3)], ls=DOT, lw=1.0, both=True)
    xm = (iL[1] + iS[0]) / 2
    txt(xm, yS3 + 0.2, "agreement\ngate G4\n(diagnostic\nand roster\nrule)", va="bottom")

    # ================================================================================== block 3: effect array
    y_f0, y_f1 = 4.75, 7.95                     # frame of the array object (solid: exact entries)
    ax.add_patch(Rectangle((xB3[0], y_f0), xB3[1] - xB3[0], y_f1 - y_f0, fc="white", ec=INK, lw=0.8, zorder=2))
    ax0, ay0 = 11.83, 6.62                       # lower-left corner of the front face of the cube
    fw, fh, dx, dy = 0.66, 0.62, 0.24, 0.24      # front face (M by W) and oblique depth (O)
    step = 0.13                                 # offset of each further T slab
    for k in (3, 2, 1, 0):                      # T slabs: ghosts behind, front slab last
        ox, oy = ax0 + k * step, ay0 - k * step
        z = 2.2 + (3 - k) * 0.01
        ax.add_patch(Polygon([(ox, oy), (ox + fw, oy), (ox + fw + dx, oy + dy), (ox + fw + dx, oy + fh + dy), (ox + dx, oy + fh + dy),
                              (ox, oy + fh)], closed=True, fc="white" if k == 0 else "#EDEDED", ec=INK, lw=0.7, zorder=z))
        if k == 0:
            line([(ox, oy + fh), (ox + fw, oy + fh), (ox + fw + dx, oy + fh + dy)], lw=0.7, z=z + 0.001)
            line([(ox + fw, oy), (ox + fw, oy + fh)], lw=0.7, z=z + 0.001)
            for gx in (1, 2, 3):                # M columns
                line([(ox + fw * gx / 4, oy), (ox + fw * gx / 4, oy + fh)], color="#999999", lw=0.4, z=z + 0.001)
            for gy in (1, 2):                   # W rows
                line([(ox, oy + fh * gy / 3), (ox + fw, oy + fh * gy / 3)], color="#999999", lw=0.4, z=z + 0.001)
            line([(ox + dx / 2 + fw, oy + dy / 2), (ox + dx / 2 + fw, oy + fh + dy / 2)], color="#999999", lw=0.4, z=z + 0.001)
    y_low = ay0 - 3 * step
    fits.append((txt(ax0 - 0.08, ay0 + fh / 2, f"W {n['wordings']}", ha="right"), xB3[0], y_f0, xB3[1], y_f1))
    fits.append((txt(ax0 + fw + dx + 0.06, ay0 + fh + dy - 0.02, f"O {n['orders']}", ha="left", va="bottom"), xB3[0], y_f0, xB3[1], y_f1))
    txt(ax0, y_low - 0.22, f"M {n['models']}", ha="left")
    txt(xB3[1] - 0.1, y_low - 0.22, f"T {n['temps']}", ha="right")
    fits.append((txt((xB3[0] + xB3[1]) / 2, y_f0 + 0.5, "effect in\nMany Labs 1\nSD units"), xB3[0], y_f0, xB3[1], y_f1))
    x_tr3 = xB3[0] + 0.1
    y_v = (1.8, 2.8)
    y_s = (3.35, 4.45)
    xb3 = (x_tr3 + 0.15, xB3[1])
    box(xb3[0], y_v[0], xb3[1], y_v[1], f"variance shares\n(Eq. {eq['eq:share']}),\nH1 and H3")
    box(xb3[0], y_s[0], xb3[1], y_s[1], f"set-up spread\n$\\mathit{{s_p}}$ (Eq. {eq['eq:setup']}),\nH2, yardsticks")
    yv_mid, ys_mid = (y_v[0] + y_v[1]) / 2, (y_s[0] + y_s[1]) / 2
    line([(x_tr3, y_f0), (x_tr3, yv_mid)])
    arrow([(x_tr3, yv_mid), (xb3[0], yv_mid)])
    arrow([(x_tr3, ys_mid), (xb3[0], ys_mid)])

    # ================================================================================== block 4: human anchor (grey)
    xb4 = (xB4[0], xB4[1] - 0.22)
    y_m = (6.95, 7.85)
    box(xb4[0], y_m[0], xb4[1], y_m[1], f"Many Labs 1\n{n['sites']} sites", fc=HUMAN, ec=GREY, lw=0.9)
    y_c = (4.7, 5.8)
    y_h = (1.95, 3.15)
    box(xb4[0], y_c[0], xb4[1], y_c[1], "single-site SE\n$\\mathit{c_p}$ precision\nreference", fc=HUMAN, ec=GREY, lw=0.9)
    box(xb4[0], y_h[0], xb4[1], y_h[1], "between-site\nSD $\\mathit{S^{H}_p}$\nwith interval", fc=HUMAN, ec=GREY, lw=0.9, lsp=1.45)
    x_tr4 = xB4[1] - 0.09
    yc_mid, yh_mid = (y_c[0] + y_c[1]) / 2, (y_h[0] + y_h[1]) / 2
    xs_ml = xb4[1] - 0.3
    line([(xs_ml, y_m[0]), (xs_ml, 6.4), (x_tr4, 6.4), (x_tr4, yh_mid)])
    arrow([(x_tr4, yc_mid), (xb4[1], yc_mid)])
    arrow([(x_tr4, yh_mid), (xb4[1], yh_mid)])
    txt((xb4[0] + xb4[1]) / 2, 1.35, "both in\nMany Labs 1\nSD units")
    # bracket from the two yardsticks to the set-up spread box: common scale, not an equivalence
    xbr = xB3[1] + 0.2
    line([(xb4[0], yc_mid), (xbr, yc_mid), (xbr, yh_mid), (xb4[0], yh_mid)], lw=0.8)
    assert abs(ys_mid - (yc_mid + yh_mid) / 2) < 1e-9  # the connector leaves the bracket at its midpoint
    arrow([(xbr, ys_mid), (xB3[1], ys_mid)])
    fits.append((txt((xbr + xb4[1]) / 2 + 0.05, (yc_mid + yh_mid) / 2, "common scale,\nnot an\nequivalence"), xbr, y_h[1], xb4[1], y_c[0]))

    # ---- legend (inside the figure)
    ly = 0.3
    lx = 7.0
    sw = (0.5, 0.26)
    ax.add_patch(Rectangle((lx, ly - sw[1] / 2), *sw, fc=BLUE_T, ec=BLUE, lw=1.0, zorder=2))
    txt(lx + sw[0] + 0.1, ly, "exact", ha="left", va="center_baseline")
    lx2 = lx + sw[0] + 0.1 + 0.9
    ax.add_patch(Rectangle((lx2, ly - sw[1] / 2), *sw, fc=VERM_T, ec=VERM, lw=1.0, ls=DASH, zorder=2))
    txt(lx2 + sw[0] + 0.1, ly, "sampled", ha="left", va="center_baseline")
    lx3 = lx2 + sw[0] + 0.1 + 1.25
    ax.add_patch(Rectangle((lx3, ly - sw[1] / 2), *sw, fc=HUMAN, ec=GREY, lw=1.0, zorder=2))
    txt(lx3 + sw[0] + 0.1, ly, "human data", ha="left", va="center_baseline")

    # ================================================================================== checks
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    inv = ax.transData.inverted()

    def bb(t):
        (a, b), (c, d) = inv.transform(t.get_window_extent(rend).get_points())
        return a, b, c, d

    bad = []
    for t, x0, y0, x1, y1 in fits:
        a, b, c, d = bb(t)
        if not (a >= x0 and c <= x1 and b >= y0 and d <= y1):
            bad.append(("text outside its box", t.get_text(), tuple(round(float(v), 2) for v in (a, b, c, d)), (x0, y0, x1, y1)))
    for t, cx, cy, hx, hy in diamonds:
        a, b, c, d = bb(t)
        for px, py in ((a, b), (a, d), (c, b), (c, d)):
            if abs(px - cx) / hx + abs(py - cy) / hy > 1.0:
                bad.append(("text outside diamond", t.get_text()))
                break
    for t1, t2 in itertools.combinations(texts, 2):
        a, b, c, d = bb(t1)
        e, f, g, h = bb(t2)
        if not (c <= e or g <= a or d <= f or h <= b):
            bad.append(("text overlap", t1.get_text(), t2.get_text()))
    for t in texts:
        a, b, c, d = bb(t)
        if not (0 <= a and c <= W and 0 <= b and d <= H):
            bad.append(("clipped", t.get_text(), tuple(round(float(v), 2) for v in (a, b, c, d))))
    assert not bad, "layout checks failed: " + "; ".join(map(str, bad))

    out_dir.mkdir(parents=True, exist_ok=True)
    png_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_dir / "fig-design.pdf", metadata={"Creator": "analysis/acme/figures/fig_design.py", "Title": "fig-design"})
    fig.savefig(png_dir / "fig-design.png", dpi=600)
    rc.write_source_recorded([out_dir / "fig-design.pdf", png_dir / "fig-design.png"], "analysis/acme/figures/fig_design.py", _REC)
    print("wrote", out_dir / "fig-design.pdf", "and", png_dir / "fig-design.png")


if __name__ == "__main__":
    main()

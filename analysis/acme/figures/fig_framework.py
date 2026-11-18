"""Fig 1 (key `framework`): the measurement pipeline of a simulated-participant experiment (design drawing).

Brief: paper/acme/figures/SPEC-fig1.md.  Nine stages left to right; stages 1-7 sit under the bracket "stochastic simulator
(computational surrogate)", stages 8-9 under "effect and human data".  Every stage carries two chips: the review section(s) that
treat it and the benchmark factor that varies it (or "fixed", "yardstick").

No run file and no count enters this figure (design drawing).  The only numerals are section numbers, read from the compiled aux
file when it exists and asserted equal to SECTION_FALLBACK, so a renumbering of the paper fails loudly instead of printing a stale tag.
Writes paper/acme/figures/fig-framework.pdf (vector, fonts embedded) and a 600 dpi PNG to --png-dir (default: next to the PDF).

Run from the project root:  .venv/Scripts/python.exe -I analysis/acme/figures/fig_framework.py
"""
from __future__ import annotations

import argparse
import itertools
import re
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, Rectangle  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
import sys  # noqa: E402
sys.path.insert(0, str(ROOT / "analysis" / "acme"))
import results_common as rc  # noqa: E402  (records the files read, for the .source.json)
_REC = rc.record_reads()

# ------------------------------------------------------------------------------------------------ style (as Figs 3, 5, 6)
CM = 1 / 2.54
TEXT_WIDTH_CM = 455.24408 / 72.27 * 2.54  # \textwidth of the ACME wrapper (sn-jnl, iicol): 16.0 cm; the float is figure*
INK, GREY, LIGHT = "#222222", "#555555", "#DDDDDD"
FONT = "Arial"
FS = 8.0  # Springer: 8 to 12 pt at final size (16.0 cm wide, printed at 100 percent)
plt.rcParams.update({
    "font.family": "sans-serif", "font.sans-serif": [FONT, "DejaVu Sans"], "font.size": FS,
    "axes.linewidth": 0.6, "pdf.fonttype": 42, "ps.fonttype": 42, "svg.fonttype": "none", "savefig.dpi": 600,
    "pdf.compression": 6,
})
# Okabe and Ito (2008)
BLUE, ORANGE = "#0072B2", "#E69F00"

# ------------------------------------------------------------------------------------------------ section numbers
SECTION_FALLBACK = {
    "sec:spec-task": "4.1", "sec:spec-prompt": "4.2", "sec:spec-model": "4.3", "sec:spec-decoding": "4.4",
    "sec:spec-readout": "4.5", "sec:val-reference": "5.1", "sec:val-effect": "5.2", "sec:audit-vary": "6.2",
    "sec:benchmark": "7",
}


def section_numbers() -> dict[str, str]:
    """Numbers from the compiled aux file when it exists; they must agree with the fallback (renumbering fails loudly)."""
    out = dict(SECTION_FALLBACK)
    for aux in (ROOT / "paper/journals/acme/build/main.aux", ROOT / "paper/journals/acme/main.aux"):
        if not aux.exists():
            continue
        txt = aux.read_text(encoding="utf-8", errors="replace")
        for key in out:
            m = re.search(r"\\newlabel\{" + re.escape(key) + r"\}\{\{([0-9.]+)\}", txt)
            assert m, f"{key} missing from {aux}"
            assert m.group(1) == out[key], f"{key}: aux says {m.group(1)}, script says {out[key]}; update SECTION_FALLBACK"
        break
    return out


# ------------------------------------------------------------------------------------------------ the nine stages (exact names)
# (box text with line breaks, review labels, audit label or None, benchmark chip, kind)
def stages(sec: dict[str, str]):
    def rv(*keys):
        return ", ".join(sec[k] for k in keys)

    aud = sec["sec:audit-vary"]
    return [(a, b.replace("; ", ";\n").replace(", ", ",\n"), c, d) for a, b, c, d in [
        ("paradigm", f"Sec. {rv('sec:spec-task')}", "fixed", "fixed"),
        ("stimulus", f"Sec. {rv('sec:spec-task')}", "fixed", "fixed"),
        ("wording", f"Sec. {rv('sec:spec-prompt')}; {aud}", "W varied", "varied"),
        ("option\norder", f"Sec. {rv('sec:spec-prompt')}; {aud}", "O varied", "varied"),
        ("decoding /\ntemperature", f"Sec. {rv('sec:spec-decoding')}; {aud}", "T varied", "varied"),
        ("model", f"Sec. {rv('sec:spec-model')}; {aud}", "M varied", "varied"),
        ("readout", f"Sec. {rv('sec:spec-readout')}", "fixed", "fixed"),
        ("scoring", f"Sec. {rv('sec:spec-readout', 'sec:val-effect')}", "fixed", "fixed"),
        ("human\nreference", f"Sec. {rv('sec:val-reference')}", "yardstick", "human"),
    ]]


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--png-dir", default=None, help="folder for the 600 dpi inspection PNG (default: next to the PDF)")
    args = ap.parse_args()
    out_dir = ROOT / "paper" / "acme" / "figures"
    png_dir = Path(args.png_dir) if args.png_dir else out_dir

    sec = section_numbers()
    st = stages(sec)
    names = [s[0].replace("\n", " ") for s in st]
    assert names == ["paradigm", "stimulus", "wording", "option order", "decoding / temperature", "model", "readout", "scoring",
                     "human reference"], names

    W, H = TEXT_WIDTH_CM, 6.15
    fig = plt.figure(figsize=(W * CM, H * CM))
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, W)
    ax.set_ylim(0, H)
    ax.axis("off")
    texts: list = []      # every text, for the overlap check
    fits: list = []       # (text, x0, y0, x1, y1): the text must lie inside the rectangle

    def txt(x, y, s, ha="center", va="center", color=INK, weight="normal", style="normal", z=5):
        t = ax.text(x, y, s, ha=ha, va=va, color=color, fontsize=FS, fontweight=weight, fontstyle=style, zorder=z,
                    linespacing=1.15)
        texts.append(t)
        return t

    # ---------------------------------------------------------------- geometry (cm)
    n = len(st)
    BH, GAP = 1.3, 0.17        # box height; gap between boxes (room for the arrow)
    BW = (W - 0.2 - (n - 1) * GAP) / n   # box width: the chain fills the text width
    x0 = 0.1
    xs = [x0 + i * (BW + GAP) for i in range(n)]
    y_box = 2.90               # bottom of the boxes
    y_up, y_lo = y_box - 0.12 - 0.70, y_box - 0.12 - 0.70 - 0.05 - 0.70   # bottoms of upper and lower chip
    chip_h = 0.70

    face = {"varied": BLUE, "fixed": LIGHT, "human": ORANGE}
    edge = {"varied": BLUE, "fixed": "#777777", "human": ORANGE}
    ink = {"varied": "white", "fixed": INK, "human": INK}

    for i, (name, rtag, btag, kind) in enumerate(st):
        xl = xs[i]
        ax.add_patch(Rectangle((xl, y_box), BW, BH, fc=face[kind], ec=edge[kind], lw=0.7, zorder=2))
        t = txt(xl + BW / 2, y_box + BH / 2, name, color=ink[kind])  # normal weight: bold "temperature" at 8 pt is wider than the box
        fits.append((t, xl, y_box, xl + BW, y_box + BH))
        for yb, tag in ((y_up, rtag), (y_lo, btag)):
            ax.add_patch(Rectangle((xl, yb), BW, chip_h, fc="white", ec=edge[kind], lw=0.7, zorder=2))
            t = txt(xl + BW / 2, yb + chip_h / 2, tag)
            fits.append((t, xl, yb, xl + BW, yb + chip_h))

    # ---------------------------------------------------------------- arrows 1 -> 8 (solid) and 9 -> 8 (dashed)
    ym = y_box + BH / 2
    for i in range(7):
        ax.add_patch(FancyArrowPatch((xs[i] + BW, ym), (xs[i + 1], ym), arrowstyle="-|>", mutation_scale=6, lw=0.8, color=INK,
                                     shrinkA=0, shrinkB=0, zorder=3))
    # dashed arc above the chain, from the top of the human reference back to the top of the scoring box
    ytop = y_box + BH
    ax.add_patch(FancyArrowPatch((xs[8] + BW / 2, ytop), (xs[7] + BW / 2, ytop), arrowstyle="-|>", mutation_scale=6, lw=0.8,
                                 color=INK, linestyle=(0, (3, 2)), connectionstyle="arc3,rad=0.4", shrinkA=0, shrinkB=0, zorder=3))
    txt((xs[7] + xs[8] + BW) / 2, ytop + 0.58, "compared with")

    # ---------------------------------------------------------------- brackets above (simulator; effect and human data)
    def bracket_top(xa, xb, y, h=0.12):
        ax.plot([xa, xa, xb, xb], [y - h, y, y, y - h], color=INK, lw=0.8, solid_capstyle="butt", zorder=2)

    y_br = y_box + BH + 0.98
    bracket_top(xs[0], xs[6] + BW, y_br)
    bracket_top(xs[7], xs[8] + BW, y_br)
    xc1 = (xs[0] + xs[6] + BW) / 2
    xc2 = (xs[7] + xs[8] + BW) / 2
    txt(xc1, y_br + 0.62, "stochastic simulator (computational surrogate)", va="center_baseline", weight="bold")
    txt(xc1, y_br + 0.30, "verification of the estimator, sensitivity analysis of the set-up", va="center_baseline")
    txt(xs[8] + BW, y_br + 0.62, "effect and human data", ha="right", va="center_baseline", weight="bold")
    txt(xs[8] + BW, y_br + 0.30, "validation against human data", ha="right", va="center_baseline")

    # ---------------------------------------------------------------- bracket below (validation: scoring + human reference)
    y_vb = y_lo - 0.22
    ax.plot([xs[7], xs[7], xs[8] + BW, xs[8] + BW], [y_vb + 0.12, y_vb, y_vb, y_vb + 0.12], color=INK, lw=0.8,
            solid_capstyle="butt", zorder=2)
    txt(xc2, y_vb - 0.2, f"validation (Section {sec['sec:val-reference'].split('.')[0]})", weight="bold")

    # ---------------------------------------------------------------- foot legend (one thin line)
    ly = 0.36
    sw = 0.22
    lx = x0
    for lab, kind in (("varied factor", "varied"), ("fixed stage", "fixed"), ("human reference", "human")):
        ax.add_patch(Rectangle((lx, ly - sw / 2), sw, sw, fc=face[kind], ec=edge[kind], lw=0.7, zorder=2))
        t = txt(lx + sw + 0.1, ly, lab, ha="left", va="center_baseline")
        lx += sw + 0.1 + 0.140 * len(lab) + 0.45
    txt(W - x0, ly, f"upper chip: review section;\nlower chip: factor of the case study in Section {sec['sec:benchmark']}",
        ha="right", va="center_baseline")

    # ---------------------------------------------------------------- checks: fit inside boxes, no text overlaps
    fig.canvas.draw()
    rend = fig.canvas.get_renderer()
    inv = ax.transData.inverted()

    def bb(t):
        (a, b), (c, d) = inv.transform(t.get_window_extent(rend).get_points())
        return a, b, c, d

    for t, ax0, ay0, ax1, ay1 in fits:
        a, b, c, d = bb(t)
        pad = 0.04
        assert a >= ax0 + pad and c <= ax1 - pad and b >= ay0 and d <= ay1, (t.get_text(), (a, b, c, d), (ax0, ay0, ax1, ay1))
    for t1, t2 in itertools.combinations(texts, 2):
        a, b, c, d = bb(t1)
        e, f, g, h = bb(t2)
        assert c <= e or g <= a or d <= f or h <= b, ("text overlap", t1.get_text(), t2.get_text())
    for t in texts:
        a, b, c, d = bb(t)
        assert 0 <= a and c <= W and 0 <= b and d <= H, ("clipped", t.get_text())

    out_dir.mkdir(parents=True, exist_ok=True)
    png_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_dir / "fig-framework.pdf", metadata={"Creator": "analysis/acme/figures/fig_framework.py", "Title": "fig-framework"})
    fig.savefig(png_dir / "fig-framework.png", dpi=600)
    rc.write_source_recorded([out_dir / "fig-framework.pdf", png_dir / "fig-framework.png"], "analysis/acme/figures/fig_framework.py", _REC)
    print("wrote", out_dir / "fig-framework.pdf", "and", png_dir / "fig-framework.png")


if __name__ == "__main__":
    main()

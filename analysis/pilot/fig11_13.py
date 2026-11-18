"""Figures 11-13 of the review: the Many Labs 1 pilot (RQ5). Reads only runs/pilot-side-by-side/.

    .venv/Scripts/python.exe -I analysis/pilot/fig11_13.py

Fig 11  forest plot per paradigm x model: LLM mean cell effect (Delta-bar) and finite-cell spread S,
        against the human ML1 pooled effect (REML CI band) and the human spread S^H (interval band).
Fig 12  variance decomposition: share of the corrected between-cell sum of squares per perturbation
        factor (heatmaps, model x paradigm).
Fig 13  sign stability: share of cells with the human (positive) sign, per model x paradigm.

Rules enforced here: preregistered A1 scale only (A2 rows are dropped by an assertion); the
LLM-S / human-S ratio column is never read; no title or caption inside a figure.
Outputs: paper/figures/Fig{11,12,13}.{pdf,eps,png}; runs/pilot-figs-11-13/figures.log
"""
from __future__ import annotations

import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import LinearSegmentedColormap, to_rgb  # noqa: E402
from matplotlib.patches import Polygon, Rectangle  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
IN = ROOT / "runs/pilot-side-by-side"
FI = IN / "fig_inputs"
OUT = ROOT / "paper/figures"
LOGDIR = ROOT / "runs/pilot-figs-11-13"

# ---------------------------------------------------------------- style
plt.rcParams.update({
    "font.family": "sans-serif",
    "font.sans-serif": ["Arial", "Helvetica", "DejaVu Sans"],
    "font.size": 7.5,
    "axes.labelsize": 7.5,
    "xtick.labelsize": 7,
    "ytick.labelsize": 7.5,
    "axes.linewidth": 0.5,
    "xtick.major.width": 0.5,
    "xtick.major.size": 2.5,
    "pdf.fonttype": 42,
    "ps.fonttype": 42,
    "hatch.linewidth": 0.6,
    "savefig.facecolor": "white",
    "figure.facecolor": "white",
})
INK = "#1A1A1A"        # text
GREY = "#595959"       # secondary text and axes (7:1 on white)
BLUE = "#0072B2"       # Okabe-Ito blue: Delta-bar and the human effect
VERM = "#D55E00"       # Okabe-Ito vermillion: S and the human spread
BAND_B = "#BCD8EC"
BAND_V = "#FBE0CE"
MM = 1 / 25.4
W_MM = 174.0           # Springer double column

MODEL_ORDER = ["granite-3.3-2b-instruct", "granite-3.3-8b-instruct", "olmo2-1b-instruct",
               "olmo2-7b-instruct", "qwen2.5-1.5b-instruct", "qwen2.5-7b-instruct"]
MODEL_LABEL = {"granite-3.3-2b-instruct": "Granite 3.3 2B", "granite-3.3-8b-instruct": "Granite 3.3 8B",
               "olmo2-1b-instruct": "OLMo 2 1B", "olmo2-7b-instruct": "OLMo 2 7B",
               "qwen2.5-1.5b-instruct": "Qwen2.5 1.5B", "qwen2.5-7b-instruct": "Qwen2.5 7B"}
PARADIGMS = ["P1", "P2a", "P2b", "P2c", "P2d", "P3", "P4"]
PARADIGM_NAME = {"P1": "P1 framing", "P2a": "P2a anchoring, SF-NYC", "P2b": "P2b anchoring, Chicago",
                 "P2c": "P2c anchoring, Everest", "P2d": "P2d anchoring, babies/day",
                 "P3": "P3 sunk cost", "P4": "P4 gambler's fallacy"}
XLAB = {"P1": "log odds ratio (sure option)", "P2a": "Hedges g on log(estimate)",
        "P2b": "Hedges g on log(estimate)", "P2c": "Hedges g on log(estimate)",
        "P2d": "Hedges g on log(estimate)", "P3": "Hedges g", "P4": "Hedges g on log(1 + estimate)"}
LOG: list[str] = []


def log(msg: str) -> None:
    LOG.append(msg)
    print(msg)


def lum(rgb) -> float:
    c = [v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4 for v in rgb]
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def contrast(a, b) -> float:
    la, lb = lum(to_rgb(a)), lum(to_rgb(b))
    return (max(la, lb) + 0.05) / (min(la, lb) + 0.05)


MIN_CONTRAST = {"value": 99.0}


def text_on(face) -> str:
    """Black or white label, whichever has the higher contrast on `face`; the minimum is logged."""
    c_w, c_k = contrast("#FFFFFF", face), contrast("#000000", face)
    MIN_CONTRAST["value"] = min(MIN_CONTRAST["value"], max(c_w, c_k))
    return "#FFFFFF" if c_w >= c_k else "#000000"


def save(fig, name: str) -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{name}.pdf")
    fig.savefig(OUT / f"{name}.eps")
    fig.savefig(OUT / f"{name}.png", dpi=600)
    from PIL import Image  # PNG as 8-bit RGB (journal rule), 600 dpi metadata kept
    im = Image.open(OUT / f"{name}.png").convert("RGB")
    im.save(OUT / f"{name}.png", dpi=(600, 600))
    plt.close(fig)
    log(f"saved {name}.pdf / .eps / .png")


class Canvas:
    """Figure laid out in millimetres, origin top-left."""

    def __init__(self, h_mm: float):
        self.h = h_mm
        self.fig = plt.figure(figsize=(W_MM * MM, h_mm * MM))

    def axes(self, x, y, w, h, **kw):
        return self.fig.add_axes([x / W_MM, 1 - (y + h) / self.h, w / W_MM, h / self.h], **kw)

    def text(self, x, y, s, **kw):
        return self.fig.text(x / W_MM, 1 - y / self.h, s, **kw)


# ---------------------------------------------------------------- data
def load():
    use_f11 = ["model", "paradigm", "scale", "scale_status", "llm_mu", "llm_mu_lo", "llm_mu_hi", "llm_S", "llm_S_lo",
               "llm_S_hi", "human_mu", "human_mu_lo", "human_mu_hi", "human_S", "human_S_lo", "human_S_hi"]
    f11 = pd.read_csv(FI / "fig11_forest.csv", usecols=use_f11)
    f11 = f11[f11.scale_status.str.startswith("preregistered")].copy()
    assert len(f11) == 42 and set(f11.scale_status) == {"preregistered (A1)"}
    # flags come from the A1 table (table_a1.csv holds only A1 rows); the ratio column is not read
    cols_t = ["model", "paradigm", "scale_status", "nd_flag_any", "topup_used", "nd_n_flagged", "nd_C"]
    ta = pd.read_csv(IN / "table_a1.csv", usecols=cols_t)
    assert set(ta.scale_status) == {"preregistered (A1)"} and len(ta) == 42
    f11 = f11.merge(ta[["model", "paradigm", "nd_flag_any", "topup_used", "nd_n_flagged", "nd_C"]],
                    on=["model", "paradigm"], validate="1:1")
    f12 = pd.read_csv(FI / "fig12_variance_terms.csv")
    f12 = f12[f12.scale == "A1_preregistered"].copy()
    assert len(f12) == 6 * (15 + 6 * 7)
    f13 = pd.read_csv(FI / "fig13_sign_cells.csv")
    f13 = f13[f13.scale == "A1_preregistered"].copy()
    assert len(f13) == 6 * (32 + 6 * 16)
    return f11, f12, f13, ta


# ---------------------------------------------------------------- Fig 11
def marker_strip(ax, y, nd, top, size=3.6):
    """Flag markers in a margin strip right of the axes: x in axes fraction, y in data."""
    tr = ax.get_yaxis_transform()
    if nd:
        ax.plot([1.045], [y], marker="s", ms=size, mfc=INK, mec=INK, mew=0.4, ls="none", transform=tr, clip_on=False)
    if top:
        ax.plot([1.125], [y], marker="^", ms=size + 0.8, mfc=INK, mec=INK, mew=0.4, ls="none", transform=tr,
                clip_on=False)


def fig11(f11):
    H = 217.0
    cv = Canvas(H)
    lab_w, ax_w, ax_h = 18.0, 55.0, 33.0
    x0s, y0s = [1.5, 88.5], [8.0, 61.0, 114.0, 167.0]
    order = PARADIGMS + ["KEY"]
    letters = "abcdefg"
    for k, p in enumerate(order):
        r, c = divmod(k, 2)
        bx, by = x0s[c], y0s[r]
        if p == "KEY":
            key_panel(cv, bx, by)
            continue
        d = f11[f11.paradigm == p].set_index("model").loc[MODEL_ORDER]
        ax = cv.axes(bx + lab_w, by + 5.0, ax_w, ax_h)
        hum = d.iloc[0]
        lo = min(d.llm_mu_lo.min(), d.llm_S_lo.min(), hum.human_mu_lo, hum.human_S_lo, 0.0)
        hi = max(d.llm_mu_hi.max(), d.llm_S_hi.max(), hum.human_mu_hi, hum.human_S_hi)
        pad = 0.04 * (hi - lo)
        ax.set_xlim(lo - pad, hi + pad)
        ax.set_ylim(len(MODEL_ORDER) - 0.5, -0.5)
        # human reference bands (full panel height)
        ax.axvspan(hum.human_S_lo, hum.human_S_hi, facecolor=BAND_V, edgecolor=VERM, hatch="/////", lw=0, zorder=0)
        ax.axvspan(hum.human_mu_lo, hum.human_mu_hi, facecolor=BAND_B, edgecolor=BLUE, hatch="", lw=0, zorder=0.5)
        ax.axvline(hum.human_mu, color=BLUE, lw=0.9, zorder=1)
        ax.axvline(hum.human_S, color=VERM, lw=0.9, ls=(0, (3, 2)), zorder=1)
        ax.axvline(0, color=GREY, lw=0.5, zorder=1)
        for i, m in enumerate(MODEL_ORDER):
            row = d.loc[m]
            ym, ys = i - 0.2, i + 0.2
            ax.plot([row.llm_mu_lo, row.llm_mu_hi], [ym, ym], color=BLUE, lw=1.1, solid_capstyle="butt", zorder=3)
            ax.plot([row.llm_mu], [ym], marker="o", ms=3.6, mfc=BLUE, mec=BLUE, mew=0.5, ls="none", zorder=4)
            ax.plot([row.llm_S_lo, row.llm_S_hi], [ys, ys], color=VERM, lw=1.1, solid_capstyle="butt", zorder=3)
            ax.plot([row.llm_S], [ys], marker="D", ms=3.3, mfc="white", mec=VERM, mew=0.9, ls="none", zorder=4)
            marker_strip(ax, i, bool(row.nd_flag_any), bool(row.topup_used))
            if i < len(MODEL_ORDER) - 1:
                ax.axhline(i + 0.5, color="#D0D0D0", lw=0.4, zorder=0.2)
        ax.set_yticks(range(len(MODEL_ORDER)))
        ax.set_yticklabels([MODEL_LABEL[m] for m in MODEL_ORDER])
        ax.tick_params(axis="y", length=0, pad=2, colors=INK)
        ax.tick_params(axis="x", colors=INK, pad=1.5)
        ax.set_xlabel(XLAB[p], labelpad=1.5, color=INK)
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        for s in ("left", "bottom"):
            ax.spines[s].set_color(GREY)
        cv.text(bx, by + 2.6, letters[k], fontweight="bold", fontsize=8.5, color=INK, va="center")
        cv.text(bx + 4.5, by + 2.6, PARADIGM_NAME[p], fontsize=7.5, color=INK, va="center")
        log(f"fig11 {p}: xlim=({lo - pad:.2f},{hi + pad:.2f}) nd={int(d.nd_flag_any.sum())} topup={int(d.topup_used.sum())}")
    save(cv.fig, "Fig11")


def key_panel(cv, bx, by):
    ax = cv.axes(bx, by, 85.0, 47.0)
    ax.set_xlim(0, 85)
    ax.set_ylim(47, 0)
    ax.axis("off")
    ytop, dy = 4.0, 5.1
    ys = [ytop + dy * i for i in range(7)]
    ax.plot([2, 9], [ys[0]] * 2, color=BLUE, lw=1.1, solid_capstyle="butt")
    ax.plot([5.5], [ys[0]], marker="o", ms=3.6, mfc=BLUE, mec=BLUE, ls="none")
    ax.text(12, ys[0], "LLM mean cell effect, 95% interval", va="center", color=INK, fontsize=7.5)
    ax.plot([2, 9], [ys[1]] * 2, color=VERM, lw=1.1, solid_capstyle="butt")
    ax.plot([5.5], [ys[1]], marker="D", ms=3.3, mfc="white", mec=VERM, mew=0.9, ls="none")
    ax.text(12, ys[1], "LLM finite-cell spread S, 95% interval", va="center", color=INK, fontsize=7.5)
    ax.add_patch(Rectangle((2, ys[2] - 1.8), 7, 3.6, facecolor=BAND_B, edgecolor="none"))
    ax.plot([5.5, 5.5], [ys[2] - 1.8, ys[2] + 1.8], color=BLUE, lw=0.9)
    ax.text(12, ys[2], "Human pooled effect (line) and 95% CI (band)", va="center", color=INK, fontsize=7.5)
    ax.add_patch(Rectangle((2, ys[3] - 1.8), 7, 3.6, facecolor=BAND_V, edgecolor=VERM, hatch="/////", lw=0))
    ax.plot([5.5, 5.5], [ys[3] - 1.8, ys[3] + 1.8], color=VERM, lw=0.9, ls=(0, (3, 2)))
    ax.text(12, ys[3], "Human between-site spread (line) and interval (band)", va="center", color=INK, fontsize=7.5)
    ax.plot([5.5], [ys[4]], marker="s", ms=3.6, mfc=INK, mec=INK, mew=0.4, ls="none")
    ax.text(12, ys[4], "Grid has near-deterministic cells", va="center", color=INK, fontsize=7.5)
    ax.plot([5.5], [ys[5]], marker="^", ms=4.4, mfc=INK, mec=INK, mew=0.4, ls="none")
    ax.text(12, ys[5], "Grid contains top-up responses", va="center", color=INK, fontsize=7.5)
    ax.text(2, ys[6] + 1.2, "Within each model row, upper mark: mean cell effect;\nlower mark: spread S. Same axis, effect units.",
            va="top", color=GREY, fontsize=7)


# ---------------------------------------------------------------- heatmap helpers
def seq_cmap():
    return LinearSegmentedColormap.from_list("seq", ["#F4F8FC", "#9CC3E0", "#2E7CB8", "#0B3C66"])


def div_cmap():
    return LinearSegmentedColormap.from_list("div", ["#B04A00", "#E8A56E", "#F2F2F2", "#7FB0D6", "#0A5C94"])


def heat(ax, M, cmap, vmin, vmax, fmt, na_mask=None, corner=None):
    """Cell grid with in-cell numbers. M: (rows, cols) float array in data units."""
    nr, nc = M.shape
    ax.set_xlim(0, nc)
    ax.set_ylim(nr, 0)
    for i in range(nr):
        for j in range(nc):
            v = M[i, j]
            if np.isnan(v) or (na_mask is not None and na_mask[i, j]):
                ax.add_patch(Rectangle((j, i), 1, 1, facecolor="#F2F2F2", edgecolor="#8C8C8C", hatch="/////", lw=0, zorder=1))
                ax.add_patch(Rectangle((j, i), 1, 1, facecolor="none", edgecolor="white", lw=1.2, zorder=2))
                if corner is not None and corner[i, j]:
                    corner_mark(ax, j, i)
                continue
            t = float(np.clip((v - vmin) / (vmax - vmin), 0, 1))
            face = cmap(t)
            ax.add_patch(Rectangle((j, i), 1, 1, facecolor=face, edgecolor="white", lw=1.2, zorder=1))
            ax.text(j + 0.5, i + 0.52, fmt(v), ha="center", va="center", fontsize=7, color=text_on(face), zorder=3)
            if corner is not None and corner[i, j]:
                corner_mark(ax, j, i)
    ax.set_xticks(np.arange(nc) + 0.5)
    ax.xaxis.tick_top()
    ax.tick_params(axis="both", length=0, pad=1.5, colors=INK)
    for s in ax.spines.values():
        s.set_visible(False)


def corner_mark(ax, j, i):
    ax.add_patch(Polygon([[j + 1, i], [j + 1, i + 0.36], [j + 0.64, i]], closed=True, facecolor=INK,
                         edgecolor="white", lw=0.4, zorder=4))


def pct(v):
    s = f"{abs(v) * 100:.0f}"
    return ("−" + s) if (v < 0 and s != "0") else s


def hbar(cv, x, y, w, h, cmap, vmin, vmax, ticks, ticklabels, label):
    ax = cv.axes(x, y, w, h)
    grad = np.linspace(0, 1, 256)[None, :]
    ax.imshow(grad, aspect="auto", cmap=cmap, extent=[vmin, vmax, 0, 1])
    ax.set_yticks([])
    ax.set_xticks(ticks)
    ax.set_xticklabels(ticklabels)
    ax.tick_params(axis="x", length=2, width=0.5, pad=1.5, colors=INK, labelsize=7)
    for s in ax.spines.values():
        s.set_linewidth(0.5)
        s.set_color(GREY)
    ax.set_xlabel(label, fontsize=7.5, labelpad=1.5, color=INK)
    return ax


# ---------------------------------------------------------------- Fig 12
def fig12(f12, ta):
    cw, ch = 6.5, 5.4             # cell size (mm)
    lab = 24.0
    H = 97.0
    cv = Canvas(H)
    ndmap = ta.set_index(["model", "paradigm"]).nd_flag_any
    d = f12.copy()
    d["factor"] = np.where(d.term.str.contains(":"), "INT", d.term)
    agg = (d.groupby(["model", "paradigm", "factor"], as_index=False)
             .agg(share=("share", lambda s: s.sum(min_count=1)), rep=("shares_reportable", "first")))
    tot = agg[agg.rep].groupby(["model", "paradigm"]).share.sum()
    assert np.abs(tot.values - 1).max() < 1e-9, "shares do not sum to one"
    panels = [("W", "Wording (W)"), ("F", "Response format (F)"), ("T", "Temperature (T)"),
              ("INT", "All interactions"), ("O", "Option order (O)")]
    letters = "abcde"
    pw = 7 * cw
    gap = 5.0
    x_cols = [lab, lab + pw + gap, lab + 2 * (pw + gap)]
    y_rows = [10.5, 10.5 + 6 * ch + 17.0]
    pos = {"W": (x_cols[0], y_rows[0], 7), "F": (x_cols[1], y_rows[0], 7), "T": (x_cols[2], y_rows[0], 7),
           "INT": (x_cols[0], y_rows[1], 7), "O": (x_cols[1], y_rows[1], 1)}
    cm = seq_cmap()
    for k, (f, title) in enumerate(panels):
        x, y, nc = pos[f]
        ax = cv.axes(x, y, nc * cw, 6 * ch)
        pars = PARADIGMS if f != "O" else ["P1"]
        M = np.full((6, nc), np.nan)
        NA = np.zeros((6, nc), bool)
        CR = np.zeros((6, nc), bool)
        for i, m in enumerate(MODEL_ORDER):
            for j, p in enumerate(pars):
                g = agg[(agg.model == m) & (agg.paradigm == p) & (agg.factor == f)]
                if g.empty:
                    NA[i, j] = True
                    continue
                if not bool(g.rep.iloc[0]):
                    NA[i, j] = True
                else:
                    M[i, j] = g.share.iloc[0]
                CR[i, j] = bool(ndmap.loc[(m, p)])
        heat(ax, M, cm, 0, 1, pct, na_mask=NA)
        ax.set_xticklabels(pars, fontsize=7)
        left = f in ("W", "INT")
        if left:
            ax.set_yticks(np.arange(6) + 0.5)
            ax.set_yticklabels([MODEL_LABEL[m] for m in MODEL_ORDER], fontsize=7.5)
        else:
            ax.set_yticks([])
        tx = x - lab + 1.0 if left else x
        cv.text(tx, y - 6.0, letters[k], fontweight="bold", fontsize=8.5, color=INK, va="center")
        cv.text(tx + 4.5, y - 6.0, title, fontsize=7.5, color=INK, va="center")
        log(f"fig12 {f}: reported cells={int((~np.isnan(M)).sum())}, not reported/absent={int(NA.sum())}")
    # key to the right of the option-order panel
    kx = x_cols[1] + cw + 12.0
    ky = y_rows[1]
    hbar(cv, kx, ky + 2.0, 60.0, 3.0, cm, 0, 1, [0, 0.25, 0.5, 0.75, 1], ["0", "25", "50", "75", "100"],
         "Share of between-cell sum of squares (%)")
    kax = cv.axes(kx, ky + 15.0, 80.0, 20.0)
    kax.set_xlim(0, 80)
    kax.set_ylim(20, 0)
    kax.axis("off")
    kax.add_patch(Rectangle((0, 1.0), cw * 0.9, ch * 0.8, facecolor="#F2F2F2", edgecolor="#8C8C8C", hatch="/////", lw=0))
    kax.text(cw + 1.5, 1.0 + ch * 0.4, "Not reported (A1.5), or factor absent", va="center", fontsize=7.5, color=INK)
    kax.text(0, 9.5, "Colour is clamped to 0 to 100; the number in each" + chr(10) + "cell is the exact share.",
             va="top", fontsize=7, color=GREY)
    save(cv.fig, "Fig12")


# ---------------------------------------------------------------- Fig 13
def fig13(f13):
    cw, ch = 9.0, 7.0
    lab = 25.0
    gap = 8.0
    H = 6 * ch + 36.0
    cv = Canvas(H)
    g = f13.groupby(["model", "paradigm"]).agg(pt=("sign_positive", "mean"),
                                                st=("canonical_sign_and_ci_excludes_0", "mean")).reset_index()
    spec = [("pt", div_cmap(), "a", "Cells with the human (positive) sign", lab),
            ("st", seq_cmap(), "b", "Cells with the human sign and a 95% CI excluding 0", lab + 7 * cw + gap)]
    for col, cmap, letter, title, x in spec:
        y = 14.0
        ax = cv.axes(x, y, 7 * cw, 6 * ch)
        M = np.zeros((6, 7))
        for i, m in enumerate(MODEL_ORDER):
            for j, p in enumerate(PARADIGMS):
                M[i, j] = g[(g.model == m) & (g.paradigm == p)][col].iloc[0]
        heat(ax, M, cmap, 0, 1, pct)
        ax.set_xticklabels(PARADIGMS, fontsize=7)
        if col == "pt":
            ax.set_yticks(np.arange(6) + 0.5)
            ax.set_yticklabels([MODEL_LABEL[m] for m in MODEL_ORDER], fontsize=7.5)
        else:
            ax.set_yticks([])
        xt = x if col == "st" else x - lab + 1.0
        cv.text(xt, 5.0, letter, fontweight="bold", fontsize=8.5, color=INK, va="center")
        cv.text(xt + 4.5, 5.0, title, fontsize=7.5, color=INK, va="center")
        hb = hbar(cv, x + 7 * cw * 0.15, y + 6 * ch + 4.0, 7 * cw * 0.7, 3.0, cmap, 0, 1, [0, 0.25, 0.5, 0.75, 1],
                  ["0", "25", "50", "75", "100"], "Share of cells (%)")
        if col == "pt":
            hb.axvline(0.5, color=INK, lw=0.6)
        log(f"fig13 {col}: min={M.min():.3f} max={M.max():.3f}")
    save(cv.fig, "Fig13")


def main():
    f11, f12, f13, ta = load()
    fig11(f11)
    fig12(f12, ta)
    fig13(f13)
    log(f"minimum text contrast in heatmap cells: {MIN_CONTRAST['value']:.2f}:1 (need >= 4.5)")
    LOGDIR.mkdir(parents=True, exist_ok=True)
    (LOGDIR / "figures.log").write_text("\n".join(LOG) + "\n", encoding="utf-8")


if __name__ == "__main__":
    sys.exit(main())

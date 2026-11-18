"""Fig 10 (key `yardsticks`): Many Labs 1 sites and simulated set-ups on one axis in ML1-SD units, one panel per item.  Brief:
paper/acme/figures/SPEC-fig10.md.

Per panel (top to bottom): the pooled human effect (diamond, Wald interval) with a bar of the between-site SD S^H, then the 36 Many Labs 1
sites (sample estimates with 95 percent intervals, sorted by estimate), then one row per model with its deterministic set-up effects
(every wording x order cell of the main array at the reference temperature, no intervals), the model mean and a bar of its set-up SD.
The light band is the pooled effect +- the single-site SE c_p.  Units: effect / sd_within (arml_scales.csv), the unit of gstudy.py.

Reads: <gstudy>/setup_sd.csv, <gstudy>/yardsticks.csv, <gstudy>/summary.json, the effects table named in summary.json config.effects
(override with --effects; it is the table gstudy.py read, so a real run needs access to that file), and the human files
arml_scales.csv, pooled_sd_units.csv, pooled_site_inputs.csv in runs/human-ml1-acme/.  Rows of a model are drawn for the items whose
array it entered (setup_sd.csv).  Nothing numeric is typed here.  Writes PDF, 600 dpi PNG and <file>.source.json.

    .venv/Scripts/python.exe -I analysis/acme/figures/fig_yardsticks.py [--gstudy runs/acme-gstudy/A1] [--effects effects.csv] [--out ...]
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import results_common as rc  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--gstudy", default=str(rc.DEFAULT_GSTUDY))
    ap.add_argument("--effects", default=None, help="effects table gstudy.py read (default: summary.json config.effects)")
    ap.add_argument("--out", default=None)
    ap.add_argument("--cols", type=int, default=5)
    a = ap.parse_args()
    gs = rc.resolve_arg(a.gstudy)
    out = rc.resolve_arg(a.out, rc.ROOT / "paper" / "acme" / "figures" / "fig-yardsticks.pdf")
    tr = rc.Tracker()
    summ = tr.json(gs / "summary.json")
    eff_path = rc.resolve_arg(a.effects) if a.effects else rc.resolve_arg(summ["config"]["effects"])
    if not eff_path.is_absolute() or not eff_path.exists():
        eff_path = rc.ROOT / summ["config"]["effects"]
    rc.guard([out, out.with_suffix(".png")], a.out is not None, gs, model_inputs=[eff_path])

    sd = tr.csv(gs / "setup_sd.csv", dtype={"item": str, "model": str})
    ys = tr.csv(gs / "yardsticks.csv", dtype={"item": str, "model": str})
    eff = tr.csv(eff_path, dtype={"W": str, "O": str, "model": str, "item": str, "variant": str})
    eff["O"] = eff["O"].fillna("0")
    eff = eff[(eff["variant"] == "main") & np.isclose(eff["T"].astype(float), 1.0)]
    sc = tr.csv(rc.HUMAN / "arml_scales.csv", dtype={"item": str}).set_index("item")
    hp = tr.csv(rc.HUMAN / "pooled_sd_units.csv", dtype={"item": str}).set_index("item")
    sites = tr.csv(rc.HUMAN / "pooled_site_inputs.csv", dtype={"item": str})
    items = rc.items_in_order(tr, sorted(sd["item"].unique()))

    plt = rc.style()
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    ncols = a.cols
    nrows = int(np.ceil(len(items) / ncols))
    models_all = sorted(set(sd["model"]) - {"__median__"})
    n_m = len(models_all)
    site_pitch, y_pool, gap = 0.17, 0.0, 1.1
    fig, axes = plt.subplots(nrows, ncols, sharey=True, figsize=(rc.TEXT_WIDTH_CM * rc.CM, 15.0 * rc.CM),
                             gridspec_kw=dict(wspace=0.12, hspace=0.30, left=0.15, right=0.995, top=0.945, bottom=0.175))
    axes = np.atleast_2d(axes)
    n_sites = sites["site"].nunique()
    y_site0 = y_pool + 1.0
    y_model0 = y_site0 + n_sites * site_pitch + gap
    for k, it in enumerate(items):
        ax = axes[k // ncols, k % ncols]
        s = float(sc.at[it, "sd_within"])
        mu, mlo, mhi = (float(hp.at[it, c]) for c in ("mu_sd", "mu_sd_lo", "mu_sd_hi"))
        cp = float(ys[(ys["item"] == it) & (ys["yardstick"] == "c_p")]["y_est"].iloc[0])
        sh = float(ys[(ys["item"] == it) & (ys["yardstick"] == "S_H")]["y_est"].iloc[0])
        med = ys[(ys["item"] == it) & (ys["model"] == "__median__")].set_index("yardstick")
        ax.axvspan(mu - cp, mu + cp, facecolor=rc.SKY, alpha=0.30, edgecolor="none", zorder=0)
        # human: pooled diamond, S^H bar, interval
        ax.plot([mu - sh, mu + sh], [y_pool] * 2, color=rc.GREY, lw=3.2, alpha=0.55, solid_capstyle="butt", zorder=2)
        ax.plot([mlo, mhi], [y_pool] * 2, color=rc.INK, lw=0.9, zorder=3)
        ax.plot([mu], [y_pool], marker="D", ms=4.6, mfc=rc.INK, mec=rc.INK, ls="none", zorder=4)
        # sites (sample estimates), sorted by estimate
        st = sites[sites["item"] == it].copy()
        st["x"], st["se"] = st["yi"] / s, np.sqrt(st["vi"]) / s
        st = st.sort_values("x").reset_index(drop=True)
        ys_site = y_site0 + np.arange(len(st)) * site_pitch
        ax.hlines(ys_site, st["x"] - 1.96 * st["se"], st["x"] + 1.96 * st["se"], color=rc.GREEN, lw=0.35, alpha=0.8, zorder=2)
        ax.plot(st["x"], ys_site, ls="none", marker="o", ms=1.6, mfc=rc.GREEN, mec="none", zorder=3)
        # models (deterministic set-up effects)
        have = set(sd[(sd["item"] == it) & (sd["model"] != "__median__")]["model"])
        e = eff[eff["item"] == it]
        for j, m in enumerate(models_all):
            if m not in have:
                continue
            x = e[e["model"] == m]["delta"].to_numpy(float) / s
            y = y_model0 + j
            sdm = float(sd[(sd["item"] == it) & (sd["model"] == m)]["setup_sd"].iloc[0])
            ax.plot([x.mean() - sdm, x.mean() + sdm], [y, y], color=rc.VERMILION, lw=2.4, alpha=0.40, solid_capstyle="butt", zorder=2)
            ax.plot(x, [y] * len(x), ls="none", marker="o", ms=1.7, mfc=rc.VERMILION, mec="none", alpha=0.55, zorder=3)
            ax.plot([x.mean()] * 2, [y - 0.32, y + 0.32], color=rc.VERMILION, lw=1.0, zorder=4)
        ax.axhline(y_model0 - gap / 2, color=rc.GREY, lw=0.4, ls=":", zorder=1)
        ax.set_ylim(y_model0 + n_m - 0.2, y_pool - 0.8)
        lines = [f"{it} {rc.SHORT.get(it, '')}"]
        r_c, r_s = med.loc["c_p", "ratio"], med.loc["S_H", "ratio"]
        lines.append(f"s/c {r_c:.1f}, s/S {r_s:.1f}" + ("*" if bool(med.loc["S_H", "sh_lo_zero"]) else "") if np.isfinite(r_s) else f"s/c {r_c:.1f}")
        ax.set_title("\n".join(lines), fontsize=7, pad=2, linespacing=1.15)
        ax.tick_params(axis="x", labelsize=7, pad=1.5)
        ax.xaxis.set_major_locator(plt.MaxNLocator(3))
        ax.grid(axis="x", color="#E3E3E3", lw=0.4, zorder=0)
        ax.spines["left"].set_visible(k % ncols == 0)
        ax.tick_params(axis="y", left=(k % ncols == 0))
    ticks = [y_pool, y_site0 + (n_sites - 1) * site_pitch / 2] + [y_model0 + j for j in range(n_m)]
    labels = ["pooled human", f"Many Labs 1 sites\n(n = {n_sites})"] + [rc.short_model(m) for m in models_all]
    for r in range(nrows):
        axes[r, 0].set_yticks(ticks)
        axes[r, 0].set_yticklabels(labels, fontsize=7)
    for k in range(len(items), nrows * ncols):
        axes[k // ncols, k % ncols].set_visible(False)
    fig.supxlabel("Effect in Many Labs 1 SD units (effect divided by the item's within-site SD)", fontsize=7.5, y=0.105)
    h = [Line2D([], [], marker="D", color=rc.INK, ms=4.2, lw=0.9, label="pooled human effect, 95% interval"),
         Line2D([], [], color=rc.GREY, lw=3.2, alpha=0.55, label="pooled ± between-site SD S$^{\\rm H}$"),
         Patch(facecolor=rc.SKY, alpha=0.30, label="pooled ± single-site SE c (band)"),
         Line2D([], [], marker="o", color=rc.GREEN, ms=2.2, lw=0.6, label="Many Labs 1 site, 95% interval (sample estimate)"),
         Line2D([], [], marker="o", color=rc.VERMILION, ms=2.4, lw=0, label="set-up effect (deterministic, no interval)"),
         Line2D([], [], color=rc.VERMILION, lw=2.4, alpha=0.40, label="model mean ± its set-up SD s")]
    fig.legend(handles=h, loc="lower center", ncol=3, frameon=False, bbox_to_anchor=(0.5, 0.012), handletextpad=0.4, columnspacing=1.2)
    star = bool(ys[(ys['yardstick'] == 'S_H') & (ys['model'] == '__median__')]['sh_lo_zero'].any())
    fig.text(0.5, 0.004, r's = median over models of the set-up SD; c = single-site SE; S = between-site SD S$^{\rm H}$' + (r'; * the S$^{\rm H}$ interval reaches 0' if star else ''),
             ha='center', va='bottom', fontsize=7)
    outs = rc.save_figure(fig, out)
    rc.write_source(outs, "analysis/acme/figures/fig_yardsticks.py", gs, tr, extra=dict(effects_file=rc.rel(eff_path), items=items, models=models_all))


if __name__ == "__main__":
    main()

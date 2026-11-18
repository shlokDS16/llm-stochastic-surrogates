"""Near-deterministic cell diagnosis (statistician, 2026-10-16; POST-RESULTS analysis, results were seen).

    .venv/Scripts/python.exe -I analysis/pilot/diagnose_near_deterministic.py [--out runs/pilot-analysis/near-deterministic] [--B 2000]

For every model x paradigm x metric analysed under Amendment A1 + A1.10 (the same cells, validity rule, SD floor,
effect and split-half variance as analyze_pilot.py; the d vector is checked against analysis_<paradigm>.json) it writes
  cells.csv       one row per cell: n, means, SDs, pooled SD, floor, SD / floor, raw difference, g, v, contribution to SS
                  (P1: proportions, counts, continuity-correction flag)
  summary.csv     per model x paradigm x metric: distribution of pooled SD, counts at/below k x floor, share of the
                  between-cell sum of squares and the effect on dbar and S of the flagged cells
  floor_sens.csv  dbar and S (point estimates, moment formula, formula variance) under other SD floors
  decoupling.csv  how much of the spread of g is the spread of the denominator (counterfactual: same raw effect in every cell)
  rawscale.csv    the A1.6 route applied to every continuous grid: raw-unit (log-estimate or rating unit) mean difference,
                  dbar and S with TI intervals, human-SD units, and the manipulation-scaled anchoring index (P2)
  human_sd.csv    within-site pooled SD distribution of the 36 ML1 sites on the same metric scale, plus raw-unit S^H
  report.md       the same, as tables
Nothing here changes the preregistered estimator; it only reads the response files.
"""
import argparse
import itertools
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import estimators as E  # noqa: E402
from analyze_pilot import METRICS, sd_floor, load  # noqa: E402

MODELS = ["granite-3.3-2b-instruct", "granite-3.3-8b-instruct", "olmo2-7b-instruct", "qwen2.5-1.5b-instruct", "qwen2.5-7b-instruct", "olmo2-1b-instruct"]
PARADIGMS = ["P1", "P2a", "P2b", "P2c", "P2d", "P3", "P4"]
# anchors in the prompts (analysis/pilot/prompts/W0/*.yaml): low and high anchor values, response units
ANCHORS = {"P2a": (1500, 6000), "P2b": (200000, 5000000), "P2c": (2000, 45500), "P2d": (100, 50000)}
HUMAN_COLS = {  # paradigm -> (column, transform) giving the primary metric scale on the human file
    "P2a": ("y", np.log), "P2b": ("y", np.log), "P2c": ("y", np.log), "P2d": ("y", np.log), "P3": ("y", None), "P4": ("y", None)}  # P4 file y is already log(1+x)


def build_cells(model, paradigm, runs="runs/pilot"):
    """Same loading, A1.9 top-up, A1.10 validity and P2 positivity rule as analyze_pilot.analyze (primary options)."""
    rows = load(ROOT / runs / model / f"{paradigm}.jsonl")
    tfile = ROOT / runs / model / f"{paradigm}.topup512.jsonl"
    if tfile.exists():
        rep = {r["key"]: r for r in load(tfile)}
        rows = [rep.get(r["key"], r) for r in rows]
    for r in rows:
        r["valid"] = bool(r["valid"]) and r["finished"]
        if paradigm.startswith("P2") and r["valid"] and not (r["y"] is not None and r["y"] > 0):
            r["valid"] = False
    sampled = [r for r in rows if not r["greedy"]]
    Ws, Fs, Ts = (sorted({r[k] for r in sampled}) for k in ("W", "F", "T"))
    Os = sorted({r["O"] for r in sampled if r["O"]}) or [None]
    levels = [len(Ws), len(Fs), len(Ts)] + ([len(Os)] if Os != [None] else [])
    factors = ["W", "F", "T"] + (["O"] if Os != [None] else [])
    cr = {}
    for r in sampled:
        key = (Ws.index(r["W"]), Fs.index(r["F"]), Ts.index(r["T"])) + ((Os.index(r["O"]),) if Os != [None] else ())
        cr.setdefault(key, []).append(r)
    names = dict(W=Ws, F=Fs, T=Ts, O=Os)
    return cr, levels, factors, names


def cell_arms(cr, key, tf):
    rs = [r for r in cr.get(key, []) if r["valid"]]
    y1 = np.array([r["y"] for r in rs if r["x"] == 1], float)
    y0 = np.array([r["y"] for r in rs if r["x"] == 0], float)
    return tf(y1), tf(y0)


def moment_s(d, v):
    d, v = np.asarray(d, float), np.asarray(v, float)
    return float(E.spread_s2(d, v))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="runs/pilot-analysis/near-deterministic")
    ap.add_argument("--B", type=int, default=2000)
    ap.add_argument("--runs", default="runs/pilot")
    ap.add_argument("--multiples", default="1,2,5", help="flag cells with pooled SD <= k x floor")
    a = ap.parse_args()
    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    mult = [float(x) for x in a.multiples.split(",")]
    rng = np.random.default_rng(20261016)

    # ---------------- human side: pooled within-site SD on the primary metric scale, raw-unit S^H
    hum_rows, human_sigma, human_raw = [], {}, {}
    for p, (col, tf) in HUMAN_COLS.items():
        df = pd.read_csv(ROOT / "data/processed/ml1" / f"{p}.csv")
        sds, cells = [], {}
        for i, (s, g) in enumerate(df.groupby("site", sort=True)):
            y1, y0 = g.loc[g.x == 1, col].to_numpy(float), g.loc[g.x == 0, col].to_numpy(float)
            if tf is not None:
                y1, y0 = tf(y1[y1 > 0]), tf(y0[y0 > 0])
            n1, n0 = len(y1), len(y0)
            sds.append(np.sqrt(((n1 - 1) * y1.var(ddof=1) + (n0 - 1) * y0.var(ddof=1)) / (n1 + n0 - 2)))
            cells[(i,)] = (y1, y0)
        sds = np.array(sds)
        # pooled over sites (df-weighted): the human within-condition SD on this scale
        dfs = np.array([len(c[0]) + len(c[1]) - 2 for c in cells.values()])
        sig = float(np.sqrt(np.sum(dfs * sds ** 2) / dfs.sum()))
        human_sigma[p] = sig
        r = E.estimate2(cells, E.Design(["site"], [len(cells)]), "diff", rng=rng, B=a.B, K=200, var_method="splithalf", intervals=("ti_boot",), term_intervals=False)
        iv = r["intervals"]["ti_boot"]
        human_raw[p] = dict(dbar=r["dbar"], dbar_ci=r["dbar_ci"], S=r["S"], S_ci=iv["S"], k=len(cells))
        gs = np.array([E.effect("cont", y1, y0, 0.0)[0] for (y1, y0) in cells.values()])
        hum_rows.append(dict(paradigm=p, k_sites=len(cells), g_min=gs.min(), g_max=gs.max(), g_mean=gs.mean(), sd_min=sds.min(), sd_p05=np.quantile(sds, .05), sd_p25=np.quantile(sds, .25), sd_median=np.median(sds),
                             sd_max=sds.max(), sd_pooled=sig, raw_dbar=r["dbar"], raw_dbar_lo=r["dbar_ci"][0], raw_dbar_hi=r["dbar_ci"][1],
                             raw_S=r["S"], raw_S_lo=iv["S"][0], raw_S_hi=iv["S"][1]))
    p1h = pd.read_csv(ROOT / "data/processed/ml1/P1.csv")
    cells = {(i,): (g.loc[g.x == 1, "y"].to_numpy(float), g.loc[g.x == 0, "y"].to_numpy(float)) for i, (s_, g) in enumerate(p1h.groupby("site", sort=True))}
    r = E.estimate2(cells, E.Design(["site"], [len(cells)]), "diff", rng=rng, B=a.B, K=200, var_method="splithalf", intervals=("ti_boot",), term_intervals=False)
    human_raw["P1"] = dict(dbar=r["dbar"], dbar_ci=r["dbar_ci"], S=r["S"], S_ci=r["intervals"]["ti_boot"]["S"], k=len(cells))
    hum = pd.DataFrame(hum_rows)
    hum.to_csv(out / "human_sd.csv", index=False)

    cell_rows, sum_rows, fl_rows, dec_rows, raw_rows = [], [], [], [], []
    for model in MODELS:
        for p in PARADIGMS:
            jf = ROOT / a.runs / model / f"analysis_{p}.json"
            if not jf.exists():
                continue
            ana = json.loads(jf.read_text(encoding="utf8"))
            cr, levels, factors, names = build_cells(model, p, a.runs)
            design = E.Design(factors, levels)
            keys = list(itertools.product(*[range(L) for L in levels]))
            for mid, kind, tf, label in METRICS[p]:
                res = ana["metrics"].get(mid, {})
                sh = res.get("split_half")
                if sh is None or res.get("scale") != "standardised":
                    continue
                floor = sd_floor(p, mid) if kind == "cont" else 0.0
                cells = {k: cell_arms(cr, k, tf if kind == "cont" else (lambda y: y)) for k in keys}
                d = np.array([E.effect(kind, *cells[k], floor)[0] for k in keys])
                assert np.allclose(d, np.array(sh["d"]), atol=1e-9), (model, p, mid, "cell effects differ from analysis json")
                v = np.array(sh["v"])
                C = len(keys)
                dbar = d.mean()
                ss_c = (d - dbar) ** 2
                recs = []
                for i, k in enumerate(keys):
                    y1, y0 = cells[k]
                    n1, n0 = len(y1), len(y0)
                    rec = dict(model=model, paradigm=p, metric=mid, cell="|".join(map(str, k)), n1=n1, n0=n0, d=d[i], v=v[i], ss_contrib=ss_c[i])
                    if kind == "cont":
                        s1, s0 = y1.var(ddof=1), y0.var(ddof=1)
                        sp = float(np.sqrt(((n1 - 1) * s1 + (n0 - 1) * s0) / (n1 + n0 - 2)))
                        rec.update(m1=y1.mean(), m0=y0.mean(), sd1=np.sqrt(s1), sd0=np.sqrt(s0), sp=sp, floor=floor, sp_over_floor=sp / floor,
                                   at_floor=sp <= floor, raw_diff=y1.mean() - y0.mean(), uniq1=len(set(y1)), uniq0=len(set(y0)),
                                   g_nofloor=((y1.mean() - y0.mean()) / sp * (1 - 3 / (4 * (n1 + n0 - 2) - 1))) if sp > 0 else np.nan)
                    else:
                        k1, k0 = int(y1.sum()), int(y0.sum())
                        zero = (k1 == 0) or (k1 == n1) or (k0 == 0) or (k0 == n0)
                        rec.update(p1=k1 / n1, p0=k0 / n0, k1=k1, k0=k0, zero_count_cell=zero, near_zero_or_one=(min(k1 / n1, 1 - k1 / n1, k0 / n0, 1 - k0 / n0) <= 0.05),
                                   sp=np.nan, floor=np.nan, sp_over_floor=np.nan, at_floor=False)
                    recs.append(rec)
                cell_rows += recs
                cdf = pd.DataFrame(recs)
                row = dict(model=model, paradigm=p, metric=mid, C=C, scale=label, dbar=dbar, S=ana["metrics"][mid]["S"], S2=moment_s(d, v), max_abs_d=np.abs(d).max())
                if kind == "cont":
                    sp = cdf.sp.to_numpy()
                    row.update(sp_min=sp.min(), sp_p10=np.quantile(sp, .1), sp_p25=np.quantile(sp, .25), sp_median=np.median(sp), sp_p75=np.quantile(sp, .75), sp_max=sp.max(),
                               floor=floor, n_at_floor=int((sp <= floor).sum()))
                    for kk in mult:
                        row[f"n_le_{kk:g}xfloor"] = int((sp <= kk * floor).sum())
                    # human-defined threshold: lowest within-site pooled SD of the 36 ML1 sites (same scale)
                    if p in set(hum.paradigm):
                        hmin = float(hum.set_index("paradigm").loc[p, "sd_min"])
                        row["human_site_sd_min"] = hmin
                        row["n_below_human_site_min"] = int((sp < hmin).sum())
                    flag = sp <= 2 * floor
                    flagname = "<=2xfloor"
                else:
                    flag = cdf.zero_count_cell.to_numpy()
                    flagname = "zero_count_cell"
                    row.update(n_zero_count_cells=int(flag.sum()), n_near_0_or_1=int(cdf.near_zero_or_one.sum()), n_cells_p1_eq_p0_equal_extremes=0,
                               v_min=v.min(), v_max=v.max(), n_v_ge_4=int((v >= 4).sum()))
                row["flag_rule"] = flagname
                row["n_flagged"] = int(flag.sum())
                row["share_ss_flagged"] = float(ss_c[flag].sum() / ss_c.sum()) if ss_c.sum() > 0 else np.nan
                if flag.any() and (~flag).sum() >= 2:
                    dk, vk = d[~flag], v[~flag]
                    row.update(dbar_excl=float(dk.mean()), S_excl=float(np.sqrt(max(0, moment_s(dk, vk)))), dbar_flagged=float(d[flag].mean()))
                    # S that would remain if the flagged cells took the mean of the unflagged ones (pure removal of their spread)
                    d2 = d.copy()
                    d2[flag] = dk.mean()
                    row["S_flagged_set_to_rest_mean"] = float(np.sqrt(max(0, moment_s(d2, v))))
                sum_rows.append(row)

                if kind == "binary":
                    k1s = np.array([int(cells[k][0].sum()) for k in keys]); n1s = np.array([len(cells[k][0]) for k in keys])
                    k0s = np.array([int(cells[k][1].sum()) for k in keys]); n0s = np.array([len(cells[k][1]) for k in keys])
                    for cc in [0.1, 0.25, 0.5, 1.0]:
                        # same rule as the pipeline (correction added to all four counts when any count is zero), other correction sizes
                        a_, b_, c_, d_ = k1s.astype(float), (n1s - k1s).astype(float), k0s.astype(float), (n0s - k0s).astype(float)
                        z = (a_ == 0) | (b_ == 0) | (c_ == 0) | (d_ == 0)
                        kk = np.where(z, cc, 0.0)
                        a_, b_, c_, d_ = a_ + kk, b_ + kk, c_ + kk, d_ + kk
                        dd = np.log(a_ * d_ / (b_ * c_)); vv = 1 / a_ + 1 / b_ + 1 / c_ + 1 / d_
                        fl_rows.append(dict(model=model, paradigm=p, metric=mid, floor=f"cc={cc}", dbar=dd.mean(), S=float(np.sqrt(max(0, moment_s(dd, vv)))), max_abs_g=np.abs(dd).max()))
                    r_ = E.estimate2(cells, design, "diff", rng=rng, B=a.B, K=200, var_method="splithalf", intervals=("ti_boot",), term_intervals=False)
                    iv = r_["intervals"]["ti_boot"]
                    raw_rows.append(dict(model=model, paradigm=p, unit="risk difference (sure option)", dbar_raw=r_["dbar"], dbar_raw_lo=r_["dbar_ci"][0], dbar_raw_hi=r_["dbar_ci"][1],
                                         S_raw=r_["S"], S_raw_lo=iv["S"][0], S_raw_hi=iv["S"][1], S2_lower_gt0=bool(iv["S2"][0] > 0), sign_stability_raw=r_["sign_stability"],
                                         g_dbar=dbar, g_S=row["S"], human_raw_dbar=human_raw["P1"]["dbar"], human_raw_S=human_raw["P1"]["S"],
                                         human_raw_S_lo=human_raw["P1"]["S_ci"][0], human_raw_S_hi=human_raw["P1"]["S_ci"][1]))
                if kind == "cont":
                    # floor sensitivity (point estimates; formula variance, moment estimator)
                    for fl in [0.05, 0.1, 0.2, 0.4, 0.8, 1.6]:
                        dd, vv = [], []
                        for k in keys:
                            g_, v_ = E.effect("cont", *cells[k], fl)
                            dd.append(g_); vv.append(v_)
                        dd, vv = np.array(dd), np.array(vv)
                        fl_rows.append(dict(model=model, paradigm=p, metric=mid, floor=fl, dbar=dd.mean(), S=float(np.sqrt(max(0, moment_s(dd, vv)))), max_abs_g=np.abs(dd).max()))
                    # decoupling: the raw difference and the pooled SD vary separately across cells
                    rd = cdf.raw_diff.to_numpy()
                    sp_f = np.maximum(cdf.sp.to_numpy(), floor)
                    J = 1 - 3 / (4 * (cdf.n1.to_numpy() + cdf.n0.to_numpy() - 2) - 1)
                    dnum = J * rd.mean() / sp_f   # same raw effect (the grid mean) in every cell: only the denominator varies
                    dden = J * rd / np.sqrt(np.mean(sp_f ** 2))   # a common SD (root mean square over cells): only the raw effect varies
                    dec_rows.append(dict(model=model, paradigm=p, metric=mid, S_g=row["S"],
                                         raw_dbar=rd.mean(), raw_spread_sd=np.sqrt(np.mean((rd - rd.mean()) ** 2)),
                                         S_if_raw_effect_identical_in_all_cells=float(np.sqrt(np.mean((dnum - dnum.mean()) ** 2))),
                                         S_if_common_sd=float(np.sqrt(np.mean((dden - dden.mean()) ** 2))),
                                         corr_log_sp_vs_log_abs_g=float(np.corrcoef(np.log(sp_f), np.log(np.abs(d) + 1e-9))[0, 1]),
                                         sp_ratio_max_min=float(sp_f.max() / sp_f.min())))
                    # A1.6 route (raw difference in response units of the metric scale) for every continuous grid
                    if mid == "primary":
                        r_ = E.estimate2(cells, design, "diff", rng=rng, B=a.B, K=200, var_method="splithalf", intervals=("ti_boot",), term_intervals=False)
                        iv = r_["intervals"]["ti_boot"]
                        rr = dict(model=model, paradigm=p, unit="log-estimate" if p.startswith("P2") or p == "P4" else "rating points",
                                  dbar_raw=r_["dbar"], dbar_raw_lo=r_["dbar_ci"][0], dbar_raw_hi=r_["dbar_ci"][1], S_raw=r_["S"], S_raw_lo=iv["S"][0], S_raw_hi=iv["S"][1],
                                  S2_lower_gt0=bool(iv["S2"][0] > 0), sign_stability_raw=r_["sign_stability"],
                                  g_dbar=dbar, g_S=row["S"])
                        if p in human_sigma:
                            sig = human_sigma[p]
                            rr.update(human_sd_pooled=sig, dbar_in_human_sd=r_["dbar"] / sig, dbar_in_human_sd_lo=r_["dbar_ci"][0] / sig, dbar_in_human_sd_hi=r_["dbar_ci"][1] / sig,
                                      S_in_human_sd=r_["S"] / sig, S_in_human_sd_lo=iv["S"][0] / sig, S_in_human_sd_hi=iv["S"][1] / sig,
                                      human_raw_dbar=human_raw[p]["dbar"], human_raw_S=human_raw[p]["S"], human_raw_S_lo=human_raw[p]["S_ci"][0], human_raw_S_hi=human_raw[p]["S_ci"][1])
                        if p in ANCHORS:
                            lr = float(np.log(ANCHORS[p][1] / ANCHORS[p][0]))
                            rr.update(log_anchor_ratio=lr, index_dbar=r_["dbar"] / lr, index_dbar_lo=r_["dbar_ci"][0] / lr, index_dbar_hi=r_["dbar_ci"][1] / lr,
                                      index_S=r_["S"] / lr, index_S_lo=iv["S"][0] / lr, index_S_hi=iv["S"][1] / lr,
                                      human_index_dbar=human_raw[p]["dbar"] / lr, human_index_S=human_raw[p]["S"] / lr,
                                      human_index_S_lo=human_raw[p]["S_ci"][0] / lr, human_index_S_hi=human_raw[p]["S_ci"][1] / lr)
                        raw_rows.append(rr)
            print("done", model, p, flush=True)

    cdf = pd.DataFrame(cell_rows)
    sdf = pd.DataFrame(sum_rows)
    cdf.to_csv(out / "cells.csv", index=False)
    sdf.to_csv(out / "summary.csv", index=False)
    pd.DataFrame(fl_rows).to_csv(out / "floor_sens.csv", index=False)
    pd.DataFrame(dec_rows).to_csv(out / "decoupling.csv", index=False)
    pd.DataFrame(raw_rows).to_csv(out / "rawscale.csv", index=False)
    make_rules_and_report(out, cdf, sdf, pd.DataFrame(raw_rows), pd.DataFrame(dec_rows), pd.DataFrame(fl_rows), hum)
    print("written to", out)


def make_rules_and_report(out, cdf, sdf, raw, dec, fl, hum):
    """Candidate switching rules (POST-RESULTS; none is preregistered) and a markdown report built from the CSVs."""
    c = cdf[(cdf.metric == "primary") & (cdf.paradigm != "P1")].copy()
    c["fb"] = c.sp <= c.floor
    c["le2"] = c.sp <= 2 * c.floor
    c["fb_signal"] = c.fb & (c.raw_diff.abs() > c.floor)
    c["le2_signal"] = c.le2 & (c.raw_diff.abs() > c.floor)
    g = c.groupby(["model", "paradigm"]).agg(C=("d", "size"), n_le1=("fb", "sum"), n_le2=("le2", "sum"), n_le1_signal=("fb_signal", "sum"), n_le2_signal=("le2_signal", "sum"),
                                             max_abs_g=("d", lambda x: x.abs().max()), max_abs_raw=("raw_diff", lambda x: x.abs().max()),
                                             sp_ratio=("sp", lambda x: np.nan)).reset_index()
    sp_ratio = c.assign(spf=np.maximum(c.sp, c.floor)).groupby(["model", "paradigm"]).spf.agg(lambda x: x.max() / x.min()).reset_index(name="sp_ratio")
    g = g.drop(columns="sp_ratio").merge(sp_ratio, on=["model", "paradigm"])
    g = g.merge(raw[["model", "paradigm", "g_dbar", "dbar_raw", "g_S", "S_raw"]], on=["model", "paradigm"])
    g["sign_disagree"] = np.sign(g.g_dbar) != np.sign(g.dbar_raw)
    g["max_g_human"] = g.paradigm.map(hum.set_index("paradigm").g_max.abs().combine(hum.set_index("paradigm").g_min.abs(), max))
    g["R1_any_floor_cell_with_signal"] = g.n_le1_signal >= 1
    g["R2_share_le2floor_ge25pct"] = g.n_le2 / g.C >= 0.25
    g["R3_share_le2floor_with_signal_ge25pct"] = g.n_le2_signal / g.C >= 0.25
    g["R4_sp_ratio_ge_10"] = g.sp_ratio >= 10
    g["R5_max_abs_g_gt_2x_human_max"] = g.max_abs_g > 2 * g.max_g_human
    g.to_csv(out / "rules.csv", index=False)
    P1 = sdf[(sdf.paradigm == "P1")][["model", "C", "n_zero_count_cells", "n_near_0_or_1", "max_abs_d", "dbar", "S"]].copy()
    P1["share_zero_count_cells"] = P1.n_zero_count_cells / P1.C
    P1.to_csv(out / "p1_zero_cells.csv", index=False)
    pc = cdf[(cdf.paradigm == "P1") & (cdf.metric == "primary")]
    arm_rows = []
    for mname, g_ in pc.groupby("model"):
        arms = np.concatenate([g_.p1.to_numpy(), g_.p0.to_numpy()])
        arm_rows.append(dict(model=mname, arms=len(arms), p_eq_0=int((arms == 0).sum()), p_eq_1=int((arms == 1).sum()), p_in_0_to_005=int(((arms > 0) & (arms <= 0.05)).sum()),
                             p_in_095_to_1=int(((arms >= 0.95) & (arms < 1)).sum()), p_middle=int(((arms > 0.05) & (arms < 0.95)).sum()),
                             cells_complete_separation=int((((g_.k1 == g_.n1) & (g_.k0 == 0)) | ((g_.k1 == 0) & (g_.k0 == g_.n0))).sum()),
                             cells_both_arms_constant_equal=int((((g_.k1 == g_.n1) & (g_.k0 == g_.n0)) | ((g_.k1 == 0) & (g_.k0 == 0))).sum()),
                             cells_with_correction=int(g_.zero_count_cell.sum()), cells=len(g_)))
    pd.DataFrame(arm_rows).to_csv(out / "p1_arm_proportions.csv", index=False)

    def md(df, fmt=3):
        cols = [str(c_) for c_ in df.columns]
        lines = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
        for _, r in df.iterrows():
            lines.append("| " + " | ".join((f"{v:.{fmt}f}" if isinstance(v, (float, np.floating)) else str(v)) for v in r) + " |")
        return chr(10).join(lines)

    prim = sdf[(sdf.metric == "primary") & (sdf.paradigm != "P1")][["model", "paradigm", "C", "dbar", "S", "max_abs_d", "sp_min", "sp_median", "sp_max", "floor", "n_at_floor", "n_le_2xfloor", "n_le_5xfloor",
                                                                      "n_below_human_site_min", "share_ss_flagged", "dbar_excl", "S_excl"]]
    txt = ["# Near-deterministic cells: diagnosis tables (generated by analysis/pilot/diagnose_near_deterministic.py; POST-RESULTS)", "",
           "Flag for the contribution columns: continuous grids pooled SD <= 2 x floor (floor 0.2 on log scales, 0.289 for P3 ratings); P1 cells with a zero count.",
           "`sp` = pooled within-cell SD of the metric scale before the floor; `share_ss_flagged` = share of sum_c (d_c - dbar)^2 from flagged cells; `*_excl` = dbar and S over unflagged cells only (moment formula, stored v).", "",
           "## A. Continuous grids (primary metric)", md(prim), "",
           "## B. P1 (log OR, 0.5 continuity correction when a count is zero)", md(P1), "", "Arm proportions of sure-option choices (2 arms per cell) and complete-separation cells (both arms constant, unequal):", md(pd.DataFrame(arm_rows)), "",
           "## C. Candidate rules: which grids each would switch to the raw scale", md(g[["model", "paradigm", "C", "n_le1", "n_le2", "n_le1_signal", "n_le2_signal", "sp_ratio", "max_abs_g", "max_g_human", "sign_disagree",
                                                                                      "R1_any_floor_cell_with_signal", "R2_share_le2floor_ge25pct", "R3_share_le2floor_with_signal_ge25pct", "R4_sp_ratio_ge_10", "R5_max_abs_g_gt_2x_human_max"]]), "",
           "Rule counts (grids of 30 continuous): " + ", ".join(f"{k}={int(g[k].sum())}" for k in g.columns if k.startswith("R")), "",
           "## D. Standardised vs raw-unit result (A1.6 route applied to every continuous grid; P1 = risk difference)", md(raw[[c_ for c_ in ["model", "paradigm", "unit", "g_dbar", "dbar_raw", "dbar_raw_lo", "dbar_raw_hi", "g_S", "S_raw", "S_raw_lo", "S_raw_hi", "human_raw_dbar", "human_raw_S", "human_raw_S_lo", "human_raw_S_hi"] if c_ in raw.columns]]), "",
           "## E. Anchoring index (raw log-estimate difference / log anchor ratio), LLM vs ML1 sites", md(raw[raw.paradigm.str.startswith("P2")][["model", "paradigm", "log_anchor_ratio", "index_dbar", "index_dbar_lo", "index_dbar_hi", "index_S", "index_S_lo", "index_S_hi", "human_index_dbar", "human_index_S", "human_index_S_lo", "human_index_S_hi"]]), "",
           "## F. Decoupling of the spread of g from the spread of the raw effect", md(dec[dec.metric == "primary"][["model", "paradigm", "S_g", "raw_spread_sd", "S_if_raw_effect_identical_in_all_cells", "S_if_common_sd", "sp_ratio_max_min"]]), "",
           "## G. Floor sensitivity of dbar and S (primary; P1 rows give continuity-correction sensitivity)", md(fl[(fl.metric == "primary") & (fl.paradigm != "P1")].assign(floor=lambda x: x.floor.astype(float)).pivot_table(index=["model", "paradigm"], columns="floor", values="S").reset_index()) + chr(10) * 2 + "P1: S under continuity correction size" + chr(10) * 2 + md(fl[fl.paradigm == "P1"].pivot_table(index="model", columns="floor", values="S").reset_index()), "",
           "## H. ML1 sites: within-site pooled SD on the same scale, g range, raw-unit S^H", md(hum), ""]
    (out / "report.md").write_text(chr(10).join(txt), encoding="utf8")


if __name__ == "__main__":
    main()

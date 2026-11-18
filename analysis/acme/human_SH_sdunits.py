"""Between-site SD of Many Labs 1 effects on the scale of the Arm L effect Delta, in ML1-SD units (erratum E5).

Site-level raw differences (kind 'diff') on Delta's scale, the same estimator and interval as the human runs
(analysis/human_ml1/acme_items.py stage_spread: estimate2, splithalf variance, K 200, B 2000, test-inversion bootstrap),
then divided by the item's sd_within from runs/human-ml1-acme/arml_scales.csv. Human data only; no model output is read.
Output: runs/human-ml1-acme/SH_sd_units.csv and .json.

Erratum E6 item 2 (added, `pooled()`): pooled human effect on the same scale. REML random-effects mean of the site-level raw
differences (x1 minus x0, the orientation of Delta = outcome(x1) - outcome(x0)), per-site sampling variance s1^2/n1 + s0^2/n0
(binary 0/1 items: p1(1-p1)/n1 + p0(1-p0)/n0), Wald 95 % interval from the REML fit (mu +- 1.96 se, no Hartung-Knapp), tau-hat on
the raw scale, and all three divided by sd_within. Sibling outputs, so SH_sd_units.csv/.json stay byte-identical:
runs/human-ml1-acme/pooled_sd_units.csv/.json and pooled_site_inputs.csv. No random numbers are used by the pooled part.
The processed ml1 columns are already in Delta's orientation (AF y = anti-speech answer; QA y = 10 - raw; P3 y = 9 definitely go);
check_orientation asserts this against runs/human-ml1-acme/canonical_signs.csv.
"""
import csv
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "analysis" / "pilot"))
import estimators as E  # noqa: E402

SEED = 20261109
ITEMS = ["P1", "P2a", "P2b", "P2c", "P2d", "P3", "P4", "AF", "QA", "NR"]
COL = {"P2a": "y_log", "P2b": "y_log", "P2c": "y_log", "P2d": "y_log", "P4": "y_log"}   # others: y
OUT = ROOT / "runs" / "human-ml1-acme"


def reml(yi, vi):
    """REML estimate of the random-effects mean (tau2 >= 0, truncated at 0) by root-finding on the REML score; Wald se."""
    from scipy.optimize import brentq
    yi, vi = np.asarray(yi, float), np.asarray(vi, float)

    def fit(t2):
        w = 1.0 / (vi + t2)
        return w, np.sum(w * yi) / np.sum(w)

    def score(t2):   # d REML loglik / d tau2 = 0.5 * (-sum w + sum w^2 (y - mu)^2 + sum w^2 / sum w)
        w, mu = fit(t2)
        return 0.5 * (-np.sum(w) + np.sum(w ** 2 * (yi - mu) ** 2) + np.sum(w ** 2) / np.sum(w))

    if score(0.0) <= 0:
        t2 = 0.0
    else:
        hi = max(1.0, float(np.var(yi)) * 10)
        while score(hi) > 0:
            hi *= 10
        t2 = brentq(score, 0.0, hi, xtol=1e-15, rtol=1e-14, maxiter=500)
    w, mu = fit(t2)
    se = 1.0 / np.sqrt(np.sum(w))
    return dict(mu=float(mu), se=float(se), tau2=float(t2), lo=float(mu - 1.959963984540054 * se), hi=float(mu + 1.959963984540054 * se))


def site_effects(p):
    """Per site: n1, n0, raw difference (x1 minus x0) and its sampling variance (binary: p(1-p)/n; else s^2/n with ddof 1)."""
    df = pd.read_csv(ROOT / "data" / "processed" / "ml1" / f"{p}.csv")
    col = COL.get(p, "y")
    df = df[np.isfinite(df[col].astype(float))]
    binary = p in ("P1", "AF", "NR")
    out = []
    for s, g in df.groupby("site", sort=True):
        a, b = g.loc[g.x == 1, col].to_numpy(float), g.loc[g.x == 0, col].to_numpy(float)
        m1, m0 = a.mean(), b.mean()
        if binary:
            v = m1 * (1 - m1) / len(a) + m0 * (1 - m0) / len(b)
        else:
            v = a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b)
        out.append((s, len(a), len(b), m1 - m0, v))
    return col, out


CONVENTION = {
    "P1": "risk difference of P(sure option), gain frame (x1) minus loss frame (x0); canonical sign +1",
    "P2a": "difference of mean log x, high anchor (x1) minus low anchor (x0); +1",
    "P2b": "difference of mean log x, high anchor minus low anchor; +1",
    "P2c": "difference of mean log x, high anchor minus low anchor; +1",
    "P2d": "difference of mean log x, high anchor minus low anchor; +1",
    "P3": "rating points, 9 = definitely go (not reversed), paid ticket (x1) minus free ticket (x0); +1",
    "P4": "difference of mean log(1 + x), three 6s (x1) minus one 3 and two 6s (x0); +1",
    "AF": "risk difference of the anti-speech answer (Yes to forbid at x1, No to allow at x0; column y, not the raw-Yes column y_yes), forbid minus allow; canonical sign -1 (negative = forbid wording lowers the anti-speech share)",
    "QA": "rating points, 9 = strongly agree (y = 10 - raw ML1 value; raw 1 = strongly agree), Washington (x1) minus bin Laden (x0); +1",
    "NR": "risk difference of Yes to the US question, other-country question first (x1) minus US question first (x0); +1",
}


def check_orientation(p, mu):
    """Sign of the pooled raw effect must equal canonical_sign; for AF, column y must be the anti-speech answer."""
    cs = {r["item"]: int(r["canonical_sign"]) for r in csv.DictReader(open(OUT / "canonical_signs.csv", encoding="utf8"))}
    ok = int(np.sign(mu)) == cs[p]
    if p == "AF":
        d = pd.read_csv(ROOT / "data" / "processed" / "ml1" / "AF.csv")
        ok = ok and bool(np.all(d.loc[d.x == 1, "y"] == d.loc[d.x == 1, "y_yes"])) and bool(np.all(d.loc[d.x == 0, "y"] == 1 - d.loc[d.x == 0, "y_yes"]))
    return cs[p], ok


def pooled():
    sd = {r["item"]: float(r["sd_within"]) for r in csv.DictReader(open(OUT / "arml_scales.csv", encoding="utf8"))}
    rows, res, inp = [], {}, []
    for p in ITEMS:
        col, se_ = site_effects(p)
        yi, vi = [e[3] for e in se_], [e[4] for e in se_]
        r = reml(yi, vi)
        tau = float(np.sqrt(r["tau2"]))
        sign, ok = check_orientation(p, r["mu"])
        z = sd[p]
        res[p] = dict(column=col, sites=len(se_), sites_vi_zero=int(sum(v == 0 for v in vi)), mu_raw=r["mu"], se_raw=r["se"], lo_raw=r["lo"], hi_raw=r["hi"],
                      tau2_raw=r["tau2"], tau_raw=tau, sd_within=z, mu_sd=r["mu"] / z, lo_sd=r["lo"] / z, hi_sd=r["hi"] / z, tau_sd=tau / z,
                      canonical_sign=sign, orientation_ok=ok, convention=CONVENTION[p])
        rows.append([p, col, len(se_), f"{r['mu']:.10g}", f"{r['lo']:.10g}", f"{r['hi']:.10g}", f"{tau:.10g}", f"{z:.10g}",
                     f"{r['mu'] / z:.10g}", f"{r['lo'] / z:.10g}", f"{r['hi'] / z:.10g}", f"{tau / z:.10g}", sign, ok, CONVENTION[p]])
        inp += [[p, s, n1, n0, repr(float(d)), repr(float(v))] for s, n1, n0, d, v in se_]
        print("pooled", p, rows[-1][8:12], "orientation_ok", ok, flush=True)
    with open(OUT / "pooled_sd_units.csv", "w", newline="", encoding="utf8") as f:
        w = csv.writer(f)
        w.writerow(["item", "column", "sites", "mu_raw", "mu_raw_lo", "mu_raw_hi", "tau_raw", "sd_within", "mu_sd", "mu_sd_lo", "mu_sd_hi", "tau_sd",
                    "canonical_sign", "orientation_ok", "convention"])
        w.writerows(rows)
    with open(OUT / "pooled_site_inputs.csv", "w", newline="", encoding="utf8") as f:
        w = csv.writer(f)
        w.writerow(["item", "site", "n1", "n0", "yi", "vi"])
        w.writerows(inp)
    res["_meta"] = dict(estimator="REML random-effects mean (own implementation: root-finding on the REML score; checked against metafor::rma REML, pooled_check.txt)",
                        interval="Wald, mu +- 1.96 se, se = 1/sqrt(sum 1/(vi + tau2)); no Hartung-Knapp", rule="erratum E6 item 2")
    (OUT / "pooled_sd_units.json").write_text(json.dumps(res, indent=1), encoding="utf8")


def main():
    sd = {r["item"]: float(r["sd_within"]) for r in csv.DictReader(open(OUT / "arml_scales.csv", encoding="utf8"))}
    rng = np.random.default_rng(SEED)
    rows, res = [], {}
    for p in ITEMS:
        df = pd.read_csv(ROOT / "data" / "processed" / "ml1" / f"{p}.csv")
        col = COL.get(p, "y")
        df = df[np.isfinite(df[col].astype(float))]
        cells = {}
        for i, (s, g) in enumerate(df.groupby("site", sort=True)):
            cells[(i,)] = (g.loc[g.x == 1, col].to_numpy(float), g.loc[g.x == 0, col].to_numpy(float))
        design = E.Design(["site"], [len(cells)])
        r = E.estimate2(cells, design, "diff", rng=rng, B=2000, K=200, var_method="splithalf", sd_floor=0.0,
                        intervals=("ti_boot",), term_intervals=False)
        if r["status"] != "ok":
            res[p] = {"status": r["status"]}
            continue
        iv = r["intervals"]["ti_boot"]["S"]
        s_raw, lo, hi = float(r["S"]), float(iv[0]), float(iv[1])
        res[p] = dict(column=col, sites=len(cells), S2_untruncated_raw=float(r["S2_untruncated"]), S_raw=s_raw, TI_S_raw=[lo, hi],
                      sd_within=sd[p], S_sd=s_raw / sd[p], TI_S_sd=[lo / sd[p], hi / sd[p]])
        rows.append([p, col, len(cells), f"{s_raw:.6g}", f"{lo:.6g}", f"{hi:.6g}", f"{sd[p]:.6g}",
                     f"{s_raw / sd[p]:.6g}", f"{lo / sd[p]:.6g}", f"{hi / sd[p]:.6g}"])
        print(p, rows[-1][7:], flush=True)
    with open(OUT / "SH_sd_units.csv", "w", newline="", encoding="utf8") as f:
        w = csv.writer(f)
        w.writerow(["item", "column", "sites", "S_raw", "S_raw_lo", "S_raw_hi", "sd_within", "S_sd", "S_sd_lo", "S_sd_hi"])
        w.writerows(rows)
    res["_meta"] = dict(seed=SEED, estimator="estimators.estimate2 kind=diff splithalf K=200 B=2000 ti_boot", rule="erratum E5")
    (OUT / "SH_sd_units.json").write_text(json.dumps(res, indent=1), encoding="utf8")
    pooled()


if __name__ == "__main__":
    main()

"""Diagnosis of the +0.07 bias of S-hat for skewed outcomes (statistician, 2026-10-16).

    .venv/Scripts/python.exe -I analysis/pilot/diagnose_variance.py [--reps 4000] [--n 50] [--delta 0.5]

For one cell (two arms of n responses, true standardised effect delta) it compares, by Monte Carlo, the TRUE sampling
variance of d (Hedges g or log OR) with the mean of three estimates of it: the normal-theory formula, the response-level
bootstrap variance (B = 400), and split-half variance (K = 100). The moment estimator of the finite-cell spread subtracts
(C-1)/C * sum_c v_c, so a mean estimate below the truth leaves noise in S2hat: bias(S2hat) = (C-1)/C * (true - mean estimate)
(in units of S^2 per cell mean). Also reports the bias of d itself (E[d] - delta), which scales the spread.
"""
import argparse
import sys
import time
from concurrent.futures import ProcessPoolExecutor

import numpy as np

sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parent))
import estimators as E  # noqa: E402
import sim_common as SC  # noqa: E402


def one_family(args):
    fam, reps, n, delta, seed = args
    rng = np.random.default_rng(seed)
    emp = SC.load_empirical(fam) if fam.startswith("emp_") else None
    smp = SC.Sampler(fam, n, emp)
    kind = "binary" if fam == "binary" else "cont"
    dlt = 0.8 if fam == "binary" else delta
    d = np.empty(reps)
    vf = np.empty(reps)
    vb = np.empty(reps)
    vs = np.empty(reps)
    vc = np.empty(reps)
    for r in range(reps):
        y1, y0 = smp.draw(rng, dlt)
        d[r], vf[r] = E.effect(kind, y1, y0)
        bd, _ = E.boot_effect(kind, y1, y0, rng, 300)
        vb[r] = bd.var(ddof=1)
        vs[r] = E.split_half_var(kind, y1, y0, rng, K=100, calibrate=False); vc[r] = E.split_half_var(kind, y1, y0, rng, K=100, calibrate=True)
    return fam, dict(mean_d=d.mean(), true_effect=dlt, true_var=d.var(ddof=1), mean_formula=vf.mean(), mean_boot=vb.mean(), mean_splithalf=vs.mean(), mean_splithalf_cal=vc.mean(),
                     sd_splithalf=vs.std(ddof=1))


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=4000)
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--delta", type=float, default=0.5)
    a = ap.parse_args()
    t0 = time.time()
    with ProcessPoolExecutor() as ex:
        res = dict(ex.map(one_family, [(f, a.reps, a.n, a.delta, 777 + i) for i, f in enumerate(SC.FAMILIES)]))
    print(f"n={a.n} per arm, reps={a.reps}; var columns are per-cell Var(d); ratio = mean estimate / true variance  [{time.time() - t0:.0f}s]")
    print(f"{'family':12s} {'E[d]-delta':>10s} {'true Var':>9s} {'formula':>9s} {'ratio':>6s} {'bootstrap':>9s} {'ratio':>6s} {'splithalf':>9s} {'ratio':>6s} {'sh-calib':>9s} {'ratio':>6s}")
    for f, r in res.items():
        tv = r["true_var"]
        print(f"{f:12s} {r['mean_d'] - r['true_effect']:+10.4f} {tv:9.4f} {r['mean_formula']:9.4f} {r['mean_formula'] / tv:6.2f} "
              f"{r['mean_boot']:9.4f} {r['mean_boot'] / tv:6.2f} {r['mean_splithalf']:9.4f} {r['mean_splithalf'] / tv:6.2f} {r['mean_splithalf_cal']:9.4f} {r['mean_splithalf_cal'] / tv:6.2f}")

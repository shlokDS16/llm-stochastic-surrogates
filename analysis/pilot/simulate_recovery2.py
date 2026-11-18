"""Recoverability check, amended (statistician, 2026-10-16). Compares estimator and interval variants on the exact design.

    .venv/Scripts/python.exe -I analysis/pilot/simulate_recovery2.py [--reps 500] [--B 2000] [--n 50] [--families all|primary|stress|a,b]
        [--out runs/pilot-sim2] [--scenarios S0,S0.1W,S0.1split,S0.3W,S0.3split] [--workers 20]

Scenarios (as preregistered): true finite-cell spread S in {0, 0.1, 0.3}; term structure all-in-W or split W/F; C = 16 cells
(W4 x F2 x T2), 32 for the binary framing outcome (x O2); n = 50 responses per condition per cell.
Variants per replicate (point estimate / interval):
  formula   + basic     legacy variance (normal theory) with the pivotal bootstrap interval (the lab engineer's working version)
  bootstrap + basic     response-level bootstrap variance
  splithalf + basic | ti_gauss | ti_boot    amendment A1 variance, three intervals
  oracle    (point)     the true Var(d_c), estimated by Monte Carlo: the bias floor of the moment estimator
Truth: the nominal grid delta_c (S exactly as preregistered) and, for skewed outcomes where E[g_c] != delta_c, the grid of
E[d_c] computed by Monte Carlo ("S_E"); coverage and bias are reported against both.
"""
import argparse
import itertools
import json
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import numpy as np  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import estimators as E  # noqa: E402
import sim_common as SC  # noqa: E402

SCEN = {"S0": (0.0, "W"), "S0.1W": (0.1, "W"), "S0.1split": (0.1, "split"), "S0.3W": (0.3, "W"), "S0.3split": (0.3, "split"),
        "S0.15split": (0.15, "split"), "S0.2split": (0.2, "split"), "S0.25split": (0.25, "split"), "S0.5split": (0.5, "split")}   # extra points for the power curve


def mc_truth(smp, kind, deltas, rng, R=3000):
    """E[d] and Var(d) of one cell as a function of its nominal effect, by Monte Carlo, for the distinct deltas."""
    out = {}
    for dl in sorted(set(np.round(deltas, 10))):
        d = np.empty(R)
        for r in range(R):
            d[r] = E.effect(kind, *smp.draw(rng, dl))[0]
        out[dl] = (d.mean(), d.var(ddof=1))
    return out


def run_scenario(args):
    family, scen, reps, B, n, seed, lean, bvar = args
    vm_main = bvar if family == 'binary' else 'splithalf'
    S, structure = SCEN[scen]
    t0 = time.time()
    binary = family == "binary"
    shape = (4, 2, 2, 2) if binary else (4, 2, 2)
    factors = ["W", "F", "T", "O"] if binary else ["W", "F", "T"]
    design = E.Design(factors, list(shape))
    kind = "binary" if binary else "cont"
    mu = 0.8 if binary else 0.5
    delta = SC.true_effects(shape, S, structure, mu)
    emp = SC.load_empirical(family) if family.startswith("emp_") else None
    smp = SC.Sampler(family, n, emp)
    rng = np.random.default_rng(seed)
    keys = list(itertools.product(*[range(L) for L in shape]))
    names, projs, Ptot = E.term_projectors(design)
    C = design.C
    tr = mc_truth(smp, kind, delta.ravel(), rng)
    ed = np.array([tr[round(float(x), 10)][0] for x in delta.ravel()])
    vt = {k: tr[round(float(delta[k]), 10)][1] for k in keys}
    nominal = delta.ravel()
    truth = {"nominal": nominal, "E": ed}
    s2_true = {k: float(x @ Ptot @ x / C) for k, x in truth.items()}
    ss_true = {k: {nm: float(x @ P @ x) for nm, (P, _) in zip(names, projs)} for k, x in truth.items()}
    variants = [("formula", "basic"), ("bootstrap", "basic"), ("splithalf", "basic"), ("splithalf", "ti_gauss"), ("splithalf", "ti_boot")]
    rec = {vi: dict(S2=[], S=[], lo=[], hi=[]) for vi in variants}
    rec["oracle"] = dict(S2=[])
    term_rec = {nm: dict(est=[], lo=[], hi=[]) for nm in names}
    for _ in range(reps):
        cells = {k: smp.draw(rng, delta[k]) for k in keys}
        rA = E.estimate2(cells, design, kind, rng=rng, B=B, var_method=vm_main, intervals=("ti_boot",), term_intervals=True)
        rB = E.estimate2(cells, design, kind, rng=rng, B=B, var_method=vm_main, intervals=("ti_gauss", "basic"), term_intervals=False)
        if lean:
            rF = rBo = rO = rB
        else:
            rF = E.estimate2(cells, design, kind, rng=rng, B=B, var_method="formula", intervals=("basic",), term_intervals=False)
            rBo = E.estimate2(cells, design, kind, rng=rng, B=B, var_method="bootstrap", intervals=("basic",), term_intervals=False)
            rO = E.estimate2(cells, design, kind, rng=rng, B=B, var_method=vt, intervals=(), term_intervals=False)
        for vi, res in [(("formula", "basic"), rF if not lean else rB), (("bootstrap", "basic"), rBo if not lean else rB), (("splithalf", "basic"), rB), (("splithalf", "ti_gauss"), rB), (("splithalf", "ti_boot"), rA)]:
            iv = res["intervals"][vi[1]] if vi[1] in res["intervals"] else res["intervals"]["basic"]
            rec[vi]["S2"].append(res["S2_untruncated"])
            rec[vi]["S"].append(res["S"])
            rec[vi]["lo"].append(iv["S2"][0])
            rec[vi]["hi"].append(iv["S2"][1])
        rec["oracle"]["S2"].append(rO["S2_untruncated"])
        for nm in names:
            term_rec[nm]["est"].append(rA["terms"][nm])
            term_rec[nm]["lo"].append(rA["intervals"]["ti_boot"][nm][0])
            term_rec[nm]["hi"].append(rA["intervals"]["ti_boot"][nm][1])
    out = dict(family=family, scenario=scen, S=S, structure=structure, reps=reps, B=B, n=n, C=C, seconds=time.time() - t0,
               var_method_main=vm_main, lean=lean, S2_true=s2_true, S_E=float(np.sqrt(max(0.0, s2_true["E"]))), variants={}, terms={})
    for vi in variants:
        r = {k: np.array(v) for k, v in rec[vi].items()}
        row = {}
        for tk in ("nominal", "E"):
            s2t = s2_true[tk]
            row[f"bias_S2_vs_{tk}"] = float(r["S2"].mean() - s2t)
            row[f"coverage_vs_{tk}"] = float(np.mean((r["lo"] <= s2t) & (s2t <= r["hi"])))
        row["bias_S_truncated_vs_nominal"] = float(r["S"].mean() - S)
        row["mean_S2"] = float(r["S2"].mean())
        row["sd_S2"] = float(r["S2"].std(ddof=1))
        row["lower_gt0"] = float(np.mean(r["lo"] > 0))
        row["mean_S_interval"] = [float(np.sqrt(np.maximum(0, r["lo"])).mean()), float(np.sqrt(np.maximum(0, r["hi"])).mean())]
        out["variants"][f"{vi[0]}+{vi[1]}"] = row
    o = np.array(rec["oracle"]["S2"])
    out["variants"]["oracle"] = dict(bias_S2_vs_nominal=float(o.mean() - s2_true["nominal"]), bias_S2_vs_E=float(o.mean() - s2_true["E"]), sd_S2=float(o.std(ddof=1)))
    # terms (ti_boot, splithalf): bias and coverage against the nominal and E truth; shares
    est_all = np.array([term_rec[nm]["est"] for nm in names])            # (terms, reps)
    tot = est_all.sum(0)
    for i, nm in enumerate(names):
        r = {k: np.array(v) for k, v in term_rec[nm].items()}
        row = {}
        for tk in ("nominal", "E"):
            t = ss_true[tk][nm]
            row[f"true_SS_{tk}"] = t
            row[f"bias_vs_{tk}"] = float(r["est"].mean() - t)
            row[f"coverage_vs_{tk}"] = float(np.mean((r["lo"] <= t) & (t <= r["hi"])))
        row["lower_gt0"] = float(np.mean(r["lo"] > 0))
        out["terms"][nm] = row
    rep = np.array(rec[("splithalf", "ti_boot")]["lo"]) > 0                 # shares reported only when S2 lower bound > 0
    tt = ss_true["nominal"]
    ttot = sum(tt.values())
    out["shares"] = dict(reported_fraction=float(rep.mean()), true_total_SS=ttot)
    if ttot > 1e-12:
        ratio_of_means = est_all.sum(1) / tot.sum()
        tsh = np.array([tt[nm] / ttot for nm in names])
        out["shares"].update(true=dict(zip(names, map(float, tsh))), ratio_of_means=dict(zip(names, map(float, ratio_of_means))),
                             max_abs_ratio_of_means_bias=float(np.abs(ratio_of_means - tsh).max()))
        if rep.sum() >= 5:
            sh = est_all[:, rep] / tot[rep][None, :]
            mae = np.abs(sh - tsh[:, None]).mean(1)
            out["shares"].update(mae_when_reported=dict(zip(names, map(float, mae))), mean_mae_when_reported=float(mae.mean()), max_mae_when_reported=float(mae.max()))
    return out


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=500)
    ap.add_argument("--B", type=int, default=2000)
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--families", default="all")
    ap.add_argument("--scenarios", default="S0,S0.1W,S0.1split,S0.3W,S0.3split")
    ap.add_argument("--out", default="runs/pilot-sim2")
    ap.add_argument("--workers", type=int, default=20)
    ap.add_argument("--seed", type=int, default=20261016)
    ap.add_argument("--tag", default="")
    ap.add_argument("--lean", action="store_true", help="only the default estimator (calibrated split-half; formula for binary) with ti_boot, ti_gauss, basic")
    ap.add_argument("--binary-var", default="formula", choices=["formula", "splithalf", "bootstrap"])
    a = ap.parse_args()
    fams = {"all": SC.FAMILIES, "primary": SC.PRIMARY_FAMILIES, "stress": SC.STRESS_FAMILIES}.get(a.families) or a.families.split(",")
    scens = a.scenarios.split(",")
    tasks = [(f, s, a.reps, a.B, a.n, a.seed + 1000 * SC.FAMILIES.index(f) + 10 * list(SCEN).index(s), a.lean, a.binary_var) for f in fams for s in scens]
    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    results = []
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        for r in ex.map(run_scenario, tasks):
            results.append(r)
            v = r["variants"]
            if a.lean:
                print(f"{r['family']:13s} {r['scenario']:10s} S2true={r['S2_true']['nominal']:.4f} S2E={r['S2_true']['E']:.4f} [{r['var_method_main']}] bias(S2)={v['splithalf+ti_boot']['bias_S2_vs_nominal']:+.4f} "
                      f"bias(S)={v['splithalf+ti_boot']['bias_S_truncated_vs_nominal']:+.4f} cov basic {v['splithalf+basic']['coverage_vs_nominal']:.3f} ti_gauss {v['splithalf+ti_gauss']['coverage_vs_nominal']:.3f} "
                      f"ti_boot {v['splithalf+ti_boot']['coverage_vs_nominal']:.3f} lo>0 {v['splithalf+ti_boot']['lower_gt0']:.2f} [{time.time() - t0:.0f}s]", flush=True)
            else:
                print(f"{r['family']:13s} {r['scenario']:10s} S2true={r['S2_true']['nominal']:.4f} S2E={r['S2_true']['E']:.4f} | "
                      f"bias(S2) formula {v['formula+basic']['bias_S2_vs_nominal']:+.4f} boot {v['bootstrap+basic']['bias_S2_vs_nominal']:+.4f} "
                      f"split {v['splithalf+ti_boot']['bias_S2_vs_nominal']:+.4f} oracle {v['oracle']['bias_S2_vs_nominal']:+.4f} | cov split+basic {v['splithalf+basic']['coverage_vs_nominal']:.3f} "
                      f"ti_gauss {v['splithalf+ti_gauss']['coverage_vs_nominal']:.3f} ti_boot {v['splithalf+ti_boot']['coverage_vs_nominal']:.3f} lo>0 {v['splithalf+ti_boot']['lower_gt0']:.2f} [{time.time() - t0:.0f}s]", flush=True)
            (out / f"results{a.tag}.json").write_text(json.dumps(results, indent=1), encoding="utf8")
    print("done", f"{time.time() - t0:.0f}s")

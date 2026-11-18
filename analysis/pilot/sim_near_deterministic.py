"""Targeted simulation: does the Amendment A1 estimator behave in the near-deterministic regime? (statistician, 2026-10-16;
POST-RESULTS: the pilot output had been seen when this was written; the regime is chosen to mimic the observed cells.)

    .venv/Scripts/python.exe -I analysis/pilot/sim_near_deterministic.py [--reps 500] [--workers 12] [--B 2000]
        [--out runs/pilot-analysis/near-deterministic] [--only cont,bin]

Continuous (log-scale responses, anchoring-like; C = 16 = W4 x F2 x T2, n = 50 per arm):
  each response equals the arm's anchor value exactly with probability 1 - pi_c ("echo"), otherwise it is drawn from
  N(anchor value, 1.5^2) (log units). pi_c common (0.02, 0.05, 0.15) or heterogeneous (F0 0.02, F1 0.40, as the observed
  F0 near-deterministic, F1 spread pattern). Raw (log-unit) effect Delta_c = 5 + S_raw * W pattern, S_raw in {0, 0.3}.
  Standardised path: Hedges g with the 0.2 SD floor, split-half v, ti_boot interval (the A1 pipeline).
  Raw path (A1.6): mean difference, split-half v, ti_boot interval.
  Targets: standardised = A1.1 target E[d_c] by Monte Carlo (20,000 draws per distinct cell type); raw = Delta_c exactly.
Binary (framing, C = 32 = W4 x F2 x T2 x O2, n = 50): sure-option probability 1 - eps_c under gain and eps_c under loss;
  eps common (0.02, 0.10) or varying by W (0.01, 0.03, 0.10, 0.30). Log OR with the 0.5 correction when a count is zero
  (A1 pipeline, Woolf variance) against (a) the A1.1 target E[d_c] and (b) the population log OR; risk difference (raw path).
Reported per scenario: share of replicates in which the A1.6 trigger fires (a cell with both arms constant and unequal means),
bias of S-hat, coverage of the 95 percent S interval, false-positive rate of 'S2 lower bound > 0' where the target is 0,
coverage of the dbar interval, and the calibration of the split-half / Woolf variance (mean v-hat over true Var(d_c)).
"""
import argparse
import json
import os
import sys
import time
import zlib
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

N = 50
FLOOR = 0.2
L0 = float(np.log(100.0))
SIGMA_C = 1.5
SHAPE_C = (4, 2, 2)
SHAPE_B = (4, 2, 2, 2)


# ----------------------------------------------------------------------------- continuous
def draw_arm(rng, loc, pi, size):
    """size = (R, n): echo `loc` exactly with prob 1 - pi, else loc + SIGMA_C * N(0,1)."""
    dev = rng.random(size) < pi
    return np.where(dev, loc + SIGMA_C * rng.standard_normal(size), loc)


def cont_scenarios():
    out = {}
    for tag, pif in [("pi0.02", lambda f: 0.02), ("pi0.05", lambda f: 0.05), ("pi0.10", lambda f: 0.10), ("pi0.15", lambda f: 0.15), ("pi0.30", lambda f: 0.30), ("pi_F0.02_F1.40", lambda f: 0.02 if f == 0 else 0.40)]:
        for S in (0.0, 0.3):
            out[f"cont_{tag}_Sraw{S}"] = dict(kind="cont", S_raw=S, pif=tag, pis=np.array([[[pif(f) for _ in range(2)] for f in range(2)] for _ in range(4)]))
    return out


def cont_truth(sc, rng, R=20000):
    delta = SC.true_effects(SHAPE_C, sc["S_raw"], "W", 5.0)
    tg, vg = np.empty(SHAPE_C), np.empty(SHAPE_C)
    cache = {}
    for idx in np.ndindex(*SHAPE_C):
        key = (round(float(delta[idx]), 10), float(sc["pis"][idx]))
        if key not in cache:
            y0 = draw_arm(rng, L0, key[1], (R, N))
            y1 = draw_arm(rng, L0 + key[0], key[1], (R, N))
            g, _ = E.effect_from_moments("cont", N, y1.mean(1), y1.var(1, ddof=1), N, y0.mean(1), y0.var(1, ddof=1), FLOOR)
            cache[key] = (float(g.mean()), float(g.var(ddof=1)))
        tg[idx], vg[idx] = cache[key]
    return delta, tg, vg


def cont_rep(args):
    sc, seed = args
    rng = np.random.default_rng(seed)
    delta = SC.true_effects(SHAPE_C, sc["S_raw"], "W", 5.0)
    cells = {}
    for idx in np.ndindex(*SHAPE_C):
        pi = float(sc["pis"][idx])
        cells[idx] = (draw_arm(rng, L0 + delta[idx], pi, (N,)), draw_arm(rng, L0, pi, (N,)))
    design = E.Design(["W", "F", "T"], list(SHAPE_C))
    # cells with both arms constant (one unique value each) and unequal means: what A1.6 intends to catch. The pipeline's own
    # test is `var(ddof=1) == 0`, which floating-point noise on repeated log values can defeat; both are recorded.
    both_const = sum(1 for (a1, a0) in cells.values() if len(set(a1)) == 1 and len(set(a0)) == 1 and a1[0] != a0[0])
    sps = []
    for (a1, a0) in cells.values():
        sps.append(np.sqrt((a1.var(ddof=1) + a0.var(ddof=1)) / 2))     # arms of equal size
    sps = np.array(sps)
    rec = dict(n_both_constant_unequal=both_const, share_le_floor=float(np.mean(sps <= FLOOR)), share_le_2floor=float(np.mean(sps <= 2 * FLOOR)))
    for name, kind, fl in (("std", "cont", FLOOR), ("raw", "diff", 0.0)):
        r = E.estimate2(cells, design, kind, rng=rng, B=2000 if sc.get("B") is None else sc["B"], K=200, var_method="splithalf", sd_floor=fl, intervals=("ti_boot",), term_intervals=False)
        if r["status"] != "ok":
            rec[name] = dict(status=r["status"], n_det=len(r["deterministic_cells"]))
            continue
        iv = r["intervals"]["ti_boot"]
        rec[name] = dict(status="ok", S=r["S"], S2=r["S2_untruncated"], S_lo=iv["S"][0], S_hi=iv["S"][1], S2_lo=iv["S2"][0], dbar=r["dbar"], dbar_lo=r["dbar_ci"][0], dbar_hi=r["dbar_ci"][1],
                         v=r["v"], d=r["d"])
    return rec


# ----------------------------------------------------------------------------- binary
def bin_scenarios():
    out = {}
    for tag, eps in [("eps0.02", [0.02] * 4), ("eps0.10", [0.10] * 4), ("eps_W.01.03.10.30", [0.01, 0.03, 0.10, 0.30])]:
        out[f"bin_{tag}"] = dict(kind="bin", eps=np.array(eps))
    return out


def bin_truth(sc, rng, R=40000):
    eps = sc["eps"]
    tg, vg, pop, rd = np.empty(SHAPE_B), np.empty(SHAPE_B), np.empty(SHAPE_B), np.empty(SHAPE_B)
    cache = {}
    for idx in np.ndindex(*SHAPE_B):
        e = eps[idx[0]]
        if e not in cache:
            k1 = rng.binomial(N, 1 - e, R).astype(float)
            k0 = rng.binomial(N, e, R).astype(float)
            d, _ = E.effect_from_moments("binary", N, k1 / N, None, N, k0 / N, None)
            cache[e] = (d.mean(), d.var(ddof=1))
        tg[idx], vg[idx] = cache[e]
        pop[idx] = np.log((1 - e) / e) - np.log(e / (1 - e))
        rd[idx] = 1 - 2 * e
    return tg, vg, pop, rd


def bin_rep(args):
    sc, seed = args
    rng = np.random.default_rng(seed)
    eps = sc["eps"]
    cells = {}
    for idx in np.ndindex(*SHAPE_B):
        e = eps[idx[0]]
        cells[idx] = ((rng.random(N) < 1 - e).astype(float), (rng.random(N) < e).astype(float))
    design = E.Design(["W", "F", "T", "O"], list(SHAPE_B))
    rec = {}
    for name, kind, vm in (("std", "binary", "formula"), ("raw", "diff", "splithalf")):
        r = E.estimate2(cells, design, kind, rng=rng, B=2000 if sc.get("B") is None else sc["B"], K=200, var_method=vm, intervals=("ti_boot",), term_intervals=False)
        if r["status"] != "ok":
            rec[name] = dict(status=r["status"], n_det=len(r["deterministic_cells"]))
            continue
        iv = r["intervals"]["ti_boot"]
        rec[name] = dict(status="ok", S=r["S"], S2=r["S2_untruncated"], S_lo=iv["S"][0], S_hi=iv["S"][1], S2_lo=iv["S2"][0], dbar=r["dbar"], dbar_lo=r["dbar_ci"][0], dbar_hi=r["dbar_ci"][1],
                         v=r["v"], d=r["d"])
    return rec


# ----------------------------------------------------------------------------- summary
def S_of(x):
    x = np.asarray(x, float).ravel()
    return float(np.sqrt(np.mean((x - x.mean()) ** 2)))


def summarise(reps, tgt_d, tgt_v, name):
    """reps: list of per-replicate dicts for path `name`. tgt_d: grid of targets; tgt_v: true Var(d_c) grid or None."""
    ok = [r[name] for r in reps if r[name]["status"] == "ok"]
    trig = 1 - len(ok) / len(reps)
    out = dict(path=name, n_reps=len(reps), share_A16_trigger_as_implemented=trig, n_ok=len(ok))
    if reps and "n_both_constant_unequal" in reps[0]:
        out["share_reps_with_exact_constant_unequal_cell"] = float(np.mean([r["n_both_constant_unequal"] > 0 for r in reps]))
        out["mean_n_such_cells"] = float(np.mean([r["n_both_constant_unequal"] for r in reps]))
    if not ok:
        return out
    S_t = S_of(tgt_d)
    dbar_t = float(np.mean(tgt_d))
    Sh = np.array([r["S"] for r in ok])
    S2h = np.array([r["S2"] for r in ok])
    lo = np.array([r["S_lo"] for r in ok])
    hi = np.array([r["S_hi"] for r in ok])
    out.update(S_target=S_t, dbar_target=dbar_t, S_hat_mean=float(Sh.mean()), S_bias=float(Sh.mean() - S_t), S_hat_sd=float(Sh.std(ddof=1)),
               S2_hat_mean=float(S2h.mean()), S2_target=S_t ** 2,
               S_coverage=float(np.mean((lo <= S_t + 1e-12) & (hi >= S_t - 1e-12))), S_interval_width=float(np.mean(hi - lo)),
               frac_S2_lower_gt0=float(np.mean([r["S2_lo"] > 0 for r in ok])),
               dbar_coverage=float(np.mean([(r["dbar_lo"] <= dbar_t) & (r["dbar_hi"] >= dbar_t) for r in ok])),
               dbar_hat_mean=float(np.mean([r["dbar"] for r in ok])))
    if tgt_v is not None:
        vh = np.mean([np.asarray(r["v"]) for r in ok], axis=0)
        tv = np.asarray(tgt_v).ravel()
        out["v_calibration_ratio_mean_over_cells"] = float(np.mean(vh / np.where(tv > 0, tv, np.nan)))
        out["v_calibration_ratio_pooled"] = float(vh.sum() / tv.sum())
        dh = np.array([r["d"] for r in ok])
        out["empirical_var_d_over_true_var"] = float(np.mean(dh.var(0, ddof=1) / np.where(tv > 0, tv, np.nan)))
    return out


def make_tables(out):
    d = json.loads((out / "sim_results.json").read_text(encoding="utf8"))
    f = lambda x, k=3: "" if x is None else f"{x:.{k}f}"
    L = ["# Near-deterministic simulation tables (generated by sim_near_deterministic.py; POST-RESULTS)", "",
         f"reps {d['meta']['reps']}, n {d['meta']['n']} per arm, floor {d['meta']['floor']}, contaminant SD {d['meta']['sigma_contaminant']} (log units), seed {d['meta']['seed']}.", "",
         "## Continuous (log-scale anchoring-like cells, C = 16)", "",
         "S_t = target; bias = mean S-hat minus S_t; cov = coverage of the 95 percent S interval for S_t; fp = share of replicates with lower bound of S2 > 0; v-cal = mean v-hat / true Var(d_c) (pooled over cells); dbar cov = coverage of the dbar interval.",
         "A1.7 gates (primary shapes): |bias| < 0.02; cov in [0.90, 0.98] where S_t > 0; fp <= 0.05 where S_t = 0.", "",
         "| scenario | path | mean share cells SD<=floor | <=2 floor | S_t | S-hat | bias | cov | fp | v-cal | dbar cov | share reps with a both-constant unequal-means cell |", "|" + "---|" * 12]
    for n, r in d["results"].items():
        if not n.startswith("cont"):
            continue
        for path, tgt in (("std", "S_g_target_E_dc"), ("raw", "S_raw_target")):
            s_ = r[path]
            L.append(f"| {n} | {path} | {f(r['mean_share_le_floor'], 2)} | {f(r['mean_share_le_2floor'], 2)} | {f(s_.get('S_target'))} | {f(s_.get('S_hat_mean'))} | {f(s_.get('S_bias'))} | {f(s_.get('S_coverage'))} | "
                     f"{f(s_.get('frac_S2_lower_gt0'))} | {f(s_.get('v_calibration_ratio_pooled'), 2)} | {f(s_.get('dbar_coverage'))} | {f(s_.get('share_reps_with_exact_constant_unequal_cell'), 2)} |")
    L += ["", "### Standardised path restricted to replicates with few cells near the floor (what a share-of-cells rule would keep)", "",
          "| scenario | stratum | n reps | S_t | S-hat | bias | cov | fp | v-cal | dbar cov |", "|" + "---|" * 10]
    for n, r in d["results"].items():
        if not n.startswith("cont"):
            continue
        for k, q in r["std_strata_by_share_of_cells_le_2xfloor"].items():
            L.append(f"| {n} | {k} | {q['n_reps']} | {f(q['S_target'])} | {f(q['S_hat_mean'])} | {f(q['S_bias'])} | {f(q['S_coverage'])} | {f(q['frac_S2_lower_gt0'])} | {f(q['v_calibration_ratio_pooled'], 2)} | {f(q['dbar_coverage'])} |")
    L += ["", "## Binary (framing, C = 32, sure option probability 1 - eps under gain, eps under loss)", "",
          "std = log OR with 0.5 correction, Woolf variance (A1 pipeline); raw = risk difference, split-half variance. Targets: A1.1 E[d_c] for std (and the population log OR in the last two columns), exact risk difference for raw.", "",
          "| scenario | path | S_t | S-hat | bias | cov | fp | v-cal | dbar_t | dbar-hat | dbar cov | S_pop | bias vs pop | cov vs pop |", "|" + "---|" * 14]
    for n, r in d["results"].items():
        if not n.startswith("bin"):
            continue
        sp = r.get("std_vs_population") or {}
        for path in ("std", "raw"):
            s_ = r[path]
            L.append(f"| {n} | {path} | {f(s_.get('S_target'))} | {f(s_.get('S_hat_mean'))} | {f(s_.get('S_bias'))} | {f(s_.get('S_coverage'))} | {f(s_.get('frac_S2_lower_gt0'))} | {f(s_.get('v_calibration_ratio_pooled'), 2)} | "
                     f"{f(s_.get('dbar_target'))} | {f(s_.get('dbar_hat_mean'))} | {f(s_.get('dbar_coverage'))} | {f(sp.get('S_target_population_logOR')) if path == 'std' else ''} | {f(sp.get('S_bias_vs_population')) if path == 'std' else ''} | {f(sp.get('S_coverage_vs_population')) if path == 'std' else ''} |")
    (out / "sim_tables.md").write_text(chr(10).join(L), encoding="utf8")


def run(fn, sc, reps, workers, seed0):
    seeds = np.random.SeedSequence(seed0).spawn(reps)
    jobs = [(sc, int(s.generate_state(1)[0])) for s in seeds]
    with ProcessPoolExecutor(max_workers=workers) as ex:
        return list(ex.map(fn, jobs, chunksize=max(1, reps // (workers * 4))))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=500)
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--B", type=int, default=None)
    ap.add_argument("--out", default="runs/pilot-analysis/near-deterministic")
    ap.add_argument("--only", default="cont,bin")
    ap.add_argument("--seed", type=int, default=20261016)
    ap.add_argument("--tables-only", action="store_true")
    a = ap.parse_args()
    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    if a.tables_only:
        make_tables(out)
        return
    rng = np.random.default_rng(a.seed)
    results, t0 = {}, time.time()
    if "cont" in a.only:
        for name, sc in cont_scenarios().items():
            sc["B"] = a.B
            delta, tg, vg = cont_truth(sc, rng)
            reps = run(cont_rep, sc, a.reps, a.workers, a.seed + zlib.crc32(name.encode()) % 100000)
            strata = {}
            for tau in (0.10, 0.25, 0.50):
                sub = [r for r in reps if r["share_le_2floor"] < tau]
                if sub:
                    q = summarise(sub, tg, vg, "std")
                    strata[f"share_le_2floor<{tau}"] = {k: q.get(k) for k in ("n_reps", "S_target", "S_hat_mean", "S_bias", "S_coverage", "frac_S2_lower_gt0", "dbar_coverage", "v_calibration_ratio_pooled")}
            results[name] = dict(
                std=summarise(reps, tg, vg, "std"), raw=summarise(reps, delta, None, "raw"), std_strata_by_share_of_cells_le_2xfloor=strata,
                mean_share_le_floor=float(np.mean([r["share_le_floor"] for r in reps])), mean_share_le_2floor=float(np.mean([r["share_le_2floor"] for r in reps])),
                nominal_S_raw=sc["S_raw"], pi_by_F=sc["pis"][0, :, 0].tolist(),
                S_raw_target=S_of(delta), S_g_target_E_dc=S_of(tg), dbar_g_target=float(tg.mean()), dbar_raw_target=float(delta.mean()),
                g_target_range=[float(tg.min()), float(tg.max())])
            print(name, f"{time.time() - t0:.0f}s", json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in results[name]["std"].items()}), flush=True)
    if "bin" in a.only:
        for name, sc in bin_scenarios().items():
            sc["B"] = a.B
            tg, vg, pop, rd = bin_truth(sc, rng)
            reps = run(bin_rep, sc, a.reps, a.workers, a.seed + zlib.crc32(name.encode()) % 100000)
            s_std = summarise(reps, tg, vg, "std")
            # population log OR as the target as well (what a reader would assume the estimator recovers)
            ok = [r["std"] for r in reps if r["std"]["status"] == "ok"]
            s_pop = None
            if ok:
                Sp = S_of(pop)
                lo = np.array([r["S_lo"] for r in ok]); hi = np.array([r["S_hi"] for r in ok]); Sh = np.array([r["S"] for r in ok])
                s_pop = dict(S_target_population_logOR=Sp, S_bias_vs_population=float(Sh.mean() - Sp), S_coverage_vs_population=float(np.mean((lo <= Sp) & (hi >= Sp))),
                             dbar_target_population=float(pop.mean()), dbar_hat_mean=float(np.mean([r["dbar"] for r in ok])))
            results[name] = dict(std=s_std, std_vs_population=s_pop, raw=summarise(reps, rd, None, "raw"), eps=sc["eps"].tolist(), S_g_target_E_dc=S_of(tg), S_rd_target=S_of(rd))
            print(name, f"{time.time() - t0:.0f}s", json.dumps({k: (round(v, 3) if isinstance(v, float) else v) for k, v in results[name]["std"].items()}), flush=True)
    meta = dict(reps=a.reps, n=N, floor=FLOOR, sigma_contaminant=SIGMA_C, seed=a.seed, elapsed_s=time.time() - t0, B=a.B or 2000)
    (out / "sim_results.json").write_text(json.dumps(dict(meta=meta, results=results), indent=1), encoding="utf8")
    make_tables(out)
    print("written", out / "sim_results.json", f"{time.time() - t0:.0f}s")


if __name__ == "__main__":
    main()

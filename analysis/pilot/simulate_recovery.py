"""Recoverability check (design v0.4, section 5): fit the full estimator to simulated data from the exact design.

    .venv/Scripts/python.exe -I analysis/pilot/simulate_recovery.py [--reps 500] [--B 2000] [--n 50] [--out runs/pilot-sim]
        [--families binary,normal,skew] [--empirical <path to a pilot <paradigm>.jsonl> --empirical-cell W0,F0,1.0]

Scenarios: true spread S in {0, 0.1, 0.3} x term structure {all spread in W; spread split between W and F}
(S = 0 has one structure). Cells: W(4) x F(2) x T(2) = 16 for continuous outcomes; x O(2) = 32 for the binary
framing outcome. n responses per condition per cell (default 50). Outcome families:
  normal : standard normal responses, true effect delta_c in SD units
  skew   : standardised log-normal (sigma 1) responses, true effect delta_c in SD units
  binary : P(sure | x=0) = 0.35, log odds shifted by delta_c in the x=1 arm
  empirical : standardised responses resampled from one cell of a real pilot file (continuous paradigms), shifted by delta_c
Pass criteria (S >= 0.1): |mean(S-hat) - S| < 0.02; coverage of the 95 % interval for S in [0.90, 0.98];
ratio-of-means factor-share bias (sum of corrected term SS over replicates / sum of corrected totals, minus the true share) < 0.10 for every term; MAE of shares in replicates where they would be reported (S2 basic lower bound > 0) is also given. The real runs proceed only if all pass.
Two intervals are evaluated: percentile (design wording) and basic (pivotal); see estimators.boot_summary.
"""
import argparse
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import estimators as E  # noqa: E402


def expit(z):
    return 1 / (1 + np.exp(-z))


def pattern(levels):
    v = np.arange(levels, dtype=float)
    v -= v.mean()
    return v / np.sqrt((v ** 2).mean())


def true_effects(shape, S, structure, mu):
    """delta grid with spread exactly S. shape = (W, F, T[, O])."""
    w = pattern(shape[0]).reshape((-1,) + (1,) * (len(shape) - 1))
    f = pattern(shape[1]).reshape((1, -1) + (1,) * (len(shape) - 2))
    if structure == "W":
        g = w * np.ones(shape)
    else:  # split
        g = (np.sqrt(0.5) * w + np.sqrt(0.5) * f) * np.ones(shape)
    g = g - g.mean()
    g = g / np.sqrt((g ** 2).mean()) if S > 0 else g * 0
    return mu + S * g


def true_shares(delta, design):
    ss, _ = E.term_ss(delta[None])
    tot = ss.sum()
    return ss[0] / tot if tot > 1e-12 else None


class Sampler:
    def __init__(self, family, n, empirical=None):
        self.family, self.n, self.emp = family, n, empirical

    def draw(self, rng, delta):
        n = self.n
        if self.family == "binary":
            p0 = 0.35
            p1 = expit(np.log(p0 / (1 - p0)) + delta)
            return (rng.random(n) < p1).astype(float), (rng.random(n) < p0).astype(float)
        if self.family == "normal":
            return rng.standard_normal(n) + delta, rng.standard_normal(n)
        if self.family == "skew":
            z = lambda: (np.exp(rng.standard_normal(n)) - np.exp(0.5)) / np.sqrt((np.exp(1) - 1) * np.exp(1))
            return z() + delta, z()
        if self.family == "empirical":
            return self.emp[rng.integers(0, len(self.emp), n)] + delta, self.emp[rng.integers(0, len(self.emp), n)]
        raise ValueError(self.family)


def load_empirical(path, cell, transform="none", pool_cells=False):
    """Standardised responses of the x=0 arm of one pilot cell (or of all cells with the same format and temperature)."""
    W, F, T = cell.split(",")
    tf = {"none": lambda v: v, "log": np.log, "log1p": np.log1p}[transform]
    ys = []
    for line in Path(path).read_text(encoding="utf8").splitlines():
        r = json.loads(line)
        if r["greedy"] or not r["valid"] or r["x"] != 0:
            continue
        if (pool_cells or r["W"] == W) and r["F"] == F and str(r["T"]) == T:
            ys.append(r["y"])
    y = tf(np.array(ys, float))
    sd = y.std(ddof=1)
    return (y - y.mean()) / (sd if sd > 0 else 1.0)


def run_scenario(family, S, structure, reps, B, n, seed, empirical=None, var_method="formula"):
    shape = (4, 2, 2, 2) if family == "binary" else (4, 2, 2)
    factors = ["W", "F", "T", "O"] if family == "binary" else ["W", "F", "T"]
    design = E.Design(factors, list(shape))
    kind = "binary" if family == "binary" else "cont"
    mu = 0.8 if family == "binary" else 0.5
    delta = true_effects(shape, S, structure, mu)
    tshare = true_shares(delta, design)
    names = E.term_names(factors)
    rng = np.random.default_rng(seed)
    smp = Sampler(family, n, empirical)
    import itertools
    keys = list(itertools.product(*[range(L) for L in shape]))
    rec = dict(css=[], s2lo=[], S2=[], S=[], cover_pct=[], cover_basic=[], cover_S2_basic=[], lo_b=[], hi_b=[], shares=[], dbar=[])
    for _ in range(reps):
        cells = {k: smp.draw(rng, delta[k]) for k in keys}
        res = E.estimate(cells, design, kind, rng=rng, B=B, var_method=var_method)
        b = res["boot"]
        rec["S2"].append(res["S2_untruncated"])
        rec["S"].append(res["S"])
        rec["dbar"].append(res["dbar"])
        rec["cover_pct"].append(b["S_ci_percentile"][0] <= S <= b["S_ci_percentile"][1])
        rec["cover_basic"].append(b["S_ci_basic"][0] <= S <= b["S_ci_basic"][1])
        rec["cover_S2_basic"].append(b["S2_ci_basic"][0] <= S ** 2 <= b["S2_ci_basic"][1])
        rec["lo_b"].append(b["S_ci_basic"][0]); rec["hi_b"].append(b["S_ci_basic"][1])
        # shares estimated from corrected SS divided by the corrected total (untruncated; a share needs a positive total)
        css = np.array([res["terms"][nm] for nm in names])
        tot = css.sum()
        rec["shares"].append((css / tot).tolist() if tot > 1e-9 else [np.nan] * len(names))
        rec["css"].append(css.tolist())
        rec["s2lo"].append(b["S2_ci_basic"][0])
    sh = np.array(rec["shares"])
    out = dict(var_method=var_method, family=family, S=S, structure=structure, reps=reps, B=B, n=n, shape=list(shape),
               mean_S2_untruncated=float(np.mean(rec["S2"])), true_S2=S ** 2,
               mean_S_hat=float(np.mean(rec["S"])), bias_S_hat=float(np.mean(rec["S"]) - S),
               bias_S2_hat=float(np.mean(rec["S2"]) - S ** 2),
               coverage_percentile=float(np.mean(rec["cover_pct"])), coverage_basic=float(np.mean(rec["cover_basic"])),
               coverage_S2_basic=float(np.mean(rec["cover_S2_basic"])),
               mean_interval_basic=[float(np.mean(rec["lo_b"])), float(np.mean(rec["hi_b"]))],
               mean_dbar=float(np.mean(rec["dbar"])), true_dbar=float(delta.mean()))
    if tshare is not None:
        css_a = np.array(rec["css"])
        ratio_of_means = css_a.sum(0) / css_a.sum()
        cond = np.array(rec["s2lo"]) > 0                      # replicates in which shares would be reported
        ok = ~np.isnan(sh).any(1) & cond
        out["true_shares"] = dict(zip(names, map(float, tshare)))
        out["share_ratio_of_means"] = dict(zip(names, map(float, ratio_of_means)))
        out["share_bias_ratio_of_means_max"] = float(max(abs(r - t) for r, t in zip(ratio_of_means, tshare)))
        out["share_reported_fraction"] = float(cond.mean())
        if ok.sum() > 5:
            mae = np.nanmean(np.abs(sh[ok] - tshare[None, :]), axis=0)
            out["share_mae_when_reported"] = dict(zip(names, map(float, mae)))
            out["share_mae_when_reported_max"] = float(mae.max())
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=500)
    ap.add_argument("--B", type=int, default=2000)
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--out", default="runs/pilot-sim")
    ap.add_argument("--families", default="binary,normal,skew")
    ap.add_argument("--empirical")
    ap.add_argument("--empirical-cell", default="W0,F0,1.0")
    ap.add_argument("--empirical-transform", default="none", choices=["none", "log", "log1p"])
    ap.add_argument("--empirical-pool-wordings", action="store_true")
    ap.add_argument("--seed", type=int, default=20261016)
    ap.add_argument("--tag", default="")
    ap.add_argument("--var-method", default="formula", choices=["formula", "bootstrap"])
    a = ap.parse_args()
    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    emp = load_empirical(a.empirical, a.empirical_cell, a.empirical_transform, a.empirical_pool_wordings) if a.empirical else None
    fams = ([] if a.families == "none" else a.families.split(",")) + (["empirical"] if emp is not None else [])
    scen = [(0.0, "W")] + [(S, st) for S in (0.1, 0.3) for st in ("W", "split")]
    results = []
    t0 = time.time()
    for fam in fams:
        for i, (S, st) in enumerate(scen):
            seed = a.seed + 1000 * fams.index(fam) + i
            r = run_scenario(fam, S, st, a.reps, a.B, a.n, seed, emp, a.var_method)
            results.append(r)
            print(f"{fam:9s} S={S:.1f} {st:5s} bias_S={r['bias_S_hat']:+.3f} bias_S2={r['bias_S2_hat']:+.4f} cov_basic={r['coverage_basic']:.3f} "
                  f"cov_pct={r['coverage_percentile']:.3f} share_bias_max={r.get('share_bias_ratio_of_means_max', float('nan')):.3f} reported={r.get('share_reported_fraction', float('nan')):.2f} "
                  f"[{time.time() - t0:.0f}s]", flush=True)
            (out / f"results{a.tag}.json").write_text(json.dumps(results, indent=1), encoding="utf8")
    # verdict
    lines = ["family,S,structure,bias_S,coverage_percentile,coverage_basic,share_bias_max,share_mae_when_reported_max,share_reported_fraction,pass_bias,pass_cov_percentile,pass_cov_basic,pass_shares"]
    verdict = {"percentile": True, "basic": True}
    for r in results:
        if r["S"] < 0.1:
            continue
        pb = abs(r["bias_S_hat"]) < 0.02
        pcp = 0.90 <= r["coverage_percentile"] <= 0.98
        pcb = 0.90 <= r["coverage_basic"] <= 0.98
        ps = r["share_bias_ratio_of_means_max"] < 0.10
        verdict["percentile"] &= pb and pcp and ps
        verdict["basic"] &= pb and pcb and ps
        lines.append(f"{r['family']},{r['S']},{r['structure']},{r['bias_S_hat']:.4f},{r['coverage_percentile']:.3f},{r['coverage_basic']:.3f},{r['share_bias_ratio_of_means_max']:.3f},{r.get('share_mae_when_reported_max', float('nan')):.3f},{r['share_reported_fraction']:.2f},{pb},{pcp},{pcb},{ps}")
    (out / f"summary{a.tag}.csv").write_text("\n".join(lines), encoding="utf8")
    (out / f"verdict{a.tag}.json").write_text(json.dumps(dict(var_method=a.var_method, all_criteria_pass=verdict, reps=a.reps, B=a.B, n=a.n, families=fams), indent=1), encoding="utf8")
    print("VERDICT (all S>=0.1 scenarios, all families):", verdict)


if __name__ == "__main__":
    main()

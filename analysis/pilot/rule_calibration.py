"""Calibration of the preregistered stable / fragile rule (pilot-design section 6) against a perfectly human-like,
prompt-invariant model, and the same rule applied to the 36 human Many Labs 1 sites. CPU only; no model is run.

    .venv/Scripts/python.exe -I analysis/pilot/rule_calibration.py [--reps 2000] [--workers 8] [--seed 20261017]
                                                                    [--out runs/pilot-rule-calibration] [--smoke]

Simulated model ("null replica"): every cell of the crossed prompt grid has the same data-generating process, the human ML1
pooled effect (Table 15 values, human_mu of runs/pilot-side-by-side/table_a1.csv) and zero spread across cells; 50 responses per
arm and cell; 16 cells (P2a-d, P3, P4) or 32 cells (P1, option order added). Each replicate is analysed with the project's own
A1 code (analysis/pilot/estimators.py estimate2: split-half cell variances, test-inversion intervals with bootstrap errors,
B = 2000, K = 200) and labelled with side_by_side.rule_outcome (the code that produced the 41/42 count).
Variants:
  normal    (primary) continuous answers N(delta, SD) on the analysis scale (log estimate for P2, log(1+x) for P4, rating for P3),
            delta = human_mu * SD, SD = pooled within-site SD of the ML1 sites (A2.1 values; runs/pilot-analysis/near-deterministic/human_sd.csv);
            P1: binomial with the human sure-option rates (pooled ML1 rate of the loss-frame arm; gain-frame rate set so the log OR equals Table 15).
  empirical (sensitivity) answers resampled with replacement from the pooled human ML1 responses of each arm (real shape, ties, bounds);
            its implied effect is the pooled-over-sites g, reported beside the Table 15 value; P1 is identical to the primary.
Human sites: rule applied to runs/human-ml1/site_effects.csv with sites as cells (A1 metric rows), point estimates and the
interval needed for 'stable' taken from table_a1 (human_S_hi) or, for the plain moment version, the point S.
Outputs under --out: reps.csv, summary.csv, summary.md, human_sites.csv, config.json, env.json, log.txt.
"""
import argparse
import hashlib
import itertools
import json
import os
import platform
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import estimators as E  # noqa: E402
from side_by_side import rule_outcome  # noqa: E402  (the project's rule code)

PARADIGMS = ["P1", "P2a", "P2b", "P2c", "P2d", "P3", "P4"]
N = 50
SD_FLOOR = {"P2a": 0.2, "P2b": 0.2, "P2c": 0.2, "P2d": 0.2, "P4": 0.2, "P3": 1 / np.sqrt(12)}   # analyze_pilot.SD_FLOOR_BY_PARADIGM / SD_FLOOR
LEVELS = {"P1": [4, 2, 2, 2]}
LEVELS.update({p: [4, 2, 2] for p in PARADIGMS[1:]})
FACT = ["W", "F", "T", "O"]
HUMAN_KEY = {"P1": "primary", "P2a": "sens_log", "P2b": "sens_log", "P2c": "sens_log", "P2d": "sens_log", "P3": "primary", "P4": "primary"}
EMP_COL = {"P2a": "y_log", "P2b": "y_log", "P2c": "y_log", "P2d": "y_log", "P3": "y", "P4": "y"}
Z = 1.959964


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load_params():
    t = pd.read_csv(ROOT / "runs/pilot-side-by-side/table_a1.csv")
    mu = t.groupby("paradigm").human_mu.first().to_dict()
    sd = pd.read_csv(ROOT / "runs/pilot-analysis/near-deterministic/human_sd.csv").set_index("paradigm").sd_pooled.to_dict()
    p1 = pd.read_csv(ROOT / "data/processed/ml1/P1.csv")
    p0 = float(p1[p1.x == 0].y.mean())
    p1x = float(p1[p1.x == 1].y.mean())
    o1 = np.exp(mu["P1"]) * p0 / (1 - p0)
    prm = dict(mu=mu, sd=sd, p0=p0, p1_pooled=p1x, p1_set=float(o1 / (1 + o1)),
               lor_pooled_data=float(np.log(p1x / (1 - p1x) * (1 - p0) / p0)))
    emp, emp_g = {}, {}
    for p, col in EMP_COL.items():
        d = pd.read_csv(ROOT / f"data/processed/ml1/{p}.csv")
        d = d[np.isfinite(d[col])]
        emp[p] = (d[d.x == 1][col].to_numpy(float), d[d.x == 0][col].to_numpy(float))
        y1, y0 = emp[p]
        sp = np.sqrt(((len(y1) - 1) * y1.var(ddof=1) + (len(y0) - 1) * y0.var(ddof=1)) / (len(y1) + len(y0) - 2))
        emp_g[p] = float((y1.mean() - y0.mean()) / sp)
    prm["emp"] = emp
    prm["emp_pooled_g"] = emp_g
    return prm


def one_replicate(args):
    p, variant, rep, seed, prm = args
    rng = np.random.default_rng([seed, PARADIGMS.index(p), 0 if variant == "normal" else 1, rep])
    levels = LEVELS[p]
    design = E.Design(FACT[:len(levels)], levels)
    cells = {}
    if p == "P1":
        kind = "binary"
        for k in itertools.product(*[range(L) for L in levels]):
            cells[k] = ((rng.random(N) < prm["p1_set"]).astype(float), (rng.random(N) < prm["p0"]).astype(float))
        floor, vmeth = 0.0, "formula"
    else:
        kind = "cont"
        sd, delta = prm["sd"][p], prm["mu"][p] * prm["sd"][p]
        e1, e0 = prm["emp"][p]
        for k in itertools.product(*[range(L) for L in levels]):
            if variant == "normal":
                cells[k] = (rng.normal(delta, sd, N), rng.normal(0.0, sd, N))
            else:
                cells[k] = (rng.choice(e1, N, replace=True), rng.choice(e0, N, replace=True))
        floor, vmeth = SD_FLOOR[p], "splithalf"
    r = E.estimate2(cells, design, kind, rng=rng, B=2000, K=200, var_method=vmeth, sd_floor=floor,
                    intervals=("ti_boot",), term_intervals=False)
    if r["status"] != "ok":
        return dict(paradigm=p, variant=variant, rep=rep, status=r["status"])
    iv = r["intervals"]["ti_boot"]
    ss, dbar, S, lo = r["sign_stability"], r["dbar"], r["S"], iv["dbar_minus_2S_lower"]
    return dict(paradigm=p, variant=variant, rep=rep, status="ok", sigma=ss, dbar=dbar, S=S, S_hi=iv["S"][1], dm2s_lower=lo,
                rule=rule_outcome(ss, dbar, S, lo), sigma_clause=bool(ss < 0.6), range_clause=bool(dbar - 2 * S < 0 < dbar + 2 * S),
                sign_agree=r["sign_agreement"])


def human_sites(out):
    se = pd.read_csv(ROOT / "runs/human-ml1/site_effects.csv")
    t = pd.read_csv(ROOT / "runs/pilot-side-by-side/table_a1.csv").groupby("paradigm").first()
    rows = []
    for p in PARADIGMS:
        s = se[(se.paradigm == p) & (se.metric == HUMAN_KEY[p])]
        d, v = s.d.to_numpy(float), s.v.to_numpy(float)
        k = len(d)
        sigma = float(np.mean(d - Z * np.sqrt(v) > 0))
        dbar = float(d.mean())
        S_mom = float(E.spread(d, v))
        dbar_lo = dbar - Z * np.sqrt(v.sum()) / k
        res = {}
        for tag, S_pt, S_hi in (("mom", S_mom, S_mom), ("a1", float(t.loc[p, "human_S"]), float(t.loc[p, "human_S_hi"]))):
            lo = dbar_lo - 2 * S_hi
            res[tag] = dict(S=S_pt, S_hi=S_hi, dm2s_lower=lo, rule=rule_outcome(sigma, dbar, S_pt, lo),
                            range_clause=bool(dbar - 2 * S_pt < 0 < dbar + 2 * S_pt))
        rows.append(dict(paradigm=p, metric=HUMAN_KEY[p], k_sites=k, sigma=sigma, n_sites_ci_above0=int(round(sigma * k)), dbar=dbar,
                         dbar_lo=dbar_lo, sigma_clause=bool(sigma < 0.6),
                         S_moment=res["mom"]["S"], range_clause_moment=res["mom"]["range_clause"], rule_moment=res["mom"]["rule"],
                         S_table_a1=res["a1"]["S"], S_hi_table_a1=res["a1"]["S_hi"],
                         range_clause_table_a1=res["a1"]["range_clause"], dm2s_lower_table_a1=res["a1"]["dm2s_lower"],
                         rule_table_a1=res["a1"]["rule"], median_site_n=int(np.median(s.n1 + s.n0)), min_site_n=int((s.n1 + s.n0).min())))
    df = pd.DataFrame(rows)
    df.to_csv(out / "human_sites.csv", index=False)
    return df


def git_sha():
    try:
        return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    except Exception:
        return "unknown"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=2000)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--seed", type=int, default=20261017)
    ap.add_argument("--out", default="runs/pilot-rule-calibration")
    ap.add_argument("--smoke", action="store_true", help="1 percent sample: reps = max(5, reps/100), output to <out>-smoke")
    a = ap.parse_args()
    reps = max(5, a.reps // 100) if a.smoke else a.reps
    out = ROOT / (a.out + ("-smoke" if a.smoke else ""))
    out.mkdir(parents=True, exist_ok=True)
    LOG = []

    def log(*x):
        s = " ".join(str(i) for i in x)
        LOG.append(s)
        print(s, flush=True)

    t0 = time.time()
    prm = load_params()
    cfg = dict(script="analysis/pilot/rule_calibration.py", script_sha256=sha(__file__), estimators_sha256=sha(HERE / "estimators.py"),
               side_by_side_sha256=sha(HERE / "side_by_side.py"), git_head=git_sha(), seed=a.seed, reps=reps, smoke=a.smoke, n_per_arm=N,
               cells={p: int(np.prod(LEVELS[p])) for p in PARADIGMS}, B=2000, K=200, workers=a.workers,
               params={k: v for k, v in prm.items() if k != "emp"}, sd_floor={k: float(v) for k, v in SD_FLOOR.items()},
               inputs_sha256={f: sha(ROOT / f) for f in ["runs/pilot-side-by-side/table_a1.csv", "runs/pilot-analysis/near-deterministic/human_sd.csv",
                                                         "runs/human-ml1/site_effects.csv", "data/processed/ml1/P1.csv"]})
    (out / "config.json").write_text(json.dumps(cfg, indent=1, default=float), encoding="utf8")
    (out / "env.json").write_text(json.dumps(dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__,
                                                  platform=platform.platform(), cpu_count=os.cpu_count()), indent=1), encoding="utf8")
    log(f"rule calibration: reps={reps} seed={a.seed} workers={a.workers} smoke={a.smoke}")
    log("params (human_mu, SD):", {p: (round(prm["mu"][p], 3), round(prm["sd"].get(p, float("nan")), 3)) for p in PARADIGMS},
        f"P1 p0={prm['p0']:.4f} p1_set={prm['p1_set']:.4f} p1_pooled={prm['p1_pooled']:.4f} lor_pooled_data={prm['lor_pooled_data']:.3f}")
    log("empirical-variant pooled g:", {p: round(g, 3) for p, g in prm["emp_pooled_g"].items()})
    jobs = [(p, v, r, a.seed, prm) for p in PARADIGMS for v in (["normal"] if p == "P1" else ["normal", "empirical"]) for r in range(reps)]
    res = []
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        for i, r in enumerate(ex.map(one_replicate, jobs, chunksize=8)):
            res.append(r)
            if (i + 1) % 1000 == 0:
                log(f"  {i + 1}/{len(jobs)} replicates, {time.time() - t0:.0f} s")
    df = pd.DataFrame(res)
    bad = df[df.status != "ok"]
    log(f"replicates: {len(df)}, not ok (deterministic cells): {len(bad)}")
    df = df[df.status == "ok"]
    df.to_csv(out / "reps.csv", index=False)
    rows = []
    for (p, v), g in df.groupby(["paradigm", "variant"], sort=False):
        n = len(g)
        row = dict(paradigm=p, variant=v, n_reps=n, cells=int(np.prod(LEVELS[p])))
        for name, m in (("P_fragile", g.rule == "fragile"), ("P_stable", g.rule == "stable"), ("P_neither", g.rule == "neither"),
                        ("P_sigma_lt_06", g.sigma_clause), ("P_range_clause", g.range_clause), ("P_sigma_ge_09", g.sigma >= 0.9),
                        ("P_all_cells_positive", g.sign_agree == 1.0)):
            pr = float(m.mean())
            row[name], row[name + "_se"] = pr, float(np.sqrt(pr * (1 - pr) / n))
        row.update(mean_sigma=float(g.sigma.mean()), mean_sigma_se=float(g.sigma.std(ddof=1) / np.sqrt(n)), mean_dbar=float(g.dbar.mean()),
                   mean_S=float(g.S.mean()))
        rows.append(row)
    s = pd.DataFrame(rows)
    s.to_csv(out / "summary.csv", index=False)
    h = human_sites(out)
    md = ["# Rule calibration: zero-spread human-replica model, n = 50 per arm per cell\n",
          f"Replicates per paradigm and variant: {reps} (smoke={a.smoke}); seed {a.seed}; Monte-Carlo SE in brackets. Source: `analysis/pilot/rule_calibration.py`; "
          "rule = `side_by_side.rule_outcome`. Evidence level E4.\n",
          "| paradigm | variant | cells | P(fragile) | P(stable) | P(neither) | mean sigma | P(sigma<0.6) | P(range clause) |", "|---|---|---|---|---|---|---|---|---|"]
    for _, r in s.iterrows():
        md.append(f"| {r['paradigm']} | {r['variant']} | {r['cells']} | {r['P_fragile']:.3f} ({r['P_fragile_se']:.3f}) | {r['P_stable']:.3f} ({r['P_stable_se']:.3f}) | "
                  f"{r['P_neither']:.3f} ({r['P_neither_se']:.3f}) | {r['mean_sigma']:.3f} ({r['mean_sigma_se']:.3f}) | {r['P_sigma_lt_06']:.3f} | {r['P_range_clause']:.3f} |")
    md += ["", "## Human ML1 sites as cells (36 sites; A1 metric rows of site_effects.csv)", "",
           "| paradigm | sigma (sites with CI above 0) | dbar | S (moment, site_effects) | S^H (table_a1) | range clause | label (moment S) | label (S^H, interval for stable) |",
           "|---|---|---|---|---|---|---|---|"]
    for _, r in h.iterrows():
        md.append(f"| {r['paradigm']} | {r['sigma']:.3f} ({r['n_sites_ci_above0']}/{r['k_sites']}) | {r['dbar']:.3f} | {r['S_moment']:.3f} | {r['S_table_a1']:.3f} | "
                  f"{r['range_clause_moment']} | {r['rule_moment']} | {r['rule_table_a1']} |")
    (out / "summary.md").write_text("\n".join(md) + "\n", encoding="utf8")
    log("\n".join(md))
    log(f"done in {time.time() - t0:.0f} s")
    (out / "log.txt").write_text("\n".join(LOG) + "\n", encoding="utf8")


if __name__ == "__main__":
    main()

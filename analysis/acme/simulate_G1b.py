"""Gate G1b (hypothesis error rates) for ACME H1-H3, PREREG-acme.md section 6, SYNTHETIC data only.

    .venv/Scripts/python.exe -I analysis/acme/simulate_G1b.py run [--reps N] [--B 1000] [--workers 2] [--out runs/acme-G1b]
        [--scenarios H1_null,H2_null,H3_null,H1_alt,H2_alt,H3_alt]
    .venv/Scripts/python.exe -I analysis/acme/simulate_G1b.py aggregate [--out runs/acme-G1b]

Specification (prereg section 6, fixed at freezing): estimator A-G1 ("A1"), real shapes (14 models, 10 wordings, 5 two-order and
5 one-order items, 4 temperatures for H1), B = 1000, 500 replicates per null (pass: rejection rate at alpha 0.05 <= 0.0695), 300
replicates per alternative (information only). A test rejects when its raw p-value < 0.05 (H1 one-sided, H3 two-sided, H2 as in
gstudy.hypotheses).

Nulls (boundary):
  H1_null  every item: wording share (W + MW) = 0.25 = T share (all terms containing T except the residual).
  H3_null  every item: MW share = W share = 0.30. Two-order items: residual 0.40. One-order items have no separable residual
           (it is labelled MW); to keep MW = W = 0.30 the remaining 0.40 sits in the fixed M effect (the residual and M are the
           only components outside W and MW in the real one-order arrays).
  H2_null  every item's true median (over the 14 models) set-up SD = c_p = 0.2 ML1-SD; the rest of the design is scenario (e) of
           simulate_G1 (component shares 8-12 percent, drawn from simulate_G1.shares_two / shares_one). single_site_se = 0.2.
Alternatives (information only): H1 wording 0.40 vs T 0.10; H3 MW 0.45 vs W 0.15; H2 true median set-up SD = 0.4 = 2 c_p.

TRUE set-up SD (definition): for model m, the population SD of Delta[m, w, o] over the wording universe (w random, infinite) and
the order set (equal weights): variance = sigma2_W + sigma2_MW + sigma2_WO + sigma2_res + mean_o (omega_o + gamma_mo)^2 for
two-order items, sigma2_W + sigma2_MW for one-order items (the residual is MW). The item's true median is the median over the 14 models of
the SD; the design is rescaled (all components by one factor) so this equals the target exactly. The estimator in gstudy.setup_sd
is the finite-sample SD (ddof = 1) over the 10 x n_o cells; its small-sample bias is part of what the gate measures.
H2 is computed here through gstudy.setup_sd + iu_pvalue with the same seeds as gstudy.hypotheses uses ([seed, j, 7]) instead of by
calling hypotheses(), to avoid building the H3 pool (identical p-value; verified in tests/test_simulate_G1b.py).
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, wait, FIRST_COMPLETED
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import numpy as np  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import gstudy as G  # noqa: E402
import simulate_G1 as S1  # noqa: E402

SEED = 20261106
N_M, N_W, N_O, N_T = 14, 10, 2, 4
N2, N1 = 5, 5
T1_INDEX = G.TEMPERATURES.index(1.0)
ALPHA = 0.05
SCENARIOS = ["H1_null", "H2_null", "H3_null", "H1_alt", "H2_alt", "H3_alt"]
SCEN_INDEX = {n: i for i, n in enumerate(SCENARIOS)}
REPS_DEFAULT = {"null": 500, "alt": 300}
PASS_MAX = 0.05 + 2 * math.sqrt(0.05 * 0.95 / 500)          # 0.0695
C_P = 0.2
COLS = ["rep", "scenario", "p_H1", "p_H2", "p_H3", "est_H1", "wording_H1", "T_H1", "est_H3", "MW_H3", "W_H3",
        "H2_n_hold", "H2_k", "H2_mean_median_sd", "H2_min_median_sd", "H2_max_median_sd", "seconds"]

# component tables (term label -> share). Labels follow gstudy naming; "res" is the highest interaction.
H1_TWO = {   # (M, W, O, T)
    "null": dict(W=0.10, MW=0.15, T=0.10, MT=0.05, WT=0.05, MWT=0.05, M=0.10, O=0.05, MO=0.05, WO=0.05, res=0.25),
    "alt":  dict(W=0.15, MW=0.25, T=0.05, MT=0.02, WT=0.02, MWT=0.01, M=0.10, O=0.05, MO=0.05, WO=0.05, res=0.25),
}
H1_ONE = {   # (M, W, T)
    "null": dict(W=0.10, MW=0.15, T=0.10, MT=0.05, WT=0.10, M=0.10, res=0.40),
    "alt":  dict(W=0.15, MW=0.25, T=0.04, MT=0.03, WT=0.03, M=0.10, res=0.40),
}
H3_TWO = {"null": dict(W=0.30, MW=0.30, res=0.40), "alt": dict(W=0.15, MW=0.45, res=0.40)}
H3_ONE = {"null": dict(W=0.30, MW=0.30, M=0.40), "alt": dict(W=0.15, MW=0.45, M=0.40)}
H1_WORDING, H3_PAIR = ("W", "MW"), ("MW", "W")


def kind_of(name):
    return name.split("_")[0], name.split("_")[1]


# ----------------------------------------------------------------------------------------------------------------------------
# generic generator for arrays with facets M, W, O, T (any subset containing M and W)
# ----------------------------------------------------------------------------------------------------------------------------
def term_facets(label, facets):
    return tuple(facets) if label == "res" else tuple(f for f in facets if f in label)


def make_term_spec(rng, facets, comp, n_m=N_M):
    """Fixed terms (no W) become sum-to-zero patterns scaled so that sum(x^2)/prod(n_f - 1) equals the target (the n-1 convention of
    the prereg quadratic forms); W-containing terms are random with the target variance."""
    sizes = {"M": n_m, "O": N_O, "T": N_T}
    fixed, rand = {}, {}
    for lab, v in comp.items():
        S = term_facets(lab, facets)
        if "W" in S:
            rand[S] = v
        else:
            x = S1._center_all(rng.standard_normal([sizes[f] for f in S]))
            df = float(np.prod([sizes[f] - 1 for f in S]))
            fixed[S] = x * math.sqrt(v * df / (x ** 2).sum())
    return dict(facets=tuple(facets), sizes=sizes, comp=dict(comp), fixed=fixed, rand=rand)


def gen_term_array(rng, sp, nw=N_W):
    facets, sizes = sp["facets"], dict(sp["sizes"], W=nw)
    shape = [sizes[f] for f in facets]
    y = np.zeros(shape)
    for S, x in sp["fixed"].items():
        y = y + x.reshape([sizes[f] if f in S else 1 for f in facets])
    for S, v in sp["rand"].items():
        y = y + math.sqrt(v) * rng.standard_normal([sizes[f] if f in S else 1 for f in facets])
    return y


# ----------------------------------------------------------------------------------------------------------------------------
# scenarios
# ----------------------------------------------------------------------------------------------------------------------------
def _h2_unit_var(sp):
    """True set-up variance per model at the spec's current scale (population over the wording universe and the order set)."""
    if sp["n_o"] == 2:
        return sp["sW"] + sp["sMW"] + sp["sWO"] + sp["sres"] + ((sp["omega"][None, :] + sp["gamma"]) ** 2).mean(axis=1)
    return np.full(sp["n_m"], sp["sW"] + sp["sMW"])


def true_median_sd(sp):
    return float(np.median(np.sqrt(_h2_unit_var(sp))))


_CACHE = {}


def scenario(name):
    """Item specs for a scenario, deterministic from SEED (cached per process)."""
    if name in _CACHE:
        return _CACHE[name]
    kind, lvl = kind_of(name)
    si = SCEN_INDEX[name]
    specs = []
    for j in range(N2 + N1):
        rng = np.random.default_rng([SEED, 8500 + si, j])
        two = j < N2
        if kind == "H1":
            specs.append(make_term_spec(rng, ("M", "W", "O", "T") if two else ("M", "W", "T"), (H1_TWO if two else H1_ONE)[lvl]))
        elif kind == "H3":
            specs.append(S1.make_spec(rng, N_M, 2 if two else 1, dict((H3_TWO if two else H3_ONE)[lvl])))
        else:
            sh = S1.shares_two("e", rng) if two else S1.shares_one("e", rng)
            sp = S1.make_spec(rng, N_M, 2 if two else 1, dict(sh))
            target = C_P if lvl == "null" else 2 * C_P
            k = (target / true_median_sd(sp)) ** 2
            for key in ("alpha", "omega", "gamma"):
                sp[key] = sp[key] * math.sqrt(k)
            for key in ("sW", "sMW", "sWO", "sres"):
                sp[key] = sp[key] * k
            sp["comp"] = {a: b * k for a, b in sp["comp"].items()}
            sp["target_sd"] = target
            specs.append(sp)
    _CACHE[name] = specs
    return specs


def target_shares(name):
    """Target share table per item (for tests and the report)."""
    kind, lvl = kind_of(name)
    return {"H1": (H1_TWO[lvl], H1_ONE[lvl]), "H3": (H3_TWO[lvl], H3_ONE[lvl])}.get(kind)


# ----------------------------------------------------------------------------------------------------------------------------
# one replicate
# ----------------------------------------------------------------------------------------------------------------------------
def h2_from_arrays(items3, B, seed, single_site_se):
    """Same computation as the H2 block of gstudy.hypotheses (same setup_sd call and seeds)."""
    rows, ps = [], []
    for j, i in enumerate(items3):
        sd = G.setup_sd(i["arr"], B, [seed, j, 7])
        se = float(single_site_se[i["name"]])
        ps.append(float(np.mean(sd["median_boot"] <= se)))
        rows.append(sd["median"])
    return G.iu_pvalue(ps), rows, sum(1 for x in ps if x < ALPHA)


def run_rep(args):
    name, rep, B = args
    t0 = time.perf_counter()
    kind, lvl = kind_of(name)
    si = SCEN_INDEX[name]
    rng = np.random.default_rng([SEED, 9000 + si, rep])
    seed = SEED + 100000 * (si + 1) + rep
    specs = scenario(name)
    row = {c: float("nan") for c in COLS}
    row.update(rep=rep, scenario=name)
    if kind == "H1":
        items4 = [dict(name=f"i{j}", arr=gen_term_array(rng, sp)) for j, sp in enumerate(specs)]
        stub = [dict(name="i0", arr=items4[0]["arr"][:, :, :, T1_INDEX])]          # H3 is not evaluated here (one cheap item)
        out = G.hypotheses(stub, items4, None, B=B, seed=seed, estimator="A1")
        h = out["H1"]
        row.update(p_H1=h["p_raw"], est_H1=h["estimate"], wording_H1=h["pooled_wording"], T_H1=h["pooled_T"])
    elif kind == "H3":
        items3 = [dict(name=f"i{j}", arr=S1.gen_delta(rng, sp, N_W, False, None)) for j, sp in enumerate(specs)]
        out = G.hypotheses(items3, None, None, B=B, seed=seed, estimator="A1")
        h = out["H3"]
        row.update(p_H3=h["p_raw"], est_H3=h["estimate"], MW_H3=h["pooled_MW"], W_H3=h["pooled_W"])
    else:
        items3 = [dict(name=f"i{j}", arr=S1.gen_delta(rng, sp, N_W, False, None)) for j, sp in enumerate(specs)]
        p, meds, n_hold = h2_from_arrays(items3, B, seed, {i["name"]: C_P for i in items3})
        row.update(p_H2=p, H2_n_hold=n_hold, H2_k=len(items3), H2_mean_median_sd=float(np.mean(meds)),
                   H2_min_median_sd=float(np.min(meds)), H2_max_median_sd=float(np.max(meds)))
    row["seconds"] = time.perf_counter() - t0
    return row


# ----------------------------------------------------------------------------------------------------------------------------
# resumable driver
# ----------------------------------------------------------------------------------------------------------------------------
def results_path(out, name):
    return Path(out) / f"results_{name}.csv"


def done_reps(path):
    path = Path(path)
    if not path.exists():
        return set()
    with open(path, newline="", encoding="utf8") as f:
        return {int(r["rep"]) for r in csv.DictReader(f) if r.get("rep", "") != ""}


def append_row(path, row):
    path = Path(path)
    new = not path.exists() or path.stat().st_size == 0
    with open(path, "a", newline="", encoding="utf8") as f:
        w = csv.DictWriter(f, COLS)
        if new:
            w.writeheader()
        w.writerow({c: row[c] for c in COLS})
        f.flush()
        os.fsync(f.fileno())


def pending_tasks(out, name, reps, B):
    done = done_reps(results_path(out, name))
    return [(name, r, B) for r in range(reps) if r not in done]


def _lower_priority():
    try:
        import psutil
        psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS if os.name == "nt" else 10)
    except Exception:
        pass


def free_phys_gb():
    sys.path.insert(0, str(HERE))
    import scoring
    r = scoring.free_ram_gb()
    return float("inf") if r is None else r["avail_phys_gb"]


def wait_ram(min_gb=6.0, log=print):
    paused = False
    while free_phys_gb() < min_gb:
        if not paused:
            log(f"[{time.strftime('%H:%M:%S')}] free RAM {free_phys_gb():.1f} GB < {min_gb} GB: pausing new tasks", flush=True)
            paused = True
        time.sleep(30)
    if paused:
        log(f"[{time.strftime('%H:%M:%S')}] RAM recovered ({free_phys_gb():.1f} GB): resuming", flush=True)


def drive(tasks_by_scen, out, workers, runner=run_rep, ram_gate=True):
    """Run tasks with at most `workers` in flight; write each finished replicate immediately."""
    t0 = time.time()
    with ProcessPoolExecutor(max_workers=workers, initializer=_lower_priority) as ex:
        for name, tasks in tasks_by_scen.items():
            it, pend, n_done = iter(tasks), {}, 0
            while True:
                while len(pend) < workers:
                    t = next(it, None)
                    if t is None:
                        break
                    if ram_gate:
                        wait_ram()
                    pend[ex.submit(runner, t)] = t
                if not pend:
                    break
                dn, _ = wait(list(pend), return_when=FIRST_COMPLETED)
                for f in dn:
                    row = f.result()
                    append_row(results_path(out, name), row)
                    del pend[f]
                    n_done += 1
                    if n_done % 25 == 0:
                        print(f"[{time.strftime('%H:%M:%S')}] {name}: {n_done}/{len(tasks)} new replicates, {time.time() - t0:.0f}s", flush=True)
            print(f"[{time.strftime('%H:%M:%S')}] {name} complete ({len(tasks)} new replicates) [{time.time() - t0:.0f}s]", flush=True)
    return time.time() - t0


def sha_lf(path):
    return hashlib.sha256(Path(path).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def git_head():
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()


def cmd_run(a):
    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    scens = a.scenarios.split(",")
    tasks = {}
    for n in scens:
        reps = a.reps if a.reps else REPS_DEFAULT[kind_of(n)[1]]
        tasks[n] = pending_tasks(out, n, reps, a.B)
    _lower_priority()
    wall = drive(tasks, out, a.workers)
    rj = out / "run.json"
    prev = json.loads(rj.read_text(encoding="utf8")) if rj.exists() else {}
    cmd = " ".join([".venv/Scripts/python.exe -I analysis/acme/simulate_G1b.py"] + sys.argv[1:])
    prev.update(
        config=dict(B=a.B, estimator="A1", alpha=ALPHA, pass_max=PASS_MAX, c_p=C_P, workers=a.workers,
                    reps={n: (a.reps if a.reps else REPS_DEFAULT[kind_of(n)[1]]) for n in scens} | prev.get("config", {}).get("reps", {}),
                    scenarios=SCENARIOS, shapes=dict(models=N_M, wordings=N_W, two_order_items=N2, one_order_items=N1, temperatures=N_T)),
        seeds=dict(base=SEED, replicate="default_rng([20261106, 9000+s, r])", spec="default_rng([20261106, 8500+s, item])",
                   estimator_seed="20261106 + 100000*(s+1) + r", scenario_index=SCEN_INDEX),
        git_head=git_head(), sha256_lf={p: sha_lf(ROOT / p) for p in ("analysis/acme/gstudy.py", "analysis/acme/simulate_G1.py", "analysis/acme/simulate_G1b.py")},
        commands=prev.get("commands", []) + [cmd], wall_s_sessions=prev.get("wall_s_sessions", []) + [round(wall, 1)])
    rj.write_text(json.dumps(prev, indent=1, default=float), encoding="utf8")


# ----------------------------------------------------------------------------------------------------------------------------
# aggregation
# ----------------------------------------------------------------------------------------------------------------------------
def load(out, name):
    import pandas as pd
    p = results_path(out, name)
    return pd.read_csv(p) if p.exists() else None


def rate(df, col):
    p = df[col].dropna()
    R = len(p)
    rej = int((p < ALPHA).sum())
    r = rej / R if R else float("nan")
    return dict(R=R, rej=rej, rate=r, se=math.sqrt(r * (1 - r) / R) if R else float("nan"), n_missing=int(len(df) - R))


def cmd_aggregate(a):
    out = ROOT / a.out
    rj = json.loads((out / "run.json").read_text(encoding="utf8"))
    res = {}
    for n in SCENARIOS:
        df = load(out, n)
        if df is not None and len(df):
            h = kind_of(n)[0]
            res[n] = dict(rate=rate(df, f"p_{h}"), secs=float(df["seconds"].sum()), df=df)
    L = ["# Gate G1b verdict (type-I error and power of H1-H3, synthetic data)", "",
         f"Estimator A-G1 (`A1`), B = {rj['config']['B']}, alpha = {ALPHA}, pass for a hypothesis: rejection rate under its boundary null <= "
         f"{PASS_MAX:.4f} (= 0.05 + 2 sqrt(0.05 x 0.95 / 500)). Rejection = raw p < 0.05 (H1 one-sided, H3 two-sided, H2 intersection-union as in `gstudy.hypotheses`). "
         "Monte Carlo SE = sqrt(r (1 - r) / R). Synthetic data only.", "",
         "## Type-I error under the boundary nulls", "", "| hypothesis | replicates | rejections | rejection rate | MC SE | limit | verdict |", "|---|---|---|---|---|---|---|"]
    for h in ("H1", "H2", "H3"):
        n = f"{h}_null"
        if n in res:
            r = res[n]["rate"]
            L.append(f"| {h} | {r['R']} | {r['rej']} | {r['rate']:.4f} | {r['se']:.4f} | {PASS_MAX:.4f} | **{'PASS' if r['rate'] <= PASS_MAX and r['R'] >= 500 else ('FAIL' if r['rate'] > PASS_MAX else 'INCOMPLETE')}** |")
    L += ["", "## Power (information only)", "", "| hypothesis | alternative | replicates | rejection rate | MC SE |", "|---|---|---|---|---|"]
    alts = {"H1": "wording (W + MW) 0.40 vs T 0.10", "H2": "true median set-up SD = 2 c_p = 0.4 ML1-SD (c_p = 0.2)", "H3": "MW 0.45 vs W 0.15"}
    for h in ("H1", "H2", "H3"):
        n = f"{h}_alt"
        if n in res:
            r = res[n]["rate"]
            L.append(f"| {h} | {alts[h]} | {r['R']} | {r['rate']:.3f} | {r['se']:.3f} |")
    L += ["", "## Diagnostics (means over replicates)", ""]
    for n, v in res.items():
        df, h = v["df"], kind_of(n)[0]
        if h == "H1":
            L.append(f"- `{n}`: mean estimate (wording - T) {df['est_H1'].mean():+.4f}, mean wording share {df['wording_H1'].mean():.4f}, mean T share {df['T_H1'].mean():.4f}; median p {df['p_H1'].median():.3f}.")
        elif h == "H3":
            L.append(f"- `{n}`: mean estimate (MW - W) {df['est_H3'].mean():+.4f}, mean MW {df['MW_H3'].mean():.4f}, mean W {df['W_H3'].mean():.4f}; median p {df['p_H3'].median():.3f}.")
        else:
            L.append(f"- `{n}`: mean over replicates and items of the estimated median set-up SD {df['H2_mean_median_sd'].mean():.4f} (true {C_P if n.endswith('null') else 2 * C_P}); "
                     f"mean number of items passing (item-level p < 0.05) {df['H2_n_hold'].mean():.2f} of {int(df['H2_k'].iloc[0])} (item-level rejection rate {df['H2_n_hold'].sum() / df['H2_k'].sum():.4f}); median p {df['p_H2'].median():.3f}.")
    tot_cpu = sum(v["secs"] for v in res.values())
    L += ["", "## Run", "", f"- CPU seconds summed over replicates: {tot_cpu:.0f} s ({tot_cpu / 3600:.2f} h) on {rj['config']['workers']} workers (below-normal priority); wall seconds per session: {rj.get('wall_s_sessions')}.",
          f"- git HEAD at run time: `{rj['git_head']}`.", "- SHA-256 (LF) of the code used: " + "; ".join(f"`{k}` {v[:12]}" for k, v in rj["sha256_lf"].items()) + ".",
          "- Commands:"] + [f"  - `{c}`" for c in rj["commands"]]
    L += ["", "## Definitions and choices (fixed by the brief and the prereg; stated for the record)", "",
          "- H1 null per item: two-order items (M, W, O, T): W .10, MW .15, T .10, MT .05, WT .05, MWT .05, M .10, O .05, MO .05, WO .05, residual .25. One-order items (M, W, T): W .10, MW .15, T .10, MT .05, WT .10, M .10, residual .40. Alternative: wording .40 (W .15, MW .25), T .10 (T .05, MT .02, WT .02, MWT .01 or T .04, MT .03, WT .03), remaining mass as in the null.",
          "- H3 null: two-order items W .30, MW .30, residual .40; one-order items W .30, MW .30 and the remaining .40 in the fixed M effect (the residual cannot be separated from MW in one-order items). Alternative: MW .45, W .15, remainder as in the null.",
          "- H2: design as scenario (e) of `simulate_G1.py` (shares from `shares_two/shares_one('e')`, rescaled by one factor per item). True set-up SD of model m = population SD of Delta[m, w, o] over the wording universe and the order set (sigma2_W + sigma2_MW + sigma2_WO + sigma2_res + mean_o (omega_o + gamma_mo)^2; one-order items sigma2_W + sigma2_MW); the item's true median over the 14 models is set to 0.2 (null) or 0.4 (alternative). The estimator uses the finite-sample SD (ddof 1) over 10 x n_o cells, so its small-sample bias belongs to what the gate measures.",
          "- H1 replicates call `hypotheses()` with one stub H3 item (T = 1 slice of item 0) to avoid building the full H3 pool; its H3 output is discarded. H3 replicates call `hypotheses()` with items3 only. H2 replicates use `setup_sd` and `iu_pvalue` with the same seeds as `hypotheses()` (equality checked in `tests/test_simulate_G1b.py`).",
          "- Fixed effects are sum-to-zero patterns with sum(x^2)/prod(n_f - 1) equal to the target component (the quadratic-form convention of the prereg); shares are component / sum of components.",
          "- Consequence (prereg section 6): a hypothesis that fails leaves the confirmatory family and is reported as exploratory; G1b does not change the estimator.", ""]
    (out / "VERDICT.md").write_text("\n".join(L), encoding="utf8")
    print("\n".join(L[:20]))


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    r = sub.add_parser("run")
    r.add_argument("--reps", type=int, default=0, help="override replicates per scenario (default 500 nulls, 300 alternatives)")
    r.add_argument("--B", type=int, default=1000)
    r.add_argument("--workers", type=int, default=2)
    r.add_argument("--out", default="runs/acme-G1b")
    r.add_argument("--scenarios", default=",".join(SCENARIOS))
    g = sub.add_parser("aggregate")
    g.add_argument("--out", default="runs/acme-G1b")
    a = ap.parse_args()
    if a.workers > 2 if hasattr(a, "workers") else False:
        raise SystemExit("at most 2 workers (brief)")
    cmd_run(a) if a.cmd == "run" else cmd_aggregate(a)


if __name__ == "__main__":
    main()

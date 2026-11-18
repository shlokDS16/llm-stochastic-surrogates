"""Gate G1 (recoverability) for the ACME G-study estimator, PREREG-acme.md section 6 (before any real data).

    .venv/Scripts/python.exe -I analysis/acme/simulate_G1.py [--reps 1000] [--B 2000] [--workers 5] [--out runs/acme-G1]
        [--variants as_written,untruncated] [--scenarios a,b,c,d,e,f,g,h25,h50]

Synthetic Delta arrays with the real shape: 14 models; 5 two-order items and 5 one-order items (10 items); scenarios
  (a) residual only, (b) W dominant, (c) M x W dominant, (d) O dominant (the 5 two-order items only), (e) all components 8-12 percent,
  (f) near-saturated binary items: latent logit effects through a logistic link with model-specific offsets (-6 .. 6) that push
      probabilities toward 0 and 1; Delta is the exact probability difference,
  (g) one model missing (scenario (e) with 13 models), (h25), (h50) the Arm S layer: scenario (f) probabilities, binomial draws with
      n = 25 or 50 per arm before differencing.
M and O are fixed facets (fixed effects drawn once per item); W is random (fresh draws each replicate). True components: for the
linear scenarios the generating values; for (f), (h) the population components of the transformed array, computed on 60,000
wordings (and, for (h), the mean binomial variance added to the residual; for one-order items to the M x W term).
One-order items have no O terms and the residual is M x W: that term is labelled MW (see gstudy.py), so the pooled MW share mixes
M x W (two-order items) and M x W + residual (one-order items), exactly as in the real analysis.

Levels evaluated: "pooled_mean" (mean over the 10 items, joint bootstrap: the quantity of hypotheses H1-H3; this is the level the pass
rule is applied to), and, as informational, "item2" (first two-order item) and "item1" (first one-order item).
Pass rule (PREREG section 6, applied as written, at the pooled level over all scenario-components):
  C1 |bias| of every share <= 0.02; C2 coverage of the 95 percent interval in [0.90, 0.98] for at least 90 percent of scenario-components;
  C3 false-positive rate of "interval lower bound > 0" <= 0.05 for every component whose true share is 0;
  C4 in every scenario where the largest true share is at least twice the next, the largest is ranked first (point estimates) in >= 90 percent.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import sys
import time
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
import numpy as np  # noqa: E402
from scipy.special import expit  # noqa: E402
from scipy.stats import norm  # noqa: E402

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import gstudy as G  # noqa: E402

SEED = 20261106
CANON = ["M", "O", "MO", "W", "MW", "WO", "res"]
N_M, N_W = 14, 10
N2, N1 = 5, 5                     # two-order and one-order items
SCEN_ORDER = ["a", "b", "c", "d", "e", "f", "g", "h25", "h50"]
SCEN_LABEL = {"a": "residual only", "b": "W dominant", "c": "MxW dominant", "d": "O dominant (two-order items)",
              "e": "all components 8-12%", "f": "saturated binary, logistic link", "g": "one model missing (13)",
              "h25": "Arm S binomial n=25", "h50": "Arm S binomial n=50"}
NW_BIG = 60000
LATENT_TOTAL = 2.0                # latent logit-scale variance of the effect in scenario (f)
OFF_RANGE = 6.0                   # model offsets from -6 to 6 on the logit scale


# ----------------------------------------------------------------------------------------------------------------------------
# item specifications
# ----------------------------------------------------------------------------------------------------------------------------
def _center_all(x):
    for _ in range(4):
        for ax in range(x.ndim):
            x = x - x.mean(axis=ax, keepdims=True)
    return x


def make_spec(rng, n_m, n_o, comp):
    """comp: dict of target components (M, O, MO, W, MW, WO, res; absent = 0). Fixed effects are sum-to-zero patterns with
    theta2_S = sum(effect^2) / df = target (the n - 1 convention of the prereg)."""
    a = _center_all(rng.standard_normal(n_m))
    a *= np.sqrt(comp.get("M", 0.0) * (n_m - 1) / (a ** 2).sum())
    if n_o == 2:
        o = np.array([-1.0, 1.0]) * np.sqrt(comp.get("O", 0.0) / 2.0)
        gm = _center_all(rng.standard_normal((n_m, n_o)))
        gm *= np.sqrt(comp.get("MO", 0.0) * (n_m - 1) * (n_o - 1) / (gm ** 2).sum())
    else:
        o = np.zeros(1)
        gm = np.zeros((n_m, 1))
    return dict(n_m=n_m, n_o=n_o, alpha=a, omega=o, gamma=gm,
                sW=comp.get("W", 0.0), sMW=comp.get("MW", 0.0), sWO=comp.get("WO", 0.0), sres=comp.get("res", 0.0), comp=dict(comp))


def gen_latent(rng, sp, nw):
    n_m, n_o = sp["n_m"], sp["n_o"]
    y = sp["alpha"][:, None, None] + sp["omega"][None, None, :] + sp["gamma"][:, None, :]
    y = y + np.sqrt(sp["sW"]) * rng.standard_normal((1, nw, 1)) + np.sqrt(sp["sMW"]) * rng.standard_normal((n_m, nw, 1))
    if n_o == 2:
        y = y + np.sqrt(sp["sWO"]) * rng.standard_normal((1, nw, n_o)) + np.sqrt(sp["sres"]) * rng.standard_normal((n_m, nw, n_o))
    return y


def gen_delta(rng, sp, nw, link, n_binom=None, return_p=False):
    """One item's Delta array (M, W, O) -> squeezed to (M, W) for one-order items."""
    d = gen_latent(rng, sp, nw)
    if link:
        base = sp["off"][:, None, None] + sp["base_sd"] * rng.standard_normal((1, nw, 1))
        base = np.broadcast_to(base, d.shape)
        p0, p1 = expit(base), expit(base + sp["mu_delta"] + d)
        if n_binom:
            delta = rng.binomial(n_binom, p1) / n_binom - rng.binomial(n_binom, p0) / n_binom
        else:
            delta = p1 - p0
        out = (delta, p0, p1)
    else:
        out = (d, None, None)
    if sp["n_o"] == 1:
        out = tuple(None if x is None else x[:, :, 0] for x in out)
    return out if return_p else out[0]


def shares_two(name, rng):
    if name == "a":
        return dict(res=1.0)
    if name == "b":
        return dict(W=0.7, res=0.3)
    if name == "c":
        return dict(MW=0.7, res=0.3)
    if name == "d":
        return dict(O=0.7, res=0.3)
    v = {k: rng.uniform(0.08, 0.12) for k in ("M", "O", "MO", "W", "MW", "WO")}      # e, f, g, h
    v["res"] = 1.0 - sum(v.values())
    return v


def shares_one(name, rng):
    if name == "a":
        return dict(MW=1.0)
    if name == "b":
        return dict(W=0.7, MW=0.3)
    if name == "c":
        return dict(MW=1.0)
    v = {k: rng.uniform(0.08, 0.12) for k in ("M", "W")}
    v["MW"] = 1.0 - sum(v.values())
    return v


_CACHE = {}


def scenario(name):
    """Specs, link/binomial flags and true shares. Deterministic from SEED, cached per process."""
    if name in _CACHE:
        return _CACHE[name]
    si = SCEN_ORDER.index(name)
    rng = np.random.default_rng([SEED, 9001, si])
    n_m = 13 if name == "g" else N_M
    base = "e" if name in ("f", "g", "h25", "h50") else name
    link = name in ("f", "h25", "h50")
    nb = {"h25": 25, "h50": 50}.get(name)
    n_two, n_one = (N2, 0) if name == "d" else (N2, N1)
    specs = []
    for j in range(n_two + n_one):
        n_o = 2 if j < n_two else 1
        sh = shares_two(base, rng) if n_o == 2 else shares_one(base, rng)
        total = LATENT_TOTAL if link else 1.0
        comp = {k: v * total for k, v in sh.items()}
        sp = make_spec(rng, n_m, n_o, comp)
        if link:
            sp["off"] = rng.permutation(np.linspace(-OFF_RANGE, OFF_RANGE, n_m))
            sp["base_sd"] = 0.5
            sp["mu_delta"] = 1.0
        specs.append(sp)
    truth = np.zeros((len(specs), len(CANON)))
    vbar = np.zeros(len(specs))
    for j, sp in enumerate(specs):
        if not link:
            c = np.array([sp["comp"].get(k, 0.0) for k in CANON])
            truth[j] = c / c.sum()
        else:
            r2 = np.random.default_rng([SEED, 9002, si, j])
            arr, p0, p1 = gen_delta(r2, sp, NW_BIG, True, None, return_p=True)
            fac = G.FACETS3 if sp["n_o"] == 2 else G.FACETS2
            d = G.decompose(arr, fac)
            comps = d["components_truncated"]
            vb = float(np.mean(p1 * (1 - p1) + p0 * (1 - p0)))      # variance of (phat1 - phat0) at n = 1, averaged over cells
            vbar[j] = vb
            truth[j] = _truth_with_noise(comps, sp["n_o"], vb / nb if nb else 0.0)
    out = dict(name=name, n_m=n_m, specs=specs, link=link, n_binom=nb, truth=truth, n_two=n_two, n_items=len(specs), vbar=vbar)
    _CACHE[name] = out
    return out


def _truth_with_noise(comps, n_o, add):
    c = {k: comps.get(k, 0.0) for k in CANON}
    c["res" if n_o == 2 else "MW"] += add
    v = np.array([c[k] for k in CANON])
    return v / v.sum()


# ----------------------------------------------------------------------------------------------------------------------------
# estimator variants evaluated on the same bootstrap draws
# ----------------------------------------------------------------------------------------------------------------------------
VARIANTS = {
    "as_written": dict(kind="plain", mode="truncated", bias="none", interval="percentile", rescale=False, shrink=False,
                       doc="PREREG as written: negative components set to 0, shares from truncated components, percentile interval (gstudy estimator 'prereg')"),
    "untruncated": dict(kind="plain", mode="untruncated", bias="none", interval="percentile", rescale=False, shrink=False,
                        doc="diagnostic D0: shares = component / sum of untruncated components, percentile interval"),
    "D1_centered": dict(kind="plain", mode="untruncated", bias="jackknife", interval="centered", rescale=False, shrink=False,
                        doc="diagnostic D1: D0 + delete-one-wording jackknife bias correction of the shares + interval centred on the corrected estimate (est + quantile - bootstrap mean)"),
    "D2_shrunk_centered": dict(kind="plain", mode="untruncated", bias="jackknife", interval="centered", rescale=True, shrink=True,
                               doc="diagnostic D2: D1 + bootstrap world with fixed effects shrunk to the unbiased estimates + deviations rescaled by sqrt(n_w/(n_w-1))"),
    "A1": dict(kind="A1", mode="untruncated", bias="jackknife", interval="student", rescale=False, shrink=True,
               doc="amendment A1 (gstudy estimator 'A1'): untruncated shares, delete-one-wording jackknife bias correction, studentized bootstrap-t interval "
                   "(inner jackknife SE in every bootstrap sample) in a bootstrap world with fixed effects shrunk to the unbiased estimates"),
}


def to_canon(names, x):
    out = np.zeros(x.shape[:-1] + (len(CANON),))
    for i, nm in enumerate(names):
        out[..., CANON.index(nm)] = x[..., i]
    return out


def run_rep(args):
    name, rep, B, variants = args
    sc = scenario(name)
    si = SCEN_ORDER.index(name)
    rng = np.random.default_rng([SEED, 7000 + si, rep])
    items = []
    for j, sp in enumerate(sc["specs"]):
        arr = gen_delta(rng, sp, N_W, sc["link"], sc["n_binom"])
        items.append(dict(name=f"i{j}", arr=arr, facets=G.FACETS3 if sp["n_o"] == 2 else G.FACETS2))
    seed = SEED + 10000 * (si + 1) + rep
    plain = [v for v in variants if VARIANTS[v]["kind"] == "plain"]
    pool = G.pool_items(items, B=B, seed=seed, jackknife=True) if plain else None
    pool_s = G.pool_items(items, B=B, seed=seed, jackknife=False, shrink_fixed=True) if any(VARIANTS[v]["shrink"] for v in plain) else None
    pool_a = G.pool_items(items, B=B, seed=seed, estimator="A1") if any(VARIANTS[v]["kind"] == "A1" for v in variants) else None
    names = (pool or pool_a)["names"]
    levels = ["pooled_mean", "item2"] + (["item1"] if sc["n_items"] > sc["n_two"] else [])
    sel_of = {"pooled_mean": list(range(sc["n_items"])), "item2": [0], "item1": [sc["n_two"]]}
    res = {}
    for v in variants:
        cfg = VARIANTS[v]
        arr = np.zeros((len(levels), 3, len(CANON)))
        if cfg["kind"] == "A1":
            for li, lv in enumerate(levels):
                sp = G.student_pooled(pool_a, np.eye(len(names)), sel=sel_of[lv])
                arr[li, 0], arr[li, 1], arr[li, 2] = to_canon(names, sp["est"]), to_canon(names, sp["lo"]), to_canon(names, sp["hi"])
            ip_for_median = to_canon(names, pool_a["item_point"])
        else:
            ip = to_canon(names, (pool["item_point_corrected_by_mode"] if cfg["bias"] == "jackknife" else pool["item_point_by_mode"])[cfg["mode"]])
            ib = to_canon(names, (pool_s if cfg["shrink"] else pool)["item_boot_by_mode"][cfg["mode"]])
            scale = math.sqrt(N_W / (N_W - 1)) if cfg["rescale"] else 1.0
            per = {"pooled_mean": (ip.mean(0), ib.mean(0)), "item2": (ip[0], ib[0])}
            if "item1" in levels:
                per["item1"] = (ip[sc["n_two"]], ib[sc["n_two"]])
            for li, lv in enumerate(levels):
                est, boot = per[lv]
                lo, hi = G.interval(est, boot, cfg["interval"], scale=scale)
                arr[li, 0], arr[li, 1], arr[li, 2] = est, lo, hi
            ip_for_median = ip
        res[v] = arr
        if v == variants[0]:
            res["median_est"] = np.median(ip_for_median, axis=0)
    return res


# ----------------------------------------------------------------------------------------------------------------------------
# aggregation and verdict
# ----------------------------------------------------------------------------------------------------------------------------
def true_levels(sc):
    t = {"pooled_mean": sc["truth"].mean(axis=0), "item2": sc["truth"][0]}
    if sc["n_items"] > sc["n_two"]:
        t["item1"] = sc["truth"][sc["n_two"]]
    return t


def aggregate(name, reps_out, variant, B):
    sc = scenario(name)
    tl = true_levels(sc)
    levels = list(tl)
    rows = []
    allr = np.stack([r[variant] for r in reps_out])                 # (R, L, 3, K)
    R = allr.shape[0]
    for li, lv in enumerate(levels):
        est, lo, hi = allr[:, li, 0], allr[:, li, 1], allr[:, li, 2]
        t = tl[lv]
        top = np.sort(t)[::-1]
        applicable = bool(top[0] >= 2 * top[1] - 1e-12) if top[0] > 0 else False
        rank_rate = float(np.mean(np.argmax(est, axis=1) == int(np.argmax(t)))) if applicable else float("nan")
        rank_any = float(np.mean(np.argmax(est, axis=1) == int(np.argmax(t))))
        for k, comp in enumerate(CANON):
            if lv == "item1" and comp in ("O", "MO", "WO", "res"):
                continue                                    # structurally absent in one-order items (the residual is MW)
            zero = bool(t[k] < 1e-12)
            rows.append(dict(scenario=name, scenario_label=SCEN_LABEL[name], level=lv, variant=variant, component=comp, n_models=sc["n_m"], reps=R, B=B,
                             true_share=float(t[k]), mean_estimate=float(est[:, k].mean()), bias=float(est[:, k].mean() - t[k]),
                             sd_estimate=float(est[:, k].std(ddof=1)),
                             coverage=float(np.mean((lo[:, k] <= t[k] + 1e-12) & (t[k] - 1e-12 <= hi[:, k]))),
                             lower_gt0_rate=float(np.mean(lo[:, k] > 1e-12)), true_is_zero=zero,
                             false_positive_rate=float(np.mean(lo[:, k] > 1e-12)) if zero else float("nan"),
                             mean_lo=float(lo[:, k].mean()), mean_hi=float(hi[:, k].mean()),
                             rank_applicable=applicable, rank_correct_rate=rank_rate, rank_correct_rate_any=rank_any,
                             true_top_component=CANON[int(np.argmax(t))]))
    return rows


def verdict(rows):
    """Apply the preregistered pass rule to the pooled_mean rows. Returns dict of criteria."""
    pr = [r for r in rows if r["level"] == "pooled_mean"]
    c1_viol = [(r["scenario"], r["component"], r["bias"]) for r in pr if abs(r["bias"]) > 0.02]
    c2_ok = [r for r in pr if 0.90 <= r["coverage"] <= 0.98]
    c2_frac = len(c2_ok) / len(pr)
    c3_rows = [r for r in pr if r["true_is_zero"]]
    c3_viol = [(r["scenario"], r["component"], r["false_positive_rate"]) for r in c3_rows if r["false_positive_rate"] > 0.05]
    c4 = {}
    for r in pr:
        if r["rank_applicable"]:
            c4[r["scenario"]] = r["rank_correct_rate"]
    c4_viol = [(s, v) for s, v in c4.items() if v < 0.90]
    return dict(
        C1=dict(pass_=not c1_viol, n_cells=len(pr), n_violations=len(c1_viol), worst=max(pr, key=lambda r: abs(r["bias"]))),
        C2=dict(pass_=c2_frac >= 0.90, fraction=c2_frac, n_cells=len(pr), n_ok=len(c2_ok)),
        C3=dict(pass_=not c3_viol, n_cells=len(c3_rows), n_violations=len(c3_viol), worst=max(c3_rows, key=lambda r: r["false_positive_rate"]) if c3_rows else None),
        C4=dict(pass_=not c4_viol, scenarios=c4, n_violations=len(c4_viol)),
        violations=dict(C1=c1_viol, C3=c3_viol, C4=c4_viol),
        overall=(not c1_viol) and c2_frac >= 0.90 and (not c3_viol) and (not c4_viol))


def write_csv(rows, path):
    import csv
    keys = list(rows[0])
    with open(path, "w", newline="", encoding="utf8") as f:
        w = csv.DictWriter(f, keys)
        w.writeheader()
        w.writerows(rows)


def verdict_md(results, cfg, runtime, notes=""):
    L = [f"# Gate G1 verdict (recoverability of the ACME G-study estimator)", "",
         f"Run: {cfg['reps']} replicates per scenario, B = {cfg['B']} bootstrap draws per item, seed {SEED}, scenarios {', '.join(cfg['scenarios'])}; "
         f"runtime {runtime:.0f} s on {cfg['workers']} workers. The pass rule is PREREG-acme.md section 6, applied as written to the pooled (mean over 10 items) level.", ""]
    L += ["## Summary", "", "| variant | C1 bias | C2 coverage | C3 false positives | C4 ranking | overall |", "|---|---|---|---|---|---|"]
    ok = lambda b: "PASS" if b else "FAIL"
    for v, (rows, vd) in results.items():
        L.append(f"| `{v}` | {ok(vd['C1']['pass_'])} | {ok(vd['C2']['pass_'])} ({vd['C2']['n_ok']}/{vd['C2']['n_cells']}) | {ok(vd['C3']['pass_'])} | {ok(vd['C4']['pass_'])} | **{ok(vd['overall'])}** |")
    L += ["", f"The preregistered estimator is `{list(results)[0]}`; its overall result is the G1 result under the rule as written. Other variants are diagnostic steps or the amendment (A1) and are not primary until approved.", ""]
    for v, (rows, vd) in results.items():
        L += [f"## Variant `{v}`: **{'PASS' if vd['overall'] else 'FAIL'}**", "", VARIANTS[v]["doc"], "",
              "| criterion | rule | result | verdict |", "|---|---|---|---|"]
        w = vd["C1"]["worst"]
        L.append(f"| C1 bias | abs(bias) of every share <= 0.02 | {vd['C1']['n_violations']} of {vd['C1']['n_cells']} scenario-components violate; worst {w['scenario']}/{w['component']} bias {w['bias']:+.3f} | {'PASS' if vd['C1']['pass_'] else 'FAIL'} |")
        L.append(f"| C2 coverage | 95% interval coverage in [0.90, 0.98] for >= 90% of scenario-components | {vd['C2']['n_ok']} of {vd['C2']['n_cells']} ({vd['C2']['fraction']:.1%}) | {'PASS' if vd['C2']['pass_'] else 'FAIL'} |")
        w = vd["C3"]["worst"]
        L.append(f"| C3 false positives | rate of lower bound > 0 <= 0.05 for true-zero components | {vd['C3']['n_violations']} of {vd['C3']['n_cells']} violate; worst {w['scenario']}/{w['component']} {w['false_positive_rate']:.3f} | {'PASS' if vd['C3']['pass_'] else 'FAIL'} |")
        L.append(f"| C4 ranking | largest share ranked first in >= 90% where >= 2x the next | " + ", ".join(f"{s}: {x:.3f}" for s, x in vd["C4"]["scenarios"].items()) + f" | {'PASS' if vd['C4']['pass_'] else 'FAIL'} |")
        L.append("")
        if vd["violations"]["C1"]:
            L.append("C1 violations (scenario, component, bias): " + "; ".join(f"{s}/{c} {b:+.3f}" for s, c, b in vd["violations"]["C1"][:40]) + ("; ..." if len(vd["violations"]["C1"]) > 40 else ""))
            L.append("")
        if vd["violations"]["C3"]:
            L.append("C3 violations (scenario, component, rate): " + "; ".join(f"{s}/{c} {b:.3f}" for s, c, b in vd["violations"]["C3"]))
            L.append("")
        # item-level informational
        il = [r for r in rows if r["level"] != "pooled_mean"]
        nb = sum(abs(r["bias"]) > 0.02 for r in il)
        nc = sum(0.90 <= r["coverage"] <= 0.98 for r in il)
        nz = [r for r in il if r["true_is_zero"]]
        fz = sum(r["false_positive_rate"] > 0.05 for r in nz)
        L.append(f"Informational, single-item levels (item2, item1; not gated): {nb} of {len(il)} abs(bias) > 0.02; coverage in range for {nc} of {len(il)} ({nc / len(il):.0%}); "
                 f"{fz} of {len(nz)} zero components with false-positive rate > 0.05.")
        L.append("")
    if notes:
        L += [notes, ""]
    return "\n".join(L)


def regen(out, tag=""):
    """Rebuild VERDICT.md from the results CSVs and run.json of a finished run (no simulation)."""
    import pandas as pd
    run = json.loads((out / f"run{tag}.json").read_text(encoding="utf8"))
    results = {}
    for v in VARIANTS:
        f = out / (f"results{tag}.csv" if v == "as_written" else f"results{tag}_{v}.csv")
        if f.exists():
            df = pd.read_csv(f)
            df["true_is_zero"] = df["true_is_zero"].astype(bool)
            df["rank_applicable"] = df["rank_applicable"].astype(bool)
            rows = df.to_dict("records")
            results[v] = (rows, verdict(rows))
    (out / f"VERDICT{tag}.md").write_text(verdict_md(results, run["cfg"], run["runtime_s"]), encoding="utf8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--regen", action="store_true", help="only rebuild VERDICT.md from the existing results in --out")
    ap.add_argument("--reps", type=int, default=1000)
    ap.add_argument("--B", type=int, default=2000)
    ap.add_argument("--workers", type=int, default=5)
    ap.add_argument("--out", default="runs/acme-G1")
    ap.add_argument("--variants", default="as_written,A1")
    ap.add_argument("--scenarios", default=",".join(SCEN_ORDER))
    ap.add_argument("--tag", default="")
    a = ap.parse_args()
    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    if a.regen:
        regen(out, a.tag)
        return
    scens = a.scenarios.split(",")
    variants = a.variants.split(",")
    t0 = time.time()
    results = {v: [] for v in variants}
    medians = {}
    with ProcessPoolExecutor(max_workers=a.workers) as ex:
        for name in scens:
            tasks = [(name, r, a.B, variants) for r in range(a.reps)]
            reps_out = list(ex.map(run_rep, tasks, chunksize=max(1, a.reps // (a.workers * 8))))
            for v in variants:
                results[v] += aggregate(name, reps_out, v, a.B)
            medians[name] = np.mean([r["median_est"] for r in reps_out], axis=0).tolist()
            print(f"scenario {name} done [{time.time() - t0:.0f}s]", flush=True)
    runtime = time.time() - t0
    verd = {}
    for v in variants:
        write_csv(results[v], out / (f"results{a.tag}.csv" if v == variants[0] else f"results{a.tag}_{v}.csv"))
        verd[v] = (results[v], verdict(results[v]))
        print(v, "PASS" if verd[v][1]["overall"] else "FAIL", {k: verd[v][1][k].get("pass_") for k in ("C1", "C2", "C3", "C4")}, flush=True)
    cfg = dict(reps=a.reps, B=a.B, scenarios=scens, workers=a.workers)
    (out / f"VERDICT{a.tag}.md").write_text(verdict_md(verd, cfg, runtime), encoding="utf8")
    (out / f"run{a.tag}.json").write_text(json.dumps(dict(cfg=cfg, runtime_s=runtime, pooled_median_share_mean=medians,
                                                          verdicts={v: {k: verd[v][1][k] for k in ("C1", "C2", "C3", "C4", "overall")} for v in variants}),
                                                     indent=1, default=float), encoding="utf8")
    print(f"runtime {runtime:.0f}s")


if __name__ == "__main__":
    main()

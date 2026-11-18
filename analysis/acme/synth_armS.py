"""Synthetic recoverability check of A1-S at the Arm S shape (errata E7 item 3). Synthetic data only; no real Arm S output enters except
the cell variances v_c of cells.csv (draw noise per cell), which the check needs to draw noise "from the real v_c".

Shape: 14 models; 4 wordings; 2 orders for AF, NR, P1, QA (facets M, W, O, T) and none for P3, P2a-d, P4 (facets M, W, T); 2 temperatures;
n = 50 draws per condition. For each of the 10 items the per-cell draw noise is that item's real v_c (ML1-SD^2) over all 14 models and
its 4 x [2] x 2 cells (cells without a finite v_c take the item's median; v_c = 0 cells stay 0). Draws are Gaussian with the cell mean
+-theta/2 for x = 1, 0 and SD s with 2 s^2 / n = v_c (so the real cell variance is reproduced; the binary +0.5 branch is covered by the
unit test of gstudy_armS.selftest, not by this check).

True model (the G1 convention of simulate_G1.py): M, O, T and their interactions fixed (drawn once per item and scenario, sum-to-zero,
theta2_S = sum of squared effects / df); W random with fresh iid effects at every replicate for W and every random interaction (MW, WO,
WT, MWO, MWT, WOT), residual iid. Scenario components are shares of a total effect variance tau^2 = r x mean(v_c) (r sets the draw-noise
share 1 / (1 + r)).
Scenarios (spanning the G1 scenarios a-e, plus T):
    a  residual only                  b  W 0.7, residual 0.3              c  M x W 0.7, residual 0.3
    dT T 0.7, residual 0.3            dO O 0.7, residual 0.3 (two-order items only)
    e3 every non-residual term 4-8% (two-order) or 6-10% (one-order), residual the rest, r = 3 (draw noise 25% of the total)
    e1 as e3 with r = 1 (draw noise 50%)       e12 as e3 with r = 12 (draw noise 7.7%)
Other scenarios use r = 3.

Two designs, both reported:
    G (generative, 2000 replicates): fresh wordings every replicate; the target is the known generating share of every term
      (E1 = share of the effect variance; E2 = share of effect variance + mean v_c, draw noise a component); bias = mean error. No bootstrap.
    C (conditional on the wordings, 500 replicates): one wording draw per (item, scenario) is fixed (the "world"); only the draws vary
      (as in the Arm S draw bootstrap, "conditional on these four wordings"). Target = the estimator at infinitely many draws on that world
      (estimate(theta, v, limit=True)); bias against it and coverage of the draw-bootstrap 95% percentile interval (B = 2000,
      seed 20261106) against it.
Pass rule (E7): |bias| <= 0.02 on every share and draw-bootstrap coverage in 0.90-0.98. Reported in summary.json both strictly (every
cell) and as the G1 rule (coverage in range for at least 90 percent of cells); see summary.json.

    .venv/Scripts/python.exe -I analysis/acme/synth_armS.py run [--design G,C] [--items ...] [--scen ...] [--workers 2]
    .venv/Scripts/python.exe -I analysis/acme/synth_armS.py aggregate
    .venv/Scripts/python.exe -I analysis/acme/synth_armS.py smoke
Parts are saved under runs/acme-S-gstudy/synthetic/parts/, one file per (design, item, scenario); existing parts are skipped (resumable).
"""
from __future__ import annotations

import argparse
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
import gstudy as G  # noqa: E402
import gstudy_armS as A  # noqa: E402

SEED = G.DEFAULT_SEED
OUT = ROOT / "runs" / "acme-S-gstudy"
SYN = OUT / "synthetic"
ITEMS = ["AF", "NR", "P1", "QA", "P3", "P2a", "P2b", "P2c", "P2d", "P4"]
TWO_ORDER = ("AF", "NR", "P1", "QA")
N_M, N_DRAWS = 14, 50
SCENARIOS = {  # name: (shares or generator tag, ratio)
    "a": ({"res": 1.0}, 3.0), "b": ({"W": 0.7, "res": 0.3}, 3.0), "c": ({"MW": 0.7, "res": 0.3}, 3.0),
    "dT": ({"T": 0.7, "res": 0.3}, 3.0), "dO": ({"O": 0.7, "res": 0.3}, 3.0),
    "e3": ("e", 3.0), "e1": ("e", 1.0), "e12": ("e", 12.0)}
R_G, R_C = 2000, 500


def scen_list(item):
    return [s for s in SCENARIOS if not (s == "dO" and item not in TWO_ORDER)]


def load_v(item, cells_path=OUT / "cells.csv"):
    """Real per-cell draw-noise variance v_c of the item, (14, 4, [2], 2) over all 14 models, ML1-SD^2."""
    import pandas as pd
    c = pd.read_csv(cells_path, dtype={"O": str, "W": str})
    c["O"] = c["O"].fillna("")
    c = c[c["item"] == item]
    models = sorted(c["model"].unique())
    assert len(models) == N_M
    orders = sorted(c["O"].unique())
    med = float(np.nanmedian(c["v_c"].to_numpy(float)))
    v = np.full((len(models), 4, len(orders), 2), np.nan)
    mi = {m: i for i, m in enumerate(models)}
    oi = {o: i for i, o in enumerate(orders)}
    for r in c.itertuples(index=False):
        v[mi[r.model], A.WS.index(r.W), oi[r.O], A.TS.index(float(r.T))] = r.v_c
    v = np.where(np.isfinite(v), v, med)
    return v[:, :, 0, :] if orders == [""] else v


# ----------------------------------------------------------------------------------------------------------------------------
# the true model
# ----------------------------------------------------------------------------------------------------------------------------
def _axes(label, facets, ndim):
    return tuple(range(ndim)) if label == "res" else tuple(facets.index(ch) for ch in label)


def _bshape(shape, axes):
    return tuple(shape[i] if i in axes else 1 for i in range(len(shape)))


def _center(x):
    for ax in range(x.ndim):
        x = x - x.mean(axis=ax, keepdims=True)
    return x


def make_item(item, v, scen, ratio=None, rng=None):
    """Item specification: shape, facets, names, true component values (variance units), fixed effects (drawn once) and the cell noise v."""
    shape = v.shape
    facets = A.facets_for(len(shape))
    probe = np.random.default_rng(0).standard_normal(shape)
    names, _, _ = G._core(probe, facets)
    spec, r0 = SCENARIOS[scen]
    ratio = r0 if ratio is None else ratio
    rng = rng if rng is not None else np.random.default_rng([SEED, 4242])
    fixed = [nm for nm in names if "W" not in nm and nm != "res"]
    rand = [nm for nm in names if nm not in fixed]
    if spec == "e":
        lo, hi = (0.04, 0.08) if len(shape) == 4 else (0.06, 0.10)
        sh = {nm: float(rng.uniform(lo, hi)) for nm in names if nm != "res"}
        sh["res"] = 1.0 - sum(sh.values())
    else:
        sh = dict(spec)
    vbar = float(v.mean())
    tau2 = ratio * vbar
    comps = {nm: sh.get(nm, 0.0) * tau2 for nm in names}
    F = np.zeros(shape)
    for nm in fixed:
        ax = _axes(nm, facets, len(shape))
        sizes = tuple(shape[i] for i in ax)
        x = _center(rng.standard_normal(sizes))
        df = float(np.prod([s - 1 for s in sizes]))
        if comps[nm] > 0:
            x = x * np.sqrt(comps[nm] * df / (x ** 2).sum())
        else:
            x = x * 0.0
        F = F + x.reshape(_bshape(shape, ax))
    return dict(item=item, shape=shape, facets=facets, names=names, fixed=fixed, rand=rand, comps=comps, F=F, v=np.asarray(v, float),
                vbar=vbar, scen=scen, ratio=ratio, tau2=tau2,
                truth_e1=np.array([comps[nm] for nm in names]) / sum(comps.values()),
                truth_e2=np.array([comps[nm] for nm in names] + [vbar]) / (sum(comps.values()) + vbar))


def draw_theta(sp, rng):
    """One realisation of the expected-effect array: fixed part plus fresh iid random terms."""
    shape, th = sp["shape"], sp["F"].copy()
    for nm in sp["rand"]:
        s2 = sp["comps"][nm]
        if s2 > 0:
            ax = _axes(nm, sp["facets"], len(shape))
            th = th + np.sqrt(s2) * rng.standard_normal(tuple(shape[i] if i in ax else 1 for i in range(len(shape))))
    return th


def draw_noise(sp, theta, rng, n=N_DRAWS):
    """Draws for every cell and condition (Gaussian, 2 s^2 / n = v_c), packed for the bootstrap, and the cell statistics."""
    s = np.sqrt(sp["v"] * n / 2.0)
    Y1 = theta[..., None] / 2.0 + s[..., None] * rng.standard_normal(theta.shape + (n,))
    Y0 = -theta[..., None] / 2.0 + s[..., None] * rng.standard_normal(theta.shape + (n,))
    nv = np.full(theta.shape, n)
    delta, vhat = A.cells_from_draws(Y1, nv, Y0, nv, 1.0, False)
    return dict(delta=delta, v=vhat, draws=dict(Y1=Y1, nv1=nv, Y0=Y0, nv0=nv, sd=1.0, binary=False))


def draw_dataset(sp, rng, theta=None):
    theta = draw_theta(sp, rng) if theta is None else theta
    d = draw_noise(sp, theta, rng)
    d["theta"] = theta
    return d


# ----------------------------------------------------------------------------------------------------------------------------
# tasks
# ----------------------------------------------------------------------------------------------------------------------------
def _spec(item, scen):
    ii, si = ITEMS.index(item), list(SCENARIOS).index(scen)
    return make_item(item, load_v(item), scen, rng=np.random.default_rng([SEED, 4242, ii, si])), ii, si


def run_G(item, scen, reps=R_G):
    sp, ii, si = _spec(item, scen)
    rng = np.random.default_rng([SEED, 5001, ii, si])
    e1, e2, l1, l2 = [], [], [], []
    for _ in range(reps):
        d = draw_dataset(sp, rng)
        est = A.estimate(d["delta"], d["v"], sp["facets"])
        lim = A.estimate(d["theta"], sp["v"], sp["facets"], limit=True)   # same wordings, infinitely many draws: the n_w = 4 part of any bias
        e1.append(est["e1"]); e2.append(est["e2"]); l1.append(lim["e1"]); l2.append(lim["e2"])
    return dict(e1=np.array(e1), e2=np.array(e2), lim1=np.array(l1), lim2=np.array(l2), truth_e1=sp["truth_e1"], truth_e2=sp["truth_e2"],
                names=sp["names"] + ["draw"])


def run_C(item, scen, reps=R_C, B=A.DEFAULT_B, chunk=100):
    sp, ii, si = _spec(item, scen)
    rng = np.random.default_rng([SEED, 6001, ii, si])
    theta = draw_theta(sp, rng)
    lim = A.estimate(theta, sp["v"], sp["facets"], limit=True)
    out = {k: [] for k in ("e1", "e2", "lo1", "hi1", "lo2", "hi2", "nlo1", "nhi1", "nlo2", "nhi2", "bm1", "bm2")}
    for r in range(reps):
        d = draw_noise(sp, theta, rng)
        est = A.estimate(d["delta"], d["v"], sp["facets"])
        b1, b2, n1, n2 = A.bootstrap_draws(**{k: d["draws"][k] for k in ("Y1", "nv1", "Y0", "nv0", "sd", "binary")}, facets=sp["facets"], B=B,
                                            seed=[SEED, 6002, ii, si, r], chunk=chunk, both=True)
        out["e1"].append(est["e1"]); out["e2"].append(est["e2"])
        for tag, x1, x2 in (("", b1, b2), ("n", n1, n2)):
            q1, q2 = A.percentile(x1), A.percentile(x2)
            out[tag + "lo1"].append(q1[0]); out[tag + "hi1"].append(q1[1]); out[tag + "lo2"].append(q2[0]); out[tag + "hi2"].append(q2[1])
        out["bm1"].append(b1.mean(0)); out["bm2"].append(b2.mean(0))
    res = {k: np.array(v) for k, v in out.items()}
    res.update(lim_e1=lim["e1"], lim_e2=lim["e2"], truth_e1=sp["truth_e1"], truth_e2=sp["truth_e2"], names=sp["names"] + ["draw"])
    return res


def part_path(design, item, scen):
    return SYN / "parts" / f"{design}_{item}_{scen}.npz"


def task(args):
    design, item, scen, reps = args
    p = part_path(design, item, scen)
    if p.exists():
        return str(p), 0.0
    t0 = time.time()
    res = run_G(item, scen, reps) if design == "G" else run_C(item, scen, reps)
    p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_name(p.stem + ".tmp.npz")
    np.savez_compressed(tmp, reps=reps, **{k: np.array(v) for k, v in res.items()})
    tmp.replace(p)
    return str(p), time.time() - t0


def run(designs, items, scens, workers, repsG, repsC):
    jobs = []
    for d in designs:
        for it in items:
            for sc in scen_list(it):
                if scens and sc not in scens:
                    continue
                jobs.append((d, it, sc, repsG if d == "G" else repsC))
    todo = [j for j in jobs if not part_path(*j[:3]).exists()]
    print(f"{len(jobs)} parts, {len(todo)} to do, workers {workers}", flush=True)
    t0 = time.time()
    if workers <= 1:
        for j in todo:
            p, dt = task(j)
            print(f"{time.time() - t0:8.0f}s  {Path(p).name}  {dt:.0f}s", flush=True)
    else:
        with ProcessPoolExecutor(workers) as ex:
            for p, dt in ex.map(task, todo):
                print(f"{time.time() - t0:8.0f}s  {Path(p).name}  {dt:.0f}s", flush=True)


# ----------------------------------------------------------------------------------------------------------------------------
# aggregation
# ----------------------------------------------------------------------------------------------------------------------------
def aggregate():
    import pandas as pd
    parts = sorted((SYN / "parts").glob("*.npz"))
    rowsG, rowsC = [], []
    for p in parts:
        design, item, scen = p.stem.split("_", 2)
        z = np.load(p)
        names = [str(x) for x in z["names"]]
        R = int(z["reps"])
        for basis, e, truth in (("E1", z["e1"], z["truth_e1"]), ("E2", z["e2"], z["truth_e2"])):
            if design == "C":
                truth = z["lim_" + basis.lower()]
            err = e - truth[None, :]
            k = "1" if basis == "E1" else "2"
            lo, hi, nlo, nhi = (z["lo" + k], z["hi" + k], z["nlo" + k], z["nhi" + k]) if design == "C" else (None,) * 4
            for i, nm in enumerate(names):
                if basis == "E1" and nm == "draw":
                    continue
                row = dict(design=design, item=item, scenario=scen, basis=basis, term=nm, reps=R, truth=float(truth[i]),
                           mean_est=float(e[:, i].mean()), bias=float(err[:, i].mean()), bias_se=float(err[:, i].std(ddof=1) / np.sqrt(R)),
                           sd_est=float(e[:, i].std(ddof=1)))
                if design == "G":
                    lim = (z["lim1"] if basis == "E1" else z["lim2"])
                    el = lim - z["truth_" + basis.lower()][None, :]
                    dd = err - el
                    row.update(bias_wordings_only=float(el[:, i].mean()), bias_draw_attributable=float(dd[:, i].mean()),
                               bias_draw_attributable_se=float(dd[:, i].std(ddof=1) / np.sqrt(R)), median_err=float(np.median(err[:, i])),
                               iqr_est=float(np.subtract(*np.quantile(e[:, i], [0.75, 0.25]))))
                if design == "C":
                    cov = np.mean((lo[:, i] <= truth[i]) & (truth[i] <= hi[:, i]))
                    covn = np.mean((nlo[:, i] <= truth[i]) & (truth[i] <= nhi[:, i]))
                    row.update(coverage=float(cov), coverage_se=float(np.sqrt(max(cov * (1 - cov), 1e-12) / R)),
                               width=float(np.mean(hi[:, i] - lo[:, i])), coverage_naive=float(covn), width_naive=float(np.mean(nhi[:, i] - nlo[:, i])),
                               boot_mean_minus_est=float((z["bm" + k][:, i] - e[:, i]).mean()),
                               true_zero=bool(abs(z["truth_" + basis.lower()][i]) < 1e-12))
                (rowsC if design == "C" else rowsG).append(row)
    G_, C_ = pd.DataFrame(rowsG), pd.DataFrame(rowsC)
    SYN.mkdir(parents=True, exist_ok=True)
    G_.to_csv(SYN / "bias_G.csv", index=False)
    C_.to_csv(SYN / "bias_coverage_C.csv", index=False)
    s = {}
    if len(G_):
        for b in ("E1", "E2"):
            x = G_[G_["basis"] == b]
            s["G_" + b] = dict(cells=len(x), reps_per_cell=int(x["reps"].min()), max_abs_bias=float(x["bias"].abs().max()),
                               n_abs_bias_gt_0p02=int((x["bias"].abs() > 0.02).sum()),
                               worst=x.loc[x["bias"].abs().idxmax(), ["item", "scenario", "term", "bias", "bias_se"]].to_dict(),
                               max_abs_bias_wordings_only=float(x["bias_wordings_only"].abs().max()),
                               n_wordings_only_gt_0p02=int((x["bias_wordings_only"].abs() > 0.02).sum()),
                               max_abs_bias_draw_attributable=float(x["bias_draw_attributable"].abs().max()),
                               n_draw_attributable_gt_0p02=int((x["bias_draw_attributable"].abs() > 0.02).sum()),
                               worst_draw_attributable=x.loc[x["bias_draw_attributable"].abs().idxmax(), ["item", "scenario", "term", "bias_draw_attributable", "bias_draw_attributable_se"]].to_dict(),
                               pass_strict=bool((x["bias"].abs() <= 0.02).all()))
    if len(C_):
        s["C_bias"] = dict(cells=len(C_), reps_per_cell=int(C_["reps"].min()), max_abs_bias=float(C_["bias"].abs().max()),
                           n_abs_bias_gt_0p02=int((C_["bias"].abs() > 0.02).sum()),
                           worst_bias=C_.loc[C_["bias"].abs().idxmax(), ["item", "scenario", "basis", "term", "bias", "bias_se"]].to_dict(),
                           pass_strict=bool((C_["bias"].abs() <= 0.02).all()))
        nz = ~C_["true_zero"]
        for tag, col in (("corrected", "coverage"), ("naive", "coverage_naive")):
            inr = (C_[col] >= 0.90) & (C_[col] <= 0.98)
            w = (C_[col] - 0.95).abs().idxmax()
            s["C_coverage_" + tag] = dict(cells=len(C_), reps_per_cell=int(C_["reps"].min()), min=float(C_[col].min()), median=float(C_[col].median()),
                                          max=float(C_[col].max()), worst=C_.loc[w, ["item", "scenario", "basis", "term", col]].to_dict(),
                                          frac_cells_in_0p90_0p98=float(inr.mean()), frac_nonzero_truth_cells_in_range=float(inr[nz].mean()),
                                          n_below_0p90=int((C_[col] < 0.90).sum()), n_above_0p98=int((C_[col] > 0.98).sum()),
                                          pass_strict=bool(inr.all()), pass_g1_rule=bool(inr.mean() >= 0.90))
        t = C_.groupby(["scenario", "basis"]).agg(cells=("coverage", "size"), cov_corrected_min=("coverage", "min"), cov_corrected_median=("coverage", "median"),
                                                  cov_corrected_max=("coverage", "max"), cov_naive_min=("coverage_naive", "min"),
                                                  cov_naive_median=("coverage_naive", "median"), cov_naive_max=("coverage_naive", "max"),
                                                  max_abs_bias=("bias", lambda x: x.abs().max())).reset_index()
        t.to_csv(SYN / "coverage_by_scenario.csv", index=False)
    if len(G_):
        t = G_.groupby(["scenario", "basis"]).agg(cells=("bias", "size"), max_abs_bias=("bias", lambda x: x.abs().max()),
                                                  max_abs_bias_wordings_only=("bias_wordings_only", lambda x: x.abs().max()),
                                                  max_abs_bias_draw_attributable=("bias_draw_attributable", lambda x: x.abs().max())).reset_index()
        t.to_csv(SYN / "bias_by_scenario.csv", index=False)
    (SYN / "summary.json").write_text(json.dumps(s, indent=1, default=float), encoding="utf8")
    print(json.dumps(s, indent=1, default=float))
    return s


def _md(df, fmt="{:.3f}"):
    cols = list(df.columns)
    out = ["| " + " | ".join(cols) + " |", "|" + "---|" * len(cols)]
    for r in df.itertuples(index=False):
        out.append("| " + " | ".join(fmt.format(x) if isinstance(x, float) else str(x) for x in r) + " |")
    return "\n".join(out)


def report():
    """Print the report tables (markdown) from the CSVs and summary.json."""
    import pandas as pd
    s = json.loads((SYN / "summary.json").read_text())
    bs = pd.read_csv(SYN / "bias_by_scenario.csv")
    cs = pd.read_csv(SYN / "coverage_by_scenario.csv")
    nw = pd.read_csv(SYN / "nw_check.csv")
    parts = []
    parts.append("### Design G, bias by scenario (max over items and terms)\n" + _md(bs))
    parts.append("### Design C, coverage and bias by scenario (min / median / max over items and terms)\n" + _md(cs))
    parts.append("### n_w check of the harness (infinite draws, AF and P3)\n" + _md(nw.groupby(["n_w", "basis"]).agg(max_abs_bias=("max_abs_bias", "max")).reset_index()))
    parts.append("### summary.json\n```json\n" + json.dumps(s, indent=1) + "\n```")
    print("\n\n".join(parts))


def nwcheck(reps=1000):
    """Harness validation: the infinite-draw estimator against the generating shares at n_w = 4 and n_w = 12 wordings (the real v_c pattern
    tiled). If the harness and the E2 split are right, the bias at 12 wordings is near 0 (G1: |bias| <= 0.004 for A1 at 10 wordings) and
    the n_w = 4 bias is the ratio bias of A1 at 3 df. Writes nw_check.csv."""
    import pandas as pd
    rows = []
    for item in ("AF", "P3"):
        v4 = load_v(item)
        for nw in (4, 12):
            v = np.concatenate([v4] * (nw // 4), axis=1)
            for scen in ("a", "b", "c", "dT", "e3"):
                sp = make_item(item, v, scen, rng=np.random.default_rng([SEED, 4243, nw]))
                rng = np.random.default_rng([SEED, 7001, nw, list(SCENARIOS).index(scen)])
                L1, L2 = [], []
                for _ in range(reps):
                    lim = A.estimate(draw_theta(sp, rng), sp["v"], sp["facets"], limit=True)
                    L1.append(lim["e1"]); L2.append(lim["e2"])
                for basis, L, tr in (("E1", L1, sp["truth_e1"]), ("E2", L2, sp["truth_e2"])):
                    L = np.array(L)
                    b = L.mean(0) - tr
                    rows.append(dict(item=item, n_w=nw, scenario=scen, basis=basis, reps=reps, max_abs_bias=float(np.abs(b).max()),
                                     worst_term=(sp["names"] + ["draw"])[int(np.abs(b).argmax())] if basis == "E2" else sp["names"][int(np.abs(b).argmax())],
                                     max_se=float((L.std(0, ddof=1) / np.sqrt(reps)).max())))
    df = pd.DataFrame(rows)
    SYN.mkdir(parents=True, exist_ok=True)
    df.to_csv(SYN / "nw_check.csv", index=False)
    print(df.to_string(index=False))


def smoke(reps=20, B=300):
    """Small, fast pass over both designs for one two-order and one one-order item; prints timings. Writes nothing to parts/."""
    for item, scen in (("AF", "e3"), ("P3", "b")):
        for design, fn in (("G", lambda: run_G(item, scen, reps * 5)), ("C", lambda: run_C(item, scen, reps, B))):
            t0 = time.time()
            r = fn()
            print(item, scen, design, f"{time.time() - t0:.1f}s", "bias max", float(np.abs(r["e2"].mean(0) - (r["truth_e2"] if design == "G" else r["lim_e2"])).max()))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", choices=["run", "aggregate", "smoke", "nwcheck", "report"])
    ap.add_argument("--design", default="G,C")
    ap.add_argument("--items", default=",".join(ITEMS))
    ap.add_argument("--scen", default="")
    ap.add_argument("--workers", type=int, default=2)
    ap.add_argument("--repsG", type=int, default=R_G)
    ap.add_argument("--repsC", type=int, default=R_C)
    a = ap.parse_args(argv)
    if a.cmd == "smoke":
        smoke()
    elif a.cmd == "aggregate":
        aggregate()
    elif a.cmd == "nwcheck":
        nwcheck()
    elif a.cmd == "report":
        report()
    else:
        run(a.design.split(","), [i for i in a.items.split(",") if i], [s for s in a.scen.split(",") if s], a.workers, a.repsG, a.repsC)


if __name__ == "__main__":
    main()

"""Sensitivity of the model-spread-versus-human-interval placement (larger / overlap / smaller) to (a) dropping grids with
near-deterministic cells and (b) removing the response-format factor (F0 cells only, and F1 cells only). CPU only; no model
generation: the stored responses runs/pilot/<model>/<paradigm>.jsonl (+ topup) are re-analysed with the A1 estimator.

    .venv/Scripts/python.exe -I analysis/pilot/placement_sensitivity.py [--out runs/pilot-placement-sensitivity] [--smoke]

Steps: (1) re-run the full grid exactly as analysis/pilot/analyze_pilot.py does (primary metric, seed 1, B = 2000, K = 200) and
assert that S, dbar and its interval equal the stored analysis_<paradigm>.json (guards the re-implementation);
(2) drop the F factor (keep the cells at one format level), same estimator and seed, design W x T (x O for P1): 8 or 16 cells;
(3) placement = side_by_side.spread_statement(S_lo, S_hi, human S^H_lo, S^H_hi) with the A1 human interval of table_a1.csv.
--smoke analyses 1 model x 7 paradigms only.
Outputs: placement_by_grid.csv, placement_counts.csv, summary.md, config.json, env.json, log.txt.
"""
import argparse
import hashlib
import itertools
import json
import platform
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import estimators as E  # noqa: E402
import analyze_pilot as AP  # noqa: E402
from side_by_side import MODELS, PARADIGMS, spread_statement  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--out", default="runs/pilot-placement-sensitivity")
ap.add_argument("--smoke", action="store_true")
a = ap.parse_args()
out = ROOT / (a.out + ("-smoke" if a.smoke else ""))
out.mkdir(parents=True, exist_ok=True)
LOG = []


def log(*x):
    s = " ".join(str(i) for i in x)
    LOG.append(s)
    print(s, flush=True)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def cells_for(model, paradigm):
    """Same row loading, validity rule and cell construction as analyze_pilot.analyze (topup on, unfinished invalid, standardised)."""
    rows = AP.load(ROOT / "runs/pilot" / model / f"{paradigm}.jsonl")
    tfile = ROOT / "runs/pilot" / model / f"{paradigm}.topup512.jsonl"
    if tfile.exists():
        rep = {r["key"]: r for r in AP.load(tfile)}
        rows = [rep.get(r["key"], r) for r in rows]
    for r in rows:
        r["valid"] = bool(r["valid"]) and r["finished"]
        if paradigm.startswith("P2") and r["valid"] and not (r["y"] is not None and r["y"] > 0):
            r["valid"] = False
    sampled = [r for r in rows if not r["greedy"]]
    Ws, Fs, Ts = (sorted({r[k] for r in sampled}) for k in ("W", "F", "T"))
    Os = sorted({r["O"] for r in sampled if r["O"]}) or [None]
    levels = [len(Ws), len(Fs), len(Ts)] + ([len(Os)] if Os != [None] else [])
    cr = {}
    for r in sampled:
        key = (Ws.index(r["W"]), Fs.index(r["F"]), Ts.index(r["T"])) + ((Os.index(r["O"]),) if Os != [None] else ())
        cr.setdefault(key, []).append(r)
    mid, kind, tf, _ = AP.METRICS[paradigm][0]
    cells = {}
    for key in itertools.product(*[range(L) for L in levels]):
        rs = [r for r in cr.get(key, []) if r["valid"]]
        y1 = np.array([r["y"] for r in rs if r["x"] == 1], float)
        y0 = np.array([r["y"] for r in rs if r["x"] == 0], float)
        if kind == "cont":
            y1, y0 = tf(y1), tf(y0)
        cells[key] = (y1, y0)
    floor = AP.sd_floor(paradigm, mid) if kind == "cont" else 0.0
    return cells, levels, Fs, kind, floor, ("formula" if kind == "binary" else "splithalf")


def run(cells, levels, factors, kind, floor, vmeth):
    rng = np.random.default_rng(1)
    r = E.estimate2(cells, E.Design(factors, levels), kind, rng=rng, B=2000, K=200, var_method=vmeth, sd_floor=floor, intervals=("ti_boot",))
    if r["status"] != "ok":
        return None
    iv = r["intervals"]["ti_boot"]
    return dict(C=r["C"], dbar=r["dbar"], S=r["S"], S_lo=iv["S"][0], S_hi=iv["S"][1], sigma=r["sign_stability"], dm2s_lower=iv["dbar_minus_2S_lower"])


t0 = time.time()
t = pd.read_csv(ROOT / "runs/pilot-side-by-side/table_a1.csv")
models = MODELS[:1] if a.smoke else MODELS
rows = []
for m in models:
    for p in PARADIGMS:
        cells, levels, Fs, kind, floor, vmeth = cells_for(m, p)
        factors = ["W", "F", "T"] + (["O"] if len(levels) == 4 else [])
        full = run(cells, levels, factors, kind, floor, vmeth)
        stored = json.loads((ROOT / "runs/pilot" / m / f"analysis_{p}.json").read_text(encoding="utf8"))["metrics"]["primary"]["split_half"]
        assert full is not None and abs(full["S"] - stored["S"]) < 1e-9 and abs(full["dbar"] - stored["dbar"]) < 1e-9 and abs(full["S_hi"] - stored["S_ci"][1]) < 1e-9, (m, p, full, stored["S"])
        tr = t[(t.model == m) & (t.paradigm == p)].iloc[0]
        rec = dict(model=m, paradigm=p, human_S_lo=tr.human_S_lo, human_S_hi=tr.human_S_hi, nd_flag_any=bool(tr.nd_flag_any), nd_n_flagged=int(tr.nd_n_flagged),
                   original_placement=tr.spread_vs_human, full_S=full["S"], full_S_lo=full["S_lo"], full_S_hi=full["S_hi"])
        assert spread_statement(full["S_lo"], full["S_hi"], tr.human_S_lo, tr.human_S_hi) == tr.spread_vs_human
        for fi, tag in ((0, "F0"), (1, "F1")):
            sub = {k[:1] + k[2:]: v for k, v in cells.items() if k[1] == fi}
            lv = [levels[0]] + levels[2:]
            fc = ["W", "T"] + (["O"] if len(levels) == 4 else [])
            rr = run(sub, lv, fc, kind, floor, vmeth)
            if rr is None:
                rec.update({f"{tag}_status": "deterministic_cells"})
                continue
            rec.update({f"{tag}_C": rr["C"], f"{tag}_S": rr["S"], f"{tag}_S_lo": rr["S_lo"], f"{tag}_S_hi": rr["S_hi"], f"{tag}_dbar": rr["dbar"],
                        f"{tag}_placement": spread_statement(rr["S_lo"], rr["S_hi"], tr.human_S_lo, tr.human_S_hi), f"{tag}_status": "ok"})
        rows.append(rec)
        log(f"{m} {p}: orig {rec['original_placement']} S={rec['full_S']:.3f} | F0 {rec.get('F0_placement')} S={rec.get('F0_S', float('nan')):.3f} | F1 {rec.get('F1_placement')} S={rec.get('F1_S', float('nan')):.3f}")
df = pd.DataFrame(rows)
df.to_csv(out / "placement_by_grid.csv", index=False)

SHORT = {"larger": "larger", "no statement (intervals overlap)": "overlap", "smaller": "smaller"}


def counts(sub, col):
    c = sub[col].map(SHORT).value_counts()
    return int(c.get("larger", 0)), int(c.get("overlap", 0)), int(c.get("smaller", 0))


nd_free = df[~df.nd_flag_any]
spec = [("original (all grids, F kept)", df, "original_placement"),
        ("(a) grids without near-deterministic cells, F kept", nd_free, "original_placement"),
        ("(a') grids with near-deterministic cells, F kept", df[df.nd_flag_any], "original_placement"),
        ("(b) F0 cells only (F removed), all grids", df, "F0_placement"),
        ("(b) F0 cells only, grids without near-deterministic cells", nd_free, "F0_placement"),
        ("(b') F1 cells only (F removed), all grids", df, "F1_placement"),
        ("(b') F1 cells only, grids without near-deterministic cells", nd_free, "F1_placement")]
crow = []
for name, sub, col in spec:
    L, O, S_ = counts(sub, col)
    crow.append(dict(analysis=name, n_grids=len(sub), larger=L, overlap=O, smaller=S_))
    log(f"{name}: n={len(sub)} larger {L} / overlap {O} / smaller {S_}")
cdf = pd.DataFrame(crow)
cdf.to_csv(out / "placement_counts.csv", index=False)
# per paradigm for F0
pp = df.assign(o=df.original_placement.map(SHORT), f0=df.F0_placement.map(SHORT)).groupby("paradigm").apply(
    lambda g: pd.Series(dict(orig_larger=int((g.o == "larger").sum()), f0_larger=int((g.f0 == "larger").sum()), f0_overlap=int((g.f0 == "overlap").sum()),
                             f0_smaller=int((g.f0 == "smaller").sum()))), include_groups=False)
pp.to_csv(out / "placement_by_paradigm.csv")
md = ["# Placement sensitivity (A1 estimator, existing responses)\n",
      f"Models: {len(models)}; smoke={a.smoke}. Placement = LLM S interval wholly above (larger), overlapping, or wholly below (smaller) the human S^H interval of `runs/pilot-side-by-side/table_a1.csv`. "
      "The full-grid re-analysis reproduces the stored S, dbar and S upper bound of every grid to 1e-9 (assert in the script). Evidence level E4.\n",
      "| analysis | grids | larger | overlap | smaller |", "|---|---|---|---|---|"]
md += [f"| {r['analysis']} | {r['n_grids']} | {r['larger']} | {r['overlap']} | {r['smaller']} |" for _, r in cdf.iterrows()]
md += ["", "Per paradigm (original larger count; F0-only larger / overlap / smaller):", "", "| paradigm | original larger | F0 larger | F0 overlap | F0 smaller |", "|---|---|---|---|---|"]
md += [f"| {i} | {r.orig_larger} | {r.f0_larger} | {r.f0_overlap} | {r.f0_smaller} |" for i, r in pp.iterrows()]
(out / "summary.md").write_text("\n".join(md) + "\n", encoding="utf8")
(out / "config.json").write_text(json.dumps(dict(script="analysis/pilot/placement_sensitivity.py", script_sha256=sha(__file__), estimators_sha256=sha(HERE / "estimators.py"),
                                              analyze_pilot_sha256=sha(HERE / "analyze_pilot.py"), seed=1, B=2000, K=200, smoke=a.smoke, models=models,
                                              input_table_a1_sha256=sha(ROOT / "runs/pilot-side-by-side/table_a1.csv"),
                                              note="seed 1 per estimate2 call, identical to analyze_pilot.py; F0 = first sorted format level"), indent=1), encoding="utf8")
(out / "env.json").write_text(json.dumps(dict(python=platform.python_version(), numpy=np.__version__, pandas=pd.__version__, platform=platform.platform()), indent=1), encoding="utf8")
log(f"done in {time.time() - t0:.0f} s")
(out / "log.txt").write_text("\n".join(LOG) + "\n", encoding="utf8")

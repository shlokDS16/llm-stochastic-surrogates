"""Gate G4, L-S agreement (PREREG-acme section 6; compute-plan 7.2 G4). CPU. Diagnostic only: decides how a model is analysed, never
enters H1-H3.

Frozen rule: on the Arm S prompts (W0-W3, F0, T 0.7 and 1.0), per (model, item, W, O, T) the Arm L effect against the Arm S sampled
effect (parsed answers, canonical scale), by response type (binary, rating, numeric). Arm L is exact, so the slope is the OLS slope of
the Arm S effect on the Arm L effect. Criteria per response type and per model: slope in [0.9, 1.1] and SD of the z-scores (difference /
binomial or sample SE of the Arm S effect) at most 1.3. The pooled slope per type is reported and decides nothing. A failing model is
analysed from Arm S only or excluded, with the reason stated (that choice is recorded by the lead, not made here).

Readings fixed in this script (written before any Arm S effect was computed, 2026-11-07, CRP-S09):
  - Response types: binary = P1, AF, NR; rating = P3, QA; numeric = P2a-P2d, P4.
  - Canonical Arm S outcome, the same direction as armL_outcomes.py: P1 1 if the sure option; AF 1 for the anti-speech answer (Yes to
    forbid, x = 1; No to allow, x = 0); NR 1 for Yes to the US question; P3 rating (reversed scale r -> 10 - r); QA 10 - r on the
    forward scale, r on the reversed; P2a-d log x over x > 0; P4 log(1 + x) over x >= 0. Invalid parses and out-of-domain numbers drop.
  - Arm S effect = mean canonical outcome at x = 1 minus at x = 0 over the valid samples of the cell.
  - SE: binary uses the binomial SE at the exact Arm L probabilities, sqrt(p1(1-p1)/n1 + p0(1-p0)/n0) (the null of faithful
    sampling, and defined when a sampled proportion is 0 or 1); rating and numeric use the sample SE sqrt(s1^2/n1 + s0^2/n0).
    A cell with SE = 0 (read numerically: SE <= SE_EPS = 1e-9) has no z (counted, left out of the SD).
  - Arm L effect: effects.csv, variant main, the same (model, item, W, O, T). Pilot items in Arm S carry O = None; for P3 that is the
    forward scale (the pilot ran only the forward scale), for P2 and P4 there is no order.
  - Arm S sources: new items runs/acme-S/<model>/<item>.S3.jsonl; pilot items runs/acme-S1/<model>/<item>.jsonl for the eight
    non-pilot models, runs/pilot/<model>/<item>.jsonl for the six pilot models; non-greedy F0 rows only.
  - A model-item pair excluded by the valid-mass rule (gate_g3.py exclusions.csv) is left out. A cell needs >= 2 valid samples per
    condition. A model passes when every response type it has passes; a model with any planned cell missing or short of n = 50
    rows is 'incomplete' (no verdict). A type with fewer than 3 cells or no spread in the Arm L effect is 'not evaluable'.
  - OLS with intercept; slope SE reported.

    .venv/Scripts/python.exe -I analysis/acme/gate_g4.py inventory          (counts Arm S rows per cell; reads no answers)
    .venv/Scripts/python.exe -I analysis/acme/gate_g4.py run [--effects runs/acme-L/outcomes/effects.csv]
                             [--exclude runs/acme-L/outcomes/exclusions.csv] [--out runs/acme-L/G4]
    .venv/Scripts/python.exe -I analysis/acme/gate_g4.py selftest           (synthetic data: slope near 1, z SD near 1)
Writes cells.csv, by_model_type.csv, pooled_type.csv, G4.json.
"""
from __future__ import annotations

import argparse
import json
import math
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
TYPE = {"P1": "binary", "AF": "binary", "NR": "binary", "P3": "rating", "QA": "rating",
        "P2a": "numeric", "P2b": "numeric", "P2c": "numeric", "P2d": "numeric", "P4": "numeric"}
NEW, PILOT = ("AF", "NR", "QA"), ("P1", "P2a", "P2b", "P2c", "P2d", "P3", "P4")
BINARY_SE = "armL"   # sensitivity reading (E7 item 1): 'sampled' = binomial SE at the sampled proportions
SE_EPS = 1e-9   # numerical zero for the SE of a cell (fix 2026-11-07 18:30 NST: constant log samples gave z ~1e13)
ORDERS = {"P1": ["sure_first", "risky_first"], "QA": ["forward", "reversed"], "AF": ["yes_first", "no_first"],
          "NR": ["yes_first", "no_first"], "P3": [None]}
WS, TS, N = ("W0", "W1", "W2", "W3"), (0.7, 1.0), 50
SLOPE_LO, SLOPE_HI, ZSD_MAX = 0.9, 1.1, 1.3


def source(runs: Path, model: str, item: str) -> Path:
    if item in NEW:
        return runs / "acme-S" / model / f"{item}.S3.jsonl"
    p = runs / "acme-S1" / model / f"{item}.jsonl"
    return p if p.exists() else runs / "pilot" / model / f"{item}.jsonl"


def load_rows(path: Path, item: str) -> list[dict]:
    if not path.exists():
        return []
    out = []
    for line in path.open(encoding="utf8"):
        if not line.strip():
            continue
        r = json.loads(line)
        if r.get("greedy") or r.get("F") != "F0" or float(r["T"]) not in TS:
            continue
        out.append(r)
    return out


def canon(item: str, r: dict):
    """Canonical outcome of one sampled answer, or None when invalid or out of domain."""
    if not r.get("valid") or r.get("parsed") is None:
        return None
    v = r["parsed"]
    if item == "P1":
        return 1.0 if v == r["sure_label"] else 0.0
    if item == "AF":
        return 1.0 if v == ("Yes" if r["x"] == 1 else "No") else 0.0
    if item == "NR":
        return 1.0 if v == "Yes" else 0.0
    if item == "P3":
        return 10.0 - float(v) if r.get("O") == "reversed" else float(v)
    if item == "QA":
        return float(v) if r.get("O") == "reversed" else 10.0 - float(v)
    x = float(v)
    if item == "P4":
        return math.log1p(x) if x >= 0 else None
    return math.log(x) if x > 0 else None


def l_order(item: str, O) -> str:
    if O is None:
        return "forward" if item == "P3" else ""
    return O


def planned_cells(item: str):
    for W in WS:
        for O in ORDERS.get(item, [None]):
            for T in TS:
                yield W, O, T


def inventory(runs: Path, models: list[str]) -> pd.DataFrame:
    rows = []
    for m in models:
        for it in TYPE:
            src = source(runs, m, it)
            have = {}
            for r in load_rows(src, it):
                k = (r["W"], r.get("O"), float(r["T"]), int(r["x"]))
                have[k] = have.get(k, 0) + 1
            for W, O, T in planned_cells(it):
                rows.append(dict(model=m, item=it, W=W, O=O, T=T, src=str(src.relative_to(runs.parent)) if src.exists() else "",
                                 n1=have.get((W, O, T, 1), 0), n0=have.get((W, O, T, 0), 0)))
    inv = pd.DataFrame(rows)
    inv["complete"] = (inv["n1"] >= N) & (inv["n0"] >= N)
    return inv


def ols(x: np.ndarray, y: np.ndarray):
    if len(x) < 3 or np.ptp(x) == 0:
        return None, None, None
    X = np.column_stack([np.ones_like(x), x])
    beta, *_ = np.linalg.lstsq(X, y, rcond=None)
    res = y - X @ beta
    s2 = res @ res / (len(x) - 2)
    se = math.sqrt(s2 / ((x - x.mean()) ** 2).sum())
    return float(beta[1]), float(beta[0]), se


def summarise(c: pd.DataFrame) -> dict:
    c = c[np.isfinite(c["dL"].to_numpy(float)) & np.isfinite(c["dS"].to_numpy(float))]   # no Arm L value (valid mass 0) only with --no-exclude
    slope, icpt, se = ols(c["dL"].to_numpy(float), c["dS"].to_numpy(float))
    z = c["z"].to_numpy(float)
    z = z[np.isfinite(z)]
    zsd = float(np.std(z, ddof=1)) if len(z) >= 2 else None
    ev = slope is not None and zsd is not None
    return dict(n_cells=len(c), n_z=len(z), n_z_undefined=int(len(c) - len(z)), slope=slope, slope_se=se, intercept=icpt, z_sd=zsd,
                evaluable=ev, slope_ok=(SLOPE_LO <= slope <= SLOPE_HI) if ev else None, z_sd_ok=(zsd <= ZSD_MAX) if ev else None,
                passes=(SLOPE_LO <= slope <= SLOPE_HI and zsd <= ZSD_MAX) if ev else None)


def run(runs: Path, effects: Path, exclude: Path | None, out: Path) -> dict:
    e = pd.read_csv(effects, dtype=str, keep_default_na=False)
    e = e[(e["variant"] == "main") & (e["T"].astype(float).isin(TS)) & (e["W"].isin(WS))]
    models = sorted(e["model"].unique())
    excl = set()
    if exclude and exclude.exists():
        ex = pd.read_csv(exclude, dtype=str)
        excl = set(zip(ex["model"], ex["item"]))
    L = {(r.model, r.item, r.W, r.O, float(r.T)): r for r in e.itertuples(index=False)}
    inv = inventory(runs, models)
    cells = []
    for m in models:
        for it in TYPE:
            if (m, it) in excl:
                continue
            data = {}
            for r in load_rows(source(runs, m, it), it):
                y = canon(it, r)
                if y is not None:
                    data.setdefault((r["W"], r.get("O"), float(r["T"]), int(r["x"])), []).append(y)
            for W, O, T in planned_cells(it):
                y1, y0 = np.array(data.get((W, O, T, 1), [])), np.array(data.get((W, O, T, 0), []))
                lr = L.get((m, it, W, l_order(it, O), T))
                if lr is None or lr.delta == "" or len(y1) < 2 or len(y0) < 2:
                    cells.append(dict(model=m, item=it, type=TYPE[it], W=W, O=O, T=T, n1=len(y1), n0=len(y0), dL=None, dS=None, se=None,
                                      z=None, usable=False))
                    continue
                dL, pL1, pL0 = float(lr.delta), float(lr.y1), float(lr.y0)
                dS = float(y1.mean() - y0.mean())
                if TYPE[it] == "binary":
                    q1, q0 = (pL1, pL0) if BINARY_SE == "armL" else (float(y1.mean()), float(y0.mean()))
                    se = math.sqrt(q1 * (1 - q1) / len(y1) + q0 * (1 - q0) / len(y0))
                else:
                    se = math.sqrt(y1.var(ddof=1) / len(y1) + y0.var(ddof=1) / len(y0))
                z = (dS - dL) / se if se > SE_EPS else None   # a constant sample gives SE ~1e-15, not exactly 0
                cells.append(dict(model=m, item=it, type=TYPE[it], W=W, O=O, T=T, n1=len(y1), n0=len(y0), dL=dL, dS=dS, se=se, z=z,
                                  usable=True))
    c = pd.DataFrame(cells)
    out.mkdir(parents=True, exist_ok=True)
    c.to_csv(out / "cells.csv", index=False)
    u = c[c["usable"]]
    bm = []
    for (m, t), g in u.groupby(["model", "type"]):
        bm.append(dict(model=m, type=t, **summarise(g)))
    bm = pd.DataFrame(bm)
    bm.to_csv(out / "by_model_type.csv", index=False)
    pooled = pd.DataFrame([dict(type=t, **summarise(g)) for t, g in u.groupby("type")])
    pooled.to_csv(out / "pooled_type.csv", index=False)
    verdict = {}
    for m in models:
        inc = inv[(inv["model"] == m) & (~inv.apply(lambda r: (r["model"], r["item"]) in excl, axis=1))]
        if not inc["complete"].all():
            verdict[m] = dict(status="incomplete", missing_cells=int((~inc["complete"]).sum()))
            continue
        g = bm[bm["model"] == m]
        ev = g[g["evaluable"] == True]  # noqa: E712
        fails = [f"{r.type}: slope {r.slope:.3f}, z SD {r.z_sd:.3f}" for r in ev.itertuples() if not r.passes]
        verdict[m] = dict(status="fail" if fails else "pass", failing_types=fails,
                          not_evaluable=sorted(set(g["type"]) - set(ev["type"])) + sorted({"binary", "rating", "numeric"} - set(g["type"])))
    res = dict(rule=dict(slope=[SLOPE_LO, SLOPE_HI], z_sd_max=ZSD_MAX, T=list(TS), W=list(WS), F="F0", n_per_condition=N),
               effects=str(effects), exclusions=sorted(f"{m}|{i}" for m, i in excl), n_cells=len(c), n_usable=int(c["usable"].sum()),
               verdict=verdict, models_pass=sorted(m for m, v in verdict.items() if v["status"] == "pass"),
               models_fail=sorted(m for m, v in verdict.items() if v["status"] == "fail"),
               models_incomplete=sorted(m for m, v in verdict.items() if v["status"] == "incomplete"),
               G4_complete=all(v["status"] != "incomplete" for v in verdict.values()))
    (out / "G4.json").write_text(json.dumps(res, indent=1), encoding="utf8")
    return res


def selftest() -> None:
    """Synthetic Arm L probabilities and means, Arm S sampled from them: a faithful sampler must pass (slope near 1, z SD near 1),
    and a sampler whose effects are halved must fail on slope."""
    rng = np.random.default_rng(20261107)
    for shrink, expect in ((1.0, "pass"), (0.5, "fail")):
        with tempfile.TemporaryDirectory() as td:
            runs = Path(td) / "runs"
            eff = []
            models = ["mA", "mB"]
            for m in models:
                for it in TYPE:
                    src = source(runs, m, it) if it in NEW else runs / "acme-S1" / m / f"{it}.jsonl"
                    src.parent.mkdir(parents=True, exist_ok=True)
                    with src.open("w", encoding="utf8") as fo:
                        for W, O, T in planned_cells(it):
                            for x in (1, 0):
                                if TYPE[it] == "binary":
                                    pL = float(rng.uniform(0.15, 0.85))
                                    mu = pL
                                elif TYPE[it] == "rating":
                                    mu = float(rng.uniform(3, 7))
                                else:
                                    mu = float(rng.uniform(4, 8))
                                eff.append(dict(model=m, item=it, W=W, O=l_order(it, O), variant="main", T=str(T), x=x, mu=mu))
                            m1 = [d for d in eff if (d["model"], d["item"], d["W"], d["O"], d["T"]) == (m, it, W, l_order(it, O), str(T))]
                            mu1 = next(d["mu"] for d in m1 if d["x"] == 1)
                            mu0 = next(d["mu"] for d in m1 if d["x"] == 0)
                            centre = (mu1 + mu0) / 2
                            for x, mu in ((1, centre + shrink * (mu1 - centre)), (0, centre + shrink * (mu0 - centre))):
                                for r in range(N):
                                    rec = dict(model=m, W=W, F="F0", T=T, O=O, x=x, r=r, greedy=False, valid=True)
                                    if it == "P1":
                                        rec.update(sure_label="A", parsed="A" if rng.random() < mu else "B")
                                    elif it == "AF":
                                        hit = rng.random() < mu
                                        rec.update(parsed=("Yes" if x == 1 else "No") if hit else ("No" if x == 1 else "Yes"))
                                    elif it == "NR":
                                        rec.update(parsed="Yes" if rng.random() < mu else "No")
                                    elif it in ("P3", "QA"):
                                        canon_v = float(np.clip(rng.normal(mu, 1.5), -50, 60))
                                        raw = canon_v if (it == "P3") == (O != "reversed") else 10 - canon_v
                                        rec.update(parsed=raw)
                                    else:
                                        lv = rng.normal(mu, 1.0)
                                        rec.update(parsed=float(math.expm1(lv) if it == "P4" else math.exp(lv)))
                                    fo.write(json.dumps(rec) + "\n")
            ef = pd.DataFrame(eff)
            k = ["model", "item", "W", "O", "variant", "T"]
            w = ef.pivot_table(index=k, columns="x", values="mu").reset_index()
            w = w.rename(columns={1: "y1", 0: "y0"})
            w["delta"] = w["y1"] - w["y0"]
            (Path(td) / "effects.csv").write_text(w.to_csv(index=False), encoding="utf8")
            res = run(runs, Path(td) / "effects.csv", None, Path(td) / "out")
            bm = pd.read_csv(Path(td) / "out" / "by_model_type.csv")
            print(f"shrink {shrink}:")
            print(bm[["model", "type", "n_cells", "slope", "z_sd", "passes"]].to_string(index=False))
            got = {v["status"] for v in res["verdict"].values()}
            assert got == {expect}, (shrink, res["verdict"])
    print("selftest OK")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("step", choices=["inventory", "run", "selftest"])
    ap.add_argument("--runs", default="runs")
    ap.add_argument("--effects", default="runs/acme-L/outcomes/effects.csv")
    ap.add_argument("--exclude", default="runs/acme-L/outcomes/exclusions.csv")
    ap.add_argument("--out", default="runs/acme-L/G4")
    ap.add_argument("--binary-se", choices=["armL", "sampled"], default="armL", help="sensitivity: SE at sampled proportions")
    ap.add_argument("--no-exclude", action="store_true", help="sensitivity: no valid-mass exclusion inside G4")
    a = ap.parse_args()
    if a.step == "selftest":
        return selftest()
    runs = ROOT / a.runs
    if a.step == "inventory":
        import yaml
        models = sorted(yaml.safe_load((ROOT / "analysis/acme/models.yaml").read_text(encoding="utf8"))["models"])
        inv = inventory(runs, models)
        s = inv.groupby("model").agg(cells=("complete", "size"), complete=("complete", "sum"))
        print(s.to_string())
        print(f"complete {int(inv['complete'].sum())} of {len(inv)} planned cells")
        return
    global BINARY_SE
    BINARY_SE = a.binary_se
    res = run(runs, ROOT / a.effects, None if a.no_exclude else ROOT / a.exclude, ROOT / a.out)
    print(json.dumps({k: res[k] for k in ["n_cells", "n_usable", "models_pass", "models_fail", "models_incomplete", "G4_complete"]}))


if __name__ == "__main__":
    main()

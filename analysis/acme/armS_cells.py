"""Arm S cell table and rosters for the A1-S decomposition (errata E7, item 2(a); EXPERT-statistician.md section 1).

Reads the Arm S sampled answers exactly as gate_g4.py does (its source(), load_rows(), canon(): F0, non-greedy rows, T 0.7 and 1.0,
wordings W0-W3; the same canonical outcomes as armL_outcomes.py) and writes, under runs/acme-S-gstudy/:

  cells.csv          one row per (model, item, W, O, T): rows1/rows0 (draws on disk), n1/n0 (valid draws used), valid1/valid0
                     (n / rows, the parse-validity share), ybar1/ybar0, s1/s0 (sample SD, ddof 1; raw canonical scale), sd (the item's
                     ML1 sd_within), delta = (ybar1 - ybar0) / sd, v_c (ML1-SD^2 units; see below) and v_c_raw (canonical scale).
  roster_strict.csv  per (model, item): share of (W, O, T, x) conditions with validity >= 0.9, min validity, largest x1-x0 validity gap,
  roster_loose.csv   ok flag. Strict: >= 95% of conditions at validity >= 0.9 and gap <= 0.1 in every (W, O, T). Loose: 0.8 and 0.2.
                     Outcome-blind: uses validity only.
  scale_check.csv    canonical scale of gate_g4 against the scale of runs/human-ml1-acme/arml_scales.csv, item by item.

v_c = s1^2/n1 + s0^2/n0 with the sample variances (ddof 1) of the valid canonical outcomes, divided by sd^2. Binary items (P1, AF, NR):
binomial variance at the sampled proportion, p(1-p)/n per condition, where p is replaced by (k + 0.5)/(n + 1) when the sampled p is
0 or 1 (E7 item 2(a)). Only cell effects (already seen inside G4) and validity are computed here: no variance component, no share.

    .venv/Scripts/python.exe -I analysis/acme/armS_cells.py            (writes the three tables)
    .venv/Scripts/python.exe -I analysis/acme/armS_cells.py selftest
"""
from __future__ import annotations

import argparse
import math
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
import gate_g4 as g4  # noqa: E402

BINARY = ("P1", "AF", "NR")
ITEMS = tuple(g4.TYPE)
OUT = ROOT / "runs" / "acme-S-gstudy"
SCALES = ROOT / "runs" / "human-ml1-acme" / "arml_scales.csv"
STRICT = dict(valid=0.9, share=0.95, gap=0.1)
LOOSE = dict(valid=0.8, share=0.95, gap=0.2)
# the scale each item is on in gate_g4.canon(), written out for the check against arml_scales.csv
G4_SCALE = {"P1": "0/1", "AF": "0/1", "NR": "0/1", "P3": "1-9", "QA": "1-9",
            "P2a": "y_log", "P2b": "y_log", "P2c": "y_log", "P2d": "y_log", "P4": "y_log"}


def arm_s_models(runs: Path) -> list[str]:
    return sorted(p.name for p in (runs / "acme-S").iterdir() if p.is_dir())


def collect(runs: Path, model: str, item: str) -> dict:
    """{(W, O, T, x): [rows, [valid canonical outcomes]]} for one model-item pair, rows read as gate_g4 does."""
    cell: dict = {}
    for r in g4.load_rows(g4.source(runs, model, item), item):
        k = (r["W"], r.get("O"), float(r["T"]), int(r["x"]))
        c = cell.setdefault(k, [0, []])
        c[0] += 1
        y = g4.canon(item, r)
        if y is not None:
            c[1].append(y)
    return cell


def cell_variance(y: np.ndarray, binary: bool) -> float:
    """Variance of the cell mean of one condition (canonical scale)."""
    n = len(y)
    if binary:
        if n < 1:
            return float("nan")
        k = float(y.sum())
        p = k / n
        if p == 0.0 or p == 1.0:
            p = (k + 0.5) / (n + 1)
        return p * (1 - p) / n
    if n < 2:
        return float("nan")
    return float(y.var(ddof=1) / n)


def cell_row(model, item, W, O, T, c1, c0, sd) -> dict:
    y1, y0 = np.array(c1[1], float), np.array(c0[1], float)
    n1, n0 = len(y1), len(y0)
    binary = item in BINARY
    ok = n1 >= 2 and n0 >= 2
    vraw = cell_variance(y1, binary) + cell_variance(y0, binary) if (n1 >= 1 and n0 >= 1) else float("nan")
    row = dict(model=model, item=item, W=W, O="" if O is None else O, T=T, n1=n1, n0=n0,
               valid1=n1 / c1[0] if c1[0] else float("nan"), valid0=n0 / c0[0] if c0[0] else float("nan"),
               ybar1=float(y1.mean()) if n1 else float("nan"), ybar0=float(y0.mean()) if n0 else float("nan"),
               s1=float(y1.std(ddof=1)) if n1 >= 2 else float("nan"), s0=float(y0.std(ddof=1)) if n0 >= 2 else float("nan"))
    row["delta"] = (row["ybar1"] - row["ybar0"]) / sd if (n1 and n0) else float("nan")
    row["v_c"] = vraw / sd ** 2 if ok or (binary and n1 >= 1 and n0 >= 1) else float("nan")
    row.update(sd=sd, rows1=c1[0], rows0=c0[0], v_c_raw=vraw if ok or binary else float("nan"))
    return row


def roster_row(model, item, cell: dict) -> dict:
    """Roster statistics of one model-item pair (the arithmetic of runs/gate-audits/expert-stat/roster.py)."""
    v = {k: (c[0] and len(c[1]) / c[0]) for k, c in cell.items()}
    vals = np.array(list(v.values()), float)
    gaps = [abs(v[(W, O, T, 1)] - v[(W, O, T, 0)]) for (W, O, T, x) in v if x == 1 and (W, O, T, 0) in v]
    return dict(model=model, item=item, n_conditions=len(vals), share_cells_ge90=float(np.mean(vals >= 0.9)),
                share_cells_ge80=float(np.mean(vals >= 0.8)), min_v=float(vals.min()), max_imb=float(max(gaps)) if gaps else float("nan"))


def scale_table(sd: dict) -> pd.DataFrame:
    sc = pd.read_csv(SCALES, dtype={"item": str}).set_index("item")
    rows = []
    for it in ITEMS:
        rows.append(dict(item=it, gate_g4_scale=G4_SCALE[it], arml_scales_scale=sc.loc[it, "scale"], match=G4_SCALE[it] == sc.loc[it, "scale"],
                         sd_within=float(sc.loc[it, "sd_within"])))
    return pd.DataFrame(rows)


def load_sd() -> dict:
    sc = pd.read_csv(SCALES, dtype={"item": str})
    return dict(zip(sc["item"], sc["sd_within"].astype(float)))


def build(runs: Path, out: Path) -> dict:
    sd = load_sd()
    models = arm_s_models(runs)
    cells, ros = [], []
    for m in models:
        for it in ITEMS:
            cell = collect(runs, m, it)
            ros.append(roster_row(m, it, cell))
            for W, O, T in g4.planned_cells(it):
                c1 = cell.get((W, O, T, 1), [0, []])
                c0 = cell.get((W, O, T, 0), [0, []])
                cells.append(cell_row(m, it, W, O, T, c1, c0, sd[it]))
    out.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(cells).to_csv(out / "cells.csv", index=False)
    r = pd.DataFrame(ros)
    for tag, rule in (("strict", STRICT), ("loose", LOOSE)):
        key = "share_cells_ge90" if tag == "strict" else "share_cells_ge80"
        d = r.copy()
        d["ok"] = (d[key] >= rule["share"]) & (d["max_imb"] <= rule["gap"])
        d["rule"] = f"share of conditions with validity >= {rule['valid']} is >= {rule['share']}; x1-x0 validity gap <= {rule['gap']}"
        d.to_csv(out / f"roster_{tag}.csv", index=False)
    sct = scale_table(sd)
    sct.to_csv(out / "scale_check.csv", index=False)
    return dict(models=len(models), cells=len(cells), scale_match=bool(sct["match"].all()))


def counts(path: Path) -> dict:
    d = pd.read_csv(path)
    return d.groupby("item")["ok"].sum().astype(int).to_dict()


def draws_for(runs: Path, model: str, item: str) -> dict:
    """{(W, O, T, x): (rows, array of valid canonical outcomes)} for the draw-level bootstrap."""
    return {k: (c[0], np.array(c[1], float)) for k, c in collect(runs, model, item).items()}


def selftest() -> None:
    # binary variance rules
    assert math.isclose(cell_variance(np.array([1.0] * 50), True), (50.5 / 51) * (1 - 50.5 / 51) / 50)
    assert math.isclose(cell_variance(np.array([0.0] * 50), True), (0.5 / 51) * (1 - 0.5 / 51) / 50)
    y = np.array([1.0] * 20 + [0.0] * 30)
    assert math.isclose(cell_variance(y, True), 0.4 * 0.6 / 50)
    assert math.isclose(cell_variance(np.array([1.0, 3.0, 5.0]), False), 4.0 / 3)
    # cell_row: delta and v_c in ML1-SD units
    c1 = [50, list(np.linspace(0, 8, 50))]
    c0 = [50, list(np.linspace(0, 4, 49))]
    r = cell_row("m", "P3", "W0", None, 1.0, c1, c0, 2.0)
    assert math.isclose(r["delta"], (4.0 - 2.0) / 2.0, abs_tol=1e-12) and r["O"] == ""
    assert math.isclose(r["v_c"], r["v_c_raw"] / 4.0) and math.isclose(r["valid0"], 49 / 50)
    # roster arithmetic on a hand-made pair: one condition below 0.9
    cell = {(w, None, t, x): [50, [1.0] * 50] for w in g4.WS for t in g4.TS for x in (1, 0)}
    assert roster_row("m", "P3", cell)["share_cells_ge90"] == 1.0
    cell[("W0", None, 0.7, 1)] = [50, [1.0] * 40]
    rr = roster_row("m", "P3", cell)
    assert rr["share_cells_ge90"] == 15 / 16 and math.isclose(rr["max_imb"], 0.2)
    print("armS_cells selftest OK")


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("cmd", nargs="?", default="build", choices=["build", "selftest"])
    ap.add_argument("--runs", default=str(ROOT / "runs"))
    ap.add_argument("--out", default=str(OUT))
    a = ap.parse_args(argv)
    if a.cmd == "selftest":
        selftest()
        return
    res = build(Path(a.runs), Path(a.out))
    print(res)
    for tag in ("strict", "loose"):
        print(tag, counts(Path(a.out) / f"roster_{tag}.csv"))


if __name__ == "__main__":
    main()

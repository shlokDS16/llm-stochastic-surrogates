"""Project GPU-hours for the full design from measured per-response times (batch logs of probe/smoke runs).

    .venv/Scripts/python.exe -I analysis/pilot/project_budget.py [--n 50] [--probe runs/pilot-probe]

Responses per model = sum over paradigms of cells x 2 conditions x n (+ one greedy response per prompt):
P1: 32 cells; P2a-d, P3, P4: 16 cells each; half of the cells use F0, half F1.
Measured models use their own seconds per response (separately for F0 and F1); models without a measurement are
marked ESTIMATE and scaled from the measured model of the same quantisation class (see SCALE).
Cut order from the design: n (not below 30), then the F1 format level.
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
CELLS = {"P1": 32, "P2a": 16, "P2b": 16, "P2c": 16, "P2d": 16, "P3": 16, "P4": 16}
# ESTIMATE rules for models not yet measured: multiply the measured reference model's seconds per response
SCALE = {
    "qwen2.5-1.5b-instruct": ("olmo2-1b-instruct", 1.2),     # bf16, similar size
    "granite-3.3-2b-instruct": ("olmo2-1b-instruct", 1.8),   # bf16, 2.5B
    "qwen2.5-7b-instruct": ("qwen2.5-7b-instruct", 1.0),       # measured
    "granite-3.3-8b-instruct": ("granite-3.3-8b-instruct", 1.0),   # measured
}
ALL = ["olmo2-1b-instruct", "olmo2-7b-instruct", "qwen2.5-1.5b-instruct", "qwen2.5-7b-instruct", "granite-3.3-2b-instruct", "granite-3.3-8b-instruct"]


def measured(probe):
    out = {}
    for d in sorted(Path(probe).glob("*")):
        files = list(d.glob("*.batches.jsonl"))
        if not files:
            continue
        rows = [json.loads(l) for f in files for l in f.read_text().splitlines() if l.strip()]
        res = {}
        for F in ("F0", "F1"):
            bb = [r for r in rows if r["F"] == F]
            if bb:
                res[F] = sum(r["seconds"] for r in bb) / sum(r["rows"] for r in bb)
        if len(res) == 2:
            out[d.name] = res
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=50)
    ap.add_argument("--probe", default="runs/pilot-probe")
    a = ap.parse_args()
    m = measured(ROOT / a.probe)
    rows = []
    for slug in ALL:
        if slug in m:
            t, kind = m[slug], "measured"
        else:
            ref, k = SCALE[slug]
            t, kind = {F: m[ref][F] * k for F in ("F0", "F1")}, f"ESTIMATE ({k} x {ref})"
        per_f = {F: sum(CELLS.values()) // 2 * 2 * a.n + 0 for F in ("F0", "F1")}   # cells/2 per format x 2 conditions x n
        half = sum(CELLS.values()) // 2 * 2 * a.n
        greedy = sum(CELLS.values()) // 4   # one greedy per (W,F,O,x): negligible; folded into F-halves
        hrs = (half * t["F0"] + half * t["F1"]) / 3600
        rows.append((slug, kind, t["F0"], t["F1"], hrs, 2 * half))
    tot = sum(r[4] for r in rows)
    print(f"n={a.n}: responses per model {rows[0][5]} (+ greedy)")
    for r in rows:
        print(f"{r[0]:26s} {r[1]:40s} F0 {r[2]:.3f} s/resp  F1 {r[3]:.3f} s/resp  -> {r[4]:.2f} h")
    print(f"TOTAL {tot:.2f} GPU-hours (cap 14)")
    for n in (40, 30):
        print(f"  at n={n}: {tot * n / a.n:.2f} h")
    f1_share = sum(((r[5] / 2) * r[3]) / 3600 for r in rows)
    print(f"  F1 share of the total at n={a.n}: {f1_share:.2f} h; dropping F1 entirely would leave {tot - f1_share:.2f} h")


if __name__ == "__main__":
    main()

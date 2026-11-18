"""Validity of pilot responses by experimental condition, and the A1.10 unfinished-answer check (revision item C1).

    .venv/Scripts/python.exe -I analysis/pilot/validity_by_condition.py [--out runs/pilot-validity]

Part 1 (no model calls). Primary validity rule of A1.10 (parsed AND finished; the 512-token top-up rows replace the
256-token rows with the same key). For every model x paradigm x format cell pooled over wording, temperature, order and
repetitions: valid share in condition x = 0 and x = 1, their difference, a Wilson interval per condition and Newcombe's
hybrid score interval for the difference. Also the same under sensitivity (a) of A1.10 (parsed-but-unfinished F0 answers
counted valid). Outputs validity_by_condition.csv and summary.md.

Part 2 (blind sample for the A1.10 check). A random sample (seed 20261016) of parsed-but-unfinished F0 responses, stratified
by model, is written to unfinished_sample_blind.jsonl with the prompt's answer instruction and the raw output only; the
condition, cell key and parsed value are kept apart in unfinished_sample_key.jsonl. A reviewer who sees only the blind
file judges whether the raw output already contains one complete, unambiguous answer before the truncation.
"""
import argparse
import csv
import json
import math
import random
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEED = 20261016


def wilson(k, n, z=1.959964):
    if n == 0:
        return float("nan"), float("nan")
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return max(0.0, c - h), min(1.0, c + h)


def newcombe(k1, n1, k0, n0):
    """Newcombe (1998) method 10 interval for p1 - p0."""
    p1, p0 = k1 / n1, k0 / n0
    l1, u1 = wilson(k1, n1)
    l0, u0 = wilson(k0, n0)
    d = p1 - p0
    return d - math.sqrt((p1 - l1) ** 2 + (u0 - p0) ** 2), d + math.sqrt((u1 - p1) ** 2 + (p0 - l0) ** 2)


def load(model_dir):
    rows = {}
    for f in sorted(model_dir.glob("P*.jsonl")):
        if "batches" in f.name or "topup" in f.name:
            continue
        for l in open(f, encoding="utf8"):
            if l.strip():
                r = json.loads(l)
                rows[r["key"]] = r
    for f in sorted(model_dir.glob("P*.topup512.jsonl")):
        for l in open(f, encoding="utf8"):
            if l.strip():
                r = json.loads(l)
                if r["key"] in rows:
                    rows[r["key"]] = r
    return list(rows.values())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--runs", default="runs/pilot")
    ap.add_argument("--out", default="runs/pilot-validity")
    ap.add_argument("--sample", type=int, default=120)
    a = ap.parse_args()
    out = ROOT / a.out
    out.mkdir(parents=True, exist_ok=True)
    models = sorted(p for p in (ROOT / a.runs).iterdir() if p.is_dir())
    res, unfinished = [], []
    for md in models:
        rows = load(md)
        cell = defaultdict(lambda: [[0, 0], [0, 0], [0, 0], [0, 0]])  # x0 valid/n, x1 valid/n, sens x0, sens x1
        for r in rows:
            x = int(r["x"])
            parsed = r.get("parsed") not in (None, "")
            v = bool(r["valid"])
            vs = v or (r["F"] == "F0" and parsed and not r["finished"])
            c = cell[(r["paradigm"], r["F"])]
            c[x][0] += v
            c[x][1] += 1
            c[2 + x][0] += vs
            c[2 + x][1] += 1
            if r["F"] == "F0" and parsed and not r["finished"]:
                unfinished.append(r)
        for (par, fm), c in sorted(cell.items()):
            for rule, (i0, i1) in (("primary", (0, 1)), ("f0_parsed_valid", (2, 3))):
                if rule == "f0_parsed_valid" and fm != "F0":
                    continue
                k0, n0 = c[i0]
                k1, n1 = c[i1]
                lo, hi = newcombe(k1, n1, k0, n0)
                res.append(dict(model=md.name, paradigm=par, format=fm, rule=rule, valid_x0=k0, n_x0=n0, valid_x1=k1, n_x1=n1,
                                share_x0=round(k0 / n0, 4), share_x1=round(k1 / n1, 4), diff_x1_minus_x0=round(k1 / n1 - k0 / n0, 4),
                                newcombe_lo=round(lo, 4), newcombe_hi=round(hi, 4), excludes_zero=bool(lo > 0 or hi < 0)))
    with open(out / "validity_by_condition.csv", "w", encoding="utf8", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(res[0]))
        w.writeheader()
        w.writerows(res)
    prim = [r for r in res if r["rule"] == "primary"]
    big = [r for r in prim if abs(r["diff_x1_minus_x0"]) >= 0.02]
    md = ["# Pilot validity by condition (C1; A1.10 primary rule, top-up applied)\n",
          f"Cells (model x paradigm x format): {len(prim)}. Cells whose Newcombe 95% interval for the difference in valid share "
          f"(x = 1 minus x = 0) excludes zero: {sum(r['excludes_zero'] for r in prim)}. Cells with an absolute difference of at "
          f"least 2 points: {len(big)}. Largest absolute difference: {max(abs(r['diff_x1_minus_x0']) for r in prim):.4f}.\n",
          "| model | paradigm | format | valid x0 | valid x1 | difference (95% Newcombe) |", "|---|---|---|---|---|---|"]
    for r in sorted(prim, key=lambda r: -abs(r["diff_x1_minus_x0"]))[:20]:
        md.append(f"| {r['model']} | {r['paradigm']} | {r['format']} | {r['valid_x0']}/{r['n_x0']} | {r['valid_x1']}/{r['n_x1']} | "
                  f"{r['diff_x1_minus_x0']:+.3f} ({r['newcombe_lo']:+.3f} to {r['newcombe_hi']:+.3f}) |")
    md.append("\n(20 cells with the largest absolute difference; all cells in validity_by_condition.csv.)\n")
    # blind sample
    rng = random.Random(SEED)
    by_model = defaultdict(list)
    for r in unfinished:
        by_model[r["model"]].append(r)
    tot = len(unfinished)
    alloc = {m: max(1, round(a.sample * len(v) / tot)) for m, v in by_model.items()}
    blind, key = [], []
    for m in sorted(by_model):
        pick = rng.sample(by_model[m], min(alloc[m], len(by_model[m])))
        for r in pick:
            key.append(dict(model=r["model"], key=r["key"], paradigm=r["paradigm"], x=r["x"], parsed=r["parsed"], raw=r["raw"]))
    rng.shuffle(key)
    for i, k in enumerate(key, 1):
        k["sid"] = f"U{i:03d}"
        src = next(r for r in by_model[k["model"]] if r["key"] == k["key"])
        instr = src["user"].strip().split("\n")[-1]
        blind.append(dict(sid=k["sid"], answer_instruction=instr, allowed_labels=src.get("labels"), raw_output=src["raw"]))
    with open(out / "unfinished_sample_blind.jsonl", "w", encoding="utf8") as fh:
        for b in blind:
            fh.write(json.dumps(b, ensure_ascii=False) + "\n")
    with open(out / "unfinished_sample_key.jsonl", "w", encoding="utf8") as fh:
        for k in key:
            fh.write(json.dumps(k, ensure_ascii=False) + "\n")
    md.append(f"Parsed-but-unfinished F0 responses (primary-invalid; valid under sensitivity a): {tot}. Blind sample: {len(blind)} "
              f"(proportional by model, seed {SEED}): " + ", ".join(f"{m} {alloc[m]}" for m in sorted(alloc)) + ".\n")
    (out / "summary.md").write_text("\n".join(md) + "\n", encoding="utf8")
    print("\n".join(md))


if __name__ == "__main__":
    main()

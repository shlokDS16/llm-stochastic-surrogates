"""NOT REPORTED: post-outcome, not in the plan; removed after red-team review 2026-11-08

Precision control: shift in the Arm L effect when Qwen2.5-1.5B-Instruct runs from its NF4 copy instead of bf16.

Reads runs/acme-L-precision/outcomes/effects.csv (NF4 copy, made by armL_outcomes.py --runs runs/acme-L-precision) and the
bf16 rows of runs/acme-L/outcomes/effects.csv. Both runs use the same pinned revision, prompts and temperatures. A cell is
(item, W, O, variant, T). Only cells whose valid mass reaches the threshold of the valid-mass rule (0.9) in both conditions of both
precisions enter; the numeric items are read apart because their readout is truncated. Writes runs/acme-L-precision/shift.csv
(one row per item) and shift_summary.json.

Usage:  .venv/Scripts/python.exe -I analysis/acme/precision_control.py
"""
from __future__ import annotations

import csv
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
MODEL = "qwen2.5-1.5b-instruct"
CTL = "qwen2.5-1.5b-instruct-nf4ctl"
VALID = 0.9
CHOICE = ["P1", "AF", "NR"]
RATING = ["P3", "QA"]
NUMERIC = ["P2a", "P2b", "P2c", "P2d", "P4"]


def load(rel: str, model: str) -> dict[tuple, dict[str, str]]:
    out = {}
    with (ROOT / rel).open(encoding="utf-8", newline="") as f:
        for r in csv.DictReader(f):
            if r["model"] == model and r["variant"] == "main":
                out[(r["item"], r["W"], r["O"], r["T"])] = r
    return out


def ok(r: dict[str, str]) -> bool:
    return r["delta"] not in ("", "None", "nan") and float(r["valid1"]) >= VALID and float(r["valid0"]) >= VALID


def main() -> None:
    a = load("runs/acme-L/outcomes/effects.csv", MODEL)
    b = load("runs/acme-L-precision/outcomes/effects.csv", CTL)
    keys = sorted(set(a) & set(b))
    assert keys, "no common cells"
    rows = []
    for it in CHOICE + RATING + NUMERIC:
        d = [(float(a[k]["delta"]), float(b[k]["delta"])) for k in keys if k[0] == it and ok(a[k]) and ok(b[k])]
        n_all = sum(1 for k in keys if k[0] == it)
        if not d:
            rows.append(dict(item=it, cells=n_all, used=0))
            continue
        diffs = [y - x for x, y in d]
        mean_a = sum(x for x, _ in d) / len(d)
        mean_b = sum(y for _, y in d) / len(d)
        rows.append(dict(item=it, cells=n_all, used=len(d), mean_effect_bf16=mean_a, mean_effect_nf4=mean_b,
                         mean_abs_shift=sum(abs(x) for x in diffs) / len(d), max_abs_shift=max(abs(x) for x in diffs),
                         mean_shift=sum(diffs) / len(diffs),
                         sign_agree=sum(1 for x, y in d if (x > 0) == (y > 0) or x == y) / len(d)))
    fields = ["item", "cells", "used", "mean_effect_bf16", "mean_effect_nf4", "mean_abs_shift", "max_abs_shift", "mean_shift", "sign_agree"]
    with (ROOT / "runs/acme-L-precision/shift.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        w.writerows(rows)

    def pooled(items):
        d = [abs(float(b[k]["delta"]) - float(a[k]["delta"])) for k in keys if k[0] in items and ok(a[k]) and ok(b[k])]
        return dict(cells=len(d), mean_abs_shift=sum(d) / len(d) if d else None, max_abs_shift=max(d) if d else None)

    summ = dict(model=MODEL, control=CTL, valid_threshold=VALID, common_cells=len(keys),
                choice=pooled(CHOICE), rating=pooled(RATING), numeric=pooled(NUMERIC),
                binary_and_rating=pooled(CHOICE + RATING))
    (ROOT / "runs/acme-L-precision/shift_summary.json").write_text(json.dumps(summ, indent=1), encoding="utf-8")
    print(json.dumps(summ, indent=1))
    for r in rows:
        print({k: (round(v, 4) if isinstance(v, float) else v) for k, v in r.items()})


if __name__ == "__main__":
    main()

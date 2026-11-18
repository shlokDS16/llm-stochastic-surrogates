"""Human scales on the Arm L outcome scales (prereg section 3): per item, the ML1 within-site SD and the single-site SE.

    .venv/Scripts/python.exe -I analysis/acme/human_scales.py      -> runs/human-ml1-acme/arml_scales.csv

Scale per item (data/processed/ml1/<item>.csv): P2a-d y_log = log(x); P4 y_log = log(1 + x); P3, QA y (1-9, higher = go / agree);
P1, AF, NR y (0/1; P1 sure option, AF anti-speech answer, NR Yes to the US question).
sd_within = median over sites of the pooled within-site SD sqrt(((n1-1)s1^2 + (n0-1)s0^2) / (n1 + n0 - 2));
se_single = median over sites of sqrt(s1^2/n1 + s0^2/n0); both on the scale above. Human data only (no model output).
"""
from __future__ import annotations

import csv
import math
from pathlib import Path
from statistics import median

ROOT = Path(__file__).resolve().parents[2]
ITEMS = ["P1", "P2a", "P2b", "P2c", "P2d", "P3", "P4", "AF", "QA", "NR"]
COL = {"P2a": "y_log", "P2b": "y_log", "P2c": "y_log", "P2d": "y_log", "P4": "y_log"}


def var(v):
    m = sum(v) / len(v)
    return sum((x - m) ** 2 for x in v) / (len(v) - 1)


def main():
    out = []
    for it in ITEMS:
        col = COL.get(it, "y")
        sites = {}
        with (ROOT / f"data/processed/ml1/{it}.csv").open(encoding="utf8") as f:
            for r in csv.DictReader(f):
                if r.get(col) in (None, "", "nan"):
                    continue
                y = float(r[col])
                if math.isnan(y) or math.isinf(y):
                    continue
                sites.setdefault(r["site"], {0: [], 1: []})[int(float(r["x"]))].append(y)
        sw, se, k = [], [], 0
        for s, g in sites.items():
            n1, n0 = len(g[1]), len(g[0])
            if n1 < 2 or n0 < 2:
                continue
            v1, v0 = var(g[1]), var(g[0])
            sw.append(math.sqrt(((n1 - 1) * v1 + (n0 - 1) * v0) / (n1 + n0 - 2)))
            se.append(math.sqrt(v1 / n1 + v0 / n0))
            k += 1
        out.append(dict(item=it, scale=col if col != "y" else ("0/1" if it in ("P1", "AF", "NR") else "1-9"), k_sites=k,
                        sd_within=median(sw), se_single=median(se), se_single_sd_units=median(se) / median(sw)))
    p = ROOT / "runs/human-ml1-acme/arml_scales.csv"
    with p.open("w", newline="", encoding="utf8") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    for r in out:
        print(r)


if __name__ == "__main__":
    main()

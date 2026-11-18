"""Diagnostic (not preregistered): share of Arm S numeric answers written with a verbal multiplier ("2.7 million").

The Arm L digit tree (numtree.py) ends a number at the first non-numeric token, so "2.7 million" reads as 2.7 there, while the
Arm S parser (analysis/pilot/parsers.py) applies the multiplier. This counts, per model and numeric item, the sampled F0 answers
at T 0.7 and 1.0 (the G4 cells) whose raw text has a digit followed by million/thousand/billion/hundred/k/m/bn/mil.
Arm S files as in gate_g4.source(). Writes runs/acme-L/diagnostics/multiplier_share.csv.

    .venv/Scripts/python.exe -I analysis/acme/numeric_multipliers.py
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
from gate_g4 import source  # noqa: E402

MULT = re.compile(r"\d\s*(million|thousand|billion|hundred|k\b|m\b|bn\b|mil\b)", re.I)
ITEMS = ("P2a", "P2b", "P2c", "P2d", "P4")


def main() -> None:
    rows = []
    models = sorted(p.name for p in (ROOT / "runs" / "acme-L").iterdir() if (p / "P2a.jsonl").exists())
    for m in models:
        for it in ITEMS:
            f = source(ROOT / "runs", m, it)
            n = k = 0
            if f.exists():
                for line in f.open(encoding="utf-8"):
                    r = json.loads(line)
                    if str(r.get("greedy")) == "True" or r.get("F", "F0") != "F0" or float(r.get("T", 0)) not in (0.7, 1.0):
                        continue
                    n += 1
                    k += bool(MULT.search(str(r.get("raw", ""))))
            rows.append(dict(model=m, item=it, source=str(f.relative_to(ROOT)), n=n, n_mult=k, share=k / n if n else None))
    out = ROOT / "runs" / "acme-L" / "diagnostics"
    out.mkdir(parents=True, exist_ok=True)
    d = pd.DataFrame(rows)
    d.to_csv(out / "multiplier_share.csv", index=False)
    print(d.pivot(index="model", columns="item", values="share").round(2).to_string())


if __name__ == "__main__":
    main()

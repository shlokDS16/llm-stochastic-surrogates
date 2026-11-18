"""Denominator check for amendment A-G1 (PREREG-acme section 3): ratio of the sum of untruncated components to the array variance
on random arrays of the real shapes (normal, heavy-tailed, model-dominated, rounded/tied). Seed 1, 4000 arrays per shape, 6 shapes.
    .venv/Scripts/python.exe -I analysis/acme/denominator_check.py   -> runs/acme-G1/denominator-check/result.json
Same generator as the check run on 2026-11-06 before freezing (it printed only the minima); this script saves the output."""
import json, sys
from pathlib import Path
import numpy as np
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gstudy as G
rng = np.random.default_rng(1)
res = {}
for shape, fac in [((14, 10, 2), G.FACETS3), ((14, 10), G.FACETS2), ((14, 10, 2, 4), G.FACETS4), ((14, 10, 4), G.FACETS3T),
                   ((13, 9, 2), G.FACETS3), ((13, 9), G.FACETS2)]:
    r = []
    for k in range(4000):
        a = rng.standard_normal(shape) * rng.exponential(1, shape) ** rng.integers(0, 3)
        if k % 2:
            a = a + rng.standard_normal(shape[:1] + (1,) * (len(shape) - 1)) * 5
        if k % 3 == 0:
            a = np.round(a, 0)
        d = G.decompose(a, fac)
        r.append(sum(d["components"].values()) / a.var())
    res[str(shape)] = dict(n=len(r), min=float(np.min(r)), median=float(np.median(r)), max=float(np.max(r)))
out = HERE.parents[1] / "runs/acme-G1/denominator-check/result.json"
out.write_text(json.dumps(res, indent=1), encoding="utf8")
print(json.dumps(res, indent=1))

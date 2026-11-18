"""Human finite-site spread S^H with the Amendment A1 estimator (statistician, 2026-10-16).

    .venv/Scripts/python.exe -I analysis/human_ml1/spread_a1.py > runs/pilot-sim2/human_spread_a1.txt

Sites are the 36 fixed ML1 samples (one factor, 36 levels). Same code path as the LLM grid: split-half v_c, test-inversion
interval ('ti_boot'). Compared with the REML tau and Q-profile interval from metafor (runs/human-ml1/metafor_results.json),
which treat sites as a random sample, so the two are placed side by side, not equated.
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "analysis" / "pilot"))
import estimators as E  # noqa: E402

PAR = {  # file, outcome column(s): (kind, column, transform)
    "P1 framing log OR": ("P1", "binary", "y", None),
    "P2a NYC g (raw)": ("P2a", "cont", "y", None), "P2a NYC g (log)": ("P2a", "cont", "y_log", None),
    "P2b Chicago g (raw)": ("P2b", "cont", "y", None), "P2b Chicago g (log)": ("P2b", "cont", "y_log", None),
    "P2c Everest g (raw)": ("P2c", "cont", "y", None), "P2c Everest g (log)": ("P2c", "cont", "y_log", None),
    "P2d babies g (raw)": ("P2d", "cont", "y", None), "P2d babies g (log)": ("P2d", "cont", "y_log", None),
    "P3 sunk g": ("P3", "cont", "y", None),
    # column y of P4 is already log(1+x) (build_tidy.py); y_raw is the count. Fixed 2026-10-16 (CRP-S02): log1p was applied twice.
    "P4 gambler g log1p": ("P4", "cont", "y", None), "P4 gambler g raw": ("P4", "cont", "y_raw", None),
}
rng = np.random.default_rng(20261016)
metafor = json.loads((ROOT / "runs/human-ml1/metafor_results.json").read_text(encoding="utf8")) if (ROOT / "runs/human-ml1/metafor_results.json").exists() else {}
print(f"{'metric':22s} {'sites':>5s} {'S2hat':>8s} {'S^H':>6s} {'TI 95% S':>16s} {'basic-ish lower>0':>18s} | formula-v S^H")
for name, (f, kind, col, tf) in PAR.items():
    df = pd.read_csv(ROOT / "data/processed/ml1" / f"{f}.csv")
    cells = {}
    for i, (s, g) in enumerate(df.groupby("site", sort=True)):
        y1, y0 = g.loc[g.x == 1, col].to_numpy(float), g.loc[g.x == 0, col].to_numpy(float)
        if tf is not None:
            y1, y0 = tf(y1), tf(y0)
        cells[(i,)] = (y1, y0)
    design = E.Design(["site"], [len(cells)])
    floor = 0.0
    r = E.estimate2(cells, design, kind, rng=rng, B=2000, K=200, var_method="splithalf", sd_floor=floor, intervals=("ti_boot",), term_intervals=False)
    if r["status"] != "ok":
        print(f"{name:22s} deterministic cells {r['deterministic_cells']}")
        continue
    rf = E.estimate2(cells, design, kind, rng=rng, var_method="formula", intervals=(), term_intervals=False)
    iv = r["intervals"]["ti_boot"]
    print(f"{name:22s} {len(cells):5d} {r['S2_untruncated']:8.4f} {r['S']:6.3f} [{iv['S'][0]:6.3f}, {iv['S'][1]:6.3f}] {str(iv['S2'][0] > 0):>18s} | {rf['S']:.3f}")
